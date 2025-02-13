from time import sleep
from datetime import datetime, timezone, timedelta
from kubernetes import client, config, watch
import json
import argparse

# Load the kubeconfig
config.load_kube_config()

# Constants
tzinfo = timezone(timedelta(hours=0))
N_RUNS = 5
VERBOSE = False
namespace = "fluidos"
daemonset_name = "node-network-manager"
cr_api_group = "network.fluidos.eu"
cr_api_version = "v1alpha1"
cr_kind_plural = "knownclusters"
cr_kind = "KnownCluster"

# Clients
v1_daemonset = client.AppsV1Api()
v1_custom = client.CustomObjectsApi()
v1_event = client.CoreV1Api()

def disable_daemonset():
    """Patch the DaemonSet to add a non-existent node label (disable it)."""
    patch = [
        {
            "op": "add",
            "path": "/spec/template/spec/nodeSelector",
            "value": {"non-existent-label": "true"}
        }
    ]
    v1_daemonset.patch_namespaced_daemon_set(daemonset_name, namespace, patch)
    print("DaemonSet disabled (non-existent node label applied).")
    # for sleep times too small, i suppose the pod does not have enough time to be destroyed
    # so the system has to wait more time from the moment i reschedule it to the moment it is actually started
    # use value > 1
    sleep(2)

def enable_daemonset():
    """Patch the DaemonSet to restore the original nodeSelector (enable it)."""
    patch = [
        {
            "op": "replace",
            "path": "/spec/template/spec/nodeSelector",
            "value": {"node-role.fluidos.eu/worker": "true"}
        }
    ]
    v1_daemonset.patch_namespaced_daemon_set(daemonset_name, namespace, patch)
    print("DaemonSet re-enabled (original node label restored).")

def delete_all_knownclusters_cr():
    """Delete all custom resources of type 'KnownCluster'."""
    crs = v1_custom.list_namespaced_custom_object(
        group=cr_api_group,
        version=cr_api_version,
        namespace=namespace,
        plural=cr_kind_plural
    )
    for cr in crs['items']:
        cr_name = cr['metadata']['name']
        v1_custom.delete_namespaced_custom_object(
            group=cr_api_group,
            version=cr_api_version,
            namespace=namespace,
            plural=cr_kind_plural,
            name=cr_name
        )
        if VERBOSE:
            print(f"Deleted KnownClusters CR: {cr_name}")
    print("All KnownClusters CRs have been deleted.")

def delete_all_events():
    """Delete all event objects in the specified namespace."""
    # List all events in the namespace
    events = v1_event.list_namespaced_event(namespace)
    
    # Iterate through each event and delete it
    for event in events.items:
        event_name = event.metadata.name
        try:
            v1_event.delete_namespaced_event(name=event_name, namespace=namespace)
            if VERBOSE:
                print(f"Deleted event: {event_name}")  
        except client.exceptions.ApiException as e:
            print(f"Failed to delete event {event_name}: {e.reason}")
    
    print(f"All events in namespace '{namespace}' have been deleted.")

# ! the time definition of cr is only seconds, while local is micro, so sometimes if
# checking via timestamp the event is not considered
def is_first_timestamp_after(first_time: datetime, second_time: datetime) -> bool:
    """Compare two timestamps to check if the first is after the second."""
    print(f"{first_time} - {second_time} - {first_time>second_time}")
    return first_time > second_time

def watch_for_first_cr_creation():
    """Watch for the creation of the first KnownClusters CR and measure the time it takes."""

    enable_daemonset()
    w = watch.Watch()
    print("Watching for the creation of the first KnownClusters CR...")

    for event in w.stream(v1_custom.list_namespaced_custom_object, 
                          group=cr_api_group, 
                          version=cr_api_version, 
                          namespace=namespace, 
                          plural=cr_kind_plural):
        if event['type'] == 'ADDED':
            cr_name = event['object']['metadata']['name']
            print(f"Detected creation of KnownClusters CR: {cr_name}")
            creation_time = datetime.now(tzinfo)
            if VERBOSE:
                print(f"Time taken for first KnownClusters CR to appear: {creation_time:.2f} seconds")
            w.stop()  # Stop the watch as we only need the first CR creation
            break
    return creation_time

# this function return the time at which the netmanager was started
def watch_netmanager_started():
    
    w = watch.Watch()
    enable_daemonset()
    for event in w.stream(v1_event.list_namespaced_event, namespace=namespace):
        if VERBOSE:
            print(f"Event: {event['type']} {event['object'].metadata.name} {event['object'].reason}")
        if (
            event['type'] == 'ADDED'
            and event['object'].metadata.name.startswith(daemonset_name)
            and event['object'].reason == 'Started'
            # and is_first_timestamp_after(event['object'].metadata.creation_timestamp, begin)
        ):
            print(f"Wanted event - Event: {event['type']} {event['object'].metadata.name} {event['object'].reason}")
            started_time = datetime.now(tzinfo)
            w.stop()
            break

    return started_time

def run_benchmark(n, output_file):
    """Run the benchmark n times and save results to a file."""
    print("Discovery only benchmark")
    times = []

    for i in range(n):
        print(f"\n--- Run {i + 1} ---")
        
        # Step 1: Disable the DaemonSet
        disable_daemonset()
        # reset the history of cr and events
        delete_all_knownclusters_cr()
        delete_all_events()

        # Step 2: Measure the startup time
        start_time = watch_netmanager_started()
        end_time = watch_for_first_cr_creation()
        elapsed_time = end_time - start_time
        times.append(elapsed_time)
        print(f"Run {i + 1} startup time: {elapsed_time.total_seconds():.2f} seconds")

    # Calculate the average time in seconds
    total_seconds = sum(t.total_seconds() for t in times)
    average_time = total_seconds / len(times) if times else 0
    print(f"\nAverage time for CR to reappear over {n} runs: {average_time:.2f} seconds")

    # Prepare results for JSON serialization
    results = {
        "runs": [t.total_seconds() for t in times],  # Convert timedelta to seconds
        "average_time": average_time
    }

    # Save results to the output file
    with open(output_file, "w") as f:
        json.dump(results, f, indent=4)
    print(f"Results saved to {output_file}")



# Run the benchmark with the specified number of iterations and save results to a file
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    args = parser.parse_args()
    if args.verbose:
        VERBOSE = True

    output_file = "netmanager_benchmark_results_discovery_only.json"
    run_benchmark(N_RUNS, output_file)
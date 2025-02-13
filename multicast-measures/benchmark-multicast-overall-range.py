import os
from time import perf_counter, sleep
from datetime import datetime, timezone, timedelta
from kubernetes import client, config, watch
import numpy as np
import argparse
import random

# Load the kubeconfig
config.load_kube_config()

# Constants
VERBOSE = False
namespace = "fluidos"
daemonset_name = "node-network-manager"
cr_api_group = "network.fluidos.eu"
cr_api_version = "v1alpha1"
cr_kind_plural = "knownclusters"
cr_kind = "KnownCluster"

vm_addr = "65"

# Clients
v1_daemonset = client.AppsV1Api()
v1_custom = client.CustomObjectsApi()
v1_event = client.CoreV1Api()

def disable_daemonset(sleep_time):
    """Patch the DaemonSet to add a non-existent node label (disable it)."""
    patch = [
        {
            "op": "add",
            "path": "/spec/template/spec/nodeSelector",
            "value": {"non-existent-label": "true"}
        }
    ]
    v1_daemonset.patch_namespaced_daemon_set(daemonset_name, namespace, patch)
    print(f"{datetime.now()} DaemonSet disabled (non-existent node label applied).")
    # for sleep times too small, i suppose the pod does not have enough time to be destroyed
    # so the system has to wait more time from the moment i reschedule it to the moment it is actually started
    # use value > 1
    sleep(int(sleep_time))

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
    print(f"{datetime.now()} DaemonSet re-enabled (original node label restored).")

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
    
    print(f"{datetime.now()} All events in namespace '{namespace}' have been deleted.")

# TODO: try this alternative implementation
# def delete_all_events():
#     """Delete all event objects in the specified namespace using deleteCollection."""
#     try:
#         v1_event.delete_collection_namespaced_event(namespace=namespace)
#         print(f"All events in namespace '{namespace}' have been deleted.")
#     except client.exceptions.ApiException as e:
#         print(f"Failed to delete events: {e.reason}")

# ! the time definition of cr is only seconds, while local is micro, so sometimes if
# checking via timestamp the event is not considered
def is_first_timestamp_after(first_time: datetime, second_time: datetime) -> bool:
    """Compare two timestamps to check if the first is after the second."""
    print(f"{first_time} - {second_time} - {first_time>second_time}")
    return first_time > second_time

def watch_for_first_cr_creation():
    """Watch for the creation of the first KnownClusters CR and measure the time it takes."""
    init_start = perf_counter()
    start_time = datetime.now()
    enable_daemonset()
    init_end = perf_counter()

    print(f"Initialization took: {init_end - init_start:.3f} seconds")
    w = watch.Watch()
    print(f"{datetime.now()} Watching for the creation of the first KnownClusters CR...")

    for event in w.stream(v1_custom.list_namespaced_custom_object, 
                          group=cr_api_group, 
                          version=cr_api_version, 
                          namespace=namespace, 
                          plural=cr_kind_plural):
        if event['type'] == 'ADDED' and event['object']['spec']['address']==f"192.168.11.{vm_addr}:30000":
            cr_name = event['object']['metadata']['name']
            print(f"{datetime.now()} Detected creation of KnownClusters CR: {cr_name}")
            creation_time = datetime.now() - start_time
            if VERBOSE:
                print(f"Time taken for first KnownClusters CR to appear: {creation_time:.2f} seconds")
            w.stop()  # Stop the watch as we only need the first CR creation
            break
    F.write(f"{creation_time.total_seconds()}\n")
    F.flush()
    return creation_time

def benchmark_startup_time():
    tzinfo = timezone(timedelta(hours=0))
    begin = datetime.now(tzinfo)

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
            break

    return started_time - begin

def run_benchmark(n, output_file,sleeptime):
    """Run the benchmark n times and save results to a file."""
    print("Overall time benchmark")
    times = []
    global F
    if os.path.exists(f"./results/{output_file}"):
        F = open(f"./results/{output_file}", 'a')
    else:
        F = open(f"./results/{output_file}", 'w')
        F.write("multicast_benchmark_time_samples\n")
    
    F.write(f"multicast_benchmark_time_samples {sleeptime}\n")
    F.flush()

    for i in range(n):
        print(f"\n--- Run {i + 1} ---")
        
        # only for random sleep time testing
        # sleeptime = random.uniform(20, 25)
        # print(f"Random sleep time selected: {sleeptime:.2f} seconds")



        # Step 1: Disable the DaemonSet
        disable_daemonset(sleeptime)
        # reset the history of cr and events
        delete_all_knownclusters_cr()
        delete_all_events()

        # Step 2: Measure the startup time
        elapsed_time = watch_for_first_cr_creation()
        times.append(elapsed_time)
        print(f"{datetime.now()} Run {i + 1} startup time: {elapsed_time.total_seconds():.2f} seconds")

    # Calculate the average time in seconds
    total_seconds = sum(t.total_seconds() for t in times)
    average_time = total_seconds / len(times) if times else 0
    print(f"\nAverage time for CR to reappear over {n} runs: {average_time:.2f} seconds")

    
    # F.writelines([f"{t.total_seconds()}\n" for t in times])
    F.close()
    print(f"Results saved to {output_file}")



# Run the benchmark with the specified number of iterations and save results to a file
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["netman", "neuropil"], help="Select mode: netman or neuropil")
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true", default=False)
    parser.add_argument("-r","--runs", help="number of runs of measure to perform", type=int, default=10)
    parser.add_argument("-o","--output", help="output file for the results", type=str, default="netmanager_benchmark_results_range.txt")
    args = parser.parse_args()
    if args.verbose:
        VERBOSE = True
    N_RUNS = args.runs
    output_file = args.output
    
    for sleep_time in np.arange(0,30,1):
        run_benchmark(N_RUNS, output_file,sleep_time)
# this benchmark is used to measure the number of nodes discovered in time by the 
# discovery service in the scalability test

from time import sleep
from datetime import datetime, timezone, timedelta
from kubernetes import client, config, watch
import json
import argparse
import os

# Expand home directory path
kube_config_path = os.path.expanduser("/home/netgroup/.kube/config")

# Load the default kubeconfig
config.load_kube_config(kube_config_path)

# Get available contexts
contexts, active_context = config.list_kube_config_contexts(kube_config_path)
# if not contexts:
#     print("Cannot find any context in kube-config file.")
#     return 0
# set specific kube context
if not contexts:
    print("Cannot find any context in kube-config file.")
    exit(1)
config.load_kube_config(config_file=kube_config_path,context="kind-fluidos-1")

# Constants
F = None # used to write the results
VERBOSE = False
N_NODES = 8
namespace = "fluidos"
daemonset_name = "node-network-manager"
neuropil_deployment = "np-fluidos-discovery"
cr_api_group = "network.fluidos.eu"
cr_api_version = "v1alpha1"
cr_kind_plural = "knownclusters"
cr_kind = "KnownCluster"

# Clients
v1_daemonset = v1_deployment = client.AppsV1Api()
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

# scales down the neuropil deployment and checks if the pods are actually deleted
# before returning
def disable_neuropil():
    """Scale down the Neuropil deployment to 0 replicas."""
    # Scale down the Neuropil deployment to 0 replicas
    
    patch = [
        {
            "op": "replace",
            "path": "/spec/replicas",
            "value": 0
        }
    ]
    v1_deployment.patch_namespaced_deployment(neuropil_deployment, namespace, patch)
    print("Neuropil deployment scaled down to 0 replicas.")
    
    # Wait for the Neuropil pods to be deleted

    w = watch.Watch()
    for event in w.stream(v1_event.list_namespaced_pod, namespace=namespace, label_selector="app.kubernetes.io/name=np-discovery"):
        if event['type'] == 'DELETED':
            pods = v1_event.list_namespaced_pod(namespace, label_selector="app.kubernetes.io/name=np-discovery")
            if not pods.items:
                w.stop()
                break
    if VERBOSE:
       print("Neuropil pods have been deleted.") 
    return 


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

def enable_neuropil():
    patch = [
        {
            "op": "replace",
            "path": "/spec/replicas",
            "value": 1
        }
    ]

    v1_deployment.patch_namespaced_deployment(neuropil_deployment, namespace, patch)
    print("Neuropil deployment scaled up to 1 replica.")
    return

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

# measures from giving the start pod command to the creation of the first KnownCluster CR
def watch_for_first_cr_creation(mode):
    """Watch for the creation of the first KnownClusters CR and measure the time it takes."""
    creation_time = None
    start_time = datetime.now()
    if mode == "netman":
        enable_daemonset()
    else: # mode == "neuropil"
        enable_neuropil()
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
            creation_time = datetime.now() - start_time
            if VERBOSE:
                print(f"Time taken for first KnownClusters CR to appear: {creation_time:.2f} seconds")
            w.stop()  # Stop the watch as we only need the first CR creation
            break
    F.write(f"{creation_time.total_seconds()}\n")
    F.flush()
    return creation_time

# measures pod startup time only
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

def scalability_test(mode):
    """Watch for the creation of the first KnownClusters CR and measure the time it takes."""
    nodes_found = 0
    creation_time = None
    start_time = datetime.now()
    if mode == "netman":
        enable_daemonset()
    else: # mode == "neuropil"
        enable_neuropil()
    w = watch.Watch()
    print("Watching for the creation of KnownClusters CRs...")

    for event in w.stream(v1_custom.list_namespaced_custom_object, 
                          group=cr_api_group, 
                          version=cr_api_version, 
                          namespace=namespace, 
                          plural=cr_kind_plural):
        if event['type'] == 'ADDED':
            cr_name = event['object']['metadata']['name']
            print(f"Detected creation of KnownClusters CR: {cr_name} with addr: {event['object']['spec']['address']}")
            # print(event['object'])
            creation_time = datetime.now() - start_time
            F.write(f"{creation_time.total_seconds()} {cr_name} {event['object']['spec']['address']}\n")
            F.flush()
            if VERBOSE:
                print(f"Time taken for first KnownClusters CR to appear: {creation_time:.2f} seconds")
            # go to next iteration if all other nodes are found or timeout is reached
            # all_crs = v1_custom.list_namespaced_custom_object(
            #     group=cr_api_group,
            #     version=cr_api_version,
            #     namespace=namespace,
            #     plural=cr_kind_plural
            # )
            # nodes_found = len(all_crs.get("items", []))
            nodes_found += 1
            if nodes_found == N_NODES-1 or datetime.now() - start_time > timedelta(minutes=5):
                w.stop()
    
    F.write(f"----------------\n")
    F.flush()

    return creation_time

def run_benchmark(mode, n, output_file):
    """Run the benchmark n times and save results to a file."""
    print("Overall time benchmark")
    global F
    if os.path.exists(f"./results/{output_file}"):
        F = open(f"./results/{output_file}", 'a')
    else:
        F = open(f"./results/{output_file}", 'w')
        F.write("multicast_benchmark_time_samples\n")

    # list to store each iteration result
    times = []

    for i in range(n):
        print(f"\n--- Run {i + 1} ---")
        
        # Step 1: Disable the DaemonSet
        if mode == "netman":
            disable_daemonset()
        else: # mode == "neuropil"
            disable_neuropil() # scales down the neuropil deployment and checks if the pods are actually deleted
        # reset the history of cr and events
        delete_all_knownclusters_cr()
        delete_all_events()

        # Step 2: Start measures
        scalability_test(mode)

    
    # old implementation, wrote the times in the file all at once at the end, not suitable in case of crashes
    # f.writelines([f"{t.total_seconds()}\n" for t in times])
    F.close()
    print(f"Results saved to {output_file}")



# Run the benchmark with the specified number of iterations and save results to a file
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["netman", "neuropil"], help="Select mode: netman or neuropil")
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true", default=False)
    parser.add_argument("-r","--runs", help="number of runs of measure to perform", type=int, default=10)
    parser.add_argument("-o","--output", help="output file for the results", type=str, default="discovery-scalability-benchmark.txt")
    parser.add_argument("-n","--nodes", help="number of nodes to find", type=int, default=8)
    args = parser.parse_args()
    if args.verbose:
        VERBOSE = True
    if args.nodes:
        N_NODES = args.nodes
    N_RUNS = args.runs
    output_file = args.output

    run_benchmark(args.mode, N_RUNS, output_file)
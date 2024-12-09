import time
from datetime import timezone, timedelta, datetime
from kubernetes import client, config, watch

# Load the kubeconfig
config.load_kube_config()

# Define the DaemonSet namespace and name
namespace = "fluidos"  # Adjust to your actual namespace
daemonset_name = "node-network-manager"

# Define the CR API and Kind
cr_api_group = "network.fluidos.eu"
cr_api_version = "v1alpha1"
cr_kind = "KnownCluster"

# Define the client to interact with the Kubernetes cluster
v1_daemonset = client.AppsV1Api()
v1_custom = client.CustomObjectsApi()
v1_event = client.CoreV1Api()

# """Monitor events for changes related to the KnownClusters CR or DaemonSet."""
# w = watch.Watch()
# for event in w.stream(v1_custom.list_namespaced_custom_object,
#                     group="network.fluidos.eu",
#                     version="v1alpha1",
#                     namespace=namespace,
#                     plural="knownclusters"):
#     # Check for ADDED events
#     if event["type"] == "ADDED":
#         new_peer = event["object"]["spec"]["address"]
#         creation_timestamp = event["object"]["metadata"]["creationTimestamp"]
#         print(f"[INFO]\t New peer '{new_peer}' added at timestamp '{creation_timestamp}'")

# w = watch.Watch()
# start_time = None

# print("Watching for pod start event for node-network-manager...")

# for event in w.stream(v1_event.list_namespaced_event, namespace=namespace):
#     if event['type'] == 'Normal' and event['reason'] == 'Started':
#         involved_pod_name = event['involvedObject'].get('name', '')
#         print(f"{involved_pod_name}")
        # Check if the event corresponds to a node-network-manager pod
        # if involved_pod_name.startswith(daemonset_name):
        #     if not start_time:
        #         # Start counting time once the pod starts
        #         start_time = time.time()
        #         print(f"Started counting time for pod {involved_pod_name} at {start_time:.2f} seconds")

def is_first_timestamp_after(first_time: datetime, second_time: datetime) -> bool:
    """
    Compare two timestamps and return True if the first is after the second.

    Args:
        first_timestamp (str): The first timestamp in ISO 8601 format (e.g., "2024-11-16 10:45:53+00:00").
        second_timestamp (str): The second timestamp in ISO 8601 format (e.g., "2024-11-16 10:30:00+00:00").

    Returns:
        bool: True if the first timestamp is after the second, False otherwise.
    """
    
    # Compare the two timestamps
    return first_time > second_time

daemonset_name = "node-network-manager"

tzinfo = timezone(timedelta(hours=0))
time = datetime.now(tzinfo)
print(time)
v1 = client.CoreV1Api()
w = watch.Watch()
for event in w.stream(v1.list_event_for_all_namespaces):
    if event['type'] == 'ADDED' and  event['object'].metadata.name.startswith(daemonset_name) and event['object'].reason == 'Started' and not is_first_timestamp_after(event['object'].metadata.creation_timestamp,time):
        object = event['object']
        print("Event: %s %s %s %s" % (event['type'], event['object'].metadata.name, event['object'].reason, object.metadata.creation_timestamp))
        print(is_first_timestamp_after(object.metadata.creation_timestamp, time))
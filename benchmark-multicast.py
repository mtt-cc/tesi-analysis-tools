import time
from kubernetes import client, config, watch

# Load the kubeconfig
config.load_kube_config()

# Define the DaemonSet namespace and name
namespace = "fluidos"
daemonset_name = "node-network-manager"

# Define the CR API and Kind
cr_api_group = "network.fluidos.eu"
cr_api_version = "v1alpha1"
cr_kind_plural = "knownclusters"  # Plural of the CR kind
cr_kind = "KnownCluster"

# Define the client to interact with the Kubernetes cluster
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
    """Delete all custom resources of type 'KnownClusters'."""
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
        print(f"Deleted KnownClusters CR: {cr_name}")
    print("All KnownClusters CRs have been deleted.")

def watch_for_first_cr_creation():
    """Watch for the creation of the first KnownClusters CR and measure the time it takes."""
    enable_daemonset()
    w = watch.Watch()
    start_time = time.time()
    print("Watching for the creation of the first KnownClusters CR...")

    for event in w.stream(v1_custom.list_namespaced_custom_object, 
                          group=cr_api_group, 
                          version=cr_api_version, 
                          namespace=namespace, 
                          plural=cr_kind_plural):
        if event['type'] == 'ADDED':
            cr_name = event['object']['metadata']['name']
            print(f"Detected creation of KnownClusters CR: {cr_name}")
            creation_time = time.time() - start_time
            print(f"Time taken for first KnownClusters CR to appear: {creation_time:.2f} seconds")
            w.stop()  # Stop the watch as we only need the first CR creation
            break
    return creation_time

def main():
    # Step 1: Disable the DaemonSet
    disable_daemonset()

    # Step 2: Delete all existing KnownClusters CRs
    delete_all_knownclusters_cr()

    # Step 3: Watch for the first KnownClusters CR creation and timestamp it
    creation_time = watch_for_first_cr_creation()
    

if __name__ == "__main__":
    main()

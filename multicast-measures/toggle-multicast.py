from kubernetes import client, config
import subprocess
import sys


def get_pod_name(prefix, namespace):
    """Find the first pod starting with a specific prefix."""
    try:
        v1 = client.CoreV1Api()
        pods = v1.list_namespaced_pod(namespace=namespace)
        for pod in pods.items:
            if pod.metadata.name.startswith(prefix):
                return pod.metadata.name
        return None
    except client.exceptions.ApiException as e:
        print(f"Error finding pod: {e}")
        sys.exit(1)


def toggle_multicast(pod_name, namespace, action):
    """Enable or disable multicast on all interfaces in the pod."""
    # Determine the ip command to enable/disable multicast
    if action == "enable":
        multicast_command = "ip link set dev {iface} multicast on"
    elif action == "disable":
        multicast_command = "ip link set dev {iface} multicast off"
    else:
        print("Invalid action. Use 'enable' or 'disable'.")
        sys.exit(1)

    try:
        # Execute the command to get interface names
        # exec_command = [
        #     "kubectl", "exec", pod_name, "-n", namespace, "--",
        #     "bash", "-c", "ip -o link show | awk -F': ' '{print $2}'"
        # ]
        exec_command = f"kubectl exec {pod_name} -n {namespace} -- ip -o link show" + " | awk -F': ' '{print $2}'"
        # result = subprocess.check_output(exec_command).decode("utf-8").strip()
        result = subprocess.run(exec_command, shell=True, check=True, text=True, capture_output=True)
        print(result.stdout)
        # print(interfaces)
        # return 0
        interfaces = result.stdout.split('\n')

        # Apply the multicast command to each interface
        for iface in interfaces:
            # Skip loopback or irrelevant interfaces
            if iface == "lo":
                continue

            # set_multicast_command = [
            #     "kubectl", "exec", pod_name, "-n", namespace, "--",
            #     multicast_command.format(iface=iface)
            # ]
            set_multicast_command = f"sudo kubectl exec {pod_name} -n {namespace} -- {multicast_command.format(iface=iface)}"
            subprocess.run(set_multicast_command, shell=True, check=True, text=True, capture_output=True)
            print(f"{action.capitalize()}d multicast on interface: {iface}")
    except subprocess.CalledProcessError as e:
        print(f"Error toggling multicast: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    if len(sys.argv) != 4:
        print("Usage: python toggle_multicast.py <namespace> <prefix> <enable|disable>")
        sys.exit(1)

    namespace = sys.argv[1]
    prefix = sys.argv[2]
    action = sys.argv[3]

    # Load Kubernetes configuration
    config.load_kube_config()

    # Find the pod
    pod_name = get_pod_name(prefix, namespace)
    if not pod_name:
        print(f"No pod found with prefix '{prefix}' in namespace '{namespace}'.")
        sys.exit(1)

    print(f"Found pod: {pod_name}")

    # Toggle multicast
    toggle_multicast(pod_name, namespace, action)


if __name__ == "__main__":
    main()

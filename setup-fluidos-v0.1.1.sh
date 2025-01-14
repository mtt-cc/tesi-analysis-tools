#!/bin/bash

# Environment variables

# FLUIDOS
FLUIDOS_VERSION="v0.1.1" # in this script the version does not affect the actual images version
NODE_NAME=vm1
NET_INTERFACE=ens18
NODE_IP=$(ip a | grep $HOST_INTERFACE | grep inet | awk '{print $2}' | cut -d '/' -f 1)
REAR_PORT=30000
# Network Manager
ENABLE_LOCAL_DISCOVERY=true
DISABLE_LOCAL_DISCOVERY=false
FIRST_OCTET=10
SECOND_OCTET=200
THIRD_OCTET=0

# Labels to add to the nodes
declare -A LABELS
LABELS["node-role.fluidos.eu/worker"]="true"
LABELS["node-role.fluidos.eu/resources"]="true"

check_dependencies() {
    if ! command -v helm &> /dev/null; then
        echo "Error: helm is not installed. Please install helm first."
        exit 1
    fi
    if ! command -v kubectl &> /dev/null; then
        echo "Error: kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    if [ ! -f /etc/rancher/k3s/k3s.yaml ]; then
        echo "Error: KUBECONFIG file not found at /etc/rancher/k3s/k3s.yaml"
        exit 1
    fi
}

install_fluidos() {
    COMPONENT=$1
    echo "Install FLUIDOS - Component: $COMPONENT"

    # Export the KUBECONFIG
    export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

    # Add the FLUIDOS Helm repository
    echo "  - Checking if FLUIDOS Helm repository is already present"
    if helm repo list | grep -q "^fluidos"; then
        echo "  - FLUIDOS Helm repository is already added"
    else
        echo "  - Adding FLUIDOS Helm repository"
        helm repo add fluidos https://fluidos-project.github.io/node/ 1>/dev/null
        helm repo update 1>/dev/null
        if [ $? -ne 0 ]; then
            echo "Error: Failed to add or update the FLUIDOS Helm repository"
            exit 1
        fi
    fi

    # Label the node
    echo "  - Labeling the node"
    for LABEL_KEY in "${!LABELS[@]}"; do
        LABEL_VALUE=${LABELS[$LABEL_KEY]}
        kubectl label node "$NODE_NAME" "$LABEL_KEY=$LABEL_VALUE" --overwrite
        echo "Label $LABEL_KEY=$LABEL_VALUE set on node $NODE_NAME"
    done

    if [ "$COMPONENT" == "network-manager" ]; then
        # Install FLUIDOS with the network-manager component
        echo "  - Installing FLUIDOS (network-manager)"
        helm upgrade --install node ./node-tesi/deployments/node \
            -n fluidos --version "$FLUIDOS_VERSION" \
            --create-namespace -f consumer-values-v0.1.1.yaml \
            --set networkManager.configMaps.nodeIdentity.ip="$NODE_IP" \
            --set rearController.service.gateway.nodePort.port="$REAR_PORT" \
            --set networkManager.config.enableLocalDiscovery="$ENABLE_LOCAL_DISCOVERY" \
            --set networkManager.config.address.thirdOctet="$THIRD_OCTET" \
            --set networkManager.config.netInterface="$NET_INTERFACE" \
            --wait \
            --debug \
            --v=2
            1>/dev/null

        if [ $? -ne 0 ]; then
            echo "Error: Failed to install FLUIDOS (network-manager)"
            exit 1
        fi
        
    #  # Export the YAML to a file
    #     kubectl get network-attachment-definitions.k8s.cni.cncf.io macvlan-conf -n fluidos -o yaml > macvlan-conf.yaml

    #     # Modify eth0 to ens18 in the file
    #     sed -i 's/"master": "eth0"/"master": "ens18"/' macvlan-conf.yaml

    #     # Apply the modified YAML back to the cluster
    #     kubectl apply -f macvlan-conf.yaml

    elif [ "$COMPONENT" == "neuropil" ]; then
        # Install FLUIDOS with the neuropil component
        echo "  - Installing FLUIDOS (neuropil)"
        helm upgrade --install node ./node-tesi/deployments/node \
            -n fluidos --version "$FLUIDOS_VERSION" \
            --create-namespace \
            --set rearController.service.gateway.nodePort.port="$REAR_PORT" \
            --set networkManager.config.enableLocalDiscovery="$DISABLE_LOCAL_DISCOVERY" \
            --set npDiscovery.enabled="true" \
            --wait \
            --debug \
            --v=2 \
            1>/dev/null

        if [ $? -ne 0 ]; then
            echo "Error: Failed to install FLUIDOS (neuropil)"
            exit 1
        fi
    else
        echo "Error: Unsupported component '$COMPONENT'"
        exit 1
    fi
}

uninstall() {
    # Export the KUBECONFIG
    export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

    # Uninstall FLUIDOS
    echo "  - Uninstalling FLUIDOS"
    helm delete node -n fluidos --debug --v=2 --wait 1>/dev/null
    kubectl delete namespace fluidos 1>/dev/null
    kubectl get crd | grep fluidos.eu | awk '{print $1}' | xargs kubectl delete crd 1>/dev/null

    if [ $? -ne 0 ]; then
        echo "Error: Failed to uninstall FLUIDOS"
        exit 1
    fi

    echo "Uninstall complete"
}

# Function to display usage instructions
usage() {
    echo "Usage: $0 <install|uninstall> [component]"
    echo ""
    echo "Commands:"
    echo "  install <network-manager|neuropil>  Install FLUIDOS with the specified component"
    echo "  uninstall                       Uninstall FLUIDOS"
    exit 1
}

# Function to validate the command-line arguments
validate_arguments() {
    if [ "$1" == "install" ]; then
        ACTION="install"
        if [ -z "$2" ]; then
            echo "Error: Component must be specified for installation"
            usage
        fi
        if [[ "$2" != "network-manager" && "$2" != "neuropil" ]]; then
            echo "Error: Invalid component. Use 'network-manager' or 'neuropil'."
            usage
        fi
        COMPONENT="$2"
    elif [ "$1" == "uninstall" ]; then
        ACTION="uninstall"
    else
        usage
    fi
}

# Ensure there is at least one argument
if [ $# -eq 0 ]; then
    usage
fi

# Validate the arguments
validate_arguments "$1" "$2"

# Check dependencies and process based on the action
check_dependencies

if [ "$ACTION" == "install" ]; then
    echo "Install FLUIDOS"
    install_fluidos "$COMPONENT"

elif [ "$ACTION" == "uninstall" ]; then
    echo "Uninstall FLUIDOS"
    uninstall
fi

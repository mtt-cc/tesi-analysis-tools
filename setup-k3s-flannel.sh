#!/bin/bash

# Environment variables

# Global
CLUSTER_NAME=tesi-ccl

# Multus
CNI_PLUGINS_VERSION="v1.5.1"
CNI_PLUGINS=("bridge" "loopback" "host-device" "macvlan")

# MetalLB
METALLB_ADDRESS_POOL_NAME=$CLUSTER_NAME-metallb-address-pool
METALLB_IF_NAME=eth0
NODE_IP=$(ip a | grep $METALLB_IF_NAME | grep inet | awk '{print $2}' | cut -d '/' -f 1)
#NODE_IP="192.168.0.125" # For edge device

# Prometheus and Grafana
GRAFANA_NODE_PORT=30003
PROMETHEUS_NODE_PORT=30090

# Flags
ACTION=""
CLUSTER_TYPE=""

install_requirements() {
    echo "Install requirements"
    
    # Update the package list
    sudo apt update &>/dev/null
    
    # Install the required packages
    sudo apt install -y curl gpg &>/dev/null
    curl -s https://baltocdn.com/helm/signing.asc | gpg --dearmor | sudo tee /usr/share/keyrings/helm.gpg > /dev/null
    sudo apt install apt-transport-https --yes &>/dev/null
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/helm.gpg] https://baltocdn.com/helm/stable/debian/ all main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list &>/dev/null
    
    # Update the package list again
    sudo apt update &>/dev/null

    # Install Helm
    sudo apt install -y helm &>/dev/null
}

disable_firewall() {
    sudo ufw disable &>/dev/null
}

change_hostname() {
    # Change the hostname
    echo "Change hostname to \"$CLUSTER_NAME\""
    sudo hostnamectl set-hostname $CLUSTER_NAME
}

install_k3s() {
    echo "Install K3s"

    # Install K3s without Ingress Controller and LoadBalancer
    echo "  - Install K3s without Ingress Controller and LoadBalancer"
    curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--disable=traefik --disable=servicelb" K3S_KUBECONFIG_MODE="644" sh - &>/dev/null

    # Export the KUBECONFIG
    export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
    # Add KUBECONFIG to .bashrc if it's not already present
    grep -qxF 'export KUBECONFIG=/etc/rancher/k3s/k3s.yaml' ~/.bashrc || echo 'export KUBECONFIG=/etc/rancher/k3s/k3s.yaml' >> ~/.bashrc
    
    # Add alias for kubectl to .bashrc only if it's not already present
    grep -qxF 'alias k=kubectl' ~/.bashrc || echo 'alias k=kubectl' >> ~/.bashrc

    # Add kubectl bash completion sourcing to .bashrc only if it's not already present
    grep -qxF 'source <(kubectl completion bash)' ~/.bashrc || echo 'source <(kubectl completion bash)' >> ~/.bashrc

    # Add kubectl completion for the alias 'k' only to .bashrc if it's not already present
    grep -qxF 'complete -F __start_kubectl k' ~/.bashrc || echo 'complete -F __start_kubectl k' >> ~/.bashrc

    # Wait until resources are available in the kube-system namespace
    while true; do
        pod_count=$(kubectl get pods -n kube-system --no-headers 2>/dev/null | wc -l)
        if [ "$pod_count" -gt 0 ]; then
            echo "Resources found in kube-system namespace."
            break
        else
            echo "Waiting for resources to appear in kube-system namespace..."
            sleep 5
        fi
    done

    # Wait for all pods to become ready
    kubectl wait --for=condition=ready pod -n kube-system --all --timeout=90s &>/dev/null
}

install_multus() {
    echo "Install Multus"

    helm repo add rke2-charts https://rke2-charts.rancher.io &>/dev/null
    helm repo update &>/dev/null

    kubectl apply -f multus-helm.yaml &>/dev/null

    # Wait until Multus resources are available in the kube-system namespace
    while true; do
        multus_pod_count=$(kubectl get pods -n kube-system -l app=rke2-multus --no-headers 2>/dev/null | wc -l)
        if [ "$multus_pod_count" -gt 0 ]; then
            echo "Multus pods found in kube-system namespace."
            break
        else
            echo "Waiting for Multus pods to appear in kube-system namespace..."
            sleep 5
        fi
    done

    # Wait for all Multus pods to become ready
    kubectl wait --for=condition=ready pod -n kube-system -l app=rke2-multus --timeout=90s &>/dev/null

    echo "  - Patch Multus DaemonSet to remove CPU and memory limits"
    # Patch the Multus DaemonSet to remove CPU and memory limits
    kubectl patch daemonset -n kube-system multus --type=json -p='[
        {
            "op": "remove",
            "path": "/spec/template/spec/containers/0/resources/limits/cpu"
        },
        {
            "op": "remove",
            "path": "/spec/template/spec/containers/0/resources/limits/memory"
        }
    ]' &>/dev/null

    # Wait until Multus resources are available in the kube-system namespace
    while true; do
        multus_pod_count=$(kubectl get pods -n kube-system -l app=rke2-multus --no-headers 2>/dev/null | wc -l)
        if [ "$multus_pod_count" -gt 0 ]; then
            echo "Multus pods found in kube-system namespace."
            break
        else
            echo "Waiting for Multus pods to appear in kube-system namespace..."
            sleep 5
        fi
    done

    # Wait for all Multus pods to become ready
    kubectl wait --for=condition=ready pod -n kube-system -l app=rke2-multus --timeout=90s &>/dev/null

    echo "  - Install CNI plugins"
    
    # Create the CNI bin directory if it doesn't exist
    sudo mkdir -p /opt/cni/bin/ &>/dev/null
    sudo mkdir -p /var/lib/rancher/k3s/data/cni &>/dev/null
    
    # Download the latest version of the CNI plugins
    curl -s -L "https://github.com/containernetworking/plugins/releases/download/${CNI_PLUGINS_VERSION}/cni-plugins-linux-amd64-${CNI_PLUGINS_VERSION}.tgz" -o /tmp/cni-plugins.tgz
    
    # Extract the CNI plugins temporarily
    mkdir -p /tmp/cni-plugins &>/dev/null
    tar -xzvf /tmp/cni-plugins.tgz -C /tmp/cni-plugins/ &>/dev/null
    
    # Move only the required plugins to /opt/cni/bin/
    for plugin in "${CNI_PLUGINS[@]}"; do
        sudo cp /tmp/cni-plugins/$plugin /opt/cni/bin/
        sudo cp /tmp/cni-plugins/$plugin /var/lib/rancher/k3s/data/cni
    done
    
    # Clean up the temporary files
    rm -rf /tmp/cni-plugins &>/dev/null
    rm /tmp/cni-plugins.tgz &>/dev/null

    # Patch Multus DaemonSet to not schedule on Liqo nodes
    kubectl patch daemonset multus -n kube-system --type='json' -p='[{"op": "add", "path": "/spec/template/spec/affinity", "value": {"nodeAffinity": {"requiredDuringSchedulingIgnoredDuringExecution": {"nodeSelectorTerms": [{"matchExpressions": [{"key": "liqo.io/type", "operator": "DoesNotExist"}]}]}}}}]' &>/dev/null
    # Rollout the Multus DaemonSet
    kubectl rollout restart daemonset multus -n kube-system &>/dev/null

    # Wait until Multus resources are available in the kube-system namespace
    while true; do
        multus_pod_count=$(kubectl get pods -n kube-system -l app=rke2-multus --no-headers 2>/dev/null | wc -l)
        if [ "$multus_pod_count" -gt 0 ]; then
            echo "Multus pods found in kube-system namespace."
            break
        else
            echo "Waiting for Multus pods to appear in kube-system namespace..."
            sleep 5
        fi
    done

    # Wait for all Multus pods to become ready
    kubectl wait --for=condition=ready pod -n kube-system -l app=rke2-multus --timeout=90s &>/dev/null
}

install_metallb() {
    echo "Install MetalLB"

    # Export the KUBECONFIG
    export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

    # Add the MetalLB Helm repository
    helm repo add metallb https://metallb.github.io/metallb &>/dev/null
    helm repo update &>/dev/null

    # Create metallb-memberlist secret
    #kubectl create secret generic metallb-memberlist \
    #    --from-literal=secretkey="$(openssl rand -base64 128)" \
    #    -n metallb-system

    # Install MetalLB with Helm
    echo "  - Install MetalLB with Helm"
    helm install metallb metallb/metallb --namespace metallb-system --create-namespace &>/dev/null
    
    # Wait until MetalLB deployments are available in the metallb-system namespace
    while true; do
        metallb_deployment_count=$(kubectl get deployments -n metallb-system -l app.kubernetes.io/name=metallb --no-headers 2>/dev/null | wc -l)
        if [ "$metallb_deployment_count" -gt 0 ]; then
            echo "MetalLB deployments found in metallb-system namespace."
            break
        else
            echo "Waiting for MetalLB deployments to appear in metallb-system namespace..."
            sleep 5
        fi
    done

    # Wait for MetalLB deployments to become available
    kubectl wait --namespace metallb-system --for=condition=available deployment --selector=app.kubernetes.io/name=metallb --timeout=300s &>/dev/null
    
    # Configure MetalLB
    echo "  - Configure MetalLB"
    # Setup address pool used by loadbalancers
    cat <<EOF | kubectl apply -f - > /dev/null
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
    name: $METALLB_ADDRESS_POOL_NAME
    namespace: metallb-system
spec:
    addresses:
        - $NODE_IP-$NODE_IP
EOF

  cat <<EOF | kubectl apply -f - > /dev/null
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
    name: $METALLB_ADDRESS_POOL_NAME
    namespace: metallb-system
EOF
}

install_inginx_ingress(){
    echo "Install Nginx Ingress Controller"

    # Export the KUBECONFIG
    export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

    # Add the Nginx Ingress Controller Helm repository
    helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx &>/dev/null
    helm repo update &>/dev/null

    # Install Nginx Ingress Controller with Helm
    echo "  - Install Nginx Ingress Controller with Helm"
    helm install ingress-nginx ingress-nginx \
        --repo https://kubernetes.github.io/ingress-nginx \
        --namespace ingress-nginx \
        --create-namespace \
        &>/dev/null
}

apply_can0() {
    # Apply the can0 network interface
    echo "Apply the can0 network interface"
    kubectl apply -f ./multus-can0.yaml &>/dev/null
}

install_prometheus_grafana() {
    echo "Install Prometheus"

    # Export the KUBECONFIG
    export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

    # Add the Prometheus Helm repository
    echo "  - Checking if Prometheus Helm repository is already present"
    if helm repo list | grep -q "^prometheus"; then
        echo "  - Prometheus Helm repository is already added"
    else
        echo "  - Adding Prometheus Helm repository"
        helm repo add prometheus-community https://prometheus-community.github.io/helm-charts 1>/dev/null
        helm repo update 1>/dev/null
        if [ $? -ne 0 ]; then
            echo "Error: Failed to add or update the Prometheus Helm repository"
            exit 1
        fi
    fi

    # Install Prometheus with Grafana (to scrape Liqo metrics)
    helm install prometheus prometheus-community/kube-prometheus-stack \
    --namespace prometheus \
    --create-namespace \
    --set grafana.service.type=NodePort \
    --set grafana.service.nodePort=$GRAFANA_NODE_PORT \
    --set prometheus.service.type=NodePort \
    --set prometheus.service.nodePort=$PROMETHEUS_NODE_PORT \
    --set prometheus.prometheusSpec.ruleSelectorNilUsesHelmValues=false \
    --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
    --set prometheus.prometheusSpec.podMonitorSelectorNilUsesHelmValues=false \
    --set prometheus.prometheusSpec.probeSelectorNilUsesHelmValues=false


    # Wait until Prometheus pods are available in the prometheus namespace
    while true; do
        prometheus_pod_count=$(kubectl get pods -n prometheus -l app.kubernetes.io/instance=prometheus --no-headers 2>/dev/null | wc -l)
        if [ "$prometheus_pod_count" -gt 0 ]; then
            echo "Prometheus pods found in prometheus namespace."
            break
        else
            echo "Waiting for Prometheus pods to appear in prometheus namespace..."
            sleep 5
        fi
    done

    # Wait for Prometheus pods to become ready
    kubectl wait --namespace prometheus --for=condition=ready pod --selector=app.kubernetes.io/instance=prometheus --timeout=300s &>/dev/null

    # Get the Grafana admin password (prom-operator)
    kubectl get secret -n prometheus prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 --decode
}

uninstall_prometheus_grafana() {
    echo "Uninstall Prometheus and Grafana"
    helm uninstall prometheus --namespace prometheus 1>/dev/null
}

uninstall() {
    # Export the KUBECONFIG
    export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

    # Uninstall Prometheus and Grafana
    if helm list -A | grep -q prometheus; then
        echo "  - Uninstall Prometheus and Grafana"
        helm uninstall prometheus --namespace prometheus 1>/dev/null
    fi

    # Uninstall NGINX Ingress Controller
    if helm list -A | grep -q ingress-nginx; then
        echo "  - Uninstall Nginx Ingress Controller"
        helm uninstall ingress-nginx --namespace ingress-nginx &>/dev/null
    fi

    # Uninstall MetalLB
    if helm list -A | grep -q metallb; then
        echo "  - Uninstall MetalLB"
        helm uninstall metallb --namespace metallb-system &>/dev/null
    fi

    # Uninstall Multus
    if kubectl get daemonset -n kube-system multus &>/dev/null; then
        echo "  - Uninstall Multus"
        helm uninstall multus -n kube-system &>/dev/null
    fi

    # Uninstall K3s
    echo "  - Uninstall K3s"
    /usr/local/bin/k3s-uninstall.sh &>/dev/null

    echo "Uninstall complete"
}

# Function to display usage instructions
usage() {
    echo "Usage: $0 install [robot|cloud] or uninstall"
    echo ""
    echo "Commands:"
    echo "  install [robot|cloud]  Install the specified cluster type (robot or cloud)"
    echo "  uninstall              Uninstall the setup"
    echo ""
    echo "Examples:"
    echo "  $0 install robot       Install the robot configuration"
    echo "  $0 install cloud       Install the cloud configuration"
    echo "  $0 uninstall           Uninstall the current setup"
    exit 1
}

# Function to validate the command-line arguments
validate_arguments() {
    if [ "$1" == "install" ]; then
        if [ "$2" == "robot" ] || [ "$2" == "cloud" ]; then
            ACTION="install"
            CLUSTER_TYPE="$2"
        else
            usage
        fi
    elif [ "$1" == "uninstall" ]; then
        if [ -n "$2" ]; then
            usage
        else
            ACTION="uninstall"
        fi
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

# Process based on the action
if [ "$ACTION" == "install" ]; then
    echo "Install for \"$CLUSTER_TYPE\""

    install_requirements
    install_k3s
    if [ "$CLUSTER_TYPE" == "robot" ]; then
        install_multus
        # apply_can0
    fi
    # install_metallb
    #install_inginx_ingress
    # install_prometheus_grafana
    #install_liqo

elif [ "$ACTION" == "uninstall" ]; then
    echo "Uninstall"
    
    uninstall
fi
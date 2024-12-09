#!/bin/bash

# Environment variables

# Global
CLUSTER_NAME=tesi-ccl
LIQOCTL_VERSION="v0.10.0"

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

install_liqo() {
    echo "Install Liqo"

    # Export the KUBECONFIG
    export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

    # Install liqoctl
    echo "  - Install liqoctl"
    curl -s --fail -LS "https://github.com/liqotech/liqo/releases/download/$LIQOCTL_VERSION/liqoctl-linux-amd64.tar.gz" | tar -xz
    if [ $? -ne 0 ]; then
        echo "Error: Failed to download liqoctl"
        exit 1
    fi
    sudo install -o root -g root -m 0755 liqoctl /usr/local/bin/liqoctl 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install liqoctl"
        exit 1
    fi

    # Clean up the temporary files
    rm -f liqoctl 2>/dev/null
    rm -f LICENSE 2>/dev/null

    # Add liqoctl completion to .bashrc if it's not already present
    if ! grep -qxF 'source <(liqoctl completion bash)' ~/.bashrc; then
        echo 'source <(liqoctl completion bash)' >> ~/.bashrc
    fi

    # Install Liqo
    echo "  - Install Liqo"
    liqoctl install k3s --cluster-name "$CLUSTER_NAME" --timeout 10m
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install Liqo"
        exit 1
    fi
}

uninstall_liqo() {
    # Export the KUBECONFIG
    export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

    # Uninstall Liqo
    if command -v liqoctl &>/dev/null; then
        LIQO_STATUS=$(liqoctl status 2>/dev/null)

        # Check if the status is not empty
        if [ -n "$LIQO_STATUS" ]; then
            echo "  - Uninstall Liqo"
            liqoctl uninstall
            if [ $? -ne 0 ]; then
                echo "Error: Failed to uninstall Liqo"
                exit 1
            fi
        else
            echo "Liqo is not installed on this cluster."
        fi
    else
        echo "liqoctl command not found. Cannot uninstall."
    fi

    echo "Uninstall complete"
}

# Function to display usage instructions
usage() {
    echo "Usage: $0 install or uninstall"
    echo ""
    echo "Commands:"
    echo "  install             Install Liqo"
    echo "  uninstall           Uninstall Liqo"
    exit 1
}

# Function to validate the command-line argument
validate_argument() {
    if [ "$1" == "install" ]; then
        ACTION="install"
    elif [ "$1" == "uninstall" ]; then
        ACTION="uninstall"
    else
        usage
    fi
}

# Ensure there is one argument
if [ $# -eq 0 ]; then
    usage
fi

# Validate the argument
validate_argument "$1"

# Check dependencies before proceeding
check_dependencies

# Process based on the action
if [ "$ACTION" == "install" ]; then
    echo "Install Liqo"
    install_liqo
elif [ "$ACTION" == "uninstall" ]; then
    echo "Uninstall Liqo"
    uninstall_liqo
fi
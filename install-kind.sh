#!/bin/bash

# Function to print title
print_title() {
    echo "================================================"
    echo "$1"
    echo "================================================"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install KIND
install_kind() {
    print_title "Installing KIND..."
    
    # Check if KIND is already installed
    if command_exists kind; then
        echo "KIND is already installed. Version:"
        kind version
        return 0
    fi

    # Check if curl is installed
    if ! command_exists curl; then
        echo "Installing curl..."
        sudo apt-get update
        sudo apt-get install -y curl
    fi

    # Download and install KIND binary
    echo "Downloading KIND..."
    curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
    
    echo "Making KIND executable..."
    chmod +x ./kind
    
    echo "Moving KIND to /usr/local/bin..."
    sudo mv ./kind /usr/local/bin/kind

    # Verify installation
    if command_exists kind; then
        echo "KIND installed successfully. Version:"
        kind version
    else
        echo "KIND installation failed!"
        return 1
    fi
}

# Check if kubectl is installed (required for KIND)
check_kubectl() {
    print_title "Checking kubectl installation..."
    
    if ! command_exists kubectl; then
        echo "kubectl is not installed. Installing..."
        sudo apt-get update
        sudo apt-get install -y kubectl
    else
        echo "kubectl is already installed. Version:"
        kubectl version --client
    fi
}

# Main execution
main() {
    print_title "Starting KIND installation process..."
    
    # Check/Install kubectl first
    check_kubectl
    
    # Install KIND
    install_kind
    
    print_title "Installation complete!"
    echo "You can now create a cluster using: kind create cluster"
}

# Run the script
main
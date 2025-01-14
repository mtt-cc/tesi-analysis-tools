#!/bin/bash

# Script Configuration
CLUSTER_NAME="cluster1"
LIQO_SETUP_SCRIPT="setup-liqo.sh"
FLUIDOS_SETUP_SCRIPT="setup-fluidos-v0.1.1.sh"

# Ensure required tools are installed
command -v kind >/dev/null 2>&1 || { echo "Kind is not installed. Install it first."; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "Docker is not installed. Install it first."; exit 1; }

# Check if setup scripts exist
if [[ ! -f "$LIQO_SETUP_SCRIPT" || ! -f "$FLUIDOS_SETUP_SCRIPT" ]]; then
    echo "Both '$LIQO_SETUP_SCRIPT' and '$FLUIDOS_SETUP_SCRIPT' must exist in the current directory."
    exit 1
fi

# Step 1: Create the Kind Cluster
echo "Creating Kind cluster '$CLUSTER_NAME'..."
kind create cluster --name "$CLUSTER_NAME" --config - <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
EOF

# Step 2: Get the Control Plane Container Name
CONTROL_PLANE_CONTAINER=$(docker ps --filter "name=$CLUSTER_NAME-control-plane" --format "{{.Names}}")
if [[ -z "$CONTROL_PLANE_CONTAINER" ]]; then
    echo "Error: Could not find control plane container for cluster '$CLUSTER_NAME'."
    exit 1
fi

# Step 3: Copy the Setup Scripts into the Control Plane Container
echo "Copying setup scripts into the control plane container '$CONTROL_PLANE_CONTAINER'..."
docker cp "$LIQO_SETUP_SCRIPT" "$CONTROL_PLANE_CONTAINER:/tmp/$LIQO_SETUP_SCRIPT"
docker cp "$FLUIDOS_SETUP_SCRIPT" "$CONTROL_PLANE_CONTAINER:/tmp/$FLUIDOS_SETUP_SCRIPT"

# Step 4: Run the Setup Scripts
echo "Running '$LIQO_SETUP_SCRIPT' inside the container..."
docker exec -it "$CONTROL_PLANE_CONTAINER" bash -c "chmod +x /tmp/$LIQO_SETUP_SCRIPT && /tmp/$LIQO_SETUP_SCRIPT"

echo "Running '$FLUIDOS_SETUP_SCRIPT' inside the container..."
docker exec -it "$CONTROL_PLANE_CONTAINER" bash -c "chmod +x /tmp/$FLUIDOS_SETUP_SCRIPT && /tmp/$FLUIDOS_SETUP_SCRIPT"

# Step 5: Verify the Setup
echo "Verifying setup in Kind cluster '$CLUSTER_NAME'..."
kubectl --context "kind-$CLUSTER_NAME" get pods --all-namespaces

echo "Setup completed for Kind cluster '$CLUSTER_NAME'."

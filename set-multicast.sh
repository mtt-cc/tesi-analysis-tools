#!/bin/bash

# Ensure the script is run as root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root. Please use sudo."
    exit 1
fi

disable(){
    echo "Disabling multicast on all network interfaces..."

    # Get a list of all network interfaces (excluding loopback)
    interfaces=$(ls /sys/class/net | grep -v lo)

    # Iterate through each interface and disable multicast
    for iface in $interfaces; do
        echo "Disabling multicast on interface: $iface"
        ip link set dev "$iface" multicast off
        if [[ $? -eq 0 ]]; then
            echo "Multicast disabled on $iface successfully."
        else
            echo "Failed to disable multicast on $iface."
        fi
    done

    echo "All interfaces processed."
}

enable(){
    echo "enabling multicast on all network interfaces..."

    # Get a list of all network interfaces (excluding loopback)
    interfaces=$(ls /sys/class/net | grep -v lo)

    # Iterate through each interface and disable multicast
    for iface in $interfaces; do
        echo "enabling multicast on interface: $iface"
        ip link set dev "$iface" multicast on
        if [[ $? -eq 0 ]]; then
            echo "Multicast enabled on $iface successfully."
        else
            echo "Failed to enable multicast on $iface."
        fi
    done

    echo "All interfaces processed."
}



# Function to display usage instructions
usage() {
    echo "Usage: $0 install or uninstall"
    echo ""
    echo "Commands:"
    echo "  install             Install FLUIDOS"
    echo "  uninstall           Uninstall FLUIDOS"
    exit 1
}

# Function to validate the command-line argument
validate_argument() {
    if [ "$1" == "enable" ]; then
        ACTION="enable"
    elif [ "$1" == "disable" ]; then
        ACTION="disable"
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

if [ "$ACTION" == "enable" ]; then
    echo "disabling multicast"
    enable

elif [ "$ACTION" == "disable" ]; then
    echo "enabling multicast"
    disable
fi
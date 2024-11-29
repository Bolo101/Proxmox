#/bin/bash

{
        echo "auto lo"
        echo "iface lo inet loopback"
        echo
        echo "auto $SECOND_INTERFACE"
        echo "iface $SECOND_INTERFACE inet dhcp"
        echo
        echo "auto vmbr0"
        echo "iface vmbr0 inet static"
        echo "    address 192.168.122.146/24"
        echo "    gateway 192.168.122.1"
        echo "    bridge-ports $SECOND_INTERFACE"
        echo "    bridge-stp off"
        echo "    bridge-fd 0"
        echo
        echo "source /etc/network/interfaces.d/*"
    } > /etc/network/interfaces || { echo "Failed to write /etc/network/interfaces"; exit 1; }

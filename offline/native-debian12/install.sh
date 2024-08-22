#!/bin/bash

# Variables
PACKAGE_DIR="/root/packages/proxmox-ve-packages"
PACKAGE_KER="/root/packages/kernel-packages"

# Mise à jour du PATH
export PATH=$PATH:/sbin:/usr/sbin:/usr/local/sbin

  # Configurer l'adresse IP statique pour l'interface bridge
  cat <<EOL > /etc/network/interfaces
# This file describes the network interfaces available on your system
# and how to activate them. For more information, see interfaces(5).

# The loopback network interface
auto lo
iface lo inet loopback

# The primary network interface
#auto enp1s0
iface eno1 inet manual

# Bridge interface
auto vmbr0
iface vmbr0 inet static
    address 172.16.1.2/24
    bridge_ports eno1
    bridge_stp off
    bridge_fd 0
    
EOL

  # Mettre à jour le fichier /etc/hosts
  cat <<EOL > /etc/hosts
127.0.0.1       localhost
172.16.1.2/24      proxmox.penly.local proxmox

# The following lines are desirable for IPv6 capable hosts
::1     localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
EOL

# systemctl restart networking

echo "Network restarted"



# Installer Proxmox default kernel
if ! dpkg -l | grep -q 'proxmox-default-kernel'; then
  dpkg -i $PACKAGE_KER/*.deb
  apt -f install -y
  echo "Kernel installed. Rebooting..."
  systemctl reboot
fi

# Vérifier si le script a déjà été exécuté et passé l'installation du kernel
if [ -f /root/proxmox_kernel_installed ]; then
  export PATH=$PATH:/sbin:/usr/sbin:/usr/local/sbin
  
  # Installer les autres paquets
  dpkg -i $PACKAGE_DIR/*.deb
  apt -f install -y

  # Nettoyer les anciennes images de noyau
  apt remove -y linux-image-amd64 'linux-image-6.1*'
  update-grub
  apt remove os-prober -y
  
  # Configurer le stockage pour Proxmox
  cat <<EOL > /etc/pve/storage.cfg
dir: local
    path /var/lib/vz
    content iso,backup,vztmpl
    maxfiles 3
EOL



  # Appliquer les changements de réseau
  systemctl restart networking

  # Configurer le démarrage automatique des services Proxmox
  systemctl enable pvedaemon
  systemctl enable pveproxy
  systemctl enable pvestatd

  echo "Proxmox VE installation complete."
else
  # Marquer que le kernel a été installé et le script doit continuer après reboot
  touch /root/proxmox_kernel_installed
  echo "Please reboot the system to continue with the Proxmox VE installation."
fi

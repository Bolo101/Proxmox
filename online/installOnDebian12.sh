#!/bin/bash

# Définir le fichier de marquage
MARKER_FILE="/root/.script_ran_before_reboot"

if [ ! -f "$MARKER_FILE" ]; then
    # Première exécution du script

    # Supprimer le contenu du fichier /etc/apt/sources.list
    > /etc/apt/sources.list

    # Ajouter les dépôts Debian et Proxmox
    echo "deb http://ftp.debian.org/debian bookworm main contrib" >> /etc/apt/sources.list
    echo "deb http://ftp.debian.org/debian bookworm-updates main contrib" >> /etc/apt/sources.list
    echo "deb http://security.debian.org/debian-security bookworm-security main contrib" >> /etc/apt/sources.list
    echo "deb [arch=amd64] http://download.proxmox.com/debian/pve bookworm pve-no-subscription" > /etc/apt/sources.list.d/pve-install-repo.list

    # Ajouter la clé du dépôt Proxmox
    wget https://enterprise.proxmox.com/debian/proxmox-release-bookworm.gpg -O /etc/apt/trusted.gpg.d/proxmox-release-bookworm.gpg

    # Mettre à jour le dépôt et le système
    apt update && apt full-upgrade -y

    # Installer le noyau Proxmox
    apt install proxmox-default-kernel -y

    # Installer les paquets GRUB
    apt install grub2-common -y
    
    # Installer zenity pour la fênetre de dialogue
    apt install zenity -y

    # Installation des paquets Proxmox VE nécessaires
    apt install proxmox-ve postfix open-iscsi chrony -y

    # Créer un fichier de marquage pour indiquer que le script a été exécuté avant le redémarrage
    touch "$MARKER_FILE"

    # Redémarrer la machine pour appliquer le noyau Proxmox
    systemctl reboot
else
    # Exécution du script après le redémarrage
    # Ajouter /usr/sbin et /sbin au PATH
    export PATH=$PATH:/usr/sbin:/sbin
    # Supprimer le fichier de marquage
    rm "$MARKER_FILE"

    # Récupérer la seconde interface réseau
    SECOND_INTERFACE=$(ip -o link show | awk -F': ' '{print $2}' | sed -n '2p')

    # Demander à l'utilisateur de saisir le nom de domaine
    LAST_NAME=$(zenity --entry --title="Nom de domaine" --text="Veuillez entrer le nom de domaine en minuscule:")

    # Si l'utilisateur annule ou ne saisit rien, utiliser une valeur par défaut
    if [ -z "$LAST_NAME" ]; then
        LAST_NAME="default"
    fi

    # Suppression des anciens noyaux Debian
    apt remove linux-image-amd64 'linux-image-6.1*' -y

    # Mise à jour GRUB2
    update-grub

    # Suppression os-prober
    apt remove os-prober -y

    # Configurer le stockage pour Proxmox
    cat <<EOL > /etc/pve/storage.cfg
dir: local
    path /var/lib/vz
    content iso,backup,vztmpl
    maxfiles 3

EOL

    # Configurer l'adresse IP statique pour l'interface réseau principale
    cat <<EOL > /etc/network/interfaces
# This file describes the network interfaces available on your system
# and how to activate them. For more information, see interfaces(5).

# The loopback network interface
auto lo
iface lo inet loopback

# The primary network interface
auto $SECOND_INTERFACE
iface $SECOND_INTERFACE inet manual

# Bridge interface
auto vmbr0
iface vmbr0 inet static
    address 172.16.1.2
    netmask 255.255.255.0
    gateway 172.16.1.254
    bridge_ports $SECOND_INTERFACE
    bridge_stp off
    bridge_fd 0
EOL

    # Mettre à jour le fichier /etc/hosts
    cat <<EOL > /etc/hosts
127.0.0.1       localhost
172.16.1.1       proxmox.$LAST_NAME.local proxmox

# The following lines are desirable for IPv6 capable hosts
::1     localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
EOL

    # Appliquer les changements de réseau
    systemctl restart networking

    # Configurer le démarrage automatique des services Proxmox
    systemctl enable pvedaemon
    systemctl enable pveproxy
    systemctl enable pvestatd

    # Terminer les configurations de base
    apt autoremove -y
    
    # Supprimer zenity
    apt remove zenity --purge -y
    
    # Redémarrer les services Proxmox pour appliquer la nouvelle configuration
    poweroff
fi

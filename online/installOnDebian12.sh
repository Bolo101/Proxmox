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

    # Configurer le démarrage automatique des services Proxmox
    systemctl enable pvedaemon
    systemctl enable pveproxy
    systemctl enable pvestatd

    # Terminer les configurations de base
    apt autoremove -y
    
    # Redémarrer les services Proxmox pour appliquer la nouvelle configuration
    poweroff
fi

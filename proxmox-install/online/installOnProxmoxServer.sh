#!/bin/bash

# Création de l'utilisateur proxmox
echo "Création du profil utilisateur proxmox"
adduser proxmox
sleep 5

# Mise à jour des dépôts
echo "Mise à jour des dépôts"
apt update
sleep 5

# Installer xfce4, lightdm et chromium à partir du dépôt local
echo "Installation de xfce4, lightdm et chromium..."
apt-get install -y gnome chromium
sleep 5

# Configurer le clavier en français (azerty)
echo "Configuration du clavier en français (AZERTY)..."
echo 'XKBLAYOUT="fr"' > /etc/default/keyboard
dpkg-reconfigure -f noninteractive keyboard-configuration
sleep 5

# Redémarrer le service de configuration du clavier pour appliquer les modifications
service keyboard-setup restart
sleep 5

# Redémarrer le système
echo "Redémarrage du système..."
reboot

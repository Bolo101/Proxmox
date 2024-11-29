#!/bin/bash

# Define the package directory
PACKAGE_DIR="/root/package_downloads"

# Add user for login
adduser proxmox
echo "proxmox user added"
sleep 2

# Change to the package directory
cd "$PACKAGE_DIR" || { echo "Failed to change directory to $PACKAGE_DIR"; exit 1; }

# Step 1: Install all packages using dpkg, but don't stop on errors
echo "Installing packages..."
dpkg -i *.deb
echo "First package install"
sleep 2

# Step 2: Fix any missing dependencies
echo "Fixing missing dependencies..."
apt-get update --fix-missing
apt-get install -f
echo "Dependencies"
sleep 2

# Step 3: Re-run dpkg to make sure all packages are installed correctly
echo "Re-installing packages to ensure all dependencies are satisfied..."
dpkg -i *.deb
echo "Reinstalling done"
sleep 3

# Step 4: Clean up
echo "Cleaning up..."
apt-get clean
sleep 2

# Configurer le clavier en français (azerty)
echo "Configuration du clavier en français (AZERTY)..."
echo 'XKBLAYOUT="fr"' > /etc/default/keyboard
dpkg-reconfigure -f noninteractive keyboard-configuration
sleep 2

# Redémarrer le service de configuration du clavier pour appliquer les modifications
service keyboard-setup restart
sleep 2

# Activer lightdm pour le démarrage automatique
echo "Activation de lightdm..."
systemctl enable lightdm
sleep 2

# Redémarrer le système
echo "Redémarrage du système..."
reboot

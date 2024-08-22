#!/bin/bash

# Add user
adduser edf

# Package repository
PACKAGE_DIR="/root/package_downloads"

# Install chromium, lightdm, xfce4 and their dependendies from local repo
dpkg -i ${PACKAGE_DIR}/*.deb

# Fix dependencies
apt-get install -f

# Configure le clavier en français (azerty)
echo "Setting keyboard layout to French (AZERTY)..."
echo 'XKBLAYOUT="fr"' > /etc/default/keyboard
dpkg-reconfigure keyboard-configuration

# Restart keyboard service for applying changes
service keyboard-setup restart

# Enable lightdm.service for automatic startup
echo "Enabling lightdm..."
systemctl enable lightdm

# Restart system 
reboot

#!/bin/bash

# Define the package directory
PACKAGE_DIR="/root/chromium"

# Change to the package directory
cd "$PACKAGE_DIR" || { echo "Failed to change directory to $PACKAGE_DIR"; exit 1; }

# Step 1: Install all packages using dpkg, but don't stop on errors
echo "Installing chromium..."
dpkg -i *.deb
echo "First package install"
sleep 2

# Step 2: Fix any missing dependencies
echo "Fixing dependencies..."
apt-get install --fix-broken
echo "Dependencies"
sleep 2

# Redémarrer le système
echo "Redémarrage du système..."
reboot

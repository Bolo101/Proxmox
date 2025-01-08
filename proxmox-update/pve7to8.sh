#!/bin/bash

set -e

# Inform the user about the process
echo "Starting Proxmox VE 7 to 8 migration using no-subscription repository..."

# Update the current package sources
echo "Updating package sources..."
apt update || true  # Ignore errors like unauthorized repository
sleep 1

# Upgrade all current packages
echo "Upgrading current packages..."
apt dist-upgrade -y || true  # Ignore errors from unauthorized packages

# Update Debian sources from Bullseye to Bookworm
echo "Updating Debian sources from Bullseye to Bookworm..."
sed -i 's/bullseye/bookworm/g' /etc/apt/sources.list

# Remove existing Proxmox enterprise repository if it exists
echo "Removing Proxmox enterprise repository if present..."
rm -f /etc/apt/sources.list.d/pve-enterprise.list || true

# Add the Proxmox VE no-subscription repository
echo "Adding Proxmox VE 8 no-subscription repository..."
echo "deb http://download.proxmox.com/debian/pve bookworm pve-no-subscription" > /etc/apt/sources.list.d/pve-no-subscription.list

# Update package sources again
echo "Updating package sources with new repositories..."
apt update || true

# Upgrade all packages to the new version
echo "Upgrading to Proxmox VE 8 packages..."
apt dist-upgrade -y || true

# Clean up old packages and dependencies
echo "Cleaning up old packages..."
apt autoremove --purge -y || true

# Inform the user about the reboot
echo "Migration completed. The system will now reboot..."
sleep 2

# Reboot the system
reboot

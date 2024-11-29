#!/bin/bash

# Directory containing the copied .deb files from the USB
CACHE_DIR="/mnt/usb/apt-cache"

# Ensure the cache directory exists
if [ ! -d "$CACHE_DIR" ]; then
  echo "Error: Cache directory $CACHE_DIR does not exist!"
  exit 1
fi

# Install the .deb packages using dpkg
echo "Installing packages using dpkg -i..."
dpkg -i "$CACHE_DIR"/*.deb

# Fix any missing dependencies with apt-get
echo "Fixing dependencies with apt-get -f..."
apt-get -f install -y

# Final check for GNOME and Chromium installation
echo "Verifying installation..."
dpkg -l | grep -E 'gnome|chromium'

echo "GNOME and Chromium installation completed successfully!"

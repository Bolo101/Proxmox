#!/bin/bash

CACHE_DIR="/mnt/usb/apt-cache"
mkdir -p "$CACHE_DIR"
apt update
apt-get -y --download-only install gnome chromium
cp /var/cache/apt/archives/*.deb "$CACHE_DIR"

echo "All packages and dependencies have been copied to $CACHE_DIR."

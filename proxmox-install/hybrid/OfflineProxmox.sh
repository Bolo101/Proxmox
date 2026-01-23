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

# Install the .deb packages using dpkg
echo "Installing packages using dpkg -i..."
dpkg -i "$CACHE_DIR"/*.deb

# Final check for GNOME and Chromium installation
echo "Verifying installation..."
dpkg -l | grep -E 'gnome|chromium'

# Disable sleep and suspend
echo "Disabling sleep and suspend modes..."

# Disable suspend in systemd
systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target

# Disable GNOME screensaver
gsettings set org.gnome.desktop.screensaver lock-enabled false
gsettings set org.gnome.desktop.session idle-delay 0

# Disable GNOME Power Management
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-timeout 0
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-timeout 0
gsettings set org.gnome.settings-daemon.plugins.power power-button-action "nothing"

# Disable GNOME automatic suspend (peut nécessiter dconf)
if command -v dconf &> /dev/null; then
  dconf write /org/gnome/settings-daemon/plugins/power/sleep-inactive-ac-timeout 0
  dconf write /org/gnome/settings-daemon/plugins/power/sleep-inactive-battery-timeout 0
fi

# Disable console blanking (kernel level)
echo "vm.power_action=nothing" >> /etc/sysctl.conf
sysctl -p

# Disable DPMS (Display Power Management Signaling)
echo 'Section "ServerFlags"
    Option "BlankTime" "0"
    Option "StandbyTime" "0"
    Option "SuspendTime" "0"
    Option "OffTime" "0"
EndSection' > /etc/X11/xorg.conf.d/10-disable-blanking.conf

echo "GNOME, Chromium et mise en veille installation completed successfully!"
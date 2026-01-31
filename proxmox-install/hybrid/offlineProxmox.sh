#!/bin/bash

set -euo pipefail

# Configuration
CACHE_DIR="/mnt/usb/apt-cache"
ARCHIVE_FILE="/root/usb.tar.gz"
GNOME_CONFIG_SCRIPT="/usr/local/bin/disable-sleep.sh"
POOL_DIR="$CACHE_DIR/pool/main"

# Logging setup
log_info() {
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2
}

log_success() {
    echo "[OK] $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_debug() {
    echo "[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log_error "This script must be run as root"
    exit 1
fi

# Trap errors
trap 'log_error "Script failed at line $LINENO"; exit 1' ERR

log_info "============================================================"
log_info "OFFLINE PROXMOX INSTALLATION"
log_info "============================================================"

# Step 1: Extract archive
log_info ""
log_info "[1/8] Extracting archive..."
if [ ! -f "$ARCHIVE_FILE" ]; then
    log_error "Archive file not found: $ARCHIVE_FILE"
    exit 1
fi

tar -xzf "$ARCHIVE_FILE" -C /mnt
log_success "Extraction completed"

# Step 2: Remove online APT sources
log_info ""
log_info "[2/8] Removing online sources..."

# Remove all files in sources.list.d
if [ -d "/etc/apt/sources.list.d" ]; then
    for source_file in /etc/apt/sources.list.d/*; do
        if [ -f "$source_file" ]; then
            rm -f "$source_file"
            log_debug "Removed $source_file"
        fi
    done
fi

# Clear sources.list
echo "# Offline mode - no online sources" > /etc/apt/sources.list

log_success "Online sources removed"

# Step 3: Install packages offline
log_info ""
log_info "[3/8] Installing packages..."

if [ ! -d "$POOL_DIR" ]; then
    log_error "Pool directory not found: $POOL_DIR"
    exit 1
fi

deb_count=$(find "$POOL_DIR" -maxdepth 1 -name "*.deb" | wc -l)

if [ "$deb_count" -eq 0 ]; then
    log_error "No .deb files found in $POOL_DIR"
    exit 1
fi

log_info "Found $deb_count packages to install"

# Build dpkg install command
deb_files=$(find "$POOL_DIR" -maxdepth 1 -name "*.deb" | sort)

log_info "Installing all packages with dpkg..."
# Use --force-all to bypass dependency checks during install
if dpkg --force-all -i $deb_files 2>&1 | grep -q "error"; then
    log_error "dpkg encountered errors (dependencies may be broken)"
else
    log_success "All packages installed"
fi

# Try to configure any unconfigured packages
log_info "Attempting to fix dependencies with available packages..."
dpkg --configure -a || true

log_success "Package installation completed"

# Step 4: Configure keyboard
log_info ""
log_info "[4/8] Configuring keyboard..."

cat > /etc/default/keyboard <<EOF
XKBLAYOUT="fr"
EOF

dpkg-reconfigure -f noninteractive keyboard-configuration || true
sleep 2
service keyboard-setup restart || true
sleep 2

log_success "Keyboard configured"

# Step 5: Create sleep disable script
log_info ""
log_info "[5/8] Creating sleep disable script..."

mkdir -p "$(dirname "$GNOME_CONFIG_SCRIPT")"
cat > "$GNOME_CONFIG_SCRIPT" <<'EOF'
#!/bin/bash
set -e
echo "Disabling GNOME sleep and suspend..."
gsettings set org.gnome.desktop.screensaver lock-enabled false
gsettings set org.gnome.desktop.session idle-delay 0
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-timeout 0
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-timeout 0
gsettings set org.gnome.settings-daemon.plugins.power power-button-action nothing
dconf write /org/gnome/settings-daemon/plugins/power/sleep-inactive-ac-timeout 0
dconf write /org/gnome/settings-daemon/plugins/power/sleep-inactive-battery-timeout 0
echo "GNOME sleep/suspend disabled."
EOF

chmod 755 "$GNOME_CONFIG_SCRIPT"
log_success "Sleep disable script created"

# Step 6: Disable sleep at systemd level
log_info ""
log_info "[6/8] Disabling sleep at systemd level..."

for target in sleep.target suspend.target hibernate.target hybrid-sleep.target; do
    systemctl mask "$target" || true
done

# Add sysctl config
if ! grep -q "vm.power_action=nothing" /etc/sysctl.conf; then
    echo "vm.power_action=nothing" >> /etc/sysctl.conf
fi
sysctl -p || true

# X11 display configuration
mkdir -p /etc/X11/xorg.conf.d
cat > /etc/X11/xorg.conf.d/10-disable-blanking.conf <<EOF
Section "ServerFlags"
Option "BlankTime" "0"
Option "StandbyTime" "0"
Option "SuspendTime" "0"
Option "OffTime" "0"
EndSection
EOF

log_success "Sleep disabled at systemd level"

# Step 7: Create user
log_info ""
log_info "[7/8] Creating user..."

read -p "Enter username for new account: " username

if [ -z "$username" ]; then
    log_error "No username provided. Skipping user creation."
    username=""
else
    # Validate username format
    if ! [[ "$username" =~ ^[a-zA-Z0-9_-]+$ ]] || [[ "$username" =~ ^- ]]; then
        log_error "Invalid username format."
        username=""
    else
        # Create user
        if useradd -m -s /bin/bash "$username" 2>/dev/null; then
            log_success "User '$username' created"
            
            log_info "Setting password for user '$username'..."
            passwd "$username" || true
            
            # Add sudo privileges for sleep script
            mkdir -p /etc/sudoers.d
            cat > "/etc/sudoers.d/${username}-gnome" <<EOF
$username ALL=(ALL) NOPASSWD: $GNOME_CONFIG_SCRIPT
EOF
            chmod 440 "/etc/sudoers.d/${username}-gnome"
        else
            log_error "Failed to create user '$username'"
            username=""
        fi
    fi
fi

# Step 8: Configure GNOME autostart
if [ -n "$username" ]; then
    log_info ""
    log_info "[8/8] Configuring GNOME..."
    
    autostart_dir="/home/$username/.config/autostart"
    mkdir -p "$autostart_dir"
    
    cat > "$autostart_dir/disable-sleep.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Disable Sleep Settings
Exec=$GNOME_CONFIG_SCRIPT
AutoStart=true
Hidden=false
X-GNOME-Autostart-enabled=true
EOF
    
    chown -R "$username:$username" "/home/$username/.config"
    
    log_success "GNOME autostart configured"
fi

# Final summary
log_info ""
log_info "============================================================"
log_success "Installation completed!"
if [ -n "$username" ]; then
    log_info "User '$username' created"
    log_info "GNOME will auto-configure on first login"
fi
log_info "============================================================"
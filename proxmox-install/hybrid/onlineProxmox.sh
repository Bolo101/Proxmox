#!/bin/bash

set -euo pipefail

# Configuration
CACHE_DIR="/mnt/usb/apt-cache"
POOL_DIR="$CACHE_DIR/pool/main"
DISTS_DIR="$CACHE_DIR/dists/stable/main/binary-amd64"
ARCHIVE_FILE="usb.tar.gz"
INSTALL_FILE="/var/cache/apt/archives"
PACKAGES=("gnome" "chromium")

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

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log_error "This script must be run as root"
    exit 1
fi

# Trap errors
trap 'log_error "Script failed at line $LINENO"; exit 1' ERR

log_info "============================================================"
log_info "Starting APT repository creation"
log_info "============================================================"

# Step 1: Update and download packages
log_info ""
log_info "[1/5] Downloading packages..."
log_info "Updating apt package lists..."
apt update || true

for package in "${PACKAGES[@]}"; do
    log_info "Downloading package: $package with all dependencies..."
    if apt-get -y --download-only \
        -o APT::Get::Autoremove=false \
        install "$package"; then
        log_success "$package downloaded successfully"
    else
        log_error "Failed to download $package"
        exit 1
    fi
done

# Step 2: Copy packages to pool
log_info ""
log_info "[2/5] Copying packages to pool..."
mkdir -p "$POOL_DIR"

copied_count=0
for deb_file in $(find "$INSTALL_FILE" -maxdepth 1 -name "*.deb" | sort); do
    filename=$(basename "$deb_file")
    dest="$POOL_DIR/$filename"
    
    if [ ! -f "$dest" ]; then
        cp "$deb_file" "$dest"
    fi
    ((copied_count++))
done

log_success "Total packages: $copied_count"

# Step 3: Generate Packages index
log_info ""
log_info "[3/5] Generating Packages index..."
mkdir -p "$DISTS_DIR"
PACKAGES_FILE="$DISTS_DIR/Packages"

> "$PACKAGES_FILE"  # Clear file

deb_count=0
total_debs=$(find "$POOL_DIR" -maxdepth 1 -name "*.deb" | wc -l)

while IFS= read -r deb_file; do
    ((deb_count++))
    
    if [ $((deb_count % 100)) -eq 0 ]; then
        log_info "  Indexed $deb_count/$total_debs packages..."
    fi
    
    # Extract metadata from package
    dpkg-deb -f "$deb_file" >> "$PACKAGES_FILE"
    
    # Add relative path
    relative_path="${deb_file#$CACHE_DIR/}"
    echo "Filename: $relative_path" >> "$PACKAGES_FILE"
    
    # Add file size
    file_size=$(stat -c%s "$deb_file")
    echo "Size: $file_size" >> "$PACKAGES_FILE"
    
    # Calculate and add MD5
    md5=$(md5sum "$deb_file" | awk '{print $1}')
    echo "MD5sum: $md5" >> "$PACKAGES_FILE"
    
    echo "" >> "$PACKAGES_FILE"
    
done < <(find "$POOL_DIR" -maxdepth 1 -name "*.deb" | sort)

log_success "Packages file created with $total_debs entries"

# Create Packages.gz
log_info "Compressing Packages.gz..."
gzip -k "$PACKAGES_FILE" -f
log_success "Packages.gz created"

# Step 4: Generate Release file
log_info ""
log_info "[4/5] Generating Release file..."
RELEASE_FILE="$CACHE_DIR/dists/stable/Release"
mkdir -p "$(dirname "$RELEASE_FILE")"

# Calculate checksums
packages_md5=$(md5sum "$PACKAGES_FILE" | awk '{print $1}')
packages_size=$(stat -c%s "$PACKAGES_FILE")
packages_gz_md5=$(md5sum "${PACKAGES_FILE}.gz" | awk '{print $1}')
packages_gz_size=$(stat -c%s "${PACKAGES_FILE}.gz")

packages_sha1=$(sha1sum "$PACKAGES_FILE" | awk '{print $1}')
packages_gz_sha1=$(sha1sum "${PACKAGES_FILE}.gz" | awk '{print $1}')

packages_sha256=$(sha256sum "$PACKAGES_FILE" | awk '{print $1}')
packages_gz_sha256=$(sha256sum "${PACKAGES_FILE}.gz" | awk '{print $1}')

today=$(date -u '+%a, %d %b %Y %H:%M:%S UTC')

cat > "$RELEASE_FILE" <<EOF
Origin: LocalProxmox
Label: Local Proxmox Repository
Suite: stable
Codename: bookworm
Date: $today
Architectures: amd64
Components: main
Description: Local offline APT repository
MD5Sum:
 $packages_md5 $packages_size main/binary-amd64/Packages
 $packages_gz_md5 $packages_gz_size main/binary-amd64/Packages.gz
SHA1:
 $packages_sha1 $packages_size main/binary-amd64/Packages
 $packages_gz_sha1 $packages_gz_size main/binary-amd64/Packages.gz
SHA256:
 $packages_sha256 $packages_size main/binary-amd64/Packages
 $packages_gz_sha256 $packages_gz_size main/binary-amd64/Packages.gz
EOF

log_success "Release file created"

# Step 5: Verify repository
log_info ""
log_info "[5/5] Verifying repository..."

all_good=true
checks=(
    "$POOL_DIR:Pool directory"
    "$PACKAGES_FILE:Packages file"
    "${PACKAGES_FILE}.gz:Packages.gz file"
    "$RELEASE_FILE:Release file"
)

for check in "${checks[@]}"; do
    path="${check%:*}"
    name="${check#*:}"
    
    if [ -e "$path" ]; then
        log_success "$name exists"
    else
        log_error "$name missing: $path"
        all_good=false
    fi
done

if [ "$all_good" = false ]; then
    log_error "Repository verification failed"
    exit 1
fi

# Create archive
log_info ""
log_info "Creating archive $ARCHIVE_FILE..."
tar -czf "$ARCHIVE_FILE" -C /mnt usb

archive_size=$(du -h "$ARCHIVE_FILE" | awk '{print $1}')
log_success "Archive created: $ARCHIVE_FILE ($archive_size)"

log_info ""
log_info "============================================================"
log_success "Setup completed successfully!"
log_success "Archive ready: $ARCHIVE_FILE"
log_info "============================================================"
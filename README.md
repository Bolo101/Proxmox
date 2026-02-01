# Proxmox Management Scripts

A collection of scripts to manage Proxmox VE installations and updates, including solutions for both online and offline environments.

## Features

- Install Proxmox graphical interface (GNOME + Chromium) for web administration
- Support for both online and offline installations
- Automated upgrade from Proxmox VE 7 to 8
- Available in both Bash and Python implementations
- Comprehensive logging and error handling
- Automatic user account creation with GNOME integration
- Sleep/suspend disable configuration at multiple levels

## Repository Structure

```
.
├── proxmox-install/
│   ├── hybrid/
│   │   ├── offlineProxmox.sh
│   │   └── onlineProxmox.sh
│   ├── hybridPython/
│   │   ├── offlineProxmox.py
│   │   └── onlineProxmox.py
│   └── online/
│       └── installOnProxmoxServer.sh
├── proxmox-update/
│   └── pve7to8.sh
└── README.md
```

## Installation Methods

### 1. Online Installation (Direct Internet Connection)

If your Proxmox server has internet access, use this method for a straightforward installation:

1. Navigate to the `proxmox-install/online` directory
2. Execute the installation script:
   ```bash
   bash installOnProxmoxServer.sh
   ```

### 2. Hybrid Installation (For Offline Servers)

The hybrid approach uses a two-step process: download packages on an internet-connected machine, then install offline. Choose between Bash or Python implementations.

#### 2a. Bash Implementation

User-friendly install procedure available [here](./proxmox-install/hybrid/README.md)

**Step 1: Package Download (Internet-Connected Machine)**

1. Copy `onlineProxmox.sh` to the `/root` directory:
   ```bash
   cp proxmox-install/hybrid/onlineProxmox.sh /root/
   ```

2. Execute the script to create the package archive:
   ```bash
   cd /root
   sudo bash onlineProxmox.sh
   ```

   This script will:
   - Update APT package lists
   - Download GNOME and Chromium packages with all dependencies
   - Copy packages to `/mnt/usb/apt-cache`
   - Generate Packages index files (Packages, Packages.gz)
   - Create Release file with checksums
   - Generate a compressed tar archive (`usb.tar.gz`)

**Step 2: Offline Installation**

1. Transfer both files to the offline Proxmox server's `/root` directory:
   - Generated `usb.tar.gz` archive
   - `OfflineProxmox.sh` script

2. Run the offline installation script on the target server:
   ```bash
   cd /root
   sudo bash OfflineProxmox.sh
   ```

   This script will:
   - Extract the archive
   - Remove all online APT sources
   - Install packages from local pool using dpkg
   - Configure French (AZERTY) keyboard layout
   - Disable sleep/suspend at multiple system levels
   - Create a new user account with sudo privileges
   - Configure GNOME autostart for the sleep disable script

#### 2b. Python Implementation

User-friendly install procedure available [here](./proxmox-install/hybridPython/README.md)

**Step 1: Package Download (Internet-Connected Machine)**

1. Copy `onlineProxmox.py` to the `/root` directory:
   ```bash
   cp proxmox-install/hybridPython/onlineProxmox.py /root/
   ```

2. Execute the script:
   ```bash
   cd /root
   sudo python3 onlineProxmox.py
   ```

   This script provides the same functionality as the Bash version with enhanced Python error handling and logging.

**Step 2: Offline Installation**

1. Transfer both files to the offline Proxmox server's `/root` directory:
   - Generated `usb.tar.gz` archive
   - `offlineProxmox.py` script

2. Run the offline installation script on the target server:
   ```bash
   cd /root
   sudo python3 offlineProxmox.py
   ```

   This script provides the same installation process as the Bash version with Python-based implementation.

### Step-by-Step Comparison

| Operation | Bash | Python |
|-----------|------|--------|
| Online Package Download | `onlineProxmox.sh` | `onlineProxmox.py` |
| Offline Installation | `OfflineProxmox.sh` (8 steps) | `offlineProxmox.py` (8 steps) |
| Error Handling | Bash trap mechanism | Python exception handling |
| Logging | Formatted timestamps (INFO/ERROR/OK) | Python logging module |
| User Interaction | Interactive user creation | Interactive user creation |

## Proxmox VE Update (7 to 8)

To upgrade your Proxmox VE installation from version 7 to 8:

1. Navigate to the `proxmox-update` directory
2. Execute the update script:
   ```bash
   cd proxmox-update
   sudo bash pve7to8.sh
   ```

Note: Internet connection is required for the update process.

## Installation Process Details

### Online Package Download (Step 1)

**Phases:**
1. Update APT cache
2. Download GNOME package with dependencies
3. Download Chromium package with dependencies
4. Copy all .deb files to pool directory
5. Generate Packages index (with metadata, sizes, MD5 hashes)
6. Generate Packages.gz (compressed index)
7. Generate Release file (with SHA1, SHA256 checksums)
8. Create final tar.gz archive

### Offline Installation (Step 2)

**Phases:**
1. Extract archive from USB/transferred media
2. Remove all online APT sources
3. Install packages using dpkg with dependency handling
4. Configure keyboard to French (AZERTY)
5. Create GNOME sleep disable script
6. Disable sleep at systemd level
7. Create new user account
8. Configure GNOME autostart

## Quick Tips

- Always verify script permissions before execution: `chmod +x script.sh`
- For offline installations, ensure all files are placed in the `/root` directory
- Back up your system before performing any major updates
- Python scripts require Python 3.x installed on the system
- Run all scripts with root privileges using `sudo`
- Monitor installation logs for any warnings or errors
- Keep USB or transfer media plugged in during offline installation
- After offline installation, the system will be fully functional without internet

## Configuration Details

### Keyboard Configuration
- Automatically configures to French (AZERTY) layout
- Can be modified by editing the keyboard configuration in the scripts

### Sleep/Suspend Disable
The scripts disable sleep/suspend at multiple levels:
- **systemd**: Masks sleep.target, suspend.target, hibernate.target, hybrid-sleep.target
- **GNOME Settings**: Disables idle delay and timeout settings
- **sysctl**: Adds power action configuration
- **X11**: Disables DPMS (Display Power Management Signaling)
- **Autostart**: Runs configuration script on user login

### User Account Setup
- Interactive username input with validation
- Password setup during installation
- Sudo privileges for sleep configuration script
- GNOME autostart configuration for the user

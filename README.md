# 🖥️ Proxmox Management Scripts

A collection of scripts to manage Proxmox VE installations and updates, including solutions for both online and offline environments.

## 🌟 Features

- Install Proxmox graphical interface (GNOME + Chromium) for web administration
- Support for both online and offline installations
- Automated upgrade from Proxmox VE 7 to 8
- Available in both Bash and Python implementations

## 📁 Repository Structure
```
proxmox-install/
├── hybrid/
│   ├── OfflineProxmox.sh
│   └── onlineProxmox.sh
├── hybridPython/
│   ├── offlineProxmox.py
│   └── onlineProxmox.py
└── online/
    └── installOnProxmoxServer.sh
proxmox-update/
└── pve7to8.sh
```

## 🚀 Installation Methods

### 1. Online Installation (Direct Internet Connection)
If your Proxmox server has internet access, use this method for a straightforward installation:

1. Navigate to the `proxmox-install/online` directory
2. Execute the installation script:
   ```bash
   bash installOnProxmoxServer.sh
   ```

### 2. Hybrid Installation (For Offline Servers)

#### Bash Implementation
**Step 1: Package Download (Internet-Connected Machine)**
1. Copy `onlineProxmox.sh` to the `/root` directory
2. Execute the script to create the package archive:
   ```bash
   cd /root
   bash onlineProxmox.sh
   ```

**Step 2: Offline Installation**
1. Transfer both the generated tar archive and `OfflineProxmox.sh` to the `/root` directory of the offline Proxmox server
2. Run the offline installation script:
   ```bash
   cd /root
   bash OfflineProxmox.sh
   ```

#### Python Implementation
**Step 1: Package Download (Internet-Connected Machine)**
1. Copy `onlineProxmox.py` to the `/root` directory
2. Execute the script:
   ```bash
   cd /root
   python3 onlineProxmox.py
   ```

**Step 2: Offline Installation**
1. Transfer both the generated tar archive and `offlineProxmox.py` to the `/root` directory of the offline Proxmox server
2. Run the offline installation script:
   ```bash
   cd /root
   python3 offlineProxmox.py
   ```

## 🔄 Proxmox VE Update (7 to 8)

To upgrade your Proxmox VE installation from version 7 to 8:

1. Navigate to the `proxmox-update` directory
2. Execute the update script:
   ```bash
   bash pve7to8.sh
   ```

⚠️ **Note**: Internet connection is required for the update process.

## ⚡ Quick Tips

- Always verify script permissions before execution
- For offline installations, ensure all files are placed in the `/root` directory
- Back up your system before performing any major updates
- Python scripts require Python 3.x installed on the system

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📝 License

This project is open-source and available under the MIT License.
# User Guide

## Overview

The two provided scripts allow for the installation of a lightweight desktop environment and a lightweight session manager. These scripts install LightDM, XFCE4, Chromium, and all associated dependencies. The proposed solution enables the administration of a Proxmox-VE server directly from the server, without the need for an additional machine on the network to access the web administration interface. The web administration interface becomes directly accessible from the Proxmox-VE server via this configuration. Below are the installation steps to be performed on a Proxmox-VE server installed via the installation ISO.

# Installation Preparation

- Download the zip file `native-proxmox.zip` to your computer and unzip the file.
- Transfer the `native-proxmox` folder to a USB drive.

# Installation

- Plug the USB drive into the Proxmox server.
- Detect the USB drive using the `lsblk` command:
```bash
lsblk
```

* Mount the USB device.
```bash
mount /dev/sdXX /mnt 
// Replace XX with the output from the `lsblk` command corresponding to the USB drive.
```

* Transfer the scripts and packages from the USB drive to the server:
```bash
rsync -a /mnt/native-proxmox/ /root/ --progress
```

* Execute the script0.sh script:
```bash
./script0.sh
```

* Set a password for the user 'proxmox'.
This user will allow access to a graphical session.

* Follow the instructions and confirm with 'y' for all validation prompts.

* After rebooting, you will be presented with a graphical login screen.

* Log in as the user 'proxmox'.

* Open a terminal.

* Obtain the IP address of the system:
```bash
ip a
```
Note the IP of vmbr0.

* Switch to the 'root' user:
```
su -
```

* Execute the script1.sh script:
```bash
./script1.sh
```

* After rebooting, log in again as 'proxmox'.

* Open the web browser.

* Connect to the server by entering the system's IP address with the connection port.
Ex: 192.168.2.13:8006

* Log in to the graphical administration interface.
Use the username 'root' and the password set during the installation of Proxmox-VE.


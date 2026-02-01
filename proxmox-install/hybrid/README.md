# Proxmox GNOME Installation - Simple Guide (Bash)

## Step 1: Download the scripts

On your computer, download the 2 files from the repository:
- `onlineProxmox.sh` (in `proxmox-install/hybrid/`)
- `offlineProxmox.sh` (in `proxmox-install/hybrid/`)

You can use wget to get targeted files as root user on your freshly installed Promox-VE:

```bash
wget https://github.com/Bolo101/Proxmox/blob/master/proxmox-install/hybrid/offlineProxmox.sh
wget https://github.com/Bolo101/Proxmox/blob/master/proxmox-install/hybrid/onlineProxmox.sh
```

## Step 2: Create the archive (machine with Internet)

**Option A: Run the online script**

```bash
# Make it executable
chmod +x /root/onlineProxmox.sh

# Execute it
sudo /root/onlineProxmox.sh

# This will create /root/usb.tar.gz (4-5 GB, 1-3 hours)
```

**Option B: Download from archive.org**

If you don't have a Linux machine with Internet, download the `usb.tar.gz` archive from [archive.org](https://archive.org/details/proxmoxGUI-offline)

## Step 3: Prepare the USB drive

On your computer:

```bash
# Plug in the USB drive
# Find it with:
lsblk

# Mount it (replace sdX1 with your drive):
sudo mkdir -p /mnt/usb
sudo mount /dev/sdX1 /mnt/usb

# Copy the files:
sudo cp /root/usb.tar.gz /mnt/usb/
sudo cp /root/offlineProxmox.sh /mnt/usb/

# Verify:
ls -lh /mnt/usb/

# Unmount:
sudo umount /mnt/usb
```

## Step 4: Install on the offline server

On the offline Proxmox server:

```bash
# Plug in the USB drive
# Find it with:
lsblk

# Mount it:
sudo mkdir -p /mnt/usb
sudo mount /dev/sdX1 /mnt/usb

# Copy to /root:
sudo cp /mnt/usb/* /root/

# Unmount:
sudo umount /mnt/usb

# Make the script executable:
sudo chmod +x /root/offlineProxmox.sh

# Execute:
sudo /root/offlineProxmox.sh

# During execution, enter a username and password
```

## Step 5: Restart and finish

```bash
# Restart the server
reboot

# After restart, log in with the created user
# and execute the sleep disable script:
su -
bash /usr/local/bin/disable-sleep.sh
```

## Done!

GNOME and Chromium are installed and sleep mode is disabled.
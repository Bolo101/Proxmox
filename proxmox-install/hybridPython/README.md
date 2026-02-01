# Proxmox GNOME Installation - Simple Guide (Python)

## Step 1: Download the scripts

On your computer, download the 2 files from the repository:
- `onlineProxmox.py` (in `proxmox-install/hybridPython/`)
- `offlineProxmox.py` (in `proxmox-install/hybridPython/`)

You can use wget to get targeted files as root user on your freshly installed Promox-VE:

```bash
wget https://github.com/Bolo101/Proxmox/blob/master/proxmox-install/hybridPython/offlineProxmox.py
wget https://github.com/Bolo101/Proxmox/blob/master/proxmox-install/hybridPython/onlineProxmox.py
```

## Step 2: Create the archive (machine with Internet)

**Option A: Run the online script**

```bash
# Make it executable
chmod +x /root/onlineProxmox.py

# Execute it
sudo python3 /root/onlineProxmox.py

```

**Option B: Download from archive.org**

If you don't have a Linux machine with Internet, download the `usb.tar.gz` archive from archive.org.

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
sudo cp /root/offlineProxmox.py /mnt/usb/

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
mkdir -p /mnt/usb
mount /dev/sdX1 /mnt/usb

# Copy to /root:
cp /mnt/usb/* /root/

# Unmount:
umount /mnt/usb

# Make the script executable:
chmod +x /root/offlineProxmox.py

# Execute:
python3 /root/offlineProxmox.py

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
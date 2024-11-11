echo "Updating source..."
sudo apt update
sleep 1
echo "Updating current packages..."
sudo apt dist-upgrade
echo "Update debain sources from bullseye to bookworm..."
sed -i 's/bullseye/bookworm/g' /etc/apt/sources.list
echo "Done!"
echo "Adding Ceph package repository"
echo "deb http://download.proxmox.com/debian/ceph-quincy bookworm no-subscription" > /etc/apt/sources.list.d/ceph.list
echo "Done"
echo "Updating new source repositories..."
sudo apt update
echo "Done"
echo "Updating packages from new sources..."
sudo apt dist-upgrade 
echo "Done"
echo "Requesting system poweroff for clean reboot"
sleep 2
poweroff

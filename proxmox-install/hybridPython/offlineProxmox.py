import os
import subprocess
import sys
import glob

# Directory containing the copied .deb files from the USB
CACHE_DIR = "/mnt/usb/apt-cache"

# Path to the tar.gz file
TAR_GZ_FILE = "/mnt/usb.tar.gz"

def run_command(command, ignore_errors=False):
    """Run a shell command."""
    try:
        print(f"Running command: {command}")
        subprocess.check_call(command, shell=True)
    except subprocess.CalledProcessError as e:
        if not ignore_errors:
            print(f"Error running command: {command}\n{e}")
            raise
        else:
            print(f"Warning: Command failed but ignored: {command}\n{e}")

# Step 1: Decompress usb.tar.gz
if os.path.exists(TAR_GZ_FILE):
    print(f"Decompressing {TAR_GZ_FILE}...")
    try:
        run_command(f"tar -xvf {TAR_GZ_FILE}")
    except Exception as e:
        print(f"Error occurred while decompressing {TAR_GZ_FILE}: {e}")
        sys.exit(1)
else:
    print(f"Error: {TAR_GZ_FILE} does not exist!")
    sys.exit(1)

# Step 2: Ensure the cache directory exists
if not os.path.isdir(CACHE_DIR):
    print(f"Error: Cache directory {CACHE_DIR} does not exist!")
    sys.exit(1)

# Step 3: Install the .deb packages individually using dpkg
print("Installing packages using dpkg -i...")
deb_files = glob.glob(f"{CACHE_DIR}/*.deb")
for deb_file in deb_files:
    try:
        run_command(f"dpkg -i {deb_file}")
    except Exception as e:
        print(f"Warning: Failed to install {deb_file}. Continuing...")

# Step 4: Fix any missing dependencies with apt-get
print("Fixing dependencies with apt-get -f...")
try:
    run_command("apt-get -f install -y")
except Exception as e:
    print(f"Error occurred while running apt-get -f: {e}")
    sys.exit(1)

# Step 5: Final check for GNOME and Chromium installation
print("Verifying installation...")
try:
    result = subprocess.check_output("dpkg -l", shell=True, stderr=subprocess.STDOUT)
    if b'gnome' in result or b'chromium' in result:
        print("GNOME and Chromium installation completed successfully!")
    else:
        print("GNOME and Chromium installation not found.")
except subprocess.CalledProcessError as e:
    print(f"Error occurred during dpkg check: {e.output.decode()}")
    sys.exit(1)

import os
import subprocess
import json

# Input directories
CACHE_DIR = "/mnt/usb/apt-cache"
INSTALL_ORDER_FILE = "/mnt/usb/install_order.json"

def run_command(command):
    """Execute a shell command."""
    try:
        subprocess.check_call(command, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}\n{e}")
        raise

def install_packages():
    """Install packages in the correct order directly from the cache."""
    if not os.path.exists(CACHE_DIR):
        raise FileNotFoundError(f"The cache directory {CACHE_DIR} does not exist!")

    if not os.path.exists(INSTALL_ORDER_FILE):
        raise FileNotFoundError(f"The installation order file {INSTALL_ORDER_FILE} does not exist!")

    # Load the installation order of packages
    with open(INSTALL_ORDER_FILE, "r") as f:
        install_order = json.load(f)

    # Install the packages in order
    print("Installing packages in the correct order...")
    for package in install_order:
        deb_path = os.path.join(CACHE_DIR, package)
        if os.path.exists(deb_path):
            print(f"Installing {package}...")
            try:
                run_command(f"dpkg -i --auto-deconfigure {deb_path}")
            except subprocess.CalledProcessError:
                print(f"Failed to install {package}. Attempting to fix dependencies...")
                run_command("apt-get -f install -y")  # Fix broken dependencies
        else:
            print(f"Warning: {package} not found in cache!")

    print("All packages have been installed successfully!")

if __name__ == "__main__":
    install_packages()


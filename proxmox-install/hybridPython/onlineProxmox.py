import os
import subprocess
import json

# Configuration
CACHE_DIR = "/mnt/usb/apt-cache"
INSTALL_ORDER_FILE = "/mnt/usb/install_order.json"
ARCHIVE_FILE = "/mnt/usb/usb.tar.gz"

PACKAGES = ["gnome", "chromium"]

def run_command(command, ignore_errors=False):
    """Run a shell command."""
    try:
        subprocess.check_call(command, shell=True)
    except subprocess.CalledProcessError as e:
        if not ignore_errors:
            print(f"Error running command: {command}\n{e}")
            raise
        else:
            print(f"Warning: Command failed but ignored: {command}\n{e}")

def download_packages(packages):
    """Download packages and their dependencies."""
    os.makedirs(CACHE_DIR, exist_ok=True)

    # Update apt package lists
    print("Updating apt package lists...")
    run_command("apt update", ignore_errors=True)

    install_order = []

    # Process each package
    for package in packages:
        print(f"Processing package: {package}")
        try:
            # Record install order
            command = f"apt-get -y --print-uris --reinstall install {package} | grep -oP \"'(.*?)'\" | sed \"s/'//g\""
            package_urls = subprocess.check_output(command, shell=True, text=True).splitlines()

            for url in package_urls:
                deb_name = os.path.basename(url)
                if deb_name not in install_order:
                    install_order.append(deb_name)

            # Download packages
            run_command(f"apt-get -y --download-only install {package}")

        except subprocess.CalledProcessError as e:
            print(f"Failed to process {package}: {e}")
            continue

    # Save install order
    print(f"Saving install order to {INSTALL_ORDER_FILE}...")
    with open(INSTALL_ORDER_FILE, "w") as f:
        json.dump(install_order, f, indent=4)

    # Copy downloaded packages to the USB directory
    print(f"Copying downloaded packages to {CACHE_DIR}...")
    run_command(f"cp /var/cache/apt/archives/*.deb {CACHE_DIR}")

def create_archive():
    """Create a compressed tar archive of the USB directory."""
    print(f"Creating archive {ARCHIVE_FILE}...")
    run_command(f"tar -czvf {ARCHIVE_FILE} /mnt/usb")

if __name__ == "__main__":
    try:
        download_packages(PACKAGES)
        create_archive()
        print(f"Setup completed successfully. Archive created at {ARCHIVE_FILE}.")
    except Exception as e:
        print(f"Critical error: {e}")

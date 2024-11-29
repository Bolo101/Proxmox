import os
import subprocess
import json

# Directories
CACHE_DIR = "/mnt/usb/apt-cache"
INSTALL_ORDER_FILE = "/mnt/usb/install_order.json"

# Packages to install
PACKAGES = ["gnome", "chromium"]

def run_command(command, ignore_errors=False):
    """Execute a shell command."""
    try:
        subprocess.check_call(command, shell=True)
    except subprocess.CalledProcessError as e:
        if not ignore_errors:
            print(f"Error running command: {command}\n{e}")
            raise
        else:
            print(f"Warning: Command failed but ignored: {command}\n{e}")

def download_and_trace(packages):
    """Download and trace installation order."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    install_order = []

    print("Updating package lists...")
    # Allow errors during apt update
    run_command("apt update", ignore_errors=True)

    for package in packages:
        print(f"Installing {package} and tracing dependencies...")
        try:
            # Install package and capture the list of installed files
            command = (
                f"apt-get install -y --print-uris --reinstall {package} "
                "| grep -oP \"'/var/cache/apt/archives/[^\']+\\.deb'\" "
                "| sed \"s/'//g\""
            )
            deb_files = subprocess.check_output(command, shell=True, text=True).splitlines()
            for deb_file in deb_files:
                package_name = os.path.basename(deb_file)
                if package_name not in install_order:
                    install_order.append(package_name)

            # Actually install the package
            run_command(f"apt-get install -y {package}")
        except subprocess.CalledProcessError:
            print(f"Failed to install {package}. Check logs for more details.")

    # Save install order to JSON
    print("Saving install order to JSON...")
    with open(INSTALL_ORDER_FILE, "w") as f:
        json.dump(install_order, f, indent=4)

    # Copy downloaded packages to USB directory
    print("Copying downloaded packages to USB...")
    run_command(f"cp /var/cache/apt/archives/*.deb {CACHE_DIR}")

    print(f"Install order and packages saved to {CACHE_DIR} and {INSTALL_ORDER_FILE}.")

if __name__ == "__main__":
    try:
        download_and_trace(PACKAGES)
    except Exception as e:
        print(f"Critical error occurred: {e}")
        print("Exiting the script.")

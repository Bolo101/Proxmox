import os
import subprocess
import tarfile

# Configuration
CACHE_DIR = "/mnt/usb/apt-cache"
ARCHIVE_FILE = "/mnt/usb.tar.gz"

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

def extract_archive(archive_file, destination):
    """Extract the tar.gz archive."""
    print(f"Extracting archive {archive_file} to {destination}...")
    if not os.path.exists(archive_file):
        raise FileNotFoundError(f"Archive file not found: {archive_file}")
    with tarfile.open(archive_file, "r:gz") as tar:
        tar.extractall(path=destination)
    print("Extraction completed.")

def install_packages(package_dir):
    """Install .deb packages using dpkg in two passes."""
    if not os.path.exists(package_dir):
        raise FileNotFoundError(f"Package directory not found: {package_dir}")
    
    # Get the list of .deb files
    deb_files = [os.path.join(package_dir, f) for f in os.listdir(package_dir) if f.endswith(".deb")]
    if not deb_files:
        raise FileNotFoundError("No .deb files found in the package directory.")
    
    print("Starting first pass of dpkg...")
    for deb in deb_files:
        print(f"Installing {deb}...")
        run_command(f"dpkg -i {deb}", ignore_errors=True)
    
    print("Resolving missing dependencies with second pass...")
    run_command("apt-get install -f -y", ignore_errors=True)

    print("Second pass of dpkg...")
    for deb in deb_files:
        print(f"Installing {deb}...")
        run_command(f"dpkg -i {deb}", ignore_errors=True)

if __name__ == "__main__":
    try:
        extract_archive(ARCHIVE_FILE, "/mnt")
        install_packages(CACHE_DIR)
        print("Offline installation completed successfully.")
    except Exception as e:
        print(f"Critical error: {e}")

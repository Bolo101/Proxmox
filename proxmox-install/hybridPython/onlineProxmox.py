import subprocess
import logging
from pathlib import Path
import shutil
from typing import List

# Configuration
CACHE_DIR: Path = Path("/mnt/usb/apt-cache/")
ARCHIVE_FILE: Path = Path("usb.tar.gz")
INSTALL_FILE: Path = Path("/var/cache/apt/archives/")

PACKAGES: List[str] = ["gnome", "chromium"]

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def run_command(command: List[str], ignore_errors: bool = False) -> None:
    """Run a shell command."""
    try:
        subprocess.check_call(command)
    except subprocess.CalledProcessError as e:
        if not ignore_errors:
            logging.error(f"Error running command: {command}\n{e}")
        else:
            logging.warning(f"Warning: Command failed but ignored: {command}\n{e}")

def download_packages(packages: List[str]) -> None:
    """Download packages and their dependencies."""
    
    # Update apt package lists
    logging.info("Updating apt package lists...")
    run_command(["apt", "update"], ignore_errors=True)

    # Process each package
    for package in packages:
        logging.info(f"Processing package: {package}")
        try:
            # Download packages
            run_command(["apt-get", "-y", "--download-only", "install", package])
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to process {package}: {e}")
            continue

    # Copy downloaded packages to the USB directory
    logging.info(f"Copying downloaded packages to {CACHE_DIR}...")
    shutil.copytree(INSTALL_FILE, CACHE_DIR)

def create_archive() -> None:
    """Create a compressed tar archive of the USB directory."""
    logging.info(f"Creating archive {ARCHIVE_FILE}...")
    # Change directory to /mnt before creating the archive to avoid including /mnt in the path
    run_command(["tar", "-czvf", str(ARCHIVE_FILE), "-C", "/mnt", "usb"])

if __name__ == "__main__":
    try:
        download_packages(PACKAGES)
        create_archive()
        logging.info(f"Setup completed successfully. Archive created at {ARCHIVE_FILE}.")
    except Exception as e:
        logging.critical(f"Critical error: {e}")

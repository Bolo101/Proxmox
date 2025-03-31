#!/usr/bin/env python3

import subprocess
import logging
from pathlib import Path
import shutil
import os
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
    try:
        shutil.copytree(INSTALL_FILE, CACHE_DIR)
    except FileExistsError:
        logging.warning(f"Cache directory {CACHE_DIR} already exists. Removing and recreating...")
        shutil.rmtree(CACHE_DIR)
        shutil.copytree(INSTALL_FILE, CACHE_DIR)
    except PermissionError:
        logging.error(f"Permission denied when copying to {CACHE_DIR}. Check your permissions.")
        raise
    except OSError as e:
        logging.error(f"OS error when copying files: {e}")
        raise

def create_archive() -> None:
    """Create a compressed tar archive of the USB directory."""
    logging.info(f"Creating archive {ARCHIVE_FILE}...")
    try:
        # Change directory to /mnt before creating the archive to avoid including /mnt in the path
        run_command(["tar", "-czvf", str(ARCHIVE_FILE), "-C", "/mnt", "usb"])
    except subprocess.SubprocessError as e:
        logging.error(f"Failed to create archive: {e}")
        raise
    except FileNotFoundError:
        logging.error(f"Directory or file not found when creating archive")
        raise

if __name__ == "__main__":
    try:
        # Check if running as root
        if os.geteuid() != 0:
            logging.error("This script must be run as root")
            exit(1)
            
        # Create cache directory if it doesn't exist
        os.makedirs(CACHE_DIR.parent, exist_ok=True)
        
        download_packages(PACKAGES)
        create_archive()
        logging.info(f"Setup completed successfully. Archive created at {ARCHIVE_FILE}.")
    except PermissionError:
        logging.critical("Permission error: Make sure you have the necessary permissions")
    except FileNotFoundError as e:
        logging.critical(f"File not found: {e}")
    except OSError as e:
        logging.critical(f"OS error: {e}")
    except subprocess.SubprocessError as e:
        logging.critical(f"Subprocess error: {e}")
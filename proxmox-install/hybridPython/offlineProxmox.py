#!/usr/bin/env python3

import logging
import subprocess
import tarfile
from pathlib import Path
from typing import List

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Configuration
CACHE_DIR: Path = Path("/mnt/usb/apt-cache")
ARCHIVE_FILE: Path = Path("/root/usb.tar.gz")

def run_command(command: List[str], ignore_errors: bool = False) -> None:
    """Run a shell command securely."""
    try:
        subprocess.check_call(command)
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {' '.join(command)} - {e}")
        if not ignore_errors:
            raise

def extract_archive(archive_file: Path, destination: Path) -> None:
    """Securely extract a tar.gz archive."""
    logging.info(f"Extracting archive {archive_file} to {destination}...")
    if not archive_file.exists():
        raise FileNotFoundError(f"Archive file not found: {archive_file}")

    with tarfile.open(archive_file, "r:gz") as tar:
        def is_within_directory(directory: Path, target: Path) -> bool:
            abs_directory = directory.resolve()
            abs_target = target.resolve()
            return abs_target.is_relative_to(abs_directory)

        for member in tar.getmembers():
            member_path = destination / member.name
            if not is_within_directory(destination, member_path):
                raise ValueError(f"Attempted Path Traversal in Tar File: {member_path}")
            tar.extract(member, path=destination)

    logging.info("Extraction completed.")

def install_packages(package_dir: Path) -> None:
    """Install .deb packages using dpkg in two passes."""
    if not package_dir.exists():
        raise FileNotFoundError(f"Package directory not found: {package_dir}")
    
    # Get the list of .deb files
    deb_files: List[Path] = list(package_dir.glob("*.deb"))
    if not deb_files:
        raise FileNotFoundError("No .deb files found in the package directory.")
    
    logging.info("Starting first pass of dpkg...")
    for deb in deb_files:
        logging.info(f"Installing {deb}...")
        run_command(["dpkg", "-i", str(deb)], ignore_errors=True)
    
    logging.info("Resolving missing dependencies with second pass...")
    run_command(["apt-get", "install", "-f", "-y"], ignore_errors=True)

    logging.info("Second pass of dpkg...")
    for deb in deb_files:
        logging.info(f"Installing {deb}...")
        run_command(["dpkg", "-i", str(deb)], ignore_errors=True)

if __name__ == "__main__":
    try:
        extract_archive(ARCHIVE_FILE, Path("/mnt"))
        install_packages(CACHE_DIR)
        logging.info("Offline installation completed successfully.")
    except Exception as e:
        logging.critical(f"Critical error: {e}", exc_info=True)

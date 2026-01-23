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

def disable_sleep_and_suspend() -> None:
    """Disable all sleep and suspend modes."""
    logging.info("Disabling sleep and suspend modes...")
    
    # Mask systemd sleep targets
    logging.info("Masking systemd sleep targets...")
    sleep_targets = ["sleep.target", "suspend.target", "hibernate.target", "hybrid-sleep.target"]
    for target in sleep_targets:
        run_command(["systemctl", "mask", target], ignore_errors=True)
    
    # Disable GNOME screensaver
    logging.info("Disabling GNOME screensaver...")
    run_command(["gsettings", "set", "org.gnome.desktop.screensaver", "lock-enabled", "false"], ignore_errors=True)
    run_command(["gsettings", "set", "org.gnome.desktop.session", "idle-delay", "0"], ignore_errors=True)
    
    # Disable GNOME Power Management
    logging.info("Disabling GNOME Power Management...")
    run_command(["gsettings", "set", "org.gnome.settings-daemon.plugins.power", "sleep-inactive-ac-timeout", "0"], ignore_errors=True)
    run_command(["gsettings", "set", "org.gnome.settings-daemon.plugins.power", "sleep-inactive-battery-timeout", "0"], ignore_errors=True)
    run_command(["gsettings", "set", "org.gnome.settings-daemon.plugins.power", "power-button-action", "nothing"], ignore_errors=True)
    
    # Disable via dconf if available
    logging.info("Configuring dconf settings...")
    run_command(["dconf", "write", "/org/gnome/settings-daemon/plugins/power/sleep-inactive-ac-timeout", "0"], ignore_errors=True)
    run_command(["dconf", "write", "/org/gnome/settings-daemon/plugins/power/sleep-inactive-battery-timeout", "0"], ignore_errors=True)
    
    # Configure sysctl for kernel-level sleep prevention
    logging.info("Configuring sysctl...")
    sysctl_config = "vm.power_action=nothing\n"
    sysctl_file = Path("/etc/sysctl.conf")
    
    # Append if not already present
    if sysctl_config.strip() not in sysctl_file.read_text():
        with open(sysctl_file, "a") as f:
            f.write(sysctl_config)
    
    run_command(["sysctl", "-p"], ignore_errors=True)
    
    # Disable DPMS (Display Power Management Signaling)
    logging.info("Disabling X11 DPMS...")
    xorg_config = '''Section "ServerFlags"
    Option "BlankTime" "0"
    Option "StandbyTime" "0"
    Option "SuspendTime" "0"
    Option "OffTime" "0"
EndSection
'''
    xorg_file = Path("/etc/X11/xorg.conf.d/10-disable-blanking.conf")
    xorg_file.parent.mkdir(parents=True, exist_ok=True)
    xorg_file.write_text(xorg_config)
    
    logging.info("Sleep and suspend modes disabled successfully.")

if __name__ == "__main__":
    try:
        extract_archive(ARCHIVE_FILE, Path("/mnt"))
        install_packages(CACHE_DIR)
        disable_sleep_and_suspend()
        logging.info("Offline installation completed successfully.")
    except Exception as e:
        logging.critical(f"Critical error: {e}", exc_info=True)
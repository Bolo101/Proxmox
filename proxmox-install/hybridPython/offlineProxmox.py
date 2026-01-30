#!/usr/bin/env python3

import logging
import subprocess
import tarfile
from pathlib import Path
from typing import List
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Configuration
CACHE_DIR: Path = Path("/mnt/usb/apt-cache")
ARCHIVE_FILE: Path = Path("/root/usb.tar.gz")
APT_SOURCES_LIST: Path = Path("/etc/apt/sources.list.d/local-repo.sources")

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

def configure_apt_repository() -> None:
    """Configure the local APT repository."""
    logging.info("Configuring local APT repository...")
    
    # Create sources.list entry for the local repository
    sources_content = f"""Types: deb
URIs: file://{CACHE_DIR}
Suites: stable
Components: main
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg
Allow-Insecure: yes
Allow-Weak: yes
"""
    
    APT_SOURCES_LIST.parent.mkdir(parents=True, exist_ok=True)
    APT_SOURCES_LIST.write_text(sources_content)
    logging.info(f"APT sources configured at {APT_SOURCES_LIST}")
    
    # Update apt cache
    logging.info("Updating APT cache...")
    run_command(["apt-get", "update"], ignore_errors=True)

def install_packages() -> None:
    """Install packages using apt-get from local repository."""
    logging.info("Installing GNOME and Chromium from local repository...")
    
    run_command(["apt-get", "-y", "install", "gnome"], ignore_errors=True)
    logging.info("GNOME installation completed.")
    
    run_command(["apt-get", "-y", "install", "chromium"], ignore_errors=True)
    logging.info("Chromium installation completed.")

def configure_keyboard() -> None:
    """Configure keyboard layout to French (AZERTY)."""
    logging.info("Configuring keyboard layout to French (AZERTY)...")
    
    # Configure keyboard in /etc/default/keyboard
    keyboard_config = 'XKBLAYOUT="fr"\n'
    keyboard_file = Path("/etc/default/keyboard")
    keyboard_file.write_text(keyboard_config)
    
    # Reconfigure keyboard
    run_command(["dpkg-reconfigure", "-f", "noninteractive", "keyboard-configuration"], ignore_errors=True)
    
    import time
    time.sleep(5)
    
    # Restart keyboard service
    run_command(["service", "keyboard-setup", "restart"], ignore_errors=True)
    time.sleep(5)
    
    logging.info("Keyboard configuration completed.")

def create_user() -> None:
    """Create a new user account."""
    logging.info("Creating new user account...")
    
    username = input("Enter the username for the new account: ").strip()
    
    if not username:
        logging.warning("No username provided. Skipping user creation.")
        return
    
    if not username.isidentifier() or username.startswith('-'):
        logging.error("Invalid username format.")
        return
    
    # Create user with home directory
    try:
        run_command(["useradd", "-m", "-s", "/bin/bash", username])
        logging.info(f"User '{username}' created successfully.")
        
        # Set password (interactive)
        logging.info(f"Setting password for user '{username}'...")
        run_command(["passwd", username], ignore_errors=True)
        
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to create user '{username}': {e}")

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
        # Check if running as root
        if os.geteuid() != 0:
            logging.error("This script must be run as root")
            exit(1)
        
        extract_archive(ARCHIVE_FILE, Path("/mnt"))
        configure_apt_repository()
        install_packages()
        configure_keyboard()
        create_user()
        disable_sleep_and_suspend()
        
        logging.info("Offline installation completed successfully.")
    except Exception as e:
        logging.critical(f"Critical error: {e}", exc_info=True)

#!/usr/bin/env python3

import logging
import subprocess
import tarfile
from pathlib import Path
from typing import List
import os
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Configuration
CACHE_DIR: Path = Path("/mnt/usb/apt-cache")
ARCHIVE_FILE: Path = Path("/root/usb.tar.gz")
GNOME_CONFIG_SCRIPT: Path = Path("/usr/local/bin/disable-sleep.sh")
POOL_DIR: Path = CACHE_DIR / "pool/main"

def run_command(command: List[str], ignore_errors: bool = False, check_call: bool = True) -> int:
    """Run a shell command securely."""
    try:
        if check_call:
            subprocess.check_call(command)
            return 0
        else:
            return subprocess.call(command)
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {' '.join(command)} - {e}")
        if not ignore_errors:
            raise
        return e.returncode

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
    
    logging.info("[OK] Extraction completed.")

def clean_apt_sources() -> None:
    """Remove all online APT sources."""
    logging.info("Removing all online APT sources...")
    
    # Remove all files in sources.list.d
    sources_dir = Path("/etc/apt/sources.list.d")
    if sources_dir.exists():
        for source_file in sources_dir.glob("*"):
            try:
                if source_file.is_file():
                    source_file.unlink()
                    logging.debug(f"Removed {source_file}")
            except Exception as e:
                logging.warning(f"Failed to delete {source_file}: {e}")
    
    # Clear sources.list
    sources_list = Path("/etc/apt/sources.list")
    sources_list.write_text("# Offline mode - no online sources\n")
    
    logging.info("[OK] Online sources removed.")

def install_packages_offline() -> None:
    """Install all packages from local pool using dpkg."""
    logging.info("Installing packages from local pool...")
    
    if not POOL_DIR.exists():
        raise FileNotFoundError(f"Pool directory not found: {POOL_DIR}")
    
    # Find all .deb files
    deb_files = sorted(POOL_DIR.glob("*.deb"))
    
    if not deb_files:
        raise FileNotFoundError(f"No .deb files found in {POOL_DIR}")
    
    logging.info(f"Found {len(deb_files)} packages to install")
    
    # Build dpkg install command
    deb_file_paths = [str(f) for f in deb_files]
    
    logging.info("Installing all packages with dpkg...")
    # Use --force-all to bypass dependency checks during install
    result = run_command(["dpkg", "--force-all", "-i"] + deb_file_paths, ignore_errors=True, check_call=False)
    
    if result != 0:
        logging.warning(f"dpkg returned exit code {result} (dependencies may be broken)")
    else:
        logging.info("[OK] All packages installed.")
    
    # Try to fix broken dependencies with local packages only
    logging.info("Attempting to fix dependencies with available packages...")
    
    # Don't use apt-get -f install, it tries to download
    # Instead, try to configure any unconfigured packages
    run_command(["dpkg", "--configure", "-a"], ignore_errors=True, check_call=False)
    
    logging.info("[OK] Package installation completed.")

def configure_keyboard() -> None:
    """Configure keyboard layout to French (AZERTY)."""
    logging.info("Configuring keyboard layout to French (AZERTY)...")
    
    keyboard_config = 'XKBLAYOUT="fr"\n'
    keyboard_file = Path("/etc/default/keyboard")
    keyboard_file.write_text(keyboard_config)
    
    run_command(["dpkg-reconfigure", "-f", "noninteractive", "keyboard-configuration"], ignore_errors=True)
    time.sleep(2)
    run_command(["service", "keyboard-setup", "restart"], ignore_errors=True)
    time.sleep(2)
    logging.info("[OK] Keyboard configured.")

def create_user() -> str:
    """Create a new user account."""
    logging.info("Creating user account...")
    
    username = input("Enter username for new account: ").strip()
    
    if not username:
        logging.warning("No username provided. Skipping user creation.")
        return None
    
    if not username.isidentifier() or username.startswith('-'):
        logging.error("Invalid username format.")
        return None
    
    try:
        run_command(["useradd", "-m", "-s", "/bin/bash", username])
        logging.info(f"[OK] User '{username}' created.")
        
        logging.info(f"Setting password for user '{username}'...")
        run_command(["passwd", username], ignore_errors=True)
        
        # Add sudo privileges for sleep script
        sudoers_content = f"{username} ALL=(ALL) NOPASSWD: /usr/local/bin/disable-sleep.sh\n"
        sudoers_file = Path(f"/etc/sudoers.d/{username}-gnome")
        sudoers_file.write_text(sudoers_content)
        sudoers_file.chmod(0o440)
        
        return username
    
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to create user '{username}': {e}")
        return None

def create_disable_sleep_script() -> None:
    """Create script to disable sleep in GNOME."""
    logging.info("Creating GNOME sleep disable script...")
    
    script_content = '''#!/bin/bash
set -e
echo "Disabling GNOME sleep and suspend..."
gsettings set org.gnome.desktop.screensaver lock-enabled false
gsettings set org.gnome.desktop.session idle-delay 0
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-timeout 0
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-timeout 0
gsettings set org.gnome.settings-daemon.plugins.power power-button-action nothing
dconf write /org/gnome/settings-daemon/plugins/power/sleep-inactive-ac-timeout 0
dconf write /org/gnome/settings-daemon/plugins/power/sleep-inactive-battery-timeout 0
echo "GNOME sleep/suspend disabled."
'''
    
    GNOME_CONFIG_SCRIPT.parent.mkdir(parents=True, exist_ok=True)
    GNOME_CONFIG_SCRIPT.write_text(script_content)
    GNOME_CONFIG_SCRIPT.chmod(0o755)
    logging.info("[OK] Sleep disable script created.")

def disable_sleep_systemd() -> None:
    """Disable sleep at systemd level."""
    logging.info("Disabling sleep at systemd level...")
    
    sleep_targets = ["sleep.target", "suspend.target", "hibernate.target", "hybrid-sleep.target"]
    for target in sleep_targets:
        run_command(["systemctl", "mask", target], ignore_errors=True)
    
    # Add sysctl config
    sysctl_file = Path("/etc/sysctl.conf")
    if not sysctl_file.exists():
        sysctl_file.touch(exist_ok=True)
    
    current_content = sysctl_file.read_text()
    if "vm.power_action=nothing" not in current_content:
        with open(sysctl_file, "a") as f:
            f.write("vm.power_action=nothing\n")
    
    run_command(["sysctl", "-p"], ignore_errors=True)
    
    # X11 display configuration
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
    
    logging.info("[OK] Sleep disabled at systemd level.")

def configure_gnome_autostart(username: str) -> None:
    """Configure GNOME autostart for user."""
    if not username:
        return
    
    logging.info(f"Configuring GNOME autostart for user '{username}'...")
    
    autostart_dir = Path(f"/home/{username}/.config/autostart")
    autostart_dir.mkdir(parents=True, exist_ok=True)
    
    desktop_file = '''[Desktop Entry]
Type=Application
Name=Disable Sleep Settings
Exec=/usr/local/bin/disable-sleep.sh
AutoStart=true
Hidden=false
X-GNOME-Autostart-enabled=true
'''
    
    desktop_file_path = autostart_dir / "disable-sleep.desktop"
    desktop_file_path.write_text(desktop_file)
    
    run_command(["chown", "-R", f"{username}:{username}", f"/home/{username}/.config"], ignore_errors=True)
    
    logging.info("[OK] GNOME autostart configured.")

if __name__ == "__main__":
    try:
        if os.geteuid() != 0:
            logging.error("ERROR: This script must be run as root")
            exit(1)
        
        logging.info("=" * 60)
        logging.info("OFFLINE PROXMOX INSTALLATION")
        logging.info("=" * 60)
        
        logging.info("\n[1/8] Extracting archive...")
        extract_archive(ARCHIVE_FILE, Path("/mnt"))
        
        logging.info("\n[2/8] Removing online sources...")
        clean_apt_sources()
        
        logging.info("\n[3/8] Installing packages...")
        install_packages_offline()
        
        logging.info("\n[4/8] Configuring keyboard...")
        configure_keyboard()
        
        logging.info("\n[5/8] Creating sleep disable script...")
        create_disable_sleep_script()
        
        logging.info("\n[6/8] Disabling sleep systemd...")
        disable_sleep_systemd()
        
        logging.info("\n[7/8] Creating user...")
        username = create_user()
        
        if username:
            logging.info("\n[8/8] Configuring GNOME...")
            configure_gnome_autostart(username)
        
        logging.info("\n" + "=" * 60)
        logging.info("SUCCESS: Installation completed!")
        if username:
            logging.info(f"User '{username}' created")
            logging.info("GNOME will auto-configure on first login")
        logging.info("=" * 60)
    
    except Exception as e:
        logging.critical(f"ERROR: {e}", exc_info=True)
        exit(1)
#!/usr/bin/env python3

import subprocess
import logging
from pathlib import Path
import shutil
import os
from typing import List
import gzip
import hashlib
import datetime

# Configuration
CACHE_DIR: Path = Path("/mnt/usb/apt-cache/")
POOL_DIR: Path = CACHE_DIR / "pool/main"
DISTS_DIR: Path = CACHE_DIR / "dists/stable/main/binary-amd64"
ARCHIVE_FILE: Path = Path("usb.tar.gz")
INSTALL_FILE: Path = Path("/var/cache/apt/archives/")
PACKAGES: List[str] = ["gnome", "chromium"]

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def run_command(command: List[str], ignore_errors: bool = False) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(command, check=True, capture_output=False)
        return result
    except subprocess.CalledProcessError as e:
        if not ignore_errors:
            logging.error(f"Error running command: {' '.join(command)}\n{e}")
            raise
        else:
            logging.warning(f"Warning: Command failed but ignored: {' '.join(command)}\n{e}")
            return e

def download_packages(packages: List[str]) -> None:
    """Download packages and ALL their dependencies."""
    logging.info("Updating apt package lists...")
    run_command(["apt", "update"], ignore_errors=True)

    for package in packages:
        logging.info(f"Downloading package: {package} with all dependencies...")
        try:
            run_command([
                "apt-get", "-y", "--download-only",
                "-o", "APT::Get::Autoremove=false",
                "install", package
            ])
            logging.info(f"✓ {package} downloaded successfully")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to download {package}: {e}")
            raise

def copy_packages_to_pool() -> int:
    """Copy downloaded packages to the pool directory and return count."""
    logging.info(f"Copying downloaded packages to pool...")
    POOL_DIR.mkdir(parents=True, exist_ok=True)
    
    copied_count = 0
    try:
        for deb_file in sorted(Path(INSTALL_FILE).glob("*.deb")):
            dest = POOL_DIR / deb_file.name
            if not dest.exists():
                shutil.copy2(deb_file, dest)
                logging.debug(f"Copied {deb_file.name}")
            copied_count += 1
        
        logging.info(f"✓ Total packages: {copied_count}")
        return copied_count
    except Exception as e:
        logging.error(f"Error copying packages: {e}")
        raise

def generate_packages_file() -> None:
    """Generate Packages and Packages.gz files with correct MD5."""
    logging.info("Generating Packages index...")
    DISTS_DIR.mkdir(parents=True, exist_ok=True)
    packages_file = DISTS_DIR / "Packages"
    
    try:
        deb_files = sorted(POOL_DIR.glob("*.deb"))
        logging.info(f"Processing {len(deb_files)} packages...")
        
        with open(packages_file, 'w') as f:
            for i, deb_file in enumerate(deb_files, 1):
                if i % 100 == 0:
                    logging.info(f"  Indexed {i}/{len(deb_files)} packages...")
                
                # Extraire les métadonnées du package
                result = subprocess.run(
                    ["dpkg-deb", "-f", str(deb_file)],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # Écrire les métadonnées
                f.write(result.stdout)
                
                # Ajouter le chemin relatif du fichier
                relative_path = deb_file.relative_to(CACHE_DIR)
                f.write(f"Filename: {relative_path}\n")
                
                # Calculer et ajouter la taille
                file_size = deb_file.stat().st_size
                f.write(f"Size: {file_size}\n")
                
                # Calculer MD5 DIRECTEMENT du fichier
                md5 = hashlib.md5()
                with open(deb_file, 'rb') as df:
                    while True:
                        chunk = df.read(8192)
                        if not chunk:
                            break
                        md5.update(chunk)
                f.write(f"MD5sum: {md5.hexdigest()}\n")
                
                f.write("\n")
        
        logging.info(f"✓ Packages file created with {len(deb_files)} entries")
        
        # Créer Packages.gz
        logging.info("Compressing Packages.gz...")
        with open(packages_file, 'rb') as f_in:
            with gzip.open(str(packages_file) + '.gz', 'wb') as f_out:
                f_out.writelines(f_in)
        logging.info("✓ Packages.gz created")
        
    except Exception as e:
        logging.error(f"Failed to generate Packages files: {e}")
        raise

def generate_release_file() -> None:
    """Generate Release file with correct checksums."""
    logging.info("Generating Release file...")
    release_file = CACHE_DIR / "dists/stable/Release"
    release_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        packages_file = DISTS_DIR / "Packages"
        packages_gz_file = DISTS_DIR / "Packages.gz"
        
        if not packages_file.exists():
            raise FileNotFoundError(f"Packages file not found: {packages_file}")
        if not packages_gz_file.exists():
            raise FileNotFoundError(f"Packages.gz file not found: {packages_gz_file}")
        
        def calculate_checksums(file_path: Path) -> dict:
            """Calculate MD5, SHA1, SHA256 checksums."""
            md5 = hashlib.md5()
            sha1 = hashlib.sha1()
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    md5.update(chunk)
                    sha1.update(chunk)
                    sha256.update(chunk)
            return {
                'md5': md5.hexdigest(),
                'sha1': sha1.hexdigest(),
                'sha256': sha256.hexdigest(),
                'size': file_path.stat().st_size
            }
        
        checksums_pkg = calculate_checksums(packages_file)
        checksums_gz = calculate_checksums(packages_gz_file)
        
        today = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S UTC")
        
        release_content = f"""Origin: LocalProxmox
Label: Local Proxmox Repository
Suite: stable
Codename: bookworm
Date: {today}
Architectures: amd64
Components: main
Description: Local offline APT repository
MD5Sum:
 {checksums_pkg['md5']} {checksums_pkg['size']} main/binary-amd64/Packages
 {checksums_gz['md5']} {checksums_gz['size']} main/binary-amd64/Packages.gz
SHA1:
 {checksums_pkg['sha1']} {checksums_pkg['size']} main/binary-amd64/Packages
 {checksums_gz['sha1']} {checksums_gz['size']} main/binary-amd64/Packages.gz
SHA256:
 {checksums_pkg['sha256']} {checksums_pkg['size']} main/binary-amd64/Packages
 {checksums_gz['sha256']} {checksums_gz['size']} main/binary-amd64/Packages.gz
"""
        
        release_file.write_text(release_content)
        logging.info(f"✓ Release file created")
        
    except Exception as e:
        logging.error(f"Failed to generate Release file: {e}")
        raise

def create_archive() -> None:
    """Create a compressed tar archive of the repository."""
    logging.info(f"Creating archive {ARCHIVE_FILE}...")
    try:
        if not CACHE_DIR.exists():
            raise FileNotFoundError(f"Cache directory not found: {CACHE_DIR}")
        
        run_command(["tar", "-czf", str(ARCHIVE_FILE), "-C", "/mnt", "usb"])
        
        archive_size = ARCHIVE_FILE.stat().st_size / (1024 * 1024)
        logging.info(f"✓ Archive created: {ARCHIVE_FILE} ({archive_size:.2f} MB)")
        
    except Exception as e:
        logging.error(f"Failed to create archive: {e}")
        raise

def verify_repository() -> bool:
    """Verify repository structure."""
    logging.info("Verifying repository structure...")
    
    checks = [
        (POOL_DIR, "Pool directory"),
        (DISTS_DIR / "Packages", "Packages file"),
        (DISTS_DIR / "Packages.gz", "Packages.gz file"),
        (CACHE_DIR / "dists/stable/Release", "Release file"),
    ]
    
    all_good = True
    for path, name in checks:
        if path.exists():
            logging.info(f"✓ {name} exists")
        else:
            logging.error(f"✗ {name} missing: {path}")
            all_good = False
    
    return all_good

if __name__ == "__main__":
    try:
        if os.geteuid() != 0:
            logging.error("This script must be run as root")
            exit(1)

        logging.info("=" * 60)
        logging.info("Starting APT repository creation")
        logging.info("=" * 60)

        os.makedirs(CACHE_DIR, exist_ok=True)

        logging.info("\n[1/5] Downloading packages...")
        download_packages(PACKAGES)
        
        logging.info("\n[2/5] Copying packages to pool...")
        copy_packages_to_pool()
        
        logging.info("\n[3/5] Generating Packages index...")
        generate_packages_file()
        
        logging.info("\n[4/5] Generating Release file...")
        generate_release_file()
        
        logging.info("\n[5/5] Verifying repository...")
        if not verify_repository():
            raise Exception("Repository verification failed")
        
        logging.info("\nCreating archive...")
        create_archive()

        logging.info("\n" + "=" * 60)
        logging.info("✓ Setup completed successfully!")
        logging.info(f"✓ Archive ready: {ARCHIVE_FILE}")
        logging.info("=" * 60)

    except Exception as e:
        logging.critical(f"✗ Error: {e}", exc_info=True)
        exit(1)
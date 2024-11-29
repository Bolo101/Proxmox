import os
import subprocess
import json

# Répertoires de sortie
CACHE_DIR = "/mnt/usb/apt-cache"
INSTALL_ORDER_FILE = "/mnt/usb/install_order.json"

# Paquets à télécharger
PACKAGES = ["gnome", "chromium"]

def run_command(command):
    """Exécute une commande shell et retourne sa sortie."""
    try:
        return subprocess.check_output(command, shell=True, text=True).strip()
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'exécution de la commande: {command}\n{e.output}")
        return ""  # Retourne une chaîne vide en cas d'erreur

def download_packages(packages):
    """Télécharge les paquets et leurs dépendances."""
    os.makedirs(CACHE_DIR, exist_ok=True)

    # Met à jour la liste des paquets (mais gère l'échec dans le cas où on est hors ligne)
    print("Mise à jour de la liste des paquets avec apt...")
    apt_update_output = run_command("apt update")
    if "Err" in apt_update_output:
        print("Attention : échec de 'apt update'. Mise à jour des paquets ignorée.")
        # Vous pouvez choisir de quitter ou de continuer selon votre logique
        # return

    # Liste des paquets à installer dans l'ordre
    install_order = []

    for package in packages:
        print(f"Téléchargement de {package} et de ses dépendances...")
        
        # Récupérer les URL de téléchargement des paquets et de leurs dépendances
        command = f"apt-get -y --print-uris --reinstall install {package} | grep -oP \"'(.*?)'\" | sed \"s/'//g\""
        package_urls = run_command(command).splitlines()

        # Ajouter les paquets téléchargés à la liste d'installation (évite les doublons)
        for url in package_urls:
            deb_name = os.path.basename(url)
            if deb_name not in install_order:
                install_order.append(deb_name)

        # Télécharger les paquets
        run_command(f"apt-get -y --download-only install {package}")

    # Sauvegarder l'ordre d'installation dans un fichier JSON
    print("Sauvegarde de l'ordre d'installation...")
    with open(INSTALL_ORDER_FILE, "w") as f:
        json.dump(install_order, f, indent=4)

    # Copier les paquets téléchargés vers le répertoire USB
    print("Copie des paquets téléchargés vers l'USB...")
    run_command(f"cp /var/cache/apt/archives/*.deb {CACHE_DIR}")

    print(f"Paquets téléchargés et ordre d'installation sauvegardés dans {CACHE_DIR} et {INSTALL_ORDER_FILE}.")

if __name__ == "__main__":
    download_packages(PACKAGES)

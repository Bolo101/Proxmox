import os
import subprocess
import json

# Répertoires d'entrée
CACHE_DIR = "/mnt/usb/apt-cache"
INSTALL_ORDER_FILE = "/mnt/usb/install_order.json"

def run_command(command):
    """Exécute une commande shell."""
    try:
        subprocess.check_call(command, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'exécution de la commande: {command}\n{e}")
        raise

def install_packages():
    """Installe les paquets dans le bon ordre directement depuis le cache local."""
    if not os.path.exists(CACHE_DIR):
        raise FileNotFoundError(f"Le répertoire de cache {CACHE_DIR} n'existe pas !")

    if not os.path.exists(INSTALL_ORDER_FILE):
        raise FileNotFoundError(f"Le fichier d'ordre d'installation {INSTALL_ORDER_FILE} n'existe pas !")

    # Charge l'ordre d'installation des paquets
    with open(INSTALL_ORDER_FILE, "r") as f:
        install_order = json.load(f)

    # Installer les paquets dans l'ordre
    print("Installation des paquets dans le bon ordre...")
    for package in install_order:
        deb_path = os.path.join(CACHE_DIR, package)
        if os.path.exists(deb_path):
            print(f"Installation de {package}...")
            run_command(f"dpkg -i {deb_path}")
        else:
            print(f"Avertissement : {package} non trouvé dans le cache !")

    # Corriger les dépendances cassées
    #print("Correction des dépendances cassées...")
    #run_command("apt-get -f install -y")

    print("Tous les paquets ont été installés avec succès !")

if __name__ == "__main__":
    install_packages()

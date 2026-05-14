#!/bin/bash

# Configuration
KDE_CONFIG_SCRIPT="/usr/local/bin/disable-sleep.sh"

# Création de l'utilisateur proxmox
echo "Création du profil utilisateur proxmox"
adduser proxmox
sleep 5

# Mise à jour des dépôts
echo "Mise à jour des dépôts"
apt update
sleep 5

# Installer xfce4, lightdm et chromium à partir du dépôt local
echo "Installation de kde et chromium..."
apt-get install -y kde-standard chromium
sleep 5

# Configurer le clavier en français (azerty)
echo "Configuration du clavier en français (AZERTY)..."
echo 'XKBLAYOUT="fr"' > /etc/default/keyboard
dpkg-reconfigure -f noninteractive keyboard-configuration
sleep 5

# Redémarrer le service de configuration du clavier pour appliquer les modifications
service keyboard-setup restart
sleep 5

# Créer le script de désactivation de la mise en veille KDE
echo "Création du script de désactivation de la mise en veille..."
mkdir -p $(dirname "$KDE_CONFIG_SCRIPT")
cat > "$KDE_CONFIG_SCRIPT" << 'EOF'
#!/bin/bash
set -e
echo "Désactivation de la mise en veille et de la suspension KDE..."
kwriteconfig5 --file kdeglobals --group General --key ScreenSaverEnabled false
kwriteconfig5 --file kdeglobals --group General --key IdleTime 0
kwriteconfig5 --file kdeglobals --group General --key SuspendTime 0
kwriteconfig5 --file kdeglobals --group General --key HibernateTime 0
echo "Mise en veille/suspension KDE désactivée."
EOF
chmod 755 "$KDE_CONFIG_SCRIPT"
sleep 2

# Désactiver la mise en veille au niveau systemd
echo "Désactivation de la mise en veille au niveau systemd..."
systemctl mask sleep.target || true
systemctl mask suspend.target || true
systemctl mask hibernate.target || true
systemctl mask hybrid-sleep.target || true
sleep 2

# Ajouter la configuration sysctl
echo "Configuration sysctl..."
if ! grep -q "vm.power_action=nothing" /etc/sysctl.conf; then
    echo "vm.power_action=nothing" >> /etc/sysctl.conf
fi
sysctl -p > /dev/null 2>&1 || true
sleep 2

# Configuration X11 pour désactiver l'extinction d'écran
echo "Configuration X11..."
mkdir -p /etc/X11/xorg.conf.d/
cat > /etc/X11/xorg.conf.d/10-disable-blanking.conf << 'EOF'
Section "ServerFlags"
Option "BlankTime" "0"
Option "StandbyTime" "0"
Option "SuspendTime" "0"
Option "OffTime" "0"
EndSection
EOF
sleep 2

# Configurer sudo pour le script de désactivation sans mot de passe
echo "Configuration des permissions sudo pour proxmox..."
cat > /etc/sudoers.d/proxmox-gnome << 'EOF'
proxmox ALL=(ALL) NOPASSWD: /usr/local/bin/disable-sleep.sh
EOF
chmod 440 /etc/sudoers.d/proxmox-gnome
sleep 2

# Configurer l'autostart KDE pour proxmox
echo "Configuration de l'autostart KDE pour proxmox..."
AUTOSTART_DIR="/home/proxmox/.config/autostart"
mkdir -p "$AUTOSTART_DIR"
cat > "$AUTOSTART_DIR/disable-sleep.desktop" << 'EOF'
[Desktop Entry]
Type=Application
Name=Disable Sleep Settings
Exec=/usr/local/bin/disable-sleep.sh
AutoStart=true
Hidden=false
X-GNOME-Autostart-enabled=true
EOF
chown -R proxmox:proxmox /home/proxmox/.config
sleep 2

echo "Installation terminée avec succès!"
echo "Le script de désactivation de la mise en veille s'exécutera automatiquement à la connexion GNOME."

# Redémarrer le système
echo "Redémarrage du système..."
sleep 3
reboot
# Guide d'utilisation

## Présentation

Les deux scripts proposés permettent l’installation d’un environnement de bureau léger ainsi que d’un gestionnaire de session léger.
Les deux scripts permettent l’installation de LightDM, XFCE4, de Chromium, et de toutes les dépendances associées. 
La solution proposée permet l’administration d’un serveur Proxmox-VE directement depuis le serveur, sans requérir l’usage d’une machine annexe sur le réseau pour accéder à l’interface web d’administration. 
L’interface web d’administration est accessible directement depuis le serveur Proxmox-VE via cette configuration. 
Vous trouverez ci-après les étapes d’installation à effectuer sur un serveur Proxmox-VE installé via l’ISO d’installation.

# Préparation de l'installation

* Télécharger le fichier zip native-proxmox.zip sur votre ordinateur et dézipper le fichier
* Transférer le dossier native-proxmox vers une clé USB

# Installation

* Brancher la clé USB sur le serveur proxmox
* Détecter la clé USB avec la commande 'lsblk'
```bash
lsblk
```
* Monter la clé USB.
```bash
mount /dev/sdXX /mnt 
//Remplacer XX par la sortie de la commande lsblk correspondant à la clé
```
* Transférer les scripts et paquets de la clé vers le serveur
```bash
rsync -a /mnt/native-proxmox/ /root/ --progress
```
* Exécuter le script 'script0.sh'
```bash
./script0.sh
```
* Renseigner un mot de passe pour l'utilisateur 'proxmox'
Cet utilisateur permettra d'accéder à une session graphique

* Suivre les intructions et valider avec 'y' toutes demandes de validation

Au redémarrage du poste vous serrez face à un champ de connexion graphique.

* Se connecter en tant qu'utilisateur 'proxmox'

* Lancer un terminal

* Obtenir l'adresse IP du poste
```bash
ip a
```
Noter l'IP de vmbr0

* Passer en tant que 'root'
```
su -
```
* Exécution du script 'script1.sh'
```bash
./script1.sh
```
* Au redémarrage se reconnecter en tant que 'proxmox'

* Lancer le navigateur web

* Se connecter au serveur
Renseigner l'adresse IP du poste avec le port de connexion

Ex: 192.168.2.13:8006

* Se connecter à l'interface d'amdinistration graphique
Utiliser le nom d'utilisateur 'root' et le mot de passe défini lors de l'installation de proxmox-VE



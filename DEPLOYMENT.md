# 🚀 Guide de Déploiement Production - Serveur IA

## ⚠️ Architecture Distribuée

Ce guide décrit l'installation du **serveur Intelligence Artificielle uniquement**.

**Asterisk doit être installé et configuré sur un serveur distant séparé.**

## Prérequis Serveur IA

### Spécifications Minimales
- **CPU**: 4 vCPU
- **RAM**: 2 GB
- **Disque**: 10 GB (20 GB si logs conservés longtemps)
- **OS**: Ubuntu 22.04 LTS ou Debian 12 ou Debian 13
- **Réseau**: Connexion stable (< 50ms vers APIs Deepgram/Groq/OpenAI)

### Serveur Asterisk (distinct)

Vous devez disposer d'un **serveur Asterisk séparé** avec:
- Asterisk 18+ installé
- Module `app_audiosocket` disponible
- Connectivité réseau vers le serveur IA sur le port 9090

## Étape 1: Préparation du Serveur IA

### 1.1 Mise à jour du système

```bash
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y git python3.11 python3.11-venv python3-pip ffmpeg docker.io ufw
```

### 1.2 Création utilisateur dédié

```bash
# Créer un utilisateur système
sudo useradd -r -s /bin/bash -d /opt/PY_SAV -m voicebot

# Ajouter au groupe audio (pour accès aux devices si nécessaire)
sudo usermod -a -G audio voicebot
```

## Étape 2: Installation de l'Application

### 2.1 Cloner le repository

```bash
# En tant que root
cd /opt
sudo git clone https://github.com/votre-org/PY_SAV.git
sudo chown -R voicebot:voicebot /opt/PY_SAV
```

### 2.2 Installation Python

```bash
# Devenir l'utilisateur voicebot
sudo su - voicebot

# Créer l'environnement virtuel
cd /opt/PY_SAV
python3.11 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install --upgrade pip
pip install -r requirements.txt
```

### 2.3 Configuration

```bash
# Copier le template
cp .env.example .env

# Éditer avec les vraies clés
nano .env
```

Renseigner:
```bash
DEEPGRAM_API_KEY=your_actual_deepgram_key
GROQ_API_KEY=your_actual_groq_key
OPENAI_API_KEY=your_actual_openai_key

AUDIOSOCKET_HOST=0.0.0.0
AUDIOSOCKET_PORT=9090
LOG_LEVEL=INFO
```

### 2.4 Générer le cache audio

```bash
# Générer les fichiers audio 8kHz
python generate_cache.py

# Vérifier
ls -lh assets/cache/
```

### 2.5 Test de configuration

```bash
# Tester que tout est OK
python test_setup.py

# Si tout est vert, passer à l'étape suivante
```

## Étape 3: Configuration du Firewall

### 3.1 Autoriser le port 9090 depuis Asterisk

```bash
# Remplacer <IP_ASTERISK> par l'IP de votre serveur Asterisk
sudo ufw allow from <IP_ASTERISK> to any port 9090 proto tcp comment 'AudioSocket depuis Asterisk'

# Autoriser SSH (si pas déjà fait)
sudo ufw allow 22/tcp

# Activer UFW si pas déjà fait
sudo ufw --force enable

# Vérifier
sudo ufw status
```

## Étape 4: Configuration Asterisk (sur serveur distant)

⚠️ **IMPORTANT**: Cette étape doit être effectuée sur votre **serveur Asterisk distant**, PAS sur le serveur IA !

### 4.1 Vérifier le module AudioSocket

```bash
# Sur le SERVEUR ASTERISK (pas sur le serveur IA!)
sudo asterisk -rx "module show like audiosocket"

# Si non chargé:
sudo asterisk -rx "module load app_audiosocket"
```

### 4.2 Configurer le dialplan

```bash
# Sur le SERVEUR ASTERISK
sudo nano /etc/asterisk/extensions.conf
```

Ajouter (voir `asterisk_config.txt` pour le détail):

```ini
[voicebot]
exten => 777,1,Answer()
    same => n,Verbose(1, "Call to Voicebot SAV Wouippleul from ${CALLERID(num)}")
    same => n,AudioSocket(${CALLERID(num)}_${UNIQUEID},<IP_DU_SERVEUR_IA>:9090)
    same => n,Verbose(1, "AudioSocket session ended")
    same => n,Hangup()
```

⚠️ **Remplacer `<IP_DU_SERVEUR_IA>` par l'adresse IP réelle du serveur Python (serveur IA).**

### 4.3 Recharger Asterisk

```bash
# Sur le SERVEUR ASTERISK
sudo asterisk -rx "dialplan reload"

# Vérifier
sudo asterisk -rx "dialplan show voicebot"
```

## Étape 5: Déploiement systemd

### 5.1 Installer le service

```bash
# Copier le fichier service
sudo cp /opt/PY_SAV/voicebot.service /etc/systemd/system/

# Recharger systemd
sudo systemctl daemon-reload
```

### 5.2 Démarrer le service

```bash
# Activer au démarrage
sudo systemctl enable voicebot

# Démarrer
sudo systemctl start voicebot

# Vérifier le statut
sudo systemctl status voicebot
```

Résultat attendu:
```
● voicebot.service - Voicebot SAV Wouippleul
   Loaded: loaded (/etc/systemd/system/voicebot.service; enabled)
   Active: active (running) since Mon 2025-11-18 10:00:00 UTC; 5s ago
```

### 5.3 Vérifier les logs

```bash
# Logs en temps réel
sudo journalctl -u voicebot -f

# Logs récents
sudo journalctl -u voicebot -n 100
```

## Étape 6: Test de Connexion

### 6.1 Vérifier le service IA

```bash
# Sur le serveur IA
sudo systemctl status voicebot
sudo netstat -tlnp | grep 9090
```

### 6.2 Tester depuis Asterisk

```bash
# Sur le serveur Asterisk, tester la connectivité TCP vers le serveur IA
telnet <IP_DU_SERVEUR_IA> 9090

# Si la connexion s'établit, appuyez sur Ctrl+] puis tapez quit
# Si la connexion échoue, vérifiez le firewall sur le serveur IA
```

## Étape 7: Monitoring

### 7.1 Logs

Les logs sont gérés par systemd journal:

```bash
# Voir les logs du service
sudo journalctl -u voicebot -f

# Logs Asterisk
tail -f /var/log/asterisk/full
```

### 7.2 Monitoring CPU/RAM

```bash
# Top des processus
htop

# Statistiques CPU par core
mpstat -P ALL 1

# Mémoire
free -h

# Utilisation disque (logs audio)
du -sh /opt/PY_SAV/logs/calls/
```

### 7.3 Alertes (optionnel)

Installer un monitoring (ex: Prometheus + Grafana):

```bash
# Exporter des métriques custom
# TODO: Ajouter un endpoint /metrics au serveur
```

## Étape 8: Backup et Maintenance

### 8.1 Backup des logs audio

```bash
# Backup quotidien (cron)
sudo crontab -e

# Ajouter:
0 4 * * * rsync -av /opt/PY_SAV/logs/calls/ /backup/voicebot/$(date +\%Y\%m\%d)/
```

### 8.2 Conversion batch nocturne

```bash
# En tant qu'utilisateur voicebot
crontab -e

# Conversion RAW -> MP3 à 3h du matin
0 3 * * * cd /opt/PY_SAV && /opt/PY_SAV/venv/bin/python convert_logs.py --delete-raw >> /var/log/voicebot_convert.log 2>&1
```

### 8.3 Rotation des logs

```bash
# Créer /etc/logrotate.d/voicebot
sudo nano /etc/logrotate.d/voicebot
```

Contenu:
```
/opt/PY_SAV/logs/calls/*.mp3 {
    weekly
    rotate 4
    compress
    missingok
    notifempty
    create 0640 voicebot voicebot
}
```

## Étape 9: Test de Production

### 9.1 Test d'appel

```bash
# Depuis un téléphone SIP, composer 777
# Vous devriez entendre le message de bienvenue
```

### 9.2 Test de charge (optionnel)

```bash
# Utiliser SIPp pour simuler 20 appels simultanés
# TODO: Créer un scénario SIPp
```

## Dépannage Production

### Problème: Service ne démarre pas

```bash
# Vérifier les logs
sudo journalctl -u voicebot -n 100

# Vérifier les permissions
ls -la /opt/PY_SAV/

# Tester manuellement
sudo su - voicebot
cd /opt/PY_SAV
source venv/bin/activate
python server.py
```

### Problème: Clés API invalides

```bash
# Vérifier le fichier .env
sudo cat /opt/PY_SAV/.env

# Tester les clés manuellement
python -c "import config; print(config.DEEPGRAM_API_KEY)"
```

### Problème: Port 9090 déjà utilisé

```bash
# Voir qui utilise le port
sudo netstat -tlnp | grep 9090

# Tuer le processus
sudo kill -9 <PID>
```

## Mise à Jour de l'Application

```bash
# Se connecter au serveur
ssh votre-serveur

# Devenir voicebot
sudo su - voicebot

# Aller dans le répertoire
cd /opt/PY_SAV

# Pull les mises à jour
git pull origin main

# Mettre à jour les dépendances si nécessaire
source venv/bin/activate
pip install -r requirements.txt

# Redémarrer le service
exit  # Revenir en root
sudo systemctl restart voicebot

# Vérifier
sudo systemctl status voicebot
```

## Rollback en cas de problème

```bash
# Revenir à la version précédente
cd /opt/PY_SAV
git log --oneline  # Trouver le commit précédent
git checkout <commit-hash>

# Redémarrer
sudo systemctl restart voicebot
```

## Sécurité Avancée

### Renforcement systemd

Modifier `/etc/systemd/system/voicebot.service`:

```ini
[Service]
# ... (configuration existante)

# Isolation
PrivateTmp=true
NoNewPrivileges=true

# Protection filesystem
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/PY_SAV/logs /opt/PY_SAV/assets/cache

# Capabilities
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_BIND_SERVICE

# Réseau
RestrictAddressFamilies=AF_INET AF_INET6
```

Recharger:
```bash
sudo systemctl daemon-reload
sudo systemctl restart voicebot
```

## Checklist Déploiement

### Serveur IA
- [ ] Serveur IA configuré (Ubuntu 22.04+, 4 vCPU, 2GB RAM)
- [ ] Utilisateur `voicebot` créé
- [ ] Repository cloné dans `/opt/PY_SAV`
- [ ] Dépendances Python installées
- [ ] FFmpeg et Docker installés
- [ ] Fichier `.env` configuré avec les vraies clés API
- [ ] Cache audio généré (`python generate_cache.py`)
- [ ] Test de configuration passé (`python test_setup.py`)
- [ ] Service systemd installé et activé
- [ ] Firewall configuré (port 9090 autorisé uniquement depuis IP Asterisk)
- [ ] Logs vérifiés (`journalctl -u voicebot`)
- [ ] Port 9090 accessible depuis le serveur Asterisk (`telnet <IP_IA> 9090`)
- [ ] Backup automatique configuré
- [ ] Conversion batch nocturne configurée
- [ ] Rotation des logs configurée

### Serveur Asterisk (distinct)
- [ ] Serveur Asterisk configuré et fonctionnel
- [ ] Module AudioSocket chargé (`asterisk -rx "module show like audiosocket"`)
- [ ] Dialplan configuré (extension 777 pointe vers `<IP_IA>:9090`)
- [ ] Configuration rechargée (`asterisk -rx "dialplan reload"`)
- [ ] Connectivité réseau vers le serveur IA vérifiée
- [ ] Test d'appel réussi (composer 777 depuis un téléphone SIP)

## Support

En cas de problème:
1. Vérifier les logs: `sudo journalctl -u voicebot -f`
2. Tester manuellement: `python server.py`
3. Vérifier le test_setup: `python test_setup.py`
4. Consulter la documentation: `README.md` et `ARCHITECTURE.md`

---

**Voicebot SAV Wouippleul est maintenant en production !** 🚀

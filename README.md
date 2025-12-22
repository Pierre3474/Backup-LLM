# Voicebot SAV Wipple - Architecture Haute Performance

Serveur d'**Intelligence Artificielle** Python asynchrone optimisé pour gérer **20 appels simultanés** sur seulement **4 vCPU** via Asterisk AudioSocket.

## ⚠️ Architecture Distribuée

Ce projet installe **uniquement la brique Intelligence Artificielle** (serveur Python/Docker).

**Asterisk doit être installé sur un serveur distant séparé** et configuré pour pointer vers ce serveur IA (voir `asterisk_config.txt`).

## Architecture

### Stack Technique
- **Runtime**: Python 3.11+ avec `uvloop` (performances réseau optimales)
- **VoIP**: Asterisk (sur serveur distant) + AudioSocket (TCP streaming audio 8kHz)
- **STT**: Deepgram API (nova-2-phonecall)
- **LLM**: Groq API (llama-3.1-70b)
- **TTS**: OpenAI API (tts-1)

### Optimisations Performance
- **Thread Principal (Core 0)**: Gestion réseau asyncio sans blocage
- **Workers (Cores 1-3)**: `ProcessPoolExecutor` pour conversions audio FFmpeg
- **Cache RAM**: Fichiers audio 8kHz pré-générés (zéro latence CPU)
- **Logging Async**: Enregistrement RAW, conversion MP3 en batch nocturne

## Structure du Projet

```
PY_SAV/
├── setup.sh                # 🚀 Script d'installation automatisée
├── server.py               # Serveur AudioSocket principal
├── config.py               # Configuration centralisée
├── db_utils.py             # Utilitaires bases de données
├── audio_utils.py          # Fonctions CPU-bound (conversions)
├── generate_cache.py       # Pré-génération cache audio 8kHz
├── convert_logs.py         # Batch conversion RAW → MP3
├── requirements.txt        # Dépendances Python
├── docker-compose.yml      # Stack Docker (PostgreSQL, Prometheus, Grafana)
├── init_db.sql             # Initialisation bases de données
├── Makefile                # Commandes Docker et utilitaires
├── .env.example            # Template variables d'environnement
├── asterisk_config.txt     # Config Asterisk à copier
└── README.md               # Ce fichier

Runtime:
├── assets/cache/           # Fichiers audio 8kHz pré-générés
└── logs/calls/             # Enregistrements RAW des appels
```

## Installation

### 🚀 Installation Automatisée (Recommandée)

Le script `setup.sh` installe et configure automatiquement le **serveur Intelligence Artificielle**.

**Prérequis**: Debian 13, accès root

⚠️ **Important**: Ce script installe **uniquement** la partie IA. Vous devez installer et configurer **Asterisk sur un serveur distant séparé**.

```bash
# Mode installation complète
sudo ./setup.sh

# Mode nettoyage puis installation
sudo ./setup.sh clean
```

Le script va:
1. ✅ Installer tous les prérequis système (Python 3.11, FFmpeg, Docker, UFW)
2. ✅ Créer l'environnement virtuel Python et installer les dépendances
3. ✅ Collecter vos clés API, mots de passe et adresse IP du serveur Asterisk distant
4. ✅ Générer automatiquement les fichiers `.env`, `docker-compose.override.yml`, `prometheus.yml`
5. ✅ Générer le cache audio (phrases pré-enregistrées)
6. ✅ Lancer la stack Docker (PostgreSQL, Prometheus, Grafana, PgAdmin)
7. ✅ Initialiser les bases de données
8. ✅ Configurer le firewall (autoriser port 9090 uniquement depuis Asterisk)
9. ✅ Démarrer le serveur voicebot IA

**Variables demandées**:
- `DEEPGRAM_API_KEY`: Clé API Deepgram (STT)
- `GROQ_API_KEY`: Clé API Groq (LLM)
- `OPENAI_API_KEY`: Clé API OpenAI (TTS)
- `DB_PASSWORD`: Mot de passe PostgreSQL
- `GRAFANA_PASSWORD`: Mot de passe admin Grafana
- `SERVER_HOST_IP`: IP locale du serveur IA (détectée automatiquement)
- `REMOTE_ASTERISK_IP`: IP du serveur Asterisk distant (pour configuration firewall)

**Services disponibles après installation**:
- 📊 **Grafana**: http://SERVER_IP:3000 (admin/votre_password)
- 📈 **Prometheus**: http://SERVER_IP:9090
- 🗄️ **PostgreSQL Clients**: SERVER_IP:5432
- 🗄️ **PostgreSQL Tickets**: SERVER_IP:5433
- 🔧 **PgAdmin**: http://SERVER_IP:5050
- 📊 **Métriques Voicebot**: http://SERVER_IP:9091/metrics
- 🤖 **Serveur IA AudioSocket**: SERVER_IP:9090

**Configuration Asterisk (serveur distant)**:
- Consultez le fichier `asterisk_config.txt` pour configurer votre serveur Asterisk
- Configurez l'extension **777** pour pointer vers `SERVER_IP:9090`

---

### 🔧 Installation Manuelle

Si vous préférez installer manuellement ou adapter l'installation:

⚠️ **Note**: Ces instructions concernent uniquement le serveur IA. Pour Asterisk, installez-le sur un serveur séparé.

#### 1. Prérequis Système

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3.11 python3-pip ffmpeg docker.io ufw

# Vérifier les versions
python3 --version  # >= 3.11
ffmpeg -version
docker --version
```

### 2. Installation Python

```bash
# Cloner le projet
cd /opt
git clone <votre-repo> PY_SAV
cd PY_SAV

# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configuration des Clés API

```bash
# Copier le template
cp .env.example .env

# Éditer avec vos clés
nano .env
```

Contenu de `.env`:
```bash
DEEPGRAM_API_KEY=votre_clé_deepgram
GROQ_API_KEY=votre_clé_groq
OPENAI_API_KEY=votre_clé_openai

AUDIOSOCKET_HOST=0.0.0.0
AUDIOSOCKET_PORT=9090
LOG_LEVEL=INFO
```

### 4. Générer le Cache Audio

```bash
# Générer les fichiers audio 8kHz (à lancer une seule fois)
python generate_cache.py
```

Résultat attendu:
```
✓ welcome.raw créé (45.2 KB, 2.8s)
✓ goodbye.raw créé (32.1 KB, 2.0s)
✓ ok.raw créé (12.5 KB, 0.8s)
...
Génération du cache terminée avec succès !
```

### 5. Configurer le Firewall

```bash
# Autoriser le port 9090 uniquement depuis l'IP du serveur Asterisk
sudo ufw allow from <REMOTE_ASTERISK_IP> to any port 9090 proto tcp

# Vérifier la règle
sudo ufw status
```

### 6. Configurer Asterisk (sur le serveur distant)

⚠️ **Cette étape doit être effectuée sur votre serveur Asterisk distant, pas sur le serveur IA.**

Consultez le fichier `asterisk_config.txt` pour les instructions détaillées.

En résumé:
```bash
# Sur le SERVEUR ASTERISK (pas sur le serveur IA!)

# Vérifier que le module AudioSocket est disponible
asterisk -rx "module show like audiosocket"

# Si non chargé:
asterisk -rx "module load app_audiosocket"

# Éditer le dialplan
sudo nano /etc/asterisk/extensions.conf
```

Ajouter le contexte (voir `asterisk_config.txt`):
```ini
[voicebot]
exten => 777,1,Answer()
    same => n,AudioSocket(${CALLERID(num)}_${UNIQUEID},<IP_DU_SERVEUR_IA>:9090)
    same => n,Hangup()
```

Remplacer `<IP_DU_SERVEUR_IA>` par l'IP réelle du serveur Python.

Recharger Asterisk:
```bash
asterisk -rx "dialplan reload"
```

## Démarrage

### Mode Développement

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Lancer le serveur
python server.py
```

Sortie attendue:
```
============================================================
AudioSocket Server started on 0.0.0.0:9090
Cache loaded: 8 phrases
Process pool workers: 3
Max concurrent calls: 20
============================================================
```

### Mode Production (systemd)

Créer `/etc/systemd/system/voicebot.service`:

```ini
[Unit]
Description=Voicebot SAV Wipple
After=network.target asterisk.service

[Service]
Type=simple
User=voicebot
WorkingDirectory=/opt/PY_SAV
Environment="PATH=/opt/PY_SAV/venv/bin"
ExecStart=/opt/PY_SAV/venv/bin/python server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Démarrer le service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable voicebot
sudo systemctl start voicebot
sudo systemctl status voicebot
```

## 🧪 Test

### Test Simple

1. Démarrer le serveur: `python server.py`
2. Composer le **777** depuis un téléphone SIP
3. Vous devriez entendre: *"Bonjour, bienvenue au SAV Wipple..."*

### Logs en Temps Réel

```bash
# Logs Python
tail -f logs/calls/*.raw  # Fichiers audio bruts

# Logs Asterisk
tail -f /var/log/asterisk/full
```

## Machine à États SAV

```
INIT → WELCOME → IDENTIFICATION → DIAGNOSTIC → SOLUTION → VERIFICATION
                                                               ↓
                                                        ┌─────┴─────┐
                                                        │           │
                                                     OUI (OK)   NON (KO)
                                                        │           │
                                                    GOODBYE    TRANSFER
```

### Exemple de Dialogue

```
Bot:  Bonjour, bienvenue au SAV Wipple. Comment puis-je vous aider ?
User: Bonjour, j'ai un problème avec ma connexion.

Bot:  Puis-je avoir votre nom et numéro de téléphone ?
User: Pierre Dupont, 06 12 34 56 78.

Bot:  Merci. Avez-vous un problème avec Internet ou Mobile ?
User: Internet.

Bot:  Essayez de débrancher votre box pendant 30 secondes, puis rebranchez-la.
User: D'accord, je vais essayer.

Bot:  Avez-vous pu faire la manipulation ? Est-ce que ça fonctionne maintenant ?
User: Oui, ça marche !

Bot:  Merci pour votre appel. Au revoir !
```

## Scripts Utilitaires

### Conversion Batch RAW → MP3

Exécuter la nuit pour économiser le CPU:

```bash
# Conversion basique
python convert_logs.py

# Avec suppression des fichiers RAW
python convert_logs.py --delete-raw

# Bitrate custom
python convert_logs.py --bitrate 128k

# Parallélisation custom
python convert_logs.py --workers 4
```

### Cron Job (Conversion Nocturne)

```bash
# Éditer crontab
crontab -e

# Ajouter la ligne (tous les jours à 3h du matin)
0 3 * * * cd /opt/PY_SAV && /opt/PY_SAV/venv/bin/python convert_logs.py --delete-raw >> /var/log/voicebot_convert.log 2>&1
```

## Dépannage

### Problème: Deepgram timeout

**Symptôme**: `Deepgram API error: timeout`

**Solution**:
1. Vérifier la connexion internet
2. Augmenter `API_TIMEOUT` dans `config.py`
3. Le système joue automatiquement un message d'attente

### Problème: No such application 'AudioSocket'

**Symptôme**: Asterisk ne trouve pas l'application AudioSocket

**Solution**:
```bash
# Installer le module
asterisk -rx "module load app_audiosocket"

# Vérifier
asterisk -rx "module show like audiosocket"
```

### Problème: Audio coupé ou saccadé

**Causes possibles**:
- Réseau saturé
- CPU surchargé
- Buffer audio trop petit

**Solutions**:
- Réduire `MAX_CONCURRENT_CALLS` dans `config.py`
- Augmenter le nombre de workers (si CPU disponible)
- Vérifier la latence réseau vers Deepgram/OpenAI

### Problème: Le robot ne répond pas

**Debug**:
```bash
# Vérifier les logs
tail -f /var/log/asterisk/full | grep AudioSocket

# Vérifier la connexion
netstat -tlnp | grep 9090

# Tester manuellement
telnet localhost 9090
```

## Monitoring Performance

### Métriques CPU

```bash
# Top des processus Python
ps aux | grep python

# htop avec filtrage
htop -p $(pgrep -d',' -f server.py)
```

### Métriques Réseau

```bash
# Connexions actives
netstat -an | grep :9090 | wc -l

# Bande passante
iftop -i eth0
```

### Logs Structurés

Le serveur log automatiquement:
- Début/fin d'appel
- Transcriptions utilisateur
- Erreurs API
- Conversions audio

Exemple:
```
2025-11-18 10:23:45 - INFO - [a1b2c3d4] New call connected
2025-11-18 10:23:47 - INFO - [a1b2c3d4] User: Bonjour, j'ai un problème
2025-11-18 10:24:12 - INFO - [a1b2c3d4] Technician available: True
2025-11-18 10:24:15 - INFO - [a1b2c3d4] Call ended
```

## Sécurité

### API Keys
- **JAMAIS** commiter les clés dans Git
- Utiliser `.env` (ignoré par `.gitignore`)
- Rotation régulière des clés

### Firewall
```bash
# Autoriser uniquement Asterisk local
sudo ufw allow from 127.0.0.1 to any port 9090

# Bloquer l'accès externe
sudo ufw deny 9090
```

## Scalabilité

### Déploiement Multi-Serveurs

Pour > 20 appels simultanés:

1. **Load Balancer Asterisk**: Répartir les appels sur plusieurs instances Python
2. **Redis Cache**: Partager le cache audio entre serveurs
3. **Queue Manager**: RabbitMQ pour distribuer les appels

### Optimisations Avancées

- **GPU TTS**: Remplacer OpenAI par un modèle local (Coqui TTS)
- **Edge STT**: Whisper local pour réduire la latence
- **CDN Audio**: Servir le cache via Nginx

## Licence

Copyright © 2025 Wipple Tous droits réservés.


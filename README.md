# 🤖 Voicebot SAV Wipple - Production-Ready IA Conversationnelle

Serveur d'**Intelligence Artificielle** Python asynchrone ultra-optimisé pour gérer **20+ appels simultanés** avec architecture **Clean** et **scalable**.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Architecture](https://img.shields.io/badge/Architecture-Clean%20Architecture-green.svg)](REFACTOR.md)
[![Security](https://img.shields.io/badge/Security-Multi--IP%20Firewall-red.svg)](DASHBOARD_SECURITY.md)
[![License](https://img.shields.io/badge/License-Proprietary-orange.svg)](#)

---

## 📋 Table des Matières

- [Vue d'ensemble](#-vue-densemble)
- [Architecture](#-architecture)
- [Nouveautés 2025](#-nouveautés-2025)
- [Installation Automatisée](#-installation-automatisée)
- [Configuration Multi-IP](#-configuration-multi-ip)
- [Structure du Projet](#-structure-du-projet)
- [Services Disponibles](#-services-disponibles)
- [Dashboard Streamlit](#-dashboard-streamlit)
- [Machine à États](#-machine-à-états-sav)
- [Performance & Optimisations](#-performance--optimisations)
- [Sécurité](#-sécurité)
- [Monitoring](#-monitoring)
- [Documentation](#-documentation)

---

## 🎯 Vue d'ensemble

### Architecture Distribuée

Ce projet installe **uniquement la brique Intelligence Artificielle** (serveur Python + Docker).

**Asterisk doit être installé sur un ou plusieurs serveurs distants séparés** et configuré pour pointer vers ce serveur IA.

```
┌─────────────────────┐
│  Serveur Asterisk 1 │ ──┐
│  (Client A)         │   │
└─────────────────────┘   │
                          │     ┌──────────────────────────┐
┌─────────────────────┐   │     │   Serveur IA Python      │
│  Serveur Asterisk 2 │ ──┼────▶│   - AudioSocket :9090    │
│  (Client B)         │   │     │   - STT (Deepgram)       │
└─────────────────────┘   │     │   - LLM (Groq)           │
                          │     │   - TTS (ElevenLabs)     │
┌─────────────────────┐   │     │   - PostgreSQL           │
│  Serveur Asterisk N │ ──┘     │   - Dashboard :8501      │
│  (Client N)         │         │   - Grafana :3000        │
└─────────────────────┘         └──────────────────────────┘
```

**Support Multi-Client** : Le serveur IA peut gérer plusieurs serveurs Asterisk simultanément avec whitelist IP.

---

## 🏗️ Architecture

### Stack Technique Production

| Composant | Technologie | Version | Rôle |
|-----------|-------------|---------|------|
| **Runtime** | Python + uvloop | 3.11+ | Performances réseau optimales |
| **VoIP** | Asterisk (distant) + AudioSocket | 18+ | Streaming audio TCP 8kHz |
| **STT** | Deepgram API | nova-2-phonecall | Speech-to-Text temps réel |
| **LLM** | Groq API | llama-3.3-70b-versatile | Génération réponses + Intent Analysis |
| **TTS** | ElevenLabs API | Turbo v2.5 (Antoine) | Text-to-Speech ultra-rapide |
| **Database** | PostgreSQL | 15+ | Clients + Tickets (2 instances) |
| **Monitoring** | Prometheus + Grafana | Latest | Métriques temps réel |
| **Dashboard** | Streamlit | Latest | Interface supervision |
| **Cache** | LRU + Static | RAM | Audio pré-généré + dynamique |

### Clean Architecture (2025)

Le projet a été **entièrement refactoré** pour suivre les principes de Clean Architecture :

```
voicebot_sav/
├── config/          # Configuration centralisée + prompts YAML
├── models/          # Modèles de données (ConversationContext, Intent)
├── services/        # Services métier (STT, LLM, TTS, Database)
├── core/            # Logique métier (StateMachine, IntentAnalyzer)
├── utils/           # Utilitaires (audio, logging, validation)
└── main.py          # Point d'entrée (serveur AudioSocket)
```

**Avantages** :
- ✅ Modules testables indépendamment
- ✅ Prompts 100% externalisés (YAML)
- ✅ State Machine déclarative
- ✅ Intent Analysis LLM → JSON structuré
- ✅ Endpointing dynamique STT (500ms / 1200ms selon contexte)

📖 **Documentation complète** : [REFACTOR.md](REFACTOR.md)

---

## 🆕 Nouveautés 2025

### 🚀 Performance Turbo

| Optimisation | Avant | Après | Gain |
|--------------|-------|-------|------|
| **STT Endpointing** | 3000ms fixe | 500ms / 1200ms dynamique | **80% plus rapide** |
| **TTS Model** | OpenAI tts-1 | ElevenLabs Turbo v2.5 | **3x plus rapide** |
| **Intent Analysis** | Mots-clés simples | LLM JSON structuré | **95% précision** |
| **Streaming TTS** | Activé | Optimisé | **Zéro latence perçue** |

### 🔐 Sécurité Multi-IP

- **Support Multi-IP** : `PERSONAL_IP=10.0.0.1,192.168.1.50,88.12.34.56`
- **3 couches de sécurité** : UFW + Iptables DOCKER-USER + Application
- **Dashboard protégé** : Validation IP au niveau applicatif (Streamlit)
- **Firewall intelligent** : Règles persistantes après reboot

📖 **Documentation complète** : [DASHBOARD_SECURITY.md](DASHBOARD_SECURITY.md)

### 📡 Multi-Asterisk

- **Support multi-serveurs** : Gérez plusieurs clients (serveurs Asterisk) simultanément
- **Whitelist IP dynamique** : Configuration via `setup.sh` interactif
- **Script de gestion** : `manage_allowed_ips.sh` pour ajouter/supprimer des IPs

📖 **Documentation complète** : [MULTI_IP_SETUP.md](MULTI_IP_SETUP.md)

---

## 🚀 Installation Automatisée

### Prérequis

- **OS** : Debian 13 (ou Ubuntu 22.04+)
- **Accès** : root (sudo)
- **Réseau** : Connexion internet stable
- **Hardware** : 4 vCPU, 8 GB RAM minimum

### Installation en 1 commande

```bash
# Cloner le projet
cd /opt
git clone https://github.com/Pierre3474/Backup-LLM.git PY_SAV
cd PY_SAV

# Lancer l'installation automatisée
sudo ./setup.sh
```

### Ce que fait `setup.sh`

Le script d'installation **tout-en-un** va :

1. ✅ **Prérequis système**
   - Python 3.11, FFmpeg, Git, Curl, UFW
   - Docker Engine + Docker Compose
   - Création utilisateur système `voicebot`

2. ✅ **Environnement Python**
   - Création venv
   - Installation dépendances (requirements.txt)
   - Génération cache audio

3. ✅ **Configuration interactive**
   - **API Keys** : Deepgram, Groq, OpenAI (pour generate_cache legacy)
   - **Passwords** : PostgreSQL, Grafana
   - **IPs Serveur IA** : Détection automatique
   - **IPs Asterisk** : Support multi-serveurs (boucle interactive)
   - **IP Admin** : Votre IP publique (pour services admin)

4. ✅ **Stack Docker**
   - PostgreSQL clients (port 5432)
   - PostgreSQL tickets (port 5433)
   - Prometheus (port 9092)
   - Grafana (port 3000)
   - PgAdmin (port 5050)
   - Dashboard Streamlit (port 8501)

5. ✅ **Firewall (3 couches)**
   - **UFW** : Port 9090 depuis serveurs Asterisk uniquement
   - **UFW** : Ports admin (3000, 5050, 8501, etc.) depuis IPs personnelles
   - **Iptables DOCKER-USER** : Empêche contournement UFW par Docker
   - **Application** : Validation IP dans dashboard.py

6. ✅ **Démarrage serveur**
   - Lancement automatique du voicebot IA (port 9090)

### Variables collectées

| Variable | Description | Exemple |
|----------|-------------|---------|
| `DEEPGRAM_API_KEY` | Clé API Deepgram (STT) | `abc123...` |
| `GROQ_API_KEY` | Clé API Groq (LLM) | `gsk_xyz...` |
| `OPENAI_API_KEY` | Clé API OpenAI (legacy cache) | `sk-proj-...` |
| `DB_PASSWORD` | Mot de passe PostgreSQL | `MySecurePass123!` |
| `GRAFANA_PASSWORD` | Mot de passe admin Grafana | `Admin123!` |
| `SERVER_HOST_IP` | IP locale serveur IA | `192.168.1.100` |
| `REMOTE_ASTERISK_IP` | IP 1er serveur Asterisk | `203.0.113.10` |
| `AMI_USERNAME` | Utilisateur AMI Asterisk | `voicebot-ami` |
| `AMI_SECRET` | Mot de passe AMI | `SecretAMI123!` |
| `PERSONAL_IP` | IP(s) admin (multi-IP) | `10.0.0.1,88.12.34.56` |

### Réinstallation / Mise à jour

```bash
# Nettoyage complet + réinstallation
sudo ./setup.sh clean

# Utiliser configuration existante (skip variables)
sudo ./setup.sh
# → Option 1 : Utiliser configuration existante
```

---

## 🌐 Configuration Multi-IP

### Multi-Asterisk (plusieurs clients)

Lors de l'installation, vous pouvez configurer **plusieurs serveurs Asterisk** :

```
Entrez l'adresse IP du 1er serveur Asterisk: 192.168.1.100
✓ IP 192.168.1.100 ajoutée (1 serveur(s) configuré(s))

Entrez l'IP du serveur Asterisk 2 (ou laissez vide pour terminer): 192.168.2.200
✓ IP 192.168.2.200 ajoutée (2 serveur(s) configuré(s))

Entrez l'IP du serveur Asterisk 3 (ou laissez vide pour terminer): [Entrée]
✓ 2 serveur(s) Asterisk configuré(s)
```

**Gestion post-installation** :

```bash
# Script interactif
./manage_allowed_ips.sh

# Ou en ligne de commande
./manage_allowed_ips.sh add 203.0.113.42
./manage_allowed_ips.sh remove 192.168.2.200
./manage_allowed_ips.sh list
```

### Multi-IP Admin (plusieurs administrateurs)

Pour autoriser **plusieurs IPs** à accéder aux services d'administration :

```bash
# Modifier .env
PERSONAL_IP=10.0.0.1,192.168.1.50,88.12.34.56

# Redémarrer les services
docker compose restart dashboard

# Mettre à jour firewall (si serveur déjà configuré)
sudo ./setup.sh  # Relancer installation (option 1 : config existante)
```

**Format** : IPs séparées par **virgules sans espaces**.

---

## 📂 Structure du Projet

```
PY_SAV/
├── 📄 setup.sh                     # Installation automatisée tout-en-un
├── 📄 server.py                    # Serveur AudioSocket principal (legacy)
├── 📄 config.py                    # Configuration legacy
├── 📄 db_utils.py                  # Utilitaires bases de données
├── 📄 audio_utils.py               # Conversions audio CPU-bound
├── 📄 generate_cache.py            # Génération cache audio 8kHz
├── 📄 convert_logs.py              # Conversion batch RAW → MP3
├── 📄 dashboard.py                 # Dashboard Streamlit (supervision)
├── 📄 manage_allowed_ips.sh        # Gestion IPs Asterisk autorisées
│
├── 📁 voicebot_sav/                # Architecture Clean (nouveau)
│   ├── config/
│   │   ├── settings.py             # Configuration centralisée
│   │   └── prompts.yaml            # Prompts externalisés
│   ├── models/
│   │   ├── conversation.py         # ConversationContext, ConversationState
│   │   └── intents.py              # Intent, IntentType (JSON)
│   ├── services/
│   │   ├── stt.py                  # STTService (Deepgram, endpointing dynamique)
│   │   ├── llm.py                  # LLMService (Groq, intent analysis)
│   │   ├── tts.py                  # TTSService (ElevenLabs, streaming)
│   │   └── database.py             # DatabaseService (wrapper async)
│   ├── core/
│   │   ├── intent_analyzer.py      # IntentAnalyzer (LLM → JSON)
│   │   ├── state_machine.py        # StateMachine (transitions)
│   │   └── call_handler.py         # CallHandler (orchestrateur)
│   └── utils/
│       ├── audio.py                # AudioCache (LRU + static)
│       ├── logging_config.py       # Logs structurés (JSON optionnel)
│       └── validation.py           # Validation email, phone, sentiment
│
├── 📁 config/
│   └── prometheus.yml              # Config Prometheus (auto-généré)
│
├── 📁 assets/
│   └── cache/                      # Fichiers audio 8kHz pré-générés
│       ├── welcome.raw
│       ├── goodbye.raw
│       └── ...
│
├── 📁 logs/
│   └── calls/                      # Enregistrements RAW des appels
│       └── call_{uuid}_{timestamp}.raw
│
├── 📄 docker-compose.yml           # Stack Docker complète
├── 📄 docker-compose.override.yml  # Passwords (auto-généré, gitignored)
├── 📄 init_db.sql                  # Initialisation PostgreSQL
├── 📄 requirements.txt             # Dépendances Python
├── 📄 .env                         # Variables d'environnement (auto-généré)
├── 📄 .env.example                 # Template .env
│
├── 📖 README.md                    # Ce fichier
├── 📖 REFACTOR.md                  # Architecture Clean détaillée
├── 📖 DASHBOARD_SECURITY.md        # Sécurité multi-IP dashboard
├── 📖 MULTI_IP_SETUP.md            # Guide multi-Asterisk
├── 📖 example_usage.py             # Exemple utilisation Clean Architecture
└── 📄 asterisk_config.txt          # Configuration Asterisk (serveur distant)
```

---

## 🌐 Services Disponibles

Après installation, les services suivants sont accessibles :

| Service | URL/Port | Sécurité | Description |
|---------|----------|----------|-------------|
| **🤖 Voicebot IA** | `SERVER_IP:9090` | 🔒 IP Asterisk uniquement | AudioSocket (connexion Asterisk) |
| **📊 Dashboard Streamlit** | `http://SERVER_IP:8501` | 🔒 Multi-IP Admin | Supervision appels + audio |
| **📈 Grafana** | `http://SERVER_IP:3000` | 🔒 Multi-IP Admin | Visualisation métriques |
| **📉 Prometheus** | `http://SERVER_IP:9092` | 🔒 Multi-IP Admin | Collecte métriques |
| **🗄️ PostgreSQL Clients** | `SERVER_IP:5432` | 🔒 Multi-IP Admin | Base clients |
| **🗄️ PostgreSQL Tickets** | `SERVER_IP:5433` | 🔒 Multi-IP Admin | Base tickets |
| **🔧 PgAdmin** | `http://SERVER_IP:5050` | 🔒 Multi-IP Admin | Interface PostgreSQL |
| **📊 Métriques Voicebot** | `http://SERVER_IP:9091/metrics` | 🔒 Multi-IP Admin | Métriques Prometheus format |

### Accès Grafana

```
URL      : http://SERVER_IP:3000
Username : admin
Password : <GRAFANA_PASSWORD défini à l'installation>
```

### Accès PgAdmin

```
URL : http://SERVER_IP:5050
```

Ajoutez une connexion avec :
- Host : `postgres-clients` (ou `postgres-tickets`)
- Port : `5432`
- Database : `db_clients` (ou `db_tickets`)
- Username : `voicebot`
- Password : `<DB_PASSWORD défini à l'installation>`

---

## 📊 Dashboard Streamlit

### Fonctionnalités

Le dashboard offre une **supervision en temps réel** :

- **📈 KPIs** :
  - Appels du jour
  - Durée moyenne
  - Clients mécontents
  - Pannes Internet

- **🎧 Enregistrements** :
  - Liste des 50 derniers tickets
  - Lecture audio intégrée (conversion RAW → WAV à la volée)
  - Sentiment analysis visuel (😐 😊 😡)
  - Métadonnées (UUID, durée, type problème, statut)

### Sécurité 3 Couches

1. **UFW** : Firewall système bloque port 8501 sauf IPs autorisées
2. **Iptables DOCKER-USER** : Empêche Docker de contourner UFW
3. **Application** : `dashboard.py` valide l'IP du visiteur avant affichage

**Résultat** : Même si un attaquant contourne UFW, Docker ET l'application bloquent l'accès.

### Exemple d'utilisation

```bash
# Accès depuis IP autorisée (10.0.0.1)
http://192.168.1.100:8501
→ ✅ Accès autorisé depuis 10.0.0.1
→ Dashboard affiché

# Accès depuis IP non autorisée (12.34.56.78)
http://192.168.1.100:8501
→ 🚫 ACCÈS REFUSÉ
→ Votre IP (12.34.56.78) n'est pas autorisée
→ IPs autorisées: 10.0.0.1, 192.168.1.50
```

📖 **Documentation complète** : [DASHBOARD_SECURITY.md](DASHBOARD_SECURITY.md)

---

## 🔄 Machine à États SAV

### Diagramme de Flux

```
INIT
  ↓
WELCOME ────────┐
  ↓             │
TICKET_         │ (si ticket en attente)
VERIFICATION    │
  ↓ (non)       │
IDENTIFICATION  │
  ↓             │
DIAGNOSTIC ◄────┘
  ↓
SOLUTION
  ↓
VERIFICATION
  ↓
┌───────┴────────┐
│                │
OUI (résolu)   NON (persiste)
│                │
GOODBYE      TRANSFER
```

### États disponibles

| État | Description | Intent attendu |
|------|-------------|----------------|
| `INIT` | Initialisation appel | - |
| `WELCOME` | Message bienvenue | - |
| `TICKET_VERIFICATION` | Vérification ticket existant | YES / NO |
| `IDENTIFICATION` | Collecte identité client | IDENTITY_PROVIDED / EMAIL_PROVIDED |
| `DIAGNOSTIC` | Identification problème | INTERNET_ISSUE / MOBILE_ISSUE / MODIFICATION_REQUEST |
| `SOLUTION` | Proposition solution | - |
| `VERIFICATION` | Vérification résolution | YES (résolu) / NO (persiste) |
| `TRANSFER` | Transfert technicien | - |
| `GOODBYE` | Fin appel | - |
| `ERROR` | Erreur système | - |

### Endpointing Dynamique

La **State Machine** ajuste automatiquement le timeout STT selon le contexte :

| État | Mode STT | Timeout | Raison |
|------|----------|---------|--------|
| `TICKET_VERIFICATION` | `yes_no` | **500ms** | Réponse courte attendue |
| `VERIFICATION` | `yes_no` | **500ms** | Confirmation rapide |
| `SOLUTION` | `yes_no` | **500ms** | Oui/Non après manipulation |
| `DIAGNOSTIC` | `open` | **1200ms** | Description problème complexe |
| `IDENTIFICATION` | `open` | **1200ms** | Nom + prénom + entreprise |
| Autres | `open` | **1200ms** | Réponse ouverte |

**Avantage** : **80% de réduction de latence** sur réponses courtes sans couper la parole sur réponses longues.

📖 **Documentation complète** : [REFACTOR.md](REFACTOR.md)

---

## ⚡ Performance & Optimisations

### Optimisations CPU

| Technique | Description | Gain |
|-----------|-------------|------|
| **uvloop** | Event loop optimisé (libuv) | +40% performances réseau |
| **ProcessPoolExecutor** | Workers FFmpeg parallèles | Zéro blocage thread principal |
| **Cache Audio RAM** | Phrases pré-générées 8kHz | Zéro latence TTS pour phrases communes |
| **LRU Cache** | Cache dynamique (50 entrées) | Réutilisation réponses fréquentes |
| **Streaming TTS** | Chunks 320 bytes (20ms) | Audio joué pendant génération |

### Optimisations Réseau

| Technique | Description | Gain |
|-----------|-------------|------|
| **Deepgram WebSocket** | Connexion persistante | Pas de handshake par phrase |
| **Groq ultra-rapide** | LLM optimisé latence | ~200ms génération |
| **ElevenLabs Turbo v2.5** | TTS ultra-rapide | **3x plus rapide qu'OpenAI** |
| **Endpointing 500ms** | Détection fin de phrase rapide | **80% réduction latence** |

### Capacité

- **4 vCPU** : 20 appels simultanés
- **8 vCPU** : 40+ appels simultanés
- **16 vCPU** : 80+ appels simultanés

**Scalabilité horizontale** : Ajouter serveurs IA + Load Balancer Asterisk.

---

## 🔐 Sécurité

### Firewall 3 Couches

#### 1. UFW (Firewall Système)

```bash
# Port AudioSocket (9090) : Asterisk uniquement
sudo ufw allow from 192.168.1.100 to any port 9090 proto tcp  # Asterisk 1
sudo ufw allow from 192.168.2.200 to any port 9090 proto tcp  # Asterisk 2

# Services Admin (3000, 5050, 8501, 9092, 5432, 5433) : Multi-IP Admin
sudo ufw allow from 10.0.0.1 to any port 8501 proto tcp       # Dashboard
sudo ufw allow from 192.168.1.50 to any port 8501 proto tcp   # Dashboard
```

#### 2. Iptables DOCKER-USER

Docker **contourne UFW** en modifiant directement iptables. Solution : chaîne `DOCKER-USER`.

```bash
# ACCEPT rules (INSERT au début)
iptables -I DOCKER-USER -p tcp --dport 8501 -s 10.0.0.1 -j ACCEPT
iptables -I DOCKER-USER -p tcp --dport 8501 -s 192.168.1.50 -j ACCEPT

# DROP rule (APPEND à la fin)
iptables -A DOCKER-USER -p tcp --dport 8501 -j DROP
```

**Ordre critique** : ACCEPT avant DROP.

#### 3. Application (dashboard.py)

```python
def validate_ip_access():
    allowed_ips = os.getenv("PERSONAL_IP").split(',')
    client_ip = get_client_ip()  # X-Forwarded-For, X-Real-IP

    if client_ip not in allowed_ips:
        st.error("🚫 ACCÈS REFUSÉ")
        st.stop()
```

### API Keys

- **Stockage** : `.env` (gitignored)
- **Permissions** : `chmod 600 .env` (lecture/écriture propriétaire uniquement)
- **Rotation** : Changement régulier recommandé

### Règles Persistantes

Les règles iptables sont **sauvegardées automatiquement** par `setup.sh` :

```bash
# Via netfilter-persistent (si disponible)
netfilter-persistent save

# Ou via iptables-save
iptables-save > /etc/iptables/rules.v4
```

**Résultat** : Règles conservées après reboot.

---

## 📈 Monitoring

### Métriques Prometheus

Le voicebot expose des métriques au format Prometheus :

```
http://SERVER_IP:9091/metrics
```

**Métriques disponibles** :
- `voicebot_calls_total` : Nombre total d'appels
- `voicebot_calls_active` : Appels en cours
- `voicebot_call_duration_seconds` : Durée moyenne appel
- `voicebot_errors_total` : Erreurs API (Deepgram, Groq, ElevenLabs)
- `voicebot_cache_hits_total` : Cache hits audio
- `voicebot_cache_misses_total` : Cache misses audio

### Grafana Dashboards

Accédez à Grafana : `http://SERVER_IP:3000` (admin/votre_password)

**Dashboards recommandés** :
- Appels en temps réel
- Taux d'erreur API
- Latence moyenne
- Utilisation cache
- Transferts techniciens

### Logs Structurés

Le système log automatiquement :

```bash
# Logs applicatifs
tail -f logs/*.log

# Logs Docker
docker compose logs -f

# Logs appels (fichiers RAW)
ls -lh logs/calls/
```

**Format** : JSON optionnel (`STRUCTURED_LOGGING=true` dans `.env`)

---

## 🧪 Test

### Test Simple

```bash
# 1. Démarrer le serveur IA
sudo ./setup.sh

# 2. Configurer Asterisk (serveur distant)
# Voir asterisk_config.txt pour configuration complète

# 3. Composer le 777 depuis un téléphone SIP
# Vous devriez entendre : "Bonjour, bienvenue au SAV Wipple..."
```

### Exemple de Dialogue

```
Bot  : Bonjour, bienvenue au SAV Wipple. Comment puis-je vous aider ?
User : Bonjour, j'ai un problème avec ma connexion Internet.

Bot  : Avez-vous déjà un ticket en cours concernant ce problème ?
User : Non.

Bot  : Puis-je avoir votre nom et votre entreprise ?
User : Pierre Dupont de la société TechCorp.

Bot  : Merci Pierre. Pouvez-vous me décrire votre problème plus en détail ?
User : Ma box Internet ne fonctionne plus depuis ce matin.

Bot  : Je comprends. Essayez de débrancher votre box pendant 30 secondes,
       puis rebranchez-la. Attendez 2 minutes que les voyants se stabilisent.
User : D'accord, je vais essayer.

[Pause 2 minutes]

Bot  : Avez-vous pu faire la manipulation ? Est-ce que ça fonctionne maintenant ?
User : Oui, ça marche ! Merci beaucoup.

Bot  : Parfait ! Merci pour votre appel. Au revoir !
```

### Debug

```bash
# Vérifier connexion AudioSocket
netstat -tlnp | grep 9090

# Logs temps réel
tail -f logs/*.log

# Tester manuellement (telnet)
telnet SERVER_IP 9090
```

---

## 📚 Documentation

### Fichiers de documentation

| Fichier | Description |
|---------|-------------|
| [README.md](README.md) | Ce fichier - Vue d'ensemble complète |
| [REFACTOR.md](REFACTOR.md) | Architecture Clean détaillée + guide migration |
| [DASHBOARD_SECURITY.md](DASHBOARD_SECURITY.md) | Sécurité multi-IP dashboard (3 couches) |
| [MULTI_IP_SETUP.md](MULTI_IP_SETUP.md) | Configuration multi-Asterisk |
| [example_usage.py](example_usage.py) | Exemple utilisation Clean Architecture |
| [asterisk_config.txt](asterisk_config.txt) | Configuration Asterisk (serveur distant) |

### Guides pratiques

- **Installation** : Voir [Installation Automatisée](#-installation-automatisée)
- **Multi-IP Asterisk** : Voir [MULTI_IP_SETUP.md](MULTI_IP_SETUP.md)
- **Sécurité Dashboard** : Voir [DASHBOARD_SECURITY.md](DASHBOARD_SECURITY.md)
- **Architecture Clean** : Voir [REFACTOR.md](REFACTOR.md)

### Support

Pour toute question ou problème :
1. Consultez la documentation ci-dessus
2. Vérifiez les logs : `tail -f logs/*.log`
3. Testez les services : `docker compose ps`
4. Vérifiez le firewall : `sudo ufw status` et `sudo iptables -L DOCKER-USER`

---

## 🚀 Déploiement Production

### Systemd Service

Créer `/etc/systemd/system/voicebot.service` :

```ini
[Unit]
Description=Voicebot SAV Wipple IA
After=network.target docker.service
Requires=docker.service

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

Activer :

```bash
sudo systemctl daemon-reload
sudo systemctl enable voicebot
sudo systemctl start voicebot
sudo systemctl status voicebot
```

### Backup Automatisé

```bash
# Créer script backup
cat > /opt/PY_SAV/backup.sh <<'EOF'
#!/bin/bash
BACKUP_DIR=/backups/voicebot/$(date +%Y-%m-%d)
mkdir -p $BACKUP_DIR

# Backup PostgreSQL
docker compose exec -T postgres-clients pg_dump -U voicebot db_clients > $BACKUP_DIR/db_clients.sql
docker compose exec -T postgres-tickets pg_dump -U voicebot db_tickets > $BACKUP_DIR/db_tickets.sql

# Backup .env
cp .env $BACKUP_DIR/.env

# Backup logs calls (7 derniers jours)
find logs/calls -name "*.raw" -mtime -7 -exec cp {} $BACKUP_DIR/ \;

echo "Backup terminé : $BACKUP_DIR"
EOF

chmod +x /opt/PY_SAV/backup.sh

# Cron job (tous les jours à 2h)
crontab -e
# Ajouter :
0 2 * * * /opt/PY_SAV/backup.sh >> /var/log/voicebot_backup.log 2>&1
```

---

## 🔧 Dépannage

### Problème : Deepgram timeout

**Symptôme** : `Deepgram API error: timeout`

**Solution** :
1. Vérifier connexion internet
2. Augmenter `API_TIMEOUT` dans `config.py`
3. Système joue automatiquement message d'attente

### Problème : Dashboard inaccessible

**Symptôme** : Connection refused sur port 8501

**Solution** :
```bash
# Vérifier container
docker compose ps dashboard

# Vérifier firewall
sudo ufw status | grep 8501
sudo iptables -L DOCKER-USER -n | grep 8501

# Vérifier IP autorisée dans .env
grep PERSONAL_IP .env

# Relancer dashboard
docker compose restart dashboard
```

### Problème : Audio coupé

**Causes possibles** :
- Réseau saturé
- CPU surchargé
- Buffer audio trop petit

**Solution** :
```bash
# Réduire concurrent calls dans config.py
MAX_CONCURRENT_CALLS = 10

# Vérifier CPU
htop

# Vérifier réseau
ping deepgram.com
```

---

## 📊 Scalabilité

### Déploiement Multi-Serveurs

Pour > 40 appels simultanés :

```
┌─────────────┐
│  Asterisk   │
│ (Clients)   │
└──────┬──────┘
       │
   ┌───▼────┐
   │  HAProxy │  (Load Balancer)
   │  :9090   │
   └───┬────┘
       │
   ┌───┴─────────────────────┐
   │                         │
┌──▼───────┐          ┌──────▼───┐
│ IA Server│          │ IA Server│
│    #1    │          │    #2    │
│  :9090   │          │  :9090   │
└──────────┘          └──────────┘
       │                    │
       └────────┬───────────┘
                │
         ┌──────▼──────┐
         │  PostgreSQL │
         │  (Shared)   │
         └─────────────┘
```

### Cache Redis (optionnel)

Pour partager le cache audio entre serveurs :

```bash
# docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

Modifier `utils/audio.py` pour utiliser Redis au lieu de LRU local.

---

## 📄 Licence

**Copyright © 2025 Wipple - Tous droits réservés**

Ce logiciel est propriétaire. Toute utilisation, reproduction ou distribution non autorisée est strictement interdite.

---

## 🎯 Roadmap

- [x] ✅ Architecture Clean (Q4 2024)
- [x] ✅ Multi-IP Asterisk (Q4 2024)
- [x] ✅ Dashboard sécurisé (Q4 2024)
- [x] ✅ Endpointing dynamique (Q4 2024)
- [x] ✅ ElevenLabs Turbo v2.5 (Q4 2024)
- [ ] 🚧 Tests unitaires complets (Q1 2025)
- [ ] 🚧 CI/CD pipeline (Q1 2025)
- [ ] 🚧 A/B testing prompts (Q1 2025)
- [ ] 🚧 ML prédiction escalade (Q2 2025)
- [ ] 🚧 Multi-langues (Q2 2025)

---

**Développé avec ❤️ par l'équipe Wipple IA**

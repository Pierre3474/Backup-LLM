# Structure du Projet Voicebot SAV

Ce document décrit l'organisation des fichiers et dossiers du projet.

## Structure des Dossiers

```
Backup-LLM/
├── Fichiers de configuration
│   ├── config.py              # Configuration centralisée (API keys, timeouts, phrases)
│   ├── prompts.yaml           # Prompts pour l'IA conversationnelle
│   ├── stt_keywords.yaml      # Mots-clés pour la reconnaissance vocale
│   ├── system_prompt_base.yaml # Prompt système de base
│   ├── requirements.txt       # Dépendances Python
│   ├── Dockerfile            # Image Docker pour le voicebot
│   └── docker-compose.yml    # Orchestration des services
│
├── Code Source Principal
│   ├── server.py             # Serveur AudioSocket (cœur du voicebot)
│   ├── audio_utils.py        # Utilitaires audio (conversion, cache)
│   ├── db_utils.py           # Utilitaires base de données
│   ├── metrics.py            # Métriques Prometheus
│   └── generate_cache.py     # Génération du cache audio TTS
│
├── Base de Données
│   ├── init_clients.sql      # Initialisation DB clients
│   ├── init_tickets.sql      # Initialisation DB tickets
│   └── migrations/           # Migrations de schéma
│       ├── 002_increase_phone_number_length.sql
│       ├── 003_increase_phone_number_clients.sql
│       ├── 004_remove_transcript_add_client_info.sql
│       └── 005_add_companies_table.sql
│
├── Monitoring
│   └── monitoring/
│       ├── dashboard.py                      # Interface Streamlit de supervision
│       ├── prometheus.yml                    # Config Prometheus
│       └── grafana/
│           ├── provisioning/                 # Provisioning Grafana
│           └── dashboards/
│               └── voicebot-roi.json        # Dashboard ROI
│
├── Données de Test
│   ├── add_clement_dumas.sh       # Ajouter Clément DUMAS (Total)
│   ├── add_clement_dumas.sql      # SQL pour Clément DUMAS
│   ├── insert_test_clients.sql    # 35 clients + 11 entreprises
│   ├── load_test_data.sh          # Charger les données de test
│   └── clean_test_data.sh         # Nettoyer les données de test
│
├── Scripts Utilitaires
│   ├── setup.sh                   # Installation et génération du cache
│   └── scripts/
│       ├── reset_database.sh      # Réinitialiser la DB
│       └── reset_database.sql     # SQL de réinitialisation
│
├── Documentation
│   ├── README.md                  # Documentation principale
│   ├── STRUCTURE.md              # Ce fichier (structure du projet)
│   ├── docs/
│   │   ├── asterisk_config.txt   # Config Asterisk
│   │   ├── STT_KEYWORDS_GUIDE.md # Guide mots-clés STT
│   │   ├── guides/               # Guides détaillés
│   │   │   ├── ARCHITECTURE_HYBRIDE.md
│   │   │   ├── DASHBOARD_CONFIG.md
│   │   │   ├── DEPLOYMENT_GUIDE.md
│   │   │   ├── GRAFANA_GUIDE.md
│   │   │   ├── GUIDE_RESET.md
│   │   │   ├── MERGE_TO_MAIN_GUIDE.md
│   │   │   ├── APPLY_SECURITY_UPDATE.md
│   │   │   ├── SECURITY_ENV.md
│   │   │   ├── OPTIMISATION_RAPPELS.md
│   │   │   ├── PRONONCIATION_TTS.md
│   │   │   └── DONNEES_TEST.md
│   │   └── changelogs/           # Historique des changements
│   │       ├── CHANGELOG_CONVERSATION_FLOW.md
│   │       ├── CHANGELOG_DEBUG.md
│   │       ├── RECAP_FINAL.md
│   │       └── STATUS_FIXES.md
│
├── Données Runtime
│   ├── assets/cache/             # Cache audio TTS (34 phrases .raw)
│   ├── cache/                    # Cache temporaire
│   ├── logs/calls/               # Logs des appels (par date)
│   └── __pycache__/              # Cache Python
│
└── Configuration Privée (non versionné)
    └── .env                      # Variables d'environnement (secrets)
```

## Fichiers Clés

### Configuration

| Fichier | Description |
|---------|-------------|
| `config.py` | Configuration centralisée (API keys, timeouts, phrases cachées) |
| `.env` | Secrets (DEEPGRAM_API_KEY, GROQ_API_KEY, ELEVENLABS_API_KEY, DB passwords) |
| `prompts.yaml` | Prompts pour l'IA conversationnelle (Groq) |
| `stt_keywords.yaml` | Mots-clés pour améliorer la reconnaissance vocale (Deepgram) |

### Code Source

| Fichier | Description | Lignes |
|---------|-------------|--------|
| `server.py` | Serveur AudioSocket, gestion des appels, flow conversationnel | ~1500 |
| `audio_utils.py` | Conversion audio, gestion du cache | ~200 |
| `db_utils.py` | Connexions DB, requêtes clients/tickets | ~150 |
| `metrics.py` | Métriques Prometheus (latence, cache hits, coûts) | ~100 |
| `monitoring/dashboard.py` | Interface Streamlit pour supervision des tickets | ~300 |

### Scripts Principaux

| Script | Usage | Description |
|--------|-------|-------------|
| `setup.sh` | `./setup.sh` | Installation complète + génération cache audio |
| `add_clement_dumas.sh` | `./add_clement_dumas.sh` | Ajouter Clément DUMAS (Total) |
| `load_test_data.sh` | `./load_test_data.sh` | Charger 35 clients de test |
| `clean_test_data.sh` | `./clean_test_data.sh` | Supprimer les données de test |

### Base de Données

| Fichier | Description |
|---------|-------------|
| `init_clients.sql` | Initialisation table clients (phone, name, company, box_model) |
| `init_tickets.sql` | Initialisation table tickets (problem, severity, status) |
| `migrations/` | Migrations progressives du schéma |

## Organisation par Fonction

### Développement
- Code source : `server.py`, `*.py`
- Configuration : `config.py`, `.env`

### Déploiement
- Docker : `Dockerfile`, `docker-compose.yml`
- Installation : `setup.sh`
- Guides : `docs/guides/DEPLOYMENT_GUIDE.md`

### Monitoring
- Métriques : `metrics.py`
- Prometheus : `monitoring/prometheus.yml`
- Grafana : `monitoring/grafana/`
- Dashboard : `monitoring/dashboard.py`

### Documentation
- README principal : `README.md`
- Guides détaillés : `docs/guides/`
- Changelogs : `docs/changelogs/`
- Structure : `STRUCTURE.md` (ce fichier)

### Données de Test
- Scripts : `add_clement_dumas.sh`, `load_test_data.sh`
- SQL : `insert_test_clients.sql`
- Guide : `docs/guides/DONNEES_TEST.md`

## Flux de Travail Typique

### Première Installation
```bash
# 1. Cloner le repo
git clone <repo>

# 2. Configurer l'environnement
cp .env.example .env
nano .env  # Remplir les API keys

# 3. Installation complète
./setup.sh

# 4. Lancer les services
docker compose up -d
```

### Ajouter des Données de Test
```bash
# Client principal
./add_clement_dumas.sh

# 35 clients de test
./load_test_data.sh
```

### Monitoring
- **Dashboard Streamlit** : http://localhost:8501
- **Grafana ROI** : http://localhost:3000 (admin/voicebot2024)
- **Prometheus** : http://localhost:9092

### Développement
```bash
# Modifier le code
nano server.py

# Rebuild l'image
docker compose build voicebot

# Redémarrer
docker compose up -d voicebot

# Voir les logs
docker logs -f voicebot-app
```

## Cache Audio

Le cache audio contient **34 phrases pré-générées** en format `.raw` (8kHz, mono, 16-bit) :

```
assets/cache/
├── greet.raw
├── welcome.raw
├── returning_client_pending_internet.raw  # ← Nouveaux (optimisation)
├── returning_client_pending_mobile.raw
├── returning_client_no_ticket.raw
├── ask_identity.raw
├── ask_email.raw
├── ...
└── error.raw
```

**Performance** : Cache hit = ~100ms vs API TTS = 1-2s (90% plus rapide)

## Fichiers Sensibles (non versionés)

Ces fichiers contiennent des secrets et **ne doivent JAMAIS** être versionés :

- `.env` - Clés API, mots de passe
- `assets/cache/*.raw` - Cache audio (généré localement)
- `logs/calls/` - Logs d'appels (données clients)
- `venv/` - Environnement virtuel Python

Vérifiez `.gitignore` pour la liste complète.

## 📖 Guides Disponibles

| Guide | Emplacement | Description |
|-------|-------------|-------------|
| Installation | `docs/guides/DEPLOYMENT_GUIDE.md` | Déploiement complet |
| Architecture | `docs/guides/ARCHITECTURE_HYBRIDE.md` | Architecture hybride cache/dynamique |
| Sécurité | `docs/guides/SECURITY_ENV.md` | Gestion des secrets |
| Grafana | `docs/guides/GRAFANA_GUIDE.md` | Configuration monitoring |
| Dashboard | `docs/guides/DASHBOARD_CONFIG.md` | Configuration Streamlit |
| Reset | `docs/guides/GUIDE_RESET.md` | Réinitialisation complète |
| Données Test | `docs/guides/DONNEES_TEST.md` | Gestion des données de test |
| Prononciation | `docs/guides/PRONONCIATION_TTS.md` | Amélioration TTS |
| Optimisation | `docs/guides/OPTIMISATION_RAPPELS.md` | Optimisation vitesse rappels |

## Changelog

L'historique des changements est documenté dans `docs/changelogs/` :

- `CHANGELOG_CONVERSATION_FLOW.md` - Évolution du flow conversationnel
- `CHANGELOG_DEBUG.md` - Corrections de bugs
- `RECAP_FINAL.md` - Résumé final des améliorations
- `STATUS_FIXES.md` - État des corrections

## 🤝 Contribution

Pour contribuer au projet :

1. Créer une branche feature : `git checkout -b feature/ma-fonctionnalite`
2. Faire les modifications
3. Committer : `git commit -m "feat: description"`
4. Push : `git push origin feature/ma-fonctionnalite`
5. Créer une Pull Request

Voir `docs/guides/MERGE_TO_MAIN_GUIDE.md` pour les détails.

## Support

Pour toute question, voir :
- `README.md` - Documentation principale
- `docs/guides/` - Guides détaillés
- Logs : `docker logs voicebot-app`

---

**Version** : 2.0 (Décembre 2025)
**Dernière mise à jour** : 31/12/2025

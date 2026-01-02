# 🔐 Guide de Sécurité - Variables d'Environnement

## 📋 Vue d'Ensemble

Toutes les informations sensibles (mots de passe, clés API, etc.) sont maintenant stockées dans le fichier `.env` et **jamais** dans le code source ou dans `docker-compose.yml`.

---

## ✅ Ce qui a été Sécurisé

| Variable | Description | Où c'était avant | Maintenant |
|----------|-------------|------------------|------------|
| `DB_PASSWORD` | Mot de passe PostgreSQL | Hardcodé dans docker-compose.yml | `.env` |
| `GRAFANA_ADMIN_USER` | Username Grafana | Hardcodé dans docker-compose.yml | `.env` |
| `GRAFANA_ADMIN_PASSWORD` | Mot de passe Grafana | Hardcodé dans docker-compose.yml | `.env` |
| `ELEVENLABS_API_KEY` | Clé API ElevenLabs | `.env` | `.env` ✅ |
| `DEEPGRAM_API_KEY` | Clé API Deepgram | `.env` | `.env` ✅ |
| `GROQ_API_KEY` | Clé API Groq | `.env` | `.env` ✅ |
| `AMI_PASSWORD` | Mot de passe Asterisk AMI | `.env` | `.env` ✅ |

---

## 🚀 Configuration Initiale

### 1. Copier le Fichier Template

```bash
cd ~/Backup-LLM

# Copier .env.example vers .env
cp .env.example .env
```

### 2. Éditer le Fichier .env

```bash
# Éditer avec votre éditeur préféré
nano .env
# ou
vim .env
```

### 3. Modifier les Valeurs Sensibles

**IMPORTANT** : Changez au minimum ces variables :

```bash
# Base de données
DB_PASSWORD=VotreMotDePassePostgreSQL_Fort_Ici

# Grafana
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=VotreMotDePasseGrafana_Fort_Ici

# Clés API (remplacez par vos vraies clés)
ELEVENLABS_API_KEY=sk_votre_vraie_cle_elevenlabs
DEEPGRAM_API_KEY=votre_vraie_cle_deepgram
GROQ_API_KEY=gsk_votre_vraie_cle_groq

# Asterisk
AMI_PASSWORD=VotreMotDePasseAMI_Fort_Ici
```

---

## 🔒 Bonnes Pratiques de Sécurité

### ✅ À FAIRE

1. **Changez TOUS les mots de passe par défaut**
   ```bash
   # Génération de mot de passe fort
   openssl rand -base64 32
   ```

2. **Ne committez JAMAIS le fichier .env**
   - Le `.env` est déjà dans `.gitignore`
   - Vérifiez avant chaque commit :
   ```bash
   git status  # .env ne doit PAS apparaître
   ```

3. **Utilisez des mots de passe forts**
   - Minimum 16 caractères
   - Mélange de lettres, chiffres, symboles
   - Unique pour chaque service

4. **Limitez les permissions du fichier .env**
   ```bash
   chmod 600 .env  # Lecture/écriture uniquement pour le propriétaire
   ```

5. **Sauvegardez le .env de manière sécurisée**
   - Utilisez un gestionnaire de mots de passe (1Password, Bitwarden)
   - Ou chiffrez-le : `gpg -c .env` (crée .env.gpg)

6. **Rotez les clés API régulièrement**
   - Changez vos clés API tous les 90 jours
   - Si une clé est compromise, régénérez-la immédiatement

---

### ❌ À NE JAMAIS FAIRE

1. ❌ **Ne committez JAMAIS le .env dans Git**
   ```bash
   # Si vous avez accidentellement commité .env :
   git rm --cached .env
   git commit -m "Remove .env from git"
   git push
   # Puis changez TOUTES vos clés/mots de passe !
   ```

2. ❌ **Ne partagez JAMAIS le .env par email/chat**
   - Utilisez des canaux sécurisés (ex: partage chiffré)

3. ❌ **Ne loggez JAMAIS les variables sensibles**
   ```python
   # ❌ MAUVAIS
   logger.info(f"API Key: {api_key}")

   # ✅ BON
   logger.info("API Key configured successfully")
   ```

4. ❌ **N'utilisez JAMAIS les mots de passe par défaut en production**

5. ❌ **Ne stockez JAMAIS les secrets dans le code**
   ```python
   # ❌ MAUVAIS
   password = "hardcoded_password"

   # ✅ BON
   password = os.getenv("DB_PASSWORD")
   ```

---

## 🔄 Mise à Jour des Variables

### Changer un Mot de Passe

**Exemple : Changer le mot de passe PostgreSQL**

```bash
# 1. Arrêter les conteneurs
docker compose down

# 2. Modifier .env
nano .env
# Changez DB_PASSWORD=nouveau_mot_de_passe_fort

# 3. Supprimer les volumes PostgreSQL (les données seront perdues !)
docker volume rm backup-llm_postgres_clients_data
docker volume rm backup-llm_postgres_tickets_data

# 4. Redémarrer avec le nouveau mot de passe
docker compose up -d

# 5. Vérifier
docker logs voicebot-db-clients
docker logs voicebot-db-tickets
```

**⚠️ ATTENTION** : Changer le mot de passe PostgreSQL supprime les données !

---

### Changer le Mot de Passe Grafana

```bash
# 1. Modifier .env
nano .env
# Changez GRAFANA_ADMIN_PASSWORD=nouveau_mot_de_passe

# 2. Supprimer le volume Grafana
docker compose down
docker volume rm backup-llm_grafana_data

# 3. Redémarrer
docker compose up -d grafana

# 4. Se connecter avec le nouveau mot de passe
# http://145.239.223.188:3000
```

---

### Régénérer une Clé API

**Exemple : Nouvelle clé ElevenLabs**

```bash
# 1. Obtenir une nouvelle clé depuis ElevenLabs
# https://elevenlabs.io/app/settings/api-keys

# 2. Modifier .env
nano .env
# Changez ELEVENLABS_API_KEY=sk_nouvelle_cle

# 3. Redémarrer le voicebot
docker restart voicebot-app

# 4. Vérifier les logs
docker logs -f voicebot-app | grep -i elevenlabs
```

---

## 🔍 Vérification de la Sécurité

### Checklist de Sécurité

```bash
# 1. Vérifier que .env n'est PAS tracké par Git
git status | grep .env
# Résultat attendu : rien (ou "Untracked" mais jamais "Changes to be committed")

# 2. Vérifier les permissions du .env
ls -la .env
# Résultat attendu : -rw------- (600)

# 3. Vérifier qu'aucun secret n'est dans docker-compose.yml
grep -i "password\|api_key\|secret" docker-compose.yml
# Résultat attendu : uniquement des ${VARIABLE}

# 4. Vérifier que tous les services utilisent .env
docker compose config | grep -A 5 environment
```

---

## 📊 Variables d'Environnement Requises

### Obligatoires

| Variable | Description | Exemple |
|----------|-------------|---------|
| `DB_PASSWORD` | Mot de passe PostgreSQL | `VotreMotDePasse123!` |
| `DB_CLIENTS_DSN` | Connexion DB clients | `postgresql://voicebot:pass@host:5432/db_clients` |
| `DB_TICKETS_DSN` | Connexion DB tickets | `postgresql://voicebot:pass@host:5432/db_tickets` |
| `ELEVENLABS_API_KEY` | Clé API ElevenLabs | `sk_abc123...` |
| `DEEPGRAM_API_KEY` | Clé API Deepgram | `xyz789...` |
| `GROQ_API_KEY` | Clé API Groq | `gsk_def456...` |
| `ASTERISK_HOST` | IP serveur Asterisk | `145.239.223.188` |
| `AMI_USERNAME` | Username AMI | `admin` |
| `AMI_PASSWORD` | Mot de passe AMI | `VotreMotDePasse!` |

---

### Optionnelles

| Variable | Description | Défaut |
|----------|-------------|--------|
| `GRAFANA_ADMIN_USER` | Username Grafana | `admin` |
| `GRAFANA_ADMIN_PASSWORD` | Mot de passe Grafana | `voicebot2024` |
| `PERSONAL_IP` | IPs autorisées dashboard | `` (vide = tous) |
| `LOG_LEVEL` | Niveau de log | `INFO` |
| `DEBUG` | Mode debug | `false` |
| `TZ` | Fuseau horaire | `Europe/Paris` |

---

## 🚨 En Cas de Fuite de Secrets

### Si vous avez accidentellement exposé des secrets :

1. **Régénérez IMMÉDIATEMENT toutes les clés compromises**
   - ElevenLabs : https://elevenlabs.io/app/settings/api-keys
   - Deepgram : https://console.deepgram.com/project/*/keys
   - Groq : https://console.groq.com/keys

2. **Changez tous les mots de passe**
   ```bash
   # Générer de nouveaux mots de passe
   openssl rand -base64 32  # PostgreSQL
   openssl rand -base64 32  # Grafana
   openssl rand -base64 32  # AMI
   ```

3. **Si commité dans Git, nettoyez l'historique**
   ```bash
   # ATTENTION : Opération dangereuse !
   git filter-branch --force --index-filter \
     'git rm --cached --ignore-unmatch .env' \
     --prune-empty --tag-name-filter cat -- --all

   git push origin --force --all
   ```

4. **Vérifiez les logs d'accès**
   - Vérifiez si les clés ont été utilisées de manière suspecte
   - Consultez les dashboards des services (ElevenLabs, Deepgram, Groq)

---

## 📝 Template de Sauvegarde Sécurisée

Pour sauvegarder votre `.env` de manière sécurisée :

```bash
# Chiffrer le fichier .env
gpg --symmetric --cipher-algo AES256 .env

# Résultat : .env.gpg (fichier chiffré)
# Vous pouvez maintenant sauvegarder .env.gpg dans le cloud

# Pour déchiffrer :
gpg --decrypt .env.gpg > .env
```

---

## ✅ Résumé

| Action | Status |
|--------|--------|
| Mots de passe PostgreSQL dans .env | ✅ Fait |
| Identifiants Grafana dans .env | ✅ Fait |
| .env dans .gitignore | ✅ Fait |
| .env.example créé | ✅ Fait |
| Documentation sécurité | ✅ Fait |
| Variables hardcodées supprimées | ✅ Fait |

---

**🔒 Vos secrets sont maintenant sécurisés !**

**Rappel** : Changez TOUS les mots de passe par défaut avant de déployer en production.

---

**Date** : 2025-12-31
**Version** : 2.2
**Sécurité** : ✅ Renforcée

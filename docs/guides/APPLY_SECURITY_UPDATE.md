# 🔐 Application de la Mise à Jour de Sécurité

## ✅ Ce qui a été fait

Toutes les informations sensibles ont été déplacées du fichier `docker-compose.yml` vers le fichier `.env` pour une meilleure sécurité.

**Variables déplacées** :
- `DB_PASSWORD` (PostgreSQL)
- `GRAFANA_ADMIN_USER` (Grafana)
- `GRAFANA_ADMIN_PASSWORD` (Grafana)

---

## 🚀 Comment Appliquer sur Votre Serveur

### Étape 1 : Récupérer les Modifications

```bash
cd ~/Backup-LLM

# Récupérer les dernières modifications
git pull origin claude/fix-all-issues-ssGib
```

---

### Étape 2 : Migrer le Fichier .env

**Option A : Migration Automatique (Recommandé)**

```bash
# Lancer le script de migration
./migrate_env.sh
```

Le script va :
- ✅ Créer un backup de votre `.env` actuel
- ✅ Ajouter les variables manquantes (`GRAFANA_ADMIN_USER`, `GRAFANA_ADMIN_PASSWORD`)
- ✅ Afficher les variables à vérifier

---

**Option B : Migration Manuelle**

Si vous préférez faire manuellement :

```bash
# Éditer votre .env
nano .env
```

**Ajoutez ces lignes si elles n'existent pas** :

```bash
# ===================================================================
# GRAFANA - DASHBOARD DE MONITORING
# ===================================================================
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=voicebot2024

# ===================================================================
# BASE DE DONNÉES POSTGRESQL
# ===================================================================
# Si DB_PASSWORD n'existe pas déjà
DB_PASSWORD=voicebot_secure_2024
```

---

### Étape 3 : Vérifier le Fichier .env

Vérifiez que votre `.env` contient au minimum :

```bash
# Variables OBLIGATOIRES

# PostgreSQL
DB_PASSWORD=votre_mot_de_passe
DB_CLIENTS_DSN=postgresql://voicebot:votre_mot_de_passe@postgres-clients:5432/db_clients
DB_TICKETS_DSN=postgresql://voicebot:votre_mot_de_passe@postgres-tickets:5432/db_tickets

# Grafana
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=votre_mot_de_passe_grafana

# APIs
ELEVENLABS_API_KEY=sk_...
DEEPGRAM_API_KEY=...
GROQ_API_KEY=gsk_...

# Asterisk
ASTERISK_HOST=145.239.223.188
AMI_USERNAME=admin
AMI_PASSWORD=votre_mot_de_passe_ami
```

---

### Étape 4 : Redémarrer les Services

```bash
# Arrêter tous les conteneurs
docker compose down

# Redémarrer avec les nouvelles variables
docker compose up -d

# Attendre 30 secondes que tout démarre
sleep 30

# Vérifier que tout tourne
docker ps
```

**Résultat attendu** :
```
voicebot-app          ✅ Up
voicebot-db-clients   ✅ Up
voicebot-db-tickets   ✅ Up
voicebot-dashboard    ✅ Up
voicebot-grafana      ✅ Up
voicebot-prometheus   ✅ Up
```

---

### Étape 5 : Tester les Accès

**Tester Grafana** :
```
URL: http://145.239.223.188:3000
Username: admin
Password: (celui défini dans GRAFANA_ADMIN_PASSWORD)
```

**Tester le Dashboard** :
```
URL: http://145.239.223.188:8501
```

**Tester les Métriques** :
```bash
curl http://localhost:9091/ | head -20
```

---

## 🔒 Sécurité - Actions Recommandées

### 1. Changez les Mots de Passe par Défaut

⚠️ **IMPORTANT** : Ne gardez PAS les mots de passe par défaut en production !

```bash
# Générer un mot de passe fort
openssl rand -base64 32
```

**Modifiez dans .env** :
```bash
DB_PASSWORD=VotreNouveauMotDePasseFort123!
GRAFANA_ADMIN_PASSWORD=VotreNouveauMotDePasseGrafana456!
```

---

### 2. Sécurisez le Fichier .env

```bash
# Limiter les permissions (lecture/écriture uniquement pour le propriétaire)
chmod 600 .env

# Vérifier
ls -la .env
# Résultat attendu : -rw------- (600)
```

---

### 3. Vérifiez que .env N'est PAS dans Git

```bash
# Vérifier
git status | grep .env

# Si .env apparaît comme "Changes to be committed" : DANGER !
# Annulez immédiatement :
git reset HEAD .env
```

Le fichier `.env` **ne doit JAMAIS** être commité dans Git.

---

## ⚠️ Si Quelque Chose Ne Fonctionne Pas

### Problème 1 : Grafana "Invalid username or password"

**Cause** : Variable `GRAFANA_ADMIN_PASSWORD` manquante ou incorrecte

**Solution** :
```bash
# Vérifier que la variable existe
grep GRAFANA_ADMIN_PASSWORD .env

# Si absente, l'ajouter
echo "GRAFANA_ADMIN_PASSWORD=voicebot2024" >> .env

# Redémarrer Grafana
docker restart voicebot-grafana

# Tester à nouveau
```

---

### Problème 2 : PostgreSQL ne démarre pas

**Cause** : Variable `DB_PASSWORD` manquante

**Solution** :
```bash
# Vérifier
grep DB_PASSWORD .env

# Si absente, l'ajouter
echo "DB_PASSWORD=voicebot_secure_2024" >> .env

# Redémarrer
docker compose down
docker compose up -d
```

---

### Problème 3 : Dashboard ne se connecte pas à la DB

**Cause** : `DB_TICKETS_DSN` incorrect ou manquant

**Solution** :
```bash
# Vérifier
grep DB_TICKETS_DSN .env

# Corriger (remplacez par votre mot de passe)
DB_TICKETS_DSN=postgresql://voicebot:voicebot_secure_2024@postgres-tickets:5432/db_tickets

# Redémarrer le dashboard
docker restart voicebot-dashboard
```

---

## 📋 Checklist Complète

Après la mise à jour, vérifiez :

- [ ] `.env` contient `GRAFANA_ADMIN_USER`
- [ ] `.env` contient `GRAFANA_ADMIN_PASSWORD`
- [ ] `.env` contient `DB_PASSWORD`
- [ ] Tous les conteneurs démarrés (`docker ps`)
- [ ] Grafana accessible (http://145.239.223.188:3000)
- [ ] Dashboard accessible (http://145.239.223.188:8501)
- [ ] Connexion Grafana fonctionne
- [ ] Permissions .env sécurisées (`chmod 600`)
- [ ] `.env` pas dans git (`git status`)
- [ ] Backup de l'ancien .env créé

---

## 📊 Nouveaux Fichiers Créés

| Fichier | Description |
|---------|-------------|
| `.env.example` | Template avec toutes les variables |
| `SECURITY_ENV.md` | Guide de sécurité complet |
| `migrate_env.sh` | Script de migration automatique |
| `APPLY_SECURITY_UPDATE.md` | Ce fichier |

---

## 🆘 Support

Si vous rencontrez un problème :

1. **Vérifier les logs** :
   ```bash
   docker logs voicebot-grafana
   docker logs voicebot-app
   docker logs voicebot-dashboard
   ```

2. **Restaurer le backup** :
   ```bash
   # Si migration automatique
   cp .env.backup.YYYYMMDD_HHMMSS .env
   docker compose restart
   ```

3. **Recréer .env depuis .env.example** :
   ```bash
   cp .env.example .env
   nano .env  # Configurer vos clés
   docker compose restart
   ```

---

## ✅ Résumé

1. `git pull origin claude/fix-all-issues-ssGib`
2. `./migrate_env.sh`
3. Vérifier `.env`
4. `docker compose down && docker compose up -d`
5. Tester Grafana et Dashboard
6. Changer les mots de passe par défaut
7. `chmod 600 .env`

**🔒 Vos secrets sont maintenant sécurisés !**

---

**Date** : 2025-12-31
**Version** : 2.2
**Commit** : `d6bd454 - security: Déplacement de toutes les informations sensibles dans .env`

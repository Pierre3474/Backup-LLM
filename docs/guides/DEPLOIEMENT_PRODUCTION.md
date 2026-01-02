# Guide de Déploiement PRODUCTION

Guide complet pour déployer le Voicebot SAV Wipple en production de manière sécurisée.

## Prérequis

### Système
- Ubuntu 20.04+ / Debian 11+ (recommandé)
- Docker 24.0+
- Docker Compose 2.0+
- Minimum 2 CPU, 4 GB RAM
- 20 GB d'espace disque

### Comptes API nécessaires
- [ ] Compte **ElevenLabs** avec API Key et Voice ID
- [ ] Compte **Deepgram** avec API Key
- [ ] Compte **Groq** avec API Key
- [ ] Serveur **Asterisk** avec accès AMI configuré

---

## Étape 1 : Installation sur le serveur

### 1.1 Cloner le dépôt

```bash
# Cloner le projet
git clone https://github.com/Pierre3474/Backup-LLM.git
cd Backup-LLM

# Se placer sur la branche principale
git checkout main
```

### 1.2 Créer le fichier .env de production

```bash
# Copier le template
cp .env.example .env

# Éditer avec vos vraies valeurs
nano .env
```

**IMPORTANT : Remplacez TOUTES les valeurs placeholders !**

---

## Étape 2 : Configuration du fichier .env

### 2.1 Générer des mots de passe forts

```bash
# Générer un mot de passe pour la base de données
openssl rand -base64 32

# Générer un mot de passe pour Grafana
openssl rand -base64 24
```

### 2.2 Variables obligatoires à configurer

#### API Keys (services IA)
```bash
# ElevenLabs - https://elevenlabs.io/app/settings/api-keys
ELEVENLABS_API_KEY=sk_votre_vraie_cle_ici
ELEVENLABS_VOICE_ID=votre_voice_id_reel_ici

# Deepgram - https://console.deepgram.com/
DEEPGRAM_API_KEY=votre_vraie_cle_ici

# Groq - https://console.groq.com/
GROQ_API_KEY=gsk_votre_vraie_cle_ici
```

#### Base de données
```bash
# Utilisez les mots de passe générés à l'étape 2.1
DB_PASSWORD=mot_de_passe_fort_genere

# Remplacez CHANGEZ_CE_MOT_DE_PASSE par votre DB_PASSWORD dans les DSN
DB_CLIENTS_DSN=postgresql://voicebot:mot_de_passe_fort_genere@postgres-clients:5432/db_clients
DB_TICKETS_DSN=postgresql://voicebot:mot_de_passe_fort_genere@postgres-tickets:5432/db_tickets
```

#### Asterisk AMI
```bash
# IP de votre serveur Asterisk
ASTERISK_HOST=IP_DE_VOTRE_ASTERISK

# Credentials AMI (définis dans /etc/asterisk/manager.conf)
AMI_USERNAME=votre_user_ami
AMI_SECRET=votre_mot_de_passe_ami_reel
```

#### Grafana
```bash
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=mot_de_passe_grafana_fort
```

#### Serveur
```bash
# IP publique de votre serveur
SERVER_IP=IP_PUBLIQUE_SERVEUR
```

### 2.3 Vérifier la configuration

Le script de démarrage vérifiera automatiquement que toutes les variables sont configurées.

---

## Étape 3 : Démarrage en production

### 3.1 Utiliser le script de démarrage automatique

```bash
# Lancer le script de démarrage production
./start-prod.sh
```

Le script va :
1. ✓ Vérifier que le fichier `.env` existe
2. ✓ Valider toutes les variables critiques
3. ✓ Vérifier que les placeholders sont remplacés
4. ✓ Vérifier l'installation de Docker
5. ✓ Vérifier la disponibilité des ports
6. ✓ Construire et démarrer les services

### 3.2 Démarrage manuel (alternatif)

Si vous préférez le contrôle manuel :

```bash
# 1. Construire les images
docker compose build --no-cache

# 2. Démarrer tous les services
docker compose up -d

# 3. Vérifier les logs
docker compose logs -f voicebot
```

---

## Étape 4 : Vérifications post-démarrage

### 4.1 Vérifier que tous les services sont UP

```bash
docker compose ps
```

Résultat attendu : tous les services doivent être "Up" et "healthy".

### 4.2 Vérifier les logs du voicebot

```bash
docker compose logs voicebot | tail -30
```

Vous devriez voir :
```
✓ Database pools ready
✓ Metrics server ready
Cache loaded: 34 phrases
AudioSocket Server started on 0.0.0.0:9090
```

### 4.3 Tester les endpoints

```bash
# Prometheus metrics
curl http://localhost:9091/metrics

# Prometheus UI
curl http://localhost:9092

# Grafana (devrait rediriger vers login)
curl -I http://localhost:3000
```

---

## Étape 5 : Configuration Asterisk

### 5.1 Configurer AudioSocket dans Asterisk

Éditez `/etc/asterisk/extensions.conf` sur votre serveur Asterisk :

```conf
[from-trunk]
exten => VOTRE_NUMERO_DID,1,NoOp(Appel SAV - Voicebot)
same => n,Answer()
same => n,AudioSocket(uuid,IP_SERVEUR_VOICEBOT:9090)
same => n,Hangup()
```

Remplacez :
- `VOTRE_NUMERO_DID` : Le numéro SDA qui arrive sur le serveur Asterisk
- `IP_SERVEUR_VOICEBOT` : L'IP du serveur où tourne le voicebot

### 5.2 Recharger Asterisk

```bash
asterisk -rx "dialplan reload"
```

### 5.3 Tester un appel

Appelez le numéro DID configuré. Vous devriez entendre :
> "Bonjour, et bienvenue au service technique de chez Wipple. Je suis Éco, votre assistant virtuel..."

---

## Étape 6 : Sécurité et Firewall

### 6.1 Configurer le firewall (ufw)

```bash
# Autoriser SSH (si pas déjà fait)
ufw allow 22/tcp

# Autoriser AudioSocket UNIQUEMENT depuis Asterisk
ufw allow from IP_ASTERISK to any port 9090 proto tcp comment "AudioSocket Asterisk"

# Autoriser Grafana (si accès externe souhaité)
ufw allow 3000/tcp comment "Grafana Dashboard"

# Activer le firewall
ufw enable
```

### 6.2 Bloquer les connexions non-Asterisk

Le voicebot rejette automatiquement :
- Requêtes HTTP/HTTPS (scanneurs)
- Connexions RDP
- Handshakes TLS/SSL

Mais ajoutez quand même une règle firewall pour limiter l'exposition.

---

## Étape 7 : Monitoring et Dashboards

### 7.1 Accéder à Grafana

1. Ouvrez http://IP_SERVEUR:3000
2. Connectez-vous avec :
   - User : `admin`
   - Password : Celui défini dans `.env` (`GRAFANA_ADMIN_PASSWORD`)
3. Le dashboard "Voicebot ROI" est automatiquement provisionné

### 7.2 Accéder au Dashboard Streamlit

1. Ouvrez http://IP_SERVEUR:8501
2. Supervision temps réel des tickets

---

## Étape 8 : Maintenance

### 8.1 Voir les logs en temps réel

```bash
# Tous les services
docker compose logs -f

# Seulement le voicebot
docker compose logs -f voicebot

# Seulement les bases de données
docker compose logs -f postgres-clients postgres-tickets
```

### 8.2 Redémarrer un service

```bash
# Redémarrer le voicebot seul
docker compose restart voicebot

# Redémarrer tous les services
docker compose restart
```

### 8.3 Arrêter complètement

```bash
docker compose down
```

### 8.4 Mettre à jour le code

```bash
# Pull les dernières modifications
git pull origin main

# Rebuild et redémarrer
docker compose build --no-cache
docker compose up -d

# Vérifier les logs
docker compose logs -f voicebot
```

---

## Étape 9 : Sauvegarde des données

### 9.1 Volumes Docker persistants

Les données sont stockées dans :
- `postgres_clients_data` : Base clients
- `postgres_tickets_data` : Base tickets
- `prometheus_data` : Métriques historiques
- `grafana_data` : Configuration Grafana

### 9.2 Backup manuel

```bash
# Backup de la base clients
docker exec voicebot-db-clients pg_dump -U voicebot db_clients > backup_clients_$(date +%Y%m%d).sql

# Backup de la base tickets
docker exec voicebot-db-tickets pg_dump -U voicebot db_tickets > backup_tickets_$(date +%Y%m%d).sql
```

### 9.3 Restauration

```bash
# Restaurer la base clients
cat backup_clients_YYYYMMDD.sql | docker exec -i voicebot-db-clients psql -U voicebot -d db_clients

# Restaurer la base tickets
cat backup_tickets_YYYYMMDD.sql | docker exec -i voicebot-db-tickets psql -U voicebot -d db_tickets
```

---

## Dépannage

### Le voicebot refuse de démarrer

**Vérifiez les logs :**
```bash
docker compose logs voicebot
```

**Erreurs courantes :**

1. **"Configuration .env incomplète"**
   - Vérifiez que toutes les variables sont définies dans `.env`
   - Vérifiez qu'aucun placeholder n'est resté (CHANGEZ_CE_MOT_DE_PASSE, etc.)

2. **"Failed to initialize database pools"**
   - Vérifiez que les bases PostgreSQL sont bien démarrées : `docker compose ps`
   - Vérifiez les credentials dans `DB_CLIENTS_DSN` et `DB_TICKETS_DSN`

3. **"Port 9090 already in use"**
   - Arrêtez le service qui utilise le port : `lsof -i :9090`
   - Ou changez le port dans `docker-compose.yml`

### Aucun appel ne fonctionne

1. **Vérifier la connectivité Asterisk → Voicebot**
   ```bash
   # Depuis le serveur Asterisk
   telnet IP_VOICEBOT 9090
   ```

2. **Vérifier les logs Asterisk**
   ```bash
   asterisk -rvvv
   # Puis passer un appel test
   ```

3. **Vérifier le firewall**
   ```bash
   ufw status
   # Le port 9090 doit être accessible depuis l'IP Asterisk
   ```

### Les métriques ne s'affichent pas dans Grafana

1. **Vérifier que Prometheus collecte les métriques**
   ```bash
   curl http://localhost:9091/metrics
   ```

2. **Vérifier la connexion Grafana ↔ Prometheus**
   - Ouvrez Grafana → Configuration → Data Sources
   - Prometheus devrait être "Connected"

---

## Checklist finale de déploiement

- [ ] Fichier `.env` créé et toutes les variables configurées
- [ ] Aucun placeholder (CHANGEZ, VOTRE, etc.) dans `.env`
- [ ] API Keys valides (ElevenLabs, Deepgram, Groq)
- [ ] Asterisk configuré avec AudioSocket
- [ ] Firewall configuré (port 9090 limité à Asterisk)
- [ ] Tous les services Docker UP et healthy
- [ ] Logs du voicebot sans erreur
- [ ] Appel test réussi
- [ ] Grafana accessible et dashboard visible
- [ ] Sauvegarde automatique configurée (optionnel)

---

## Support

- **Documentation complète :** README.md
- **Sécurité .env :** docs/guides/SECURITY_ENV.md
- **Structure projet :** STRUCTURE.md
- **Issues GitHub :** https://github.com/Pierre3474/Backup-LLM/issues

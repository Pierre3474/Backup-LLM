#  Guide de Déploiement et Mise à Jour

## Table des Matières

1. [Déploiement Initial](#déploiement-initial)
2. [Mise à Jour du Serveur](#mise-à-jour-du-serveur)
3. [Options de Reset](#options-de-reset)
4. [Débogage des Conversations](#débogage-des-conversations)
5. [Monitoring en Production](#monitoring-en-production)

---

## Déploiement Initial

### Prérequis
- Serveur Debian 12/13
- Accès root (sudo)
- Git installé

### Étapes d'installation

```bash
# 1. Cloner le dépôt
git clone https://github.com/Pierre3474/Backup-LLM.git
cd Backup-LLM

# 2. Lancer l'installation
sudo ./setup.sh install
```

Le script va vous demander :
-  Clés API (Deepgram, Groq, ElevenLabs)
-  Mots de passe PostgreSQL
-  IP du serveur IA
-  IP(s) des serveurs Asterisk
-  Identifiants AMI Asterisk
-  Votre IP personnelle (pour accès admin)

---

## Mise à Jour du Serveur

### Méthode Recommandée : Reset avec Conservation du .env

Cette méthode est **PARFAITE** pour les mises à jour car elle :
-  Garde toutes vos clés API et mots de passe
-  Nettoie Docker complètement
-  Réinstalle une version propre
-  Évite les conflits de configuration

### Procédure de Mise à Jour

```bash
# 1. Se connecter au serveur en SSH
ssh root@votre-serveur.com

# 2. Aller dans le répertoire du projet
cd /chemin/vers/Backup-LLM

# 3. Arrêter le serveur si actif (Ctrl+C dans le terminal)

# 4. Récupérer la dernière version depuis GitHub
git fetch origin
git pull origin main

# 5. Lancer le reset avec conservation du .env
sudo ./setup.sh reset
```

Le script va :
1. 🔹 **Sauvegarder** votre .env en mémoire
2. 🔹 **Supprimer** tous les conteneurs Docker
3. 🔹 **Supprimer** tous les volumes ( données DB perdues)
4. 🔹 **Supprimer** l'environnement virtuel Python
5. 🔹 **Supprimer** le cache audio
6. 🔹 **Restaurer** votre .env
7. 🔹 **Proposer** de réinstaller automatiquement

### Vérification après Mise à Jour

```bash
# Vérifier que Docker est actif
docker ps

# Vous devriez voir :
# - postgres-clients
# - postgres-tickets
# - voicebot
# - dashboard
# - prometheus
# - grafana

# Vérifier les logs
docker logs voicebot --tail 50
```

---

## 🛠️ Options de Reset

Le `setup.sh` propose maintenant **3 modes** :

### 1️⃣ Mode Install (Défaut)

```bash
./setup.sh
# ou
./setup.sh install
```

**Usage** : Première installation ou si l'option 1 a été choisie au démarrage

### 2️⃣ Mode Clean (Nettoyage Total)

```bash
./setup.sh clean
```

** ATTENTION** : Supprime **TOUT** y compris le `.env`

**Supprime** :
-  Stack Docker (conteneurs + volumes)
-  Environnement virtuel Python
-  Fichier `.env` (clés API perdues)
-  Fichier `docker-compose.override.yml`
-  Cache audio
-  Logs

**Quand l'utiliser** :
- 🔹 Vous voulez repartir de zéro
- 🔹 Vous avez perdu vos clés API
- 🔹 Désinstallation complète

### 3️⃣ Mode Reset (Nettoyage avec Conservation .env) - **NOUVEAU**

```bash
./setup.sh reset
```

** RECOMMANDÉ** pour les mises à jour

**Supprime** :
-  Stack Docker (conteneurs + volumes)
-  Environnement virtuel Python
-  Fichier `docker-compose.override.yml`
-  Cache audio
-  Logs

**Conserve** :
-  Fichier `.env` (clés API, mots de passe)

**Quand l'utiliser** :
- 🔹 Mise à jour du code depuis GitHub
- 🔹 Réinstallation propre
- 🔹 Résolution de problèmes Docker
- 🔹 Vous voulez repartir sur une base propre sans ressaisir les configs

---

## 🐛 Débogage des Conversations

### Nouveau Système de Logs Amélioré

Les logs montrent maintenant clairement les échanges entre le **CLIENT** et l'**IA** :

```log
[call_abc123]  CLIENT (STT): Bonjour, j'ai un problème avec ma connexion internet
[call_abc123]  CLIENT: Bonjour, j'ai un problème avec ma connexion internet
[call_abc123]  IA: Bonjour ! Je comprends que vous rencontrez un problème avec votre connexion internet. Pourriez-vous me donner votre nom complet s'il vous plaît ?
[call_abc123]  IA PARLE: Bonjour ! Je comprends que vous rencontrez un problème...
[call_abc123]  CLIENT (STT): Je m'appelle Pierre Martin
[call_abc123]  CLIENT: Je m'appelle Pierre Martin
[call_abc123]  IA: Merci Pierre. Et votre adresse email ?
```

### Légende des Emojis

| Emoji | Signification | Description |
|-------|---------------|-------------|
|  **CLIENT (STT)** | Transcription Speech-to-Text | Ce que Deepgram a entendu |
|  **CLIENT** | Message traité | Message envoyé au LLM |
|  **CLIENT (INTERRUPTION)** | Barge-in détecté | Client a interrompu l'IA |
|  **IA** | Réponse générée | Ce que le LLM a répondu |
|  **IA PARLE** | Synthèse vocale | Texte envoyé à ElevenLabs |

### Suivre les Logs en Temps Réel

```bash
# Méthode 1 : Logs Docker (recommandé)
docker logs -f voicebot

# Méthode 2 : Logs du fichier
tail -f logs/voicebot_YYYY-MM-DD.log

# Méthode 3 : Filtrer uniquement les conversations
docker logs -f voicebot | grep -E "||"
```

### Exemples de Patterns à Chercher

```bash
# Voir toutes les transcriptions clients
docker logs voicebot | grep " CLIENT (STT)"

# Voir toutes les réponses IA
docker logs voicebot | grep " IA:"

# Voir les interruptions (barge-in)
docker logs voicebot | grep "INTERRUPTION"

# Voir les erreurs
docker logs voicebot | grep -i error

# Voir les appels d'un numéro spécifique
docker logs voicebot | grep "0612345678"
```

---

## Monitoring en Production

### Dashboard Streamlit

Accès : `http://IP_SERVEUR:8501` (depuis votre IP autorisée)

**Informations disponibles** :
-  Appels en cours
-  Statistiques du jour
- 🎫 Derniers tickets créés
- 😡 Détection de colère
-  Durées moyennes

### Prometheus + Grafana

**Prometheus** : `http://IP_SERVEUR:9092`
**Grafana** : `http://IP_SERVEUR:3000`

**Métriques disponibles** :
- Nombre d'appels actifs
- Latence LLM (Groq)
- Latence STT (Deepgram)
- Latence TTS (ElevenLabs)
- Taux de cache hit TTS
- Durée moyenne des appels

### Alertes à Surveiller

```bash
# Vérifier la santé des conteneurs
docker ps --format "table {{.Names}}\t{{.Status}}"

# Vérifier l'utilisation CPU/RAM
docker stats --no-stream

# Vérifier les connexions PostgreSQL
docker exec postgres-clients psql -U voicebot -d db_clients -c "SELECT COUNT(*) FROM clients;"
docker exec postgres-tickets psql -U voicebot -d db_tickets -c "SELECT COUNT(*) FROM tickets;"
```

---

## Résolution de Problèmes Courants

### Problème : Le serveur ne démarre pas après une mise à jour

```bash
# Solution : Reset complet
sudo ./setup.sh reset
# Répondre 'Y' pour réinstaller
```

### Problème : Erreur de clés API

```bash
# Vérifier le .env
cat .env | grep API_KEY

# Si les clés sont vides, il faut refaire un clean
sudo ./setup.sh clean
```

### Problème : Base de données corrompue

```bash
# Reset (efface les données)
sudo ./setup.sh reset
```

### Problème : Cache audio manquant

```bash
# Régénérer le cache
source venv/bin/activate
python generate_cache.py
```

### Problème : Docker ne répond plus

```bash
# Redémarrer Docker
sudo systemctl restart docker

# Puis relancer l'installation
sudo ./setup.sh reset
```

---

## Checklist de Mise à Jour

- [ ] Se connecter au serveur SSH
- [ ] Arrêter le serveur actuel (Ctrl+C)
- [ ] `git pull origin main`
- [ ] `sudo ./setup.sh reset`
- [ ] Vérifier que tous les conteneurs sont up : `docker ps`
- [ ] Vérifier les logs : `docker logs voicebot --tail 50`
- [ ] Tester un appel de test
- [ ] Vérifier le dashboard Streamlit
- [ ] Vérifier Grafana

---

## 🆘 Support

En cas de problème :

1. Consulter les logs : `docker logs voicebot`
2. Vérifier GitHub Issues : https://github.com/Pierre3474/Backup-LLM/issues
3. Créer une nouvelle issue avec :
   - Les logs d'erreur
   - La commande exécutée
   - La version de Debian
   - La sortie de `docker ps`

---

## Félicitations !

Votre serveur est maintenant à jour et prêt à traiter les appels.

**Prochaines étapes recommandées** :
1. Surveiller les logs pendant les premières heures
2. Vérifier les métriques dans Grafana
3. Effectuer des appels de test
4. Ajuster les prompts LLM si nécessaire (fichier `prompts.yaml`)

#  Configuration du Dashboard Streamlit

## Objectif

Le dashboard permet de superviser en temps réel les appels du voicebot avec :
-  KPIs (appels du jour, durée moyenne, sentiment client)
-  Liste des 50 derniers tickets
- 🎧 Lecture des enregistrements audio

---

## Configuration Requise

### 1. Variables d'Environnement (.env)

Ajoutez ces lignes dans votre fichier `.env` :

```bash
# Base de données tickets (OBLIGATOIRE)
DB_TICKETS_DSN=postgresql://voicebot:votre_mot_de_passe@postgres-tickets:5432/db_tickets

# IP autorisée pour accéder au dashboard (OPTIONNEL)
# Laissez vide ou commentez pour désactiver la validation IP
PERSONAL_IP=votre.ip.publique.ici

# Si vous avez plusieurs IPs autorisées, séparez par des virgules :
# PERSONAL_IP=192.168.1.100,82.64.123.45
```

**Comment trouver votre IP publique ?**

```bash
# Sur le serveur
curl ifconfig.me

# Ou
curl icanhazip.com
```

---

### 2. Vérifier PostgreSQL

Assurez-vous que la base de données tickets est accessible :

```bash
# Vérifier que le conteneur tourne
docker ps | grep postgres-tickets

# Tester la connexion
docker exec -it postgres-tickets psql -U voicebot -d db_tickets -c "SELECT COUNT(*) FROM tickets;"
```

**Résultat attendu** :
```
 count
-------
     5
(1 row)
```

Si vous obtenez une erreur, vérifiez :
- Le conteneur postgres-tickets est bien démarré
- Le mot de passe dans .env correspond au mot de passe PostgreSQL
- Le nom de la base est bien `db_tickets`

---

### 3. Créer le Répertoire des Logs (Optionnel)

Pour que les enregistrements audio soient disponibles :

```bash
mkdir -p logs/calls
chmod 755 logs/calls
```

**Note** : Les enregistrements sont automatiquement sauvegardés par server.py dans ce dossier.

---

## Démarrage du Dashboard

### Option 1 : Avec Docker Compose (Recommandé)

```bash
# Démarrer tous les services y compris le dashboard
docker compose up -d

# Ou uniquement le dashboard si les autres tournent déjà
docker compose up -d dashboard
```

### Option 2 : En Local (Pour Développement)

```bash
# Installer les dépendances
pip install streamlit pandas psycopg2-binary python-dotenv

# Lancer le dashboard
streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0
```

---

## Accès au Dashboard

Une fois démarré, accédez au dashboard via :

```
http://votre-serveur-ip:8501
```

Exemple :
```
http://145.239.223.188:8501
```

---

## Résolution de Problèmes

### Erreur : "DB_TICKETS_DSN non configuré"

**Cause** : La variable `DB_TICKETS_DSN` n'est pas dans le .env

**Solution** :
```bash
# Vérifier que .env contient DB_TICKETS_DSN
grep DB_TICKETS_DSN .env

# Si absent, ajoutez-le :
echo 'DB_TICKETS_DSN=postgresql://voicebot:votre_mot_de_passe@postgres-tickets:5432/db_tickets' >> .env

# Redémarrer le dashboard
docker restart voicebot-dashboard
```

---

### Erreur : "Impossible de se connecter à la base de données"

**Causes possibles** :
1. PostgreSQL n'est pas démarré
2. Mot de passe incorrect dans DB_TICKETS_DSN
3. Nom de la base incorrect

**Solutions** :

```bash
# 1. Vérifier que PostgreSQL tourne
docker ps | grep postgres-tickets

# Si absent, démarrer :
docker compose up -d postgres-tickets

# 2. Vérifier le mot de passe
# Le mot de passe doit correspondre à celui défini dans docker-compose.yml
grep POSTGRES_PASSWORD docker-compose.yml
grep DB_TICKETS_DSN .env

# 3. Tester la connexion manuellement
docker exec -it postgres-tickets psql -U voicebot -d db_tickets

# Si ça fonctionne, tapez \q pour quitter
```

---

### Erreur : "Accès Refusé" (IP bloquée)

**Cause** : Votre IP n'est pas dans `PERSONAL_IP`

**Solutions** :

**Option 1 : Désactiver la validation IP**
```bash
# Dans .env, commentez ou supprimez PERSONAL_IP
# PERSONAL_IP=

# Redémarrer
docker restart voicebot-dashboard
```

**Option 2 : Ajouter votre IP**
```bash
# Trouver votre IP publique
curl ifconfig.me

# Ajouter dans .env
PERSONAL_IP=82.64.123.45

# Redémarrer
docker restart voicebot-dashboard
```

---

### ℹ️ Aucun Ticket Affiché

**Cause** : La base de données est vide (aucun appel n'a encore été enregistré)

**Solution** : Faites un appel test au voicebot pour créer des tickets

---

### Audio Non Trouvé

**Cause** : Les enregistrements audio ne sont pas dans `logs/calls/`

**Vérifications** :

```bash
# Vérifier que le répertoire existe
ls -la logs/calls/

# Vérifier les permissions
chmod 755 logs/calls

# Vérifier que server.py sauvegarde bien les fichiers
# (Chercher "Enregistrement sauvegardé" dans les logs)
docker logs voicebot-app | grep "Enregistrement"
```

**Note** : Les fichiers audio sont au format :
```
call_{uuid}_{timestamp}.raw
```

Exemple :
```
call_abc123-def456-789_1735689012.raw
```

---

## Utilisation du Dashboard

### KPIs Affichés

| Indicateur | Description |
|------------|-------------|
| **Appels du Jour** | Nombre d'appels reçus aujourd'hui |
| **Durée Moyenne** | Durée moyenne de tous les appels (secondes) |
| **Clients Mécontents** | Nombre d'appels avec sentiment négatif |
| **Pannes Internet** | Nombre de problèmes type "internet" |

### Liste des Tickets

Chaque ticket affiche :
- 🕐 Heure de l'appel
-  Numéro de téléphone
- 🏷️ Type de problème (INTERNET, MOBILE, etc.)
- 😐😡🙂 Sentiment client
-  Résumé du problème
- 🎧 Enregistrement audio (si disponible)

---

## Sécurité

### Validation IP

Par défaut, le dashboard est **ouvert** si `PERSONAL_IP` n'est pas configuré.

**Pour le sécuriser** :

```bash
# Dans .env
PERSONAL_IP=votre.ip.publique

# Multiples IPs autorisées :
PERSONAL_IP=82.64.123.45,91.45.78.12,192.168.1.100
```

### Firewall

Assurez-vous que le port 8501 est accessible :

```bash
# Autoriser le port 8501
ufw allow 8501/tcp

# Vérifier
ufw status | grep 8501
```

---

## Commandes Utiles

```bash
# Voir les logs du dashboard
docker logs -f voicebot-dashboard

# Redémarrer le dashboard
docker restart voicebot-dashboard

# Arrêter le dashboard
docker stop voicebot-dashboard

# Démarrer uniquement le dashboard
docker compose up -d dashboard

# Vérifier l'état
docker ps | grep dashboard
```

---

## 🆚 Dashboard vs Grafana

**Dashboard Streamlit (Port 8501)** :
-  Simple et rapide à utiliser
-  Lecture des enregistrements audio
-  Détails des tickets
-  Pas de graphiques avancés

**Grafana (Port 3000)** :
-  Graphiques avancés et alertes
-  Métriques Prometheus en temps réel
-  Dashboards personnalisables
-  Pas de lecture audio

**Recommandation** : Utilisez les deux !
- **Streamlit** pour l'analyse détaillée des appels
- **Grafana** pour le monitoring global

---

## Exemple de Configuration Complète

```bash
# .env (exemple complet)

# === BASE DE DONNÉES ===
DB_CLIENTS_DSN=postgresql://voicebot:SecurePassword123@postgres-clients:5432/db_clients
DB_TICKETS_DSN=postgresql://voicebot:SecurePassword123@postgres-tickets:5432/db_tickets

# === DASHBOARD ===
PERSONAL_IP=82.64.123.45

# === API KEYS ===
ELEVENLABS_API_KEY=sk_abc...
DEEPGRAM_API_KEY=xyz...
GROQ_API_KEY=gsk_...

# === ASTERISK ===
ASTERISK_HOST=145.239.223.188
AMI_USERNAME=admin
AMI_PASSWORD=secret123
```

---

## Checklist de Démarrage

Avant d'utiliser le dashboard, vérifiez :

- [ ] `.env` contient `DB_TICKETS_DSN`
- [ ] PostgreSQL tourne (`docker ps | grep postgres-tickets`)
- [ ] Table `tickets` existe (tester avec psql)
- [ ] Répertoire `logs/calls/` existe
- [ ] Port 8501 ouvert dans le firewall
- [ ] Dashboard démarré (`docker ps | grep dashboard`)
- [ ] Accessible via navigateur (http://ip:8501)

---

## Test de Fonctionnement

Pour tester que tout fonctionne :

1. **Démarrer le dashboard**
   ```bash
   docker compose up -d dashboard
   ```

2. **Ouvrir dans le navigateur**
   ```
   http://votre-ip:8501
   ```

3. **Vérifier l'affichage** :
   -  Titre "Supervision SAV Wipple"
   -  Message "Connecté à la base de données (X tickets)"
   -  4 KPIs affichés
   -  Liste des tickets (ou message "Aucun ticket trouvé")

4. **Faire un appel test** pour vérifier qu'un nouveau ticket apparaît

---

**Status** :  Dashboard corrigé et documenté
**Date** : 2025-12-31
**Version** : 2.1

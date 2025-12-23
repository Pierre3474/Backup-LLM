# Sécurisation Dashboard Streamlit - Multi-IP

## 📋 Vue d'ensemble

Le Dashboard Streamlit (port 8501) est désormais **sécurisé à trois niveaux** avec support de **plusieurs IPs autorisées** définies dans `.env`.

### Format de configuration

```bash
# .env
PERSONAL_IP=10.0.0.1,192.168.1.50,88.12.34.56
```

**Important :** Les IPs sont séparées par des **virgules sans espaces**.

---

## 🔒 Trois couches de sécurité

### 1. **UFW (Firewall système)** - `setup.sh:configure_firewall()`

Le script `setup.sh` configure automatiquement UFW pour autoriser le port 8501 uniquement depuis les IPs définies dans `PERSONAL_IP`.

**Modifications apportées :**
- Parsing de `PERSONAL_IP` en tableau : `IFS=',' read -ra PERSONAL_IPS`
- Boucle sur chaque IP pour créer les règles UFW :
  ```bash
  ufw allow from "$personal_ip" to any port 8501 proto tcp comment "Dashboard - IP admin #$count"
  ```

**Fichier :** `setup.sh` lignes 550-567

---

### 2. **Iptables DOCKER-USER** - `setup.sh:configure_docker_firewall()`

Docker **contourne UFW** en modifiant directement iptables. Les règles iptables DOCKER-USER sont donc **critiques**.

**Modifications apportées :**
- Parsing de `PERSONAL_IP` en tableau
- Règles **ACCEPT** pour chaque IP (port 8501) avec `-I` (INSERT au début)
- Règle **DROP** globale avec `-A` (APPEND à la fin)

**Ordre critique :**
```bash
# ACCEPT rules first (inserted)
iptables -I DOCKER-USER -p tcp --dport 8501 -s "$personal_ip" -j ACCEPT

# DROP rule last (appended)
iptables -A DOCKER-USER -p tcp --dport 8501 -j DROP
```

**Fichier :** `setup.sh` lignes 596-640

---

### 3. **Validation applicative** - `dashboard.py`

Le dashboard vérifie lui-même l'IP du visiteur **avant toute opération**.

**Fonctionnement :**

1. **Récupération de l'IP réelle du client** (`get_client_ip()`) :
   - Vérifie `X-Forwarded-For` (proxy/reverse proxy)
   - Vérifie `X-Real-IP` (nginx)
   - Fallback sur `Remote-Addr`

2. **Validation contre la whitelist** (`validate_ip_access()`) :
   - Parse `PERSONAL_IP` depuis `.env`
   - Compare l'IP du visiteur avec la liste autorisée
   - Bloque l'accès avec `st.stop()` si non autorisé

**Code ajouté :** `dashboard.py` lignes 11-89

**Exemple de blocage :**
```
🚫 ACCÈS REFUSÉ
⚠️ Votre IP (12.34.56.78) n'est pas autorisée à accéder à ce dashboard.
ℹ️ IPs autorisées: 10.0.0.1, 192.168.1.50, 88.12.34.56
```

---

## 📊 Affichage de la sécurité - `setup.sh:display_summary()`

Le résumé d'installation affiche désormais la **liste complète des IPs autorisées** :

**Avant :**
```
🔒 Sécurité:
  ✓ Services d'administration accessibles uniquement depuis: 10.0.0.1
```

**Après :**
```
🔒 Sécurité:
  ✓ Services d'administration accessibles depuis 3 IP(s) autorisée(s):
      → 10.0.0.1
      → 192.168.1.50
      → 88.12.34.56
  ✓ AudioSocket (9090) accessible depuis 2 serveur(s) Asterisk:
      → 192.168.1.100
      → 192.168.2.200
```

**Fichier :** `setup.sh` lignes 675-705

---

## ✅ Vérification Docker Compose

Le fichier `docker-compose.yml` passe correctement la variable `PERSONAL_IP` au conteneur dashboard via :

```yaml
dashboard:
  env_file: .env  # ✓ Toutes les variables .env sont injectées
```

**Fichier :** `docker-compose.yml` ligne 68

---

## 🚀 Utilisation

### Configuration initiale

1. **Définir les IPs autorisées dans `.env` :**
   ```bash
   PERSONAL_IP=10.0.0.1,192.168.1.50,88.12.34.56
   ```

2. **Lancer l'installation (si première fois) :**
   ```bash
   sudo ./setup.sh
   ```

3. **Ou mettre à jour les règles firewall uniquement :**
   ```bash
   # Relancer configure_firewall et configure_docker_firewall manuellement
   source .env
   IFS=',' read -ra PERSONAL_IPS <<< "$PERSONAL_IP"

   # UFW
   for ip in "${PERSONAL_IPS[@]}"; do
     sudo ufw allow from "$ip" to any port 8501 proto tcp
   done

   # Iptables
   sudo iptables -F DOCKER-USER
   for ip in "${PERSONAL_IPS[@]}"; do
     sudo iptables -I DOCKER-USER -p tcp --dport 8501 -s "$ip" -j ACCEPT
   done
   sudo iptables -A DOCKER-USER -p tcp --dport 8501 -j DROP
   ```

### Ajouter une nouvelle IP

1. **Modifier `.env` :**
   ```bash
   # Avant
   PERSONAL_IP=10.0.0.1,192.168.1.50

   # Après
   PERSONAL_IP=10.0.0.1,192.168.1.50,203.0.113.42
   ```

2. **Redémarrer le conteneur dashboard :**
   ```bash
   docker compose restart dashboard
   ```

3. **Mettre à jour les règles firewall :**
   ```bash
   # UFW
   sudo ufw allow from 203.0.113.42 to any port 8501 proto tcp

   # Iptables
   sudo iptables -I DOCKER-USER -p tcp --dport 8501 -s 203.0.113.42 -j ACCEPT
   ```

---

## 🔍 Debugging

### Tester l'accès

1. **Depuis une IP autorisée :**
   ```bash
   curl -I http://<SERVER_IP>:8501
   # HTTP/1.1 200 OK (accès autorisé)
   ```

2. **Depuis une IP non autorisée :**
   ```bash
   curl -I http://<SERVER_IP>:8501
   # Connection refused ou timeout (bloqué par iptables)
   ```

### Vérifier les règles UFW

```bash
sudo ufw status numbered | grep 8501
```

**Sortie attendue :**
```
[10] 8501/tcp    ALLOW IN    10.0.0.1    # Dashboard - IP admin #1
[11] 8501/tcp    ALLOW IN    192.168.1.50 # Dashboard - IP admin #2
[12] 8501/tcp    ALLOW IN    88.12.34.56  # Dashboard - IP admin #3
```

### Vérifier les règles iptables

```bash
sudo iptables -L DOCKER-USER -n -v
```

**Sortie attendue :**
```
Chain DOCKER-USER (1 references)
 pkts bytes target     prot opt in     out     source               destination
    0     0 ACCEPT     tcp  --  *      *       10.0.0.1             0.0.0.0/0            tcp dpt:8501
    0     0 ACCEPT     tcp  --  *      *       192.168.1.50         0.0.0.0/0            tcp dpt:8501
    0     0 ACCEPT     tcp  --  *      *       88.12.34.56          0.0.0.0/0            tcp dpt:8501
    0     0 DROP       tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:8501
```

### Logs du dashboard

```bash
docker compose logs dashboard -f
```

Rechercher les messages :
- `✅ Accès autorisé depuis <IP>` : accès valide
- `🚫 ACCÈS REFUSÉ` : IP bloquée au niveau applicatif

---

## 📝 Résumé des fichiers modifiés

| Fichier | Modifications |
|---------|---------------|
| `setup.sh` | - `configure_firewall()` : parsing multi-IP, règles UFW port 8501<br>- `configure_docker_firewall()` : parsing multi-IP, règles iptables port 8501<br>- `display_summary()` : affichage liste IPs autorisées |
| `dashboard.py` | - `get_client_ip()` : récupération IP réelle (X-Forwarded-For, X-Real-IP)<br>- `validate_ip_access()` : validation whitelist + blocage si non autorisé<br>- Appel `validate_ip_access()` au démarrage |
| `docker-compose.yml` | ✅ Déjà configuré avec `env_file: .env` (aucune modification nécessaire) |

---

## 🛡️ Avantages de cette architecture

### Sécurité en profondeur (Defense in Depth)

1. **Couche réseau (UFW)** : bloque au niveau système
2. **Couche Docker (iptables)** : empêche le contournement UFW
3. **Couche applicative (Streamlit)** : vérification explicite dans le code

### Flexibilité

- **Multi-IP** : support natif de plusieurs administrateurs
- **Sans redéploiement** : modification `.env` + restart container
- **Logs clairs** : messages d'erreur explicites pour débugger

### Production-ready

- **Règles persistantes** : sauvegarde iptables après reboot
- **Validation robuste** : gestion des proxies (X-Forwarded-For)
- **Feedback utilisateur** : messages d'erreur clairs et professionnels

---

## 🔐 Sécurité supplémentaire recommandée

Pour renforcer davantage la sécurité :

1. **HTTPS avec certificat SSL** :
   ```bash
   # Installer nginx/traefik comme reverse proxy
   # Activer SSL/TLS pour le dashboard
   ```

2. **Authentification utilisateur** :
   - Ajouter login/password avec `streamlit-authenticator`
   - Stocker les credentials hashés dans PostgreSQL

3. **Rate limiting** :
   - Limiter le nombre de tentatives de connexion par IP
   - Bannissement temporaire après X échecs

4. **Audit logs** :
   - Logger tous les accès (autorisés et refusés)
   - Envoyer les alertes de tentatives suspectes

---

**Auteur :** Expert DevOps et Sécurité
**Date :** 2025-12-23
**Version :** 1.0.0

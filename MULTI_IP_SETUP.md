# Gestion Multi-IP pour Serveurs Asterisk

Ce guide explique comment gérer plusieurs serveurs Asterisk autorisés à se connecter au voicebot (cas multi-clients).

## 📋 Vue d'ensemble

Le voicebot peut autoriser **plusieurs serveurs Asterisk** (plusieurs clients) à se connecter simultanément au port 9090 (AudioSocket). Chaque serveur client a sa propre IP qui doit être autorisée par le firewall UFW.

## 🚀 Configuration initiale (Setup)

Lors de l'installation avec `setup.sh`, vous pouvez configurer plusieurs IPs :

```bash
sudo ./setup.sh
```

Le script vous demandera :

```
Configuration des serveurs Asterisk autorisés
Vous pouvez autoriser plusieurs serveurs Asterisk (plusieurs clients)

Entrez l'adresse IP du 1er serveur Asterisk: 192.168.1.10
✓ IP 192.168.1.10 ajoutée (1 serveur(s) configuré(s))

Entrez l'IP du serveur Asterisk 2 (ou laissez vide pour terminer): 192.168.1.20
✓ IP 192.168.1.20 ajoutée (2 serveur(s) configuré(s))

Entrez l'IP du serveur Asterisk 3 (ou laissez vide pour terminer): [ENTER]

✓ 2 serveur(s) Asterisk configuré(s)
```

## 🔧 Gestion après installation

### Script de gestion des IPs

Un script dédié permet de gérer les IPs autorisées après l'installation :

```bash
sudo ./manage_allowed_ips.sh
```

### Mode interactif (menu)

Sans argument, le script lance un menu interactif :

```
==================================================================
     Gestion des IPs Asterisk autorisées - Voicebot SAV
==================================================================

  1) Lister les IPs autorisées
  2) Ajouter une nouvelle IP
  3) Supprimer une IP
  4) Afficher l'état du firewall UFW
  5) Quitter

Choisissez une option (1-5):
```

### Mode ligne de commande

#### Lister les IPs autorisées

```bash
sudo ./manage_allowed_ips.sh list
```

Affiche :
```
==================================================================
  IPs Asterisk autorisées pour le port 9090 (AudioSocket)
==================================================================

  1. 192.168.1.10 - Serveur Asterisk #1
  2. 192.168.1.20 - Client ABC
  3. 192.168.1.30 - Client XYZ

Total: 3 IP(s) autorisée(s)
```

#### Ajouter une nouvelle IP

```bash
sudo ./manage_allowed_ips.sh add 192.168.1.40 "Client DEF"
```

Ou sans commentaire :
```bash
sudo ./manage_allowed_ips.sh add 192.168.1.40
```

**Effet :**
- Ajoute l'IP au fichier `/opt/PY_SAV/.allowed_asterisk_ips`
- Crée automatiquement la règle UFW : `ufw allow from 192.168.1.40 to any port 9090`

#### Supprimer une IP

```bash
sudo ./manage_allowed_ips.sh remove 192.168.1.40
```

**Effet :**
- Retire l'IP du fichier de configuration
- Supprime la règle UFW correspondante

#### Voir l'état du firewall

```bash
sudo ./manage_allowed_ips.sh status
```

Affiche toutes les règles UFW pour le port 9090.

## 📂 Fichiers de configuration

### `/opt/PY_SAV/.allowed_asterisk_ips`

Fichier texte contenant la liste des IPs autorisées au format :

```
192.168.1.10|Serveur Asterisk #1
192.168.1.20|Client ABC
192.168.1.30|Client XYZ
```

Format : `IP|Commentaire`

**Permissions :** `600` (lecture/écriture propriétaire uniquement)

## 🔒 Sécurité

### Règles firewall UFW

Chaque IP autorisée crée une règle UFW :

```bash
# Vérifier les règles actives
sudo ufw status numbered

# Exemple de sortie
[1] 9090/tcp     ALLOW IN    192.168.1.10    # AudioSocket Asterisk #1
[2] 9090/tcp     ALLOW IN    192.168.1.20    # AudioSocket Asterisk #2
```

### Bonnes pratiques

1. **IP fixes uniquement** : Utilisez des IPs statiques pour les serveurs Asterisk
2. **Documentation** : Utilisez des commentaires descriptifs lors de l'ajout d'IPs
3. **Audit régulier** : Vérifiez périodiquement les IPs autorisées
4. **Suppression** : Retirez les IPs des clients qui ne sont plus actifs

## 🧪 Test de connectivité

### Depuis un serveur Asterisk autorisé

```bash
# Test de connexion TCP au port 9090
telnet <IP_VOICEBOT> 9090
```

**Résultat attendu :**
```
Trying <IP_VOICEBOT>...
Connected to <IP_VOICEBOT>.
Escape character is '^]'.
```

Si la connexion échoue, vérifiez :
1. L'IP est bien dans la liste autorisée : `sudo ./manage_allowed_ips.sh list`
2. Le firewall UFW est actif : `sudo ufw status`
3. Le serveur voicebot est démarré : `systemctl status voicebot`

### Depuis une IP NON autorisée

```bash
telnet <IP_VOICEBOT> 9090
```

**Résultat attendu :**
```
Trying <IP_VOICEBOT>...
telnet: connect to address <IP_VOICEBOT>: Connection refused
```

C'est **normal** et **souhaitable** pour la sécurité.

## 📊 Cas d'usage multi-clients

### Scénario : Hébergeur de voicebot pour 5 clients

```bash
# Installation initiale avec le premier client
sudo ./setup.sh
# Entrer IP du client 1

# Après installation, ajouter les autres clients
sudo ./manage_allowed_ips.sh add 192.168.1.101 "Client A - Société ABC"
sudo ./manage_allowed_ips.sh add 192.168.1.102 "Client B - Société DEF"
sudo ./manage_allowed_ips.sh add 192.168.1.103 "Client C - Société GHI"
sudo ./manage_allowed_ips.sh add 192.168.1.104 "Client D - Société JKL"

# Vérifier la configuration
sudo ./manage_allowed_ips.sh list
```

### Scénario : Retrait d'un client

```bash
# Lister pour voir l'IP exacte
sudo ./manage_allowed_ips.sh list

# Supprimer l'IP du client
sudo ./manage_allowed_ips.sh remove 192.168.1.102

# Vérifier que la règle UFW a bien été supprimée
sudo ufw status | grep 9090
```

## 🛠️ Dépannage

### Problème : IP ajoutée mais connexion refusée

**Diagnostic :**
```bash
# 1. Vérifier que l'IP est dans le fichier
cat /opt/PY_SAV/.allowed_asterisk_ips | grep <IP>

# 2. Vérifier la règle UFW
sudo ufw status | grep <IP>

# 3. Vérifier que UFW est actif
sudo ufw status
```

**Solution :**
```bash
# Si UFW n'est pas actif
sudo ufw enable

# Si la règle manque, la recréer
sudo ./manage_allowed_ips.sh add <IP> "Description"
```

### Problème : Trop d'IPs autorisées (liste encombrée)

```bash
# Lister toutes les IPs
sudo ./manage_allowed_ips.sh list

# Supprimer les IPs obsolètes une par une
sudo ./manage_allowed_ips.sh remove <IP>
```

### Problème : Script refuse de s'exécuter

**Erreur :** `Ce script doit être exécuté avec sudo`

**Solution :**
```bash
# Toujours utiliser sudo
sudo ./manage_allowed_ips.sh
```

## 📚 Références

- [Documentation UFW](https://help.ubuntu.com/community/UFW)
- [Asterisk AudioSocket](https://wiki.asterisk.org/wiki/display/AST/AudioSocket)
- Script principal : `manage_allowed_ips.sh`
- Configuration setup : `setup.sh`

## ✅ Checklist de déploiement multi-clients

- [ ] Installation initiale effectuée (`setup.sh`)
- [ ] Première IP client configurée
- [ ] Script `manage_allowed_ips.sh` testé
- [ ] IPs additionnelles ajoutées pour chaque client
- [ ] Tests de connectivité effectués depuis chaque serveur Asterisk
- [ ] Documentation des IPs (commentaires descriptifs)
- [ ] Procédure de retrait client documentée
- [ ] Audit de sécurité périodique planifié

---

**Version :** 1.0
**Dernière mise à jour :** 2025-12-23

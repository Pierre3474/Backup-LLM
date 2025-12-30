# 🔄 Guide d'Utilisation du Reset

## 📋 Le script `./setup.sh reset` fonctionne correctement !

Il demande simplement votre **confirmation** avant d'agir.

---

## 🎯 Méthode 1 : Mode Interactif (Recommandé)

### Étapes

```bash
# 1. Lancer la commande
./setup.sh reset

# 2. Lire l'avertissement qui s'affiche
# 3. Taper 'y' puis ENTRÉE pour confirmer
# 4. Taper 'Y' (ou juste ENTRÉE) pour réinstaller après le reset
```

### Exemple Complet

```bash
root@serveur:/chemin/vers/Backup-LLM# ./setup.sh reset

=======================================================================
Reset Propre avec Conservation du .env
=======================================================================

[INFO] Cette opération va:
  ✓ Arrêter et supprimer TOUS les conteneurs Docker
  ✓ Supprimer TOUS les volumes Docker (données DB effacées)
  ✓ Supprimer les réseaux Docker
  ✓ Supprimer l'environnement virtuel Python
  ✓ Supprimer le cache audio
  ✓ Supprimer les logs

  ✓ CONSERVER le fichier .env (clés API, mots de passe)

[WARNING] Les données des bases PostgreSQL seront PERDUES

Voulez-vous continuer? [y/N]: y  ← VOUS TAPEZ 'y' ICI

[INFO] Sauvegarde du fichier .env...
[SUCCESS] .env sauvegardé en mémoire
[INFO] Arrêt et suppression de la stack Docker...
[INFO] Suppression de l'environnement virtuel Python...
[INFO] Suppression de docker-compose.override.yml...
[INFO] Suppression du cache audio...
[INFO] Suppression des logs...
[INFO] Restauration du fichier .env...
[SUCCESS] .env restauré avec succès
[SUCCESS] Reset terminé - .env conservé

[INFO] Le reset est terminé. Vous pouvez maintenant réinstaller proprement.

Souhaitez-vous lancer l'installation maintenant? [Y/n]: Y  ← VOUS APPUYEZ SUR ENTRÉE

[INFO] Installation des prérequis système...
...
```

---

## 🚀 Méthode 2 : Mode Automatique (Script Prêt à l'Emploi)

J'ai créé un script qui fait tout automatiquement :

```bash
# Utiliser le script automatique
./quick_reset.sh
```

Ce script :
- ✅ Répond automatiquement 'y' pour confirmer le reset
- ✅ Répond automatiquement 'Y' pour lancer l'installation
- ✅ Pas besoin d'interaction manuelle

**Parfait pour** :
- Mises à jour rapides
- Scripts automatisés
- CI/CD pipelines

---

## ⚙️ Méthode 3 : Commandes Séparées (Contrôle Total)

Si vous voulez plus de contrôle :

```bash
# 1. Reset seulement (sans réinstaller)
echo "y" | ./setup.sh reset
# Puis répondre 'n' quand on demande de réinstaller

# 2. Ensuite, quand vous êtes prêt, réinstaller
./setup.sh install
```

---

## 🐛 Dépannage

### Problème : "Rien ne se passe après avoir lancé ./setup.sh reset"

**Cause** : Le script attend votre réponse

**Solution** : Tapez 'y' puis appuyez sur ENTRÉE

---

### Problème : "Ce script doit être exécuté en tant que root"

**Cause** : Vous n'êtes pas root

**Solution** :
```bash
# Option 1 : Utiliser sudo
sudo ./setup.sh reset

# Option 2 : Devenir root
su -
cd /chemin/vers/Backup-LLM
./setup.sh reset
```

---

### Problème : "Le script s'arrête après le reset"

**Cause** : Vous avez répondu 'n' quand on a demandé de réinstaller

**Solution** : Relancer l'installation manuellement
```bash
./setup.sh install
```

---

## ✅ Vérification Post-Reset

Après le reset et la réinstallation, vérifiez que tout fonctionne :

```bash
# 1. Vérifier que tous les conteneurs sont UP
docker ps

# Vous devriez voir :
# - postgres-clients
# - postgres-tickets
# - voicebot
# - dashboard
# - prometheus
# - grafana

# 2. Vérifier les logs
docker logs voicebot --tail 50

# 3. Vérifier que le .env est bien présent
cat .env | grep API_KEY

# 4. Tester le dashboard
# http://IP_SERVEUR:8501
```

---

## 📊 Comparaison des Modes

| Méthode | Commande | Interaction | Usage |
|---------|----------|-------------|-------|
| Interactif | `./setup.sh reset` | Manuelle | Première fois, contrôle total |
| Automatique | `./quick_reset.sh` | Aucune | Mises à jour rapides |
| Séparé | `echo "y" \| ./setup.sh reset` | Partielle | Scripts personnalisés |

---

## 🎯 Exemples d'Utilisation Réelle

### Scénario 1 : Mise à Jour Hebdomadaire

```bash
cd /opt/Backup-LLM
git pull origin main
./quick_reset.sh  # Automatique, aucune question
```

### Scénario 2 : Problème Docker à Résoudre

```bash
# Arrêter le serveur si actif (Ctrl+C)
./setup.sh reset
# Taper 'y' pour confirmer
# Taper 'Y' pour réinstaller
```

### Scénario 3 : Reset Sans Réinstaller (pour debug)

```bash
echo -e "y\nn" | ./setup.sh reset
# Le 'y' confirme le reset
# Le 'n' refuse la réinstallation

# Puis plus tard, quand vous êtes prêt
./setup.sh install
```

---

## 🎉 Résumé

Le script `./setup.sh reset` **fonctionne parfaitement** !

Il demande juste votre confirmation pour éviter les suppressions accidentelles.

**Pour une utilisation simple et rapide** :
```bash
./quick_reset.sh
```

**Pour plus de contrôle** :
```bash
./setup.sh reset
# Puis répondre aux questions
```

---

## 📞 Besoin d'Aide ?

Si le problème persiste :

1. Vérifier que vous êtes root : `id`
2. Vérifier les permissions : `ls -la setup.sh`
3. Vérifier la syntaxe : `bash -n setup.sh`
4. Consulter les logs d'erreur complets

**Le script fonctionne** - il attend juste votre input ! 😊

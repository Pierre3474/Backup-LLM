#!/bin/bash
# Script de déploiement de la migration ElevenLabs sur le serveur
# Usage: ./deploy_elevenlabs.sh

set -e  # Arrêter en cas d'erreur

echo "=========================================="
echo "🚀 Déploiement migration ElevenLabs"
echo "=========================================="
echo ""

# Couleurs pour l'affichage
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Variables
PROJECT_DIR="/root/PY_SAV"
VENV_DIR="$PROJECT_DIR/venv"
CACHE_DIR="$PROJECT_DIR/assets/cache"

echo "📂 Répertoire du projet: $PROJECT_DIR"
echo ""

# Étape 1: Vérifier que nous sommes dans le bon répertoire
if [ ! -f "server.py" ]; then
    echo -e "${RED}❌ Erreur: server.py non trouvé. Êtes-vous dans le bon répertoire ?${NC}"
    exit 1
fi

# Étape 2: Activer l'environnement virtuel
echo "🔧 Activation de l'environnement virtuel..."
source "$VENV_DIR/bin/activate"
echo -e "${GREEN}✓ Environnement virtuel activé${NC}"
echo ""

# Étape 3: Installer ElevenLabs
echo "📦 Installation de la bibliothèque ElevenLabs..."
pip install elevenlabs==1.13.1 --quiet
echo -e "${GREEN}✓ ElevenLabs installé${NC}"
echo ""

# Étape 4: Vérifier les clés API dans .env
echo "🔑 Vérification du fichier .env..."
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Fichier .env non trouvé !${NC}"
    echo "Créez un fichier .env avec votre clé API ElevenLabs"
    exit 1
fi

if ! grep -q "ELEVENLABS_API_KEY=sk_" .env; then
    echo -e "${YELLOW}⚠️  ATTENTION: ELEVENLABS_API_KEY semble ne pas être configurée dans .env${NC}"
    echo "Assurez-vous d'ajouter votre clé API ElevenLabs dans le fichier .env"
    echo ""
    read -p "Voulez-vous continuer quand même ? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓ ELEVENLABS_API_KEY trouvée dans .env${NC}"
fi
echo ""

# Étape 5: Sauvegarder l'ancien cache (optionnel)
echo "💾 Sauvegarde de l'ancien cache..."
if [ -d "$CACHE_DIR" ]; then
    BACKUP_DIR="${CACHE_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
    cp -r "$CACHE_DIR" "$BACKUP_DIR"
    echo -e "${GREEN}✓ Cache sauvegardé dans: $BACKUP_DIR${NC}"
else
    echo -e "${YELLOW}⚠️  Répertoire cache non trouvé, création...${NC}"
    mkdir -p "$CACHE_DIR"
fi
echo ""

# Étape 6: Regénérer le cache avec ElevenLabs
echo "🎵 Génération du cache audio avec ElevenLabs..."
echo "   (Cela peut prendre quelques minutes - 27 phrases)"
echo ""

python generate_cache.py

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Cache audio généré avec succès${NC}"
else
    echo ""
    echo -e "${RED}❌ Erreur lors de la génération du cache${NC}"
    exit 1
fi
echo ""

# Étape 7: Vérifier que tous les fichiers sont présents
echo "📋 Vérification du cache généré..."
EXPECTED_COUNT=27
ACTUAL_COUNT=$(ls -1 "$CACHE_DIR"/*.raw 2>/dev/null | wc -l)

if [ "$ACTUAL_COUNT" -eq "$EXPECTED_COUNT" ]; then
    echo -e "${GREEN}✓ Tous les fichiers sont présents ($ACTUAL_COUNT/$EXPECTED_COUNT)${NC}"
else
    echo -e "${YELLOW}⚠️  Nombre de fichiers: $ACTUAL_COUNT/$EXPECTED_COUNT${NC}"
fi
echo ""

# Étape 8: Tester le serveur (optionnel)
echo "🧪 Voulez-vous tester le serveur maintenant ?"
read -p "Lancer le serveur en mode test ? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 Démarrage du serveur..."
    echo "   Appuyez sur Ctrl+C pour arrêter"
    echo ""
    sleep 2
    python server.py
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✅ Migration ElevenLabs terminée !${NC}"
echo "=========================================="
echo ""
echo "📝 Prochaines étapes:"
echo "   1. Testez un appel via Asterisk"
echo "   2. Vérifiez les logs du serveur"
echo "   3. Consultez les métriques Prometheus sur :9091/metrics"
echo ""
echo "📚 Documentation complète: MIGRATION_ELEVENLABS.md"
echo ""

#!/bin/bash
# Script de démarrage PRODUCTION pour Voicebot SAV Wipple
# Vérifie la configuration avant de lancer Docker Compose

set -e  # Arrêter en cas d'erreur

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================================================="
echo " DEMARRAGE PRODUCTION - Voicebot SAV Wipple"
echo "======================================================================="
echo ""

# Fonction pour afficher les erreurs
error() {
    echo -e "${RED}ERREUR:${NC} $1"
    exit 1
}

# Fonction pour afficher les avertissements
warn() {
    echo -e "${YELLOW}ATTENTION:${NC} $1"
}

# Fonction pour afficher les succès
success() {
    echo -e "${GREEN}✓${NC} $1"
}

# 1. Vérifier que .env existe
echo "[1/6] Vérification du fichier .env..."
if [ ! -f .env ]; then
    error "Le fichier .env n'existe pas !

Actions requises:
  1. Copiez le template: cp .env.example .env
  2. Éditez .env et configurez TOUTES les valeurs
  3. Relancez ce script

Documentation: voir docs/guides/SECURITY_ENV.md"
fi
success "Fichier .env trouvé"

# 2. Vérifier que les variables critiques sont définies dans .env
echo "[2/6] Vérification des variables critiques..."
MISSING_VARS=()
INVALID_VARS=()

# Charger le .env
set -a
source .env
set +a

# Variables obligatoires
[ -z "$DEEPGRAM_API_KEY" ] && MISSING_VARS+=("DEEPGRAM_API_KEY")
[ -z "$GROQ_API_KEY" ] && MISSING_VARS+=("GROQ_API_KEY")
[ -z "$ELEVENLABS_API_KEY" ] && MISSING_VARS+=("ELEVENLABS_API_KEY")
[ -z "$ELEVENLABS_VOICE_ID" ] && MISSING_VARS+=("ELEVENLABS_VOICE_ID")
[ -z "$AMI_SECRET" ] && MISSING_VARS+=("AMI_SECRET")
[ -z "$DB_PASSWORD" ] && MISSING_VARS+=("DB_PASSWORD")
[ -z "$GRAFANA_ADMIN_PASSWORD" ] && MISSING_VARS+=("GRAFANA_ADMIN_PASSWORD")

# Vérifier les placeholders non remplacés
[[ "$DB_PASSWORD" == *"CHANGEZ"* ]] && INVALID_VARS+=("DB_PASSWORD")
[[ "$GRAFANA_ADMIN_PASSWORD" == *"CHANGEZ"* ]] && INVALID_VARS+=("GRAFANA_ADMIN_PASSWORD")
[[ "$AMI_SECRET" == *"VOTRE_MOT_DE_PASSE"* ]] && INVALID_VARS+=("AMI_SECRET")
[[ "$DB_CLIENTS_DSN" == *"user:pass"* ]] && INVALID_VARS+=("DB_CLIENTS_DSN")
[[ "$DB_CLIENTS_DSN" == *"CHANGEZ"* ]] && INVALID_VARS+=("DB_CLIENTS_DSN")
[[ "$ELEVENLABS_API_KEY" == *"votre_cle"* ]] && INVALID_VARS+=("ELEVENLABS_API_KEY")
[[ "$ELEVENLABS_VOICE_ID" == *"VOTRE_VOICE_ID"* ]] && INVALID_VARS+=("ELEVENLABS_VOICE_ID")

# Afficher les erreurs si nécessaire
if [ ${#MISSING_VARS[@]} -gt 0 ] || [ ${#INVALID_VARS[@]} -gt 0 ]; then
    echo ""
    echo "======================================================================="
    error "Configuration .env incomplète ou invalide

Variables manquantes:
$(printf '  - %s\n' "${MISSING_VARS[@]}")

Variables avec placeholders non remplacés:
$(printf '  - %s\n' "${INVALID_VARS[@]}")

Actions requises:
  1. Éditez .env: nano .env
  2. Remplacez TOUTES les valeurs placeholders
  3. Relancez ce script

Documentation: voir docs/guides/SECURITY_ENV.md
======================================================================="
fi
success "Toutes les variables critiques sont configurées"

# 3. Vérifier que Docker est installé
echo "[3/6] Vérification de Docker..."
if ! command -v docker &> /dev/null; then
    error "Docker n'est pas installé. Installez Docker: https://docs.docker.com/engine/install/"
fi
success "Docker est installé ($(docker --version))"

# 4. Vérifier que Docker Compose est installé
echo "[4/6] Vérification de Docker Compose..."
if ! command -v docker compose &> /dev/null; then
    error "Docker Compose n'est pas installé. Installez Docker Compose: https://docs.docker.com/compose/install/"
fi
success "Docker Compose est installé"

# 5. Vérifier que les ports ne sont pas déjà utilisés
echo "[5/6] Vérification des ports..."
PORTS=(5432 5433 9090 9091 9092 3000 8501)
PORTS_IN_USE=()

for PORT in "${PORTS[@]}"; do
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        PORTS_IN_USE+=("$PORT")
    fi
done

if [ ${#PORTS_IN_USE[@]} -gt 0 ]; then
    warn "Les ports suivants sont déjà utilisés: ${PORTS_IN_USE[*]}

Si des services sont en cours d'exécution, arrêtez-les d'abord:
  docker compose down

Puis relancez ce script."

    read -p "Voulez-vous continuer quand même ? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    success "Tous les ports requis sont disponibles"
fi

# 6. Construire et démarrer les services
echo "[6/6] Démarrage des services Docker..."
echo ""

# Rebuild si nécessaire
read -p "Voulez-vous rebuild les images Docker ? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Construction des images..."
    docker compose build --no-cache
fi

# Démarrer les services
echo "Démarrage des conteneurs..."
docker compose up -d

echo ""
echo "======================================================================="
success "Voicebot SAV Wipple démarré en mode PRODUCTION"
echo "======================================================================="
echo ""
echo "Services disponibles:"
echo "  - AudioSocket (Asterisk):  http://localhost:9090"
echo "  - Prometheus Metrics:      http://localhost:9091/metrics"
echo "  - Prometheus UI:           http://localhost:9092"
echo "  - Grafana Dashboard:       http://localhost:3000 (admin / voir .env)"
echo "  - Streamlit Dashboard:     http://localhost:8501"
echo ""
echo "Commandes utiles:"
echo "  - Voir les logs:           docker compose logs -f voicebot"
echo "  - Arrêter les services:    docker compose down"
echo "  - Redémarrer:              docker compose restart voicebot"
echo ""
echo "Documentation complète: README.md"
echo "======================================================================="

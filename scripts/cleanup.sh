#!/bin/bash

#######################################################################
# Script de nettoyage complet du voicebot
# Supprime proprement : conteneurs, volumes, caches Docker
#######################################################################

set -e

COLOR_RED='\033[0;31m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_BLUE='\033[0;34m'
COLOR_RESET='\033[0m'

log_info() {
    echo -e "${COLOR_BLUE}[INFO]${COLOR_RESET} $1"
}

log_success() {
    echo -e "${COLOR_GREEN}[SUCCESS]${COLOR_RESET} $1"
}

log_warning() {
    echo -e "${COLOR_YELLOW}[WARNING]${COLOR_RESET} $1"
}

log_error() {
    echo -e "${COLOR_RED}[ERROR]${COLOR_RESET} $1"
}

echo ""
echo "======================================================================="
echo "🧹 Nettoyage Complet du Voicebot"
echo "======================================================================="
echo ""

# 1. Arrêter tous les conteneurs voicebot
log_info "Arrêt de tous les conteneurs du projet..."
docker-compose down 2>/dev/null || true
log_success "Conteneurs arrêtés"

# 2. Supprimer les conteneurs orphelins
log_info "Suppression des conteneurs orphelins..."
docker ps -a --filter "name=voicebot" --format "{{.ID}}" | xargs -r docker rm -f 2>/dev/null || true
log_success "Conteneurs orphelins supprimés"

# 3. Supprimer les volumes (bases de données)
log_warning "⚠️  Suppression des volumes (TOUTES LES DONNÉES SERONT PERDUES)"
docker volume ls --filter "name=backup-llm" --format "{{.Name}}" | xargs -r docker volume rm -f 2>/dev/null || true
log_success "Volumes supprimés"

# 4. Supprimer les réseaux
log_info "Suppression des réseaux Docker..."
docker network ls --filter "name=backup-llm" --format "{{.Name}}" | xargs -r docker network rm 2>/dev/null || true
log_success "Réseaux supprimés"

# 5. Supprimer les images non utilisées
log_info "Suppression des images voicebot..."
docker images --filter "reference=backup-llm*" --format "{{.ID}}" | xargs -r docker rmi -f 2>/dev/null || true
log_success "Images supprimées"

# 6. Nettoyer le cache Docker (buildkit)
log_info "Nettoyage du cache de build Docker..."
docker builder prune -f 2>/dev/null || true
log_success "Cache de build nettoyé"

# 7. Tuer les processus Python qui pourraient bloquer les ports
log_info "Vérification des processus Python sur les ports 9090-9091..."
PYTHON_PIDS=$(lsof -ti:9090,9091 2>/dev/null || true)
if [ -n "$PYTHON_PIDS" ]; then
    log_warning "Processus trouvés sur les ports, arrêt forcé..."
    echo "$PYTHON_PIDS" | xargs -r kill -9 2>/dev/null || true
    log_success "Processus arrêtés"
else
    log_info "Aucun processus à arrêter"
fi

# 8. Vérifier les ports
log_info "Vérification des ports libres..."
if lsof -i:9090 >/dev/null 2>&1; then
    log_error "Le port 9090 est encore utilisé !"
    lsof -i:9090
    exit 1
fi
if lsof -i:9091 >/dev/null 2>&1; then
    log_error "Le port 9091 est encore utilisé !"
    lsof -i:9091
    exit 1
fi
log_success "Ports 9090-9091 libres"

# 9. Résumé
echo ""
echo "======================================================================="
echo "✅ Nettoyage terminé avec succès"
echo "======================================================================="
echo ""
log_info "Tous les conteneurs, volumes, images et caches ont été supprimés"
log_info "Pour redémarrer le voicebot proprement, utilisez :"
echo ""
echo "    docker-compose up -d"
echo ""
log_warning "⚠️  Les bases de données sont VIDES (volumes supprimés)"
log_info "Les tables seront recréées automatiquement au démarrage"
echo ""

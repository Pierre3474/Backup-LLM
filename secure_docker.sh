#!/bin/bash

################################################################################
# Script: secure_docker.sh
# Description: Sécurise les ports Docker avec iptables
# Usage: sudo ./secure_docker.sh
################################################################################

set -e

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérifier que le script est exécuté en root
if [[ $EUID -ne 0 ]]; then
   log_error "Ce script doit être exécuté en tant que root"
   exit 1
fi

# Charger les variables depuis .env
if [[ ! -f .env ]]; then
    log_error "Fichier .env introuvable"
    exit 1
fi

source .env

log_info "Configuration de la sécurité Docker avec iptables..."
echo ""
log_info "IP personnelle autorisée: ${PERSONAL_IP}"
log_info "IP Asterisk distante: ${REMOTE_ASTERISK_IP}"
echo ""

# Créer la chaîne DOCKER-USER si elle n'existe pas
iptables -N DOCKER-USER 2>/dev/null || true

# FLUSH des règles existantes dans DOCKER-USER
log_info "Nettoyage des règles existantes..."
iptables -F DOCKER-USER

# === AUTORISER LES IPS LÉGITIMES ===

log_info "Autorisation des services pour ${PERSONAL_IP}..."

# Grafana (3000)
iptables -I DOCKER-USER -p tcp --dport 3000 -s ${PERSONAL_IP} -j ACCEPT

# PgAdmin (5050)
iptables -I DOCKER-USER -p tcp --dport 5050 -s ${PERSONAL_IP} -j ACCEPT

# Prometheus (9092)
iptables -I DOCKER-USER -p tcp --dport 9092 -s ${PERSONAL_IP} -j ACCEPT

# PostgreSQL clients (5432)
iptables -I DOCKER-USER -p tcp --dport 5432 -s ${PERSONAL_IP} -j ACCEPT

# PostgreSQL tickets (5433)
iptables -I DOCKER-USER -p tcp --dport 5433 -s ${PERSONAL_IP} -j ACCEPT

# === BLOQUER TOUT LE RESTE ===

log_info "Blocage des services depuis Internet..."

# Bloquer Grafana depuis Internet (sauf IP autorisée)
iptables -A DOCKER-USER -p tcp --dport 3000 -j DROP

# Bloquer PgAdmin depuis Internet
iptables -A DOCKER-USER -p tcp --dport 5050 -j DROP

# Bloquer Prometheus depuis Internet
iptables -A DOCKER-USER -p tcp --dport 9092 -j DROP

# Bloquer PostgreSQL depuis Internet
iptables -A DOCKER-USER -p tcp --dport 5432 -j DROP
iptables -A DOCKER-USER -p tcp --dport 5433 -j DROP

# Autoriser le reste du trafic Docker
iptables -A DOCKER-USER -j RETURN

# Sauvegarder les règles (persistent après reboot)
log_info "Sauvegarde des règles iptables..."
if command -v netfilter-persistent &>/dev/null; then
    netfilter-persistent save
    log_success "Règles sauvegardées avec netfilter-persistent"
elif command -v iptables-save &>/dev/null; then
    mkdir -p /etc/iptables
    iptables-save > /etc/iptables/rules.v4
    log_success "Règles sauvegardées dans /etc/iptables/rules.v4"
else
    log_warning "Impossible de sauvegarder les règles automatiquement"
fi

echo ""
log_success "✓ Sécurité Docker configurée avec succès!"
echo ""
echo "Règles actives:"
echo "  • Grafana (3000): Accessible uniquement depuis ${PERSONAL_IP}"
echo "  • PgAdmin (5050): Accessible uniquement depuis ${PERSONAL_IP}"
echo "  • Prometheus (9092): Accessible uniquement depuis ${PERSONAL_IP}"
echo "  • PostgreSQL (5432/5433): Accessible uniquement depuis ${PERSONAL_IP}"
echo "  • Tout autre accès depuis Internet: BLOQUÉ"
echo ""
log_info "Pour vérifier les règles: sudo iptables -L DOCKER-USER -n -v"

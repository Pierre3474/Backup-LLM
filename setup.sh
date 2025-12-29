#!/bin/bash

################################################################################
# setup.sh - Script d'installation automatisée pour Voicebot PY_SAV
#
# Usage:
#   ./setup.sh              # Mode install (par défaut)
#   ./setup.sh install      # Mode install (explicite)
#   ./setup.sh clean        # Mode clean (nettoyage complet)
#
# Environnement: Debian 13
# Exécution: root
################################################################################

set -e  # Arrêt immédiat en cas d'erreur

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Répertoire du script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

################################################################################
# Fonctions utilitaires
################################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Ce script doit être exécuté en tant que root"
        log_info "Utilisez: sudo ./setup.sh"
        exit 1
    fi
}

################################################################################
# Fonction: get_user_vars
# Collecte et valide toutes les variables nécessaires à l'installation
################################################################################

get_user_vars() {
    log_info "Collecte des variables d'environnement..."
    echo ""

    # DEEPGRAM_API_KEY
    while true; do
        read -p "$(echo -e ${BLUE}Entrez votre DEEPGRAM_API_KEY:${NC} )" DEEPGRAM_API_KEY
        if [[ -n "$DEEPGRAM_API_KEY" ]]; then
            break
        fi
        log_warning "La clé API Deepgram ne peut pas être vide"
    done

    # GROQ_API_KEY
    while true; do
        read -p "$(echo -e ${BLUE}Entrez votre GROQ_API_KEY:${NC} )" GROQ_API_KEY
        if [[ -n "$GROQ_API_KEY" ]]; then
            break
        fi
        log_warning "La clé API Groq ne peut pas être vide"
    done

    # ELEVENLABS_API_KEY
    while true; do
        read -p "$(echo -e ${BLUE}Entrez votre ELEVENLABS_API_KEY:${NC} )" ELEVENLABS_API_KEY
        if [[ -n "$ELEVENLABS_API_KEY" ]]; then
            break
        fi
        log_warning "La clé API ElevenLabs ne peut pas être vide"
    done

    # DB_PASSWORD
    while true; do
        read -sp "$(echo -e ${BLUE}Entrez le mot de passe PostgreSQL:${NC} )" DB_PASSWORD
        echo ""
        if [[ -n "$DB_PASSWORD" ]]; then
            read -sp "$(echo -e ${BLUE}Confirmez le mot de passe PostgreSQL:${NC} )" DB_PASSWORD_CONFIRM
            echo ""
            if [[ "$DB_PASSWORD" == "$DB_PASSWORD_CONFIRM" ]]; then
                break
            fi
            log_warning "Les mots de passe ne correspondent pas"
        else
            log_warning "Le mot de passe ne peut pas être vide"
        fi
    done


    # SERVER_HOST_IP
    # Détecter l'IP locale automatiquement et proposer
    DEFAULT_IP=$(hostname -I | awk '{print $1}')
    read -p "$(echo -e ${BLUE}Entrez l\'adresse IP locale du serveur IA [${DEFAULT_IP}]:${NC} )" SERVER_HOST_IP
    SERVER_HOST_IP=${SERVER_HOST_IP:-$DEFAULT_IP}

    # Validation IP
    if ! [[ $SERVER_HOST_IP =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        log_warning "Format d'IP invalide, utilisation de $DEFAULT_IP"
        SERVER_HOST_IP=$DEFAULT_IP
    fi

    # REMOTE_ASTERISK_IP (support de plusieurs IPs)
    echo ""
    log_info "Configuration des serveurs Asterisk autorisés"
    log_info "Vous pouvez autoriser plusieurs serveurs Asterisk (plusieurs clients)"
    echo ""

    ASTERISK_IPS=()
    ASTERISK_IP_COUNT=0

    while true; do
        ASTERISK_IP_COUNT=$((ASTERISK_IP_COUNT + 1))

        if [ $ASTERISK_IP_COUNT -eq 1 ]; then
            prompt_msg="Entrez l'adresse IP du 1er serveur Asterisk"
        else
            prompt_msg="Entrez l'IP du serveur Asterisk $ASTERISK_IP_COUNT (ou laissez vide pour terminer)"
        fi

        read -p "$(echo -e ${BLUE}$prompt_msg:${NC} )" ASTERISK_IP

        # Si vide et au moins 1 IP déjà saisie, on termine
        if [[ -z "$ASTERISK_IP" ]] && [ ${#ASTERISK_IPS[@]} -gt 0 ]; then
            break
        fi

        # Si vide et aucune IP, on redemande
        if [[ -z "$ASTERISK_IP" ]] && [ ${#ASTERISK_IPS[@]} -eq 0 ]; then
            log_warning "Au moins 1 serveur Asterisk doit être configuré"
            ASTERISK_IP_COUNT=$((ASTERISK_IP_COUNT - 1))
            continue
        fi

        # Validation IP
        if [[ $ASTERISK_IP =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
            ASTERISK_IPS+=("$ASTERISK_IP")
            log_success "IP $ASTERISK_IP ajoutée (${#ASTERISK_IPS[@]} serveur(s) configuré(s))"
        else
            log_warning "Format d'IP invalide"
            ASTERISK_IP_COUNT=$((ASTERISK_IP_COUNT - 1))
        fi
    done

    # Garder la première IP comme REMOTE_ASTERISK_IP pour compatibilité
    REMOTE_ASTERISK_IP="${ASTERISK_IPS[0]}"

    echo ""
    log_success "${#ASTERISK_IPS[@]} serveur(s) Asterisk configuré(s)"

    # AMI_USERNAME (pour récupération CALLERID via AMI)
    read -p "$(echo -e ${BLUE}Entrez le nom d\'utilisateur AMI Asterisk [voicebot-ami]:${NC} )" AMI_USERNAME
    AMI_USERNAME=${AMI_USERNAME:-voicebot-ami}

    # AMI_SECRET
    while true; do
        read -sp "$(echo -e ${BLUE}Entrez le mot de passe AMI Asterisk:${NC} )" AMI_SECRET
        echo ""
        if [[ -n "$AMI_SECRET" ]]; then
            break
        fi
        log_warning "Le mot de passe AMI ne peut pas être vide"
    done

    # PERSONAL_IP (pour sécuriser Dashboard, PostgreSQL)
    echo ""
    log_info "=== SÉCURITÉ : Accès aux services d'administration ==="
    echo ""
    echo "Pour sécuriser Dashboard et PostgreSQL,"
    echo "vous devez fournir votre adresse IP publique personnelle."
    echo ""
    echo "Pour connaître votre IP publique, visitez: https://mon-ip.io"
    echo "ou tapez: curl ifconfig.me"
    echo ""

    while true; do
        read -p "$(echo -e ${BLUE}Entrez votre adresse IP publique personnelle:${NC} )" PERSONAL_IP
        if [[ -n "$PERSONAL_IP" ]]; then
            # Validation IP
            if [[ $PERSONAL_IP =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
                break
            else
                log_warning "Format d'IP invalide"
            fi
        else
            log_warning "L'adresse IP personnelle ne peut pas être vide"
        fi
    done

    echo ""
    log_success "Variables collectées avec succès"
    log_info "SERVER_HOST_IP (serveur IA): $SERVER_HOST_IP"
    log_info "REMOTE_ASTERISK_IP: $REMOTE_ASTERISK_IP"
    log_info "AMI_USERNAME: $AMI_USERNAME"
    log_info "PERSONAL_IP (accès admin): $PERSONAL_IP"
}

################################################################################
# Fonction: generate_env_file
# Génère le fichier .env avec les DSN PostgreSQL et toutes les configurations
################################################################################

generate_env_file() {
    log_info "Génération du fichier .env..."

    # Créer le fichier .env
    # IMPORTANT: Les DSN doivent contenir le mot de passe en dur (pas de ${VAR})
    # car les fichiers .env ne supportent PAS l'interpolation de variables
    cat > .env <<EOF
# ============================================
# Configuration Voicebot PY_SAV
# Généré automatiquement par setup.sh
# Date: $(date)
# ============================================

# === API Keys ===
DEEPGRAM_API_KEY=${DEEPGRAM_API_KEY}
GROQ_API_KEY=${GROQ_API_KEY}
ELEVENLABS_API_KEY=${ELEVENLABS_API_KEY}

# === ElevenLabs TTS Configuration ===
# Modèle Flash v2.5 pour latence ultra-faible (<300ms)
ELEVENLABS_MODEL=eleven_flash_v2_5
# Voix française Adrien (claire et naturelle)
ELEVENLABS_VOICE_ID=N2lVS1w4EtoT3dr4eOWO

# === Database Configuration ===
DB_PASSWORD=${DB_PASSWORD}
DB_CLIENTS_DSN=postgresql://voicebot:${DB_PASSWORD}@postgres-clients:5432/db_clients
DB_TICKETS_DSN=postgresql://voicebot:${DB_PASSWORD}@postgres-tickets:5432/db_tickets

# === Server Configuration ===
SERVER_HOST_IP=${SERVER_HOST_IP}
AUDIOSOCKET_PORT=9090

# === Remote Asterisk Configuration ===
REMOTE_ASTERISK_IP=${REMOTE_ASTERISK_IP}

# === Asterisk AMI Configuration ===
# Configuration pour récupérer le CALLERID via AMI
AMI_HOST=${REMOTE_ASTERISK_IP}
AMI_PORT=5038
AMI_USERNAME=${AMI_USERNAME}
AMI_SECRET=${AMI_SECRET}

# === Security Configuration ===
# IP personnelle autorisée pour accéder aux services d'administration
PERSONAL_IP=${PERSONAL_IP}

# === Logging ===
LOG_LEVEL=INFO
EOF

    chmod 600 .env  # Sécuriser le fichier
    log_success "Fichier .env créé avec succès"
}

################################################################################
# Fonction: generate_docker_compose_override
# Génère un fichier docker-compose.override.yml avec les mots de passe
################################################################################

generate_docker_compose_override() {
    log_info "Génération du fichier docker-compose.override.yml..."

    cat > docker-compose.override.yml <<EOF
# Configuration override pour les mots de passe
# Généré automatiquement par setup.sh

version: '3.8'

services:
  postgres-clients:
    environment:
      - POSTGRES_PASSWORD=${DB_PASSWORD}

  postgres-tickets:
    environment:
      - POSTGRES_PASSWORD=${DB_PASSWORD}
EOF

    log_success "Fichier docker-compose.override.yml créé avec succès"
}

################################################################################
# Fonction: install_system_prerequisites
# Installe tous les prérequis système pour Debian 13
################################################################################

install_system_prerequisites() {
    log_info "Installation des prérequis système (Debian 12/13)..."

    # Mise à jour des dépôts
    log_info "Mise à jour des dépôts apt..."
    apt-get update -qq

    # Installation des paquets système de base (sans Docker)
    log_info "Installation des paquets de base: python3, python3-venv, ffmpeg, git, curl, ufw..."
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
        python3 \
        python3-venv \
        python3-pip \
        ffmpeg \
        git \
        curl \
        ca-certificates \
        gnupg \
        lsb-release \
        ufw 2>&1 | grep -v "^Reading\|^Building\|^The following"

    if [ ${PIPESTATUS[0]} -ne 0 ]; then
        log_warning "Certains paquets ont échoué, mais on continue..."
    fi

    # Vérifier si Docker est déjà installé
    if command -v docker &> /dev/null; then
        log_success "Docker est déjà installé (version: $(docker --version))"
    else
        log_info "Docker n'est pas installé - Installation via le script officiel..."

        # Télécharger et exécuter le script officiel Docker
        curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
        sh /tmp/get-docker.sh
        rm -f /tmp/get-docker.sh

        log_success "Docker installé avec succès"
    fi

    # Vérifier si docker-compose est installé (v2 plugin ou standalone)
    if docker compose version &> /dev/null; then
        log_success "Docker Compose (plugin) est disponible"
    elif command -v docker-compose &> /dev/null; then
        log_success "Docker Compose (standalone) est disponible"
    else
        log_warning "Docker Compose n'est pas installé - Installation..."
        # Installer docker-compose via apt si disponible
        DEBIAN_FRONTEND=noninteractive apt-get install -y docker-compose 2>&1 | grep -v "^Reading"
        if [ ${PIPESTATUS[0]} -ne 0 ]; then
            log_warning "Impossible d'installer docker-compose via apt, mais Docker Compose v2 (plugin) devrait être disponible"
        fi
    fi

    # Créer l'utilisateur système dédié pour le service voicebot
    log_info "Création de l'utilisateur système 'voicebot'..."
    if ! id -u voicebot &>/dev/null; then
        useradd -r -s /bin/false voicebot
        log_success "Utilisateur 'voicebot' créé"
    else
        log_info "Utilisateur 'voicebot' existe déjà"
    fi

    # Ajouter voicebot au groupe docker
    log_info "Ajout de l'utilisateur 'voicebot' au groupe docker..."
    usermod -aG docker voicebot 2>/dev/null || log_warning "Impossible d'ajouter voicebot au groupe docker"

    # Définir les permissions sur le répertoire du projet
    log_info "Application des permissions pour l'utilisateur 'voicebot'..."
    chown -R voicebot:voicebot .

    # Démarrer et activer Docker
    log_info "Démarrage du service Docker..."
    systemctl start docker 2>/dev/null || log_warning "Docker déjà démarré ou erreur de démarrage"
    systemctl enable docker 2>/dev/null

    log_success "Prérequis système installés avec succès"
}

################################################################################
# Fonction: setup_python_environment
# Configure l'environnement Python et génère le cache audio
################################################################################

setup_python_environment() {
    log_info "Configuration de l'environnement Python..."

    # Créer l'environnement virtuel
    if [[ ! -d "venv" ]]; then
        log_info "Création de l'environnement virtuel..."
        python3 -m venv venv
    else
        log_info "Environnement virtuel déjà existant"
    fi

    # Activer l'environnement virtuel
    source venv/bin/activate

    # Mettre à jour pip
    log_info "Mise à jour de pip..."
    pip install --upgrade pip > /dev/null 2>&1

    # Installer les dépendances
    log_info "Installation des dépendances Python (cela peut prendre quelques minutes)..."
    pip install -r requirements.txt > /dev/null 2>&1

    log_success "Environnement Python configuré avec succès"
}

################################################################################
# Fonction: generate_audio_cache
# Génère le cache audio avec generate_cache.py
################################################################################

generate_audio_cache() {
    log_info "Génération du cache audio..."

    # Vérifier que l'environnement virtuel est activé
    if [[ -z "$VIRTUAL_ENV" ]]; then
        source venv/bin/activate
    fi

    # Générer le cache (non-bloquant)
    if python generate_cache.py 2>/dev/null; then
        log_success "Cache audio généré avec succès"
    else
        log_warning "Impossible de générer le cache audio (conflit de dépendances)"
        log_warning "Le serveur fonctionnera en mode dynamique (génération TTS à la volée)"
        log_info "Pour corriger plus tard: pip install --upgrade httpx openai"
    fi
}

################################################################################
# Fonction: setup_docker_stack
# Lance la stack Docker et initialise les bases de données
################################################################################

setup_docker_stack() {
    log_info "Configuration de la stack Docker..."

    # Lancer Docker Compose
    log_info "Démarrage des conteneurs Docker..."
    docker compose up -d

    # Attendre que les bases de données soient prêtes
    log_info "Attente du démarrage des bases de données (30 secondes)..."
    sleep 30

    # Initialiser la base de données clients
    log_info "Initialisation de la base de données clients (db_clients)..."
    docker compose exec -T postgres-clients psql -U voicebot -d db_clients < init_clients.sql

    # Initialiser la base de données tickets
    log_info "Initialisation de la base de données tickets (db_tickets)..."
    docker compose exec -T postgres-tickets psql -U voicebot -d db_tickets < init_tickets.sql

    log_success "Stack Docker configurée et initialisée avec succès"
}

################################################################################
# Fonction: configure_firewall
# Configure UFW pour autoriser le port 9090 uniquement depuis l'IP Asterisk distante
################################################################################

configure_firewall() {
    log_info "Configuration du firewall UFW..."

    # Port 9090 pour AudioSocket (tous les serveurs Asterisk autorisés)
    log_info "Autorisation du port TCP 9090 pour ${#ASTERISK_IPS[@]} serveur(s) Asterisk..."

    # Créer le fichier des IPs autorisées
    ALLOWED_IPS_FILE="/opt/PY_SAV/.allowed_asterisk_ips"
    > "$ALLOWED_IPS_FILE"  # Vider le fichier
    chmod 600 "$ALLOWED_IPS_FILE"

    local ip_count=0
    for asterisk_ip in "${ASTERISK_IPS[@]}"; do
        ip_count=$((ip_count + 1))
        log_info "  [$ip_count/${#ASTERISK_IPS[@]}] Autorisation de $asterisk_ip..."
        ufw allow from "$asterisk_ip" to any port 9090 proto tcp comment "AudioSocket Asterisk #$ip_count"

        # Ajouter l'IP au fichier de configuration
        echo "$asterisk_ip|Serveur Asterisk #$ip_count" >> "$ALLOWED_IPS_FILE"
    done

    # Convertir PERSONAL_IP en tableau (support multi-IP séparées par virgule)
    IFS=',' read -ra PERSONAL_IPS <<< "$PERSONAL_IP"

    # Services d'administration (IPs personnelles autorisées)
    log_info "Sécurisation des services d'administration depuis ${#PERSONAL_IPS[@]} IP(s)..."

    local personal_ip_count=0
    for personal_ip in "${PERSONAL_IPS[@]}"; do
        personal_ip_count=$((personal_ip_count + 1))
        log_info "  [$personal_ip_count/${#PERSONAL_IPS[@]}] Autorisation de $personal_ip..."

        ufw allow from "$personal_ip" to any port 8501 proto tcp comment "Dashboard - IP admin #$personal_ip_count"
        ufw allow from "$personal_ip" to any port 5432 proto tcp comment "PostgreSQL clients - IP admin #$personal_ip_count"
        ufw allow from "$personal_ip" to any port 5433 proto tcp comment "PostgreSQL tickets - IP admin #$personal_ip_count"
    done

    log_success "Firewall configuré avec succès"
    log_info "AudioSocket (9090): accessible depuis ${#ASTERISK_IPS[@]} serveur(s) Asterisk"
    for asterisk_ip in "${ASTERISK_IPS[@]}"; do
        log_info "  - $asterisk_ip"
    done
    log_info "Services admin (Dashboard, PostgreSQL): accessible depuis ${#PERSONAL_IPS[@]} IP(s)"
    for personal_ip in "${PERSONAL_IPS[@]}"; do
        log_info "  - $personal_ip"
    done
}

################################################################################
# Fonction: configure_docker_firewall
# Configure iptables pour bloquer Docker depuis Internet (Docker contourne UFW!)
# IMPORTANT: Docker modifie directement iptables et contourne UFW
################################################################################

configure_docker_firewall() {
    log_info "Configuration des règles iptables pour Docker (Docker contourne UFW!)..."

    # La chaîne DOCKER-USER permet de contrôler Docker avant ses propres règles
    # Créer la chaîne si elle n'existe pas déjà
    iptables -N DOCKER-USER 2>/dev/null || true

    # FLUSH des règles existantes dans DOCKER-USER (pour éviter les doublons)
    iptables -F DOCKER-USER

    # Convertir PERSONAL_IP en tableau (support multi-IP séparées par virgule)
    IFS=',' read -ra PERSONAL_IPS <<< "$PERSONAL_IP"

    # === AUTORISER LES IPS LÉGITIMES ===

    # 1. Autoriser les serveurs Asterisk sur le port 9090 (AudioSocket)
    log_info "Autorisation AudioSocket (9090) depuis ${#ASTERISK_IPS[@]} serveur(s) Asterisk..."

    local asterisk_ip_count=0
    for asterisk_ip in "${ASTERISK_IPS[@]}"; do
        asterisk_ip_count=$((asterisk_ip_count + 1))

        # AudioSocket (9090) - CRITIQUE pour recevoir les appels
        iptables -I DOCKER-USER -p tcp --dport 9090 -s "$asterisk_ip" -j ACCEPT

        log_info "  [$asterisk_ip_count/${#ASTERISK_IPS[@]}] IP Asterisk $asterisk_ip autorisée (port 9090)"
    done

    # 2. Autoriser les IPs admin pour les services d'administration
    log_info "Autorisation services admin depuis ${#PERSONAL_IPS[@]} IP(s)..."

    local personal_ip_count=0
    for personal_ip in "${PERSONAL_IPS[@]}"; do
        personal_ip_count=$((personal_ip_count + 1))

        # Dashboard Streamlit (8501)
        iptables -I DOCKER-USER -p tcp --dport 8501 -s "$personal_ip" -j ACCEPT

        # PostgreSQL clients (5432)
        iptables -I DOCKER-USER -p tcp --dport 5432 -s "$personal_ip" -j ACCEPT

        # PostgreSQL tickets (5433)
        iptables -I DOCKER-USER -p tcp --dport 5433 -s "$personal_ip" -j ACCEPT

        log_info "  [$personal_ip_count/${#PERSONAL_IPS[@]}] IP admin $personal_ip autorisée (ports: 8501, 5432, 5433)"
    done

    # === BLOQUER TOUT LE RESTE ===

    # Bloquer AudioSocket (9090) depuis Internet (sauf IPs Asterisk autorisées)
    log_info "Blocage AudioSocket (9090) depuis Internet..."
    iptables -A DOCKER-USER -p tcp --dport 9090 -j DROP

    # Bloquer Dashboard Streamlit depuis Internet
    log_info "Blocage Dashboard Streamlit depuis Internet..."
    iptables -A DOCKER-USER -p tcp --dport 8501 -j DROP

    # Bloquer PostgreSQL depuis Internet
    log_info "Blocage PostgreSQL depuis Internet..."
    iptables -A DOCKER-USER -p tcp --dport 5432 -j DROP
    iptables -A DOCKER-USER -p tcp --dport 5433 -j DROP

    # Autoriser le reste du trafic Docker normal
    iptables -A DOCKER-USER -j RETURN

    # Sauvegarder les règles iptables (persistent après reboot)
    log_info "Sauvegarde des règles iptables..."
    if command -v netfilter-persistent &>/dev/null; then
        netfilter-persistent save
    elif command -v iptables-save &>/dev/null; then
        iptables-save > /etc/iptables/rules.v4
    fi

    log_success "Règles iptables Docker configurées avec succès"
    log_warning "IMPORTANT: Ces règles bloquent l'accès depuis Internet aux services Docker"

    log_info "IPs Asterisk autorisées (port 9090 AudioSocket): ${#ASTERISK_IPS[@]} serveur(s)"
    for asterisk_ip in "${ASTERISK_IPS[@]}"; do
        log_info "  - $asterisk_ip"
    done

    log_info "IPs admin autorisées (Dashboard, PostgreSQL): ${#PERSONAL_IPS[@]} IP(s)"
    for personal_ip in "${PERSONAL_IPS[@]}"; do
        log_info "  - $personal_ip"
    done
}

################################################################################
# Fonction: display_summary
# Affiche un résumé des services et leurs URLs
################################################################################

display_summary() {
    # Convertir PERSONAL_IP en tableau (support multi-IP)
    IFS=',' read -ra PERSONAL_IPS <<< "$PERSONAL_IP"

    echo ""
    echo "======================================================================="
    echo -e "${GREEN}Installation terminée avec succès!${NC}"
    echo "======================================================================="
    echo ""
    echo "📊 Services disponibles:"
    echo ""
    echo -e "  ${BLUE}AudioSocket (Asterisk):${NC}  ${SERVER_HOST_IP}:9090  ${GREEN}✓ Sécurisé (${#ASTERISK_IPS[@]} IP(s))${NC}"
    echo -e "  ${BLUE}PostgreSQL (clients):${NC}    ${SERVER_HOST_IP}:5432  ${GREEN}✓ Sécurisé (${#PERSONAL_IPS[@]} IP(s))${NC}"
    echo -e "  ${BLUE}PostgreSQL (tickets):${NC}    ${SERVER_HOST_IP}:5433  ${GREEN}✓ Sécurisé (${#PERSONAL_IPS[@]} IP(s))${NC}"
    echo -e "  ${BLUE}Dashboard Streamlit:${NC}     http://${SERVER_HOST_IP}:8501  ${GREEN}✓ Sécurisé (${#PERSONAL_IPS[@]} IP(s))${NC}"
    echo ""
    echo "🔒 Sécurité:"
    echo -e "  ${GREEN}✓${NC} Services d'administration accessibles depuis ${#PERSONAL_IPS[@]} IP(s) autorisée(s):"
    for personal_ip in "${PERSONAL_IPS[@]}"; do
        echo -e "      → ${GREEN}${personal_ip}${NC}"
    done
    echo -e "  ${GREEN}✓${NC} AudioSocket (9090) accessible depuis ${#ASTERISK_IPS[@]} serveur(s) Asterisk:"
    for asterisk_ip in "${ASTERISK_IPS[@]}"; do
        echo -e "      → ${GREEN}${asterisk_ip}${NC}"
    done
    echo ""
    echo "🤖 Serveur Intelligence Artificielle:"
    echo -e "  ${BLUE}Adresse IP de ce serveur IA:${NC} ${GREEN}${SERVER_HOST_IP}${NC}"
    echo -e "  ${BLUE}Port AudioSocket:${NC}            ${GREEN}9090${NC}"
    echo ""
    echo "☎️  Configuration Asterisk (serveur distant: ${REMOTE_ASTERISK_IP}):"
    echo -e "  ${YELLOW}⚠️  IMPORTANT: Vous devez configurer votre serveur Asterisk distant${NC}"
    echo ""
    echo -e "  ${BLUE}Configuration dialplan requise:${NC}"
    echo -e "    ${BLUE}Set(GLOBAL(CALLER_\${UNIQUEID})=\${CALLERID(num)})${NC}"
    echo -e "    ${BLUE}AudioSocket(\${UNIQUEID},${GREEN}${SERVER_HOST_IP}:9090${BLUE})${NC}"
    echo ""
    echo -e "  ${BLUE}Configuration AMI requise:${NC}"
    echo -e "    ${BLUE}Utilisateur AMI:${NC} ${AMI_USERNAME}"
    echo -e "    ${BLUE}Port AMI:${NC} 5038"
    echo ""
    echo -e "  ${YELLOW}    Consultez le fichier 'asterisk_config.txt' pour la configuration complète.${NC}"
    echo ""
    echo "🚀 Lancement du serveur voicebot..."
    echo "   (Ctrl+C pour arrêter)"
    echo ""
    echo "======================================================================="
    echo ""
}

################################################################################
# Fonction: start_voicebot_server
# Lance le serveur Python voicebot
################################################################################

start_voicebot_server() {
    log_info "Activation de l'environnement virtuel..."
    source venv/bin/activate

    log_info "Démarrage du serveur voicebot sur le port 9090..."
    echo ""
    python server.py
}

################################################################################
# Fonction: check_existing_installation
# Vérifie si une installation existe et demande à l'utilisateur quoi faire
################################################################################

check_existing_installation() {
    SKIP_CONFIGURATION=false

    # Vérifier si un fichier .env existe
    if [[ -f ".env" ]]; then
        echo ""
        echo "======================================================================="
        echo -e "${YELLOW}⚠️  CONFIGURATION EXISTANTE DÉTECTÉE${NC}"
        echo "======================================================================="
        echo ""
        log_info "Un fichier .env a été trouvé avec une configuration existante."
        echo ""
        echo "╔═══════════════════════════════════════════════════════════════════╗"
        echo "║  OPTION 1 : Démarrage Rapide (Garder la config actuelle)         ║"
        echo "╠═══════════════════════════════════════════════════════════════════╣"
        echo "║  ✓ Ne demande RIEN (clés, IPs, mots de passe conservés)          ║"
        echo "║  ✓ Charge les variables depuis .env existant                     ║"
        echo "║  ✓ Passe directement à : Cache audio → Docker → Firewall         ║"
        echo "║  ✓ Redémarre les services avec la config actuelle                ║"
        echo "╚═══════════════════════════════════════════════════════════════════╝"
        echo ""
        echo "╔═══════════════════════════════════════════════════════════════════╗"
        echo "║  OPTION 2 : Reconfiguration Complète (Tout effacer)              ║"
        echo "╠═══════════════════════════════════════════════════════════════════╣"
        echo "║  ⚠  AVERTISSEMENT : Cette option écrase tout                      ║"
        echo "║  ↻ Redemande TOUTES les variables :                              ║"
        echo "║     - Clés API (Deepgram, Groq, ElevenLabs)                       ║"
        echo "║     - IPs (Serveur IA, Asterisk, Admin)                          ║"
        echo "║     - Mots de passe (PostgreSQL, AMI)                             ║"
        echo "║  ✗ Écrase .env et docker-compose.override.yml                     ║"
        echo "╚═══════════════════════════════════════════════════════════════════╝"
        echo ""

        while true; do
            read -p "$(echo -e ${BLUE}Votre choix [1/2]:${NC} )" choice
            case $choice in
                1)
                    log_success "✓ Démarrage Rapide : Configuration existante conservée"
                    SKIP_CONFIGURATION=true

                    # Charger TOUTES les variables depuis .env (crucial pour éviter les erreurs plus tard)
                    set -a  # Auto-export toutes les variables
                    source .env 2>/dev/null || {
                        log_error "Impossible de charger .env - fichier corrompu ?"
                        SKIP_CONFIGURATION=false
                        return
                    }
                    set +a

                    # Reconstruire le tableau ASTERISK_IPS depuis le fichier des IPs autorisées
                    ASTERISK_IPS=()
                    ALLOWED_IPS_FILE="/opt/PY_SAV/.allowed_asterisk_ips"
                    if [[ -f "$ALLOWED_IPS_FILE" ]]; then
                        while IFS='|' read -r ip description; do
                            if [[ -n "$ip" ]]; then
                                ASTERISK_IPS+=("$ip")
                            fi
                        done < "$ALLOWED_IPS_FILE"
                    else
                        # Fallback: utiliser REMOTE_ASTERISK_IP si fichier manquant
                        if [[ -n "$REMOTE_ASTERISK_IP" ]]; then
                            ASTERISK_IPS=("$REMOTE_ASTERISK_IP")
                        fi
                    fi

                    # Convertir PERSONAL_IP en tableau pour affichage
                    IFS=',' read -ra PERSONAL_IPS_ARRAY <<< "$PERSONAL_IP"

                    echo ""
                    log_info "Configuration chargée depuis .env :"
                    log_info "  ├─ Serveur IA         : ${SERVER_HOST_IP:-non défini}"
                    log_info "  ├─ Serveur Asterisk   : ${AMI_HOST:-non défini}"
                    log_info "  ├─ Utilisateur AMI    : ${AMI_USERNAME:-non défini}"
                    log_info "  ├─ IPs Asterisk       : ${#ASTERISK_IPS[@]} serveur(s)"
                    log_info "  ├─ IPs Admin          : ${#PERSONAL_IPS_ARRAY[@]} IP(s)"
                    log_info "  └─ Base de données    : ${DB_CLIENTS_DSN:-non défini}"
                    echo ""
                    log_info "Les étapes suivantes : Génération cache → Docker → Firewall → Démarrage"
                    echo ""
                    break
                    ;;
                2)
                    log_warning "⚠  Reconfiguration complète - les anciennes valeurs seront ÉCRASÉES"
                    SKIP_CONFIGURATION=false
                    echo ""
                    read -p "$(echo -e ${RED}Êtes-vous ABSOLUMENT sûr ? [y/N]:${NC} )" -n 1 -r
                    echo ""
                    if [[ $REPLY =~ ^[Yy]$ ]]; then
                        log_info "Suppression de la configuration existante..."
                        rm -f .env docker-compose.override.yml 2>/dev/null
                        log_success "Ancienne configuration supprimée - collecte des nouvelles variables..."
                        echo ""
                        break
                    else
                        log_info "Annulé - retour au menu"
                        echo ""
                    fi
                    ;;
                *)
                    log_warning "Choix invalide. Veuillez entrer 1 ou 2."
                    ;;
            esac
        done
    fi
}

################################################################################
# Fonction: install_full_stack
# Fonction principale d'installation complète
################################################################################

install_full_stack() {
    echo ""
    echo "======================================================================="
    echo -e "${GREEN}Installation Serveur IA Voicebot PY_SAV${NC}"
    echo "======================================================================="
    echo ""

    # Vérifier s'il existe une installation précédente
    check_existing_installation

    # Étape 1: Prérequis système
    install_system_prerequisites

    # Étape 2: Configuration Python
    setup_python_environment

    # Étape 3: Collecte des variables (skip si configuration existante)
    if [[ "$SKIP_CONFIGURATION" == false ]]; then
        get_user_vars
    fi

    # Étape 4: Génération des fichiers de configuration (skip si configuration existante)
    if [[ "$SKIP_CONFIGURATION" == false ]]; then
        generate_env_file
        generate_docker_compose_override
    else
        log_info "Fichiers de configuration existants conservés"
        # Vérifier que docker-compose.override.yml existe
        if [[ ! -f "docker-compose.override.yml" ]]; then
            log_warning "docker-compose.override.yml manquant - régénération"
            generate_docker_compose_override
        fi
    fi

    # Étape 5: Génération du cache audio
    generate_audio_cache

    # Étape 6: Setup Docker
    setup_docker_stack

    # Étape 7: Configuration du firewall (uniquement si nouvelle config)
    if [[ "$SKIP_CONFIGURATION" == false ]]; then
        configure_firewall
        configure_docker_firewall  # IMPORTANT: Docker contourne UFW!
    else
        log_info "Configuration firewall existante conservée"
    fi

    # Étape 8: Afficher le résumé
    display_summary

    # Étape 9: Lancer le serveur
    start_voicebot_server
}

################################################################################
# Fonction: clean_environment
# Nettoie complètement l'environnement
################################################################################

clean_environment() {
    echo ""
    echo "======================================================================="
    echo -e "${YELLOW}Nettoyage de l'environnement${NC}"
    echo "======================================================================="
    echo ""

    log_warning "Cette opération va supprimer:"
    echo "  - La stack Docker (conteneurs, volumes, réseaux)"
    echo "  - L'environnement virtuel Python"
    echo "  - Les fichiers de configuration (.env, docker-compose.override.yml)"
    echo "  - Le cache audio"
    echo "  - Les logs"
    echo ""

    read -p "$(echo -e ${RED}Êtes-vous sûr de vouloir continuer? [y/N]:${NC} )" -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Nettoyage annulé"
        exit 0
    fi

    # Arrêter et supprimer la stack Docker
    if [[ -f "docker-compose.yml" ]]; then
        log_info "Arrêt et suppression de la stack Docker..."
        docker compose down -v 2>/dev/null || log_warning "Erreur lors de l'arrêt de Docker"
    fi

    # Supprimer l'environnement virtuel
    if [[ -d "venv" ]]; then
        log_info "Suppression de l'environnement virtuel..."
        rm -rf venv
    fi

    # Supprimer les fichiers de configuration
    log_info "Suppression des fichiers de configuration..."
    rm -f .env
    rm -f docker-compose.override.yml

    # Supprimer le cache audio
    if [[ -d "assets/cache" ]]; then
        log_info "Suppression du cache audio..."
        rm -rf assets/cache
    fi

    # Supprimer les logs
    if [[ -d "logs" ]]; then
        log_info "Suppression des logs..."
        rm -rf logs
    fi

    log_success "Nettoyage terminé"
    echo ""
    log_info "Note: Le serveur Asterisk distant doit être reconfiguré manuellement"
    echo "      si vous souhaitez le déconnecter de ce serveur IA."
    echo ""
}

################################################################################
# Point d'entrée principal
################################################################################

main() {
    # Vérifier les privilèges root
    check_root

    # Déterminer le mode d'exécution
    MODE=${1:-install}

    case $MODE in
        install)
            install_full_stack
            ;;
        clean)
            clean_environment

            # Demander si l'utilisateur souhaite installer après le nettoyage
            echo ""
            read -p "$(echo -e ${BLUE}Souhaitez-vous lancer l\'installation maintenant? [y/N]:${NC} )" -n 1 -r
            echo ""

            if [[ $REPLY =~ ^[Yy]$ ]]; then
                install_full_stack
            else
                log_info "Installation non lancée. Utilisez './setup.sh install' pour installer."
            fi
            ;;
        *)
            log_error "Mode inconnu: $MODE"
            echo ""
            echo "Usage:"
            echo "  ./setup.sh              # Mode install (par défaut)"
            echo "  ./setup.sh install      # Mode install (explicite)"
            echo "  ./setup.sh clean        # Mode clean (nettoyage)"
            exit 1
            ;;
    esac
}

# Lancer le script principal
main "$@"

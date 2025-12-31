#!/bin/bash

################################################################################
# Script de gestion des IPs autorisées pour le voicebot
# Permet d'ajouter/supprimer/lister les serveurs Asterisk autorisés
################################################################################

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fichier de configuration des IPs autorisées
ALLOWED_IPS_FILE="/opt/PY_SAV/.allowed_asterisk_ips"

################################################################################
# Fonctions utilitaires
################################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

################################################################################
# Fonction: validate_ip
# Valide qu'une chaîne est une adresse IP valide
################################################################################
validate_ip() {
    local ip=$1
    if [[ $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        # Vérifier que chaque octet est entre 0 et 255
        IFS='.' read -ra ADDR <<< "$ip"
        for i in "${ADDR[@]}"; do
            if [ $i -gt 255 ]; then
                return 1
            fi
        done
        return 0
    else
        return 1
    fi
}

################################################################################
# Fonction: list_allowed_ips
# Liste toutes les IPs autorisées
################################################################################
list_allowed_ips() {
    echo ""
    echo -e "${BLUE}==================================================================${NC}"
    echo -e "${BLUE}  IPs Asterisk autorisées pour le port 9090 (AudioSocket)${NC}"
    echo -e "${BLUE}==================================================================${NC}"
    echo ""

    if [ ! -f "$ALLOWED_IPS_FILE" ]; then
        log_warning "Aucune IP configurée (fichier $ALLOWED_IPS_FILE n'existe pas)"
        echo ""
        return
    fi

    if [ ! -s "$ALLOWED_IPS_FILE" ]; then
        log_warning "Aucune IP configurée (fichier vide)"
        echo ""
        return
    fi

    local count=0
    while IFS='|' read -r ip comment; do
        count=$((count + 1))
        if [ -n "$comment" ]; then
            echo -e "  ${GREEN}$count.${NC} ${YELLOW}$ip${NC} - $comment"
        else
            echo -e "  ${GREEN}$count.${NC} ${YELLOW}$ip${NC}"
        fi
    done < "$ALLOWED_IPS_FILE"

    echo ""
    log_info "Total: $count IP(s) autorisée(s)"
    echo ""
}

################################################################################
# Fonction: add_ip
# Ajoute une nouvelle IP autorisée
################################################################################
add_ip() {
    local new_ip=$1
    local comment=$2

    # Validation de l'IP
    if ! validate_ip "$new_ip"; then
        log_error "L'adresse IP '$new_ip' n'est pas valide"
        return 1
    fi

    # Créer le fichier s'il n'existe pas
    if [ ! -f "$ALLOWED_IPS_FILE" ]; then
        touch "$ALLOWED_IPS_FILE"
        chmod 600 "$ALLOWED_IPS_FILE"
    fi

    # Vérifier si l'IP existe déjà
    if grep -q "^$new_ip|" "$ALLOWED_IPS_FILE" 2>/dev/null; then
        log_warning "L'IP $new_ip est déjà autorisée"
        return 0
    fi

    # Ajouter l'IP au fichier
    echo "$new_ip|$comment" >> "$ALLOWED_IPS_FILE"

    # Ajouter la règle UFW
    log_info "Ajout de la règle firewall UFW..."
    sudo ufw allow from "$new_ip" to any port 9090 proto tcp comment "AudioSocket Asterisk - $comment"

    log_success "IP $new_ip autorisée avec succès"

    if [ -n "$comment" ]; then
        log_info "Commentaire: $comment"
    fi
}

################################################################################
# Fonction: remove_ip
# Supprime une IP autorisée
################################################################################
remove_ip() {
    local ip_to_remove=$1

    if [ ! -f "$ALLOWED_IPS_FILE" ]; then
        log_error "Aucune IP configurée"
        return 1
    fi

    # Vérifier si l'IP existe
    if ! grep -q "^$ip_to_remove|" "$ALLOWED_IPS_FILE"; then
        log_error "L'IP $ip_to_remove n'est pas dans la liste des IPs autorisées"
        return 1
    fi

    # Supprimer l'IP du fichier
    grep -v "^$ip_to_remove|" "$ALLOWED_IPS_FILE" > "$ALLOWED_IPS_FILE.tmp"
    mv "$ALLOWED_IPS_FILE.tmp" "$ALLOWED_IPS_FILE"

    # Supprimer la règle UFW
    log_info "Suppression de la règle firewall UFW..."
    sudo ufw delete allow from "$ip_to_remove" to any port 9090 proto tcp || log_warning "Règle UFW non trouvée"

    log_success "IP $ip_to_remove supprimée avec succès"
}

################################################################################
# Fonction: show_firewall_status
# Affiche l'état du firewall UFW pour le port 9090
################################################################################
show_firewall_status() {
    echo ""
    echo -e "${BLUE}==================================================================${NC}"
    echo -e "${BLUE}  État du firewall UFW (port 9090)${NC}"
    echo -e "${BLUE}==================================================================${NC}"
    echo ""

    sudo ufw status | grep "9090" || log_info "Aucune règle pour le port 9090"
    echo ""
}

################################################################################
# Fonction: interactive_add
# Mode interactif pour ajouter une IP
################################################################################
interactive_add() {
    echo ""
    echo -e "${GREEN}=== Ajout d'une nouvelle IP Asterisk autorisée ===${NC}"
    echo ""

    read -p "$(echo -e ${BLUE}Entrez l\'adresse IP du serveur Asterisk: ${NC})" ip
    read -p "$(echo -e ${BLUE}Commentaire/Description \(optionnel\): ${NC})" comment

    add_ip "$ip" "$comment"
}

################################################################################
# Fonction: interactive_remove
# Mode interactif pour supprimer une IP
################################################################################
interactive_remove() {
    echo ""
    list_allowed_ips

    read -p "$(echo -e ${BLUE}Entrez l\'IP à supprimer: ${NC})" ip

    read -p "$(echo -e ${YELLOW}Êtes-vous sûr de vouloir supprimer $ip? \(y/N\): ${NC})" confirm

    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        remove_ip "$ip"
    else
        log_info "Suppression annulée"
    fi
}

################################################################################
# Menu principal
################################################################################
show_menu() {
    echo ""
    echo -e "${BLUE}==================================================================${NC}"
    echo -e "${BLUE}     Gestion des IPs Asterisk autorisées - Voicebot SAV${NC}"
    echo -e "${BLUE}==================================================================${NC}"
    echo ""
    echo "  1) Lister les IPs autorisées"
    echo "  2) Ajouter une nouvelle IP"
    echo "  3) Supprimer une IP"
    echo "  4) Afficher l'état du firewall UFW"
    echo "  5) Quitter"
    echo ""
    read -p "$(echo -e ${BLUE}Choisissez une option \(1-5\): ${NC})" choice

    case $choice in
        1)
            list_allowed_ips
            show_menu
            ;;
        2)
            interactive_add
            show_menu
            ;;
        3)
            interactive_remove
            show_menu
            ;;
        4)
            show_firewall_status
            show_menu
            ;;
        5)
            echo ""
            log_info "Au revoir!"
            echo ""
            exit 0
            ;;
        *)
            log_error "Option invalide"
            show_menu
            ;;
    esac
}

################################################################################
# Point d'entrée principal
################################################################################

# Vérifier les permissions root
if [ "$EUID" -ne 0 ]; then
    log_error "Ce script doit être exécuté avec sudo"
    exit 1
fi

# Arguments en ligne de commande
case "${1:-}" in
    list|ls)
        list_allowed_ips
        ;;
    add)
        if [ -z "$2" ]; then
            log_error "Usage: $0 add <IP> [commentaire]"
            exit 1
        fi
        add_ip "$2" "${3:-}"
        ;;
    remove|rm|delete)
        if [ -z "$2" ]; then
            log_error "Usage: $0 remove <IP>"
            exit 1
        fi
        remove_ip "$2"
        ;;
    status)
        show_firewall_status
        ;;
    help|-h|--help)
        echo "Usage: $0 [COMMAND] [ARGS]"
        echo ""
        echo "Commandes:"
        echo "  list                    Liste toutes les IPs autorisées"
        echo "  add <IP> [comment]      Ajoute une nouvelle IP autorisée"
        echo "  remove <IP>             Supprime une IP autorisée"
        echo "  status                  Affiche l'état du firewall UFW"
        echo "  help                    Affiche cette aide"
        echo ""
        echo "Sans argument: lance le menu interactif"
        ;;
    *)
        show_menu
        ;;
esac

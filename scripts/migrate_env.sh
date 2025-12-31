#!/bin/bash

# ===================================================================
# Script de Migration .env - Ajout des Variables de Sécurité
# ===================================================================
# Ce script ajoute les nouvelles variables manquantes à votre .env
# ===================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "======================================================================="
echo -e "${BLUE}🔐 Migration du fichier .env - Ajout des variables de sécurité${NC}"
echo "======================================================================="
echo ""

# Vérifier si .env existe
if [[ ! -f ".env" ]]; then
    echo -e "${RED}❌ Fichier .env introuvable${NC}"
    echo ""
    echo "Création d'un nouveau fichier .env depuis .env.example..."

    if [[ -f ".env.example" ]]; then
        cp .env.example .env
        echo -e "${GREEN}✅ Fichier .env créé depuis .env.example${NC}"
        echo ""
        echo -e "${YELLOW}⚠️  IMPORTANT : Éditez le fichier .env et configurez vos clés API !${NC}"
        echo ""
        echo "   nano .env"
        echo ""
        exit 0
    else
        echo -e "${RED}❌ Fichier .env.example introuvable${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Fichier .env trouvé${NC}"
echo ""

# Backup du .env actuel
BACKUP_FILE=".env.backup.$(date +%Y%m%d_%H%M%S)"
cp .env "$BACKUP_FILE"
echo -e "${GREEN}✅ Backup créé : $BACKUP_FILE${NC}"
echo ""

# Fonction pour ajouter une variable si elle n'existe pas
add_env_var() {
    local var_name=$1
    local var_value=$2
    local var_description=$3

    if grep -q "^${var_name}=" .env; then
        echo -e "${BLUE}ℹ️  ${var_name} existe déjà${NC}"
    else
        echo -e "${YELLOW}➕ Ajout de ${var_name}${NC}"
        echo "" >> .env
        echo "# ${var_description}" >> .env
        echo "${var_name}=${var_value}" >> .env
    fi
}

# Vérifier et ajouter les variables manquantes
echo "Vérification des variables..."
echo ""

# Variables Grafana
add_env_var "GRAFANA_ADMIN_USER" "admin" "Username administrateur Grafana"
add_env_var "GRAFANA_ADMIN_PASSWORD" "voicebot2024" "Mot de passe administrateur Grafana"

# Variable DB_PASSWORD (au cas où elle manque)
add_env_var "DB_PASSWORD" "voicebot_secure_2024" "Mot de passe PostgreSQL"

# Variable PERSONAL_IP (optionnelle pour dashboard)
add_env_var "PERSONAL_IP" "" "IPs autorisées pour le dashboard Streamlit (optionnel)"

echo ""
echo "======================================================================="
echo -e "${GREEN}✅ Migration terminée${NC}"
echo "======================================================================="
echo ""

# Afficher les variables de sécurité
echo -e "${YELLOW}⚠️  VARIABLES DE SÉCURITÉ À VÉRIFIER :${NC}"
echo ""

echo "Base de données PostgreSQL :"
grep "^DB_PASSWORD=" .env || echo "  ❌ DB_PASSWORD manquant"
echo ""

echo "Grafana :"
grep "^GRAFANA_ADMIN_USER=" .env || echo "  ❌ GRAFANA_ADMIN_USER manquant"
grep "^GRAFANA_ADMIN_PASSWORD=" .env || echo "  ❌ GRAFANA_ADMIN_PASSWORD manquant"
echo ""

echo "======================================================================="
echo -e "${YELLOW}📝 ACTIONS RECOMMANDÉES :${NC}"
echo "======================================================================="
echo ""
echo "1. Vérifiez votre fichier .env :"
echo "   ${BLUE}nano .env${NC}"
echo ""
echo "2. Changez les mots de passe par défaut :"
echo "   - DB_PASSWORD (PostgreSQL)"
echo "   - GRAFANA_ADMIN_PASSWORD"
echo ""
echo "3. Générer un mot de passe fort :"
echo "   ${BLUE}openssl rand -base64 32${NC}"
echo ""
echo "4. Redémarrez les services pour appliquer les changements :"
echo "   ${BLUE}docker compose down${NC}"
echo "   ${BLUE}docker compose up -d${NC}"
echo ""
echo "5. Backup disponible : ${GREEN}$BACKUP_FILE${NC}"
echo ""
echo "======================================================================="
echo ""

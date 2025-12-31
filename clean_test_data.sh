#!/bin/bash
# Script pour supprimer les données de test de la base de données
# Date: 2025-12-31

set -e

echo "=========================================="
echo "Nettoyage des données de test"
echo "=========================================="

# Charger les variables d'environnement
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Vérifier que le conteneur postgres-clients est en cours d'exécution
if ! docker ps | grep -q voicebot-db-clients; then
    echo "❌ Erreur: Le conteneur voicebot-db-clients n'est pas en cours d'exécution"
    exit 1
fi

echo "⚠️  ATTENTION: Cette action va supprimer tous les clients de test"
echo "   (numéros commençant par 0699 et 0698)"
echo ""
read -p "Êtes-vous sûr ? [y/N] " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Annulé"
    exit 1
fi

echo "🗑️  Suppression des clients de test..."

# Supprimer les clients de test
docker exec -i voicebot-db-clients psql -U voicebot -d db_clients <<-EOF
    -- Supprimer les clients de test
    DELETE FROM clients WHERE phone_number LIKE '0699%' OR phone_number LIKE '0698%';

    -- Supprimer les entreprises de test (optionnel)
    DELETE FROM companies WHERE name IN (
        'TechCorp', 'DataSolutions', 'CloudInnovate', 'SecureNet', 'MediaPlus',
        'AutoConnect', 'HealthCare Services', 'EduTech', 'FinanceGroup', 'RetailExpress'
    );

    -- Afficher le résumé
    SELECT COUNT(*) as "Clients restants" FROM clients;
    SELECT COUNT(*) as "Entreprises restantes" FROM companies;
EOF

echo ""
echo "✅ Données de test supprimées avec succès !"
echo ""

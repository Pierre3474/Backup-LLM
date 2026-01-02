#!/bin/bash
# Script pour charger les données de test dans la base de données clients
# Date: 2025-12-31

set -e

echo "=========================================="
echo "Chargement des données de test"
echo "=========================================="

# Charger les variables d'environnement
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Vérifier que le conteneur postgres-clients est en cours d'exécution
if ! docker ps | grep -q voicebot-db-clients; then
    echo "❌ Erreur: Le conteneur voicebot-db-clients n'est pas en cours d'exécution"
    echo "   Lancez-le avec: docker compose up -d postgres-clients"
    exit 1
fi

echo "✓ Conteneur voicebot-db-clients détecté"

# Exécuter le script SQL
echo "📝 Insertion des données de test..."
docker exec -i voicebot-db-clients psql -U voicebot -d db_clients < insert_test_clients.sql

echo ""
echo "=========================================="
echo "✅ Données de test chargées avec succès !"
echo "=========================================="
echo ""
echo "Pour tester, appelez avec un de ces numéros:"
echo "  - 0699111001 (Thomas Lefebvre - TechCorp)"
echo "  - 0699222001 (Camille Petit - DataSolutions)"
echo "  - 0699333001 (Alexandre Durand - CloudInnovate)"
echo "  - 0698000001 (Marc Vidal - Sans entreprise)"
echo ""
echo "Total: 35 clients de test + 10 entreprises"
echo ""

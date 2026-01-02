#!/bin/bash
# Script pour ajouter Clément DUMAS de Total
# Numéro: 0781833134

set -e

echo "=========================================="
echo "Ajout de Clément DUMAS (Total)"
echo "=========================================="

# Charger les variables d'environnement
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Vérifier que le conteneur postgres-clients est en cours d'exécution
if ! docker ps | grep -q voicebot-db-clients; then
    echo " Erreur: Le conteneur voicebot-db-clients n'est pas en cours d'exécution"
    echo "   Lancez-le avec: docker compose up -d postgres-clients"
    exit 1
fi

echo "✓ Conteneur voicebot-db-clients détecté"

# Exécuter le script SQL
echo "Ajout de Clément DUMAS..."
docker exec -i voicebot-db-clients psql -U voicebot -d db_clients < add_clement_dumas.sql

echo ""
echo "=========================================="
echo "Client ajouté avec succès !"
echo "=========================================="
echo ""
echo "Numéro: 0781833134"
echo "Nom: Clément DUMAS"
echo "Entreprise: Total"
echo ""
echo "Vous pouvez maintenant appeler avec ce numéro pour tester."
echo ""

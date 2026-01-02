#!/bin/bash
# Script pour vider les bases de données clients et tickets

echo "ATTENTION : Vous allez SUPPRIMER TOUTES les données clients et tickets !"
echo "Cette opération est IRRÉVERSIBLE."
echo ""
read -p "Êtes-vous sûr ? (tapez 'OUI' en majuscules pour confirmer) : " CONFIRM

if [ "$CONFIRM" != "OUI" ]; then
    echo " Opération annulée."
    exit 1
fi

echo ""
echo "Suppression des données en cours..."

# Exécuter le script SQL dans les conteneurs PostgreSQL
echo "Nettoyage base TICKETS..."
docker exec voicebot-db-tickets psql -U voicebot -d db_tickets -c "TRUNCATE TABLE tickets RESTART IDENTITY CASCADE;"

echo "Nettoyage base CLIENTS..."
docker exec voicebot-db-clients psql -U voicebot -d db_clients -c "TRUNCATE TABLE clients RESTART IDENTITY CASCADE;"

echo ""
echo "Bases de données vidées avec succès !"
echo ""
echo "Vérification :"
docker exec voicebot-db-tickets psql -U voicebot -d db_tickets -c "SELECT COUNT(*) AS tickets_restants FROM tickets;"
docker exec voicebot-db-clients psql -U voicebot -d db_clients -c "SELECT COUNT(*) AS clients_restants FROM clients;"

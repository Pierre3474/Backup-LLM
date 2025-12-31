#!/bin/bash
#
# Script de reset automatique (sans demander de confirmation)
# Usage: ./quick_reset.sh
#

set -e

echo "🔄 Démarrage du reset automatique..."
echo ""

# Répondre 'y' pour confirmer le reset, puis 'Y' pour réinstaller
echo -e "y\nY" | ./setup.sh reset

echo ""
echo "✅ Reset et réinstallation terminés !"

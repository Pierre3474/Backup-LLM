.PHONY: help install cache run test clean convert docker-up docker-down db-init

help:
	@echo "🎙️  Voicebot SAV Wouippleul - Commandes disponibles"
	@echo ""
	@echo "  make install      - Installer les dépendances Python"
	@echo "  make cache        - Générer le cache audio 8kHz"
	@echo "  make run          - Démarrer le serveur AudioSocket"
	@echo "  make test         - Tester la configuration"
	@echo "  make convert      - Convertir les logs RAW en MP3"
	@echo "  make clean        - Nettoyer les fichiers temporaires"
	@echo ""
	@echo "  🐳 Docker:"
	@echo "  make docker-up    - Lancer la stack Docker (PostgreSQL, Prometheus, Grafana)"
	@echo "  make docker-down  - Arrêter la stack Docker"
	@echo "  make db-init      - Initialiser les bases de données"
	@echo "  make logs         - Afficher les logs Docker"
	@echo ""

install:
	@echo "📦 Installation des dépendances..."
	pip install --upgrade pip
	pip install -r requirements.txt
	@echo "✅ Installation terminée"

cache:
	@echo "🎵 Génération du cache audio..."
	python generate_cache.py
	@echo "✅ Cache généré"

run:
	@echo "🚀 Démarrage du serveur..."
	python server.py

test:
	@echo "🧪 Test de configuration..."
	@python -c "import config; print('✅ Config OK')"
	@python -c "import audio_utils; print('✅ Audio utils OK')"
	@test -f .env && echo "✅ .env existe" || echo "❌ .env manquant"
	@test -d assets/cache && echo "✅ Cache directory OK" || echo "❌ Cache directory manquant"

convert:
	@echo "🔄 Conversion RAW → MP3..."
	python convert_logs.py

convert-delete:
	@echo "🔄 Conversion RAW → MP3 (avec suppression)..."
	python convert_logs.py --delete-raw

clean:
	@echo "🧹 Nettoyage..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name "*.log" -delete 2>/dev/null || true
	@echo "✅ Nettoyage terminé"

setup: install
	@echo "🔧 Configuration initiale..."
	@test -f .env || (cp .env.example .env && echo "⚠️  Éditer le fichier .env avec vos clés API")
	@mkdir -p assets/cache
	@mkdir -p logs/calls
	@echo "✅ Setup terminé"

dev: setup cache run

asterisk-reload:
	@echo "🔄 Rechargement Asterisk..."
	asterisk -rx "dialplan reload"
	@echo "✅ Asterisk rechargé"

logs-server:
	@echo "📋 Logs serveur (Ctrl+C pour quitter)..."
	tail -f /var/log/voicebot.log 2>/dev/null || echo "Pas de logs système"

logs-asterisk:
	@echo "📋 Logs Asterisk (Ctrl+C pour quitter)..."
	tail -f /var/log/asterisk/full

# === Docker Commands ===

docker-up:
	@echo "🐳 Démarrage de la stack Docker..."
	docker-compose up -d
	@echo "✅ Stack Docker lancée"
	@echo ""
	@echo "📊 Services disponibles :"
	@echo "  - PostgreSQL (clients): localhost:5432"
	@echo "  - PostgreSQL (tickets): localhost:5433"
	@echo "  - Prometheus: http://localhost:9090"
	@echo "  - Grafana: http://localhost:3000 (admin/admin_voicebot_2024)"
	@echo "  - PgAdmin: http://localhost:5050"
	@echo "  - Métriques Voicebot: http://localhost:9091/metrics"

docker-down:
	@echo "🛑 Arrêt de la stack Docker..."
	docker-compose down
	@echo "✅ Stack Docker arrêtée"

db-init:
	@echo "⚙️ Initialisation des bases de données..."
	@echo "📝 Note: docker-compose doit être lancé (make docker-up)"
	@sleep 2
	docker-compose exec -T postgres-clients psql -U voicebot -d db_clients < init_db.sql
	docker-compose exec -T postgres-tickets psql -U voicebot -d db_tickets < init_db.sql
	@echo "✅ Bases de données initialisées"

logs:
	@echo "📋 Logs Docker (Ctrl+C pour quitter)..."
	docker-compose logs -f

docker-status:
	@echo "📊 Statut de la stack Docker :"
	docker-compose ps

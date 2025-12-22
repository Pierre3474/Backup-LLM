-- ============================================================================
-- Schéma de Base de Données pour Voicebot SAV Wouippleul
-- ============================================================================

-- ============================================================================
-- DATABASE: db_clients
-- ============================================================================

-- Créer la base de données clients (si elle n'existe pas)
-- À exécuter en tant que superuser PostgreSQL
-- CREATE DATABASE db_clients;

-- Se connecter à db_clients
\c db_clients

-- Table: clients
-- Stocke les informations clients
CREATE TABLE IF NOT EXISTS clients (
    phone_number VARCHAR(20) PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    box_model VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour recherches rapides
CREATE INDEX IF NOT EXISTS idx_clients_names ON clients(last_name, first_name);

-- Fonction pour mettre à jour updated_at automatiquement
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger pour updated_at
DROP TRIGGER IF EXISTS update_clients_updated_at ON clients;
CREATE TRIGGER update_clients_updated_at
    BEFORE UPDATE ON clients
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Données de test
INSERT INTO clients (phone_number, first_name, last_name, box_model) VALUES
    ('0612345678', 'Pierre', 'Dupont', 'Livebox 5'),
    ('0698765432', 'Marie', 'Martin', 'Freebox Revolution'),
    ('0623456789', 'Jean', 'Dubois', 'SFR Box 8'),
    ('0645678901', 'Sophie', 'Bernard', 'Bbox Ultym'),
    ('0656789012', 'Luc', 'Thomas', 'Livebox 6')
ON CONFLICT (phone_number) DO NOTHING;

COMMENT ON TABLE clients IS 'Table des clients avec leurs informations de contact et équipements';
COMMENT ON COLUMN clients.phone_number IS 'Numéro de téléphone (clé primaire)';
COMMENT ON COLUMN clients.box_model IS 'Modèle de box Internet du client';


-- ============================================================================
-- DATABASE: db_tickets
-- ============================================================================

-- Créer la base de données tickets (si elle n'existe pas)
-- CREATE DATABASE db_tickets;

-- Se connecter à db_tickets
\c db_tickets

-- Table: tickets
-- Stocke l'historique des appels et interventions
CREATE TABLE IF NOT EXISTS tickets (
    id SERIAL PRIMARY KEY,
    call_uuid VARCHAR(255) NOT NULL UNIQUE,
    phone_number VARCHAR(20) NOT NULL,
    problem_type VARCHAR(50) DEFAULT 'unknown',
    status VARCHAR(50) DEFAULT 'unknown',
    sentiment VARCHAR(50) DEFAULT 'neutral',
    summary TEXT,
    duration_seconds INTEGER DEFAULT 0,
    tag VARCHAR(100) DEFAULT 'UNKNOWN',
    severity VARCHAR(20) DEFAULT 'MEDIUM',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour recherches fréquentes
CREATE INDEX IF NOT EXISTS idx_tickets_phone ON tickets(phone_number);
CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_sentiment ON tickets(sentiment);
CREATE INDEX IF NOT EXISTS idx_tickets_problem_type ON tickets(problem_type);
CREATE INDEX IF NOT EXISTS idx_tickets_tag ON tickets(tag);
CREATE INDEX IF NOT EXISTS idx_tickets_severity ON tickets(severity);

-- Index composite pour stats du jour
CREATE INDEX IF NOT EXISTS idx_tickets_today_stats ON tickets(
    DATE(created_at),
    sentiment
);

-- Index composite pour analytics par tag
CREATE INDEX IF NOT EXISTS idx_tickets_tag_analytics ON tickets(
    tag,
    severity,
    created_at DESC
);

-- Contraintes de validation
ALTER TABLE tickets
    ADD CONSTRAINT check_problem_type
    CHECK (problem_type IN ('internet', 'mobile', 'unknown', 'other'));

ALTER TABLE tickets
    ADD CONSTRAINT check_status
    CHECK (status IN ('resolved', 'transferred', 'failed', 'unknown'));

ALTER TABLE tickets
    ADD CONSTRAINT check_sentiment
    CHECK (sentiment IN ('positive', 'neutral', 'negative'));

ALTER TABLE tickets
    ADD CONSTRAINT check_duration_positive
    CHECK (duration_seconds >= 0);

ALTER TABLE tickets
    ADD CONSTRAINT check_severity
    CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH'));

-- Données de test
INSERT INTO tickets (
    call_uuid,
    phone_number,
    problem_type,
    status,
    sentiment,
    summary,
    duration_seconds,
    tag,
    severity,
    created_at
) VALUES
    (
        'test-uuid-001',
        '0612345678',
        'internet',
        'resolved',
        'positive',
        'Client avait un problème de connexion Internet. Résolu en redémarrant la box.',
        180,
        'FIBRE_SYNCHRO',
        'MEDIUM',
        CURRENT_TIMESTAMP - INTERVAL '2 hours'
    ),
    (
        'test-uuid-002',
        '0698765432',
        'mobile',
        'resolved',
        'neutral',
        'Problème de réception mobile. Résolu en redémarrant le téléphone.',
        120,
        'MOBILE_RESEAU',
        'LOW',
        CURRENT_TIMESTAMP - INTERVAL '1 hour'
    ),
    (
        'test-uuid-003',
        '0623456789',
        'internet',
        'transferred',
        'negative',
        'Problème persistant malgré redémarrage. Transféré au technicien.',
        240,
        'CONNEXION_INSTABLE',
        'HIGH',
        CURRENT_TIMESTAMP - INTERVAL '30 minutes'
    )
ON CONFLICT (call_uuid) DO NOTHING;

-- Vue pour statistiques rapides
CREATE OR REPLACE VIEW v_daily_stats AS
SELECT
    DATE(created_at) as date,
    COUNT(*) as total_calls,
    AVG(duration_seconds)::INTEGER as avg_duration_seconds,
    COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_count,
    COUNT(CASE WHEN status = 'transferred' THEN 1 END) as transferred_count,
    COUNT(CASE WHEN sentiment = 'positive' THEN 1 END) as positive_count,
    COUNT(CASE WHEN sentiment = 'negative' THEN 1 END) as negative_count,
    COUNT(CASE WHEN problem_type = 'internet' THEN 1 END) as internet_issues,
    COUNT(CASE WHEN problem_type = 'mobile' THEN 1 END) as mobile_issues,
    COUNT(CASE WHEN severity = 'HIGH' THEN 1 END) as high_severity_count,
    COUNT(CASE WHEN severity = 'MEDIUM' THEN 1 END) as medium_severity_count,
    COUNT(CASE WHEN severity = 'LOW' THEN 1 END) as low_severity_count
FROM tickets
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Vue pour analytics par tag
CREATE OR REPLACE VIEW v_tag_analytics AS
SELECT
    tag,
    severity,
    COUNT(*) as occurrence_count,
    AVG(duration_seconds)::INTEGER as avg_duration_seconds,
    COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_count,
    COUNT(CASE WHEN status = 'transferred' THEN 1 END) as transferred_count
FROM tickets
WHERE tag != 'UNKNOWN'
GROUP BY tag, severity
ORDER BY occurrence_count DESC;

-- Vue pour les tickets récents avec détails
CREATE OR REPLACE VIEW v_recent_tickets AS
SELECT
    t.id,
    t.call_uuid,
    t.phone_number,
    t.problem_type,
    t.status,
    t.sentiment,
    t.summary,
    t.duration_seconds,
    t.tag,
    t.severity,
    t.created_at,
    -- Format lisible de la durée
    CONCAT(
        LPAD((duration_seconds / 60)::TEXT, 2, '0'), ':',
        LPAD((duration_seconds % 60)::TEXT, 2, '0')
    ) as duration_formatted
FROM tickets t
ORDER BY t.created_at DESC
LIMIT 50;

COMMENT ON TABLE tickets IS 'Historique des appels et interventions du voicebot';
COMMENT ON COLUMN tickets.call_uuid IS 'UUID unique de l''appel Asterisk';
COMMENT ON COLUMN tickets.problem_type IS 'Type de problème: internet, mobile, other, unknown';
COMMENT ON COLUMN tickets.status IS 'Statut final: resolved, transferred, failed, unknown';
COMMENT ON COLUMN tickets.sentiment IS 'Sentiment détecté: positive, neutral, negative';
COMMENT ON COLUMN tickets.summary IS 'Résumé généré par le LLM';
COMMENT ON COLUMN tickets.duration_seconds IS 'Durée de l''appel en secondes';
COMMENT ON COLUMN tickets.tag IS 'Tag de classification automatique (ex: FIBRE_SYNCHRO, MOBILE_RESEAU)';
COMMENT ON COLUMN tickets.severity IS 'Niveau de sévérité: LOW, MEDIUM, HIGH';


-- ============================================================================
-- FONCTIONS UTILITAIRES
-- ============================================================================

-- Fonction: get_today_summary
-- Retourne un résumé des appels du jour
CREATE OR REPLACE FUNCTION get_today_summary()
RETURNS TABLE(
    total_calls BIGINT,
    avg_duration_seconds INTEGER,
    resolved_count BIGINT,
    transferred_count BIGINT,
    angry_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*) as total_calls,
        COALESCE(AVG(duration_seconds)::INTEGER, 0) as avg_duration_seconds,
        COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_count,
        COUNT(CASE WHEN status = 'transferred' THEN 1 END) as transferred_count,
        COUNT(CASE WHEN sentiment = 'negative' THEN 1 END) as angry_count
    FROM tickets
    WHERE DATE(created_at) = CURRENT_DATE;
END;
$$ LANGUAGE plpgsql;

-- Fonction: cleanup_old_tickets
-- Nettoie les tickets de plus de N jours
CREATE OR REPLACE FUNCTION cleanup_old_tickets(days_to_keep INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM tickets
    WHERE created_at < CURRENT_DATE - INTERVAL '1 day' * days_to_keep;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- GRANTS & PERMISSIONS
-- ============================================================================

-- Créer un utilisateur applicatif (optionnel)
-- CREATE USER voicebot_app WITH PASSWORD 'secure_password_here';

-- Accorder les permissions nécessaires
-- GRANT CONNECT ON DATABASE db_clients TO voicebot_app;
-- GRANT CONNECT ON DATABASE db_tickets TO voicebot_app;

-- Sur db_clients
-- \c db_clients
-- GRANT SELECT ON clients TO voicebot_app;

-- Sur db_tickets
-- \c db_tickets
-- GRANT SELECT, INSERT ON tickets TO voicebot_app;
-- GRANT USAGE, SELECT ON SEQUENCE tickets_id_seq TO voicebot_app;
-- GRANT SELECT ON v_daily_stats, v_recent_tickets TO voicebot_app;


-- ============================================================================
-- FIN DU SCRIPT
-- ============================================================================

-- Afficher un résumé
\echo '============================================================'
\echo 'Schéma de base de données créé avec succès !'
\echo '============================================================'
\echo 'Base de données clients:'
\c db_clients
SELECT COUNT(*) as nombre_clients FROM clients;

\echo ''
\echo 'Base de données tickets:'
\c db_tickets
SELECT COUNT(*) as nombre_tickets FROM tickets;

\echo ''
\echo '✓ Tables créées'
\echo '✓ Index créés'
\echo '✓ Vues créées'
\echo '✓ Fonctions créées'
\echo '✓ Données de test insérées'
\echo ''
\echo 'Pour tester les stats du jour:'
\echo '  SELECT * FROM get_today_summary();'
\echo ''
\echo 'Pour voir les tickets récents:'
\echo '  SELECT * FROM v_recent_tickets LIMIT 10;'
\echo '============================================================'

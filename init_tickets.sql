-- Fichier: init_tickets.sql

-- Table: tickets
CREATE TABLE IF NOT EXISTS tickets (
    id SERIAL PRIMARY KEY,
    call_uuid VARCHAR(255) NOT NULL UNIQUE,
    phone_number VARCHAR(20) NOT NULL,
    problem_type VARCHAR(50) DEFAULT 'unknown',
    status VARCHAR(50) DEFAULT 'unknown',
    sentiment VARCHAR(50) DEFAULT 'neutral',
    summary TEXT,
    transcript TEXT,  -- Transcription complète de la conversation
    duration_seconds INTEGER DEFAULT 0,
    tag VARCHAR(100) DEFAULT 'UNKNOWN',
    severity VARCHAR(20) DEFAULT 'MEDIUM',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tickets_phone ON tickets(phone_number);
CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_today_stats ON tickets(DATE(created_at), sentiment);
CREATE INDEX IF NOT EXISTS idx_tickets_tag_analytics ON tickets(tag, severity, created_at DESC);

ALTER TABLE tickets ADD CONSTRAINT check_severity CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH'));

INSERT INTO tickets (call_uuid, phone_number, problem_type, status, sentiment, summary, duration_seconds, tag, severity, created_at) VALUES
    ('test-uuid-001', '0612345678', 'internet', 'resolved', 'positive', 'Test ticket 1', 180, 'FIBRE_SYNCHRO', 'MEDIUM', CURRENT_TIMESTAMP - INTERVAL '2 hours');

CREATE OR REPLACE VIEW v_daily_stats AS
SELECT
    DATE(created_at) as date,
    COUNT(*) as total_calls,
    AVG(duration_seconds)::INTEGER as avg_duration_seconds,
    COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_count,
    COUNT(CASE WHEN sentiment = 'negative' THEN 1 END) as negative_count
FROM tickets
GROUP BY DATE(created_at)
ORDER BY date DESC;

CREATE OR REPLACE FUNCTION get_today_summary()
RETURNS TABLE(total_calls BIGINT, avg_duration_seconds INTEGER, resolved_count BIGINT, transferred_count BIGINT, angry_count BIGINT) AS $$
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

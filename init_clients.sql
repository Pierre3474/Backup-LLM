-- Fichier: init_clients.sql

-- Table: clients
CREATE TABLE IF NOT EXISTS clients (
    phone_number VARCHAR(50) PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    box_model VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_clients_names ON clients(last_name, first_name);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_clients_updated_at ON clients;
CREATE TRIGGER update_clients_updated_at
    BEFORE UPDATE ON clients
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

INSERT INTO clients (phone_number, first_name, last_name, box_model) VALUES
    ('0612345678', 'Pierre', 'Dupont', 'Livebox 5'),
    ('0698765432', 'Marie', 'Martin', 'Freebox Revolution'),
    ('0623456789', 'Jean', 'Dubois', 'SFR Box 8'),
    ('0645678901', 'Sophie', 'Bernard', 'Bbox Ultym'),
    ('0656789012', 'Luc', 'Thomas', 'Livebox 6')
ON CONFLICT (phone_number) DO NOTHING;

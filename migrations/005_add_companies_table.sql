-- Migration 005: Ajout de la table companies
-- Objectif: Créer une table de référence des entreprises clientes
-- Date: 2025-12-31

-- Créer la table companies
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    normalized_name VARCHAR(255) NOT NULL,  -- Version normalisée pour recherche
    contact_email VARCHAR(255),
    phone_number VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ajouter un index sur le nom normalisé pour recherche rapide
CREATE INDEX idx_companies_normalized_name ON companies(normalized_name);

-- Insérer les 5 entreprises initiales
INSERT INTO companies (name, normalized_name, is_active) VALUES
    ('CARvertical', 'carvertical', TRUE),
    ('Vetodok', 'vetodok', TRUE),
    ('RCF Elec', 'rcf elec', TRUE),
    ('L''ONAsoft', 'onasoft', TRUE),
    ('SNCF', 'sncf', TRUE)
ON CONFLICT (name) DO NOTHING;

-- Ajouter une colonne company_id à la table clients (référence optionnelle)
ALTER TABLE clients ADD COLUMN IF NOT EXISTS company_id INTEGER REFERENCES companies(id) ON DELETE SET NULL;

-- Créer un index sur company_id pour jointures rapides
CREATE INDEX IF NOT EXISTS idx_clients_company_id ON clients(company_id);

-- Créer une fonction pour normaliser les noms d'entreprise
CREATE OR REPLACE FUNCTION normalize_company_name(company_name TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN LOWER(TRIM(
        REGEXP_REPLACE(
            REGEXP_REPLACE(company_name, '[''"]', '', 'g'),  -- Enlever apostrophes/guillemets
            '\s+', ' ', 'g'  -- Normaliser les espaces
        )
    ));
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Mettre à jour les noms normalisés existants
UPDATE companies SET normalized_name = normalize_company_name(name);

-- Commentaires sur la table
COMMENT ON TABLE companies IS 'Table de référence des entreprises clientes';
COMMENT ON COLUMN companies.name IS 'Nom officiel de l''entreprise';
COMMENT ON COLUMN companies.normalized_name IS 'Nom normalisé pour recherche (minuscules, sans caractères spéciaux)';
COMMENT ON COLUMN companies.is_active IS 'Entreprise active ou désactivée';
COMMENT ON COLUMN clients.company_id IS 'Référence optionnelle vers la table companies';

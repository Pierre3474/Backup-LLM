-- Migration 001: Ajout colonne transcript à la table tickets
-- Date: 2025-12-24
-- Description: Ajoute la transcription complète de la conversation dans chaque ticket

-- Ajouter la colonne transcript si elle n'existe pas
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'tickets'
        AND column_name = 'transcript'
    ) THEN
        ALTER TABLE tickets ADD COLUMN transcript TEXT;
        RAISE NOTICE 'Colonne transcript ajoutée avec succès';
    ELSE
        RAISE NOTICE 'Colonne transcript existe déjà';
    END IF;
END$$;

-- Mettre à jour les tickets existants avec un placeholder
UPDATE tickets
SET transcript = 'Transcription non disponible (ticket créé avant mise à jour)'
WHERE transcript IS NULL;

-- Ajouter un commentaire sur la colonne
COMMENT ON COLUMN tickets.transcript IS 'Transcription complète de la conversation client (ajoutée le 2025-12-24)';

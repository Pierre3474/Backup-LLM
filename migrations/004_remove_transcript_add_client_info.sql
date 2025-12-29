-- Migration 004: Suppression transcript + Ajout infos client essentielles
-- Date: 2025-12-29
-- Description: Supprime transcript (trop lourd) et ajoute email, nom, date/heure détaillée

-- 1. Supprimer la colonne transcript si elle existe
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'tickets'
        AND column_name = 'transcript'
    ) THEN
        ALTER TABLE tickets DROP COLUMN transcript;
        RAISE NOTICE 'Colonne transcript supprimée (trop volumineuse)';
    END IF;
END$$;

-- 2. Ajouter client_name si n'existe pas
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'tickets'
        AND column_name = 'client_name'
    ) THEN
        ALTER TABLE tickets ADD COLUMN client_name VARCHAR(200);
        RAISE NOTICE 'Colonne client_name ajoutée';
    END IF;
END$$;

-- 3. Ajouter client_email si n'existe pas
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'tickets'
        AND column_name = 'client_email'
    ) THEN
        ALTER TABLE tickets ADD COLUMN client_email VARCHAR(255);
        RAISE NOTICE 'Colonne client_email ajoutée';
    END IF;
END$$;

-- 4. Ajouter call_date si n'existe pas
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'tickets'
        AND column_name = 'call_date'
    ) THEN
        ALTER TABLE tickets ADD COLUMN call_date DATE DEFAULT CURRENT_DATE;
        RAISE NOTICE 'Colonne call_date ajoutée';
    END IF;
END$$;

-- 5. Ajouter call_time si n'existe pas
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'tickets'
        AND column_name = 'call_time'
    ) THEN
        ALTER TABLE tickets ADD COLUMN call_time TIME DEFAULT CURRENT_TIME;
        RAISE NOTICE 'Colonne call_time ajoutée';
    END IF;
END$$;

-- 6. Remplir call_date et call_time depuis created_at pour tickets existants
UPDATE tickets
SET
    call_date = DATE(created_at),
    call_time = created_at::TIME
WHERE call_date IS NULL OR call_time IS NULL;

-- 7. Ajouter commentaires
COMMENT ON COLUMN tickets.client_name IS 'Nom complet du client (prénom + nom)';
COMMENT ON COLUMN tickets.client_email IS 'Email du client';
COMMENT ON COLUMN tickets.call_date IS 'Date de l''appel (JJ/MM/AAAA)';
COMMENT ON COLUMN tickets.call_time IS 'Heure de l''appel (HH:MM:SS)';

RAISE NOTICE 'Migration 004 terminée : transcript supprimé, infos client ajoutées';

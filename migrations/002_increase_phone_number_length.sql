-- Migration 002: Augmentation taille champ phone_number
-- Date: 2025-12-29
-- Description: Passe phone_number de VARCHAR(20) à VARCHAR(50) pour supporter numéros internationaux

-- Augmenter la taille du champ phone_number dans la table tickets
ALTER TABLE tickets ALTER COLUMN phone_number TYPE VARCHAR(50);

-- Ajouter un commentaire
COMMENT ON COLUMN tickets.phone_number IS 'Numéro de téléphone du client (format international supporté, max 50 caractères)';

-- Log
DO $$
BEGIN
    RAISE NOTICE 'Colonne phone_number étendue à VARCHAR(50)';
END$$;

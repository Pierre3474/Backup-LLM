-- Script pour insérer des clients de test pour l'entraînement de l'IA
-- Date: 2025-12-31

-- 1. Ajouter des entreprises de test
INSERT INTO companies (name, normalized_name, is_active) VALUES
    ('TechCorp', 'techcorp', TRUE),
    ('DataSolutions', 'datasolutions', TRUE),
    ('CloudInnovate', 'cloudinnovate', TRUE),
    ('SecureNet', 'securenet', TRUE),
    ('MediaPlus', 'mediaplus', TRUE),
    ('AutoConnect', 'autoconnect', TRUE),
    ('HealthCare Services', 'healthcare services', TRUE),
    ('EduTech', 'edutech', TRUE),
    ('FinanceGroup', 'financegroup', TRUE),
    ('RetailExpress', 'retailexpress', TRUE)
ON CONFLICT (name) DO NOTHING;

-- 2. Insérer des clients de test (numéros commençant par 0699 pour identifier facilement les tests)
INSERT INTO clients (phone_number, first_name, last_name, box_model, company_id) VALUES
    -- TechCorp (company_id sera résolu dynamiquement)
    ('0699111001', 'Thomas', 'Lefebvre', 'Livebox 6', (SELECT id FROM companies WHERE name = 'TechCorp')),
    ('0699111002', 'Emma', 'Rousseau', 'Freebox Delta', (SELECT id FROM companies WHERE name = 'TechCorp')),
    ('0699111003', 'Lucas', 'Garcia', 'SFR Box 8', (SELECT id FROM companies WHERE name = 'TechCorp')),

    -- DataSolutions
    ('0699222001', 'Camille', 'Petit', 'Bbox Ultym', (SELECT id FROM companies WHERE name = 'DataSolutions')),
    ('0699222002', 'Antoine', 'Robert', 'Livebox 5', (SELECT id FROM companies WHERE name = 'DataSolutions')),
    ('0699222003', 'Julie', 'Richard', 'Freebox Revolution', (SELECT id FROM companies WHERE name = 'DataSolutions')),

    -- CloudInnovate
    ('0699333001', 'Alexandre', 'Durand', 'SFR Box 7', (SELECT id FROM companies WHERE name = 'CloudInnovate')),
    ('0699333002', 'Sarah', 'Moreau', 'Livebox 6', (SELECT id FROM companies WHERE name = 'CloudInnovate')),
    ('0699333003', 'Nicolas', 'Simon', 'Freebox Pop', (SELECT id FROM companies WHERE name = 'CloudInnovate')),

    -- SecureNet
    ('0699444001', 'Laura', 'Laurent', 'Bbox Must', (SELECT id FROM companies WHERE name = 'SecureNet')),
    ('0699444002', 'Maxime', 'Michel', 'Livebox 6', (SELECT id FROM companies WHERE name = 'SecureNet')),
    ('0699444003', 'Chloé', 'Leroy', 'Freebox Delta', (SELECT id FROM companies WHERE name = 'SecureNet')),

    -- MediaPlus
    ('0699555001', 'Hugo', 'Fontaine', 'SFR Box 8', (SELECT id FROM companies WHERE name = 'MediaPlus')),
    ('0699555002', 'Léa', 'Chevalier', 'Livebox 5', (SELECT id FROM companies WHERE name = 'MediaPlus')),
    ('0699555003', 'Arthur', 'Girard', 'Freebox Revolution', (SELECT id FROM companies WHERE name = 'MediaPlus')),

    -- AutoConnect
    ('0699666001', 'Manon', 'Bonnet', 'Bbox Ultym', (SELECT id FROM companies WHERE name = 'AutoConnect')),
    ('0699666002', 'Théo', 'Blanc', 'Livebox 6', (SELECT id FROM companies WHERE name = 'AutoConnect')),
    ('0699666003', 'Clara', 'Garnier', 'Freebox Pop', (SELECT id FROM companies WHERE name = 'AutoConnect')),

    -- HealthCare Services
    ('0699777001', 'Louis', 'Faure', 'SFR Box 7', (SELECT id FROM companies WHERE name = 'HealthCare Services')),
    ('0699777002', 'Inès', 'André', 'Livebox 6', (SELECT id FROM companies WHERE name = 'HealthCare Services')),
    ('0699777003', 'Gabriel', 'Mercier', 'Freebox Delta', (SELECT id FROM companies WHERE name = 'HealthCare Services')),

    -- EduTech
    ('0699888001', 'Océane', 'Renard', 'Bbox Must', (SELECT id FROM companies WHERE name = 'EduTech')),
    ('0699888002', 'Nathan', 'Barbier', 'Livebox 5', (SELECT id FROM companies WHERE name = 'EduTech')),
    ('0699888003', 'Mathilde', 'Arnaud', 'Freebox Revolution', (SELECT id FROM companies WHERE name = 'EduTech')),

    -- FinanceGroup
    ('0699999001', 'Raphaël', 'Gaillard', 'SFR Box 8', (SELECT id FROM companies WHERE name = 'FinanceGroup')),
    ('0699999002', 'Zoé', 'Brun', 'Livebox 6', (SELECT id FROM companies WHERE name = 'FinanceGroup')),
    ('0699999003', 'Ethan', 'Roux', 'Freebox Pop', (SELECT id FROM companies WHERE name = 'FinanceGroup')),

    -- RetailExpress
    ('0699000001', 'Lina', 'Morel', 'Bbox Ultym', (SELECT id FROM companies WHERE name = 'RetailExpress')),
    ('0699000002', 'Adam', 'Fournier', 'Livebox 6', (SELECT id FROM companies WHERE name = 'RetailExpress')),
    ('0699000003', 'Jade', 'Giraud', 'Freebox Delta', (SELECT id FROM companies WHERE name = 'RetailExpress')),

    -- Clients sans entreprise (pour tester le flow d'identification complet)
    ('0698000001', 'Marc', 'Vidal', 'Livebox 5', NULL),
    ('0698000002', 'Sophie', 'Martinez', 'Freebox Revolution', NULL),
    ('0698000003', 'David', 'Lopez', 'SFR Box 7', NULL),
    ('0698000004', 'Caroline', 'Gonzalez', 'Bbox Must', NULL),
    ('0698000005', 'Paul', 'Perez', 'Livebox 6', NULL)
ON CONFLICT (phone_number) DO NOTHING;

-- Afficher un résumé
DO $$
DECLARE
    total_companies INTEGER;
    total_clients INTEGER;
    test_clients INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_companies FROM companies;
    SELECT COUNT(*) INTO total_clients FROM clients;
    SELECT COUNT(*) INTO test_clients FROM clients WHERE phone_number LIKE '0699%' OR phone_number LIKE '0698%';

    RAISE NOTICE '==============================================';
    RAISE NOTICE 'DONNÉES DE TEST INSÉRÉES AVEC SUCCÈS';
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Total entreprises : %', total_companies;
    RAISE NOTICE 'Total clients : %', total_clients;
    RAISE NOTICE 'Clients de test (0699*/0698*) : %', test_clients;
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Les clients de test ont des numéros commençant par:';
    RAISE NOTICE '  - 0699XXXXX : Clients avec entreprise';
    RAISE NOTICE '  - 0698XXXXX : Clients sans entreprise';
    RAISE NOTICE '==============================================';
END$$;

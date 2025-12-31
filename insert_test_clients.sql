-- Script pour insérer des clients de test pour l'entraînement de l'IA
-- Date: 2025-12-31

-- 1. Ajouter des entreprises de test
INSERT INTO companies (name, normalized_name, is_active) VALUES
    ('Total', 'total', TRUE),
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
    -- Total - Client principal
    ('0781833134', 'Clément', 'DUMAS', 'ER605 OMADA', (SELECT id FROM companies WHERE name = 'Total')),

    -- TechCorp (company_id sera résolu dynamiquement)
    ('0699111001', 'Thomas', 'Lefebvre', 'UniFi Dream Machine', (SELECT id FROM companies WHERE name = 'TechCorp')),
    ('0699111002', 'Emma', 'Rousseau', 'ER605 OMADA', (SELECT id FROM companies WHERE name = 'TechCorp')),
    ('0699111003', 'Lucas', 'Garcia', 'EdgeRouter X', (SELECT id FROM companies WHERE name = 'TechCorp')),

    -- DataSolutions
    ('0699222001', 'Camille', 'Petit', 'UniFi Security Gateway', (SELECT id FROM companies WHERE name = 'DataSolutions')),
    ('0699222002', 'Antoine', 'Robert', 'ER7206 OMADA', (SELECT id FROM companies WHERE name = 'DataSolutions')),
    ('0699222003', 'Julie', 'Richard', 'UniFi Dream Router', (SELECT id FROM companies WHERE name = 'DataSolutions')),

    -- CloudInnovate
    ('0699333001', 'Alexandre', 'Durand', 'EdgeRouter 4', (SELECT id FROM companies WHERE name = 'CloudInnovate')),
    ('0699333002', 'Sarah', 'Moreau', 'ER605 OMADA', (SELECT id FROM companies WHERE name = 'CloudInnovate')),
    ('0699333003', 'Nicolas', 'Simon', 'UniFi Dream Machine Pro', (SELECT id FROM companies WHERE name = 'CloudInnovate')),

    -- SecureNet
    ('0699444001', 'Laura', 'Laurent', 'UniFi Security Gateway Pro', (SELECT id FROM companies WHERE name = 'SecureNet')),
    ('0699444002', 'Maxime', 'Michel', 'ER7206 OMADA', (SELECT id FROM companies WHERE name = 'SecureNet')),
    ('0699444003', 'Chloé', 'Leroy', 'EdgeRouter 6P', (SELECT id FROM companies WHERE name = 'SecureNet')),

    -- MediaPlus
    ('0699555001', 'Hugo', 'Fontaine', 'UniFi Dream Machine', (SELECT id FROM companies WHERE name = 'MediaPlus')),
    ('0699555002', 'Léa', 'Chevalier', 'ER605 OMADA', (SELECT id FROM companies WHERE name = 'MediaPlus')),
    ('0699555003', 'Arthur', 'Girard', 'UniFi Dream Router', (SELECT id FROM companies WHERE name = 'MediaPlus')),

    -- AutoConnect
    ('0699666001', 'Manon', 'Bonnet', 'EdgeRouter X', (SELECT id FROM companies WHERE name = 'AutoConnect')),
    ('0699666002', 'Théo', 'Blanc', 'ER7206 OMADA', (SELECT id FROM companies WHERE name = 'AutoConnect')),
    ('0699666003', 'Clara', 'Garnier', 'UniFi Security Gateway', (SELECT id FROM companies WHERE name = 'AutoConnect')),

    -- HealthCare Services
    ('0699777001', 'Louis', 'Faure', 'UniFi Dream Machine Pro', (SELECT id FROM companies WHERE name = 'HealthCare Services')),
    ('0699777002', 'Inès', 'André', 'ER605 OMADA', (SELECT id FROM companies WHERE name = 'HealthCare Services')),
    ('0699777003', 'Gabriel', 'Mercier', 'EdgeRouter 4', (SELECT id FROM companies WHERE name = 'HealthCare Services')),

    -- EduTech
    ('0699888001', 'Océane', 'Renard', 'UniFi Dream Router', (SELECT id FROM companies WHERE name = 'EduTech')),
    ('0699888002', 'Nathan', 'Barbier', 'ER7206 OMADA', (SELECT id FROM companies WHERE name = 'EduTech')),
    ('0699888003', 'Mathilde', 'Arnaud', 'UniFi Security Gateway Pro', (SELECT id FROM companies WHERE name = 'EduTech')),

    -- FinanceGroup
    ('0699999001', 'Raphaël', 'Gaillard', 'EdgeRouter 6P', (SELECT id FROM companies WHERE name = 'FinanceGroup')),
    ('0699999002', 'Zoé', 'Brun', 'ER605 OMADA', (SELECT id FROM companies WHERE name = 'FinanceGroup')),
    ('0699999003', 'Ethan', 'Roux', 'UniFi Dream Machine', (SELECT id FROM companies WHERE name = 'FinanceGroup')),

    -- RetailExpress
    ('0699000001', 'Lina', 'Morel', 'UniFi Dream Router', (SELECT id FROM companies WHERE name = 'RetailExpress')),
    ('0699000002', 'Adam', 'Fournier', 'ER7206 OMADA', (SELECT id FROM companies WHERE name = 'RetailExpress')),
    ('0699000003', 'Jade', 'Giraud', 'EdgeRouter X', (SELECT id FROM companies WHERE name = 'RetailExpress')),

    -- Clients sans entreprise (pour tester le flow d'identification complet)
    ('0698000001', 'Marc', 'Vidal', 'ER605 OMADA', NULL),
    ('0698000002', 'Sophie', 'Martinez', 'UniFi Security Gateway', NULL),
    ('0698000003', 'David', 'Lopez', 'EdgeRouter 4', NULL),
    ('0698000004', 'Caroline', 'Gonzalez', 'UniFi Dream Machine', NULL),
    ('0698000005', 'Paul', 'Perez', 'ER7206 OMADA', NULL)
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

-- Ajouter Clément DUMAS de Total
-- Numéro: 0781833134

-- 1. Ajouter l'entreprise Total si elle n'existe pas
INSERT INTO companies (name, normalized_name, is_active) VALUES
    ('Total', 'total', TRUE)
ON CONFLICT (name) DO NOTHING;

-- 2. Ajouter ou mettre à jour Clément DUMAS
INSERT INTO clients (phone_number, first_name, last_name, box_model, company_id)
VALUES (
    '0781833134',
    'Clément',
    'DUMAS',
    'ER605 OMADA',
    (SELECT id FROM companies WHERE name = 'Total')
)
ON CONFLICT (phone_number)
DO UPDATE SET
    first_name = 'Clément',
    last_name = 'DUMAS',
    box_model = 'ER605 OMADA',
    company_id = (SELECT id FROM companies WHERE name = 'Total'),
    updated_at = CURRENT_TIMESTAMP;

-- Vérifier que le client a bien été ajouté
SELECT
    c.phone_number,
    c.first_name,
    c.last_name,
    co.name as company_name,
    c.box_model
FROM clients c
LEFT JOIN companies co ON c.company_id = co.id
WHERE c.phone_number = '0781833134';

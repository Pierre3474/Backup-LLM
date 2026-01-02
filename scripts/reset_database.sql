-- Script pour effacer toutes les données clients et tickets
-- ATTENTION : Cette opération est IRRÉVERSIBLE !

-- Base de données TICKETS
\c db_tickets

-- Supprimer tous les tickets
TRUNCATE TABLE tickets RESTART IDENTITY CASCADE;

SELECT 'Base TICKETS vidée : ' || COUNT(*) || ' tickets restants' FROM tickets;

-- Base de données CLIENTS
\c db_clients

-- Supprimer tous les clients
TRUNCATE TABLE clients RESTART IDENTITY CASCADE;

SELECT 'Base CLIENTS vidée : ' || COUNT(*) || ' clients restants' FROM clients;

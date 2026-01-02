# Données de Test pour l'Entraînement de l'IA

Ce document explique comment charger et gérer les données de test pour entraîner le voicebot.

## Client Principal

**Clément DUMAS - Total**
- **Numéro** : 0781833134
- **Nom** : DUMAS
- **Prénom** : Clément
- **Entreprise** : Total
- **Équipement** : ER605 OMADA

Ce client est permanent et ne sera **PAS supprimé** lors du nettoyage des données de test.

**Note** : Tous les clients utilisent des équipements **Ubiquiti** ou **OMADA** (pas de Livebox/Freebox/SFR Box).

Pour ajouter ce client rapidement :
```bash
./add_clement_dumas.sh
```

## Fichiers

- **add_clement_dumas.sh** : Script pour ajouter Clément DUMAS (Total)
- **add_clement_dumas.sql** : Script SQL pour Clément DUMAS
- **insert_test_clients.sql** : Script SQL contenant les données de test
- **load_test_data.sh** : Script pour charger les données
- **clean_test_data.sh** : Script pour supprimer les données de test

## Charger les Données de Test

```bash
cd ~/Backup-LLM
./load_test_data.sh
```

Ce script va insérer :
- **10 entreprises de test**
- **35 clients de test** avec numéros commençant par `0699` et `0698`

## Données Insérées

### Entreprises de Test

| Nom | Clients |
|-----|---------|
| TechCorp | 3 clients |
| DataSolutions | 3 clients |
| CloudInnovate | 3 clients |
| SecureNet | 3 clients |
| MediaPlus | 3 clients |
| AutoConnect | 3 clients |
| HealthCare Services | 3 clients |
| EduTech | 3 clients |
| FinanceGroup | 3 clients |
| RetailExpress | 3 clients |

### Exemples de Clients pour Tests

#### Clients avec Entreprise (0699XXXXX)

| Téléphone | Nom | Prénom | Entreprise | Équipement |
|-----------|-----|--------|------------|------------|
| 0699111001 | Lefebvre | Thomas | TechCorp | UniFi Dream Machine |
| 0699111002 | Rousseau | Emma | TechCorp | ER605 OMADA |
| 0699222001 | Petit | Camille | DataSolutions | UniFi Security Gateway |
| 0699333001 | Durand | Alexandre | CloudInnovate | EdgeRouter 4 |
| 0699444001 | Laurent | Laura | SecureNet | UniFi Security Gateway Pro |
| 0699555001 | Fontaine | Hugo | MediaPlus | UniFi Dream Machine |

#### Clients sans Entreprise (0698XXXXX)

| Téléphone | Nom | Prénom | Équipement |
|-----------|-----|--------|------------|
| 0698000001 | Vidal | Marc | ER605 OMADA |
| 0698000002 | Martinez | Sophie | UniFi Security Gateway |
| 0698000003 | Lopez | David | EdgeRouter 4 |
| 0698000004 | Gonzalez | Caroline | UniFi Dream Machine |
| 0698000005 | Perez | Paul | ER7206 OMADA |

## Scénarios de Test

### Scénario 1 : Client Connu avec Entreprise
**Appeler avec** : `0699111001` (Thomas Lefebvre - TechCorp)

**Comportement attendu** :
- L'IA reconnaît le client par son numéro
- Salue "Bonjour, je suis Éco. Comment puis-je vous aider ?"
- Connaît déjà le prénom (Thomas), le nom (Lefebvre), et l'entreprise (TechCorp)

### Scénario 2 : Client Connu sans Entreprise
**Appeler avec** : `0698000001` (Marc Vidal)

**Comportement attendu** :
- L'IA reconnaît le client
- Connaît le prénom et nom
- Demande l'entreprise car elle n'est pas renseignée

### Scénario 3 : Nouveau Client (Non dans la Base)
**Appeler avec** : `0611111111` (numéro inconnu)

**Comportement attendu** :
- L'IA ne reconnaît pas le client
- Demande le nom complet
- Demande l'email
- Demande l'entreprise

### Scénario 4 : Client qui Rappelle avec Ticket Ouvert
1. Créer un ticket pour `0699222001` (Camille Petit)
2. Rappeler avec ce numéro

**Comportement attendu** :
- L'IA détecte le ticket ouvert
- Demande si l'appel concerne le ticket existant
- Réponse rapide (cache audio optimisé)

## Tester la Reconnaissance d'Entreprise

L'IA devrait reconnaître ces noms d'entreprise (insensible à la casse) :

- "TechCorp" / "tech corp" / "TECHCORP"
- "DataSolutions" / "data solutions" / "DATA SOLUTIONS"
- "CloudInnovate" / "cloud innovate"
- "SecureNet" / "secure net"
- "MediaPlus" / "media plus"
- "AutoConnect" / "auto connect"
- "HealthCare Services" / "healthcare services" / "health care"
- "EduTech" / "edu tech"
- "FinanceGroup" / "finance group"
- "RetailExpress" / "retail express"

## Vérifier les Données

### Lister tous les clients de test
```bash
docker exec -i voicebot-db-clients psql -U voicebot -d db_clients -c \
  "SELECT phone_number, first_name, last_name, company_id FROM clients WHERE phone_number LIKE '0699%' OR phone_number LIKE '0698%';"
```

### Lister les entreprises
```bash
docker exec -i voicebot-db-clients psql -U voicebot -d db_clients -c \
  "SELECT * FROM companies;"
```

### Compter les clients de test
```bash
docker exec -i voicebot-db-clients psql -U voicebot -d db_clients -c \
  "SELECT COUNT(*) as total_test_clients FROM clients WHERE phone_number LIKE '0699%' OR phone_number LIKE '0698%';"
```

## Nettoyer les Données de Test

Pour supprimer toutes les données de test :

```bash
./clean_test_data.sh
```

 **Attention** : Cette action est irréversible. Les données de test seront supprimées définitivement.

## Ajouter vos Propres Données

Pour ajouter vos propres clients de test, modifiez `insert_test_clients.sql` et relancez :

```bash
./load_test_data.sh
```

Les doublons seront automatiquement ignorés (ON CONFLICT DO NOTHING).

## Logs des Appels de Test

Tous les appels de test sont loggés dans :
- **Logs serveur** : `docker logs voicebot-app`
- **Logs fichiers** : `./logs/calls/YYYY-MM-DD/`

Format des logs :
```
 CLIENT: [transcription de la parole du client]
 IA: [réponse de l'IA]
 IA PARLE: [phrase audio jouée]
```

## Base de Tickets de Test

Les tickets créés pendant les tests apparaissent dans :
- **Dashboard Streamlit** : http://145.239.223.188:8501
- **Grafana** : http://145.239.223.188:3000
- **Base de données** : `db_tickets`

## Notes

- Les numéros `0699*` ont tous une entreprise associée
- Les numéros `0698*` n'ont PAS d'entreprise (pour tester le flow complet)
- Tous les clients de test ont un `box_model` différent pour plus de réalisme
- Les entreprises sont normalisées (minuscules, sans accents) pour recherche

## Troubleshooting

### "Conteneur postgres-clients n'est pas en cours d'exécution"
```bash
docker compose up -d postgres-clients
```

### "Données déjà insérées"
Normal, le script utilise `ON CONFLICT DO NOTHING`. Pour réinsérer :
```bash
./clean_test_data.sh
./load_test_data.sh
```

### "Permission denied"
```bash
chmod +x load_test_data.sh clean_test_data.sh
```

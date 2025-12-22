"""
Utilitaires de base de données PostgreSQL (asyncpg)
Gestion asynchrone des clients et tickets
"""
import asyncpg
import logging
from typing import Optional, Dict
from datetime import datetime
import config

logger = logging.getLogger(__name__)


# === Connection Pools (singleton) ===
_clients_pool: Optional[asyncpg.Pool] = None
_tickets_pool: Optional[asyncpg.Pool] = None


async def init_db_pools():
    """Initialise les pools de connexion PostgreSQL au démarrage du serveur"""
    global _clients_pool, _tickets_pool

    try:
        # Pool pour la DB clients
        _clients_pool = await asyncpg.create_pool(
            config.DB_CLIENTS_DSN,
            min_size=2,
            max_size=10,
            command_timeout=5
        )
        logger.info("✓ Database pool 'clients' initialized")

        # Pool pour la DB tickets
        _tickets_pool = await asyncpg.create_pool(
            config.DB_TICKETS_DSN,
            min_size=2,
            max_size=10,
            command_timeout=5
        )
        logger.info("✓ Database pool 'tickets' initialized")

    except Exception as e:
        logger.error(f"Failed to initialize database pools: {e}")
        raise


async def close_db_pools():
    """Ferme les pools de connexion proprement"""
    global _clients_pool, _tickets_pool

    if _clients_pool:
        await _clients_pool.close()
        logger.info("✓ Database pool 'clients' closed")

    if _tickets_pool:
        await _tickets_pool.close()
        logger.info("✓ Database pool 'tickets' closed")


async def get_client_info(phone_number: str) -> Optional[Dict]:
    """
    Récupère les informations d'un client depuis la DB

    Args:
        phone_number: Numéro de téléphone (format: "0612345678")

    Returns:
        Dict avec first_name, last_name, box_model ou None si non trouvé

    Example:
        >>> await get_client_info("0612345678")
        {'first_name': 'Pierre', 'last_name': 'Dupont', 'box_model': 'Livebox 5'}
    """
    if not _clients_pool:
        logger.error("Clients pool not initialized")
        return None

    try:
        async with _clients_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT first_name, last_name, box_model
                FROM clients
                WHERE phone_number = $1
                """,
                phone_number
            )

            if row:
                client_info = {
                    'first_name': row['first_name'],
                    'last_name': row['last_name'],
                    'box_model': row['box_model']
                }
                logger.info(f"Client found: {client_info['first_name']} {client_info['last_name']}")
                return client_info
            else:
                logger.info(f"Client not found: {phone_number}")
                return None

    except Exception as e:
        logger.error(f"Error fetching client info: {e}")
        return None


async def create_ticket(call_data: Dict) -> Optional[int]:
    """
    Crée un ticket dans la base de données

    Args:
        call_data: Dictionnaire contenant les données de l'appel
            - call_uuid (str): UUID de l'appel
            - phone_number (str): Numéro de téléphone
            - problem_type (str): "internet" ou "mobile"
            - status (str): "resolved", "transferred", "failed"
            - sentiment (str): "positive", "neutral", "negative"
            - summary (str): Résumé de l'appel
            - duration_seconds (int): Durée en secondes
            - tag (str): Tag de classification (ex: "FIBRE_SYNCHRO")
            - severity (str): Sévérité (LOW, MEDIUM, HIGH)

    Returns:
        ID du ticket créé ou None si erreur

    Example:
        >>> await create_ticket({
        ...     'call_uuid': 'a1b2c3d4',
        ...     'phone_number': '0612345678',
        ...     'problem_type': 'internet',
        ...     'status': 'resolved',
        ...     'sentiment': 'positive',
        ...     'summary': 'Problème résolu en redémarrant la box',
        ...     'duration_seconds': 120,
        ...     'tag': 'FIBRE_SYNCHRO',
        ...     'severity': 'MEDIUM'
        ... })
        42
    """
    if not _tickets_pool:
        logger.error("Tickets pool not initialized")
        return None

    try:
        async with _tickets_pool.acquire() as conn:
            ticket_id = await conn.fetchval(
                """
                INSERT INTO tickets (
                    call_uuid,
                    phone_number,
                    problem_type,
                    status,
                    sentiment,
                    summary,
                    duration_seconds,
                    tag,
                    severity,
                    created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING id
                """,
                call_data['call_uuid'],
                call_data['phone_number'],
                call_data.get('problem_type', 'unknown'),
                call_data.get('status', 'unknown'),
                call_data.get('sentiment', 'neutral'),
                call_data.get('summary', 'Aucun résumé disponible'),
                call_data.get('duration_seconds', 0),
                call_data.get('tag', 'UNKNOWN'),
                call_data.get('severity', 'MEDIUM'),
                datetime.now()
            )

            logger.info(f"✓ Ticket created: {ticket_id} (call: {call_data['call_uuid']}, tag: {call_data.get('tag', 'UNKNOWN')})")
            return ticket_id

    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        return None


async def get_today_stats() -> Dict:
    """
    Récupère les statistiques du jour

    Returns:
        Dict avec total_calls, avg_duration, angry_count
    """
    if not _tickets_pool:
        logger.error("Tickets pool not initialized")
        return {'total_calls': 0, 'avg_duration': 0, 'angry_count': 0}

    try:
        async with _tickets_pool.acquire() as conn:
            result = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total_calls,
                    COALESCE(AVG(duration_seconds), 0)::int as avg_duration,
                    COUNT(CASE WHEN sentiment = 'negative' THEN 1 END) as angry_count
                FROM tickets
                WHERE DATE(created_at) = CURRENT_DATE
                """
            )

            return {
                'total_calls': result['total_calls'],
                'avg_duration': result['avg_duration'],
                'angry_count': result['angry_count']
            }

    except Exception as e:
        logger.error(f"Error fetching today stats: {e}")
        return {'total_calls': 0, 'avg_duration': 0, 'angry_count': 0}


async def get_recent_tickets(limit: int = 10) -> list:
    """
    Récupère les derniers tickets

    Args:
        limit: Nombre de tickets à récupérer (défaut: 10)

    Returns:
        Liste de dicts avec les infos des tickets
    """
    if not _tickets_pool:
        logger.error("Tickets pool not initialized")
        return []

    try:
        async with _tickets_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    id,
                    call_uuid,
                    phone_number,
                    problem_type,
                    status,
                    sentiment,
                    summary,
                    duration_seconds,
                    tag,
                    severity,
                    created_at
                FROM tickets
                ORDER BY created_at DESC
                LIMIT $1
                """,
                limit
            )

            tickets = []
            for row in rows:
                tickets.append({
                    'id': row['id'],
                    'call_uuid': row['call_uuid'],
                    'phone_number': row['phone_number'],
                    'problem_type': row['problem_type'],
                    'status': row['status'],
                    'sentiment': row['sentiment'],
                    'summary': row['summary'],
                    'duration_seconds': row['duration_seconds'],
                    'tag': row['tag'],
                    'severity': row['severity'],
                    'created_at': row['created_at']
                })

            return tickets

    except Exception as e:
        logger.error(f"Error fetching recent tickets: {e}")
        return []


async def get_pending_tickets(phone_number: str) -> list:
    """
    Récupère les tickets non résolus pour un numéro de téléphone

    Args:
        phone_number: Numéro de téléphone (format: "0612345678")

    Returns:
        Liste de dicts avec les tickets en attente (status != 'resolved')

    Example:
        >>> await get_pending_tickets("0612345678")
        [{'id': 42, 'problem_type': 'internet', 'status': 'transferred', ...}]
    """
    if not _tickets_pool:
        logger.error("Tickets pool not initialized")
        return []

    try:
        async with _tickets_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    id,
                    call_uuid,
                    phone_number,
                    problem_type,
                    status,
                    sentiment,
                    summary,
                    duration_seconds,
                    tag,
                    severity,
                    created_at
                FROM tickets
                WHERE phone_number = $1
                  AND status != 'resolved'
                ORDER BY created_at DESC
                LIMIT 5
                """,
                phone_number
            )

            tickets = []
            for row in rows:
                tickets.append({
                    'id': row['id'],
                    'call_uuid': row['call_uuid'],
                    'phone_number': row['phone_number'],
                    'problem_type': row['problem_type'],
                    'status': row['status'],
                    'sentiment': row['sentiment'],
                    'summary': row['summary'],
                    'duration_seconds': row['duration_seconds'],
                    'tag': row['tag'],
                    'severity': row['severity'],
                    'created_at': row['created_at']
                })

            if tickets:
                logger.info(f"Found {len(tickets)} pending ticket(s) for {phone_number}")
            else:
                logger.info(f"No pending tickets for {phone_number}")

            return tickets

    except Exception as e:
        logger.error(f"Error fetching pending tickets: {e}")
        return []


async def get_client_history(phone_number: str, limit: int = 10) -> list:
    """
    Récupère l'historique complet des tickets d'un client (mémoire long terme)

    Args:
        phone_number: Numéro de téléphone (format: "0612345678")
        limit: Nombre de tickets à récupérer (défaut: 10)

    Returns:
        Liste de dicts avec summary, created_at, status, problem_type

    Example:
        >>> await get_client_history("0612345678", limit=10)
        [
            {
                'summary': 'Problème Internet résolu',
                'created_at': datetime(...),
                'status': 'resolved',
                'problem_type': 'internet'
            },
            ...
        ]
    """
    if not _tickets_pool:
        logger.error("Tickets pool not initialized")
        return []

    try:
        async with _tickets_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    summary,
                    created_at,
                    status,
                    problem_type
                FROM tickets
                WHERE phone_number = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                phone_number,
                limit
            )

            history = []
            for row in rows:
                history.append({
                    'summary': row['summary'],
                    'created_at': row['created_at'],
                    'status': row['status'],
                    'problem_type': row['problem_type']
                })

            if history:
                logger.info(f"Found {len(history)} historical ticket(s) for {phone_number}")
            else:
                logger.info(f"No history found for {phone_number}")

            return history

    except Exception as e:
        logger.error(f"Error fetching client history: {e}")
        return []


# Pour tester les fonctions (si exécuté directement)
if __name__ == "__main__":
    import asyncio

    async def test():
        await init_db_pools()

        # Test get_client_info
        client = await get_client_info("0612345678")
        print(f"Client: {client}")

        # Test create_ticket
        ticket_id = await create_ticket({
            'call_uuid': 'test-uuid-123',
            'phone_number': '0612345678',
            'problem_type': 'internet',
            'status': 'resolved',
            'sentiment': 'positive',
            'summary': 'Test ticket',
            'duration_seconds': 120
        })
        print(f"Ticket ID: {ticket_id}")

        # Test stats
        stats = await get_today_stats()
        print(f"Stats: {stats}")

        # Test recent tickets
        tickets = await get_recent_tickets(5)
        print(f"Recent tickets: {len(tickets)}")

        await close_db_pools()

    asyncio.run(test())

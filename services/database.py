"""
Service Database - Wrapper asynchrone pour db_utils
Gestion des clients, tickets, et données de conversation
"""
import logging
from typing import Optional, List, Dict, Any

# Import du module db_utils existant
import db_utils

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Service de gestion de la base de données
    Wrapper asynchrone autour de db_utils.py existant
    """

    def __init__(self, call_id: str):
        self.call_id = call_id

    async def get_client_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les informations client par numéro de téléphone

        Args:
            phone_number: Numéro de téléphone

        Returns:
            Dict avec infos client ou None si absent
        """
        try:
            client_info = await db_utils.get_client_by_phone(phone_number)
            if client_info:
                logger.info(f"[{self.call_id}] Client trouvé: {client_info.get('first_name')} "
                           f"{client_info.get('last_name')}")
            return client_info
        except Exception as e:
            logger.error(f"[{self.call_id}] Erreur récupération client: {e}")
            return None

    async def get_client_history(self, phone_number: str) -> List[Dict[str, Any]]:
        """
        Récupère l'historique des tickets d'un client

        Args:
            phone_number: Numéro de téléphone

        Returns:
            Liste de tickets (peut être vide)
        """
        try:
            history = await db_utils.get_client_history(phone_number)
            if history:
                logger.info(f"[{self.call_id}] Historique client: {len(history)} ticket(s)")
            return history or []
        except Exception as e:
            logger.error(f"[{self.call_id}] Erreur récupération historique: {e}")
            return []

    async def get_pending_tickets(self, phone_number: str) -> List[Dict[str, Any]]:
        """
        Récupère les tickets en attente pour un numéro

        Args:
            phone_number: Numéro de téléphone

        Returns:
            Liste de tickets en attente
        """
        try:
            pending = await db_utils.get_pending_tickets(phone_number)
            if pending:
                logger.info(f"[{self.call_id}] Tickets en attente: {len(pending)}")
            return pending or []
        except Exception as e:
            logger.error(f"[{self.call_id}] Erreur récupération tickets en attente: {e}")
            return []

    async def create_ticket(
        self,
        phone_number: str,
        problem_type: str,
        summary: str,
        description: Optional[str] = None
    ) -> Optional[int]:
        """
        Crée un nouveau ticket

        Args:
            phone_number: Numéro de téléphone
            problem_type: Type de problème ("internet", "mobile", etc.)
            summary: Résumé court
            description: Description détaillée (optionnel)

        Returns:
            ID du ticket créé ou None si échec
        """
        try:
            ticket_id = await db_utils.create_ticket(
                phone_number=phone_number,
                problem_type=problem_type,
                summary=summary,
                description=description
            )

            if ticket_id:
                logger.info(f"[{self.call_id}] Ticket créé: #{ticket_id}")
            return ticket_id

        except Exception as e:
            logger.error(f"[{self.call_id}] Erreur création ticket: {e}")
            return None

    async def update_ticket_status(self, ticket_id: int, status: str) -> bool:
        """
        Met à jour le statut d'un ticket

        Args:
            ticket_id: ID du ticket
            status: Nouveau statut ("pending", "in_progress", "resolved", etc.)

        Returns:
            True si succès, False sinon
        """
        try:
            success = await db_utils.update_ticket_status(ticket_id, status)
            if success:
                logger.info(f"[{self.call_id}] Ticket #{ticket_id} → {status}")
            return success
        except Exception as e:
            logger.error(f"[{self.call_id}] Erreur mise à jour ticket: {e}")
            return False

    async def is_technician_available(
        self,
        max_active: int = 5,
        window_minutes: int = 10
    ) -> bool:
        """
        Vérifie si un technicien est disponible

        Args:
            max_active: Nombre max de transferts actifs
            window_minutes: Fenêtre de temps en minutes

        Returns:
            True si technicien disponible
        """
        try:
            available = await db_utils.is_technician_available(
                max_active=max_active,
                window_minutes=window_minutes
            )

            logger.info(f"[{self.call_id}] Technicien disponible: {available}")
            return available

        except Exception as e:
            logger.error(f"[{self.call_id}] Erreur vérification technicien: {e}")
            # En cas d'erreur, considérer comme disponible (safe fallback)
            return True

    async def log_call_interaction(
        self,
        phone_number: str,
        interaction_type: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Log une interaction d'appel pour analytics

        Args:
            phone_number: Numéro de téléphone
            interaction_type: Type d'interaction (ex: "welcome", "transfer", etc.)
            details: Détails additionnels (JSON)
        """
        try:
            # À implémenter selon besoins analytics
            logger.debug(f"[{self.call_id}] Interaction logged: {interaction_type}")
        except Exception as e:
            logger.error(f"[{self.call_id}] Erreur log interaction: {e}")

"""
Modèles de données pour la conversation
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List, Any


class ConversationState(Enum):
    """États de la machine à états SAV"""
    INIT = "init"
    WELCOME = "welcome"
    TICKET_VERIFICATION = "ticket_verification"
    IDENTIFICATION = "identification"
    DIAGNOSTIC = "diagnostic"
    SOLUTION = "solution"
    VERIFICATION = "verification"
    TRANSFER = "transfer"
    GOODBYE = "goodbye"
    ERROR = "error"


class ProblemType(Enum):
    """Types de problèmes supportés"""
    INTERNET = "internet"
    MOBILE = "mobile"
    MODIFICATION = "modification"
    UNKNOWN = "unknown"


@dataclass
class ClientInfo:
    """Informations client depuis la base de données"""
    client_id: Optional[int] = None
    phone_number: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    box_model: Optional[str] = None
    mobile_count: int = 0
    created_at: Optional[datetime] = None


@dataclass
class TicketInfo:
    """Informations ticket en attente"""
    ticket_id: int
    problem_type: str
    status: str
    summary: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class ConversationContext:
    """
    Contexte complet de la conversation
    Contient toutes les informations collectées durant l'appel
    """
    # Identification de l'appel
    call_id: str
    phone_number: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.now)

    # État actuel
    current_state: ConversationState = ConversationState.INIT
    previous_state: Optional[ConversationState] = None

    # Informations client
    client_info: Optional[ClientInfo] = None
    client_history: List[TicketInfo] = field(default_factory=list)
    pending_ticket: Optional[TicketInfo] = None

    # Données collectées durant l'appel
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_company: Optional[str] = None
    problem_type: Optional[ProblemType] = None
    problem_description: Optional[str] = None
    device_count: Optional[int] = None
    device_restarted: Optional[bool] = None
    is_on_mobile: Optional[bool] = None  # Pour warning box

    # Historique de conversation (court terme)
    transcript_history: List[Dict[str, str]] = field(default_factory=list)

    # Contrôle de flux
    confirmation_attempts: int = 0
    clarification_attempts: int = 0
    negative_sentiment_count: int = 0

    # Flags
    is_returning_customer: bool = False
    has_pending_tickets: bool = False
    technician_available: bool = False

    # Métadonnées
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_user_message(self, text: str):
        """Ajoute un message utilisateur à l'historique"""
        self.transcript_history.append({
            "role": "user",
            "content": text,
            "timestamp": datetime.now().isoformat()
        })

    def add_assistant_message(self, text: str):
        """Ajoute un message assistant à l'historique"""
        self.transcript_history.append({
            "role": "assistant",
            "content": text,
            "timestamp": datetime.now().isoformat()
        })

    def get_recent_transcript(self, n: int = 5) -> List[Dict[str, str]]:
        """Retourne les N derniers messages"""
        return self.transcript_history[-n:]

    def transition_to(self, new_state: ConversationState):
        """Effectue une transition d'état"""
        self.previous_state = self.current_state
        self.current_state = new_state

    def increment_confirmation_attempts(self) -> bool:
        """
        Incrémente le compteur de tentatives de confirmation
        Retourne True si le max est atteint
        """
        self.confirmation_attempts += 1
        from config.settings import STATE_CONFIRMATION_ATTEMPTS_MAX
        return self.confirmation_attempts >= STATE_CONFIRMATION_ATTEMPTS_MAX

    def increment_clarification_attempts(self) -> bool:
        """
        Incrémente le compteur de demandes de clarification
        Retourne True si le max est atteint
        """
        self.clarification_attempts += 1
        from config.settings import STATE_CLARIFICATION_ATTEMPTS_MAX
        return self.clarification_attempts >= STATE_CLARIFICATION_ATTEMPTS_MAX

    def reset_attempts(self):
        """Réinitialise les compteurs de tentatives"""
        self.confirmation_attempts = 0
        self.clarification_attempts = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convertit le contexte en dictionnaire pour logging"""
        return {
            "call_id": self.call_id,
            "phone_number": self.phone_number,
            "current_state": self.current_state.value,
            "problem_type": self.problem_type.value if self.problem_type else None,
            "is_returning_customer": self.is_returning_customer,
            "transcript_count": len(self.transcript_history),
            "metadata": self.metadata
        }

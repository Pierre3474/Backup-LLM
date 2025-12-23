"""
Machine à états pour la conversation SAV
Gère les transitions entre états de manière déclarative
"""
import logging
from typing import Optional, Dict, Callable, Awaitable
from dataclasses import dataclass

from models.conversation import ConversationState, ConversationContext, ProblemType
from models.intents import Intent, IntentType

logger = logging.getLogger(__name__)


@dataclass
class StateTransition:
    """Définition d'une transition d'état"""
    from_state: ConversationState
    to_state: ConversationState
    condition: Optional[Callable[[ConversationContext, Intent], bool]] = None
    action: Optional[Callable[[ConversationContext, Intent], Awaitable[None]]] = None


class StateMachine:
    """
    Machine à états conversationnelle
    Gère les transitions entre états de manière propre et testable
    """

    def __init__(self, call_id: str):
        self.call_id = call_id
        self.transitions: Dict[ConversationState, list] = {}
        self._build_transitions()

    def _build_transitions(self):
        """
        Définit toutes les transitions possibles
        Structure déclarative claire
        """
        # INIT → WELCOME
        self.add_transition(
            StateTransition(
                from_state=ConversationState.INIT,
                to_state=ConversationState.WELCOME,
                condition=lambda ctx, intent: True  # Toujours
            )
        )

        # WELCOME → TICKET_VERIFICATION (si ticket en attente)
        self.add_transition(
            StateTransition(
                from_state=ConversationState.WELCOME,
                to_state=ConversationState.TICKET_VERIFICATION,
                condition=lambda ctx, intent: ctx.has_pending_tickets
            )
        )

        # WELCOME → DIAGNOSTIC (si pas de ticket)
        self.add_transition(
            StateTransition(
                from_state=ConversationState.WELCOME,
                to_state=ConversationState.DIAGNOSTIC,
                condition=lambda ctx, intent: not ctx.has_pending_tickets
            )
        )

        # TICKET_VERIFICATION → DIAGNOSTIC (si oui)
        self.add_transition(
            StateTransition(
                from_state=ConversationState.TICKET_VERIFICATION,
                to_state=ConversationState.DIAGNOSTIC,
                condition=lambda ctx, intent: intent.is_yes()
            )
        )

        # TICKET_VERIFICATION → IDENTIFICATION (si non)
        self.add_transition(
            StateTransition(
                from_state=ConversationState.TICKET_VERIFICATION,
                to_state=ConversationState.IDENTIFICATION,
                condition=lambda ctx, intent: intent.is_no()
            )
        )

        # IDENTIFICATION → DIAGNOSTIC (une fois identité collectée)
        self.add_transition(
            StateTransition(
                from_state=ConversationState.IDENTIFICATION,
                to_state=ConversationState.DIAGNOSTIC,
                condition=lambda ctx, intent: (
                    intent.intent_type == IntentType.IDENTITY_PROVIDED
                    and intent.confidence > 0.6
                )
            )
        )

        # DIAGNOSTIC → SOLUTION (une fois problème identifié)
        self.add_transition(
            StateTransition(
                from_state=ConversationState.DIAGNOSTIC,
                to_state=ConversationState.SOLUTION,
                condition=lambda ctx, intent: (
                    intent.intent_type in [IntentType.INTERNET_ISSUE, IntentType.MOBILE_ISSUE]
                    and intent.confidence > 0.6
                )
            )
        )

        # SOLUTION → VERIFICATION (après proposition solution)
        self.add_transition(
            StateTransition(
                from_state=ConversationState.SOLUTION,
                to_state=ConversationState.VERIFICATION,
                condition=lambda ctx, intent: True  # Automatique après délai
            )
        )

        # VERIFICATION → GOODBYE (si problème résolu)
        self.add_transition(
            StateTransition(
                from_state=ConversationState.VERIFICATION,
                to_state=ConversationState.GOODBYE,
                condition=lambda ctx, intent: intent.is_yes()
            )
        )

        # VERIFICATION → TRANSFER (si problème persiste)
        self.add_transition(
            StateTransition(
                from_state=ConversationState.VERIFICATION,
                to_state=ConversationState.TRANSFER,
                condition=lambda ctx, intent: intent.is_no()
            )
        )

        # ANY → TRANSFER (si escalade nécessaire)
        for state in ConversationState:
            if state not in [ConversationState.TRANSFER, ConversationState.GOODBYE, ConversationState.ERROR]:
                self.add_transition(
                    StateTransition(
                        from_state=state,
                        to_state=ConversationState.TRANSFER,
                        condition=lambda ctx, intent: ctx.metadata.get('force_transfer', False)
                    )
                )

        # ANY → ERROR (en cas de problème)
        for state in ConversationState:
            if state != ConversationState.ERROR:
                self.add_transition(
                    StateTransition(
                        from_state=state,
                        to_state=ConversationState.ERROR,
                        condition=lambda ctx, intent: ctx.metadata.get('error_occurred', False)
                    )
                )

    def add_transition(self, transition: StateTransition):
        """Ajoute une transition à la machine"""
        if transition.from_state not in self.transitions:
            self.transitions[transition.from_state] = []
        self.transitions[transition.from_state].append(transition)

    async def process_intent(
        self,
        context: ConversationContext,
        intent: Intent
    ) -> Optional[ConversationState]:
        """
        Traite une intention et détermine le prochain état

        Args:
            context: Contexte actuel de conversation
            intent: Intention analysée

        Returns:
            Nouvel état ou None si aucune transition applicable
        """
        current_state = context.current_state

        logger.info(f"[{self.call_id}] Processing intent in state {current_state.value}: "
                   f"{intent.intent_type.value} (confidence: {intent.confidence:.2f})")

        # Récupérer les transitions possibles depuis l'état actuel
        possible_transitions = self.transitions.get(current_state, [])

        # Évaluer chaque transition
        for transition in possible_transitions:
            try:
                # Vérifier la condition
                if transition.condition and transition.condition(context, intent):
                    logger.info(f"[{self.call_id}] Transition: {current_state.value} → "
                               f"{transition.to_state.value}")

                    # Exécuter l'action si présente
                    if transition.action:
                        await transition.action(context, intent)

                    # Mettre à jour le contexte
                    context.transition_to(transition.to_state)

                    return transition.to_state

            except Exception as e:
                logger.error(f"[{self.call_id}] Erreur évaluation transition: {e}", exc_info=True)

        # Aucune transition applicable
        logger.warning(f"[{self.call_id}] Aucune transition depuis {current_state.value} "
                      f"pour intent {intent.intent_type.value}")
        return None

    def get_expected_intent_types(self, state: ConversationState) -> list:
        """
        Retourne les types d'intentions attendues pour un état

        Args:
            state: État actuel

        Returns:
            Liste des IntentType attendus
        """
        expectations = {
            ConversationState.INIT: [],
            ConversationState.WELCOME: [],
            ConversationState.TICKET_VERIFICATION: [IntentType.YES, IntentType.NO],
            ConversationState.IDENTIFICATION: [IntentType.IDENTITY_PROVIDED, IntentType.EMAIL_PROVIDED],
            ConversationState.DIAGNOSTIC: [IntentType.INTERNET_ISSUE, IntentType.MOBILE_ISSUE,
                                          IntentType.MODIFICATION_REQUEST],
            ConversationState.SOLUTION: [IntentType.YES, IntentType.NO],
            ConversationState.VERIFICATION: [IntentType.YES, IntentType.NO,
                                           IntentType.PROBLEM_RESOLVED, IntentType.PROBLEM_PERSISTS],
            ConversationState.TRANSFER: [],
            ConversationState.GOODBYE: [],
            ConversationState.ERROR: []
        }

        return expectations.get(state, [])

    def should_use_short_endpointing(self, state: ConversationState) -> bool:
        """
        Détermine si on doit utiliser un endpointing court (yes/no)

        Args:
            state: État actuel

        Returns:
            True si endpointing court (500ms), False si long (1200ms)
        """
        short_endpointing_states = [
            ConversationState.TICKET_VERIFICATION,
            ConversationState.VERIFICATION,
            ConversationState.SOLUTION  # Après proposition solution
        ]

        return state in short_endpointing_states

    def get_stt_mode_for_state(self, state: ConversationState) -> str:
        """
        Retourne le mode STT approprié pour l'état

        Args:
            state: État actuel

        Returns:
            Mode STT ("open", "yes_no", "quick")
        """
        if self.should_use_short_endpointing(state):
            return "yes_no"
        else:
            return "open"

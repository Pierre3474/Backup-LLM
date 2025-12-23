#!/usr/bin/env python3
"""
Exemple d'utilisation de la nouvelle architecture modulaire
Montre comment intégrer les services dans votre code existant
"""
import asyncio
import logging
from typing import Optional

# Nouveaux imports
from models.conversation import ConversationContext, ConversationState, ClientInfo
from models.intents import IntentType
from services.stt import STTService
from services.llm import LLMService
from services.tts import TTSService
from services.database import DatabaseService
from core.intent_analyzer import IntentAnalyzer
from core.state_machine import StateMachine
from utils.audio import AudioCache
from utils.logging_config import setup_logging, get_call_logger

# Configuration
logger = setup_logging()


class SimplifiedCallHandler:
    """
    Exemple simplifié de gestionnaire d'appel utilisant les nouveaux modules
    """

    def __init__(self, call_id: str, phone_number: Optional[str] = None):
        self.call_id = call_id
        self.phone_number = phone_number

        # Logger avec call_id automatique
        self.logger = get_call_logger(__name__, call_id)

        # Contexte de conversation
        self.context = ConversationContext(
            call_id=call_id,
            phone_number=phone_number
        )

        # Services
        self.audio_cache = AudioCache()
        self.stt_service = STTService(call_id)
        self.llm_service = LLMService(call_id)
        self.tts_service = TTSService(call_id, self.audio_cache)
        self.db_service = DatabaseService(call_id)

        # Core
        self.intent_analyzer = IntentAnalyzer(call_id, self.llm_service)
        self.state_machine = StateMachine(call_id)

        # Queues
        self.audio_input_queue = asyncio.Queue()
        self.audio_output_queue = asyncio.Queue()

        self.is_active = True

    async def start(self):
        """Démarre le gestionnaire d'appel"""
        self.logger.info(f"Démarrage appel {self.call_id}")

        try:
            # 1. Charger les infos client si numéro disponible
            if self.phone_number:
                await self._load_client_info()

            # 2. Démarrer le STT
            await self._start_stt()

            # 3. Message de bienvenue
            await self._send_welcome()

            # 4. Boucle principale
            await self._conversation_loop()

        except Exception as e:
            self.logger.error(f"Erreur durant l'appel: {e}", exc_info=True)
        finally:
            await self.stop()

    async def _load_client_info(self):
        """Charge les informations client depuis la DB"""
        self.logger.info("Chargement infos client...")

        # Récupérer client
        client_data = await self.db_service.get_client_by_phone(self.phone_number)
        if client_data:
            self.context.client_info = ClientInfo(**client_data)
            self.context.is_returning_customer = True
            self.logger.info(f"Client reconnu: {client_data.get('first_name')} "
                           f"{client_data.get('last_name')}")

        # Récupérer historique
        history = await self.db_service.get_client_history(self.phone_number)
        self.context.client_history = history

        # Récupérer tickets en attente
        pending = await self.db_service.get_pending_tickets(self.phone_number)
        if pending:
            self.context.has_pending_tickets = True
            self.context.pending_ticket = pending[0]

    async def _start_stt(self):
        """Démarre le service STT"""
        # Callback pour transcriptions
        async def on_transcript(text: str, is_final: bool):
            if is_final:
                await self._process_user_input(text)

        # Déterminer le mode d'endpointing selon l'état
        stt_mode = self.state_machine.get_stt_mode_for_state(self.context.current_state)
        self.stt_service.set_endpointing_mode(stt_mode)

        # Démarrer
        await self.stt_service.start(
            input_queue=self.audio_input_queue,
            on_transcript=on_transcript
        )

    async def _send_welcome(self):
        """Envoie le message de bienvenue"""
        self.logger.info("Envoi message de bienvenue")

        # Utiliser phrase pré-cachée si client anonyme
        if not self.context.is_returning_customer:
            welcome_audio = self.tts_service.get_cached_phrase("welcome")
            if welcome_audio:
                await self._play_audio(welcome_audio)
                self.context.transition_to(ConversationState.WELCOME)
                return

        # Générer message personnalisé
        if self.context.client_info:
            welcome_text = (
                f"Bonjour {self.context.client_info.first_name}, "
                f"bienvenue au SAV Wouippleul. Comment puis-je vous aider ?"
            )
        else:
            welcome_text = "Bonjour, bienvenue au SAV Wouippleul."

        await self._say(welcome_text)
        self.context.transition_to(ConversationState.WELCOME)

    async def _conversation_loop(self):
        """Boucle principale de conversation"""
        while self.is_active:
            await asyncio.sleep(0.1)  # Boucle événementielle

    async def _process_user_input(self, user_text: str):
        """
        Traite l'input utilisateur avec analyse d'intention
        C'est ici que la MAGIE opère
        """
        self.logger.info(f"User: {user_text}")
        self.context.add_user_message(user_text)

        try:
            # 1. Analyser le sentiment (colère/frustration)
            needs_escalation = self.intent_analyzer.analyze_sentiment(user_text, self.context)
            if needs_escalation:
                self.logger.warning("Escalade immédiate requise (colère)")
                self.context.metadata['force_transfer'] = True
                await self._transfer_to_technician()
                return

            # 2. Analyser l'intention selon l'état actuel
            intent = await self._analyze_intent_for_current_state(user_text)

            self.logger.info(f"Intent: {intent.intent_type.value} "
                           f"(confidence: {intent.confidence:.2f})")

            # 3. Gérer hors-sujet
            if intent.is_off_topic:
                await self._say("Excusez-moi, je n'ai pas compris si vous vous adressiez à moi. "
                              "Pouvez-vous me décrire votre problème ?")
                return

            # 4. Demander clarification si nécessaire
            if intent.requires_clarification:
                if self.context.increment_clarification_attempts():
                    # Trop de clarifications → transfert
                    await self._transfer_to_technician()
                    return
                await self._ask_clarification()
                return

            # 5. Passer à l'état suivant via la state machine
            new_state = await self.state_machine.process_intent(self.context, intent)

            if new_state:
                # Changer mode STT si nécessaire
                stt_mode = self.state_machine.get_stt_mode_for_state(new_state)
                self.stt_service.set_endpointing_mode(stt_mode)

                # Exécuter l'action pour le nouvel état
                await self._execute_state_action(new_state, intent)

        except Exception as e:
            self.logger.error(f"Erreur traitement input: {e}", exc_info=True)
            await self._say("error")

    async def _analyze_intent_for_current_state(self, user_text: str):
        """Analyse l'intention selon l'état actuel"""
        state = self.context.current_state

        # TICKET_VERIFICATION ou VERIFICATION → yes/no
        if state in [ConversationState.TICKET_VERIFICATION, ConversationState.VERIFICATION]:
            return await self.intent_analyzer.analyze_yes_no(user_text, self.context)

        # DIAGNOSTIC → type de problème
        elif state == ConversationState.DIAGNOSTIC:
            return await self.intent_analyzer.analyze_problem_type(user_text)

        # IDENTIFICATION → identité ou email
        elif state == ConversationState.IDENTIFICATION:
            # Tenter email d'abord
            if "@" in user_text or "arobase" in user_text.lower():
                return await self.intent_analyzer.analyze_email(user_text)
            else:
                return await self.intent_analyzer.analyze_identity(user_text)

        # Fallback : génération réponse LLM
        else:
            return await self.intent_analyzer.analyze_yes_no(user_text, self.context)

    async def _execute_state_action(self, state: ConversationState, intent):
        """Exécute l'action appropriée pour un état"""
        if state == ConversationState.DIAGNOSTIC:
            await self._handle_diagnostic(intent)

        elif state == ConversationState.SOLUTION:
            await self._handle_solution(intent)

        elif state == ConversationState.VERIFICATION:
            await self._handle_verification()

        elif state == ConversationState.TRANSFER:
            await self._transfer_to_technician()

        elif state == ConversationState.GOODBYE:
            await self._say("goodbye")
            self.is_active = False

    async def _handle_diagnostic(self, intent):
        """Gère l'état diagnostic"""
        if intent.intent_type == IntentType.INTERNET_ISSUE:
            # Problème internet → warning box
            await self._say("Attention, si vous appelez depuis une ligne fixe, "
                          "le redémarrage de la box coupera la communication. "
                          "Êtes-vous sur un mobile ?")
            # Passage automatique à SOLUTION après réponse

        elif intent.intent_type == IntentType.MOBILE_ISSUE:
            await self._say("Essayez de redémarrer votre téléphone.")
            self.context.transition_to(ConversationState.VERIFICATION)

    async def _handle_solution(self, intent):
        """Gère l'état solution"""
        await asyncio.sleep(2)  # Laisser temps de manipulation
        await self._say("Avez-vous pu faire la manipulation ? "
                       "Est-ce que ça fonctionne maintenant ?")

    async def _handle_verification(self):
        """Gère l'état vérification - déjà géré par state machine"""
        pass

    async def _transfer_to_technician(self):
        """Transfère vers un technicien"""
        self.logger.info("Tentative de transfert technicien")

        # Vérifier disponibilité
        available = await self.db_service.is_technician_available()

        if available:
            await self._say("transfer")
            self.is_active = False
        else:
            await self._say("Malheureusement, aucun technicien n'est disponible. "
                          "Nous vous rappellerons dans les plus brefs délais.")
            await asyncio.sleep(5)
            await self._say("goodbye")
            self.is_active = False

    async def _ask_clarification(self):
        """Demande une clarification"""
        await self._say("Je n'ai pas bien compris. Pouvez-vous reformuler ?")

    async def _say(self, text_or_key: str):
        """
        Joue un message audio (pré-caché ou généré)
        """
        # Essayer cache statique d'abord
        cached = self.tts_service.get_cached_phrase(text_or_key)
        if cached:
            await self._play_audio(cached)
            self.context.add_assistant_message(text_or_key)
            return

        # Générer avec TTS
        self.logger.info(f"Bot: {text_or_key}")
        async for chunk in self.tts_service.generate_audio(text_or_key):
            await self.audio_output_queue.put(chunk)

        self.context.add_assistant_message(text_or_key)

    async def _play_audio(self, audio_data: bytes):
        """Envoie audio vers la queue de sortie par chunks"""
        chunk_size = 320  # 20ms @ 8kHz
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i + chunk_size]
            if len(chunk) < chunk_size:
                chunk += b'\x00' * (chunk_size - len(chunk))
            await self.audio_output_queue.put(chunk)

    async def stop(self):
        """Arrête proprement tous les services"""
        self.logger.info("Arrêt appel")
        self.is_active = False
        await self.stt_service.stop()


# === Exemple d'utilisation ===
async def main():
    """Exemple de démarrage d'un appel"""
    handler = SimplifiedCallHandler(
        call_id="test-123",
        phone_number="0612345678"
    )

    await handler.start()


if __name__ == "__main__":
    # Setup logging
    setup_logging()

    # Run
    asyncio.run(main())

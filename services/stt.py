"""
Service STT (Speech-to-Text) - Deepgram
Gestion de la connexion WebSocket avec endpointing dynamique
"""
import asyncio
import logging
from typing import Optional, Callable, Awaitable

from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions

from config.settings import (
    DEEPGRAM_API_KEY,
    DEEPGRAM_MODEL,
    DEEPGRAM_LANGUAGE,
    DEEPGRAM_ENCODING,
    DEEPGRAM_SAMPLE_RATE,
    get_stt_endpointing_mode
)

logger = logging.getLogger(__name__)


class STTService:
    """
    Service de reconnaissance vocale (Speech-to-Text) via Deepgram
    Support de l'endpointing dynamique selon le contexte
    """

    def __init__(self, call_id: str):
        self.call_id = call_id
        self.client = DeepgramClient(DEEPGRAM_API_KEY)
        self.connection = None
        self.is_active = False

        # Callbacks
        self.on_transcript_callback: Optional[Callable[[str, bool], Awaitable[None]]] = None
        self.on_speech_started_callback: Optional[Callable[[], Awaitable[None]]] = None

        # Mode d'endpointing actuel
        self.current_endpointing_mode = "open"  # "open", "yes_no", "quick"

    def set_endpointing_mode(self, mode: str):
        """
        Change le mode d'endpointing

        Args:
            mode: "open" (1200ms), "yes_no" (500ms), "quick" (500ms)
        """
        if mode in ["open", "yes_no", "quick"]:
            self.current_endpointing_mode = mode
            logger.info(f"[{self.call_id}] STT endpointing mode: {mode} "
                       f"({get_stt_endpointing_mode(mode)}ms)")
        else:
            logger.warning(f"[{self.call_id}] Mode endpointing invalide: {mode}, "
                          f"utilisation de 'open'")
            self.current_endpointing_mode = "open"

    async def start(
        self,
        input_queue: asyncio.Queue,
        on_transcript: Callable[[str, bool], Awaitable[None]],
        on_speech_started: Optional[Callable[[], Awaitable[None]]] = None
    ):
        """
        Démarre la connexion Deepgram

        Args:
            input_queue: Queue contenant l'audio brut (8kHz, mono, 16-bit)
            on_transcript: Callback appelé lors de réception d'une transcription
                          (transcript: str, is_final: bool)
            on_speech_started: Callback optionnel appelé quand l'utilisateur parle
        """
        self.on_transcript_callback = on_transcript
        self.on_speech_started_callback = on_speech_started

        try:
            # Options Deepgram avec endpointing dynamique
            endpointing_ms = get_stt_endpointing_mode(self.current_endpointing_mode)

            options = LiveOptions(
                model=DEEPGRAM_MODEL,
                language=DEEPGRAM_LANGUAGE,
                encoding=DEEPGRAM_ENCODING,
                sample_rate=DEEPGRAM_SAMPLE_RATE,
                channels=1,
                interim_results=True,
                punctuate=True,
                vad_events=True,
                endpointing=endpointing_ms
            )

            logger.info(f"[{self.call_id}] Démarrage connexion Deepgram "
                       f"(endpointing: {endpointing_ms}ms)")

            # Créer la connexion
            self.connection = self.client.listen.asyncwebsocket.v("1")

            # Handlers d'événements
            async def on_message(conn, result, **kwargs):
                try:
                    sentence = result.channel.alternatives[0].transcript

                    if sentence and self.on_transcript_callback:
                        is_final = result.is_final
                        await self.on_transcript_callback(sentence, is_final)

                except Exception as e:
                    logger.error(f"[{self.call_id}] Erreur traitement transcript: {e}")

            async def on_speech_started(conn, **kwargs):
                try:
                    if self.on_speech_started_callback:
                        await self.on_speech_started_callback()
                except Exception as e:
                    logger.error(f"[{self.call_id}] Erreur speech_started: {e}")

            async def on_error(conn, error, **kwargs):
                logger.error(f"[{self.call_id}] Deepgram error: {error}")

            # Enregistrer les handlers
            self.connection.on(LiveTranscriptionEvents.Transcript, on_message)
            self.connection.on(LiveTranscriptionEvents.SpeechStarted, on_speech_started)
            self.connection.on(LiveTranscriptionEvents.Error, on_error)

            # Démarrer la connexion
            if not await self.connection.start(options):
                logger.error(f"[{self.call_id}] Échec démarrage Deepgram")
                return False

            self.is_active = True
            logger.info(f"[{self.call_id}] Connexion Deepgram active")

            # Streamer l'audio vers Deepgram
            await self._stream_audio(input_queue)

            return True

        except Exception as e:
            logger.error(f"[{self.call_id}] Erreur STT service: {e}", exc_info=True)
            return False

    async def _stream_audio(self, input_queue: asyncio.Queue):
        """
        Stream audio depuis la queue vers Deepgram

        Args:
            input_queue: Queue contenant les chunks audio
        """
        while self.is_active:
            try:
                chunk = await asyncio.wait_for(input_queue.get(), timeout=1.0)

                if self.connection:
                    await self.connection.send(chunk)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"[{self.call_id}] Erreur streaming audio: {e}")
                break

    async def stop(self):
        """Arrête proprement la connexion Deepgram"""
        self.is_active = False

        if self.connection:
            try:
                await self.connection.finish()
                logger.info(f"[{self.call_id}] Connexion Deepgram fermée")
            except Exception as e:
                logger.error(f"[{self.call_id}] Erreur fermeture Deepgram: {e}")

        self.connection = None

    async def update_endpointing(self, mode: str):
        """
        Met à jour l'endpointing dynamiquement
        Note: Nécessite de redémarrer la connexion Deepgram

        Args:
            mode: Nouveau mode ("open", "yes_no", "quick")
        """
        if mode != self.current_endpointing_mode:
            logger.info(f"[{self.call_id}] Changement endpointing: "
                       f"{self.current_endpointing_mode} → {mode}")
            self.set_endpointing_mode(mode)
            # Note: La reconnexion sera gérée par le CallHandler si nécessaire

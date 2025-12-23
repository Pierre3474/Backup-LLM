"""
Service TTS (Text-to-Speech) - ElevenLabs
Génération audio avec streaming et cache
"""
import logging
from typing import Optional, Iterator

from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings

from config.settings import (
    ELEVENLABS_API_KEY,
    ELEVENLABS_VOICE_ID,
    ELEVENLABS_MODEL,
    ELEVENLABS_STABILITY,
    ELEVENLABS_SIMILARITY_BOOST,
    ELEVENLABS_STYLE,
    ELEVENLABS_USE_SPEAKER_BOOST
)
from utils.audio import AudioCache
from audio_utils import stream_and_convert_to_8khz

logger = logging.getLogger(__name__)


class TTSService:
    """
    Service de synthèse vocale (Text-to-Speech) via ElevenLabs
    Support du streaming et cache audio
    """

    def __init__(self, call_id: str, audio_cache: AudioCache):
        self.call_id = call_id
        self.client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        self.audio_cache = audio_cache

    async def generate_audio(
        self,
        text: str,
        use_cache: bool = True
    ) -> Iterator[bytes]:
        """
        Génère de l'audio à partir de texte avec streaming

        Args:
            text: Texte à synthétiser
            use_cache: Utiliser le cache dynamique

        Yields:
            Chunks audio 8kHz (320 bytes = 20ms)
        """
        try:
            # 1. Vérifier cache dynamique
            if use_cache:
                cached_audio = self.audio_cache.get_dynamic(text)
                if cached_audio:
                    logger.info(f"[{self.call_id}] Cache dynamique HIT")
                    # Retourner par chunks de 320 bytes
                    chunk_size = 320
                    for i in range(0, len(cached_audio), chunk_size):
                        yield cached_audio[i:i + chunk_size]
                    return

            # 2. Génération streaming ElevenLabs
            logger.info(f"[{self.call_id}] Génération TTS streaming...")

            audio_stream_iterator = self.client.generate(
                text=text,
                voice=ELEVENLABS_VOICE_ID,
                model=ELEVENLABS_MODEL,
                stream=True,
                output_format="mp3_44100_128",
                latency=1,  # Latence minimale
                voice_settings=VoiceSettings(
                    stability=ELEVENLABS_STABILITY,
                    similarity_boost=ELEVENLABS_SIMILARITY_BOOST,
                    style=ELEVENLABS_STYLE,
                    use_speaker_boost=ELEVENLABS_USE_SPEAKER_BOOST
                ) if ELEVENLABS_STABILITY else None
            )

            # 3. Conversion à la volée MP3 → PCM 8kHz
            pcm_stream = stream_and_convert_to_8khz(audio_stream_iterator)

            # 4. Stream et mise en cache simultanée
            full_audio_for_cache = bytearray()

            for chunk in pcm_stream:
                if chunk:
                    full_audio_for_cache.extend(chunk)
                    yield chunk

            # 5. Ajouter au cache dynamique
            if use_cache and len(full_audio_for_cache) > 0:
                self.audio_cache.set_dynamic(text, bytes(full_audio_for_cache))
                logger.debug(f"[{self.call_id}] Audio mis en cache ({len(full_audio_for_cache)} bytes)")

        except Exception as e:
            logger.error(f"[{self.call_id}] Erreur génération TTS: {e}", exc_info=True)
            # Retourner silence en cas d'erreur
            from audio_utils import generate_silence
            silence = generate_silence(1000)  # 1 seconde de silence
            yield silence

    def get_cached_phrase(self, phrase_key: str) -> Optional[bytes]:
        """
        Récupère une phrase pré-générée depuis le cache statique

        Args:
            phrase_key: Clé de la phrase (ex: "welcome", "goodbye")

        Returns:
            Audio 8kHz ou None si absent
        """
        audio = self.audio_cache.get(phrase_key)

        if audio:
            logger.debug(f"[{self.call_id}] Cache statique HIT: {phrase_key}")
        else:
            logger.warning(f"[{self.call_id}] Cache statique MISS: {phrase_key}")

        return audio

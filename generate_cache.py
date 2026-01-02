#!/usr/bin/env python3
"""
Script de génération du cache audio 8kHz
À lancer une seule fois pour pré-générer les phrases courantes

Usage:
    python generate_cache.py
"""
import asyncio
import sys
from pathlib import Path
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
import io
from pydub import AudioSegment
from pydub.effects import normalize
import config
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def convert_to_8khz(audio_bytes: bytes, input_format: str = "mp3") -> bytes:
    """
    Convertit l'audio OpenAI (24kHz MP3) en RAW 8kHz 16-bit Mono
    """
    try:
        # Charger l'audio
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=input_format)

        # Convertir en mono
        if audio.channels > 1:
            audio = audio.set_channels(1)

        # Resampler à 8kHz
        audio = audio.set_frame_rate(8000)

        # 16-bit
        audio = audio.set_sample_width(2)

        # Normaliser
        audio = normalize(audio, headroom=0.1)

        return audio.raw_data

    except Exception as e:
        logger.error(f"Erreur conversion: {e}")
        raise


async def generate_phrase(client: ElevenLabs, phrase_key: str, phrase_text: str) -> bool:
    """
    Génère un fichier audio 8kHz pour une phrase donnée
    """
    output_path = config.CACHE_DIR / f"{phrase_key}.raw"

    # Vérifier si le fichier existe déjà
    if output_path.exists():
        logger.info(f"✓ {phrase_key}.raw existe déjà (skip)")
        return True

    try:
        logger.info(f"Génération: '{phrase_text}' -> {phrase_key}.raw")

        # Appeler ElevenLabs TTS
        audio_generator = client.text_to_speech.convert(
            voice_id=config.ELEVENLABS_VOICE_ID,
            optimize_streaming_latency=0,
            output_format="mp3_44100_128",
            text=phrase_text,
            model_id=config.ELEVENLABS_MODEL,
            voice_settings=VoiceSettings(
                stability=config.ELEVENLABS_STABILITY,
                similarity_boost=config.ELEVENLABS_SIMILARITY_BOOST,
                style=config.ELEVENLABS_STYLE,
                use_speaker_boost=config.ELEVENLABS_USE_SPEAKER_BOOST
            )
        )

        # Récupérer les bytes audio
        audio_bytes = b""
        for chunk in audio_generator:
            if chunk:
                audio_bytes += chunk

        # Convertir en 8kHz RAW
        audio_8khz = convert_to_8khz(audio_bytes, input_format="mp3")

        # Sauvegarder
        with open(output_path, 'wb') as f:
            f.write(audio_8khz)

        file_size_kb = len(audio_8khz) / 1024
        duration_sec = len(audio_8khz) / (8000 * 2)  # sample_rate * sample_width

        logger.info(f"✓ {phrase_key}.raw créé ({file_size_kb:.1f} KB, {duration_sec:.1f}s)")
        return True

    except Exception as e:
        logger.error(f"✗ Erreur pour '{phrase_key}': {e}")
        return False


async def main():
    """
    Génère tous les fichiers audio du cache
    """
    # Vérifier les clés API
    if not config.ELEVENLABS_API_KEY:
        logger.error(" ELEVENLABS_API_KEY non définie dans .env")
        sys.exit(1)

    # Créer le répertoire cache
    config.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Initialiser le client ElevenLabs
    client = ElevenLabs(api_key=config.ELEVENLABS_API_KEY)

    logger.info("=" * 60)
    logger.info("🎵 Génération du cache audio 8kHz pour SAV Wouippleul")
    logger.info("=" * 60)
    logger.info(f"Répertoire: {config.CACHE_DIR}")
    logger.info(f"Nombre de phrases: {len(config.CACHED_PHRASES)}")
    logger.info("")

    # Générer toutes les phrases
    results = []
    for phrase_key, phrase_text in config.CACHED_PHRASES.items():
        success = await generate_phrase(client, phrase_key, phrase_text)
        results.append((phrase_key, success))

        # Pause pour éviter le rate limiting
        await asyncio.sleep(0.5)

    # Résumé
    logger.info("")
    logger.info("=" * 60)
    logger.info(" Résumé de la génération")
    logger.info("=" * 60)

    success_count = sum(1 for _, success in results if success)
    total_count = len(results)

    for phrase_key, success in results:
        status = "✓" if success else "✗"
        logger.info(f"{status} {phrase_key}")

    logger.info("")
    logger.info(f"Succès: {success_count}/{total_count}")

    if success_count == total_count:
        logger.info(" Génération du cache terminée avec succès !")
        return 0
    else:
        logger.error(" Certaines phrases n'ont pas pu être générées")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

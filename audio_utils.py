"""
Audio Utilities - Fonctions CPU-bound pour conversion audio
Ces fonctions seront exécutées dans le ProcessPoolExecutor
"""
import io
from pydub import AudioSegment
from pydub.effects import normalize
import numpy as np
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def convert_24khz_to_8khz(audio_data_24khz: bytes, input_format: str = "mp3") -> bytes:
    """
    Convertit l'audio 24kHz (OpenAI TTS) vers 8kHz (Asterisk AudioSocket)

    Args:
        audio_data_24khz: Données audio en 24kHz
        input_format: Format d'entrée ("mp3", "wav", "raw")

    Returns:
        bytes: Audio en format RAW 8kHz, 16-bit Mono (Signed Linear PCM)

    Note: Cette fonction est CPU-bound et doit être exécutée dans un ProcessPoolExecutor
    """
    try:
        # Charger l'audio depuis les bytes
        audio = AudioSegment.from_file(
            io.BytesIO(audio_data_24khz),
            format=input_format
        )

        # Convertir en mono si nécessaire
        if audio.channels > 1:
            audio = audio.set_channels(1)

        # Resampler à 8kHz
        audio = audio.set_frame_rate(8000)

        # S'assurer que c'est en 16-bit
        audio = audio.set_sample_width(2)

        # Normaliser pour éviter la saturation
        audio = normalize(audio, headroom=0.1)

        # Exporter en RAW (Signed 16-bit PCM Little Endian)
        return audio.raw_data

    except Exception as e:
        logger.error(f"Erreur conversion 24kHz->8kHz: {e}")
        # Retourner du silence en cas d'erreur (1 seconde)
        return b'\x00\x00' * 8000


def convert_raw_to_mp3(
    raw_audio_path: str,
    output_path: str,
    sample_rate: int = 8000,
    channels: int = 1,
    sample_width: int = 2,
    bitrate: str = "64k"
) -> bool:
    """
    Convertit un fichier RAW en MP3 (pour le script de batch nocturne)

    Args:
        raw_audio_path: Chemin du fichier .raw
        output_path: Chemin du fichier .mp3
        sample_rate: Fréquence d'échantillonnage (défaut: 8kHz)
        channels: Nombre de canaux (défaut: 1 - Mono)
        sample_width: Largeur d'échantillon en bytes (défaut: 2 - 16-bit)
        bitrate: Bitrate de sortie MP3

    Returns:
        bool: True si succès, False sinon
    """
    try:
        # Lire le fichier RAW
        with open(raw_audio_path, 'rb') as f:
            raw_data = f.read()

        # Créer un AudioSegment depuis les données RAW
        audio = AudioSegment(
            data=raw_data,
            sample_width=sample_width,
            frame_rate=sample_rate,
            channels=channels
        )

        # Normaliser
        audio = normalize(audio, headroom=0.1)

        # Exporter en MP3
        audio.export(
            output_path,
            format="mp3",
            bitrate=bitrate,
            parameters=["-ar", str(sample_rate), "-ac", str(channels)]
        )

        logger.info(f"Converti: {raw_audio_path} -> {output_path}")
        return True

    except Exception as e:
        logger.error(f"Erreur conversion RAW->MP3 ({raw_audio_path}): {e}")
        return False


def generate_silence(duration_ms: int, sample_rate: int = 8000) -> bytes:
    """
    Génère du silence en format RAW

    Args:
        duration_ms: Durée en millisecondes
        sample_rate: Fréquence d'échantillonnage

    Returns:
        bytes: Données audio silence
    """
    num_samples = int(duration_ms * sample_rate / 1000)
    return b'\x00\x00' * num_samples


def validate_audio_format(audio_data: bytes, expected_sample_rate: int = 8000) -> bool:
    """
    Valide que les données audio sont conformes au format attendu

    Args:
        audio_data: Données audio à valider
        expected_sample_rate: Sample rate attendu

    Returns:
        bool: True si valide
    """
    try:
        # Vérifier que la taille est paire (16-bit samples)
        if len(audio_data) % 2 != 0:
            logger.warning("Audio data length is not even (not 16-bit aligned)")
            return False

        # Vérifier qu'il y a au moins 100ms d'audio
        min_samples = expected_sample_rate // 10  # 100ms
        if len(audio_data) < min_samples * 2:  # *2 pour 16-bit
            logger.warning(f"Audio too short: {len(audio_data)} bytes")
            return False

        return True

    except Exception as e:
        logger.error(f"Error validating audio: {e}")
        return False


def mix_audio(audio_chunks: list[bytes]) -> bytes:
    """
    Mixe plusieurs chunks audio ensemble (pour concatenation)

    Args:
        audio_chunks: Liste de bytes audio en format RAW 8kHz

    Returns:
        bytes: Audio mixé
    """
    try:
        if not audio_chunks:
            return b''

        # Simple concatenation pour du RAW
        return b''.join(audio_chunks)

    except Exception as e:
        logger.error(f"Error mixing audio: {e}")
        return b''


def adjust_volume(audio_data: bytes, volume_db: float) -> bytes:
    """
    Ajuste le volume d'un audio RAW

    Args:
        audio_data: Audio en format RAW 8kHz 16-bit
        volume_db: Ajustement en décibels (positif = plus fort, négatif = plus faible)

    Returns:
        bytes: Audio avec volume ajusté
    """
    try:
        # Convertir bytes en numpy array
        audio_array = np.frombuffer(audio_data, dtype=np.int16)

        # Calculer le facteur de gain
        gain = 10 ** (volume_db / 20)

        # Appliquer le gain avec clipping
        adjusted = np.clip(audio_array * gain, -32768, 32767).astype(np.int16)

        return adjusted.tobytes()

    except Exception as e:
        logger.error(f"Error adjusting volume: {e}")
        return audio_data


# Pour tester les fonctions (si exécuté directement)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test de génération de silence
    silence = generate_silence(1000)  # 1 seconde
    print(f"Generated {len(silence)} bytes of silence")

    # Test de validation
    is_valid = validate_audio_format(silence)
    print(f"Silence is valid: {is_valid}")

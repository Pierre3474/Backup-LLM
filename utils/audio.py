"""
Utilitaires audio - Cache et gestion des fichiers audio
"""
import logging
from pathlib import Path
from typing import Dict, Optional
from collections import OrderedDict

from config.settings import CACHE_DIR, CACHED_PHRASES, DYNAMIC_CACHE_MAX_SIZE

logger = logging.getLogger(__name__)


class AudioCache:
    """
    Gestionnaire de cache audio 8kHz
    - Cache statique: Phrases pré-générées depuis CACHE_DIR
    - Cache dynamique: Solutions LLM fréquentes (LRU)
    """

    def __init__(self):
        self.static_cache: Dict[str, bytes] = {}
        self.dynamic_cache: OrderedDict[str, bytes] = OrderedDict()
        self._load_static_cache()

    def _load_static_cache(self):
        """Charge les phrases pré-générées depuis le disque"""
        loaded_count = 0
        missing_count = 0

        for phrase_key in CACHED_PHRASES.keys():
            file_path = CACHE_DIR / f"{phrase_key}.raw"

            if file_path.exists():
                with open(file_path, 'rb') as f:
                    self.static_cache[phrase_key] = f.read()
                loaded_count += 1
            else:
                logger.warning(f"Cache audio manquant: {phrase_key}.raw")
                missing_count += 1

        logger.info(f"Cache statique chargé: {loaded_count} phrases ({missing_count} manquantes)")

    def get(self, phrase_key: str) -> Optional[bytes]:
        """
        Récupère audio depuis le cache statique

        Args:
            phrase_key: Clé de la phrase (ex: "welcome", "goodbye")

        Returns:
            Données audio RAW 8kHz ou None si absent
        """
        return self.static_cache.get(phrase_key)

    def get_dynamic(self, text: str) -> Optional[bytes]:
        """
        Récupère audio depuis le cache dynamique (LRU)

        Args:
            text: Texte exact généré par TTS

        Returns:
            Données audio RAW 8kHz ou None si absent
        """
        # Clé = hash du texte pour éviter les problèmes de caractères
        cache_key = str(hash(text))

        if cache_key in self.dynamic_cache:
            # Déplacer en fin (LRU)
            self.dynamic_cache.move_to_end(cache_key)
            logger.debug(f"Cache dynamique HIT: {cache_key[:8]}...")
            return self.dynamic_cache[cache_key]

        return None

    def set_dynamic(self, text: str, audio_data: bytes):
        """
        Ajoute audio au cache dynamique (LRU)

        Args:
            text: Texte généré
            audio_data: Données audio RAW 8kHz
        """
        cache_key = str(hash(text))

        # Ajouter en fin
        self.dynamic_cache[cache_key] = audio_data

        # Supprimer le plus ancien si limite atteinte
        if len(self.dynamic_cache) > DYNAMIC_CACHE_MAX_SIZE:
            oldest_key = next(iter(self.dynamic_cache))
            del self.dynamic_cache[oldest_key]
            logger.debug(f"Cache dynamique: éviction LRU ({len(self.dynamic_cache)}/{DYNAMIC_CACHE_MAX_SIZE})")

        logger.debug(f"Cache dynamique SET: {cache_key[:8]}... ({len(audio_data)} bytes)")

    def clear_dynamic(self):
        """Vide le cache dynamique"""
        self.dynamic_cache.clear()
        logger.info("Cache dynamique vidé")

    def get_cache_stats(self) -> Dict[str, int]:
        """Retourne les statistiques du cache"""
        return {
            "static_phrases_count": len(self.static_cache),
            "dynamic_entries_count": len(self.dynamic_cache),
            "dynamic_max_size": DYNAMIC_CACHE_MAX_SIZE
        }

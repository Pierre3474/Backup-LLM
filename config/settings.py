"""
Configuration centralisée pour le Voicebot SAV - Architecture modulaire
Hérite de config.py existant et ajoute des configurations spécifiques
"""
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

# Importer la configuration existante
import config as legacy_config

# === Réexporter toutes les configurations existantes ===
# API Keys
DEEPGRAM_API_KEY = legacy_config.DEEPGRAM_API_KEY
GROQ_API_KEY = legacy_config.GROQ_API_KEY
ELEVENLABS_API_KEY = legacy_config.ELEVENLABS_API_KEY

# Audio
SAMPLE_RATE_ASTERISK = legacy_config.SAMPLE_RATE_ASTERISK
SAMPLE_RATE_ELEVENLABS = legacy_config.SAMPLE_RATE_ELEVENLABS
SAMPLE_WIDTH = legacy_config.SAMPLE_WIDTH
CHANNELS = legacy_config.CHANNELS

# Server
AUDIOSOCKET_HOST = legacy_config.AUDIOSOCKET_HOST
AUDIOSOCKET_PORT = legacy_config.AUDIOSOCKET_PORT
MAX_CONCURRENT_CALLS = legacy_config.MAX_CONCURRENT_CALLS

# Monitoring
PROMETHEUS_PORT = legacy_config.PROMETHEUS_PORT

# Performance
PROCESS_POOL_WORKERS = legacy_config.PROCESS_POOL_WORKERS

# Timeouts
SILENCE_WARNING_TIMEOUT = legacy_config.SILENCE_WARNING_TIMEOUT
SILENCE_HANGUP_TIMEOUT = legacy_config.SILENCE_HANGUP_TIMEOUT
MAX_CALL_DURATION = legacy_config.MAX_CALL_DURATION

# API Retry
API_RETRY_ATTEMPTS = legacy_config.API_RETRY_ATTEMPTS
API_TIMEOUT = legacy_config.API_TIMEOUT

# Paths
BASE_DIR = legacy_config.BASE_DIR
CACHE_DIR = legacy_config.CACHE_DIR
LOGS_DIR = legacy_config.LOGS_DIR

# Database
DB_CLIENTS_DSN = legacy_config.DB_CLIENTS_DSN
DB_TICKETS_DSN = legacy_config.DB_TICKETS_DSN

# Asterisk AMI
AMI_HOST = legacy_config.AMI_HOST
AMI_PORT = legacy_config.AMI_PORT
AMI_USERNAME = legacy_config.AMI_USERNAME
AMI_SECRET = legacy_config.AMI_SECRET

# Business Schedule
BUSINESS_SCHEDULE = legacy_config.BUSINESS_SCHEDULE

# Cached Phrases
CACHED_PHRASES = legacy_config.CACHED_PHRASES

# Deepgram
DEEPGRAM_MODEL = legacy_config.DEEPGRAM_MODEL
DEEPGRAM_LANGUAGE = legacy_config.DEEPGRAM_LANGUAGE
DEEPGRAM_ENCODING = legacy_config.DEEPGRAM_ENCODING
DEEPGRAM_SAMPLE_RATE = legacy_config.DEEPGRAM_SAMPLE_RATE

# Groq
GROQ_MODEL = legacy_config.GROQ_MODEL
GROQ_TEMPERATURE = legacy_config.GROQ_TEMPERATURE
GROQ_MAX_TOKENS = legacy_config.GROQ_MAX_TOKENS

# ElevenLabs
ELEVENLABS_VOICE_ID = legacy_config.ELEVENLABS_VOICE_ID
ELEVENLABS_MODEL = legacy_config.ELEVENLABS_MODEL
ELEVENLABS_STABILITY = legacy_config.ELEVENLABS_STABILITY
ELEVENLABS_SIMILARITY_BOOST = legacy_config.ELEVENLABS_SIMILARITY_BOOST
ELEVENLABS_STYLE = legacy_config.ELEVENLABS_STYLE
ELEVENLABS_USE_SPEAKER_BOOST = legacy_config.ELEVENLABS_USE_SPEAKER_BOOST

# Logging
LOG_LEVEL = legacy_config.LOG_LEVEL

# Technician Load
TECHNICIAN_MAX_ACTIVE_TRANSFERS = legacy_config.TECHNICIAN_MAX_ACTIVE_TRANSFERS
TECHNICIAN_LOAD_WINDOW_MIN = legacy_config.TECHNICIAN_LOAD_WINDOW_MIN

# Prompts
PROMPTS_PATH = legacy_config.PROMPTS_PATH

# === Nouvelles configurations pour l'architecture modulaire ===

# STT - Endpointing dynamique
STT_ENDPOINTING_DEFAULT = int(os.getenv("STT_ENDPOINTING_DEFAULT", "1200"))  # 1.2s pour réponses ouvertes
STT_ENDPOINTING_SHORT = int(os.getenv("STT_ENDPOINTING_SHORT", "500"))  # 0.5s pour Oui/Non
STT_ENDPOINTING_MODES = {
    "open": STT_ENDPOINTING_DEFAULT,
    "yes_no": STT_ENDPOINTING_SHORT,
    "quick": STT_ENDPOINTING_SHORT,
}

# Intent Analysis - Configuration LLM pour analyse JSON
INTENT_ANALYSIS_MODEL = os.getenv("INTENT_ANALYSIS_MODEL", GROQ_MODEL)
INTENT_ANALYSIS_TEMPERATURE = 0.1  # Très bas pour consistance JSON
INTENT_ANALYSIS_MAX_TOKENS = 100  # Court pour JSON uniquement

# State Machine - Configuration des transitions
STATE_CONFIRMATION_ATTEMPTS_MAX = 3  # Nombre max de tentatives de confirmation
STATE_CLARIFICATION_ATTEMPTS_MAX = 2  # Nombre max de demandes de clarification

# Sentiment Analysis - Détection colère/frustration
SENTIMENT_NEGATIVE_KEYWORDS = [
    "colère", "arnaque", "incompétent", "merde", "nul", "répéter",
    "enervé", "furieux", "scandale", "honte", "dégoûtant", "pourri",
    "marre", "ras le bol", "insupportable", "inadmissible", "inacceptable"
]
SENTIMENT_ANGER_THRESHOLD = int(os.getenv("SENTIMENT_ANGER_THRESHOLD", "3"))

# Cache - Configuration du cache dynamique
DYNAMIC_CACHE_MAX_SIZE = int(os.getenv("DYNAMIC_CACHE_MAX_SIZE", "50"))

# Logging - Configuration structurée
STRUCTURED_LOGGING = os.getenv("STRUCTURED_LOGGING", "true").lower() == "true"
LOG_FORMAT_JSON = os.getenv("LOG_FORMAT_JSON", "false").lower() == "true"

# Métriques
METRICS_ENABLED = os.getenv("METRICS_ENABLED", "true").lower() == "true"

def validate_config() -> List[str]:
    """
    Valide la configuration au démarrage
    Retourne une liste d'erreurs (vide si OK)
    """
    errors = []

    # Vérifier les clés API obligatoires
    if not DEEPGRAM_API_KEY:
        errors.append("DEEPGRAM_API_KEY manquante")
    if not GROQ_API_KEY:
        errors.append("GROQ_API_KEY manquante")
    if not ELEVENLABS_API_KEY:
        errors.append("ELEVENLABS_API_KEY manquante")

    # Vérifier les paths
    if not CACHE_DIR.exists():
        errors.append(f"CACHE_DIR n'existe pas: {CACHE_DIR}")
    if not LOGS_DIR.exists():
        errors.append(f"LOGS_DIR n'existe pas: {LOGS_DIR}")

    # Vérifier le fichier prompts
    prompts_file = BASE_DIR / PROMPTS_PATH
    if not prompts_file.exists():
        errors.append(f"Fichier prompts introuvable: {prompts_file}")

    return errors


def get_stt_endpointing_mode(context_type: str = "open") -> int:
    """
    Retourne l'endpointing approprié selon le contexte

    Args:
        context_type: Type de réponse attendue ("open", "yes_no", "quick")

    Returns:
        Durée d'endpointing en millisecondes
    """
    return STT_ENDPOINTING_MODES.get(context_type, STT_ENDPOINTING_DEFAULT)

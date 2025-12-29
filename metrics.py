#!/usr/bin/env python3
"""
Métriques Prometheus pour le voicebot - Orienté ROI et KPIs business
"""

from prometheus_client import Counter, Histogram, Gauge, Info, start_http_server
import logging

logger = logging.getLogger(__name__)

# ==============================================================================
# MÉTRIQUES PRINCIPALES - ROI & BUSINESS KPIs
# ==============================================================================

# Nombre total d'appels traités
calls_total = Counter(
    'voicebot_calls_total',
    'Nombre total d\'appels traités par le voicebot',
    ['status', 'problem_type']
)

# Durée des appels
call_duration_seconds = Histogram(
    'voicebot_call_duration_seconds',
    'Durée des appels en secondes',
    ['problem_type'],
    buckets=[10, 30, 60, 120, 180, 300, 600]
)

# Sentiment des clients
client_sentiment = Counter(
    'voicebot_client_sentiment_total',
    'Sentiment des clients (positif/neutre/négatif)',
    ['sentiment', 'problem_type']
)

# Tickets créés par sévérité
tickets_created = Counter(
    'voicebot_tickets_created_total',
    'Nombre de tickets créés',
    ['severity', 'tag', 'problem_type']
)

# ==============================================================================
# MÉTRIQUES COÛTS API - Pour calcul ROI
# ==============================================================================

# Coûts ElevenLabs (TTS)
elevenlabs_requests = Counter(
    'voicebot_elevenlabs_requests_total',
    'Nombre de requêtes ElevenLabs',
    ['type']  # 'cache_hit' ou 'api_call'
)

elevenlabs_characters = Counter(
    'voicebot_elevenlabs_characters_total',
    'Nombre total de caractères générés par ElevenLabs'
)

# Coûts Deepgram (STT)
deepgram_requests = Counter(
    'voicebot_deepgram_requests_total',
    'Nombre de requêtes Deepgram'
)

deepgram_audio_seconds = Counter(
    'voicebot_deepgram_audio_seconds_total',
    'Durée totale audio transcrite par Deepgram (secondes)'
)

# Coûts Groq (LLM)
groq_requests = Counter(
    'voicebot_groq_requests_total',
    'Nombre de requêtes Groq',
    ['model']
)

groq_tokens_input = Counter(
    'voicebot_groq_tokens_input_total',
    'Tokens d\'entrée Groq'
)

groq_tokens_output = Counter(
    'voicebot_groq_tokens_output_total',
    'Tokens de sortie Groq'
)

# ==============================================================================
# MÉTRIQUES PERFORMANCE
# ==============================================================================

# Temps de réponse TTS
tts_response_time = Histogram(
    'voicebot_tts_response_seconds',
    'Temps de réponse TTS (cache vs génération)',
    ['source'],  # 'cache' ou 'elevenlabs'
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
)

# Temps de transcription STT
stt_response_time = Histogram(
    'voicebot_stt_response_seconds',
    'Temps de transcription Deepgram',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Temps de génération LLM
llm_response_time = Histogram(
    'voicebot_llm_response_seconds',
    'Temps de réponse Groq LLM',
    ['task'],  # 'understanding', 'summary', 'classification'
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0]
)

# ==============================================================================
# MÉTRIQUES SYSTÈME
# ==============================================================================

# Appels simultanés actifs
active_calls = Gauge(
    'voicebot_active_calls',
    'Nombre d\'appels actifs en cours'
)

# Cache TTS - Hit rate
cache_size = Gauge(
    'voicebot_cache_phrases_loaded',
    'Nombre de phrases pré-enregistrées en cache'
)

# Erreurs système
errors_total = Counter(
    'voicebot_errors_total',
    'Nombre total d\'erreurs',
    ['error_type', 'component']
)

# ==============================================================================
# MÉTRIQUES DÉTECTION INTELLIGENTE
# ==============================================================================

# Précision de détection du problème
problem_detection_score = Histogram(
    'voicebot_problem_detection_score',
    'Score de confiance de détection du problème',
    ['detected_type'],
    buckets=[0, 1, 2, 3, 5, 10, 20]
)

# ==============================================================================
# INFO - Métadonnées du système
# ==============================================================================

voicebot_info = Info(
    'voicebot_build_info',
    'Informations sur le build du voicebot'
)

# ==============================================================================
# FONCTIONS UTILITAIRES
# ==============================================================================

def init_metrics_server(port: int = 9091):
    """
    Démarre le serveur HTTP pour exposer les métriques Prometheus

    Args:
        port: Port HTTP pour les métriques (défaut: 9091)
    """
    try:
        start_http_server(port)
        logger.info(f"✅ Serveur de métriques Prometheus démarré sur le port {port}")

        # Définir les infos du build
        voicebot_info.info({
            'version': '2.0',
            'python_version': '3.11',
            'deployment': 'docker'
        })

    except Exception as e:
        logger.error(f"❌ Erreur démarrage serveur métriques: {e}")
        raise


def track_call_completed(status: str, problem_type: str, duration: float, sentiment: str):
    """
    Enregistre la complétion d'un appel avec toutes ses métriques

    Args:
        status: Statut de l'appel (completed, failed, escalated)
        problem_type: Type de problème (internet, mobile, unknown)
        duration: Durée en secondes
        sentiment: Sentiment client (positive, neutral, negative)
    """
    calls_total.labels(status=status, problem_type=problem_type).inc()
    call_duration_seconds.labels(problem_type=problem_type).observe(duration)
    client_sentiment.labels(sentiment=sentiment, problem_type=problem_type).inc()


def track_ticket_created(severity: str, tag: str, problem_type: str):
    """
    Enregistre la création d'un ticket

    Args:
        severity: Sévérité (LOW, MEDIUM, HIGH, CRITICAL)
        tag: Tag du ticket (INTERNET_DOWN, MOBILE_ISSUE, etc.)
        problem_type: Type de problème (internet, mobile)
    """
    tickets_created.labels(severity=severity, tag=tag, problem_type=problem_type).inc()


def track_tts_cache_hit():
    """Enregistre une utilisation du cache TTS (économie API)"""
    elevenlabs_requests.labels(type='cache_hit').inc()


def track_tts_api_call(characters: int, response_time: float):
    """
    Enregistre un appel API ElevenLabs

    Args:
        characters: Nombre de caractères générés
        response_time: Temps de réponse en secondes
    """
    elevenlabs_requests.labels(type='api_call').inc()
    elevenlabs_characters.inc(characters)
    tts_response_time.labels(source='elevenlabs').observe(response_time)


def track_stt_request(audio_duration: float, response_time: float):
    """
    Enregistre une requête Deepgram STT

    Args:
        audio_duration: Durée audio transcrite (secondes)
        response_time: Temps de réponse (secondes)
    """
    deepgram_requests.inc()
    deepgram_audio_seconds.inc(audio_duration)
    stt_response_time.observe(response_time)


def track_llm_request(model: str, task: str, tokens_in: int, tokens_out: int, response_time: float):
    """
    Enregistre une requête Groq LLM

    Args:
        model: Modèle utilisé (llama-3.1-70b-versatile)
        task: Tâche (understanding, summary, classification)
        tokens_in: Tokens d'entrée
        tokens_out: Tokens de sortie
        response_time: Temps de réponse (secondes)
    """
    groq_requests.labels(model=model).inc()
    groq_tokens_input.inc(tokens_in)
    groq_tokens_output.inc(tokens_out)
    llm_response_time.labels(task=task).observe(response_time)


def track_problem_detection(detected_type: str, score: int):
    """
    Enregistre la détection intelligente du problème

    Args:
        detected_type: Type détecté (internet, mobile)
        score: Score de confiance (nombre de mots-clés matchés)
    """
    problem_detection_score.labels(detected_type=detected_type).observe(score)


def track_error(error_type: str, component: str):
    """
    Enregistre une erreur système

    Args:
        error_type: Type d'erreur (api_error, db_error, timeout, etc.)
        component: Composant concerné (elevenlabs, deepgram, groq, database)
    """
    errors_total.labels(error_type=error_type, component=component).inc()


# ==============================================================================
# CALCULS ROI (à utiliser dans les dashboards Grafana)
# ==============================================================================

"""
FORMULES POUR DASHBOARDS GRAFANA:

1. Coût par appel:
   (
     (voicebot_elevenlabs_characters_total * 0.00011) +  # ElevenLabs: $0.11/1000 chars
     (voicebot_deepgram_audio_seconds_total * 0.0043) +  # Deepgram: $0.0043/min * 60
     ((voicebot_groq_tokens_input_total + voicebot_groq_tokens_output_total) * 0.00000059)  # Groq: $0.59/1M tokens
   ) / voicebot_calls_total

2. Économies cache TTS:
   (voicebot_elevenlabs_requests_total{type="cache_hit"} /
    (voicebot_elevenlabs_requests_total{type="cache_hit"} + voicebot_elevenlabs_requests_total{type="api_call"})) * 100

3. Taux de résolution automatique:
   (voicebot_calls_total{status="completed"} / sum(voicebot_calls_total)) * 100

4. Économies vs agent humain:
   (voicebot_calls_total * 15) -  # Coût agent humain: 15€/appel
   (coût total API)

5. Temps moyen de traitement:
   avg(voicebot_call_duration_seconds)

6. Distribution problèmes:
   voicebot_calls_total{problem_type="internet"} vs voicebot_calls_total{problem_type="mobile"}

7. Satisfaction client:
   (voicebot_client_sentiment_total{sentiment="positive"} / sum(voicebot_client_sentiment_total)) * 100
"""

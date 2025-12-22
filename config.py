"""
Configuration centralisée pour le Voicebot SAV Wouippleul
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# === API Configuration ===
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# === Audio Specs ===
SAMPLE_RATE_ASTERISK = 8000  # Hz (AudioSocket format)
SAMPLE_RATE_ELEVENLABS = 24000   # Hz (ElevenLabs TTS output - mp3_44100_128 sera resamplé)
SAMPLE_WIDTH = 2              # bytes (16-bit)
CHANNELS = 1                  # Mono

# === Server Settings ===
AUDIOSOCKET_HOST = os.getenv("AUDIOSOCKET_HOST", "0.0.0.0")
AUDIOSOCKET_PORT = int(os.getenv("AUDIOSOCKET_PORT", 9090))
MAX_CONCURRENT_CALLS = 20

# === Monitoring Settings ===
PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", 9091))

# === Performance ===
PROCESS_POOL_WORKERS = 3  # Cores 1-3 pour conversions CPU-bound

# === Timeouts (secondes) ===
SILENCE_WARNING_TIMEOUT = 15  # "Allô, vous êtes toujours là ?" (15s pour laisser le temps de parler)
SILENCE_HANGUP_TIMEOUT = 30   # Raccrocher après 30s de silence total
MAX_CALL_DURATION = 600       # 10 minutes

# === API Retry ===
API_RETRY_ATTEMPTS = 2
API_TIMEOUT = 10  # secondes

# === Chemins ===
BASE_DIR = Path(__file__).parent
CACHE_DIR = BASE_DIR / "assets" / "cache"
LOGS_DIR = BASE_DIR / "logs" / "calls"

# Créer les répertoires si nécessaire
CACHE_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# === Database Settings ===
DB_CLIENTS_DSN = os.getenv("DB_CLIENTS_DSN", "postgresql://user:pass@localhost/db_clients")
DB_TICKETS_DSN = os.getenv("DB_TICKETS_DSN", "postgresql://user:pass@localhost/db_tickets")

# === Asterisk AMI Settings ===
# Configuration pour récupérer les variables de canal (CALLERID, etc.)
AMI_HOST = os.getenv("AMI_HOST", "localhost")
AMI_PORT = int(os.getenv("AMI_PORT", 5038))
AMI_USERNAME = os.getenv("AMI_USERNAME", "admin")
AMI_SECRET = os.getenv("AMI_SECRET", "admin")

# === Business Hours ===
BUSINESS_HOURS_START = 8   # 8h00
BUSINESS_HOURS_END = 19    # 19h00

# === Phrases pré-cachées (8kHz) ===
CACHED_PHRASES = {
    # --- Accueil ---
    "greet": "Bonjour et bienvenue au service support technique de chez Wipple.",
    "welcome": "Je suis Eko, votre assistant virtuel. Je vais vous aider à enregistrer votre demande afin de vous dépanner rapidement.",

    # --- Identification ---
    "ask_identity": "Pour commencer, pouvez-vous me donner votre nom, votre prénom, ainsi que le nom de votre entreprise, s'il vous plaît ?",
    "ask_firstname": "Quel est votre prénom ?",
    "ask_email": "Pouvez-vous m'épeler votre adresse email afin de créer un ticket attitré ?",
    "ask_company": "Quel est le nom de votre entreprise ?",
    "email_invalid": "L'adresse email que vous avez donnée semble incorrecte. Pouvez-vous la répéter ?",

    # --- Type de problème ---
    "ask_problem_or_modif": "Merci. S'agit-il d'une panne technique ou d'une demande de modification sur votre installation ?",
    "ask_description_technique": "D'accord. Pouvez-vous m'expliquer en détail votre problème ? Prenez votre temps, je vous écoute.",
    "ask_number_equipement": "Combien d'équipements sont concernés par ce problème ?",
    "ask_restart_devices": "Avez-vous essayé de redémarrer vos équipements ?",

    # --- Confirmations courtes ---
    "ok": "D'accord.",
    "wait": "Un instant s'il vous plaît.",
    "filler_checking": "Je vérifie cela.",
    "filler_processing": "Je traite votre demande.",

    # --- Relances ---
    "still_there_gentle": "Êtes-vous toujours là ?",
    "clarify_unclear": "Je n'ai pas bien compris. Pouvez-vous reformuler ?",
    "clarify_yes_no": "Pouvez-vous me répondre par oui ou par non ?",

    # --- Escalade technicien ---
    "transfer": "Je vous transfère à un technicien. Ne raccrochez pas.",
    "ticket_transfer_ok": "Très bien, je vous transfère immédiatement à un technicien qui va prendre la suite.",
    "offer_email_transfer": "Je peux vous envoyer un email avec les détails du problème et vous serez rappelé dans les plus brefs délais.",

    # --- Création de ticket ---
    "confirm_ticket": "Très bien. J'ai bien enregistré votre demande. Je procède maintenant à la création de votre ticket.",
    "ticket_created": "Votre ticket a été créé avec succès. Vous allez recevoir un email de confirmation avec le numéro de ticket.",

    # --- Suivi ticket existant ---
    "ticket_not_related": "D'accord, quel est votre problème aujourd'hui ?",

    # --- Horaires et fermeture ---
    "closed_hours": "Nos bureaux sont actuellement fermés. Le service technique est disponible du lundi au jeudi de neuf heures à douze heures et de quatorze heures à dix-huit heures, et le vendredi de neuf heures à douze heures et de quatorze heures à dix-sept heures.",

    # --- Fin d'appel ---
    "goodbye": "Au revoir et bonne journée. N'hésitez pas à nous rappeler si besoin.",
    "error": "Je suis désolé, une erreur technique s'est produite. Veuillez réessayer.",
}

# === Deepgram Settings ===
DEEPGRAM_MODEL = "nova-2"  # nova-2 supporte le français (nova-2-phonecall est anglais uniquement)
DEEPGRAM_LANGUAGE = "fr"
DEEPGRAM_ENCODING = "linear16"
DEEPGRAM_SAMPLE_RATE = SAMPLE_RATE_ASTERISK

# === Groq Settings ===
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_TEMPERATURE = 0.7
GROQ_MAX_TOKENS = 150

# === ElevenLabs TTS Settings ===
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "N2lVS1w4EtoT3dr4eOWO")  # Adrien - French voice
ELEVENLABS_MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2")  # Modèle multilingue v2
ELEVENLABS_STABILITY = 0.5  # Stabilité de la voix (0.0 - 1.0)
ELEVENLABS_SIMILARITY_BOOST = 0.75  # Clarté de la voix (0.0 - 1.0)
ELEVENLABS_STYLE = 0.0  # Style exagération (0.0 - 1.0)
ELEVENLABS_USE_SPEAKER_BOOST = True  # Amélioration du locuteur

# === Logging ===
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

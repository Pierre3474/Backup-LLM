"""
Configuration centralisée pour le Voicebot SAV Wouippleul
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# === Validation des variables critiques ===
def validate_env_vars():
    """Vérifie que toutes les variables d'environnement critiques sont définies"""
    missing_vars = []
    invalid_vars = []

    # Variables API obligatoires
    required_vars = {
        "DEEPGRAM_API_KEY": os.getenv("DEEPGRAM_API_KEY"),
        "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
        "ELEVENLABS_API_KEY": os.getenv("ELEVENLABS_API_KEY"),
        "ELEVENLABS_VOICE_ID": os.getenv("ELEVENLABS_VOICE_ID"),
        "AMI_SECRET": os.getenv("AMI_SECRET"),
    }

    # Vérifier les variables manquantes
    for var_name, var_value in required_vars.items():
        if not var_value:
            missing_vars.append(var_name)

    # Vérifier les DSN avec placeholders non remplacés
    db_clients_dsn = os.getenv("DB_CLIENTS_DSN", "")
    db_tickets_dsn = os.getenv("DB_TICKETS_DSN", "")

    if "user:pass" in db_clients_dsn or "CHANGEZ_CE_MOT_DE_PASSE" in db_clients_dsn:
        invalid_vars.append("DB_CLIENTS_DSN (contient des placeholders)")
    if "user:pass" in db_tickets_dsn or "CHANGEZ_CE_MOT_DE_PASSE" in db_tickets_dsn:
        invalid_vars.append("DB_TICKETS_DSN (contient des placeholders)")

    # Afficher les erreurs si nécessaire
    if missing_vars or invalid_vars:
        print("\n" + "=" * 70)
        print("ERREUR: Configuration .env incomplète ou invalide")
        print("=" * 70)

        if missing_vars:
            print("\nVariables manquantes dans .env:")
            for var in missing_vars:
                print(f"  - {var}")

        if invalid_vars:
            print("\nVariables invalides (placeholders non remplacés):")
            for var in invalid_vars:
                print(f"  - {var}")

        print("\nActions requises:")
        print("  1. Copiez .env.example vers .env")
        print("     cp .env.example .env")
        print("  2. Éditez .env et remplacez TOUTES les valeurs placeholders")
        print("  3. Relancez le voicebot")
        print("\nDocumentation: voir docs/guides/SECURITY_ENV.md")
        print("=" * 70 + "\n")

        sys.exit(1)

# Valider immédiatement au chargement du module
validate_env_vars()

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
# IMPORTANT: Définissez AMI_HOST et AMI_SECRET dans .env pour la production
AMI_HOST = os.getenv("AMI_HOST", "localhost")
AMI_PORT = int(os.getenv("AMI_PORT", 5038))
AMI_USERNAME = os.getenv("AMI_USERNAME", "admin")
AMI_SECRET = os.getenv("AMI_SECRET")  # DOIT être défini dans .env

# === Horaires d'ouverture précis ===
# Format : Jour (0=Lundi, 4=Vendredi) : [(Heure_Debut, Heure_Fin), (Heure_Debut, Heure_Fin)]
# Note: Les heures sont exclusives pour la fin (12 signifie jusqu'à 11h59)
BUSINESS_SCHEDULE = {
    0: [(9, 12), (14, 18)],  # Lundi
    1: [(9, 12), (14, 18)],  # Mardi
    2: [(9, 12), (14, 18)],  # Mercredi
    3: [(9, 12), (14, 18)],  # Jeudi
    4: [(9, 12), (14, 17)],  # Vendredi
    # 5: Samedi (Fermé - absent de la liste)
    # 6: Dimanche (Fermé)
}

# === Phrases pré-cachées (8kHz) ===
CACHED_PHRASES = {
    # --- Accueil ---
    "greet": "Bonjour, et bienvenue au service technique de chez Wipple.",
    "welcome": "Je suis Éco, votre assistant virtuel. Je vais vous aider à enregistrer votre demande, afin de vous dépanner rapidement.",

    # --- Clients qui rappellent (optimisé vitesse) ---
    "returning_client_pending_internet": "Bonjour, je suis Éco. Vous avez un ticket ouvert concernant votre connexion. Est-ce à ce sujet ?",
    "returning_client_pending_mobile": "Bonjour, je suis Éco. Vous avez un ticket ouvert concernant votre mobile. Est-ce à ce sujet ?",
    "returning_client_no_ticket": "Bonjour, je vous reconnais. Je suis Éco. Comment puis-je vous aider ?",

    # --- Identification ---
    "ask_identity": "Pour commencer, pouvez-vous me donner votre nom, votre prénom, ainsi que le nom de votre entreprise, s'il vous plaît ?",
    "ask_firstname": "Quel est votre prénom ?",
    "ask_email": "Pouvez-vous m'épeler votre adresse email, afin de créer un ticket ?",
    "ask_company": "Quel est le nom de votre entreprise ?",
    "email_invalid": "L'adresse email que vous avez donnée semble incorrecte. Pouvez-vous la répéter ?",

    # --- Type de problème ---
    "ask_problem_or_modif": "Merci. S'agit-il d'une panne technique, ou d'une demande de modification sur votre installation ?",
    "ask_description_technique": "D'accord. Pouvez-vous m'expliquer en détail votre problème ? Prenez votre temps, je vous écoute.",
    "ask_number_equipement": "Combien d'équipements sont concernés par ce problème ?",
    "ask_restart_devices": "Avez-vous essayé de redémarrer vos équipements ?",

    # --- Confirmations courtes ---
    "ok": "D'accord.",
    "wait": "Un instant, s'il vous plaît.",

    # --- Fillers pour masquer latence ---
    "filler_hum": "Hum, laissez-moi regarder.",
    "filler_ok": "Très bien, je note.",
    "filler_one_moment": "Un instant, s'il vous plaît.",
    "filler_checking": "Je vérifie cela.",
    "filler_processing": "Je traite votre demande.",
    "filler_let_me_see": "Laissez-moi voir ça.",

    # --- Relances ---
    "still_there_gentle": "Êtes-vous toujours là ?",
    "clarify_unclear": "Je n'ai pas bien compris. Pouvez-vous reformuler ?",
    "clarify_yes_no": "Pouvez-vous me répondre par oui, ou par non ?",

    # --- Escalade technicien ---
    "transfer": "Je vous transfère à un technicien. Ne raccrochez pas.",
    "ticket_transfer_ok": "Très bien. Je vous transfère immédiatement à un technicien, qui va prendre la suite.",
    "offer_email_transfer": "Je peux vous envoyer un email avec les détails du problème, et vous serez rappelé dans les plus brefs délais.",

    # --- Création de ticket ---
    "confirm_ticket": "Très bien. J'ai bien enregistré votre demande. Je procède maintenant à la création de votre ticket.",
    "ticket_created": "Votre ticket a été créé avec succès. Vous allez recevoir un email de confirmation, avec le numéro de ticket.",

    # --- Suivi ticket existant ---
    "ticket_not_related": "D'accord. Quel est votre problème aujourd'hui ?",

    # --- Horaires et fermeture ---
    "closed_hours": "Nos bureaux sont actuellement fermés. Le service technique est disponible du lundi au jeudi, de neuf heures à douze heures, et de quatorze heures à dix-huit heures. Le vendredi, de neuf heures à douze heures, et de quatorze heures à dix-sept heures.",

    # --- Fin d'appel ---
    "goodbye": "Au revoir, et bonne journée. N'hésitez pas à nous rappeler si besoin.",
    "error": "Je suis désolé, une erreur technique s'est produite. Veuillez réessayer.",
}

# === Deepgram Settings ===
DEEPGRAM_MODEL = "nova-2"  # nova-2 supporte le français (nova-2-phonecall est anglais uniquement)
DEEPGRAM_LANGUAGE = "fr"
DEEPGRAM_ENCODING = "linear16"
DEEPGRAM_SAMPLE_RATE = SAMPLE_RATE_ASTERISK

# Endpointing dynamique (temps d'attente du silence avant de finaliser)
DEEPGRAM_ENDPOINTING_SHORT = 500   # 500ms pour réponses courtes (Oui/Non, validation)
DEEPGRAM_ENDPOINTING_LONG = 1200   # 1200ms pour réponses longues (description problème)

# === Groq Settings ===
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_TEMPERATURE = 0.7
GROQ_MAX_TOKENS = 150

# === ElevenLabs TTS Settings ===
# Voice ID : DOIT être défini dans .env (validation faite au démarrage)
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
ELEVENLABS_MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_turbo_v2_5")  # Modèle Turbo v2.5 (optimisé téléphonie, -50% coût, <300ms latence)
ELEVENLABS_STABILITY = 0.5  # Stabilité de la voix (0.0 - 1.0)
ELEVENLABS_SIMILARITY_BOOST = 0.75  # Clarté de la voix (0.0 - 1.0)
ELEVENLABS_STYLE = 0.0  # Style exagération (0.0 - 1.0)
ELEVENLABS_USE_SPEAKER_BOOST = True  # Amélioration du locuteur

# === Logging ===
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Gestion de la charge techniciens
# Nombre max de transferts acceptés dans la fenêtre de temps
TECHNICIAN_MAX_ACTIVE_TRANSFERS = int(os.getenv("TECHNICIAN_MAX_ACTIVE_TRANSFERS", "5"))
# Fenêtre de temps en minutes pour calculer la charge
TECHNICIAN_LOAD_WINDOW_MIN = int(os.getenv("TECHNICIAN_LOAD_WINDOW_MIN", "10"))
# Chemin vers le fichier de prompts
PROMPTS_PATH = os.getenv("PROMPTS_PATH", "prompts.yaml")

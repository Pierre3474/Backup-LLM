#!/usr/bin/env python3
"""
Serveur AudioSocket Asyncio pour Voicebot SAV Wouippleul
Architecture haute performance avec uvloop + ProcessPoolExecutor
"""
import os
import re
import asyncio
import uvloop
import logging
import signal
import sys
import os
import struct
import time
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
from concurrent.futures import ProcessPoolExecutor
from collections import deque
from enum import Enum
import yaml

# AI APIs
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from groq import Groq
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings

# Asterisk AMI
from panoramisk import Manager as AMIManager

# Local imports
import config
from audio_utils import generate_silence, stream_and_convert_to_8khz
import db_utils

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# === Utils ===
def clean_email_text(text: str) -> str:
    """Nettoie une transcription d'email (at->@, dot->., etc.)"""
    if not text:
        return ""

    # Dictionnaire de remplacements phonétiques
    replacements = {
        r'\s+arobase\s+': '@',
        r'\s+at\s+': '@',
        r'\s+chez\s+': '@',
        r'\s+point\s+': '.',
        r'\s+dot\s+': '.',
        r'\s+tiret\s+': '-',
        r'\s+underscore\s+': '_',
        r'\s+': ''  # Supprimer tous les espaces restants
    }
    cleaned = text.lower()
    for pattern, repl in replacements.items():
        cleaned = re.sub(pattern, repl, cleaned)

    # Extraction regex stricte pour valider
    match = re.search(r'[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}', cleaned)
    return match.group(0) if match else text


# === États de la conversation ===
class ConversationState(Enum):
    """États de la machine à états SAV Wouippleul"""
    INIT = "init"
    WELCOME = "welcome"
    TICKET_VERIFICATION = "ticket_verification"
    IDENTIFICATION = "identification"
    DIAGNOSTIC = "diagnostic"
    SOLUTION = "solution"
    VERIFICATION = "verification"
    TRANSFER = "transfer"
    GOODBYE = "goodbye"
    ERROR = "error"


# === Cache Audio Manager ===
class AudioCache:
    """
    Gestionnaire de cache audio 8kHz pré-généré + cache dynamique pour solutions fréquentes
    """

    def __init__(self):
        self.cache: Dict[str, bytes] = {}  # Cache statique (phrases pré-générées)
        self.dynamic_cache: Dict[str, bytes] = {}  # Cache dynamique (solutions LLM fréquentes)
        self.dynamic_cache_max_size = 50  # Limite du cache dynamique
        self._load_cache()

    def _load_cache(self):
        """Charge tous les fichiers .raw du répertoire cache"""
        if not config.CACHE_DIR.exists():
            logger.warning(f"Cache directory not found: {config.CACHE_DIR}")
            return

        for phrase_key in config.CACHED_PHRASES.keys():
            cache_file = config.CACHE_DIR / f"{phrase_key}.raw"
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        self.cache[phrase_key] = f.read()
                    logger.info(f"✓ Cached audio loaded: {phrase_key} ({len(self.cache[phrase_key])} bytes)")
                except Exception as e:
                    logger.error(f"Failed to load cache {phrase_key}: {e}")
            else:
                logger.warning(f"Missing cache file: {cache_file}")

    def get(self, phrase_key: str) -> Optional[bytes]:
        """Récupère un audio depuis le cache statique"""
        return self.cache.get(phrase_key)

    def has(self, phrase_key: str) -> bool:
        """Vérifie si une phrase est en cache statique"""
        return phrase_key in self.cache

    def get_dynamic(self, text: str) -> Optional[bytes]:
        """
        Récupère un audio depuis le cache dynamique (basé sur hash du texte)

        Args:
            text: Texte à chercher dans le cache dynamique

        Returns:
            Audio 8kHz si trouvé, None sinon
        """
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()

        if text_hash in self.dynamic_cache:
            logger.info(f"✓ Dynamic cache HIT: {text[:50]}...")
            return self.dynamic_cache[text_hash]

        return None

    def set_dynamic(self, text: str, audio_data: bytes):
        """
        Stocke un audio dans le cache dynamique

        Args:
            text: Texte de la solution (clé)
            audio_data: Audio 8kHz (valeur)
        """
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()

        # Si le cache est plein, supprimer l'entrée la plus ancienne (FIFO)
        if len(self.dynamic_cache) >= self.dynamic_cache_max_size:
            oldest_key = next(iter(self.dynamic_cache))
            del self.dynamic_cache[oldest_key]
            logger.debug("Dynamic cache full, removed oldest entry")

        self.dynamic_cache[text_hash] = audio_data
        logger.info(f"✓ Dynamic cache STORED: {text[:50]}... (size: {len(self.dynamic_cache)})")

    def get_cache_stats(self) -> Dict:
        """Retourne les statistiques du cache"""
        return {
            'static_cache_size': len(self.cache),
            'dynamic_cache_size': len(self.dynamic_cache),
            'dynamic_cache_max': self.dynamic_cache_max_size
        }


PROMPTS_CONFIG = None


def _load_prompts_config() -> Dict:
    """Charge le fichier de prompts externe pour permettre la modification à chaud."""
    global PROMPTS_CONFIG

    if PROMPTS_CONFIG is not None:
        return PROMPTS_CONFIG

    default_path = Path(__file__).resolve().parent / "prompts.yaml"
    prompts_path = getattr(config, "PROMPTS_PATH", default_path)

    try:
        with open(prompts_path, "r", encoding="utf-8") as f:
            PROMPTS_CONFIG = yaml.safe_load(f) or {}
            logger.info(f"Prompts loaded from {prompts_path}")
    except FileNotFoundError:
        logger.warning(f"Prompts file not found at {prompts_path}, using defaults")
        PROMPTS_CONFIG = {}
    except Exception as e:
        logger.error(f"Failed to load prompts file {prompts_path}: {e}")
        PROMPTS_CONFIG = {}

    return PROMPTS_CONFIG


# === Helper Functions ===
def construct_system_prompt(client_info: Dict = None, client_history: list = None) -> str:
    """
    Construit le prompt système pour le LLM avec les règles métier (Rôle: Secrétaire AI)
    en s'appuyant sur un fichier externe (prompts.yaml) pour faciliter la maintenance.
    """
    prompts_cfg = _load_prompts_config()

    default_base_prompt = (
        "Tu es l'assistant vocal secrétaire du Service Après-Vente Wouippleul. "
        "Ton rôle est UNIQUEMENT de faire un DIAGNOSTIC DE PREMIER NIVEAU et d'ASSISTER le client, "
        "PAS de résoudre des problèmes complexes.\n\n"
        "RÈGLES CRITIQUES :\n"
        "- Réponses TRÈS COURTES (1-2 phrases maximum)\n"
        "- Professionnel, empathique et rassurant\n"
        "- INTERDIT : Function Calling, actions complexes, commandes système\n"
        "- Ton but : GUIDER le client pour qu'il fasse lui-même les manipulations simples\n"
        "- Si le problème est complexe : TRANSFERT au technicien immédiatement\n\n"
        "PROCÉDURE DE DIAGNOSTIC :\n"
        "1. Demande quel type de problème : 'Internet' ou 'Mobile' ?\n"
        "2. Pour INTERNET :\n"
        "   a) ⚠️ IMPÉRATIF SÉCURITÉ : AVANT toute manipulation de box, tu DOIS dire :\n"
        "      'Attention, si vous appelez d'une ligne fixe, redémarrer la box coupera l'appel. "
        "Êtes-vous sur mobile ?'\n"
        "   b) Si OUI mobile : Guide le client pour redémarrer la box (débrancher 10 sec)\n"
        "   c) Si NON fixe : Propose de rappeler depuis un mobile OU transfert technicien\n"
        "3. Pour MOBILE : Propose simplement de redémarrer le téléphone\n"
        "4. Après manipulation : Demande si ça fonctionne maintenant\n"
        "5. Si échec ou problème complexe : Transfert immédiat au technicien\n\n"
        "PRÉVENTION : Le client fait les actions, toi tu GUIDES uniquement."
    )

    prompt = prompts_cfg.get("system_prompt_base", default_base_prompt)

    if client_info:
        prompt += (
            f"\n\nCLIENT RECONNU : {client_info.get('first_name')} {client_info.get('last_name')} "
            f"(Équipement: {client_info.get('box_model')})."
        )

    # MÉMOIRE LONG TERME : Injecter l'historique des tickets
    if client_history and len(client_history) > 0:
        prompt += "\n\nHISTORIQUE CLIENT (MÉMOIRE LONG TERME) :\n"

        # Compter les appels récents et problèmes non résolus
        recent_calls_count = len(client_history)
        unresolved_count = sum(1 for ticket in client_history if ticket['status'] != 'resolved')

        prompt += f"- {recent_calls_count} appel(s) récent(s) dans l'historique\n"

        if unresolved_count > 0:
            prompt += f"- {unresolved_count} problème(s) NON RÉSOLU(S) ⚠️\n"
            # Mentionner le dernier problème non résolu
            last_unresolved = next((t for t in client_history if t['status'] != 'resolved'), None)
            if last_unresolved:
                problem_type_fr = "Internet" if last_unresolved['problem_type'] == "internet" else "Mobile"
                prompt += f"- Dernier problème non résolu: {problem_type_fr} - {last_unresolved.get('summary', 'N/A')}\n"

        prompt += "\nADAPTE TON APPROCHE en fonction de cet historique. Si le client a des problèmes récurrents, sois plus empathique et considère un transfert technicien plus rapidement.\n"

    return prompt


def is_business_hours() -> bool:
    """
    Vérifie si on est dans les plages horaires précises (Lundi-Jeudi 9-12/14-18, Ven 9-12/14-17)
    """
    now = datetime.now()
    current_day = now.weekday()  # 0=Lundi, ..., 6=Dimanche
    current_hour = now.hour
    # Si le jour n'est pas dans le planning (ex: Samedi/Dimanche), c'est fermé
    if current_day not in config.BUSINESS_SCHEDULE:
        return False

    # Récupérer les plages du jour (ex: [(9, 12), (14, 18)])
    ranges = config.BUSINESS_SCHEDULE[current_day]

    # Vérifier si l'heure actuelle tombe dans l'une des plages
    for start_h, end_h in ranges:
        if start_h <= current_hour < end_h:
            return True

    return False


# === Call Handler ===
class CallHandler:
    """
    Gestionnaire d'appel individuel
    Implémente la logique métier SAV Wouippleul
    """

    def __init__(
        self,
        call_id: str,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        audio_cache: AudioCache,
        process_pool: ProcessPoolExecutor,
        phone_number: Optional[str] = None
    ):
        self.call_id = call_id
        self.reader = reader
        self.writer = writer
        self.audio_cache = audio_cache
        self.process_pool = process_pool
        self.phone_number = phone_number

        # État de la conversation
        self.state = ConversationState.INIT
        self.context: Dict = {}

        # Stocker le numéro de téléphone dans le contexte s'il est disponible
        if phone_number:
            self.context['phone_number'] = phone_number

        # Queues audio
        self.input_queue = asyncio.Queue()  # Audio brut depuis Asterisk
        self.output_queue = deque()  # Audio à envoyer vers Asterisk

        # Clients API
        self.deepgram_client = DeepgramClient(config.DEEPGRAM_API_KEY)
        self.groq_client = Groq(api_key=config.GROQ_API_KEY)
        self.elevenlabs_client = ElevenLabs(api_key=config.ELEVENLABS_API_KEY)

        # Asterisk AMI (pour récupérer CALLERID si absent du handshake)
        self.ami_manager = None

        # Contrôle de flux
        self.is_active = True
        self.is_speaking = False  # Robot parle actuellement
        self.last_user_speech_time = time.time()
        self.call_start_time = time.time()

        # Deepgram connection
        self.deepgram_connection = None

        # Logging audio
        self.audio_log_file = None
        self._init_audio_logging()

        # ANALYSE DE SENTIMENT TEMPS RÉEL
        # Liste de mots-clés négatifs (colère, frustration)
        self.negative_keywords = [
            "colère", "arnaque", "incompétent", "merde", "nul", "répéter",
            "enervé", "furieux", "scandale", "honte", "dégoûtant", "pourri",
            "marre", "ras le bol", "insupportable", "inadmissible", "inacceptable"
        ]
        self.negative_keyword_count = 0  # Compteur de mots négatifs détectés
        self.anger_threshold = 3  # Seuil de déclenchement (3 mots négatifs = transfert)

    def _init_audio_logging(self):
        """Initialise le fichier de log audio RAW"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_filename = config.LOGS_DIR / f"call_{self.call_id}_{timestamp}.raw"
            self.audio_log_file = open(log_filename, 'wb')
            logger.info(f"Audio logging: {log_filename}")
        except Exception as e:
            logger.error(f"Failed to init audio logging: {e}")

    def _detect_anger(self, user_text: str) -> bool:
        """
        Détecte la colère en temps réel via analyse de mots-clés (CPU friendly)

        Args:
            user_text: Texte transcrit de l'utilisateur

        Returns:
            True si le seuil de colère est atteint, False sinon
        """
        text_lower = user_text.lower()

        # Compter les mots négatifs dans cette phrase
        for keyword in self.negative_keywords:
            if keyword in text_lower:
                self.negative_keyword_count += 1
                logger.warning(
                    f"[{self.call_id}] Negative keyword detected: '{keyword}' "
                    f"(count: {self.negative_keyword_count}/{self.anger_threshold})"
                )

        # Vérifier si le seuil est atteint
        if self.negative_keyword_count >= self.anger_threshold:
            logger.warning(f"[{self.call_id}] ANGER THRESHOLD REACHED - Forcing transfer")
            return True

        return False

    async def _get_callerid_via_ami(self, uniqueid: str) -> Optional[str]:
        """
        Récupère le numéro de téléphone (CALLERID) via Asterisk AMI
        en utilisant une variable globale définie dans Asterisk.

        IMPORTANT: Cette fonction suppose que dans le dialplan Asterisk,
        une variable globale a été définie AVANT l'appel à AudioSocket:

        Set(GLOBAL(CALLER_${UNIQUEID})=${CALLERID(num)})
        AudioSocket(${UNIQUEID},<IP_SERVEUR_IA>:9090)

        Args:
            uniqueid: L'UNIQUEID de l'appel Asterisk (ex: "1763568391.4")

        Returns:
            Le numéro de téléphone (str) ou None si non trouvé
        """
        try:
            # Créer la connexion AMI si nécessaire
            if self.ami_manager is None:
                logger.info(f"[{self.call_id}] Connecting to Asterisk AMI at {config.AMI_HOST}:{config.AMI_PORT}")
                self.ami_manager = AMIManager(
                    host=config.AMI_HOST,
                    port=config.AMI_PORT,
                    username=config.AMI_USERNAME,
                    secret=config.AMI_SECRET,
                    ping_delay=10,
                    ping_timeout=5
                )
                await self.ami_manager.connect()
                logger.info(f"[{self.call_id}] AMI connected successfully")

            # Récupérer la variable globale CALLER_<UNIQUEID>
            # Cette variable doit avoir été définie dans Asterisk avec:
            # Set(GLOBAL(CALLER_${UNIQUEID})=${CALLERID(num)})

            # Utiliser l'UNIQUEID tel quel (garder les tirets pour format UUID standard)
            variable_name = f'CALLER_{uniqueid}'

            logger.info(f"[{self.call_id}] Fetching global variable '{variable_name}' via AMI")

            response = await self.ami_manager.send_action({
                'Action': 'Getvar',
                'Variable': variable_name
            })

            # Vérifier la réponse
            if response and hasattr(response, 'Value'):
                phone_number = response.Value
                logger.info(f"[{self.call_id}] CALLERID retrieved via AMI: {phone_number}")
                return phone_number
            else:
                logger.warning(
                    f"[{self.call_id}] Could not retrieve phone number from AMI. "
                    f"Make sure Asterisk dialplan sets: Set(GLOBAL(CALLER_${{UNIQUEID}})=${{CALLERID(num)}})"
                )
                return None

        except Exception as e:
            logger.error(f"[{self.call_id}] Failed to retrieve CALLERID via AMI: {e}")
            return None

    async def handle_call(self):
        """Point d'entrée principal pour gérer un appel"""
        try:
            logger.info(f"[{self.call_id}] Call started")

            # VÉRIFICATION HORAIRES D'OUVERTURE
            if not is_business_hours():
                logger.warning(f"[{self.call_id}] Call outside business hours")

                # Jouer message fermé
                await self._say("closed_hours")
                await asyncio.sleep(3)  # Laisser le message finir
                self.is_active = False

                return

            # RÉCUPÉRATION DU NUMÉRO DE TÉLÉPHONE VIA AMI (si absent du handshake)
            if not self.phone_number:
                logger.info(f"[{self.call_id}] Phone number not in handshake, fetching via AMI...")
                self.phone_number = await self._get_callerid_via_ami(self.call_id)

                if self.phone_number:
                    self.context['phone_number'] = self.phone_number
                    logger.info(f"[{self.call_id}] Phone number retrieved: {self.phone_number}")
                else:
                    logger.warning(f"[{self.call_id}] Could not retrieve phone number via AMI")

            # RÉCUPÉRATION INFOS CLIENT (si numéro de téléphone disponible)
            client_info = None
            client_history = []
            if self.phone_number:
                client_info = await db_utils.get_client_info(self.phone_number)
                # MÉMOIRE LONG TERME : Récupérer l'historique des tickets du client
                client_history = await db_utils.get_client_history(self.phone_number, limit=10)
            else:
                logger.warning(f"[{self.call_id}] No phone number available for client lookup")
            if client_info:
                self.context['client_info'] = client_info
                logger.info(f"[{self.call_id}] Client recognized: {client_info['first_name']} {client_info['last_name']}")
            if client_history:
                self.context['client_history'] = client_history
                logger.info(f"[{self.call_id}] Client history loaded: {len(client_history)} ticket(s)")

            # Démarrer les tâches en parallèle
            tasks = [
                asyncio.create_task(self._audio_input_handler()),
                asyncio.create_task(self._audio_output_handler()),
                asyncio.create_task(self._deepgram_handler()),
                asyncio.create_task(self._conversation_handler()),
                asyncio.create_task(self._timeout_monitor())
            ]

            # Attendre qu'une tâche se termine (erreur ou fin d'appel)
            done, pending = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED
            )

            # Annuler les tâches restantes
            for task in pending:
                task.cancel()

            logger.info(f"[{self.call_id}] Call ended")

        except Exception as e:
            logger.error(f"[{self.call_id}] Call error: {e}", exc_info=True)

        finally:
            await self._cleanup()

    async def _audio_input_handler(self):
        """Lit l'audio depuis AudioSocket et l'envoie à Deepgram"""
        try:
            while self.is_active:
                # Lire le header de la trame AudioSocket (3 bytes)
                # Format: type (1 byte) + length (2 bytes big-endian)
                header = await self.reader.readexactly(3)

                if not header or len(header) < 3:
                    logger.info(f"[{self.call_id}] AudioSocket closed")
                    self.is_active = False
                    break

                # Parser le header
                frame_type = header[0]
                frame_length = int.from_bytes(header[1:3], byteorder='big')

                # Lire les données de la trame
                chunk = await self.reader.readexactly(frame_length)

                if not chunk:
                    logger.info(f"[{self.call_id}] AudioSocket closed")
                    self.is_active = False
                    break

                # Logger l'audio brut (seulement si c'est une trame audio)
                if frame_type == 0x10 and self.audio_log_file:
                    try:
                        self.audio_log_file.write(chunk)
                    except Exception as e:
                        logger.error(f"Audio logging error: {e}")

                # Envoyer à la queue d'input (seulement si c'est une trame audio)
                if frame_type == 0x10:
                    await self.input_queue.put(chunk)

        except asyncio.CancelledError:
            pass
        except asyncio.IncompleteReadError:
            logger.info(f"[{self.call_id}] AudioSocket connection closed gracefully")
            self.is_active = False
        except Exception as e:
            logger.error(f"[{self.call_id}] Audio input error: {e}")
            self.is_active = False

    async def _audio_output_handler(self):
        """Envoie l'audio vers AudioSocket depuis la queue de sortie"""
        try:
            # Générer un chunk de silence (320 bytes = 20ms @ 8kHz 16-bit)
            silence_chunk = b'\x00' * 320

            while self.is_active:
                # Vérifier s'il y a de l'audio dans la queue
                if self.output_queue:
                    chunk = self.output_queue.popleft()
                else:
                    # CRITIQUE: Envoyer du silence pour maintenir le flux audio constant
                    # Asterisk s'attend à recevoir de l'audio toutes les 20ms
                    chunk = silence_chunk

                try:
                    # Encapsuler dans une trame AudioSocket
                    # Format: 0x10 (type audio) + length (2 bytes big-endian) + data
                    frame_type = bytes([0x10])
                    frame_length = len(chunk).to_bytes(2, byteorder='big')
                    frame = frame_type + frame_length + chunk

                    self.writer.write(frame)
                    await self.writer.drain()
                except Exception as e:
                    logger.error(f"[{self.call_id}] Failed to send audio: {e}")
                    self.is_active = False
                    break

                # Attendre 20ms avant le prochain chunk (maintenir 8kHz)
                await asyncio.sleep(0.02)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"[{self.call_id}] Audio output error: {e}")
            self.is_active = False

    async def _deepgram_handler(self):
        """Gère la connexion Deepgram STT avec streaming"""
        try:
            # Options Deepgram
            options = LiveOptions(
                model=config.DEEPGRAM_MODEL,
                language=config.DEEPGRAM_LANGUAGE,
                encoding=config.DEEPGRAM_ENCODING,
                sample_rate=config.DEEPGRAM_SAMPLE_RATE,
                channels=1,
                interim_results=True,
                punctuate=True,
                vad_events=True,
                endpointing=500  # Attendre 0.5s de silence avant de finaliser (réactivité maximale)
            )

            # Créer la connexion (API Deepgram 3.7+)
            self.deepgram_connection = self.deepgram_client.listen.asyncwebsocket.v("1")

            # Handlers d'événements
            async def on_message(conn, result, **kwargs):
                try:
                    sentence = result.channel.alternatives[0].transcript

                    if sentence:
                        # --- BARGE-IN UNIVERSEL ---
                        # Si le robot parle ET qu'on reçoit N'IMPORTE QUEL MOT, on coupe et on analyse
                        if self.is_speaking:
                            logger.info(f"[{self.call_id}] Barge-in triggered by user speech: '{sentence}'")
                            await self._handle_barge_in()

                            # On traite la phrase immédiatement (même si pas finale)
                            # pour réagir rapidement à l'interruption
                            if result.is_final:
                                logger.info(f"[{self.call_id}] User interrupted (final): {sentence}")
                                self.last_user_speech_time = time.time()

                                # ANALYSE DE SENTIMENT TEMPS RÉEL
                                anger_detected = self._detect_anger(sentence)

                                if anger_detected:
                                    # FORCER LE TRANSFERT IMMÉDIAT (bypass LLM)
                                    logger.warning(f"[{self.call_id}] Anger detected - bypassing LLM, forcing transfer")

                                    calming_message = (
                                        "Je comprends votre frustration. "
                                        "Je vais immédiatement vous mettre en relation avec un technicien "
                                        "qui pourra mieux vous aider."
                                    )
                                    await self._say_dynamic(calming_message)

                                    self.state = ConversationState.TRANSFER
                                    await asyncio.sleep(2)
                                    self.is_active = False
                                    return

                                # Analyser la demande d'interruption et répondre intelligemment
                                await self._process_user_input(sentence)
                            else:
                                # Transcription intermédiaire (interim) - on log juste
                                logger.debug(f"[{self.call_id}] User interrupted (interim): '{sentence}'")
                        # ------------------------------------

                        # Traitement normal si le bot ne parlait pas
                        elif result.is_final:
                            logger.info(f"[{self.call_id}] User: {sentence}")
                            self.last_user_speech_time = time.time()

                            # ANALYSE DE SENTIMENT TEMPS RÉEL
                            anger_detected = self._detect_anger(sentence)

                            if anger_detected:
                                # FORCER LE TRANSFERT IMMÉDIAT (bypass LLM)
                                logger.warning(f"[{self.call_id}] Anger detected - bypassing LLM, forcing transfer")

                                calming_message = (
                                    "Je comprends votre frustration. "
                                    "Je vais immédiatement vous mettre en relation avec un technicien "
                                    "qui pourra mieux vous aider."
                                )
                                await self._say_dynamic(calming_message)

                                self.state = ConversationState.TRANSFER
                                await asyncio.sleep(2)
                                self.is_active = False
                                return

                            # Continuer le traitement normal
                            await self._process_user_input(sentence)

                except Exception as e:
                    logger.error(f"Deepgram message error: {e}")

            async def on_speech_started(conn, speech_started, **kwargs):
                """Détection VAD : On log juste l'activité, MAIS ON NE COUPE PAS"""
                logger.info(f"[{self.call_id}] VAD activity detected (bruit/voix) - Ignored for barge-in")
                # Supprimé : await self._handle_barge_in()  <-- Ne pas couper sur simple VAD

            async def on_error(conn, error, **kwargs):
                logger.error(f"Deepgram error: {error}")

            # Enregistrer les handlers
            self.deepgram_connection.on(LiveTranscriptionEvents.Transcript, on_message)
            self.deepgram_connection.on(LiveTranscriptionEvents.SpeechStarted, on_speech_started)
            self.deepgram_connection.on(LiveTranscriptionEvents.Error, on_error)

            # Démarrer la connexion
            if not await self.deepgram_connection.start(options):
                logger.error("Failed to start Deepgram connection")
                logger.warning(f"[{self.call_id}] Continuing call without STT (Speech-to-Text disabled)")
                # NE PAS terminer l'appel - continuer sans STT
                return

            # Streamer l'audio vers Deepgram
            while self.is_active:
                try:
                    chunk = await asyncio.wait_for(
                        self.input_queue.get(),
                        timeout=1.0
                    )
                    await self.deepgram_connection.send(chunk)

                except asyncio.TimeoutError:
                    continue

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"[{self.call_id}] Deepgram handler error: {e}", exc_info=True)
            logger.warning(f"[{self.call_id}] Deepgram failed, but call continues without STT")
            # NE PAS terminer l'appel - continuer sans STT
        finally:
            if self.deepgram_connection:
                try:
                    await self.deepgram_connection.finish()
                except Exception as e:
                    logger.error(f"Deepgram finish error: {e}")

    async def _conversation_handler(self):
        """Gestionnaire de la machine à états conversationnelle"""
        try:
            # Démarrer avec le message de bienvenue PERSONNALISÉ si client reconnu
            client_info = self.context.get('client_info')
            client_history = self.context.get('client_history', [])

            # VÉRIFIER LES TICKETS EN ATTENTE (pour tous les clients, même sans fiche)
            pending_tickets = []
            if self.phone_number:
                pending_tickets = await db_utils.get_pending_tickets(self.phone_number)

            if client_info:
                # CLIENT AVEC FICHE COMPLÈTE
                if pending_tickets:
                    # Il y a des tickets en attente, demander si c'est pour ça
                    ticket = pending_tickets[0]  # Premier ticket en attente
                    problem_type_fr = "connexion" if ticket['problem_type'] == "internet" else "mobile"

                    welcome_with_ticket = (
                        f"Bonjour {client_info['first_name']} {client_info['last_name']}, "
                        f"je vois un ticket ouvert concernant votre {problem_type_fr}. "
                        f"Est-ce à ce sujet ?"
                    )
                    await self._say_dynamic(welcome_with_ticket)
                    logger.info(f"[{self.call_id}] Ticket verification: {ticket['id']} ({ticket['problem_type']})")

                    # Stocker le ticket dans le contexte
                    self.context['pending_ticket'] = ticket
                    self.state = ConversationState.TICKET_VERIFICATION

                else:
                    # Pas de ticket en attente, message personnalisé normal
                    welcome_personalized = (
                        f"Bonjour {client_info['first_name']} {client_info['last_name']}, "
                        f"bienvenue au SAV Wouippleul. Comment puis-je vous aider ?"
                    )
                    await self._say_dynamic(welcome_personalized)
                    logger.info(f"[{self.call_id}] Personalized welcome (no pending tickets)")
                    self.state = ConversationState.DIAGNOSTIC

            elif client_history and len(client_history) > 0:
                # CLIENT RÉCURRENT (avec historique mais sans fiche client)
                if pending_tickets:
                    # Il y a des tickets en attente
                    ticket = pending_tickets[0]
                    problem_type_fr = "connexion" if ticket['problem_type'] == "internet" else "mobile"

                    welcome_returning_with_ticket = (
                        f"Bonjour, je vois que vous avez déjà appelé {len(client_history)} fois. "
                        f"Je suis Eko, votre assistant virtuel. "
                        f"Vous avez un ticket ouvert concernant votre {problem_type_fr}. "
                        f"Est-ce à ce sujet ?"
                    )
                    await self._say_dynamic(welcome_returning_with_ticket)
                    logger.info(f"[{self.call_id}] Returning client with pending ticket: {ticket['id']}")

                    # Stocker le ticket dans le contexte
                    self.context['pending_ticket'] = ticket
                    self.state = ConversationState.TICKET_VERIFICATION

                else:
                    # Client récurrent sans ticket en attente
                    welcome_returning = (
                        f"Bonjour, je vois que vous avez déjà appelé {len(client_history)} fois. "
                        f"Je suis Eko, votre assistant virtuel. "
                        f"Comment puis-je vous aider aujourd'hui ?"
                    )
                    await self._say_dynamic(welcome_returning)
                    logger.info(f"[{self.call_id}] Returning client welcome ({len(client_history)} previous calls)")
                    self.state = ConversationState.DIAGNOSTIC

            else:
                # NOUVEAU CLIENT (pas d'historique, pas de fiche)
                # Utiliser le message en cache mais CONTINUER avec un message dynamique
                # pour garantir que "Je suis Eko" soit dit
                welcome_new = (
                    "Bonjour et bienvenue au service support technique de Wipple. "
                    "Je suis Eko, votre assistant virtuel. "
                    "Comment puis-je vous aider aujourd'hui ?"
                )
                await self._say_dynamic(welcome_new)
                logger.info(f"[{self.call_id}] New client welcome")
                self.state = ConversationState.DIAGNOSTIC

            # BOUCLE DE CONVERSATION : Garder le handler actif
            # Le traitement des réponses se fait via _process_user_input() appelé par Deepgram
            while self.is_active:
                await asyncio.sleep(0.3)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"[{self.call_id}] Conversation error: {e}")

    async def _timeout_monitor(self):
        """Surveille les timeouts (silence, durée max)"""
        try:
            while self.is_active:
                await asyncio.sleep(1)

                # Vérifier la durée max de l'appel
                call_duration = time.time() - self.call_start_time
                if call_duration > config.MAX_CALL_DURATION:
                    logger.warning(f"[{self.call_id}] Max call duration reached")
                    await self._say("goodbye")
                    self.is_active = False
                    break

                # Vérifier le silence utilisateur (seulement si on attend une réponse)
                if not self.is_speaking and self.state not in [ConversationState.INIT, ConversationState.GOODBYE]:
                    silence_duration = time.time() - self.last_user_speech_time

                    if silence_duration > config.SILENCE_HANGUP_TIMEOUT:
                        logger.warning(f"[{self.call_id}] Silence timeout - hanging up")
                        await self._say("goodbye")
                        self.is_active = False
                        break

                    elif silence_duration > config.SILENCE_WARNING_TIMEOUT:
                        # Jouer "Allô, vous êtes toujours là ?"
                        if not self.is_speaking:
                            await self._say("allo")
                            self.last_user_speech_time = time.time()  # Reset

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"[{self.call_id}] Timeout monitor error: {e}")

    async def _process_user_input(self, user_text: str):
        """Traite l'input utilisateur selon l'état actuel"""
        try:
            # Récupérer les infos client et historique si disponibles
            client_info = self.context.get('client_info')
            client_history = self.context.get('client_history', [])

            # Logique de la machine à états SAV Wouippleul
            if self.state == ConversationState.TICKET_VERIFICATION:
                # Vérifier si le client appelle pour le ticket en attente
                user_lower = user_text.lower()

                if any(word in user_lower for word in ["oui", "yes", "exact", "c'est", "correct", "affirmatif"]):
                    # OUI, c'est pour le ticket en attente
                    logger.info(f"[{self.call_id}] Client confirms ticket: {self.context['pending_ticket']['id']}")
                    await self._say("ticket_transfer_ok")
                    # Attendre que l'audio soit réellement joué
                    audio_data = self.audio_cache.get("ticket_transfer_ok")
                    if audio_data:
                        audio_duration = len(audio_data) / (8000 * 2)
                        await asyncio.sleep(audio_duration + 0.5)
                    self.state = ConversationState.TRANSFER
                    self.is_active = False

                elif any(word in user_lower for word in ["non", "no", "pas", "autre", "différent"]):
                    # NON, c'est pour un autre problème
                    logger.info(f"[{self.call_id}] Client has different issue")
                    await self._say("ticket_not_related")
                    self.state = ConversationState.DIAGNOSTIC

                else:
                    # Pas clair, redemander
                    clarification = "Est-ce bien à ce sujet ? Répondez oui ou non s'il vous plaît."
                    await self._say_dynamic(clarification)

            elif self.state == ConversationState.WELCOME:
                # Demander l'identification
                response = await self._ask_llm(
                    user_text,
                    system_prompt=construct_system_prompt(client_info, client_history)
                )
                await self._say_dynamic(response)
                self.state = ConversationState.IDENTIFICATION

            elif self.state == ConversationState.IDENTIFICATION:
                # Extraire les infos et passer au diagnostic
                cleaned_email = clean_email_text(user_text)
                self.context['user_info'] = cleaned_email
                if "@" in cleaned_email:
                    self.context['email'] = cleaned_email
                response = await self._ask_llm(
                    user_text,
                    system_prompt=construct_system_prompt(client_info, client_history)
                )
                await self._say_dynamic(response)
                self.state = ConversationState.DIAGNOSTIC

            elif self.state == ConversationState.DIAGNOSTIC:
                # Déterminer le type de problème
                problem_type = "internet" if "internet" in user_text.lower() else "mobile"
                self.context['problem_type'] = problem_type

                # Proposer la solution avec WARNING pour Internet
                if problem_type == "internet":
                    # IMPORTANT: Demander si l'utilisateur est sur mobile avant de redémarrer la box
                    warning = (
                        "Attention, si vous appelez depuis une ligne fixe, "
                        "le redémarrage de la box coupera la communication. "
                        "Êtes-vous sur un mobile ?"
                    )
                    await self._say_dynamic(warning)
                    self.state = ConversationState.SOLUTION
                else:
                    solution = "Essayez de redémarrer votre téléphone."
                    await self._say_dynamic(solution)
                    self.state = ConversationState.SOLUTION

            elif self.state == ConversationState.SOLUTION:
                # Demander si la solution a fonctionné
                await asyncio.sleep(2)  # Attendre un peu
                await self._say_dynamic("Avez-vous pu faire la manipulation ? Est-ce que ça fonctionne maintenant ?")
                self.state = ConversationState.VERIFICATION

            elif self.state == ConversationState.VERIFICATION:
                # Vérifier si ça marche
                if any(word in user_text.lower() for word in ["oui", "marche", "fonctionne", "ok", "bien"]):
                    # Problème résolu
                    await self._say("goodbye")
                    self.is_active = False
                else:
                    # Problème non résolu -> Technicien
                    tech_available = await self._check_technician()

                    if tech_available:
                        await self._say("transfer")
                        # Attendre que l'audio soit joué
                        audio_data = self.audio_cache.get("transfer")
                        if audio_data:
                            await asyncio.sleep(len(audio_data) / (8000 * 2) + 0.5)
                        self.state = ConversationState.TRANSFER
                        self.is_active = False
                    else:
                        await self._say_dynamic("Malheureusement, aucun technicien n'est disponible pour le moment. Nous vous rappellerons dans les plus brefs délais.")
                        await asyncio.sleep(6)  # ~6s pour message dynamique
                        await self._say("goodbye")
                        # Attendre que l'audio goodbye soit joué
                        audio_data = self.audio_cache.get("goodbye")
                        if audio_data:
                            await asyncio.sleep(len(audio_data) / (8000 * 2) + 0.5)
                        self.is_active = False

        except Exception as e:
            logger.error(f"[{self.call_id}] Error processing user input: {e}")
            await self._say("error")

    async def _ask_llm(self, user_message: str, system_prompt: str) -> str:
        """Appelle Groq LLM pour générer une réponse"""
        try:
            start_time = time.time()

            response = self.groq_client.chat.completions.create(
                model=config.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=config.GROQ_TEMPERATURE,
                max_tokens=config.GROQ_MAX_TOKENS,
                timeout=config.API_TIMEOUT
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"[{self.call_id}] Groq API error: {e}")
            return "Je suis désolé, pouvez-vous répéter ?"

    async def _analyze_sentiment_llm(self, conversation_summary: str) -> str:
        """
        Analyse le sentiment du client via LLM

        Args:
            conversation_summary: Résumé de la conversation

        Returns:
            'positive', 'neutral', ou 'negative'
        """
        try:
            sentiment_prompt = (
                "Tu es un expert en analyse de sentiment. "
                "Analyse le sentiment du client dans cette conversation SAV.\n"
                "Réponds UNIQUEMENT par un seul mot : positive, neutral, ou negative."
            )

            result = await self._ask_llm(conversation_summary, sentiment_prompt)
            result = result.lower().strip()

            # Validation stricte
            if result in ['positive', 'neutral', 'negative']:
                logger.info(f"[{self.call_id}] Sentiment analyzed: {result}")
                return result
            else:
                logger.warning(f"[{self.call_id}] Invalid sentiment response: {result}, defaulting to neutral")
                return 'neutral'

        except Exception as e:
            logger.error(f"[{self.call_id}] Sentiment analysis error: {e}")
            return 'neutral'

    async def _classify_problem(self, problem_description: str, problem_type: str) -> Dict[str, str]:
        """
        Classifie le problème avec des tags stricts via LLM

        Args:
            problem_description: Description du problème
            problem_type: 'internet' ou 'mobile'

        Returns:
            Dict avec 'tag' et 'severity' (LOW, MEDIUM, HIGH)
        """
        try:
            classify_prompt = (
                "Tu es un expert en classification de problèmes SAV.\n"
                "Classifie le problème avec un tag strict.\n\n"
                "TAGS INTERNET : FIBRE_SYNCHRO, FIBRE_DEBIT, WIFI_FAIBLE, BOX_ETEINTE, CONNEXION_INSTABLE, DNS_PROBLEME\n"
                "TAGS MOBILE : MOBILE_RESEAU, MOBILE_DATA, MOBILE_APPELS, MOBILE_SMS, CARTE_SIM\n\n"
                "Réponds au format JSON strict : {\"tag\": \"XXX\", \"severity\": \"LOW|MEDIUM|HIGH\"}\n"
                "Exemple: {\"tag\": \"FIBRE_SYNCHRO\", \"severity\": \"MEDIUM\"}"
            )

            result = await self._ask_llm(problem_description, classify_prompt)

            # Parser le JSON
            import json
            try:
                classification = json.loads(result)
                tag = classification.get('tag', 'UNKNOWN').upper()
                severity = classification.get('severity', 'MEDIUM').upper()

                # Validation
                if severity not in ['LOW', 'MEDIUM', 'HIGH']:
                    severity = 'MEDIUM'

                logger.info(f"[{self.call_id}] Problem classified: {tag} ({severity})")

                return {'tag': tag, 'severity': severity}

            except json.JSONDecodeError:
                logger.warning(f"[{self.call_id}] Invalid JSON from classification: {result}")
                return {'tag': 'UNKNOWN', 'severity': 'MEDIUM'}

        except Exception as e:
            logger.error(f"[{self.call_id}] Classification error: {e}")
            return {'tag': 'UNKNOWN', 'severity': 'MEDIUM'}

    async def _say(self, phrase_key: str):
        """Dit une phrase depuis le cache (pas de CPU)"""
        try:
            audio_data = self.audio_cache.get(phrase_key)

            if not audio_data:
                logger.warning(f"[{self.call_id}] Cache miss: {phrase_key}")
                return

            # Envoyer directement à la queue de sortie (déjà en 8kHz)
            self.is_speaking = True
            await self._send_audio(audio_data)
            self.is_speaking = False

        except Exception as e:
            logger.error(f"[{self.call_id}] Error saying '{phrase_key}': {e}")

    async def _say_dynamic(self, text: str):
        """Version Optimisée : Streaming Temps Réel + Modèle Turbo"""
        try:
            self.is_speaking = True

            # 1. Cache Check
            cached_audio = self.audio_cache.get_dynamic(text)
            if cached_audio:
                logger.info(f"[{self.call_id}] Cache HIT dynamic")
                await self._send_audio(cached_audio)
                self.is_speaking = False
                return

            # 2. Streaming Generation (Turbo v2.5)
            logger.info(f"[{self.call_id}] Streaming TTS generation...")
            
            audio_stream_iterator = self.elevenlabs_client.generate(
                text=text,
                voice=config.ELEVENLABS_VOICE_ID,
                model="eleven_turbo_v2_5", # Moins cher et plus rapide
                stream=True,
                output_format="mp3_44100_128",
                latency=1
            )
            
            # 3. Conversion à la volée (Pipe)
            pcm_stream = stream_and_convert_to_8khz(audio_stream_iterator)

            # 4. Envoi immédiat à Asterisk
            full_audio_for_cache = bytearray()
            
            for chunk in pcm_stream:
                if not self.output_queue and not self.is_speaking: 
                    break # Stop si interruption
                    
                self.output_queue.append(chunk)
                full_audio_for_cache.extend(chunk)

            # 5. Mise en cache
            if len(full_audio_for_cache) > 0:
                self.audio_cache.set_dynamic(text, bytes(full_audio_for_cache))
            
            self.is_speaking = False

        except Exception as e:
            logger.error(f"[{self.call_id}] Error in streaming TTS: {e}")
            self.is_speaking = False
            await self._say("error")

    async def _send_audio(self, audio_data: bytes):
        """Envoie de l'audio à la queue de sortie par chunks"""
        # Découper en chunks de 320 bytes (20ms @ 8kHz)
        chunk_size = 320
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i + chunk_size]

            # Padding si nécessaire
            if len(chunk) < chunk_size:
                chunk += b'\x00' * (chunk_size - len(chunk))

            self.output_queue.append(chunk)

    async def _handle_barge_in(self):
        """Gère l'interruption (barge-in) de l'utilisateur"""
        logger.info(f"[{self.call_id}] Barge-in detected - clearing output queue")

        # Vider la queue de sortie immédiatement
        self.output_queue.clear()
        self.is_speaking = False

    async def _check_technician(self) -> bool:
        """Vérifie si un technicien est disponible via la charge réelle des tickets transférés."""
        try:
            # Fenêtre et seuil par défaut (peut être surchargé via config)
            window_minutes = getattr(config, "TECHNICIAN_LOAD_WINDOW_MIN", 10)
            max_active = getattr(config, "TECHNICIAN_MAX_ACTIVE_TRANSFERS", 5)

            is_available = await db_utils.is_technician_available(
                max_active=max_active,
                window_minutes=window_minutes
            )

            logger.info(f"[{self.call_id}] Technician availability (window {window_minutes}m, max {max_active}): {is_available}")
            return is_available

        except Exception as e:
            logger.error(f"[{self.call_id}] Technician availability check failed: {e}")
            # Fail-open: on préfère tenter le transfert plutôt que de bloquer
            return True

    async def _cleanup(self):
        """Nettoyage des ressources + sauvegarde ticket avec analyse LLM"""
        try:
            # SAUVEGARDER LE TICKET DANS LA BASE DE DONNÉES
            call_duration = int(time.time() - self.call_start_time)

            # Générer un résumé de la conversation via LLM
            summary = "Appel traité par le voicebot."
            classification = {'tag': 'UNKNOWN', 'severity': 'MEDIUM'}

            if self.context.get('problem_type'):
                try:
                    # Construire un contexte de conversation
                    conversation_context = (
                        f"Type de problème: {self.context.get('problem_type', 'inconnu')}\n"
                        f"État final: {self.state.value}\n"
                        f"Durée: {call_duration}s\n"
                        f"Infos utilisateur: {self.context.get('user_info', 'Non renseigné')}"
                    )

                    # Demander au LLM un résumé court
                    summary = await self._ask_llm(
                        conversation_context,
                        system_prompt="Génère un résumé très court (1 phrase) de cet appel SAV."
                    )

                    # CLASSIFICATION AUTOMATIQUE avec tags stricts
                    classification = await self._classify_problem(
                        summary,
                        self.context.get('problem_type', 'unknown')
                    )

                except Exception as e:
                    logger.error(f"[{self.call_id}] Failed to generate summary/classification: {e}")
                    summary = f"Problème {self.context.get('problem_type', 'inconnu')} traité."

            # Déterminer le statut final
            if self.state == ConversationState.GOODBYE:
                status = "resolved"
            elif self.state == ConversationState.TRANSFER:
                status = "transferred"
            else:
                status = "failed"

            # ANALYSE DE SENTIMENT VIA LLM (amélioration)
            sentiment = await self._analyze_sentiment_llm(summary)

            # Préparer les données du ticket
            ticket_data = {
                'call_uuid': self.call_id,
                'phone_number': self.context.get('phone_number', self.call_id),  # Fallback sur call_id
                'problem_type': self.context.get('problem_type', 'unknown'),
                'status': status,
                'sentiment': sentiment,
                'summary': summary,
                'duration_seconds': call_duration,
                'tag': classification['tag'],
                'severity': classification['severity']
            }

            # Sauvegarder dans la DB
            ticket_id = await db_utils.create_ticket(ticket_data)
            if ticket_id:
                logger.info(f"[{self.call_id}] Ticket saved: {ticket_id} (tag: {classification['tag']}, sentiment: {sentiment})")
            else:
                logger.warning(f"[{self.call_id}] Failed to save ticket")

            # Fermer le fichier de log audio
            if self.audio_log_file:
                self.audio_log_file.close()

            # Fermer la connexion Deepgram
            if self.deepgram_connection:
                try:
                    await self.deepgram_connection.finish()
                except:
                    pass

            # Fermer le writer
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except:
                pass

            logger.info(f"[{self.call_id}] Cleanup completed")

        except Exception as e:
            logger.error(f"[{self.call_id}] Cleanup error: {e}")


# === AudioSocket Server ===
class AudioSocketServer:
    """Serveur TCP AudioSocket principal"""

    def __init__(self):
        self.audio_cache = AudioCache()
        self.process_pool = ProcessPoolExecutor(max_workers=config.PROCESS_POOL_WORKERS)
        self.active_calls = 0

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Gère une connexion AudioSocket (un appel)"""
        call_id = None
        phone_number = None

        try:
            # Lire le handshake (jusqu'à 64 bytes pour supporter le format "0612345678_UUID")
            identifier_bytes = await reader.read(64)

            if len(identifier_bytes) == 0:
                logger.error("Invalid AudioSocket handshake: no data")
                writer.close()
                await writer.wait_closed()
                return

            # Parser l'identifiant selon le protocole AudioSocket
            logger.info(f"Handshake bytes (first 20): {identifier_bytes[:20].hex()}")

            phone_number = None

            # Vérifier le format du handshake AudioSocket
            if len(identifier_bytes) >= 3 and identifier_bytes[0] == 0x01:
                # Format binaire AudioSocket : \x01 + length (2 bytes) + UUID (16 bytes)
                uuid_length = int.from_bytes(identifier_bytes[1:3], byteorder='big')
                logger.info(f"AudioSocket binary handshake detected, UUID length: {uuid_length}")

                if uuid_length == 16 and len(identifier_bytes) >= 19:
                    # Extraire les 16 bytes d'UUID
                    uuid_bytes = identifier_bytes[3:19]
                    uuid_hex = uuid_bytes.hex()

                    # Reformater au format UUID standard : XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
                    call_id = f"{uuid_hex[0:8]}-{uuid_hex[8:12]}-{uuid_hex[12:16]}-{uuid_hex[16:20]}-{uuid_hex[20:32]}"
                    logger.info(f"[{call_id}] New call connected (AudioSocket binary protocol)")
                    logger.info(f"[{call_id}] UUID extracted from binary handshake")
                else:
                    # Fallback : utiliser les 16 premiers bytes comme UUID
                    call_id = identifier_bytes[3:19].hex()
                    logger.warning(f"[{call_id}] Unexpected UUID length: {uuid_length}")
            else:
                # Essayer de décoder en texte UTF-8 (ancien format)
                try:
                    identifier_str = identifier_bytes.decode('utf-8', errors='ignore').strip('\x00').strip()
                    if identifier_str:
                        call_id = identifier_str
                        logger.info(f"[{call_id}] New call connected (text format)")
                    else:
                        # Fallback final
                        call_id = identifier_bytes[:16].hex()
                        logger.info(f"[{call_id}] New call connected (raw hex format)")
                except Exception as e:
                    logger.warning(f"Failed to parse handshake: {e}")
                    call_id = identifier_bytes[:16].hex()
                    logger.info(f"[{call_id}] New call connected (fallback format)")

            # Vérifier la limite de calls simultanés
            if self.active_calls >= config.MAX_CONCURRENT_CALLS:
                logger.warning(f"[{call_id}] Max concurrent calls reached - rejecting")
                writer.close()
                await writer.wait_closed()
                return

            self.active_calls += 1

            # Créer le handler d'appel (qui lancera automatiquement _audio_output_handler)
            handler = CallHandler(
                call_id=call_id,
                reader=reader,
                writer=writer,
                audio_cache=self.audio_cache,
                process_pool=self.process_pool,
                phone_number=phone_number
            )

            # Traiter l'appel
            await handler.handle_call()

        except Exception as e:
            logger.error(f"[{call_id or 'unknown'}] Client error: {e}", exc_info=True)

        finally:
            self.active_calls -= 1
            logger.info(f"Active calls: {self.active_calls}")

    async def start(self):
        """Démarre le serveur AudioSocket"""
        server = await asyncio.start_server(
            self.handle_client,
            config.AUDIOSOCKET_HOST,
            config.AUDIOSOCKET_PORT
        )

        addr = server.sockets[0].getsockname()
        logger.info("=" * 60)
        logger.info(f"🎙️  AudioSocket Server started on {addr[0]}:{addr[1]}")
        logger.info(f"📦 Cache loaded: {len(self.audio_cache.cache)} phrases")
        logger.info(f"⚙️  Process pool workers: {config.PROCESS_POOL_WORKERS}")
        logger.info(f"📞 Max concurrent calls: {config.MAX_CONCURRENT_CALLS}")
        logger.info("=" * 60)

        async with server:
            await server.serve_forever()

    def shutdown(self):
        """Arrêt propre du serveur"""
        logger.info("Shutting down server...")
        self.process_pool.shutdown(wait=True)


# === Main Entry Point ===
async def main():
    """Point d'entrée principal avec uvloop"""

    # Vérifier les clés API
    if not all([config.DEEPGRAM_API_KEY, config.GROQ_API_KEY, config.ELEVENLABS_API_KEY]):
        logger.error("❌ Missing API keys in .env file")
        sys.exit(1)

    # INITIALISER LES POOLS DE BASE DE DONNÉES
    try:
        logger.info("Initializing database pools...")
        await db_utils.init_db_pools()
        logger.info("✓ Database pools ready")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        logger.warning("⚠️  Continuing without database (tickets won't be saved)")

    # Créer le serveur
    server = AudioSocketServer()

    # Gérer les signaux pour arrêt propre
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        server.shutdown()
        # Fermer les pools DB
        asyncio.create_task(db_utils.close_db_pools())
        os._exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Démarrer le serveur
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    finally:
        server.shutdown()
        # Fermer les pools DB proprement
        await db_utils.close_db_pools()


if __name__ == "__main__":
    # Utiliser uvloop pour de meilleures performances
    uvloop.install()
    asyncio.run(main())

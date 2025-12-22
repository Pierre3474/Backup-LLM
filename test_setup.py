#!/usr/bin/env python3
"""
Script de test de la configuration du voicebot
Vérifie que tout est prêt avant de lancer le serveur

Usage:
    python test_setup.py
"""
import sys
import os
from pathlib import Path

# Couleurs pour l'output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'


def print_success(msg):
    print(f"{GREEN}✓{RESET} {msg}")


def print_error(msg):
    print(f"{RED}✗{RESET} {msg}")


def print_warning(msg):
    print(f"{YELLOW}⚠{RESET} {msg}")


def test_python_version():
    """Vérifie la version Python >= 3.11"""
    import sys
    version = sys.version_info

    if version.major >= 3 and version.minor >= 11:
        print_success(f"Python version: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python version: {version.major}.{version.minor}.{version.micro} (requis: >= 3.11)")
        return False


def test_dependencies():
    """Vérifie que toutes les dépendances sont installées"""
    required_modules = [
        'uvloop',
        'pydub',
        'deepgram',
        'groq',
        'openai',
        'dotenv',
        'aiofiles'
    ]

    all_ok = True
    for module in required_modules:
        try:
            __import__(module)
            print_success(f"Module '{module}' installé")
        except ImportError:
            print_error(f"Module '{module}' manquant")
            all_ok = False

    return all_ok


def test_ffmpeg():
    """Vérifie que FFmpeg est installé"""
    import subprocess

    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print_success(f"FFmpeg installé: {version_line}")
            return True
        else:
            print_error("FFmpeg non trouvé")
            return False

    except FileNotFoundError:
        print_error("FFmpeg non installé")
        return False
    except Exception as e:
        print_error(f"Erreur vérification FFmpeg: {e}")
        return False


def test_env_file():
    """Vérifie que le fichier .env existe et contient les clés"""
    if not Path('.env').exists():
        print_error(".env manquant (copier .env.example)")
        return False

    print_success(".env existe")

    # Vérifier les clés
    try:
        import config

        keys_ok = True

        if not config.DEEPGRAM_API_KEY or config.DEEPGRAM_API_KEY.startswith('your_'):
            print_warning("DEEPGRAM_API_KEY non configurée")
            keys_ok = False
        else:
            print_success("DEEPGRAM_API_KEY configurée")

        if not config.GROQ_API_KEY or config.GROQ_API_KEY.startswith('your_'):
            print_warning("GROQ_API_KEY non configurée")
            keys_ok = False
        else:
            print_success("GROQ_API_KEY configurée")

        if not config.OPENAI_API_KEY or config.OPENAI_API_KEY.startswith('your_'):
            print_warning("OPENAI_API_KEY non configurée")
            keys_ok = False
        else:
            print_success("OPENAI_API_KEY configurée")

        return keys_ok

    except Exception as e:
        print_error(f"Erreur lecture .env: {e}")
        return False


def test_directories():
    """Vérifie que les répertoires nécessaires existent"""
    import config

    all_ok = True

    if config.CACHE_DIR.exists():
        print_success(f"Cache directory: {config.CACHE_DIR}")
    else:
        print_error(f"Cache directory manquant: {config.CACHE_DIR}")
        all_ok = False

    if config.LOGS_DIR.exists():
        print_success(f"Logs directory: {config.LOGS_DIR}")
    else:
        print_error(f"Logs directory manquant: {config.LOGS_DIR}")
        all_ok = False

    return all_ok


def test_audio_cache():
    """Vérifie que le cache audio a été généré"""
    import config

    if not config.CACHE_DIR.exists():
        print_error("Cache directory manquant")
        return False

    cache_files = list(config.CACHE_DIR.glob("*.raw"))

    if len(cache_files) == 0:
        print_warning("Aucun fichier audio en cache (exécuter: python generate_cache.py)")
        return False

    expected_count = len(config.CACHED_PHRASES)

    if len(cache_files) >= expected_count:
        print_success(f"Cache audio: {len(cache_files)}/{expected_count} fichiers")
        return True
    else:
        print_warning(f"Cache audio incomplet: {len(cache_files)}/{expected_count} fichiers")
        return False


def test_audio_utils():
    """Teste les fonctions audio_utils"""
    try:
        from audio_utils import generate_silence, validate_audio_format

        # Générer du silence
        silence = generate_silence(1000)  # 1 seconde

        # Valider
        is_valid = validate_audio_format(silence)

        if is_valid:
            print_success("audio_utils fonctionne")
            return True
        else:
            print_error("audio_utils: validation échouée")
            return False

    except Exception as e:
        print_error(f"audio_utils erreur: {e}")
        return False


def test_port_availability():
    """Vérifie que le port AudioSocket est disponible"""
    import socket
    import config

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((config.AUDIOSOCKET_HOST, config.AUDIOSOCKET_PORT))
            print_success(f"Port {config.AUDIOSOCKET_PORT} disponible")
            return True

    except OSError:
        print_error(f"Port {config.AUDIOSOCKET_PORT} déjà utilisé")
        return False


def main():
    """Point d'entrée principal"""
    print("=" * 60)
    print("🧪 Test de Configuration - Voicebot SAV Wouippleul")
    print("=" * 60)
    print()

    results = {
        "Python version": test_python_version(),
        "Dépendances Python": test_dependencies(),
        "FFmpeg": test_ffmpeg(),
        "Fichier .env": test_env_file(),
        "Répertoires": test_directories(),
        "Cache audio": test_audio_cache(),
        "Audio utils": test_audio_utils(),
        "Port disponible": test_port_availability()
    }

    print()
    print("=" * 60)
    print("📊 Résumé")
    print("=" * 60)

    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    for test_name, result in results.items():
        status = f"{GREEN}✓{RESET}" if result else f"{RED}✗{RESET}"
        print(f"{status} {test_name}")

    print()
    print(f"Score: {success_count}/{total_count}")
    print()

    if success_count == total_count:
        print(f"{GREEN}✅ Tous les tests passent ! Vous pouvez lancer le serveur.{RESET}")
        print()
        print("Commandes suivantes:")
        print("  python server.py")
        return 0

    else:
        print(f"{RED}❌ Certains tests échouent. Veuillez corriger les erreurs.{RESET}")
        print()
        print("Actions suggérées:")

        if not results["Dépendances Python"]:
            print("  pip install -r requirements.txt")

        if not results["FFmpeg"]:
            print("  sudo apt-get install ffmpeg")

        if not results["Fichier .env"]:
            print("  cp .env.example .env")
            print("  nano .env  # Éditer avec vos clés API")

        if not results["Répertoires"]:
            print("  mkdir -p assets/cache logs/calls")

        if not results["Cache audio"]:
            print("  python generate_cache.py")

        return 1


if __name__ == "__main__":
    sys.exit(main())

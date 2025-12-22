#!/usr/bin/env python3
"""
Script de conversion batch des logs audio RAW vers MP3
À exécuter la nuit via un cron job pour économiser le CPU

Usage:
    python convert_logs.py [--delete-raw] [--bitrate 64k]

Options:
    --delete-raw    Supprimer les fichiers .raw après conversion
    --bitrate       Bitrate MP3 (défaut: 64k)
"""
import sys
import argparse
import logging
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Tuple
import config
from audio_utils import convert_raw_to_mp3

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_raw_files(directory: Path) -> List[Path]:
    """
    Trouve tous les fichiers .raw dans un répertoire

    Args:
        directory: Répertoire à scanner

    Returns:
        Liste des chemins de fichiers .raw
    """
    raw_files = list(directory.glob("**/*.raw"))
    return raw_files


def convert_single_file(
    raw_path: Path,
    bitrate: str,
    delete_raw: bool
) -> Tuple[bool, str, str]:
    """
    Convertit un fichier RAW en MP3

    Args:
        raw_path: Chemin du fichier .raw
        bitrate: Bitrate MP3
        delete_raw: Supprimer le .raw après conversion

    Returns:
        (success, raw_filename, message)
    """
    try:
        # Générer le chemin de sortie
        mp3_path = raw_path.with_suffix('.mp3')

        # Vérifier si le MP3 existe déjà
        if mp3_path.exists():
            logger.debug(f"Skipping {raw_path.name} (MP3 exists)")
            return (True, raw_path.name, "Already converted")

        # Convertir
        success = convert_raw_to_mp3(
            raw_audio_path=str(raw_path),
            output_path=str(mp3_path),
            sample_rate=config.SAMPLE_RATE_ASTERISK,
            channels=config.CHANNELS,
            sample_width=config.SAMPLE_WIDTH,
            bitrate=bitrate
        )

        if not success:
            return (False, raw_path.name, "Conversion failed")

        # Supprimer le .raw si demandé
        if delete_raw:
            try:
                raw_path.unlink()
                logger.debug(f"Deleted {raw_path.name}")
            except Exception as e:
                logger.warning(f"Failed to delete {raw_path.name}: {e}")

        return (True, raw_path.name, "Converted")

    except Exception as e:
        return (False, raw_path.name, str(e))


def main():
    """Point d'entrée principal"""
    # Parser les arguments
    parser = argparse.ArgumentParser(
        description="Convertit les logs audio RAW en MP3"
    )
    parser.add_argument(
        '--delete-raw',
        action='store_true',
        help='Supprimer les fichiers .raw après conversion'
    )
    parser.add_argument(
        '--bitrate',
        type=str,
        default='64k',
        help='Bitrate MP3 (défaut: 64k)'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=config.PROCESS_POOL_WORKERS,
        help=f'Nombre de workers (défaut: {config.PROCESS_POOL_WORKERS})'
    )
    parser.add_argument(
        '--directory',
        type=str,
        default=str(config.LOGS_DIR),
        help=f'Répertoire des logs (défaut: {config.LOGS_DIR})'
    )

    args = parser.parse_args()

    # Vérifier le répertoire
    log_directory = Path(args.directory)
    if not log_directory.exists():
        logger.error(f"Directory not found: {log_directory}")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("🎵 Conversion RAW -> MP3")
    logger.info("=" * 60)
    logger.info(f"Directory: {log_directory}")
    logger.info(f"Bitrate: {args.bitrate}")
    logger.info(f"Workers: {args.workers}")
    logger.info(f"Delete RAW: {args.delete_raw}")
    logger.info("")

    # Trouver tous les fichiers .raw
    raw_files = find_raw_files(log_directory)

    if not raw_files:
        logger.info("No .raw files found")
        return 0

    logger.info(f"Found {len(raw_files)} .raw file(s)")
    logger.info("")

    # Convertir en parallèle
    success_count = 0
    error_count = 0
    skip_count = 0

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        # Soumettre tous les jobs
        futures = {
            executor.submit(
                convert_single_file,
                raw_path,
                args.bitrate,
                args.delete_raw
            ): raw_path
            for raw_path in raw_files
        }

        # Attendre les résultats
        for future in as_completed(futures):
            raw_path = futures[future]

            try:
                success, filename, message = future.result()

                if success:
                    if message == "Already converted":
                        skip_count += 1
                        logger.info(f"⊘ {filename} (skip)")
                    else:
                        success_count += 1
                        logger.info(f"✓ {filename}")
                else:
                    error_count += 1
                    logger.error(f"✗ {filename}: {message}")

            except Exception as e:
                error_count += 1
                logger.error(f"✗ {raw_path.name}: {e}")

    # Résumé
    logger.info("")
    logger.info("=" * 60)
    logger.info("📊 Résumé")
    logger.info("=" * 60)
    logger.info(f"Total: {len(raw_files)} fichiers")
    logger.info(f"✓ Convertis: {success_count}")
    logger.info(f"⊘ Déjà convertis: {skip_count}")
    logger.info(f"✗ Erreurs: {error_count}")
    logger.info("")

    if error_count > 0:
        logger.warning("⚠️  Certains fichiers n'ont pas pu être convertis")
        return 1
    else:
        logger.info("✅ Conversion terminée avec succès !")
        return 0


if __name__ == "__main__":
    sys.exit(main())

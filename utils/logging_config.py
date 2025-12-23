"""
Configuration centralisée du logging
Support pour logs structurés et JSON
"""
import logging
import sys
from pathlib import Path
from typing import Optional

from config.settings import LOG_LEVEL, STRUCTURED_LOGGING, LOG_FORMAT_JSON


def setup_logging(
    name: Optional[str] = None,
    level: Optional[str] = None,
    log_file: Optional[Path] = None
) -> logging.Logger:
    """
    Configure le logger pour l'application

    Args:
        name: Nom du logger (None = root logger)
        level: Niveau de log (DEBUG, INFO, WARNING, ERROR)
        log_file: Fichier de log optionnel

    Returns:
        Logger configuré
    """
    logger = logging.getLogger(name)

    # Éviter les doublons si déjà configuré
    if logger.handlers:
        return logger

    log_level = getattr(logging, level or LOG_LEVEL, logging.INFO)
    logger.setLevel(log_level)

    # Format
    if LOG_FORMAT_JSON:
        # Format JSON structuré (pour outils comme ELK, Splunk)
        formatter = JsonFormatter()
    elif STRUCTURED_LOGGING:
        # Format structuré lisible
        formatter = logging.Formatter(
            fmt='%(asctime)s - [%(name)s] - %(levelname)s - [%(call_id)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        # Format simple
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler optionnel
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


class JsonFormatter(logging.Formatter):
    """
    Formatter JSON pour logs structurés
    """
    def format(self, record: logging.LogRecord) -> str:
        import json
        from datetime import datetime

        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Ajouter call_id si disponible
        if hasattr(record, 'call_id'):
            log_data['call_id'] = record.call_id

        # Ajouter exception si présente
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Ajouter extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                          'levelname', 'levelno', 'lineno', 'module', 'msecs',
                          'message', 'pathname', 'process', 'processName',
                          'relativeCreated', 'thread', 'threadName', 'exc_info',
                          'exc_text', 'stack_info']:
                log_data[key] = value

        return json.dumps(log_data)


class CallLoggerAdapter(logging.LoggerAdapter):
    """
    Adapter pour ajouter automatiquement le call_id aux logs
    """
    def process(self, msg, kwargs):
        # Ajouter call_id comme extra field
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        kwargs['extra']['call_id'] = self.extra.get('call_id', 'unknown')
        return msg, kwargs


def get_call_logger(logger_name: str, call_id: str) -> CallLoggerAdapter:
    """
    Crée un logger avec call_id automatique

    Args:
        logger_name: Nom du logger
        call_id: ID de l'appel

    Returns:
        Logger avec call_id dans chaque message
    """
    base_logger = logging.getLogger(logger_name)
    return CallLoggerAdapter(base_logger, {'call_id': call_id})

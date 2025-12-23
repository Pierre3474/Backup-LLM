"""
Fonctions de validation (email, téléphone, etc.)
"""
import re
from typing import Optional


def clean_email_text(text: str) -> str:
    """
    Nettoie une transcription d'email vocale
    Convertit "jean point dupont arobase gmail point com" → "jean.dupont@gmail.com"

    Args:
        text: Transcription vocale brute

    Returns:
        Email formaté ou texte original si invalide
    """
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


def is_valid_email(email: str) -> bool:
    """
    Valide le format d'un email

    Args:
        email: Adresse email à valider

    Returns:
        True si valide, False sinon
    """
    if not email:
        return False

    pattern = r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
    return bool(re.match(pattern, email.lower()))


def clean_phone_number(phone: str) -> str:
    """
    Nettoie un numéro de téléphone

    Args:
        phone: Numéro brut

    Returns:
        Numéro nettoyé (chiffres uniquement)
    """
    if not phone:
        return ""

    # Garder uniquement les chiffres et le +
    cleaned = re.sub(r'[^\d+]', '', phone)

    # Supprimer le + initial si présent
    if cleaned.startswith('+'):
        cleaned = cleaned[1:]

    return cleaned


def is_valid_french_phone(phone: str) -> bool:
    """
    Valide un numéro de téléphone français

    Args:
        phone: Numéro à valider

    Returns:
        True si format français valide (10 chiffres commençant par 0)
    """
    cleaned = clean_phone_number(phone)

    # Format français: 10 chiffres commençant par 0
    if len(cleaned) == 10 and cleaned.startswith('0'):
        return True

    # Format international français: 11 chiffres commençant par 33
    if len(cleaned) == 11 and cleaned.startswith('33'):
        return True

    return False


def extract_yes_no(text: str) -> Optional[bool]:
    """
    Extrait une réponse Oui/Non depuis un texte
    Utilise des mots-clés simples (fallback si LLM intent échoue)

    Args:
        text: Texte à analyser

    Returns:
        True (oui), False (non), None (unclear)
    """
    text_lower = text.lower()

    # Mots-clés positifs
    yes_keywords = ['oui', 'ouais', 'ok', 'd\'accord', 'exact', 'exactement',
                    'tout à fait', 'bien sûr', 'affirmatif', 'correct']

    # Mots-clés négatifs
    no_keywords = ['non', 'pas du tout', 'jamais', 'négatif', 'aucunement']

    # Compter les matches
    yes_count = sum(1 for kw in yes_keywords if kw in text_lower)
    no_count = sum(1 for kw in no_keywords if kw in text_lower)

    if yes_count > no_count:
        return True
    elif no_count > yes_count:
        return False
    else:
        return None  # Ambigu


def detect_negative_sentiment(text: str, keywords: list) -> int:
    """
    Détecte les mots négatifs dans un texte

    Args:
        text: Texte à analyser
        keywords: Liste de mots-clés négatifs

    Returns:
        Nombre de mots négatifs détectés
    """
    text_lower = text.lower()
    return sum(1 for keyword in keywords if keyword in text_lower)


def is_off_topic_sentence(text: str) -> bool:
    """
    Détecte les phrases hors sujet (conversation avec quelqu'un d'autre)

    Args:
        text: Phrase à analyser

    Returns:
        True si probablement hors sujet
    """
    text_lower = text.lower()

    # Patterns de conversation avec tierce personne
    off_topic_patterns = [
        r'(range|rangez)\s+(le|la|les)',  # "range le lait"
        r'(tais-toi|silence)\s+',         # "tais-toi le chien"
        r'(passe|passes)-moi\s+',         # "passe-moi le sel"
        r'(attends|attendez)\s+(une|un)\s+seconde',  # Mais peut être adressé au bot
        r'(chut|chuuut)',
        r'\b(chéri|chérie|maman|papa|jacqueline)\b',  # Prénoms
    ]

    for pattern in off_topic_patterns:
        if re.search(pattern, text_lower):
            return True

    return False

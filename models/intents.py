"""
Modèles d'intentions pour l'analyse LLM structurée (JSON)
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any
import json


class IntentType(Enum):
    """Types d'intentions possibles"""
    # Confirmations
    YES = "yes"
    NO = "no"
    MAYBE = "maybe"

    # Actions
    PROBLEM_DESCRIPTION = "problem_description"
    IDENTITY_PROVIDED = "identity_provided"
    EMAIL_PROVIDED = "email_provided"

    # Problèmes
    INTERNET_ISSUE = "internet_issue"
    MOBILE_ISSUE = "mobile_issue"
    MODIFICATION_REQUEST = "modification_request"

    # États
    DEVICE_RESTARTED = "device_restarted"
    PROBLEM_RESOLVED = "problem_resolved"
    PROBLEM_PERSISTS = "problem_persists"

    # Transfert
    REQUEST_TECHNICIAN = "request_technician"

    # Hors sujet
    OFF_TOPIC = "off_topic"
    UNCLEAR = "unclear"
    NO_RESPONSE = "no_response"


class ConfidenceLevel(Enum):
    """Niveaux de confiance pour l'analyse"""
    HIGH = "high"      # > 0.8
    MEDIUM = "medium"  # 0.5 - 0.8
    LOW = "low"        # < 0.5


@dataclass
class Intent:
    """
    Résultat de l'analyse d'intention
    Structure attendue du LLM en JSON
    """
    intent_type: IntentType
    confidence: float  # 0.0 à 1.0
    extracted_value: Optional[Any] = None
    is_off_topic: bool = False
    requires_clarification: bool = False
    reasoning: Optional[str] = None  # Pour debug

    @classmethod
    def from_json(cls, json_str: str) -> 'Intent':
        """
        Crée un Intent depuis une chaîne JSON
        Format attendu:
        {
            "intent": "yes",
            "confidence": 0.95,
            "extracted_value": null,
            "is_off_topic": false,
            "requires_clarification": false,
            "reasoning": "L'utilisateur a clairement dit oui"
        }
        """
        try:
            data = json.loads(json_str)

            intent_type = IntentType(data.get("intent", "unclear"))
            confidence = float(data.get("confidence", 0.0))
            extracted_value = data.get("extracted_value")
            is_off_topic = bool(data.get("is_off_topic", False))
            requires_clarification = bool(data.get("requires_clarification", False))
            reasoning = data.get("reasoning")

            return cls(
                intent_type=intent_type,
                confidence=confidence,
                extracted_value=extracted_value,
                is_off_topic=is_off_topic,
                requires_clarification=requires_clarification,
                reasoning=reasoning
            )
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            # Fallback en cas d'erreur de parsing
            return cls(
                intent_type=IntentType.UNCLEAR,
                confidence=0.0,
                is_off_topic=False,
                requires_clarification=True,
                reasoning=f"Erreur parsing JSON: {str(e)}"
            )

    def get_confidence_level(self) -> ConfidenceLevel:
        """Retourne le niveau de confiance"""
        if self.confidence > 0.8:
            return ConfidenceLevel.HIGH
        elif self.confidence > 0.5:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    def is_confirmation(self) -> bool:
        """Vérifie si c'est une confirmation (oui/non)"""
        return self.intent_type in [IntentType.YES, IntentType.NO]

    def is_yes(self) -> bool:
        """Vérifie si c'est un oui avec confiance suffisante"""
        return self.intent_type == IntentType.YES and self.confidence > 0.6

    def is_no(self) -> bool:
        """Vérifie si c'est un non avec confiance suffisante"""
        return self.intent_type == IntentType.NO and self.confidence > 0.6

    def to_dict(self) -> dict:
        """Convertit en dictionnaire pour logging"""
        return {
            "intent": self.intent_type.value,
            "confidence": self.confidence,
            "confidence_level": self.get_confidence_level().value,
            "extracted_value": self.extracted_value,
            "is_off_topic": self.is_off_topic,
            "requires_clarification": self.requires_clarification,
            "reasoning": self.reasoning
        }


# Prompts JSON pour différents contextes
INTENT_PROMPTS = {
    "yes_no": """Analyse cette réponse utilisateur et retourne un JSON:
{
  "intent": "yes" | "no" | "unclear",
  "confidence": 0.0-1.0,
  "extracted_value": null,
  "is_off_topic": false/true,
  "requires_clarification": false/true,
  "reasoning": "explication courte"
}

Réponse utilisateur: "{user_text}"

Critères:
- "yes" si: oui, ok, d'accord, exactement, tout à fait, bien sûr
- "no" si: non, pas du tout, jamais
- "unclear" si: réponse ambiguë ou hors sujet
- is_off_topic = true si parle à quelqu'un d'autre
- requires_clarification = true si confiance < 0.6
""",

    "problem_type": """Analyse le problème mentionné et retourne un JSON:
{
  "intent": "internet_issue" | "mobile_issue" | "modification_request" | "unclear",
  "confidence": 0.0-1.0,
  "extracted_value": "description courte du problème",
  "is_off_topic": false/true,
  "requires_clarification": false/true,
  "reasoning": "explication"
}

Utilisateur: "{user_text}"

Critères:
- "internet_issue": box, wifi, connexion internet, réseau
- "mobile_issue": téléphone, mobile, appels, SMS
- "modification_request": changer, modifier, ajouter
""",

    "email": """Extrait l'email de cette transcription et retourne un JSON:
{
  "intent": "email_provided",
  "confidence": 0.0-1.0,
  "extracted_value": "email@example.com",
  "is_off_topic": false,
  "requires_clarification": false/true,
  "reasoning": "explication"
}

Utilisateur: "{user_text}"

Instructions:
- Convertis "arobase"/"at"/"chez" → @
- Convertis "point"/"dot" → .
- Extrait le format email standard
- requires_clarification = true si email invalide
""",

    "identity": """Extrait les informations d'identité et retourne un JSON:
{
  "intent": "identity_provided",
  "confidence": 0.0-1.0,
  "extracted_value": {
    "name": "prénom nom" ou null,
    "company": "entreprise" ou null
  },
  "is_off_topic": false/true,
  "requires_clarification": false/true,
  "reasoning": "explication"
}

Utilisateur: "{user_text}"
"""
}

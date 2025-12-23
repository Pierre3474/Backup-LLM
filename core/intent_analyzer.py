"""
Analyseur d'intentions - Utilise le LLM pour analyser les intentions utilisateur
Retourne des structures JSON au lieu de simples mots-clés
"""
import logging
from typing import Optional

from models.intents import Intent, IntentType, INTENT_PROMPTS
from models.conversation import ConversationContext
from services.llm import LLMService
from utils.validation import extract_yes_no, is_off_topic_sentence, detect_negative_sentiment
from config.settings import SENTIMENT_NEGATIVE_KEYWORDS

logger = logging.getLogger(__name__)


class IntentAnalyzer:
    """
    Analyse intelligente des intentions utilisateur
    Utilise le LLM pour retourner des structures JSON au lieu de mots-clés
    """

    def __init__(self, call_id: str, llm_service: LLMService):
        self.call_id = call_id
        self.llm = llm_service

    async def analyze_yes_no(self, user_text: str, context: ConversationContext) -> Intent:
        """
        Analyse une réponse Oui/Non avec le LLM

        Args:
            user_text: Texte utilisateur
            context: Contexte de conversation

        Returns:
            Intent avec type YES, NO ou UNCLEAR
        """
        try:
            # Vérifier si off-topic d'abord (rapide)
            if is_off_topic_sentence(user_text):
                logger.info(f"[{self.call_id}] Phrase hors-sujet détectée: '{user_text}'")
                return Intent(
                    intent_type=IntentType.OFF_TOPIC,
                    confidence=0.9,
                    is_off_topic=True,
                    requires_clarification=True,
                    reasoning="Conversation avec tierce personne détectée"
                )

            # Utiliser le LLM pour analyse fine
            prompt = INTENT_PROMPTS["yes_no"]
            json_response = await self.llm.analyze_intent_json(user_text, prompt)

            intent = Intent.from_json(json_response)

            logger.info(f"[{self.call_id}] Intent yes/no: {intent.intent_type.value} "
                       f"(confidence: {intent.confidence:.2f})")

            return intent

        except Exception as e:
            logger.error(f"[{self.call_id}] Erreur analyse yes/no: {e}")
            # Fallback sur méthode simple
            result = extract_yes_no(user_text)
            if result is True:
                return Intent(IntentType.YES, 0.6)
            elif result is False:
                return Intent(IntentType.NO, 0.6)
            else:
                return Intent(IntentType.UNCLEAR, 0.3, requires_clarification=True)

    async def analyze_problem_type(self, user_text: str) -> Intent:
        """
        Analyse le type de problème (Internet, Mobile, Modification)

        Args:
            user_text: Description du problème

        Returns:
            Intent avec type INTERNET_ISSUE, MOBILE_ISSUE, MODIFICATION_REQUEST ou UNCLEAR
        """
        try:
            prompt = INTENT_PROMPTS["problem_type"]
            json_response = await self.llm.analyze_intent_json(user_text, prompt)

            intent = Intent.from_json(json_response)

            logger.info(f"[{self.call_id}] Type problème: {intent.intent_type.value} "
                       f"(confidence: {intent.confidence:.2f})")

            return intent

        except Exception as e:
            logger.error(f"[{self.call_id}] Erreur analyse problème: {e}")
            # Fallback sur mots-clés simples
            text_lower = user_text.lower()

            if any(kw in text_lower for kw in ["internet", "wifi", "box", "connexion", "réseau"]):
                return Intent(IntentType.INTERNET_ISSUE, 0.7, extracted_value=user_text)
            elif any(kw in text_lower for kw in ["mobile", "téléphone", "appel", "sms"]):
                return Intent(IntentType.MOBILE_ISSUE, 0.7, extracted_value=user_text)
            elif any(kw in text_lower for kw in ["modifier", "changer", "ajouter"]):
                return Intent(IntentType.MODIFICATION_REQUEST, 0.7, extracted_value=user_text)
            else:
                return Intent(IntentType.UNCLEAR, 0.3, requires_clarification=True)

    async def analyze_email(self, user_text: str) -> Intent:
        """
        Extrait et valide un email

        Args:
            user_text: Transcription vocale contenant l'email

        Returns:
            Intent avec extracted_value = email formaté ou None
        """
        try:
            prompt = INTENT_PROMPTS["email"]
            json_response = await self.llm.analyze_intent_json(user_text, prompt)

            intent = Intent.from_json(json_response)

            logger.info(f"[{self.call_id}] Email extrait: {intent.extracted_value} "
                       f"(confidence: {intent.confidence:.2f})")

            return intent

        except Exception as e:
            logger.error(f"[{self.call_id}] Erreur analyse email: {e}")
            # Fallback sur validation simple
            from utils.validation import clean_email_text, is_valid_email

            cleaned = clean_email_text(user_text)
            if is_valid_email(cleaned):
                return Intent(IntentType.EMAIL_PROVIDED, 0.8, extracted_value=cleaned)
            else:
                return Intent(IntentType.EMAIL_PROVIDED, 0.3,
                            extracted_value=cleaned, requires_clarification=True)

    async def analyze_identity(self, user_text: str) -> Intent:
        """
        Extrait nom/prénom et entreprise

        Args:
            user_text: Texte contenant l'identité

        Returns:
            Intent avec extracted_value = {"name": str, "company": str}
        """
        try:
            prompt = INTENT_PROMPTS["identity"]
            json_response = await self.llm.analyze_intent_json(user_text, prompt)

            intent = Intent.from_json(json_response)

            logger.info(f"[{self.call_id}] Identité extraite: {intent.extracted_value}")

            return intent

        except Exception as e:
            logger.error(f"[{self.call_id}] Erreur analyse identité: {e}")
            return Intent(IntentType.IDENTITY_PROVIDED, 0.5,
                        extracted_value={"name": user_text, "company": None},
                        requires_clarification=True)

    def analyze_sentiment(self, user_text: str, context: ConversationContext) -> bool:
        """
        Analyse le sentiment (détection colère/frustration)

        Args:
            user_text: Texte à analyser
            context: Contexte pour mise à jour du compteur

        Returns:
            True si seuil de colère atteint (→ transfert immédiat)
        """
        negative_count = detect_negative_sentiment(user_text, SENTIMENT_NEGATIVE_KEYWORDS)

        if negative_count > 0:
            context.negative_sentiment_count += negative_count
            logger.warning(f"[{self.call_id}] Mots négatifs détectés: +{negative_count} "
                         f"(total: {context.negative_sentiment_count})")

            from config.settings import SENTIMENT_ANGER_THRESHOLD
            if context.negative_sentiment_count >= SENTIMENT_ANGER_THRESHOLD:
                logger.warning(f"[{self.call_id}] SEUIL DE COLÈRE ATTEINT → Transfert immédiat")
                return True

        return False

    async def requires_human_escalation(self, context: ConversationContext) -> bool:
        """
        Détermine si l'escalade vers un humain est nécessaire

        Args:
            context: Contexte de conversation

        Returns:
            True si transfert technicien recommandé
        """
        # Critères d'escalade
        escalation_reasons = []

        # 1. Trop de tentatives de clarification
        if context.clarification_attempts >= 2:
            escalation_reasons.append("trop de clarifications")

        # 2. Trop de tentatives de confirmation
        if context.confirmation_attempts >= 3:
            escalation_reasons.append("trop de confirmations")

        # 3. Sentiment négatif élevé
        from config.settings import SENTIMENT_ANGER_THRESHOLD
        if context.negative_sentiment_count >= SENTIMENT_ANGER_THRESHOLD:
            escalation_reasons.append("client frustré/en colère")

        # 4. Problème complexe (à implémenter selon business logic)
        # if context.metadata.get('complex_issue'):
        #     escalation_reasons.append("problème complexe")

        if escalation_reasons:
            logger.info(f"[{self.call_id}] Escalade recommandée: {', '.join(escalation_reasons)}")
            return True

        return False

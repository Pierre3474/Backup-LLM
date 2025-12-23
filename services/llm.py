"""
Service LLM (Large Language Model) - Groq
Gestion des prompts, historique de conversation, et génération de réponses
"""
import logging
import time
from typing import List, Dict, Optional
import yaml

from groq import Groq

from config.settings import (
    GROQ_API_KEY,
    GROQ_MODEL,
    GROQ_TEMPERATURE,
    GROQ_MAX_TOKENS,
    INTENT_ANALYSIS_MODEL,
    INTENT_ANALYSIS_TEMPERATURE,
    INTENT_ANALYSIS_MAX_TOKENS,
    BASE_DIR,
    PROMPTS_PATH
)

logger = logging.getLogger(__name__)


class LLMService:
    """
    Service de génération de réponses via LLM (Groq)
    Gère les prompts système, l'historique, et les appels API
    """

    def __init__(self, call_id: str):
        self.call_id = call_id
        self.client = Groq(api_key=GROQ_API_KEY)
        self.prompts_config = self._load_prompts()

    def _load_prompts(self) -> Dict:
        """Charge les prompts depuis prompts.yaml"""
        prompts_file = BASE_DIR / PROMPTS_PATH

        if not prompts_file.exists():
            logger.warning(f"[{self.call_id}] Fichier prompts introuvable: {prompts_file}")
            return {}

        try:
            with open(prompts_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"[{self.call_id}] Erreur chargement prompts: {e}")
            return {}

    def build_system_prompt(
        self,
        client_info: Optional[Dict] = None,
        client_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Construit le prompt système complet

        Args:
            client_info: Informations client (nom, équipement, etc.)
            client_history: Historique des tickets

        Returns:
            Prompt système formaté
        """
        # Base prompt depuis YAML
        base_prompt = self.prompts_config.get("system_prompt_base", "")

        if not base_prompt:
            # Fallback si YAML manquant
            base_prompt = (
                "Tu es l'assistant vocal du SAV Wouippleul. "
                "Réponds en 1-2 phrases maximum. Guide le client, ne résous pas."
            )

        # Ajouter infos client si disponibles
        if client_info:
            client_section = (
                f"\n\nCLIENT RECONNU: {client_info.get('first_name')} {client_info.get('last_name')} "
                f"(Équipement: {client_info.get('box_model')})."
            )
            base_prompt += client_section

        # Ajouter historique si disponible
        if client_history and len(client_history) > 0:
            history_section = f"\n\nHISTORIQUE CLIENT:\n"
            history_section += f"- {len(client_history)} appel(s) récent(s)\n"

            # Compter problèmes non résolus
            unresolved = [t for t in client_history if t.get('status') != 'resolved']
            if unresolved:
                history_section += f"- {len(unresolved)} problème(s) NON RÉSOLU(S) ⚠️\n"

            base_prompt += history_section

        return base_prompt

    async def generate_response(
        self,
        user_message: str,
        system_prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Génère une réponse du bot

        Args:
            user_message: Message de l'utilisateur
            system_prompt: Prompt système
            conversation_history: Historique récent (format: [{"role": "user/assistant", "content": "..."}])

        Returns:
            Réponse générée par le LLM
        """
        try:
            start_time = time.time()

            # Construire les messages
            messages = [{"role": "system", "content": system_prompt}]

            # Ajouter historique (limité aux 5 derniers)
            if conversation_history:
                messages.extend(conversation_history[-5:])

            # Ajouter message courant
            messages.append({"role": "user", "content": user_message})

            # Appel Groq
            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                temperature=GROQ_TEMPERATURE,
                max_tokens=GROQ_MAX_TOKENS
            )

            generated_text = response.choices[0].message.content.strip()
            latency = time.time() - start_time

            logger.info(f"[{self.call_id}] LLM response generated ({latency:.2f}s)")
            logger.debug(f"[{self.call_id}] Response: {generated_text[:100]}...")

            return generated_text

        except Exception as e:
            logger.error(f"[{self.call_id}] Erreur LLM: {e}", exc_info=True)
            return "Je suis désolé, j'ai rencontré un problème technique."

    async def analyze_intent_json(
        self,
        user_message: str,
        intent_prompt_template: str
    ) -> str:
        """
        Analyse l'intention de l'utilisateur et retourne un JSON structuré

        Args:
            user_message: Message de l'utilisateur
            intent_prompt_template: Template de prompt avec {user_text}

        Returns:
            JSON string (à parser avec Intent.from_json())
        """
        try:
            start_time = time.time()

            # Formater le prompt avec le message utilisateur
            prompt = intent_prompt_template.format(user_text=user_message)

            # Appel Groq avec température basse pour consistance
            response = self.client.chat.completions.create(
                model=INTENT_ANALYSIS_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=INTENT_ANALYSIS_TEMPERATURE,
                max_tokens=INTENT_ANALYSIS_MAX_TOKENS
            )

            json_response = response.choices[0].message.content.strip()
            latency = time.time() - start_time

            logger.info(f"[{self.call_id}] Intent analysis completed ({latency:.2f}s)")
            logger.debug(f"[{self.call_id}] Intent JSON: {json_response}")

            return json_response

        except Exception as e:
            logger.error(f"[{self.call_id}] Erreur analyse intent: {e}", exc_info=True)
            # Retourner un JSON fallback
            return '{"intent": "unclear", "confidence": 0.0, "requires_clarification": true}'

    def get_prompt_template(self, template_name: str) -> str:
        """
        Récupère un template de prompt depuis la config

        Args:
            template_name: Nom du template (ex: "CAPTURE_EMAIL")

        Returns:
            Template de prompt ou chaîne vide si absent
        """
        return self.prompts_config.get(template_name, "")

# Refactoring Architecture - Voicebot SAV Production-Ready

## 📋 Vue d'ensemble

Ce document explique la nouvelle architecture modulaire du voicebot, conçue pour être **maintenable, testable et production-ready**.

### Problèmes résolus

| Avant (Monolithe) | Après (Clean Architecture) |
|-------------------|----------------------------|
| 1 fichier de 1500+ lignes | Modules séparés ~200 lignes |
| If/elif imbriqués pour états | Machine à états déclarative |
| Prompts en dur dans le code | 100% externalisés dans YAML |
| Analyse par mots-clés | LLM → JSON structuré |
| Endpointing fixe (500ms) | Dynamique selon contexte |
| Difficile à tester | Modules indépendants testables |

---

## 🏗️ Architecture

```
voicebot_sav/
├── config/
│   ├── settings.py          # Configuration centralisée (hérite config.py)
│   └── prompts.yaml          # Prompts externalisés + intents JSON
│
├── models/
│   ├── conversation.py       # ConversationContext, ConversationState, ClientInfo
│   └── intents.py            # Intent, IntentType, prompts JSON
│
├── services/
│   ├── stt.py                # STTService (Deepgram, endpointing dynamique)
│   ├── llm.py                # LLMService (Groq, prompts, historique)
│   ├── tts.py                # TTSService (ElevenLabs, streaming, cache)
│   └── database.py           # DatabaseService (wrapper db_utils)
│
├── core/
│   ├── intent_analyzer.py    # IntentAnalyzer (LLM → JSON)
│   ├── state_machine.py      # StateMachine (transitions déclaratives)
│   └── call_handler.py       # CallHandler (orchestrateur)
│
├── utils/
│   ├── audio.py              # AudioCache (LRU dynamique)
│   ├── logging_config.py     # Logs structurés (JSON optionnel)
│   └── validation.py         # Validation email, phone, sentiment
│
└── main.py                   # Point d'entrée (serveur AudioSocket)
```

---

## 🎯 Concepts clés

### 1. **Endpointing Dynamique (STT)**

Au lieu d'un endpointing fixe (500ms), le système adapte automatiquement :

```python
# Réponse oui/non → 500ms (réactif)
stt_service.set_endpointing_mode("yes_no")

# Réponse ouverte → 1200ms (laisse temps de réfléchir)
stt_service.set_endpointing_mode("open")
```

**Configuration** : `config/settings.py`
```python
STT_ENDPOINTING_MODES = {
    "open": 1200,      # Pour questions ouvertes
    "yes_no": 500,     # Pour confirmations
    "quick": 500       # Pour réponses courtes
}
```

### 2. **Analyse d'Intention (LLM → JSON)**

Au lieu de mots-clés simples, le LLM retourne du JSON structuré :

```python
# Ancien (mots-clés)
if "oui" in user_text.lower():
    # Pas fiable si phrase complexe

# Nouveau (JSON structuré)
intent = await intent_analyzer.analyze_yes_no(user_text, context)
# Intent {
#   "intent": "yes",
#   "confidence": 0.95,
#   "is_off_topic": false,
#   "requires_clarification": false
# }

if intent.is_yes():
    # Fiable même avec phrase complexe
```

**Prompts** : `prompts.yaml` (section `INTENT_*`)

### 3. **Machine à États Déclarative**

Au lieu de if/elif imbriqués, transitions propres :

```python
# Ancien
if self.state == "VERIFICATION":
    if "oui" in text:
        self.state = "GOODBYE"
    else:
        self.state = "TRANSFER"

# Nouveau
state_machine.add_transition(
    StateTransition(
        from_state=ConversationState.VERIFICATION,
        to_state=ConversationState.GOODBYE,
        condition=lambda ctx, intent: intent.is_yes()
    )
)

new_state = await state_machine.process_intent(context, intent)
```

**Fichier** : `core/state_machine.py`

### 4. **Prompts 100% Externes**

Aucun prompt en dur dans le code Python :

```python
# Ancien
prompt = "Tu es un assistant vocal SAV. Réponds en 1-2 phrases..."

# Nouveau
prompt = llm_service.build_system_prompt(client_info, client_history)
# Charge depuis prompts.yaml avec variables dynamiques
```

**Configuration** : `prompts.yaml`

---

## 📚 Guide d'utilisation des modules

### Services

#### STTService (Speech-to-Text)

```python
from services.stt import STTService

stt = STTService(call_id="abc123")

# Callback pour transcriptions
async def on_transcript(text: str, is_final: bool):
    if is_final:
        print(f"Transcription finale: {text}")

# Démarrer
await stt.start(
    input_queue=audio_queue,
    on_transcript=on_transcript
)

# Changer mode dynamiquement
stt.set_endpointing_mode("yes_no")  # Court
stt.set_endpointing_mode("open")    # Long

# Arrêter proprement
await stt.stop()
```

#### LLMService (Génération réponses)

```python
from services.llm import LLMService

llm = LLMService(call_id="abc123")

# Construire prompt système
system_prompt = llm.build_system_prompt(
    client_info={"first_name": "Jean", "last_name": "Dupont"},
    client_history=[...]
)

# Générer réponse
response = await llm.generate_response(
    user_message="J'ai un problème avec ma box",
    system_prompt=system_prompt,
    conversation_history=[
        {"role": "assistant", "content": "Bonjour..."},
        {"role": "user", "content": "Bonjour"}
    ]
)

# Analyse intention (retour JSON)
json_response = await llm.analyze_intent_json(
    user_message="Oui exactement",
    intent_prompt_template=INTENT_PROMPTS["yes_no"]
)
```

#### TTSService (Synthèse vocale)

```python
from services.tts import TTSService
from utils.audio import AudioCache

cache = AudioCache()
tts = TTSService(call_id="abc123", audio_cache=cache)

# Générer audio (streaming)
async for chunk in tts.generate_audio("Bonjour, comment puis-je vous aider ?"):
    # Envoyer chunk (320 bytes = 20ms) à Asterisk
    await send_to_asterisk(chunk)

# Récupérer phrase pré-cachée
audio = tts.get_cached_phrase("welcome")
if audio:
    await send_to_asterisk(audio)
```

### Core

#### IntentAnalyzer

```python
from core.intent_analyzer import IntentAnalyzer
from models.conversation import ConversationContext

analyzer = IntentAnalyzer(call_id="abc123", llm_service=llm)
context = ConversationContext(call_id="abc123")

# Analyser oui/non
intent = await analyzer.analyze_yes_no("Oui c'est ça", context)
if intent.is_yes():
    print("Confirmation positive")

# Analyser type de problème
intent = await analyzer.analyze_problem_type("Ma box ne marche plus")
if intent.intent_type == IntentType.INTERNET_ISSUE:
    print(f"Problème internet détecté (confidence: {intent.confidence})")

# Analyser sentiment
needs_escalation = analyzer.analyze_sentiment("C'est inadmissible !", context)
if needs_escalation:
    print("Client en colère → Transfert immédiat")
```

#### StateMachine

```python
from core.state_machine import StateMachine
from models.conversation import ConversationState

sm = StateMachine(call_id="abc123")

# Traiter une intention
new_state = await sm.process_intent(context, intent)

# Obtenir le mode STT approprié
stt_mode = sm.get_stt_mode_for_state(context.current_state)
# "yes_no" pour VERIFICATION, "open" pour DIAGNOSTIC

# Vérifier les intentions attendues
expected = sm.get_expected_intent_types(ConversationState.VERIFICATION)
# [IntentType.YES, IntentType.NO]
```

---

## 🔄 Migration progressive

### Étape 1 : Utiliser les nouveaux services sans modifier server.py

```python
# Dans server.py existant, remplacer progressivement:

# Ancien
self.deepgram_client = DeepgramClient(config.DEEPGRAM_API_KEY)

# Nouveau
from services.stt import STTService
self.stt_service = STTService(self.call_id)
```

### Étape 2 : Adopter l'analyse d'intention

```python
# Ancien
if "oui" in user_text.lower():
    ...

# Nouveau
from core.intent_analyzer import IntentAnalyzer
intent = await self.intent_analyzer.analyze_yes_no(user_text, self.context)
if intent.is_yes():
    ...
```

### Étape 3 : Utiliser la state machine

```python
# Ancien
if self.state == "VERIFICATION":
    if "oui" in text:
        self.state = "GOODBYE"

# Nouveau
new_state = await self.state_machine.process_intent(self.context, intent)
if new_state:
    self.context.transition_to(new_state)
```

---

## 🧪 Tests

L'architecture modulaire facilite les tests unitaires :

```python
# tests/test_intent_analyzer.py
import pytest
from core.intent_analyzer import IntentAnalyzer

@pytest.mark.asyncio
async def test_yes_analysis():
    analyzer = IntentAnalyzer("test", mock_llm_service)
    intent = await analyzer.analyze_yes_no("Oui c'est ça", mock_context)

    assert intent.is_yes()
    assert intent.confidence > 0.8
```

---

## 📊 Avantages de la nouvelle architecture

### 1. **Maintenabilité**
- Chaque module a une responsabilité unique
- Facile de modifier un service sans casser le reste
- Prompts externalisés = modifications sans redéploiement code

### 2. **Testabilité**
- Services indépendants facilement mockables
- Tests unitaires par module
- State machine testable sans API externes

### 3. **Extensibilité**
- Ajouter un nouveau service (ex: Sentiment Analysis) = créer un fichier
- Nouveaux états = ajouter transitions dans state_machine
- Nouveaux intents = ajouter dans models/intents.py

### 4. **Performance**
- Endpointing dynamique réduit latence perçue
- Cache audio LRU optimisé
- Logging structuré pour monitoring

### 5. **Debugging**
- Logs structurés avec call_id automatique
- Intents avec reasoning pour comprendre décisions LLM
- State transitions tracées proprement

---

## ⚙️ Configuration

### Variables d'environnement (ajouts)

```bash
# Endpointing STT dynamique
STT_ENDPOINTING_DEFAULT=1200
STT_ENDPOINTING_SHORT=500

# Intent analysis
INTENT_ANALYSIS_MODEL=llama-3.3-70b-versatile
SENTIMENT_ANGER_THRESHOLD=3

# Cache
DYNAMIC_CACHE_MAX_SIZE=50

# Logging
STRUCTURED_LOGGING=true
LOG_FORMAT_JSON=false
```

### Fichiers de configuration

- `config/settings.py` : Hérite et étend `config.py`
- `prompts.yaml` : Tous les prompts système et intents
- `.env` : Variables sensibles (API keys)

---

## 🚀 Prochaines étapes

### Phase 1 : Migration server.py → CallHandler
- [ ] Créer `core/call_handler.py` utilisant les nouveaux services
- [ ] Migrer logique état par état
- [ ] Tests de non-régression

### Phase 2 : Optimisations
- [ ] Implémenter retry automatique sur erreurs API
- [ ] Métriques Prometheus détaillées par service
- [ ] Circuit breaker pour services externes

### Phase 3 : Fonctionnalités avancées
- [ ] Multi-langues via configuration
- [ ] A/B testing de prompts
- [ ] ML pour prédiction escalade

---

## 📖 Références

- Architecture: Clean Architecture (Uncle Bob)
- Patterns: State Machine, Strategy, Dependency Injection
- Logs: Structured Logging (12 Factor App)

---

**Auteur**: Refactoring Architecture
**Date**: 2025-12-23
**Version**: 1.0.0

# 🏗️ Architecture Technique - Voicebot SAV Wouippleul

## Vue d'Ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                         ASTERISK PBX                            │
│                    (Extension 777)                              │
└────────────────────┬────────────────────────────────────────────┘
                     │ AudioSocket (TCP)
                     │ 8kHz, 16-bit, Mono
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│               PYTHON ASYNCIO SERVER (uvloop)                    │
│                     server.py - Core 0                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              AudioSocket Handler                         │  │
│  │  • Handshake (16 bytes UUID)                            │  │
│  │  • Streaming bidirectionnel                             │  │
│  └───────┬──────────────────────────────────────────┬───────┘  │
│          │                                          │           │
│          ▼                                          ▼           │
│  ┌──────────────┐                          ┌──────────────┐    │
│  │ Input Queue  │                          │ Output Queue │    │
│  │ (asyncio)    │                          │   (deque)    │    │
│  └──────┬───────┘                          └───────▲──────┘    │
│         │                                          │            │
│         │                                          │            │
│  ┌──────▼──────────────────────────────────────────┴──────┐    │
│  │             CallHandler (Machine à États)             │    │
│  │                                                        │    │
│  │  States: INIT → WELCOME → IDENT → DIAG → SOLUTION    │    │
│  │          → VERIFICATION → TRANSFER/GOODBYE            │    │
│  │                                                        │    │
│  │  Features:                                             │    │
│  │  • Barge-in (interruption)                            │    │
│  │  • Timeout monitoring                                  │    │
│  │  • Audio logging (RAW)                                │    │
│  └───┬───────────────┬──────────────────┬────────────┘    │
│      │               │                  │                     │
│      ▼               ▼                  ▼                     │
│  ┌────────┐    ┌─────────┐      ┌────────────┐              │
│  │Deepgram│    │  Groq   │      │  OpenAI    │              │
│  │  STT   │    │   LLM   │      │    TTS     │              │
│  │ (nova) │    │(llama)  │      │  (tts-1)   │              │
│  └────────┘    └─────────┘      └──────┬─────┘              │
│                                         │                     │
│                                         ▼                     │
│                              ┌──────────────────┐             │
│                              │ ProcessPoolExecutor           │
│                              │  (Cores 1-3)     │             │
│                              │                  │             │
│                              │ audio_utils.py:  │             │
│                              │ • 24kHz → 8kHz   │             │
│                              │ • FFmpeg/pydub   │             │
│                              └──────────────────┘             │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 AudioCache (RAM)                         │  │
│  │  • welcome.raw (8kHz pré-généré)                        │  │
│  │  • goodbye.raw                                           │  │
│  │  • ok.raw, wait.raw, error.raw, etc.                    │  │
│  │  → Bypass CPU (envoi direct)                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Flux de Données Audio

### 1. Input (Asterisk → Python)

```
Asterisk (8kHz SLIN)
    ↓
AudioSocket TCP
    ↓
server.py: _audio_input_handler()
    ↓
Log to disk (RAW) ────────┐
    ↓                      │
input_queue (asyncio)      │
    ↓                      │
Deepgram WebSocket         │
    ↓                      │
Transcription → CallHandler│
                           │
                           ▼
                    logs/calls/call_xxx.raw
```

### 2. Output (Python → Asterisk)

```
CallHandler Decision
    │
    ├─→ Cache Hit (welcome, goodbye, etc.)
    │       ↓
    │   assets/cache/phrase.raw (8kHz)
    │       ↓
    │   Direct Send (NO CPU) ────┐
    │                            │
    └─→ Dynamic Speech           │
            ↓                    │
        OpenAI TTS API           │
            ↓                    │
        MP3 24kHz                │
            ↓                    │
        ProcessPoolExecutor      │
            ↓                    │
        convert_24khz_to_8khz()  │
        (FFmpeg/pydub)           │
            ↓                    │
        RAW 8kHz ────────────────┘
            ↓
        output_queue (deque)
            ↓
        _audio_output_handler()
            ↓
        AudioSocket TCP
            ↓
        Asterisk (Play to caller)
```

## Parallélisme et CPU

### Core 0 (Thread Principal - uvloop)
- **Responsabilité**: Réseau asyncio, orchestration
- **Charge**: Faible (I/O bound)
- **Tâches**:
  - Accepter connexions TCP
  - Gérer les WebSockets (Deepgram)
  - Appels API REST (Groq, OpenAI)
  - Gestion d'événements

### Cores 1-3 (ProcessPoolExecutor)
- **Responsabilité**: Conversions audio CPU-intensive
- **Charge**: Élevée (CPU bound)
- **Tâches**:
  - Conversion 24kHz → 8kHz (FFmpeg)
  - Batch conversion RAW → MP3 (nocturne)
  - Traitement audio (normalisation, resampling)

### Optimisation Clé
```python
# ✅ BON: Cache hit (pas de CPU)
audio = audio_cache.get("welcome")  # Lecture RAM
output_queue.append(audio)          # Envoi direct

# ❌ ÉVITÉ: Conversion en temps réel sur thread principal
# audio = convert_to_8khz(data)  # BLOQUERAIT uvloop !

# ✅ BON: Conversion dans ProcessPool
loop = asyncio.get_event_loop()
audio = await loop.run_in_executor(
    process_pool,
    convert_24khz_to_8khz,
    data_24khz
)
```

## Gestion des États

### Machine à États SAV Wouippleul

```python
class ConversationState(Enum):
    INIT = "init"
    WELCOME = "welcome"
    IDENTIFICATION = "identification"
    DIAGNOSTIC = "diagnostic"
    SOLUTION = "solution"
    VERIFICATION = "verification"
    TRANSFER = "transfer"
    GOODBYE = "goodbye"
    ERROR = "error"
```

### Transitions

```
INIT
  ↓
WELCOME (Cache: "Bonjour...")
  ↓ (user speaks)
IDENTIFICATION (LLM: ask name/phone)
  ↓ (user provides info)
DIAGNOSTIC (LLM: "Internet ou Mobile ?")
  ↓
  ├─→ Internet → SOLUTION ("Débrancher box...")
  └─→ Mobile → SOLUTION ("Redémarrer téléphone...")
      ↓
VERIFICATION ("Ça marche ?")
  ↓
  ├─→ OUI → GOODBYE (Cache: "Au revoir")
  └─→ NON → check_technician()
            ↓
            ├─→ Available → TRANSFER
            └─→ Unavailable → GOODBYE
```

## Gestion des Erreurs

### Stratégie Multi-Niveaux

```python
try:
    # Appel API (Deepgram/Groq/OpenAI)
    response = await api_call()

except TimeoutError:
    # Retry avec exponential backoff
    if retry_count < MAX_RETRIES:
        await asyncio.sleep(2 ** retry_count)
        retry()
    else:
        # Fallback: Message cache
        await self._say("wait")

except APIError as e:
    # Log l'erreur
    logger.error(f"API error: {e}")

    # Jouer message d'erreur
    await self._say("error")

    # Soft hangup
    self.is_active = False

except Exception as e:
    # Erreur critique
    logger.critical(f"Unhandled error: {e}", exc_info=True)

    # Cleanup et hangup
    await self._cleanup()
```

### Points de Défaillance et Mitigations

| Composant | Risque | Mitigation |
|-----------|--------|------------|
| Deepgram WebSocket | Déconnexion | Reconnexion auto + buffer |
| Groq API | Rate limit | Queue + retry backoff |
| OpenAI TTS | Timeout | Cache fallback + retry |
| FFmpeg conversion | Crash | Process isolation (Pool) |
| AudioSocket | Fermeture | Graceful cleanup |

## Performance

### Métriques Cibles

- **Latence STT**: < 300ms (Deepgram streaming)
- **Latence LLM**: < 500ms (Groq streaming)
- **Latence TTS**: < 800ms (OpenAI + conversion)
- **Latence Cache**: < 50ms (RAM direct)
- **Throughput**: 20 appels simultanés @ 4 vCPU

### Profiling CPU

```bash
# Monitorer la charge par core
mpstat -P ALL 1

# Résultat attendu:
# Core 0: 30-40% (asyncio I/O)
# Core 1: 60-80% (conversion audio)
# Core 2: 60-80% (conversion audio)
# Core 3: 60-80% (conversion audio)
```

### Memory Footprint

```
Base: ~50 MB (Python + libs)
Cache: ~5 MB (8 phrases × 600 KB)
Per call: ~2 MB (buffers + state)

Total @ 20 calls: ~50 + 5 + (20 × 2) = 95 MB
```

## Sécurité

### Validation des Entrées

```python
# Handshake AudioSocket
uuid_bytes = await reader.read(16)
if len(uuid_bytes) != 16:
    # Rejeter connexion invalide
    writer.close()
    return

# Validation format audio
if not validate_audio_format(chunk):
    logger.warning("Invalid audio format")
    # Envoyer du silence
    chunk = generate_silence(20)
```

### Isolation

- **ProcessPool**: Crash d'un worker n'affecte pas les autres
- **Async Tasks**: Exception dans une tâche isolée
- **API Timeouts**: Évite le blocage infini

## Monitoring

### Logs Structurés

```python
logger.info(
    f"[{call_id}] State transition",
    extra={
        "call_id": call_id,
        "from_state": old_state,
        "to_state": new_state,
        "duration": time.time() - state_start
    }
)
```

### Métriques à Surveiller

1. **Taux d'erreur API** (> 5% = alerte)
2. **Latence moyenne** (> 1s = dégradation)
3. **Calls actifs** (= MAX_CONCURRENT = saturation)
4. **CPU usage** (> 90% = bottleneck)
5. **Conversion queue depth** (> 10 = surcharge)

## Évolution Future

### Scalabilité Horizontale

```
                    ┌──────────────┐
                    │Load Balancer │
                    │  (Asterisk)  │
                    └───────┬──────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │ Python VM 1  │ │ Python VM 2  │ │ Python VM 3  │
    │ (20 calls)   │ │ (20 calls)   │ │ (20 calls)   │
    └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
           │                │                │
           └────────────────┼────────────────┘
                            ▼
                    ┌──────────────┐
                    │ Redis Cache  │
                    │ (Shared)     │
                    └──────────────┘
```

### Optimisations Avancées

1. **GPU Inference**: TTS/STT local sur GPU
2. **Edge Computing**: Déploiement on-premise
3. **WebRTC**: Remplacer AudioSocket pour mobile
4. **Multi-langue**: Support i18n (Deepgram + prompts)

---

**Architecture optimisée pour 20 appels @ 4 vCPU avec latence < 1s** 🚀

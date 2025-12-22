# 📚 DOCUMENTATION TECHNIQUE COMPLÈTE
## Voicebot SAV Wouippleul - Guide de Référence

---

**Version** : 1.0.0
**Date** : 18 novembre 2025
**Auteur** : Expert Python/VoIP
**Public** : Développeurs, DevOps, Architectes

---

## 📖 TABLE DES MATIÈRES

### PARTIE 1 : INTRODUCTION
1. [Vue d'Ensemble](#1-vue-densemble)
2. [Glossaire Technique](#2-glossaire-technique)
3. [Prérequis](#3-prérequis)

### PARTIE 2 : ARCHITECTURE
4. [Architecture Globale](#4-architecture-globale)
5. [Protocole AudioSocket](#5-protocole-audiosocket)
6. [Machine à États](#6-machine-à-états)
7. [Flux de Données](#7-flux-de-données)

### PARTIE 3 : COMPOSANTS
8. [server.py - Serveur Principal](#8-serverpy---serveur-principal)
9. [config.py - Configuration](#9-configpy---configuration)
10. [audio_utils.py - Utilitaires Audio](#10-audio_utilspy---utilitaires-audio)
11. [Scripts Utilitaires](#11-scripts-utilitaires)

### PARTIE 4 : INTÉGRATIONS
12. [Intégration Deepgram (STT)](#12-intégration-deepgram-stt)
13. [Intégration Groq (LLM)](#13-intégration-groq-llm)
14. [Intégration OpenAI (TTS)](#14-intégration-openai-tts)

### PARTIE 5 : OPTIMISATIONS
15. [Performance CPU](#15-performance-cpu)
16. [Optimisation Mémoire](#16-optimisation-mémoire)
17. [Cache Audio](#17-cache-audio)
18. [Gestion Erreurs](#18-gestion-erreurs)

### PARTIE 6 : DÉPLOIEMENT
19. [Installation Développement](#19-installation-développement)
20. [Déploiement Production](#20-déploiement-production)
21. [Monitoring](#21-monitoring)
22. [Maintenance](#22-maintenance)

### PARTIE 7 : RÉFÉRENCE API
23. [API CallHandler](#23-api-callhandler)
24. [API AudioCache](#24-api-audiocache)
25. [API AudioUtils](#25-api-audioutils)

### PARTIE 8 : ANNEXES
26. [Troubleshooting](#26-troubleshooting)
27. [FAQ](#27-faq)
28. [Exemples de Code](#28-exemples-de-code)

---

# PARTIE 1 : INTRODUCTION

## 1. Vue d'Ensemble

### 1.1 Qu'est-ce que le Voicebot SAV Wouippleul ?

Le Voicebot SAV Wouippleul est un **système de réponse vocale interactive (IVR) intelligent** conçu pour automatiser le service après-vente. Il combine :

- **VoIP** : Asterisk PBX avec protocole AudioSocket
- **IA Conversationnelle** : Deepgram (STT) + Groq (LLM) + OpenAI (TTS)
- **Architecture Asyncio** : Python 3.11+ avec uvloop pour haute performance

**Objectif principal :** Gérer 20 appels téléphoniques simultanés sur un serveur modeste (4 vCPU) avec une latence < 1 seconde.

### 1.2 Cas d'Usage

**Scénario typique :**

```
Client : Appelle le 777
   ↓
Asterisk : Route vers AudioSocket (Python)
   ↓
Voicebot : "Bonjour, bienvenue au SAV Wouippleul"
   ↓
Client : "J'ai un problème avec mon internet"
   ↓
Voicebot : "Puis-je avoir votre nom et numéro ?"
   ↓
Client : "Pierre Dupont, 06 12 34 56 78"
   ↓
Voicebot : "Essayez de débrancher votre box 30 secondes"
   ↓
Client : (fait la manipulation)
   ↓
Voicebot : "Est-ce que ça marche ?"
   ↓
Client : "Oui, c'est bon !"
   ↓
Voicebot : "Merci, au revoir !"
```

**Résultat :**
- ✅ Problème résolu automatiquement
- ✅ Aucun agent humain mobilisé
- ✅ Durée : ~2 minutes
- ✅ Satisfaction client : Rapide et efficace

### 1.3 Architecture en 3 Couches

```
┌─────────────────────────────────────────────────────────┐
│              COUCHE 1 : TÉLÉPHONIE                      │
│                                                         │
│  Asterisk PBX                                           │
│  • Gestion appels SIP                                   │
│  • Routing vers extension 777                           │
│  • Conversion codec → SLIN 8kHz                         │
│                                                         │
└────────────────────┬────────────────────────────────────┘
                     │ AudioSocket TCP
                     │ (8kHz, 16-bit, Mono)
┌────────────────────▼────────────────────────────────────┐
│              COUCHE 2 : ORCHESTRATION                   │
│                                                         │
│  Python Server (uvloop + asyncio)                       │
│  • Gestion protocole AudioSocket                        │
│  • Machine à états conversationnelle                    │
│  • Cache audio RAM                                      │
│  • Logging + monitoring                                 │
│                                                         │
└─────────┬──────────────────────┬─────────────┬──────────┘
          │                      │             │
          │ WebSocket            │ HTTP        │ HTTP
          │                      │             │
┌─────────▼─────────┐  ┌─────────▼──────┐  ┌──▼─────────┐
│   COUCHE 3 : IA   │  │                │  │            │
│                   │  │                │  │            │
│  Deepgram         │  │  Groq          │  │  OpenAI    │
│  (STT)            │  │  (LLM)         │  │  (TTS)     │
│  nova-2-phonecall │  │  llama-3.1-70b │  │  tts-1     │
└───────────────────┘  └────────────────┘  └────────────┘
```

---

## 2. Glossaire Technique

| Terme | Définition |
|-------|------------|
| **AudioSocket** | Protocole Asterisk pour streaming audio bidirectionnel via TCP |
| **STT** | Speech-to-Text (Reconnaissance vocale) |
| **TTS** | Text-to-Speech (Synthèse vocale) |
| **LLM** | Large Language Model (Modèle de langage) |
| **uvloop** | Event loop ultra-rapide pour asyncio (basé sur libuv) |
| **ProcessPool** | Pool de processus pour exécution CPU-bound parallèle |
| **SLIN** | Signed Linear PCM (format audio brut non compressé) |
| **Barge-in** | Interruption du robot par l'utilisateur |
| **VAD** | Voice Activity Detection (Détection d'activité vocale) |
| **Handshake** | Échange initial de connexion (ici : UUID 16 bytes) |
| **Chunk** | Bloc audio (ici : 320 bytes = 20ms @ 8kHz) |

---

## 3. Prérequis

### 3.1 Matériel

**Configuration minimale :**
- CPU : 4 vCPU (x86_64)
- RAM : 2 GB
- Disque : 10 GB
- Réseau : 10 Mbps symétrique

**Configuration recommandée :**
- CPU : 8 vCPU
- RAM : 4 GB
- Disque : 50 GB SSD
- Réseau : 100 Mbps

### 3.2 Logiciel

**Système d'exploitation :**
- Ubuntu 22.04 LTS (recommandé)
- Debian 12
- CentOS Stream 9

**Dépendances système :**
```bash
# Ubuntu/Debian
sudo apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    ffmpeg \
    asterisk \
    git

# CentOS/RHEL
sudo dnf install -y \
    python3.11 \
    python3-pip \
    ffmpeg \
    asterisk \
    git
```

**Dépendances Python :**
```bash
pip install -r requirements.txt
```

### 3.3 Clés API

**Obligatoires :**
- **Deepgram** : https://console.deepgram.com (STT)
- **Groq** : https://console.groq.com (LLM)
- **OpenAI** : https://platform.openai.com (TTS)

**Coût estimé :**
- ~$0.034 par appel de 2 minutes
- ~$34 pour 1000 appels/mois

---

# PARTIE 2 : ARCHITECTURE

## 4. Architecture Globale

### 4.1 Diagramme de Composants

```
┌───────────────────────────────────────────────────────────────┐
│                        SERVEUR (4 vCPU)                       │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                    Core 0 (Thread Principal)            │ │
│  │                      uvloop Event Loop                  │ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │                                                         │ │
│  │  ┌───────────────────────────────────────────────────┐ │ │
│  │  │        AudioSocketServer                          │ │ │
│  │  │  • Écoute TCP :9090                               │ │ │
│  │  │  • Accepte connexions (max 20)                    │ │ │
│  │  │  • Crée CallHandler par appel                     │ │ │
│  │  └───────────────────────────────────────────────────┘ │ │
│  │                                                         │ │
│  │  ┌───────────────────────────────────────────────────┐ │ │
│  │  │        CallHandler (par appel)                    │ │ │
│  │  │                                                   │ │ │
│  │  │  Tâches parallèles (asyncio.create_task) :       │ │ │
│  │  │  ┌───────────────────────────────────────────┐   │ │ │
│  │  │  │ 1. _audio_input_handler()                 │   │ │ │
│  │  │  │    ├─ Lit AudioSocket (320 bytes/20ms)    │   │ │ │
│  │  │  │    ├─ Log RAW sur disque                  │   │ │ │
│  │  │  │    └─ → input_queue                       │   │ │ │
│  │  │  └───────────────────────────────────────────┘   │ │ │
│  │  │                                                   │ │ │
│  │  │  ┌───────────────────────────────────────────┐   │ │ │
│  │  │  │ 2. _audio_output_handler()                │   │ │ │
│  │  │  │    ├─ Lit output_queue                    │   │ │ │
│  │  │  │    └─ Écrit AudioSocket (320 bytes/20ms)  │   │ │ │
│  │  │  └───────────────────────────────────────────┘   │ │ │
│  │  │                                                   │ │ │
│  │  │  ┌───────────────────────────────────────────┐   │ │ │
│  │  │  │ 3. _deepgram_handler()                    │   │ │ │
│  │  │  │    ├─ Connexion WebSocket                 │   │ │ │
│  │  │  │    ├─ Stream audio → Deepgram             │   │ │ │
│  │  │  │    ├─ Reçoit transcriptions               │   │ │ │
│  │  │  │    └─ Détecte barge-in (VAD)              │   │ │ │
│  │  │  └───────────────────────────────────────────┘   │ │ │
│  │  │                                                   │ │ │
│  │  │  ┌───────────────────────────────────────────┐   │ │ │
│  │  │  │ 4. _conversation_handler()                │   │ │ │
│  │  │  │    └─ Machine à états (SAV Wouippleul)    │   │ │ │
│  │  │  └───────────────────────────────────────────┘   │ │ │
│  │  │                                                   │ │ │
│  │  │  ┌───────────────────────────────────────────┐   │ │ │
│  │  │  │ 5. _timeout_monitor()                     │   │ │ │
│  │  │  │    ├─ Silence utilisateur (8s → 15s)      │   │ │ │
│  │  │  │    └─ Durée max appel (10 min)            │   │ │ │
│  │  │  └───────────────────────────────────────────┘   │ │ │
│  │  │                                                   │ │ │
│  │  └───────────────────────────────────────────────────┘ │ │
│  │                                                         │ │
│  │  ┌───────────────────────────────────────────────────┐ │ │
│  │  │        AudioCache (Singleton)                     │ │ │
│  │  │  • Charge au démarrage : assets/cache/*.raw      │ │ │
│  │  │  • 8 phrases pré-générées en 8kHz                │ │ │
│  │  │  • Envoi direct (bypass CPU)                     │ │ │
│  │  └───────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Cores 1-3 (ProcessPoolExecutor)            │ │
│  │                                                         │ │
│  │  Worker 1: convert_24khz_to_8khz() [FFmpeg/pydub]      │ │
│  │  Worker 2: convert_24khz_to_8khz() [FFmpeg/pydub]      │ │
│  │  Worker 3: convert_24khz_to_8khz() [FFmpeg/pydub]      │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### 4.2 Séparation des Responsabilités

| Composant | Responsabilité | Thread/Process |
|-----------|----------------|----------------|
| **AudioSocketServer** | Accepter connexions TCP | Main thread (Core 0) |
| **CallHandler** | Orchestrer un appel | Main thread (asyncio) |
| **_audio_input_handler** | Lire audio Asterisk | Coroutine asyncio |
| **_audio_output_handler** | Écrire audio Asterisk | Coroutine asyncio |
| **_deepgram_handler** | STT streaming | Coroutine asyncio |
| **_conversation_handler** | Logique métier | Coroutine asyncio |
| **_timeout_monitor** | Surveiller timeouts | Coroutine asyncio |
| **AudioCache** | Servir cache RAM | Main thread (sync) |
| **ProcessPoolExecutor** | Conversions FFmpeg | Processes séparés (Cores 1-3) |

### 4.3 Flux de Vie d'un Appel

```
1. CLIENT COMPOSE LE 777
   ↓
2. ASTERISK ROUTE VERS AudioSocket (localhost:9090)
   ↓
3. PYTHON : AudioSocketServer.handle_client()
   ├─ Lecture handshake (16 bytes UUID)
   ├─ Validation
   └─ Création CallHandler
         ↓
4. CALLHANDLER : Démarrage 5 tâches parallèles
   ├─ _audio_input_handler()
   ├─ _audio_output_handler()
   ├─ _deepgram_handler()
   ├─ _conversation_handler()
   └─ _timeout_monitor()
         ↓
5. CONVERSATION
   ├─ Jouer "welcome" (cache)
   ├─ Écouter utilisateur (Deepgram STT)
   ├─ Analyser (Groq LLM)
   ├─ Répondre (OpenAI TTS → conversion → AudioSocket)
   └─ Boucle jusqu'à état GOODBYE
         ↓
6. FIN D'APPEL
   ├─ Annulation tâches
   ├─ Cleanup (fermer fichiers, connexions)
   └─ Libération ressources
         ↓
7. ASTERISK : Fin de communication
```

---

## 5. Protocole AudioSocket

### 5.1 Spécifications

**RFC Asterisk AudioSocket :**
- Transport : **TCP** (pas UDP)
- Format : **Signed Linear PCM** (SLIN)
- Sample rate : **8000 Hz**
- Sample width : **16-bit** (2 bytes)
- Channels : **1** (Mono)
- Endianness : **Little Endian**

**Calcul taille chunk :**
```
20ms @ 8kHz = 0.02 × 8000 = 160 samples
160 samples × 2 bytes = 320 bytes par chunk
```

### 5.2 Handshake

**À la connexion, Asterisk envoie :**

```
Offset  | Taille | Description
--------|--------|-------------
0-15    | 16 B   | UUID de l'appel (bytes bruts)
```

**Exemple de lecture (Python) :**

```python
async def handle_client(self, reader, writer):
    # Lire le handshake
    uuid_bytes = await reader.read(16)

    if len(uuid_bytes) != 16:
        logger.error("Invalid handshake")
        writer.close()
        return

    # Convertir en string hex
    call_id = uuid_bytes.hex()
    # Exemple : "40325ec8c2844c1fb8e5a0b64e492d60"

    logger.info(f"[{call_id}] New call")
```

### 5.3 Streaming Audio

**Après le handshake, streaming bidirectionnel :**

**INPUT (Asterisk → Python) :**
```python
while True:
    chunk = await reader.read(320)  # 20ms @ 8kHz
    if not chunk:
        break  # Connexion fermée

    # Traiter le chunk
    await process_audio(chunk)
```

**OUTPUT (Python → Asterisk) :**
```python
# Audio au format RAW 8kHz, 16-bit, Mono
audio_data = b'\x00\x01\x02...'  # 320 bytes

writer.write(audio_data)
await writer.drain()
```

### 5.4 Configuration Asterisk

**extensions.conf :**

```ini
[voicebot]
exten => 777,1,Answer()
    same => n,Verbose(1, "Call to Voicebot")
    ; AudioSocket(UUID, host:port)
    same => n,AudioSocket(40325ec8-c284-4c1f-b8e5-a0b64e492d60,localhost:9090)
    same => n,Verbose(1, "AudioSocket ended")
    same => n,Hangup()
```

**Paramètres AudioSocket() :**
- `UUID` : Identifiant unique (peut être dynamique via dialplan vars)
- `host:port` : Adresse du serveur Python

### 5.5 Gestion Déconnexion

**Asterisk ferme la connexion si :**
- Utilisateur raccroche
- Timeout réseau
- Erreur Asterisk

**Python détecte la fermeture :**

```python
chunk = await reader.read(320)
if not chunk:  # EOF
    logger.info(f"[{call_id}] Connection closed")
    self.is_active = False
```

**Cleanup :**

```python
async def _cleanup(self):
    # Fermer le writer
    try:
        self.writer.close()
        await self.writer.wait_closed()
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
```

---

## 6. Machine à États

### 6.1 Définition des États

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

### 6.2 Diagramme de Transitions

```
                    ┌──────┐
                    │ INIT │
                    └───┬──┘
                        │ start
                        ▼
                  ┌──────────┐
                  │ WELCOME  │ ("Bonjour, bienvenue...")
                  └─────┬────┘
                        │ user speaks
                        ▼
             ┌──────────────────┐
             │ IDENTIFICATION   │ ("Votre nom et tél ?")
             └────────┬─────────┘
                      │ info received
                      ▼
             ┌──────────────────┐
             │   DIAGNOSTIC     │ ("Internet ou Mobile ?")
             └────────┬─────────┘
                      │
           ┌──────────┴──────────┐
           │                     │
    "Internet"              "Mobile"
           │                     │
           ▼                     ▼
     ┌──────────┐          ┌──────────┐
     │ SOLUTION │          │ SOLUTION │
     │(Débrancher)        │(Redémarrer)│
     └────┬─────┘          └────┬─────┘
          │                     │
          └──────────┬──────────┘
                     │ wait 2s
                     ▼
            ┌────────────────┐
            │ VERIFICATION   │ ("Ça marche ?")
            └───────┬────────┘
                    │
         ┌──────────┴──────────┐
         │                     │
       "Oui"                 "Non"
         │                     │
         ▼                     ▼
    ┌─────────┐       ┌────────────────┐
    │ GOODBYE │       │check_technician│
    └─────────┘       └───────┬────────┘
                              │
                   ┌──────────┴──────────┐
                   │                     │
              Available            Not available
                   │                     │
                   ▼                     ▼
             ┌──────────┐          ┌─────────┐
             │ TRANSFER │          │ GOODBYE │
             └──────────┘          └─────────┘
```

### 6.3 Implémentation

**Méthode principale :**

```python
async def _process_user_input(self, user_text: str):
    """Traite l'input selon l'état actuel"""

    if self.state == ConversationState.WELCOME:
        # Transition WELCOME → IDENTIFICATION
        response = await self._ask_llm(
            user_text,
            system_prompt="Demande nom et téléphone"
        )
        await self._say_dynamic(response)
        self.state = ConversationState.IDENTIFICATION

    elif self.state == ConversationState.IDENTIFICATION:
        # Sauvegarder infos
        self.context['user_info'] = user_text

        # Transition → DIAGNOSTIC
        response = await self._ask_llm(
            user_text,
            system_prompt="Demande type de problème"
        )
        await self._say_dynamic(response)
        self.state = ConversationState.DIAGNOSTIC

    # ... etc
```

### 6.4 Contexte de Conversation

**Stockage des données :**

```python
self.context = {
    'user_info': "Pierre Dupont, 06 12 34 56 78",
    'problem_type': "internet",
    'solution_tried': True,
    'problem_solved': False
}
```

**Utilisation :**

```python
if self.context['problem_type'] == "internet":
    solution = "Débrancher la box..."
else:
    solution = "Redémarrer le téléphone..."
```

---

## 7. Flux de Données

### 7.1 Flux Audio Input (Asterisk → Python → Deepgram)

```
┌──────────┐
│ Asterisk │
│   8kHz   │
└────┬─────┘
     │ AudioSocket TCP
     │ Chunks 320 bytes (20ms)
     ▼
┌──────────────────────────────────┐
│ Python: _audio_input_handler()   │
│                                  │
│ chunk = await reader.read(320)  │
└────┬─────────────────────────────┘
     │
     ├──────────────────┐
     │                  │
     ▼                  ▼
┌────────────┐   ┌──────────────┐
│ Log RAW    │   │input_queue   │
│ to disk    │   │(asyncio)     │
│            │   │              │
│ .raw file  │   └──────┬───────┘
└────────────┘          │
                        │
                        ▼
                ┌─────────────────┐
                │ Deepgram        │
                │ WebSocket       │
                │                 │
                │ connection.send │
                └────────┬────────┘
                         │
                         ▼
                  ┌────────────┐
                  │Transcription│
                  │  "Bonjour" │
                  └──────┬─────┘
                         │
                         ▼
              ┌──────────────────────┐
              │_process_user_input() │
              │   (Machine à états)  │
              └──────────────────────┘
```

### 7.2 Flux Audio Output (Python → Asterisk)

**Cas 1 : Cache Hit (phrases courantes)**

```
CallHandler décide : "dire welcome"
         ↓
AudioCache.get("welcome")
         ↓
assets/cache/welcome.raw (déjà 8kHz!)
         ↓
_send_audio(audio_data)
         ↓
Découpe en chunks 320 bytes
         ↓
output_queue.append(chunk1)
output_queue.append(chunk2)
...
         ↓
_audio_output_handler()
         ↓
writer.write(chunk)
         ↓
AudioSocket TCP → Asterisk → Utilisateur
```

**Latence totale : ~30-50ms** (lecture RAM + envoi réseau)

**Cas 2 : Cache Miss (réponse dynamique LLM)**

```
CallHandler décide : réponse dynamique
         ↓
_ask_llm(user_text, prompt)
         ↓
Groq API → Réponse texte
         ↓
OpenAI TTS API
         ↓
MP3 24kHz (bytes)
         ↓
ProcessPoolExecutor.run_in_executor(
    process_pool,
    convert_24khz_to_8khz,
    mp3_data
)
         ↓
Worker process (Core 1/2/3) :
├─ Décode MP3 (pydub)
├─ Resample 24kHz → 8kHz (FFmpeg)
├─ Normalise volume
└─ Export RAW 8kHz
         ↓
Return vers main thread
         ↓
_send_audio(audio_8khz)
         ↓
output_queue
         ↓
AudioSocket → Asterisk
```

**Latence totale : ~800-1500ms**
- Groq : ~400ms
- OpenAI TTS : ~300ms
- Conversion : ~100-200ms
- Réseau : ~100ms

---

# PARTIE 3 : COMPOSANTS

## 8. server.py - Serveur Principal

### 8.1 Imports et Configuration

```python
#!/usr/bin/env python3
import asyncio
import uvloop
import logging
import signal
import sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from collections import deque

# AI APIs
from deepgram import DeepgramClient, LiveTranscriptionEvents
from groq import Groq
from openai import OpenAI

# Local
import config
from audio_utils import convert_24khz_to_8khz
```

### 8.2 Classe AudioSocketServer

**Responsabilité :** Serveur TCP principal

```python
class AudioSocketServer:
    def __init__(self):
        # Cache audio RAM
        self.audio_cache = AudioCache()

        # Pool de processus pour conversions CPU-bound
        self.process_pool = ProcessPoolExecutor(
            max_workers=config.PROCESS_POOL_WORKERS
        )

        # Compteur appels actifs
        self.active_calls = 0

    async def handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ):
        """Gère une connexion AudioSocket (= un appel)"""

        # 1. Handshake
        uuid_bytes = await reader.read(16)
        if len(uuid_bytes) != 16:
            writer.close()
            return

        call_id = uuid_bytes.hex()

        # 2. Limiter appels simultanés
        if self.active_calls >= config.MAX_CONCURRENT_CALLS:
            logger.warning(f"Max calls reached")
            writer.close()
            return

        self.active_calls += 1

        # 3. Créer handler d'appel
        try:
            handler = CallHandler(
                call_id=call_id,
                reader=reader,
                writer=writer,
                audio_cache=self.audio_cache,
                process_pool=self.process_pool
            )

            await handler.handle_call()

        finally:
            self.active_calls -= 1

    async def start(self):
        """Démarre le serveur"""
        server = await asyncio.start_server(
            self.handle_client,
            config.AUDIOSOCKET_HOST,
            config.AUDIOSOCKET_PORT
        )

        logger.info(f"Server started on {config.AUDIOSOCKET_PORT}")

        async with server:
            await server.serve_forever()
```

### 8.3 Classe CallHandler

**Responsabilité :** Orchestrer un appel individuel

**Attributs clés :**

```python
class CallHandler:
    def __init__(self, call_id, reader, writer, audio_cache, process_pool):
        # Identifiants
        self.call_id = call_id
        self.reader = reader
        self.writer = writer

        # État conversationnel
        self.state = ConversationState.INIT
        self.context = {}

        # Audio queues
        self.input_queue = asyncio.Queue()
        self.output_queue = deque()

        # APIs
        self.deepgram_client = DeepgramClient(config.DEEPGRAM_API_KEY)
        self.groq_client = Groq(api_key=config.GROQ_API_KEY)
        self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)

        # Contrôle
        self.is_active = True
        self.is_speaking = False

        # Timestamps
        self.last_user_speech_time = time.time()
        self.call_start_time = time.time()

        # Logging audio
        self.audio_log_file = open(
            config.LOGS_DIR / f"call_{call_id}_{timestamp}.raw",
            'wb'
        )
```

**Méthode principale :**

```python
async def handle_call(self):
    """Point d'entrée : démarre toutes les tâches"""

    tasks = [
        asyncio.create_task(self._audio_input_handler()),
        asyncio.create_task(self._audio_output_handler()),
        asyncio.create_task(self._deepgram_handler()),
        asyncio.create_task(self._conversation_handler()),
        asyncio.create_task(self._timeout_monitor())
    ]

    # Attendre qu'UNE tâche se termine (= fin d'appel)
    done, pending = await asyncio.wait(
        tasks,
        return_when=asyncio.FIRST_COMPLETED
    )

    # Annuler les tâches restantes
    for task in pending:
        task.cancel()

    # Cleanup
    await self._cleanup()
```

### 8.4 Tâche : _audio_input_handler()

**Responsabilité :** Lire audio depuis AudioSocket

```python
async def _audio_input_handler(self):
    """Lit l'audio depuis Asterisk et l'envoie à Deepgram"""

    try:
        while self.is_active:
            # Lire 320 bytes (20ms @ 8kHz)
            chunk = await self.reader.read(320)

            if not chunk:
                # Connexion fermée
                self.is_active = False
                break

            # Logger sur disque
            if self.audio_log_file:
                self.audio_log_file.write(chunk)

            # Envoyer à Deepgram
            await self.input_queue.put(chunk)

    except Exception as e:
        logger.error(f"Audio input error: {e}")
        self.is_active = False
```

### 8.5 Tâche : _audio_output_handler()

**Responsabilité :** Envoyer audio vers AudioSocket

```python
async def _audio_output_handler(self):
    """Envoie l'audio vers Asterisk depuis la queue"""

    try:
        while self.is_active:
            # Vider la queue
            while self.output_queue:
                chunk = self.output_queue.popleft()

                self.writer.write(chunk)
                await self.writer.drain()

                # Yield pour éviter blocage
                await asyncio.sleep(0)

            # Pas d'audio, attendre
            await asyncio.sleep(0.02)  # 20ms

    except Exception as e:
        logger.error(f"Audio output error: {e}")
        self.is_active = False
```

### 8.6 Tâche : _deepgram_handler()

**Responsabilité :** Streaming STT

```python
async def _deepgram_handler(self):
    """Gère Deepgram STT avec streaming"""

    # Options
    options = LiveOptions(
        model="nova-2-phonecall",
        language="fr",
        encoding="linear16",
        sample_rate=8000,
        interim_results=True,
        vad_events=True
    )

    # Connexion
    connection = self.deepgram_client.listen.asynclive.v("1")

    # Handler transcription
    async def on_message(result, **kwargs):
        sentence = result.channel.alternatives[0].transcript
        if sentence and result.is_final:
            logger.info(f"[{self.call_id}] User: {sentence}")
            await self._process_user_input(sentence)

    # Handler barge-in
    async def on_speech_started(speech_started, **kwargs):
        await self._handle_barge_in()

    # Enregistrer handlers
    connection.on(LiveTranscriptionEvents.Transcript, on_message)
    connection.on(LiveTranscriptionEvents.SpeechStarted, on_speech_started)

    # Démarrer
    await connection.start(options)

    # Streamer audio
    while self.is_active:
        chunk = await self.input_queue.get()
        await connection.send(chunk)

    # Cleanup
    await connection.finish()
```

### 8.7 Tâche : _conversation_handler()

**Responsabilité :** Démarrer la conversation

```python
async def _conversation_handler(self):
    """Initialise la conversation"""

    # Message d'accueil
    await self._say("welcome")
    self.state = ConversationState.WELCOME
```

### 8.8 Tâche : _timeout_monitor()

**Responsabilité :** Surveiller timeouts

```python
async def _timeout_monitor(self):
    """Surveille silence et durée max"""

    while self.is_active:
        await asyncio.sleep(1)

        # Durée max appel
        call_duration = time.time() - self.call_start_time
        if call_duration > config.MAX_CALL_DURATION:
            await self._say("goodbye")
            self.is_active = False
            break

        # Silence utilisateur
        if not self.is_speaking:
            silence = time.time() - self.last_user_speech_time

            if silence > config.SILENCE_HANGUP_TIMEOUT:
                # 15s → Raccrocher
                await self._say("goodbye")
                self.is_active = False
                break

            elif silence > config.SILENCE_WARNING_TIMEOUT:
                # 8s → "Allô ?"
                await self._say("allo")
                self.last_user_speech_time = time.time()
```

---

## 9. config.py - Configuration

### 9.1 Variables d'Environnement

```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# API Keys
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
```

### 9.2 Specs Audio

```python
# Format AudioSocket
SAMPLE_RATE_ASTERISK = 8000   # Hz
SAMPLE_RATE_OPENAI = 24000    # Hz
SAMPLE_WIDTH = 2              # bytes (16-bit)
CHANNELS = 1                  # Mono
```

### 9.3 Paramètres Serveur

```python
AUDIOSOCKET_HOST = os.getenv("AUDIOSOCKET_HOST", "0.0.0.0")
AUDIOSOCKET_PORT = int(os.getenv("AUDIOSOCKET_PORT", 9090))
MAX_CONCURRENT_CALLS = 20
PROCESS_POOL_WORKERS = 3
```

### 9.4 Timeouts

```python
SILENCE_WARNING_TIMEOUT = 8   # secondes
SILENCE_HANGUP_TIMEOUT = 15
MAX_CALL_DURATION = 600       # 10 minutes
API_TIMEOUT = 10
API_RETRY_ATTEMPTS = 2
```

### 9.5 Chemins

```python
BASE_DIR = Path(__file__).parent
CACHE_DIR = BASE_DIR / "assets" / "cache"
LOGS_DIR = BASE_DIR / "logs" / "calls"

# Créer si nécessaire
CACHE_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
```

### 9.6 Phrases Cachées

```python
CACHED_PHRASES = {
    "welcome": "Bonjour, bienvenue au SAV Wouippleul...",
    "goodbye": "Merci pour votre appel. Au revoir !",
    "ok": "D'accord.",
    "wait": "Un instant s'il vous plaît...",
    "error": "Désolé, nous rencontrons un problème...",
    "allo": "Allô, vous êtes toujours là ?",
    "transfer": "Je vous transfère à un technicien...",
    "understood": "Très bien, j'ai compris."
}
```

---

## 10. audio_utils.py - Utilitaires Audio

### 10.1 Conversion 24kHz → 8kHz

**Fonction principale (CPU-bound) :**

```python
def convert_24khz_to_8khz(
    audio_data_24khz: bytes,
    input_format: str = "mp3"
) -> bytes:
    """
    Convertit OpenAI TTS (24kHz) vers Asterisk (8kHz)

    Note: Cette fonction est CPU-intensive et doit être
    exécutée dans un ProcessPoolExecutor !
    """
    try:
        # Charger l'audio depuis bytes
        audio = AudioSegment.from_file(
            io.BytesIO(audio_data_24khz),
            format=input_format
        )

        # Mono
        if audio.channels > 1:
            audio = audio.set_channels(1)

        # Resampler à 8kHz
        audio = audio.set_frame_rate(8000)

        # 16-bit
        audio = audio.set_sample_width(2)

        # Normaliser volume
        audio = normalize(audio, headroom=0.1)

        # Export RAW (Signed PCM Little Endian)
        return audio.raw_data

    except Exception as e:
        logger.error(f"Conversion error: {e}")
        # Retourner silence en cas d'erreur
        return b'\x00\x00' * 8000  # 1 seconde
```

**Utilisation dans server.py :**

```python
# ❌ NE PAS FAIRE (bloque l'event loop !)
audio_8khz = convert_24khz_to_8khz(audio_24khz)

# ✅ BON : Exécution dans ProcessPool
loop = asyncio.get_event_loop()
audio_8khz = await loop.run_in_executor(
    self.process_pool,
    convert_24khz_to_8khz,
    audio_24khz,
    "mp3"
)
```

### 10.2 Génération de Silence

```python
def generate_silence(duration_ms: int, sample_rate: int = 8000) -> bytes:
    """Génère du silence (utile pour padding)"""
    num_samples = int(duration_ms * sample_rate / 1000)
    return b'\x00\x00' * num_samples
```

### 10.3 Validation Format Audio

```python
def validate_audio_format(audio_data: bytes, expected_sample_rate: int = 8000) -> bool:
    """Valide que l'audio est bien 16-bit aligned"""
    # Taille paire ?
    if len(audio_data) % 2 != 0:
        return False

    # Au moins 100ms ?
    min_samples = expected_sample_rate // 10
    if len(audio_data) < min_samples * 2:
        return False

    return True
```

---

## 11. Scripts Utilitaires

### 11.1 generate_cache.py

**Objectif :** Pré-générer les fichiers audio 8kHz

**Workflow :**

```python
# 1. Lire les phrases depuis config
for phrase_key, phrase_text in config.CACHED_PHRASES.items():

    # 2. Appeler OpenAI TTS
    response = openai_client.audio.speech.create(
        model="tts-1",
        voice="nova",
        input=phrase_text
    )
    audio_24khz = response.read()

    # 3. Convertir 24kHz → 8kHz
    audio_8khz = convert_to_8khz(audio_24khz)

    # 4. Sauvegarder
    output_path = config.CACHE_DIR / f"{phrase_key}.raw"
    with open(output_path, 'wb') as f:
        f.write(audio_8khz)
```

**Utilisation :**

```bash
python generate_cache.py
```

**Sortie :**

```
✓ welcome.raw créé (45.2 KB, 2.8s)
✓ goodbye.raw créé (32.1 KB, 2.0s)
✓ ok.raw créé (12.5 KB, 0.8s)
...
✅ Génération du cache terminée !
```

### 11.2 convert_logs.py

**Objectif :** Conversion batch RAW → MP3 (nocturne)

**Workflow :**

```python
# 1. Scanner répertoire logs
raw_files = list(config.LOGS_DIR.glob("**/*.raw"))

# 2. Conversion parallèle
with ProcessPoolExecutor(max_workers=3) as executor:
    futures = []

    for raw_path in raw_files:
        mp3_path = raw_path.with_suffix('.mp3')

        future = executor.submit(
            convert_raw_to_mp3,
            str(raw_path),
            str(mp3_path),
            bitrate="64k"
        )
        futures.append(future)

    # 3. Attendre résultats
    for future in as_completed(futures):
        success, filename = future.result()
        if success:
            print(f"✓ {filename}")
```

**Utilisation :**

```bash
# Simple
python convert_logs.py

# Avec suppression RAW
python convert_logs.py --delete-raw

# Custom bitrate
python convert_logs.py --bitrate 128k
```

### 11.3 test_setup.py

**Objectif :** Valider configuration avant lancement

**Tests :**

1. Python version >= 3.11
2. Modules installés (uvloop, pydub, etc.)
3. FFmpeg présent
4. Fichier .env existe
5. Clés API configurées
6. Répertoires créés
7. Cache audio généré
8. Port 9090 disponible

**Utilisation :**

```bash
python test_setup.py
```

**Sortie :**

```
✓ Python version: 3.11.0
✓ Module 'uvloop' installé
✓ FFmpeg installé
✓ .env existe
✓ Cache audio: 8/8 fichiers
...
✅ Tous les tests passent !
```

---

# PARTIE 4 : INTÉGRATIONS

## 12. Intégration Deepgram (STT)

### 12.1 Configuration

```python
from deepgram import (
    DeepgramClient,
    LiveTranscriptionEvents,
    LiveOptions
)

client = DeepgramClient(api_key=config.DEEPGRAM_API_KEY)
```

### 12.2 Options de Streaming

```python
options = LiveOptions(
    model="nova-2-phonecall",     # Optimisé téléphonie
    language="fr",                # Français
    encoding="linear16",          # Format audio
    sample_rate=8000,             # 8kHz
    channels=1,                   # Mono
    interim_results=True,         # Résultats intermédiaires
    punctuate=True,               # Ponctuation
    vad_events=True               # Détection activité vocale
)
```

### 12.3 Connexion WebSocket

```python
connection = client.listen.asynclive.v("1")

# Handlers d'événements
async def on_transcript(result, **kwargs):
    text = result.channel.alternatives[0].transcript
    if text and result.is_final:
        # Transcription finale
        await process_text(text)

connection.on(LiveTranscriptionEvents.Transcript, on_transcript)

# Démarrer
await connection.start(options)
```

### 12.4 Streaming Audio

```python
# Envoyer audio chunk par chunk
while is_active:
    chunk = await input_queue.get()  # 320 bytes
    await connection.send(chunk)
```

### 12.5 Détection Barge-in

```python
async def on_speech_started(speech_started, **kwargs):
    """VAD détecte début de parole utilisateur"""
    logger.info("Barge-in detected")

    # Vider buffer de sortie
    output_queue.clear()

    # Stopper TTS en cours
    is_speaking = False
```

---

## 13. Intégration Groq (LLM)

### 13.1 Configuration

```python
from groq import Groq

client = Groq(api_key=config.GROQ_API_KEY)
```

### 13.2 Génération de Réponses

```python
async def _ask_llm(self, user_message: str, system_prompt: str) -> str:
    """Appelle Groq pour générer une réponse"""

    try:
        response = self.groq_client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=150,
            timeout=config.API_TIMEOUT
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"Groq error: {e}")
        return "Désolé, pouvez-vous répéter ?"
```

### 13.3 Prompts par État

**IDENTIFICATION :**

```python
system_prompt = """
Tu es un agent SAV professionnel et courtois.
L'utilisateur vient de se présenter.
Demande-lui poliment son nom et son numéro de téléphone
s'il ne les a pas encore donnés.
Reste concis (1-2 phrases max).
"""
```

**DIAGNOSTIC :**

```python
system_prompt = """
Tu es un agent SAV.
Demande au client s'il a un problème avec Internet ou Mobile.
Reste concis et direct.
"""
```

---

## 14. Intégration OpenAI (TTS)

### 14.1 Configuration

```python
from openai import OpenAI

client = OpenAI(api_key=config.OPENAI_API_KEY)
```

### 14.2 Génération Audio

```python
async def _say_dynamic(self, text: str):
    """Génère et dit un texte via OpenAI TTS"""

    self.is_speaking = True

    # 1. Appeler OpenAI TTS
    response = self.openai_client.audio.speech.create(
        model="tts-1",
        voice="nova",              # Voix féminine
        input=text,
        response_format="mp3",
        speed=1.0
    )

    audio_24khz = response.read()  # bytes MP3 @ 24kHz

    # 2. Convertir 24kHz → 8kHz (ProcessPool)
    loop = asyncio.get_event_loop()
    audio_8khz = await loop.run_in_executor(
        self.process_pool,
        convert_24khz_to_8khz,
        audio_24khz,
        "mp3"
    )

    # 3. Envoyer vers AudioSocket
    await self._send_audio(audio_8khz)

    self.is_speaking = False
```

### 14.3 Choix de la Voix

**Voix disponibles :**
- `alloy` : Neutre
- `echo` : Masculine
- `fable` : Accent britannique
- `onyx` : Profonde
- `nova` : ✅ **Féminine professionnelle (recommandée)**
- `shimmer` : Douce

---

# PARTIE 5 : OPTIMISATIONS

## 15. Performance CPU

### 15.1 Séparation I/O vs CPU-bound

**Core 0 (Thread principal - uvloop) :**

```python
# ✅ Tâches I/O bound (non-bloquantes)
- Réseau AudioSocket (TCP)
- WebSocket Deepgram
- API HTTP (Groq, OpenAI)
- Orchestration asyncio
```

**Cores 1-3 (ProcessPoolExecutor) :**

```python
# ✅ Tâches CPU-bound (bloquantes)
- Conversion FFmpeg (24kHz → 8kHz)
- Batch conversion (RAW → MP3)
- Normalisation audio
```

### 15.2 Profiling CPU

**Commande :**

```bash
mpstat -P ALL 1
```

**Résultat attendu :**

```
CPU    %usr  %sys  %iowait  %idle
0      35    5     2        58     ← I/O asyncio
1      75    10    1        14     ← Conversion FFmpeg
2      72    11    2        15     ← Conversion FFmpeg
3      70    12    3        15     ← Conversion FFmpeg
```

**Interprétation :**
- Core 0 : ~40% (I/O bound, beaucoup d'idle)
- Cores 1-3 : ~80% (CPU bound, peu d'idle)
- **Total** : ~70% (marge de 30%)

---

## 16. Optimisation Mémoire

### 16.1 Memory Footprint

**Mesure :**

```bash
ps aux | grep python
```

**Breakdown :**

```
Python runtime + libs:     50 MB
AudioCache (8 phrases):     5 MB
Par appel actif:            2 MB

Total @ 20 appels:
50 + 5 + (20 × 2) = 95 MB
```

### 16.2 Garbage Collection

**Cleanup après chaque appel :**

```python
async def _cleanup(self):
    # Fermer fichiers
    if self.audio_log_file:
        self.audio_log_file.close()

    # Fermer connexions
    await self.deepgram_connection.finish()
    self.writer.close()

    # Libérer queues
    del self.input_queue
    del self.output_queue
    del self.context

    # GC suggéré
    import gc
    gc.collect()
```

---

## 17. Cache Audio

### 17.1 Chargement au Démarrage

```python
class AudioCache:
    def __init__(self):
        self.cache = {}
        self._load_cache()

    def _load_cache(self):
        for phrase_key in config.CACHED_PHRASES.keys():
            cache_file = config.CACHE_DIR / f"{phrase_key}.raw"

            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    self.cache[phrase_key] = f.read()
```

### 17.2 Utilisation

```python
async def _say(self, phrase_key: str):
    """Dit une phrase depuis le cache"""

    audio_data = self.audio_cache.get(phrase_key)

    if audio_data:
        # Envoi DIRECT (déjà en 8kHz)
        await self._send_audio(audio_data)
```

### 17.3 Gain de Performance

| Métrique | Cache Miss (TTS) | Cache Hit |
|----------|------------------|-----------|
| Latence | ~800ms | ~30ms |
| CPU | 100% (conversion) | 0% |
| Coût API | $0.020 | $0 |
| Qualité | Variable | Constante |

---

## 18. Gestion Erreurs

### 18.1 Stratégie Multi-Niveaux

**Niveau 1 : Retry avec Backoff**

```python
for retry in range(config.API_RETRY_ATTEMPTS):
    try:
        response = await api_call()
        break
    except TimeoutError:
        wait_time = 2 ** retry  # Exponentiel
        await asyncio.sleep(wait_time)
```

**Niveau 2 : Fallback vers Cache**

```python
except APIError as e:
    logger.error(f"API error: {e}")

    # Jouer message d'attente
    await self._say("wait")
```

**Niveau 3 : Soft Hangup**

```python
if consecutive_errors > 3:
    # Erreur persistante
    await self._say("error")
    self.is_active = False  # Fin d'appel propre
```

### 18.2 Isolation des Erreurs

**ProcessPoolExecutor :**

```python
try:
    audio = await loop.run_in_executor(
        pool,
        convert_audio,  # Peut crasher !
        data
    )
except Exception as e:
    # Crash dans worker process
    # → Ne crash PAS le serveur principal !
    logger.error(f"Worker error: {e}")
    audio = generate_silence(1000)  # Fallback
```

---

# PARTIE 6 : DÉPLOIEMENT

## 19. Installation Développement

### 19.1 Prérequis

```bash
# Ubuntu 22.04
sudo apt-get update
sudo apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    ffmpeg \
    git
```

### 19.2 Setup Projet

```bash
# Clone
git clone <repo>
cd PY_SAV

# Venv
python3.11 -m venv venv
source venv/bin/activate

# Dépendances
pip install -r requirements.txt

# Config
cp .env.example .env
nano .env  # Ajouter clés API

# Cache
python generate_cache.py

# Test
python test_setup.py

# Run
python server.py
```

---

## 20. Déploiement Production

### 20.1 Service systemd

**Fichier : `/etc/systemd/system/voicebot.service`**

```ini
[Unit]
Description=Voicebot SAV Wouippleul
After=network.target asterisk.service

[Service]
Type=simple
User=voicebot
WorkingDirectory=/opt/PY_SAV
Environment="PATH=/opt/PY_SAV/venv/bin"
ExecStart=/opt/PY_SAV/venv/bin/python server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Commandes :**

```bash
# Activer
sudo systemctl enable voicebot

# Démarrer
sudo systemctl start voicebot

# Status
sudo systemctl status voicebot

# Logs
sudo journalctl -u voicebot -f
```

---

## 21. Monitoring

### 21.1 Logs

**Systemd journal :**

```bash
# Temps réel
sudo journalctl -u voicebot -f

# Dernières 100 lignes
sudo journalctl -u voicebot -n 100

# Depuis hier
sudo journalctl -u voicebot --since yesterday
```

**Logs Asterisk :**

```bash
tail -f /var/log/asterisk/full
```

### 21.2 Métriques

**CPU par core :**

```bash
mpstat -P ALL 1
```

**Mémoire :**

```bash
free -h
```

**Connexions actives :**

```bash
netstat -an | grep :9090 | wc -l
```

---

## 22. Maintenance

### 22.1 Backup Logs

```bash
# Cron quotidien
0 4 * * * rsync -av /opt/PY_SAV/logs/ /backup/voicebot/$(date +\%Y\%m\%d)/
```

### 22.2 Conversion Nocturne

```bash
# Cron à 3h du matin
0 3 * * * cd /opt/PY_SAV && python convert_logs.py --delete-raw
```

---

# PARTIE 7 : RÉFÉRENCE API

## 23. API CallHandler

### 23.1 Méthodes Publiques

```python
async def handle_call(self) -> None:
    """Point d'entrée : gère un appel complet"""

async def _say(self, phrase_key: str) -> None:
    """Dit une phrase depuis le cache"""

async def _say_dynamic(self, text: str) -> None:
    """Génère et dit un texte dynamique (TTS)"""

async def _ask_llm(self, user_message: str, system_prompt: str) -> str:
    """Appelle Groq LLM"""

async def _check_technician(self) -> bool:
    """Vérifie disponibilité technicien"""
```

---

## 24. API AudioCache

```python
class AudioCache:
    def get(self, phrase_key: str) -> Optional[bytes]:
        """Récupère audio depuis cache"""

    def has(self, phrase_key: str) -> bool:
        """Vérifie si phrase en cache"""
```

---

## 25. API AudioUtils

```python
def convert_24khz_to_8khz(
    audio_data_24khz: bytes,
    input_format: str = "mp3"
) -> bytes:
    """Convertit audio OpenAI vers Asterisk"""

def generate_silence(duration_ms: int, sample_rate: int = 8000) -> bytes:
    """Génère du silence"""

def validate_audio_format(audio_data: bytes) -> bool:
    """Valide format audio"""
```

---

# PARTIE 8 : ANNEXES

## 26. Troubleshooting

### Problème : Service ne démarre pas

**Symptôme :**

```bash
sudo systemctl status voicebot
● voicebot.service - failed
```

**Diagnostic :**

```bash
sudo journalctl -u voicebot -n 50
```

**Causes fréquentes :**
1. Clés API invalides → Vérifier `.env`
2. Port 9090 occupé → `netstat -tlnp | grep 9090`
3. Modules manquants → `pip install -r requirements.txt`

---

## 27. FAQ

**Q : Combien coûte le voicebot par appel ?**

R : ~$0.034 pour un appel de 2 minutes (STT + LLM + TTS)

**Q : Peut-on utiliser un autre LLM que Groq ?**

R : Oui, modifier `_ask_llm()` pour appeler OpenAI GPT-4 par exemple.

**Q : Le voicebot supporte-t-il plusieurs langues ?**

R : Non actuellement (hardcodé français). À implémenter : détection automatique de langue.

---

## 28. Exemples de Code

### 28.1 Ajouter un Nouvel État

**1. Définir l'état :**

```python
class ConversationState(Enum):
    # ... existants
    NEW_STATE = "new_state"
```

**2. Ajouter la logique :**

```python
async def _process_user_input(self, user_text: str):
    # ... autres états

    elif self.state == ConversationState.NEW_STATE:
        # Logique métier
        await self._say_dynamic("Réponse personnalisée")
        self.state = ConversationState.NEXT_STATE
```

### 28.2 Ajouter une Phrase au Cache

**1. Modifier config.py :**

```python
CACHED_PHRASES = {
    # ... existants
    "new_phrase": "Texte de la nouvelle phrase"
}
```

**2. Régénérer le cache :**

```bash
python generate_cache.py
```

**3. Utiliser :**

```python
await self._say("new_phrase")
```

---

**FIN DE LA DOCUMENTATION TECHNIQUE COMPLÈTE**

---

**Version** : 1.0.0
**Dernière mise à jour** : 18 novembre 2025
**Auteur** : Expert Python/VoIP
**Licence** : Propriétaire SAV Wouippleul

Pour toute question : support@wouippleul.fr

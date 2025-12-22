# Migration vers ElevenLabs TTS

Ce document décrit la migration d'OpenAI TTS vers ElevenLabs TTS pour le voicebot SAV Wouippleul.

## Modifications effectuées

### 1. Configuration (`config.py`)
- ✅ Remplacement de `OPENAI_API_KEY` par `ELEVENLABS_API_KEY`
- ✅ Remplacement de `SAMPLE_RATE_OPENAI` par `SAMPLE_RATE_ELEVENLABS`
- ✅ Ajout des paramètres ElevenLabs :
  - `ELEVENLABS_VOICE_ID` : ID de la voix (Adrien - French Modern)
  - `ELEVENLABS_MODEL` : Modèle multilingue v2
  - `ELEVENLABS_STABILITY` : Stabilité de la voix (0.5)
  - `ELEVENLABS_SIMILARITY_BOOST` : Clarté (0.75)
  - `ELEVENLABS_STYLE` : Style (0.0)
  - `ELEVENLABS_USE_SPEAKER_BOOST` : Amélioration (True)

### 2. Serveur principal (`server.py`)
- ✅ Import : `from elevenlabs.client import ElevenLabs` et `from elevenlabs import VoiceSettings`
- ✅ Remplacement du client OpenAI par ElevenLabs
- ✅ Mise à jour de la métrique Prometheus `ELEVENLABS_TTS_ERRORS`
- ✅ Réécriture de la fonction `_say_dynamic()` pour utiliser ElevenLabs API
- ✅ Vérification des clés API au démarrage

### 3. Script de génération de cache (`generate_cache.py`)
- ✅ Import ElevenLabs au lieu d'OpenAI
- ✅ Mise à jour de la fonction `generate_phrase()` pour utiliser ElevenLabs
- ✅ Vérification de la clé API ElevenLabs

### 4. Dépendances (`requirements.txt`)
- ✅ Remplacement de `openai==1.54.4` par `elevenlabs==1.13.1`

### 5. Variables d'environnement (`.env`)
- ✅ Création du fichier `.env` avec les variables ElevenLabs
- ⚠️ **IMPORTANT** : Vous devez remplacer les valeurs suivantes dans `.env` :
  - `ELEVENLABS_API_KEY=VOTRE_CLE_ELEVENLABS_ICI`
  - `DEEPGRAM_API_KEY=VOTRE_CLE_DEEPGRAM_ICI`
  - `GROQ_API_KEY=VOTRE_CLE_GROQ_ICI`
  - Autres secrets (AMI_SECRET, POSTGRES_PASSWORD, etc.)

## Étapes de déploiement sur le serveur SSH

### 1. Installer la bibliothèque ElevenLabs

Connectez-vous à votre serveur SSH et exécutez :

```bash
cd /root/PY_SAV
source venv/bin/activate
pip install elevenlabs==1.13.1
```

### 2. Mettre à jour le fichier .env

Éditez le fichier `.env` et ajoutez votre clé API ElevenLabs :

```bash
nano .env
```

Ajoutez ou modifiez :
```
ELEVENLABS_API_KEY=sk_3XXXXXX35c226620bc049
ELEVENLABS_VOICE_ID=N2lVS1w4EtoT3dr4eOWO
ELEVENLABS_MODEL=eleven_multilingual_v2
```

### 3. Regénérer le cache audio

Le cache audio existant a été généré avec OpenAI TTS. Vous devez le regénérer avec ElevenLabs :

**Option A - Automatique (recommandé):**
```bash
cd /root/PY_SAV
chmod +x deploy_elevenlabs.sh
./deploy_elevenlabs.sh
```

Le script va automatiquement :
- Installer ElevenLabs
- Vérifier le .env
- Sauvegarder l'ancien cache
- Générer les 27 nouveaux fichiers .raw avec ElevenLabs

**Option B - Manuelle:**
```bash
cd /root/PY_SAV
source venv/bin/activate
python generate_cache.py
```

Cela va générer les 27 fichiers `.raw` dans `assets/cache/` avec la voix ElevenLabs.

### 4. Tester le serveur

Lancez le serveur en mode test :

```bash
cd /root/PY_SAV
source venv/bin/activate
python server.py
```

Vérifiez les logs pour s'assurer que :
- ✅ La clé API ElevenLabs est chargée
- ✅ Le cache audio est chargé (27 phrases)
- ✅ Le serveur démarre sans erreur

### 5. Tester un appel

Effectuez un appel test depuis Asterisk et vérifiez que :
- ✅ Les phrases en cache sont jouées correctement
- ✅ Les phrases dynamiques sont générées avec ElevenLabs
- ✅ La latence est acceptable (devrait être similaire à OpenAI)

### 6. Surveiller les métriques Prometheus

Consultez les métriques sur `http://145.239.223.189:9091/metrics` :
- `voicebot_elevenlabs_tts_errors_total` : Nombre d'erreurs ElevenLabs
- `voicebot_api_latency_seconds{api="elevenlabs_tts"}` : Latence de l'API

## Avantages d'ElevenLabs

1. **Qualité vocale** : Voix naturelles de haute qualité en français
2. **Modèle multilingue** : Support natif du français avec `eleven_multilingual_v2`
3. **Contrôle fin** : Paramètres de stabilité, clarté et style
4. **Performance** : Latence comparable à OpenAI
5. **Voix française dédiée** : Adrien - optimisée pour les narrations et podcasts

## Configuration de la voix

Voix utilisée : **Adrien** (`N2lVS1w4EtoT3dr4eOWO`)
- Langue : Français
- Type : French Modern for Narration, Podcasts
- Modèle : `eleven_multilingual_v2`

### Paramètres de la voix :
- **Stability** : 0.5 (équilibre entre expressivité et cohérence)
- **Similarity Boost** : 0.75 (clarté élevée)
- **Style** : 0.0 (style naturel, sans exagération)
- **Speaker Boost** : True (amélioration du locuteur)

## Rollback (si nécessaire)

Si vous devez revenir à OpenAI TTS :

1. Réinstallez `openai==1.54.4` :
   ```bash
   pip install openai==1.54.4
   ```

2. Restaurez les anciennes versions des fichiers :
   ```bash
   git checkout HEAD~1 config.py server.py generate_cache.py requirements.txt
   ```

3. Mettez à jour `.env` avec `OPENAI_API_KEY`

4. Regénérez le cache avec OpenAI

## Vérification finale

Avant de pousser sur GitHub :

- [ ] Le serveur démarre sans erreur
- [ ] Les appels tests fonctionnent correctement
- [ ] Le cache audio est regénéré avec ElevenLabs
- [ ] Les métriques Prometheus sont fonctionnelles
- [ ] Le fichier `.env` est bien dans `.gitignore`
- [ ] La documentation est à jour

## Support

- Documentation ElevenLabs : https://elevenlabs.io/docs
- Liste des voix : https://elevenlabs.io/voice-library
- API Reference : https://elevenlabs.io/docs/api-reference/text-to-speech

---

**Date de migration** : 2025-12-04
**Version** : 2.0 (ElevenLabs TTS)

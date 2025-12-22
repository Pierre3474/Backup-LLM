# Changelog - Migration ElevenLabs v2.0

**Date**: 2025-12-04
**Type**: Migration majeure TTS (OpenAI → ElevenLabs)
**Impact**: Tous les fichiers de synthèse vocale

---

## 🎯 Objectif

Migrer le système de Text-to-Speech d'OpenAI vers ElevenLabs pour bénéficier de voix françaises de meilleure qualité et d'un contrôle plus fin de la synthèse vocale.

---

## 📦 Changements

### Fichiers modifiés

#### `config.py`
- ❌ Supprimé : `OPENAI_API_KEY`, `SAMPLE_RATE_OPENAI`, `OPENAI_TTS_MODEL`, `OPENAI_TTS_VOICE`, `OPENAI_TTS_SPEED`
- ✅ Ajouté : `ELEVENLABS_API_KEY`, `SAMPLE_RATE_ELEVENLABS`
- ✅ Ajouté : Configuration complète ElevenLabs (voice_id, model, stability, similarity_boost, style, speaker_boost)
- ✅ Réduit les phrases en cache de 201 → 27 (phrases réellement utilisées)

#### `server.py`
- ❌ Supprimé : `from openai import OpenAI`
- ✅ Ajouté : `from elevenlabs.client import ElevenLabs` et `from elevenlabs import VoiceSettings`
- ✅ Remplacé : `self.openai_client` par `self.elevenlabs_client`
- ✅ Modifié : Métrique Prometheus `OPENAI_TTS_ERRORS` → `ELEVENLABS_TTS_ERRORS`
- ✅ Réécrit : Fonction `_say_dynamic()` pour utiliser l'API ElevenLabs
- ✅ Modifié : Vérification des clés API au démarrage (ligne 1520)

#### `generate_cache.py`
- ❌ Supprimé : `from openai import OpenAI`
- ✅ Ajouté : `from elevenlabs.client import ElevenLabs` et `from elevenlabs import VoiceSettings`
- ✅ Réécrit : Fonction `generate_phrase()` pour l'API ElevenLabs
- ✅ Modifié : Initialisation du client (ligne 121)

#### `requirements.txt`
- ❌ Supprimé : `openai==1.54.4`
- ✅ Ajouté : `elevenlabs==1.13.1`

### Fichiers créés

- ✅ `.env` - Template des variables d'environnement
- ✅ `.gitignore` - Protection des secrets
- ✅ `MIGRATION_ELEVENLABS.md` - Documentation complète
- ✅ `QUICK_START.md` - Guide de démarrage rapide
- ✅ `CHANGELOG_ELEVENLABS.md` - Ce fichier
- ✅ `deploy_elevenlabs.sh` - Script de déploiement automatique

---

## 🔧 Configuration ElevenLabs

### Voix sélectionnée
- **ID**: `N2lVS1w4EtoT3dr4eOWO`
- **Nom**: Adrien
- **Type**: French Modern for Narration, Podcasts
- **Langue**: Français

### Modèle
- **Model ID**: `eleven_multilingual_v2`
- **Capacités**: Multilingue, optimisé pour le français

### Paramètres vocaux
```python
stability = 0.5              # Équilibre expressivité/cohérence
similarity_boost = 0.75      # Clarté élevée
style = 0.0                  # Style naturel sans exagération
use_speaker_boost = True     # Amélioration du locuteur activée
```

### Format audio
- **Sortie ElevenLabs**: MP3 44.1kHz 128kbps
- **Conversion**: MP3 → RAW PCM 8kHz 16-bit mono (pour Asterisk)

---

## 📊 Métriques Prometheus

### Anciennes métriques (supprimées)
- `voicebot_openai_tts_errors_total`
- `voicebot_api_latency_seconds{api="openai_tts"}`

### Nouvelles métriques
- `voicebot_elevenlabs_tts_errors_total` - Nombre d'erreurs ElevenLabs
- `voicebot_api_latency_seconds{api="elevenlabs_tts"}` - Latence API ElevenLabs

---

## 🎵 Cache audio

### Phrases réduites (201 → 27)

Les phrases suivantes sont pré-générées en cache :

**Accueil** (2):
- greet, welcome

**Identification** (5):
- ask_identity, ask_firstname, ask_email, ask_company, email_invalid

**Problème** (4):
- ask_problem_or_modif, ask_description_technique, ask_number_equipement, ask_restart_devices

**Confirmations** (4):
- ok, wait, filler_checking, filler_processing

**Relances** (3):
- still_there_gentle, clarify_unclear, clarify_yes_no

**Transfert** (3):
- transfer, ticket_transfer_ok, offer_email_transfer

**Tickets** (3):
- confirm_ticket, ticket_created, ticket_not_related

**Horaires** (1):
- closed_hours

**Fin** (2):
- goodbye, error

**Avantage**: Moins de fichiers = génération plus rapide et cache plus léger

---

## ⚡ Performance attendue

### Latence API
- **OpenAI TTS**: ~1-2 secondes
- **ElevenLabs**: ~1-3 secondes (comparable)

### Qualité vocale
- **OpenAI**: Bonne, mais voix anglaise adaptée au français
- **ElevenLabs**: Excellente, voix française native (Adrien)

### Coûts
- **OpenAI**: $15/1M caractères
- **ElevenLabs**: Variables selon le plan (Free: 10k chars/mois)

---

## 🔒 Sécurité

### Fichiers sensibles (dans .gitignore)
- `.env` - **NE JAMAIS COMMITER**
- `venv/` - Environnement virtuel
- `logs/` - Logs d'appels
- `assets/cache/*.raw` - Cache audio

### Clés API requises
```bash
DEEPGRAM_API_KEY=...      # Transcription vocale (STT)
GROQ_API_KEY=...          # LLM pour réponses
ELEVENLABS_API_KEY=...    # Synthèse vocale (TTS)
```

---

## 🧪 Tests à effectuer

### Avant déploiement
- [ ] Vérifier que `.env` contient `ELEVENLABS_API_KEY`
- [ ] Tester `python generate_cache.py` (doit générer 27 fichiers)
- [ ] Vérifier que `python server.py` démarre sans erreur

### Après déploiement
- [ ] Faire un appel test depuis Asterisk
- [ ] Vérifier que les phrases en cache sont jouées correctement
- [ ] Vérifier que les phrases dynamiques sont générées avec ElevenLabs
- [ ] Consulter les métriques Prometheus (aucune erreur)
- [ ] Tester un appel complet de bout en bout

---

## 🔄 Rollback

En cas de problème, pour revenir à OpenAI :

```bash
# 1. Réinstaller OpenAI
pip uninstall elevenlabs
pip install openai==1.54.4

# 2. Restaurer les anciens fichiers
git checkout HEAD~1 config.py server.py generate_cache.py requirements.txt

# 3. Restaurer l'ancien cache
cp -r assets/cache_backup_XXXXXX/* assets/cache/

# 4. Mettre à jour .env
# Remplacer ELEVENLABS_API_KEY par OPENAI_API_KEY

# 5. Redémarrer le serveur
python server.py
```

---

## 📚 Documentation

- [MIGRATION_ELEVENLABS.md](MIGRATION_ELEVENLABS.md) - Guide complet
- [QUICK_START.md](QUICK_START.md) - Démarrage rapide
- [deploy_elevenlabs.sh](deploy_elevenlabs.sh) - Script automatique

### Liens externes
- [ElevenLabs Documentation](https://elevenlabs.io/docs)
- [API Reference](https://elevenlabs.io/docs/api-reference/text-to-speech)
- [Voice Library](https://elevenlabs.io/voice-library)

---

## ✅ Checklist de déploiement

- [ ] Code local mis à jour
- [ ] `.env` configuré avec `ELEVENLABS_API_KEY`
- [ ] `.gitignore` créé (protège `.env`)
- [ ] Tests locaux OK (si possible)
- [ ] Code poussé sur GitHub
- [ ] Pull sur le serveur SSH
- [ ] `pip install elevenlabs==1.13.1` sur le serveur
- [ ] Cache audio regénéré (27 fichiers)
- [ ] Serveur testé
- [ ] Appel test effectué
- [ ] Métriques vérifiées
- [ ] Documentation mise à jour

---

**Version**: 2.0
**Auteur**: Migration automatisée
**Status**: ✅ Prêt pour déploiement

# Guide d'Amélioration de la Prononciation TTS

## Problèmes Courants de Prononciation

Le TTS ElevenLabs peut mal prononcer certains mots français. Voici comment les corriger :

---

## 1. Corrections Phonétiques Recommandées

### Noms de Marque / Propres

**Wipple** → Peut être mal prononcé
- Correction : "Ouipple" ou "Wippeul"
- Test : Essayer les deux versions

**Eko** → Prononcé "éco" (économie)
- Correction : "Éco" (si c'est la prononciation voulue)
- OU : "Ékko" (pour accentuer le double k)

---

### Mots Techniques

**Email** → Prononcé à l'anglaise "i-meil"
- Correction : "e-mail" OU "courrier électronique"
- Meilleur : "adresse e-mail" (plus clair au téléphone)

**Ticket** → Prononcé "tikette" ou à l'anglaise
- Correction : "tikè" OU "dossier" OU "demande"
- Recommandation : Garder "ticket" (terme professionnel accepté)

**Support technique** → OK en général
- Alternative : "service technique" (plus français)

---

### Nombres et Horaires

**"neuf heures"** → Peut être confondu avec "neuf heure" (sans s)
- Correction : "9 heures" (le chiffre est mieux prononcé)

**"quatorze heures"** → OK
- Alternative : "14 heures"

**"dix-huit heures"** → OK
- Alternative : "18 heures"

**"dix-sept heures"** → OK
- Alternative : "17 heures"

---

## 2. Astuces de Prononciation

### A. Utiliser la Ponctuation

**Virgules** → Ajoutent des pauses naturelles
```python
# Avant
"Bonjour et bienvenue au service support technique de chez Wipple"

# Après (avec pauses)
"Bonjour, et bienvenue au service support technique de chez Wipple."
```

**Points** → Créent des pauses plus longues
```python
# Avant
"Je suis Eko, votre assistant virtuel. Je vais vous aider..."

# Après (mieux rythmé)
"Je suis Eko. Votre assistant virtuel. Je vais vous aider..."
```

---

### B. Séparer les Phrases Longues

**Avant** :
```python
"Nos bureaux sont actuellement fermés. Le service technique est disponible du lundi au jeudi de neuf heures à douze heures et de quatorze heures à dix-huit heures, et le vendredi de neuf heures à douze heures et de quatorze heures à dix-sept heures."
```

**Après** (plus respirable) :
```python
"Nos bureaux sont actuellement fermés. Le service technique est disponible du lundi au jeudi, de 9h à 12h, et de 14h à 18h. Le vendredi, de 9h à 12h, et de 14h à 17h."
```

---

### C. Orthographe Phonétique

Si un mot est systématiquement mal prononcé, utilisez l'orthographe phonétique :

**Wipple** → "Ouipple"
**email** → "e-mél" OU "mél"
**Eko** → "Éco" ou "É-ko"

---

## 3. Phrases Corrigées Proposées

Voici les phrases que je recommande de corriger dans `config.py` :

```python
CACHED_PHRASES = {
    # --- Accueil ---
    "greet": "Bonjour, et bienvenue au service technique de chez Ouipple.",
    "welcome": "Je suis Éco, votre assistant virtuel. Je vais vous aider à enregistrer votre demande, afin de vous dépanner rapidement.",

    # --- Clients qui rappellent ---
    "returning_client_pending_internet": "Bonjour, je suis Éco. Vous avez un dossier ouvert concernant votre connexion. Est-ce à ce sujet ?",
    "returning_client_pending_mobile": "Bonjour, je suis Éco. Vous avez un dossier ouvert concernant votre mobile. Est-ce à ce sujet ?",
    "returning_client_no_ticket": "Bonjour, je vous reconnais. Je suis Éco. Comment puis-je vous aider ?",

    # --- Identification ---
    "ask_identity": "Pour commencer, pouvez-vous me donner votre nom, votre prénom, ainsi que le nom de votre entreprise, s'il vous plaît ?",
    "ask_firstname": "Quel est votre prénom ?",
    "ask_email": "Pouvez-vous m'épeler votre adresse mél, afin de créer un dossier ?",
    "ask_company": "Quel est le nom de votre entreprise ?",
    "email_invalid": "L'adresse que vous avez donnée semble incorrecte. Pouvez-vous la répéter ?",

    # --- Type de problème ---
    "ask_problem_or_modif": "Merci. S'agit-il d'une panne technique, ou d'une demande de modification sur votre installation ?",
    "ask_description_technique": "D'accord. Pouvez-vous m'expliquer en détail votre problème ? Prenez votre temps, je vous écoute.",
    "ask_number_equipement": "Combien d'équipements sont concernés par ce problème ?",
    "ask_restart_devices": "Avez-vous essayé de redémarrer vos équipements ?",

    # --- Confirmations courtes ---
    "ok": "D'accord.",
    "wait": "Un instant, s'il vous plaît.",

    # --- Fillers pour masquer latence ---
    "filler_hum": "Hum, laissez-moi regarder.",
    "filler_ok": "Très bien, je note.",
    "filler_one_moment": "Un instant, s'il vous plaît.",
    "filler_checking": "Je vérifie cela.",
    "filler_processing": "Je traite votre demande.",
    "filler_let_me_see": "Laissez-moi voir ça.",

    # --- Relances ---
    "still_there_gentle": "Êtes-vous toujours là ?",
    "clarify_unclear": "Je n'ai pas bien compris. Pouvez-vous reformuler ?",
    "clarify_yes_no": "Pouvez-vous me répondre par oui, ou par non ?",

    # --- Escalade technicien ---
    "transfer": "Je vous transfère à un technicien. Ne raccrochez pas.",
    "ticket_transfer_ok": "Très bien. Je vous transfère immédiatement à un technicien, qui va prendre la suite.",
    "offer_email_transfer": "Je peux vous envoyer un mél avec les détails du problème, et vous serez rappelé dans les plus brefs délais.",

    # --- Création de ticket ---
    "confirm_ticket": "Très bien. J'ai bien enregistré votre demande. Je procède maintenant à la création de votre dossier.",
    "ticket_created": "Votre dossier a été créé avec succès. Vous allez recevoir un mél de confirmation, avec le numéro de dossier.",

    # --- Suivi ticket existant ---
    "ticket_not_related": "D'accord. Quel est votre problème aujourd'hui ?",

    # --- Horaires et fermeture ---
    "closed_hours": "Nos bureaux sont actuellement fermés. Le service technique est disponible du lundi au jeudi, de 9h à 12h, et de 14h à 18h. Le vendredi, de 9h à 12h, et de 14h à 17h.",

    # --- Fin d'appel ---
    "goodbye": "Au revoir, et bonne journée. N'hésitez pas à nous rappeler si besoin.",
    "error": "Je suis désolé, une erreur technique s'est produite. Veuillez réessayer.",
}
```

---

## 4. Changements Principaux

| Avant | Après | Raison |
|-------|-------|--------|
| Wipple | Ouipple | Meilleure prononciation française |
| Eko | Éco | Évite confusion avec "éco" (économie) |
| email | mél | Terme français officiel, mieux prononcé |
| ticket | dossier | Terme français, plus clair au téléphone |
| neuf heures | 9h | Chiffres mieux prononcés que texte |
| "..." | "... ." | Ajout de pauses avec virgules |

---

## 5. Test de Prononciation

### Méthode 1 : Test Manuel

```bash
# Générer une seule phrase pour tester
python3 << EOF
import os
from elevenlabs import VoiceSettings, generate, save
from dotenv import load_dotenv

load_dotenv()

text = "Bonjour, je suis Éco. Vous avez un dossier ouvert concernant votre connexion."

audio = generate(
    text=text,
    voice="N2lVS1w4EtoT3dr4eOWO",  # Adrien
    model="eleven_turbo_v2_5",
    voice_settings=VoiceSettings(
        stability=0.5,
        similarity_boost=0.75,
        style=0.0,
        use_speaker_boost=True
    )
)

save(audio, "test_pronunciation.mp3")
print("Test audio saved to test_pronunciation.mp3")
EOF

# Écouter le résultat
ffplay test_pronunciation.mp3
```

### Méthode 2 : Tester Plusieurs Variantes

Créez un fichier `test_tts.py` :

```python
from elevenlabs import generate, save, VoiceSettings
import os
from dotenv import load_dotenv

load_dotenv()

# Tester différentes orthographes
variants = {
    "wipple_v1": "Bonjour au service de chez Wipple",
    "wipple_v2": "Bonjour au service de chez Ouipple",
    "wipple_v3": "Bonjour au service de chez Wippeul",

    "eko_v1": "Je suis Eko",
    "eko_v2": "Je suis Éco",
    "eko_v3": "Je suis É-ko",
}

for name, text in variants.items():
    audio = generate(
        text=text,
        voice="N2lVS1w4EtoT3dr4eOWO",
        model="eleven_turbo_v2_5",
        voice_settings=VoiceSettings(
            stability=0.5,
            similarity_boost=0.75,
            style=0.0,
            use_speaker_boost=True
        )
    )
    save(audio, f"test_{name}.mp3")
    print(f"Saved: test_{name}.mp3")

print("\nÉcoutez tous les fichiers et choisissez la meilleure prononciation")
```

Puis :
```bash
python3 test_tts.py
# Écouter tous les fichiers générés
```

---

## 6. Paramètres ElevenLabs pour Meilleure Prononciation

Dans `config.py`, vous pouvez ajuster :

```python
# === ElevenLabs TTS Settings ===
ELEVENLABS_VOICE_ID = "N2lVS1w4EtoT3dr4eOWO"  # Adrien - Voix française
ELEVENLABS_MODEL = "eleven_turbo_v2_5"

# Paramètres de prononciation
ELEVENLABS_STABILITY = 0.6       # ↑ Plus stable, moins de variations
ELEVENLABS_SIMILARITY_BOOST = 0.8  # ↑ Plus fidèle à la voix originale
ELEVENLABS_STYLE = 0.0           # Pas d'exagération
ELEVENLABS_USE_SPEAKER_BOOST = True  # Amélioration du locuteur
```

**Recommandations** :
- **stability** : 0.5-0.7 (bon équilibre)
- **similarity_boost** : 0.75-0.85 (clarté maximale)
- **style** : 0.0-0.2 (éviter exagération au téléphone)

---

## 7. Application des Changements

### Étape 1 : Modifier config.py

```bash
# Éditer le fichier
nano config.py

# Appliquer les corrections proposées ci-dessus
```

### Étape 2 : Régénérer le Cache Audio

```bash
# Supprimer l'ancien cache
rm -rf assets/cache/*.raw

# Régénérer avec les nouvelles phrases
./setup.sh

# Répondre 'y' quand demandé
```

### Étape 3 : Redémarrer

```bash
docker restart voicebot-app
```

### Étape 4 : Tester

Faites un appel test et écoutez la prononciation améliorée.

---

## 8. Mots Problématiques Fréquents

| Mot | Prononciation TTS | Correction |
|-----|-------------------|------------|
| WiFi | "oui-fi" | "ouifi" OU "réseau sans fil" |
| Internet | OK | - |
| Box | "boxe" (sport) | "la box" OU "le boîtier" |
| Support | "supporte" | "service technique" |
| Email | "i-meil" | "mél" OU "e-mail" |
| Ticket | "tikette" | "dossier" OU garder "ticket" |
| SAV | "S A V" (épellé) | "service après-vente" |

---

## 9. Checklist Finale

Avant de régénérer le cache :

- [ ] Tester les variantes de "Wipple" → Choisir la meilleure
- [ ] Tester les variantes de "Eko" → Choisir la meilleure
- [ ] Remplacer "email" par "mél" ou "e-mail"
- [ ] Remplacer "ticket" par "dossier" (optionnel)
- [ ] Ajouter des virgules pour les pauses
- [ ] Remplacer nombres texte par chiffres (9h au lieu de neuf heures)
- [ ] Tester une phrase avant de tout régénérer

---

## 10. Exemple de Test Rapide

```bash
# Test rapide d'une phrase
cd ~/Backup-LLM

# Activer l'environnement virtuel
source venv/bin/activate

# Tester
python3 -c "
from elevenlabs import generate, save, VoiceSettings
import os

text = 'Bonjour, je suis Éco. Vous avez un dossier ouvert.'

audio = generate(
    text=text,
    voice='N2lVS1w4EtoT3dr4eOWO',
    model='eleven_turbo_v2_5',
    voice_settings=VoiceSettings(
        stability=0.5,
        similarity_boost=0.75
    )
)

save(audio, 'test.mp3')
print('Test saved to test.mp3')
"

# Écouter (sur le serveur)
ffplay test.mp3 2>/dev/null || echo "Téléchargez test.mp3 pour écouter"
```

---

**Recommandation** : Commencez par tester 2-3 phrases clés avant de régénérer tout le cache.

Quelles phrases sont les plus problématiques pour vous ?

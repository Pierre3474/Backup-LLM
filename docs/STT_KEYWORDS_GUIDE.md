# Guide : Améliorer la reconnaissance vocale (STT) avec les Keywords

## Vue d'ensemble

Le système utilise **Deepgram** pour la reconnaissance vocale (STT - Speech-To-Text). Par défaut, Deepgram peut avoir des difficultés à reconnaître :
- 🏷️ **Noms propres** (prénoms, noms de famille)
- 🏢 **Noms d'entreprises**
-  **Termes techniques spécifiques**

La fonctionnalité **Keywords** de Deepgram permet de "booster" la reconnaissance de mots spécifiques.

## Comment ça marche ?

Le fichier `stt_keywords.yaml` contient une liste de mots avec un niveau de boost (0-4) :

```yaml
firstnames:
  - Pierre:3      # Boost de niveau 3 (recommandé pour noms propres)
  - Marie:3

telecom_companies:
  - Orange:3
  - SFR:3

technical_terms:
  - fibre:2       # Boost de niveau 2 (pour termes techniques)
  - ADSL:2
```

### Niveaux de boost recommandés

| Niveau | Usage | Exemple |
|--------|-------|---------|
| **3** | Noms propres (prénoms, noms, entreprises) | Pierre:3, Dupont:3, Orange:3 |
| **2** | Termes techniques courants | fibre:2, ADSL:2, WiFi:2 |
| **1** | Termes peu courants | - |
| **4** |  À éviter (trop agressif) | - |

## Comment ajouter de nouveaux keywords ?

### 1. Éditer le fichier `stt_keywords.yaml`

```bash
nano stt_keywords.yaml
```

### 2. Ajouter vos keywords dans la catégorie appropriée

**Exemple : Ajouter un prénom client fréquent**
```yaml
firstnames:
  - Pierre:3
  - Jean:3
  - Maxime:3      # ← Nouveau prénom
```

**Exemple : Ajouter une entreprise cliente**
```yaml
telecom_companies:
  - Orange:3
  - SFR:3
  - MonEntrepriseSAV:3    # ← Nouvelle entreprise
```

**Exemple : Ajouter un terme technique spécifique**
```yaml
technical_terms:
  - fibre:2
  - "fibre optique":2     # ← Utiliser des guillemets pour les expressions
  - FTTH:2                # ← Nouvel acronyme
```

### 3. Redémarrer le serveur

Les keywords sont chargés au démarrage de chaque appel :

```bash
systemctl restart voicebot
```

## Limites et bonnes pratiques

### Limites de performance

- **Maximum recommandé** : 100-200 keywords
- **Au-delà** : Risque de ralentissement et faux positifs
- **Actuellement** : ~150 keywords chargés

### Bonnes pratiques

 **À FAIRE**
- Ajouter les noms de vos clients les plus fréquents
- Utiliser niveau 3 pour les noms propres
- Utiliser niveau 2 pour les termes techniques
- Tester après chaque ajout important

 **À ÉVITER**
- Ajouter des mots trop courants (le, la, de, etc.)
- Utiliser boost niveau 4 (trop agressif)
- Dépasser 200 keywords
- Ajouter des mots qui se ressemblent phonétiquement

### Exemples de ce qu'il NE faut PAS ajouter

```yaml
#  MAUVAIS EXEMPLES
common_words:
  - bonjour:3     # Mot trop courant, déjà bien reconnu
  - merci:3       # Mot trop courant
  - problème:3    # Mot trop courant
  - internet:3    # Mot trop courant dans un contexte SAV télécom
```

## Comment tester l'amélioration ?

### 1. Avant l'ajout

Faites un appel test et notez les erreurs de transcription :

```
User: "Je m'appelle Pier et je suis client chez Oranje"
                     ^^^^                         ^^^^^^
                     Erreur                       Erreur
```

### 2. Ajouter les keywords

```yaml
firstnames:
  - Pierre:3

telecom_companies:
  - Orange:3
```

### 3. Après l'ajout

Refaites un appel test :

```
User: "Je m'appelle Pierre et je suis client chez Orange"
                     ✓                              ✓
                     Correct                        Correct
```

## Analyse des logs

Pour vérifier que les keywords sont bien chargés :

```bash
journalctl -u voicebot -f | grep "STT keywords"
```

Vous devriez voir :
```
✓ Loaded 150 STT keywords for improved recognition
```

## Dépannage

### Problème : Keywords non chargés

**Symptôme** :
```
stt_keywords.yaml not found, STT will work without keyword boosting
```

**Solution** :
```bash
# Vérifier l'emplacement du fichier
ls -la /opt/voicebot/stt_keywords.yaml

# Vérifier les permissions
chmod 644 stt_keywords.yaml
```

### Problème : Erreur de syntaxe YAML

**Symptôme** :
```
Failed to load STT keywords: ...
```

**Solution** :
```bash
# Valider la syntaxe YAML
python3 -c "import yaml; yaml.safe_load(open('stt_keywords.yaml'))"
```

### Problème : Trop de faux positifs

**Symptôme** : Le système "entend" des mots qui n'ont pas été dits

**Solution** : Réduire le niveau de boost ou retirer les keywords problématiques

```yaml
# Avant (trop agressif)
- Pierre:4

# Après (équilibré)
- Pierre:3
```

## Métriques de succès

Indicateurs pour mesurer l'amélioration :

1. **Taux de reconnaissance des noms propres**
   - Avant : ~60-70%
   - Objectif : ~90-95%

2. **Réduction des erreurs de transcription**
   - Mesurer le nombre d'erreurs avant/après

3. **Satisfaction utilisateur**
   - Le bot comprend-il mieux les noms au premier coup ?

## 🔗 Ressources

- [Documentation Deepgram Keywords](https://developers.deepgram.com/docs/keywords)
- [Guide Deepgram - Améliorer la précision](https://developers.deepgram.com/docs/accuracy-best-practices)

## Support

Pour toute question sur la configuration des keywords :
- Consulter les logs : `journalctl -u voicebot -f`
- Vérifier la charge : Ne pas dépasser 200 keywords
- Tester progressivement : Ajouter par lots de 10-20 keywords

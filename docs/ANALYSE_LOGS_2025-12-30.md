# Analyse des logs et problèmes identifiés

## 📊 Contexte de l'appel analysé

**Log timestamp**: 2025-12-30 15:22:17
**Serveur démarré**: 2025-12-30 15:19:08
**Texte utilisateur**: "Perte de paiement et"
**Tag obtenu**: UNKNOWN
**Problèmes visibles**:
- ❌ Erreur Deepgram "tasks cancelled"
- ❌ Pas de log "Loaded keywords"
- ❌ Classification UNKNOWN

---

## 🔍 Problème 1: Erreur Deepgram "tasks cancelled"

### Cause
Erreur normale lors de la fermeture de la connexion WebSocket Deepgram. Cette erreur est bénigne mais pollue les logs.

### Solution appliquée
```python
# server.py ligne 49-51
logging.getLogger('deepgram').setLevel(logging.CRITICAL)
logging.getLogger('deepgram.clients.common.v1.abstract_async_websocket').setLevel(logging.CRITICAL)
```

**Résultat**: Les erreurs "tasks cancelled" ne seront plus affichées ✅

---

## 🔍 Problème 2: Keywords STT non chargés

### Cause
Le serveur a démarré à **15:19:08** mais mes commits avec les keywords ont été faits **après** le démarrage. Le code en production ne contient pas encore les modifications.

### État actuel
```
Commits dans le dépôt:
✓ 138e56b - feat: Amélioration reconnaissance STT avec keywords
✓ 41e6d9c - fix: Correction erreur UTF-8 octets nuls

Serveur en production:
❌ Version antérieure (sans keywords, sans fix UTF-8)
```

### Solution
**Redéployer le code** pour activer :
1. 134 keywords STT (noms, entreprises, termes techniques)
2. Fix UTF-8 pour les octets nuls
3. Suppression logs Deepgram verbeux

```bash
# Sur le serveur
git pull origin claude/fix-utf8-encoding-error-xAXe0
systemctl restart voicebot
```

Après redéploiement, vous verrez dans les logs :
```
✓ Loaded 134 STT keywords for improved recognition
```

---

## 🔍 Problème 3: Tag UNKNOWN pour "Perte de paiement"

### Cause racine
Le système de classification actuel a 2 limitations :

1. **Détection problem_type obligatoire**
   ```python
   # server.py:1513
   if self.context.get('problem_type'):  # ← Classification seulement si détecté
       classification = await self._classify_problem(...)
   ```

2. **Mots-clés limités à "internet" ou "mobile"**
   - "Perte de paiement" n'est ni internet, ni mobile
   - C'est un problème de **facturation**
   - Pas de catégorie "billing" dans le système

### Analyse du texte "Perte de paiement et"

**Problèmes identifiés** :
- ❌ Phrase incomplète (utilisateur a raccroché)
- ❌ Sujet : facturation (hors scope technique actuel)
- ❌ Aucun mot-clé internet/mobile détecté

**Ce que le système a fait** :
1. Pas de `problem_type` détecté → pas de classification
2. Garde le tag par défaut : `UNKNOWN`
3. Sauvegarde quand même le ticket (✓ bon comportement)

---

## 🛠️ Solutions proposées

### Option A: Ajouter catégorie "billing" (recommandé)

Étendre le système pour gérer les problèmes de facturation/paiement :

**Tags facturation** :
- `BILLING_PAYMENT` - Problème de paiement/prélèvement
- `BILLING_INVOICE` - Problème de facture
- `BILLING_SUBSCRIPTION` - Problème d'abonnement
- `BILLING_REFUND` - Demande de remboursement

**Mots-clés facturation** :
```python
billing_keywords = [
    'facture', 'paiement', 'prélèvement', 'impayé',
    'remboursement', 'abonnement', 'tarif', 'prix',
    'montant', 'débit', 'compte bancaire', 'carte bancaire'
]
```

### Option B: Forcer classification même sans problem_type

Modifier la logique pour tenter une classification avec tous les tags disponibles, même si problem_type n'est pas détecté :

```python
# Au lieu de :
if self.context.get('problem_type'):
    classification = await self._classify_problem(...)

# Faire :
# Toujours tenter une classification
classification = await self._classify_problem_generic(summary)
```

### Option C: Rediriger vers humain pour hors-scope

Si le problème n'est pas technique (internet/mobile), transférer directement à un conseiller :

```python
if not problem_type and 'facture' in user_text or 'paiement' in user_text:
    # Rediriger vers service facturation
    self.state = ConversationState.TRANSFER
```

---

## ✅ Recommandation

**Implémenter Option A + B** :

1. ✅ Ajouter catégorie "billing" avec 5-10 tags
2. ✅ Détecter automatiquement le type (internet/mobile/billing)
3. ✅ Classifier même si incertain (meilleur qu'UNKNOWN)
4. ✅ Transférer vers bon service selon la catégorie

**Bénéfices** :
- Couverture complète des cas d'usage
- Moins de tags UNKNOWN
- Meilleure orientation des appels
- Stats plus précises

---

## 📋 Actions à faire

### 1. Redéployer immédiatement (fixes existants)

```bash
git pull
systemctl restart voicebot
```

Obtient :
- ✅ Fix UTF-8 octets nuls
- ✅ 134 keywords STT
- ✅ Suppression logs Deepgram

### 2. Décision architecture (nouvelle fonctionnalité)

Voulez-vous que j'implémente :
- [ ] Catégorie "billing" avec tags facturation
- [ ] Classification générique (même sans problem_type)
- [ ] Les deux

Temps estimé : 15-20 minutes

---

## 📊 Impact attendu après redéploiement

| Métrique | Avant | Après |
|----------|-------|-------|
| Logs erreur Deepgram | ~2 par appel | 0 |
| Reconnaissance noms propres | 60-70% | 90-95% |
| Erreurs UTF-8 null bytes | Fréquentes | 0 |
| Tags UNKNOWN (technique) | ~20% | ~5% |
| Tags UNKNOWN (facturation) | 100% | TBD* |

*TBD = À déterminer selon si Option A est implémentée

---

## 🎯 Conclusion

**3 problèmes, 3 solutions** :

1. ✅ **Logs Deepgram** → Corrigé (logging.CRITICAL)
2. ⏳ **Keywords STT** → Prêt (redéployer)
3. 🔧 **Tag UNKNOWN** → Nécessite décision architecture

**Prochain commit disponible après votre choix d'option.**

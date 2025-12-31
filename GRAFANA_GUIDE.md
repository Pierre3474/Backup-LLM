# 📊 Guide Grafana - Monitoring Voicebot

## 🎯 Qu'est-ce que Grafana ?

**Grafana** est votre tableau de bord principal pour monitorer les performances et le ROI du voicebot en temps réel.

**Différence avec le Dashboard Streamlit (Port 8501)** :
- **Streamlit** : Détails des appels + écoute audio
- **Grafana** : Métriques temps réel + graphiques + alertes

---

## 🌐 Accès à Grafana

```
http://145.239.223.188:3000
```

**Identifiants par défaut** :
- **Username** : `admin`
- **Password** : `admin`

⚠️ **IMPORTANT** : Changez le mot de passe lors de la première connexion !

---

## ✅ Vérification que Grafana Tourne

```bash
# Vérifier le conteneur
docker ps | grep grafana

# Voir les logs
docker logs voicebot-grafana --tail 50

# Redémarrer si besoin
docker restart voicebot-grafana
```

**Logs attendus** :
```
logger=settings t=2025-12-31T10:00:00+0000 lvl=info msg="Starting Grafana"
HTTP Server Listen addr=0.0.0.0:3000 protocol=http
```

---

## 📊 Dashboard Pré-configuré : "Voicebot ROI"

Grafana est déjà configuré avec un dashboard complet qui affiche :

### 1. 💰 Métriques ROI (Coûts)

| Métrique | Description | Formule |
|----------|-------------|---------|
| **Coût par appel** | Coût total API par appel | (ElevenLabs + Deepgram + Groq) / Nombre appels |
| **Économies cache TTS** | % d'économies grâce au cache | (Cache hits / Total requests) * 100 |
| **Coût total journalier** | Dépenses API du jour | Somme de toutes les API |

### 2. 📞 Métriques Business

| Métrique | Description |
|----------|-------------|
| **Appels traités** | Nombre total d'appels |
| **Taux de résolution** | % d'appels résolus automatiquement |
| **Durée moyenne** | Temps moyen de traitement |
| **Sentiment client** | Distribution positif/neutre/négatif |

### 3. ⚡ Métriques Performance

| Métrique | Description |
|----------|-------------|
| **Latence STT** | Temps de transcription Deepgram |
| **Latence LLM** | Temps de réponse Groq |
| **Latence TTS** | Temps de génération ElevenLabs |
| **Appels simultanés** | Nombre d'appels en cours |

### 4. 🏷️ Distribution des Problèmes

- Pannes Internet
- Problèmes Mobile
- Problèmes inconnus

---

## 🔧 Configuration Actuelle

### 1. Source de Données : Prometheus

Grafana récupère les métriques depuis **Prometheus** (port 9091).

**Fichier de config** : `monitoring/grafana/provisioning/datasources/prometheus.yml`

```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    url: http://voicebot-app:9091
    access: proxy
    isDefault: true
```

### 2. Dashboard Auto-chargé

**Fichier** : `monitoring/grafana/dashboards/voicebot-roi.json`

Ce dashboard est automatiquement chargé au démarrage de Grafana.

---

## 🚀 Démarrage de Grafana

### Avec Docker Compose

```bash
# Démarrer Grafana uniquement
docker compose up -d grafana

# Démarrer Grafana + Prometheus
docker compose up -d prometheus grafana

# Démarrer tous les services de monitoring
docker compose up -d voicebot-app prometheus grafana dashboard
```

### Vérifier que tout fonctionne

```bash
# Vérifier les conteneurs
docker ps | grep -E "grafana|prometheus"

# Tester l'accès Grafana
curl http://localhost:3000/api/health
```

**Résultat attendu** :
```json
{
  "commit": "...",
  "database": "ok",
  "version": "10.x.x"
}
```

---

## 📈 Utilisation du Dashboard

### 1. Accéder au Dashboard Pré-configuré

1. Ouvrir http://145.239.223.188:3000
2. Se connecter avec `admin` / `admin`
3. Changer le mot de passe
4. Aller dans **Dashboards** → **Voicebot ROI**

### 2. Période d'Affichage

En haut à droite, vous pouvez choisir la période :
- **Last 5 minutes** (temps réel)
- **Last 1 hour**
- **Last 24 hours**
- **Last 7 days**
- **Custom range** (période personnalisée)

### 3. Rafraîchissement Auto

Activez le rafraîchissement automatique :
- Cliquez sur l'icône ⟳ en haut à droite
- Choisissez : 5s, 10s, 30s, 1m, 5m

---

## 🔍 Métriques Disponibles

Toutes les métriques exposées par le voicebot :

### Appels
```
voicebot_calls_total{status="completed", problem_type="internet"}
voicebot_call_duration_seconds
voicebot_active_calls
```

### Sentiment Client
```
voicebot_client_sentiment_total{sentiment="positive"}
voicebot_client_sentiment_total{sentiment="negative"}
```

### Tickets
```
voicebot_tickets_created_total{severity="HIGH", tag="INTERNET_DOWN"}
```

### Coûts API
```
# ElevenLabs (TTS)
voicebot_elevenlabs_requests_total{type="cache_hit"}
voicebot_elevenlabs_requests_total{type="api_call"}
voicebot_elevenlabs_characters_total

# Deepgram (STT)
voicebot_deepgram_requests_total
voicebot_deepgram_audio_seconds_total

# Groq (LLM)
voicebot_groq_requests_total{model="llama-3.1-70b-versatile"}
voicebot_groq_tokens_input_total
voicebot_groq_tokens_output_total
```

### Performance
```
voicebot_tts_response_seconds{source="cache"}
voicebot_tts_response_seconds{source="elevenlabs"}
voicebot_stt_response_seconds
voicebot_llm_response_seconds{task="understanding"}
```

---

## 💡 Exemples de Requêtes PromQL

### Coût Total par Appel

```promql
(
  (voicebot_elevenlabs_characters_total * 0.00011) +
  (voicebot_deepgram_audio_seconds_total * 0.0043 / 60) +
  ((voicebot_groq_tokens_input_total + voicebot_groq_tokens_output_total) * 0.00000059)
) / voicebot_calls_total
```

### Taux de Résolution Automatique

```promql
(
  sum(voicebot_calls_total{status="completed"}) /
  sum(voicebot_calls_total)
) * 100
```

### % Économies Cache TTS

```promql
(
  voicebot_elevenlabs_requests_total{type="cache_hit"} /
  (voicebot_elevenlabs_requests_total{type="cache_hit"} + voicebot_elevenlabs_requests_total{type="api_call"})
) * 100
```

### Appels par Heure

```promql
rate(voicebot_calls_total[1h]) * 3600
```

---

## 🎨 Personnaliser le Dashboard

### Ajouter un Nouveau Panel

1. Cliquer sur **Add** → **Visualization**
2. Choisir **Prometheus** comme source
3. Entrer une requête PromQL
4. Choisir le type de graphique (Time series, Gauge, Stat, etc.)
5. Configurer les seuils et couleurs
6. Sauvegarder

### Exemple : Panel "Appels en Cours"

```
Panel Title: Appels Simultanés
Query: voicebot_active_calls
Visualization: Stat
Unit: calls
Thresholds:
  - Green: 0-5
  - Yellow: 5-10
  - Red: 10+
```

---

## 🔔 Alertes (Optionnel)

### Créer une Alerte

**Exemple** : Alerter si plus de 10 appels simultanés

1. Éditer un panel
2. Onglet **Alert**
3. **Create alert rule**
4. **Condition** : `voicebot_active_calls > 10`
5. **Evaluation** : Every 1m for 5m
6. **Notification** : Email ou Slack

---

## 🆚 Grafana vs Dashboard Streamlit

| Feature | Grafana (Port 3000) | Streamlit (Port 8501) |
|---------|---------------------|------------------------|
| **Métriques temps réel** | ✅ Oui | ❌ Non |
| **Graphiques avancés** | ✅ Oui | ❌ Non |
| **Alertes** | ✅ Oui | ❌ Non |
| **Historique** | ✅ Oui (Prometheus) | ❌ Non |
| **Détails des tickets** | ❌ Non | ✅ Oui |
| **Écoute audio** | ❌ Non | ✅ Oui |
| **ROI / Coûts** | ✅ Oui | ❌ Non |

**Recommandation** : Utilisez les deux !
- **Grafana** pour le monitoring global et les tendances
- **Streamlit** pour analyser les appels individuels

---

## 🔧 Résolution de Problèmes

### ❌ "Unable to connect to Prometheus"

**Cause** : Prometheus n'est pas accessible

**Solution** :
```bash
# Vérifier que Prometheus tourne
docker ps | grep prometheus

# Vérifier les logs
docker logs voicebot-prometheus

# Redémarrer
docker restart voicebot-prometheus

# Vérifier l'endpoint
curl http://localhost:9092/api/v1/query?query=up
```

---

### ❌ "No data" dans les graphiques

**Cause** : Aucune métrique collectée (pas d'appels)

**Solution** : Faites un appel test au voicebot pour générer des métriques

---

### ❌ Dashboard "Voicebot ROI" introuvable

**Cause** : Dashboard non chargé automatiquement

**Solution** :
```bash
# Vérifier que le fichier existe
ls -la monitoring/grafana/dashboards/voicebot-roi.json

# Redémarrer Grafana
docker restart voicebot-grafana

# Importer manuellement :
# Grafana → Dashboards → Import → Upload JSON file
```

---

### ❌ Impossible de se connecter (mot de passe oublié)

**Solution** : Réinitialiser le mot de passe admin

```bash
# Se connecter au conteneur
docker exec -it voicebot-grafana grafana-cli admin reset-admin-password newpassword

# Ou réinitialiser complètement Grafana
docker compose down
docker volume rm backup-llm_grafana_data
docker compose up -d grafana
```

---

## 📊 Ports du Stack de Monitoring

| Service | Port | URL | Description |
|---------|------|-----|-------------|
| **Voicebot** | 9090 | - | Serveur principal |
| **Métriques** | 9091 | http://145.239.223.188:9091 | Endpoint Prometheus |
| **Prometheus** | 9092 | http://145.239.223.188:9092 | Interface Prometheus |
| **Grafana** | 3000 | http://145.239.223.188:3000 | Dashboards |
| **Dashboard** | 8501 | http://145.239.223.188:8501 | Streamlit |

---

## ✅ Checklist de Démarrage

Avant d'utiliser Grafana :

- [ ] Voicebot tourne (`docker ps | grep voicebot-app`)
- [ ] Prometheus tourne (`docker ps | grep prometheus`)
- [ ] Grafana tourne (`docker ps | grep grafana`)
- [ ] Métriques accessibles (curl http://localhost:9091/)
- [ ] Grafana accessible (http://145.239.223.188:3000)
- [ ] Mot de passe admin changé
- [ ] Dashboard "Voicebot ROI" visible
- [ ] Au moins 1 appel effectué pour avoir des données

---

## 🎉 Exemple de Dashboard Complet

Votre dashboard Grafana devrait afficher :

```
╔══════════════════════════════════════════════════════════════╗
║                    📊 VOICEBOT ROI DASHBOARD                 ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  💰 COÛTS (Aujourd'hui)                                      ║
║  ┌─────────────┬──────────────┬─────────────┬──────────────┐║
║  │ Coût Total  │ Coût/Appel   │ Économies   │ Cache Hit    │║
║  │   $2.45     │    $0.12     │   $1.80     │     65%      │║
║  └─────────────┴──────────────┴─────────────┴──────────────┘║
║                                                              ║
║  📞 BUSINESS KPIs                                            ║
║  ┌─────────────┬──────────────┬─────────────┬──────────────┐║
║  │   Appels    │ Résolution   │  Duration   │  Sentiment   │║
║  │     20      │     85%      │    120s     │  🙂 70%      │║
║  └─────────────┴──────────────┴─────────────┴──────────────┘║
║                                                              ║
║  📈 GRAPHIQUES TEMPS RÉEL                                    ║
║  ┌──────────────────────────────────────────────────────────┐║
║  │ Appels par heure                                         │║
║  │ ████▁▁▁███▁▁████▁▁▁██                                    │║
║  └──────────────────────────────────────────────────────────┘║
║                                                              ║
║  ┌──────────────────────────────────────────────────────────┐║
║  │ Distribution des problèmes                               │║
║  │ Internet: ████████ 60%                                   │║
║  │ Mobile:   ████ 30%                                       │║
║  │ Autre:    ██ 10%                                         │║
║  └──────────────────────────────────────────────────────────┘║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 🚀 Commandes Rapides

```bash
# Démarrer le monitoring complet
docker compose up -d voicebot-app prometheus grafana

# Vérifier l'état
docker ps | grep -E "voicebot|prometheus|grafana"

# Voir les logs
docker logs -f voicebot-grafana

# Accès rapide
open http://145.239.223.188:3000  # macOS
xdg-open http://145.239.223.188:3000  # Linux

# Redémarrer tout le stack monitoring
docker restart voicebot-app voicebot-prometheus voicebot-grafana
```

---

**Status** : ✅ Grafana pré-configuré et prêt à l'emploi
**Date** : 2025-12-31
**Version** : 2.1
**Port** : 3000
**Dashboard** : Voicebot ROI (auto-chargé)

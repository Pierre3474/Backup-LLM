# Quick Start - Migration ElevenLabs

## ⚡ Déploiement rapide sur le serveur SSH

### 1. Se connecter au serveur
```bash
ssh root@145.239.223.189
cd /root/PY_SAV
```

### 2. Mettre à jour le code
```bash
git pull origin main
```

### 3. Configurer la clé API
Éditez le fichier `.env` et ajoutez votre clé ElevenLabs :
```bash
nano .env
```

Ajoutez la ligne :
```
ELEVENLABS_API_KEY=sk_3XXXXXX35c226620bc049
```

**Note** : Remplacez `sk_3XXXXXX35c226620bc049` par votre vraie clé API.

### 4. Déployer automatiquement
```bash
chmod +x deploy_elevenlabs.sh
./deploy_elevenlabs.sh
```

Le script va :
- ✅ Installer ElevenLabs
- ✅ Vérifier les clés API
- ✅ Sauvegarder l'ancien cache OpenAI
- ✅ Générer les 27 fichiers audio avec la voix ElevenLabs
- ✅ Proposer de tester le serveur

### 5. Tester
```bash
python server.py
```

Faites un appel test depuis Asterisk pour vérifier que tout fonctionne.

---

## 🔍 Vérification

### Vérifier que le cache est généré
```bash
ls -l assets/cache/*.raw | wc -l
# Devrait afficher: 27
```

### Vérifier les logs du serveur
```bash
tail -f logs/calls/*.log
```

### Vérifier les métriques Prometheus
Ouvrez dans votre navigateur :
```
http://145.239.223.189:9091/metrics
```

Cherchez :
- `voicebot_elevenlabs_tts_errors_total` (devrait être 0)
- `voicebot_api_latency_seconds{api="elevenlabs_tts"}`

---

## 🎯 Fichiers modifiés

- ✅ `config.py` - Configuration ElevenLabs
- ✅ `server.py` - Intégration API ElevenLabs
- ✅ `generate_cache.py` - Génération cache avec ElevenLabs
- ✅ `requirements.txt` - Dépendance ElevenLabs

## 📋 Liste des 27 phrases en cache

1. greet
2. welcome
3. ask_identity
4. ask_firstname
5. ask_email
6. ask_company
7. email_invalid
8. ask_problem_or_modif
9. ask_description_technique
10. ask_number_equipement
11. ask_restart_devices
12. ok
13. wait
14. filler_checking
15. filler_processing
16. still_there_gentle
17. clarify_unclear
18. clarify_yes_no
19. transfer
20. ticket_transfer_ok
21. offer_email_transfer
22. confirm_ticket
23. ticket_created
24. ticket_not_related
25. closed_hours
26. goodbye
27. error

---

## 🆘 Rollback (si problème)

Si vous devez revenir à OpenAI :

```bash
cd /root/PY_SAV
git log --oneline -5  # Trouver le commit avant la migration
git checkout <commit-hash-avant-migration> .
pip install openai==1.54.4
# Restaurer l'ancien cache
cp -r assets/cache_backup_XXXXXX/* assets/cache/
python server.py
```

---

## 📞 Support

- Documentation complète : `MIGRATION_ELEVENLABS.md`
- ElevenLabs Docs : https://elevenlabs.io/docs
- API Reference : https://elevenlabs.io/docs/api-reference/text-to-speech

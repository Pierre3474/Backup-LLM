#!/usr/bin/env python3
"""
Test de connexion Deepgram STT
"""
import asyncio
import os
from dotenv import load_dotenv
from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents

load_dotenv()

async def test_deepgram():
    print("=" * 60)
    print("🎙️  Test Deepgram STT")
    print("=" * 60)

    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        print("❌ DEEPGRAM_API_KEY non trouvée dans .env")
        return False

    print(f"✓ Clé API: {api_key[:20]}...")

    try:
        # Créer le client
        client = DeepgramClient(api_key)
        print("✓ Client Deepgram créé")

        # Créer la connexion
        connection = client.listen.asyncwebsocket.v("1")
        print("✓ Connexion asynclive créée")

        # Options
        options = LiveOptions(
            model="nova-2",
            language="fr",
            encoding="linear16",
            sample_rate=8000,
            channels=1,
            interim_results=True,
            punctuate=True,
            vad_events=True
        )
        print("✓ Options configurées")

        # Handlers
        async def on_open(self, open_event, **kwargs):
            print("✅ Connexion WebSocket OUVERTE")

        async def on_error(self, error, **kwargs):
            print(f"❌ Erreur: {error}")

        connection.on(LiveTranscriptionEvents.Open, on_open)
        connection.on(LiveTranscriptionEvents.Error, on_error)

        # Démarrer
        print("🔄 Tentative de connexion au serveur Deepgram...")
        result = await connection.start(options)

        if result:
            print("✅ CONNEXION RÉUSSIE !")
            print("✓ Deepgram STT fonctionne correctement")
            await connection.finish()
            return True
        else:
            print("❌ CONNEXION ÉCHOUÉE")
            print("⚠️  Vérifiez votre clé API sur https://console.deepgram.com/")
            return False

    except Exception as e:
        print(f"❌ ERREUR: {e}")
        print("⚠️  Causes possibles:")
        print("   - Clé API invalide ou expirée")
        print("   - Quota Deepgram épuisé")
        print("   - Problème de connexion réseau")
        print("\n🔧 Solution: Créez une nouvelle clé sur https://console.deepgram.com/")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_deepgram())
    exit(0 if success else 1)

import os
import glob
import wave
import io
from pathlib import Path

import psycopg2
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Chargement de la configuration
load_dotenv()
st.set_page_config(page_title="Wipple SAV Cockpit", layout="wide")

# Configuration des chemins (relatif à la racine du projet)
LOGS_DIR = Path("logs/calls")


def get_db_connection():
    """Établit la connexion à la base de données PostgreSQL"""
    try:
        return psycopg2.connect(os.getenv("DB_TICKETS_DSN"))
    except Exception as e:
        st.error(f"Erreur de connexion DB: {e}")
        return None


def convert_raw_to_wav(raw_data, sample_rate=8000):
    """Convertit les données RAW (PCM 16-bit 8kHz mono) en WAV pour le navigateur"""
    with io.BytesIO() as wav_buffer:
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)      # Mono
            wav_file.setsampwidth(2)      # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(raw_data)
        return wav_buffer.getvalue()


def find_audio_file(call_uuid):
    """Cherche le fichier .raw correspondant à un UUID d'appel"""
    if not call_uuid:
        return None

    # Le format de fichier dans server.py est : call_{uuid}_{timestamp}.raw
    # On cherche tout fichier contenant l'UUID
    search_pattern = LOGS_DIR / f"call_{call_uuid}_*.raw"
    files = list(glob.glob(str(search_pattern)))

    if files:
        # S'il y en a plusieurs (rare), on prend le plus récent
        return sorted(files)[-1]
    return None


st.title("🎛️ Supervision SAV Wipple")

conn = get_db_connection()

if conn:
    try:
        # 1. KPIs (Indicateurs Clés)
        col1, col2, col3, col4 = st.columns(4)

        # Appels du jour
        count = pd.read_sql(
            "SELECT COUNT(*) FROM tickets WHERE DATE(created_at) = CURRENT_DATE", conn
        ).iloc[0, 0]
        col1.metric("Appels du Jour", count)

        # Durée moyenne
        avg = pd.read_sql(
            "SELECT COALESCE(AVG(duration_seconds),0) FROM tickets", conn
        ).iloc[0, 0]
        col2.metric("Durée Moyenne", f"{int(avg)}s")

        # Clients mécontents
        angry = pd.read_sql(
            "SELECT COUNT(*) FROM tickets WHERE sentiment = 'negative'", conn
        ).iloc[0, 0]
        col3.metric("Clients Mécontents", angry, delta_color="inverse")

        # Pannes Internet
        internet = pd.read_sql(
            "SELECT COUNT(*) FROM tickets WHERE problem_type = 'internet'", conn
        ).iloc[0, 0]
        col4.metric("Pannes Internet", internet)

        # 2. Liste des tickets avec lecture audio
        st.subheader("Derniers Tickets & Enregistrements")

        # Récupération des données
        df = pd.read_sql(
            """
            SELECT
                created_at,
                call_uuid,
                phone_number,
                problem_type,
                status,
                sentiment,
                summary,
                duration_seconds,
                tag,
                severity
            FROM tickets
            ORDER BY created_at DESC
            LIMIT 50
            """,
            conn,
        )

        # Affichage personnalisé pour chaque ticket
        for index, row in df.iterrows():
            # Couleur de la bordure selon le sentiment
            sentiment_emoji = "😐"
            if row['sentiment'] == 'positive': sentiment_emoji = "🙂"
            elif row['sentiment'] == 'negative': sentiment_emoji = "😡"

            # Titre de l'expander
            expander_title = (
                f"{sentiment_emoji} {row['created_at'].strftime('%H:%M')} - "
                f"{row['phone_number']} - {row['problem_type'].upper()} "
                f"({row['status']})"
            )

            with st.expander(expander_title):
                c1, c2 = st.columns([2, 1])

                with c1:
                    st.markdown(f"**Résumé :** {row['summary']}")
                    st.markdown(f"**Tag :** `{row['tag']}` | **Sévérité :** `{row['severity']}`")
                    st.caption(f"UUID: {row['call_uuid']}")

                with c2:
                    # Recherche et lecture du fichier audio
                    audio_path = find_audio_file(row['call_uuid'])

                    if audio_path and os.path.exists(audio_path):
                        try:
                            with open(audio_path, "rb") as f:
                                raw_data = f.read()

                            # Conversion à la volée
                            wav_data = convert_raw_to_wav(raw_data)

                            st.audio(wav_data, format="audio/wav")
                            st.caption("🎧 Enregistrement converti (WAV)")

                        except Exception as e:
                            st.error(f"Erreur lecture: {e}")
                    else:
                        st.warning("⚠️ Audio non trouvé")

    except Exception as e:
        st.error(f"Erreur globale: {e}")
    finally:
        conn.close()
else:
    st.error("Impossible de se connecter à la base de données.")


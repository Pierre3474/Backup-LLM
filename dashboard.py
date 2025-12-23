import os
import glob
import wave
import io
from pathlib import Path

import psycopg2
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from streamlit.runtime.scriptrunner import get_script_run_ctx
from streamlit.web.server.websocket_headers import _get_websocket_headers

# Chargement de la configuration
load_dotenv()
st.set_page_config(page_title="Wipple SAV Cockpit", layout="wide")

# ============================================
# SÉCURITÉ : Validation IP
# ============================================

def get_client_ip():
    """Récupère l'IP réelle du client depuis les headers de la requête"""
    try:
        ctx = get_script_run_ctx()
        if ctx is None:
            return None

        # Tenter d'obtenir les headers WebSocket
        headers = _get_websocket_headers()

        if headers:
            # Vérifier X-Forwarded-For (proxy/reverse proxy)
            forwarded_for = headers.get("X-Forwarded-For")
            if forwarded_for:
                # X-Forwarded-For peut contenir plusieurs IPs séparées par des virgules
                # La première est l'IP réelle du client
                return forwarded_for.split(',')[0].strip()

            # Vérifier X-Real-IP (nginx)
            real_ip = headers.get("X-Real-IP")
            if real_ip:
                return real_ip.strip()

            # Fallback: Remote-Addr
            remote_addr = headers.get("Remote-Addr")
            if remote_addr:
                return remote_addr.strip()

        return None
    except Exception as e:
        st.warning(f"Impossible de récupérer l'IP client: {e}")
        return None


def validate_ip_access():
    """Valide que l'IP du visiteur est autorisée"""
    # Récupérer la liste des IPs autorisées depuis .env
    allowed_ips_str = os.getenv("PERSONAL_IP", "")

    if not allowed_ips_str:
        st.error("🚫 ERREUR DE CONFIGURATION: Aucune IP autorisée définie (PERSONAL_IP manquant)")
        st.stop()

    # Parser les IPs autorisées (séparées par virgules)
    allowed_ips = [ip.strip() for ip in allowed_ips_str.split(',') if ip.strip()]

    # Récupérer l'IP du client
    client_ip = get_client_ip()

    if client_ip is None:
        st.error("🚫 ACCÈS REFUSÉ: Impossible de déterminer votre adresse IP")
        st.info("Ce dashboard est protégé. Contactez l'administrateur.")
        st.stop()

    # Vérifier si l'IP est autorisée
    if client_ip not in allowed_ips:
        st.error(f"🚫 ACCÈS REFUSÉ")
        st.warning(f"Votre IP ({client_ip}) n'est pas autorisée à accéder à ce dashboard.")
        st.info("IPs autorisées: " + ", ".join(allowed_ips))
        st.caption("Contactez l'administrateur système pour obtenir l'accès.")
        st.stop()

    # Accès autorisé
    st.success(f"✅ Accès autorisé depuis {client_ip}")


# Vérifier l'accès avant toute opération
validate_ip_access()

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


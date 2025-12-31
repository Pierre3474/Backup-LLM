import os
import glob
import wave
import io
from pathlib import Path
from datetime import datetime

import psycopg2
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Chargement de la configuration
load_dotenv()
st.set_page_config(page_title="Wipple SAV Cockpit", layout="wide")

# Configuration des chemins (relatif à la racine du projet)
LOGS_DIR = Path("logs/calls")

# ============================================
# SÉCURITÉ : Validation IP (OPTIONNELLE)
# ============================================

def get_client_ip():
    """Récupère l'IP réelle du client depuis les headers de la requête"""
    try:
        # Essayer de récupérer depuis streamlit
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        ctx = get_script_run_ctx()
        if ctx is None:
            return None

        # Essayer les headers
        try:
            from streamlit.web.server.websocket_headers import _get_websocket_headers
            headers = _get_websocket_headers()

            if headers:
                # X-Forwarded-For (proxy/reverse proxy)
                forwarded_for = headers.get("X-Forwarded-For")
                if forwarded_for:
                    return forwarded_for.split(',')[0].strip()

                # X-Real-IP (nginx)
                real_ip = headers.get("X-Real-IP")
                if real_ip:
                    return real_ip.strip()

                # Remote-Addr
                remote_addr = headers.get("Remote-Addr")
                if remote_addr:
                    return remote_addr.strip()
        except Exception:
            pass

        return None
    except Exception:
        return None


def validate_ip_access():
    """Valide que l'IP du visiteur est autorisée (si PERSONAL_IP est configuré)"""
    # Récupérer la liste des IPs autorisées depuis .env
    allowed_ips_str = os.getenv("PERSONAL_IP", "")

    # Si PERSONAL_IP n'est pas configuré, on désactive la validation
    if not allowed_ips_str or allowed_ips_str == "":
        st.info("ℹ️ Validation IP désactivée (PERSONAL_IP non configuré)")
        return True

    # Parser les IPs autorisées (séparées par virgules)
    allowed_ips = [ip.strip() for ip in allowed_ips_str.split(',') if ip.strip()]

    # Récupérer l'IP du client
    client_ip = get_client_ip()

    if client_ip is None:
        # Si on ne peut pas déterminer l'IP, on affiche un avertissement mais on laisse passer
        st.warning("⚠️ Impossible de déterminer votre adresse IP")
        st.caption("Validation IP ignorée pour cette session")
        return True

    # Vérifier si l'IP est autorisée
    if client_ip not in allowed_ips:
        st.error(f"🚫 ACCÈS REFUSÉ")
        st.warning(f"Votre IP ({client_ip}) n'est pas autorisée à accéder à ce dashboard.")
        st.info("IPs autorisées: " + ", ".join(allowed_ips))
        st.caption("Contactez l'administrateur système pour obtenir l'accès.")
        st.stop()
        return False

    # Accès autorisé
    st.success(f"✅ Accès autorisé depuis {client_ip}")
    return True


def get_db_connection():
    """Établit la connexion à la base de données PostgreSQL"""
    try:
        db_dsn = os.getenv("DB_TICKETS_DSN")

        if not db_dsn:
            st.error("❌ DB_TICKETS_DSN non configuré dans .env")
            st.code("""
# Ajoutez ceci dans votre fichier .env :
DB_TICKETS_DSN=postgresql://voicebot:votre_mot_de_passe@postgres-tickets:5432/db_tickets
            """)
            return None

        return psycopg2.connect(db_dsn)
    except psycopg2.OperationalError as e:
        st.error(f"❌ Erreur de connexion à la base de données")
        st.code(f"Détails: {str(e)}")
        st.info("Vérifiez que PostgreSQL est démarré et que DB_TICKETS_DSN est correct")
        return None
    except Exception as e:
        st.error(f"❌ Erreur inattendue: {e}")
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

    # Vérifier que le répertoire existe
    if not LOGS_DIR.exists():
        return None

    # Le format de fichier dans server.py est : call_{uuid}_{timestamp}.raw
    # On cherche tout fichier contenant l'UUID
    search_pattern = LOGS_DIR / f"call_{call_uuid}_*.raw"
    files = list(glob.glob(str(search_pattern)))

    if files:
        # S'il y en a plusieurs (rare), on prend le plus récent
        return sorted(files)[-1]
    return None


# ============================================
# INTERFACE PRINCIPALE
# ============================================

st.title("🎛️ Supervision SAV Wipple")

# Vérifier l'accès IP (optionnel)
validate_ip_access()

# Connexion à la base de données
conn = get_db_connection()

if not conn:
    st.error("🚫 Impossible de se connecter à la base de données")
    st.info("Le dashboard ne peut pas fonctionner sans connexion DB")

    # Instructions de configuration
    with st.expander("📋 Instructions de Configuration"):
        st.markdown("""
### Configuration Requise

**1. Fichier .env**

Assurez-vous que votre fichier `.env` contient :

```bash
# Base de données tickets
DB_TICKETS_DSN=postgresql://voicebot:votre_mot_de_passe@postgres-tickets:5432/db_tickets

# IP autorisée (optionnel, laissez vide pour désactiver)
PERSONAL_IP=votre.ip.publique
```

**2. Vérifier PostgreSQL**

```bash
# Vérifier que le conteneur tourne
docker ps | grep postgres-tickets

# Tester la connexion
docker exec -it postgres-tickets psql -U voicebot -d db_tickets -c "SELECT COUNT(*) FROM tickets;"
```

**3. Redémarrer le Dashboard**

```bash
docker restart voicebot-dashboard
```
        """)

    st.stop()

# Base de données connectée
try:
    # Vérifier que la table tickets existe
    test_query = pd.read_sql("SELECT COUNT(*) FROM tickets", conn)
    tickets_count = test_query.iloc[0, 0]

    st.success(f"✅ Connecté à la base de données ({tickets_count} tickets)")

    # 1. KPIs (Indicateurs Clés)
    st.subheader("📊 Indicateurs Clés")
    col1, col2, col3, col4 = st.columns(4)

    # Appels du jour
    try:
        count = pd.read_sql(
            "SELECT COUNT(*) FROM tickets WHERE DATE(created_at) = CURRENT_DATE", conn
        ).iloc[0, 0]
        col1.metric("Appels du Jour", count)
    except Exception as e:
        col1.metric("Appels du Jour", "❌")
        st.error(f"Erreur KPI 'Appels du jour': {e}")

    # Durée moyenne
    try:
        avg = pd.read_sql(
            "SELECT COALESCE(AVG(duration_seconds),0) FROM tickets", conn
        ).iloc[0, 0]
        col2.metric("Durée Moyenne", f"{int(avg)}s")
    except Exception as e:
        col2.metric("Durée Moyenne", "❌")
        st.error(f"Erreur KPI 'Durée moyenne': {e}")

    # Clients mécontents
    try:
        angry = pd.read_sql(
            "SELECT COUNT(*) FROM tickets WHERE sentiment = 'negative'", conn
        ).iloc[0, 0]
        col3.metric("Clients Mécontents", angry, delta_color="inverse")
    except Exception as e:
        col3.metric("Clients Mécontents", "❌")
        st.error(f"Erreur KPI 'Clients mécontents': {e}")

    # Pannes Internet
    try:
        internet = pd.read_sql(
            "SELECT COUNT(*) FROM tickets WHERE problem_type = 'internet'", conn
        ).iloc[0, 0]
        col4.metric("Pannes Internet", internet)
    except Exception as e:
        col4.metric("Pannes Internet", "❌")
        st.error(f"Erreur KPI 'Pannes Internet': {e}")

    # 2. Liste des tickets avec lecture audio
    st.subheader("📋 Derniers Tickets & Enregistrements")

    # Récupération des données
    try:
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

        if len(df) == 0:
            st.info("ℹ️ Aucun ticket trouvé. Faites un appel test pour voir les données ici.")
        else:
            # Affichage personnalisé pour chaque ticket
            for index, row in df.iterrows():
                # Couleur de la bordure selon le sentiment
                sentiment_emoji = "😐"
                if row['sentiment'] == 'positive':
                    sentiment_emoji = "🙂"
                elif row['sentiment'] == 'negative':
                    sentiment_emoji = "😡"

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
                        st.caption(f"Durée: {row['duration_seconds']}s")

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
                                st.caption("🎧 Enregistrement (WAV)")

                            except Exception as e:
                                st.error(f"❌ Erreur lecture: {e}")
                        else:
                            st.warning("⚠️ Audio non trouvé")
                            st.caption(f"Cherché dans: {LOGS_DIR}")

    except Exception as e:
        st.error(f"❌ Erreur lors de la récupération des tickets: {e}")
        st.code(str(e))

except Exception as e:
    st.error(f"❌ Erreur globale: {e}")
    st.code(str(e))

    with st.expander("🔍 Détails de l'erreur"):
        import traceback
        st.code(traceback.format_exc())

finally:
    if conn:
        conn.close()

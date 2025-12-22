import os

import psycopg2
import pandas as pd
import streamlit as st
from dotenv import load_dotenv


load_dotenv()
st.set_page_config(page_title="Wipple SAV Cockpit", layout="wide")


def get_db_connection():
    return psycopg2.connect(os.getenv("DB_TICKETS_DSN"))


st.title("🎛️ Supervision SAV Wipple")

try:
    conn = get_db_connection()

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        count = pd.read_sql(
            "SELECT COUNT(*) FROM tickets WHERE DATE(created_at) = CURRENT_DATE", conn
        ).iloc[0, 0]
        st.metric("Appels du Jour", count)
    with col2:
        avg = pd.read_sql(
            "SELECT COALESCE(AVG(duration_seconds),0) FROM tickets", conn
        ).iloc[0, 0]
        st.metric("Durée Moyenne", f"{int(avg)}s")
    with col3:
        angry = pd.read_sql(
            "SELECT COUNT(*) FROM tickets WHERE sentiment = 'negative'", conn
        ).iloc[0, 0]
        st.metric("Clients Mécontents", angry, delta_color="inverse")
    with col4:
        internet = pd.read_sql(
            "SELECT COUNT(*) FROM tickets WHERE problem_type = 'internet'", conn
        ).iloc[0, 0]
        st.metric("Pannes Internet", internet)

    # Tableau
    st.subheader("Derniers Tickets")
    df = pd.read_sql(
        """
        SELECT
            created_at,
            phone_number,
            problem_type,
            status,
            sentiment,
            summary,
            duration_seconds
        FROM tickets
        ORDER BY created_at DESC
        LIMIT 50
        """,
        conn,
    )
    st.dataframe(df, use_container_width=True)

    conn.close()
except Exception as e:
    st.error(f"Erreur connexion DB: {e}")



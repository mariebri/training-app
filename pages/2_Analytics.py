import streamlit as st

# Check if user is logged in
if not st.session_state.get("user_id"):
    st.error("🔒 Please log in first")
    st.stop()

import pandas as pd
import plotly.express as px

from services.calendar_service import get_all_sessions
from services.performance_model import compute_ctl_atl

st.title("Performance Dashboard")

if st.session_state.user_id:
    with st.sidebar:
        st.write(f"👤 Logged in as: **{st.session_state.username}**")
        if st.button("🚪 Logout"):
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()

rows = get_all_sessions(st.session_state.user_id)

sessions = [
    {"session_date": r[5], "duration_minutes": r[6], "intensity": r[3]} for r in rows
]

history = compute_ctl_atl(sessions)

df = pd.DataFrame(history)

# ==========================================
# FITNESS / FATIGUE CHART
# ==========================================

fig = px.line(df, x="date", y=["ctl", "atl", "tsb"])

st.plotly_chart(fig, width="content")

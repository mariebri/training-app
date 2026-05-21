import streamlit as st
import pandas as pd
import plotly.express as px

from services.calendar_service import get_all_sessions
from services.performance_model import compute_ctl_atl

st.title("Performance Dashboard")

rows = get_all_sessions()

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

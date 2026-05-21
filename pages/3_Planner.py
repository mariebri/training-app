import streamlit as st

from services.calendar_service import get_all_sessions, sessions_to_dicts
from services.performance_model import compute_ctl_atl

from services.coach.coach_engine import generate_week_plan
from services.coach.workout_generator import build_workout

st.title("AI Training Coach")

rows = get_all_sessions()
sessions = sessions_to_dicts(rows)

history = compute_ctl_atl(sessions)

latest = history[-1] if history else {"ctl": 50, "atl": 50, "tsb": 0}

weekly_load_7d = sum([h["load"] for h in history[-7:]])
weekly_load_28d = sum([h["load"] for h in history[-28:]])

base_load = weekly_load_28d / 4 if weekly_load_28d > 0 else 200

plan_output = generate_week_plan(
    ctl=latest["ctl"],
    atl=latest["atl"],
    tsb=latest["tsb"],
    weekly_load_7d=weekly_load_7d,
    weekly_load_28d=weekly_load_28d,
    current_week_number=42,
    base_load=base_load,
)

st.metric("TSB", round(latest["tsb"], 1))
st.metric("Spike Ratio", round(plan_output["spike_ratio"], 2))
st.metric("Next Week Load", round(plan_output["next_week_load"], 0))

st.subheader("Coach State")
st.write(plan_output["state"])

if plan_output.get("message"):
    st.warning(plan_output["message"])

st.subheader("Weekly Plan")

for w in plan_output["plan"]:
    st.write("•", w)

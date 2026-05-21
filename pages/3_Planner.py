import streamlit as st

# Check if user is logged in
if not st.session_state.get("user_id"):
    st.error("🔒 Please log in first")
    st.stop()


from services.calendar_service import get_all_sessions, sessions_to_dicts
from services.performance_model import compute_ctl_atl

from services.coach.coach_engine import generate_week_plan
from services.coach.workout_generator import build_workout

st.title("AI Training Coach")

if st.session_state.user_id:
    with st.sidebar:
        st.write(f"👤 Logged in as: **{st.session_state.username}**")
        if st.button("🚪 Logout"):
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()

rows = get_all_sessions(st.session_state.user_id)
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

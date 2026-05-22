import streamlit as st
import pandas as pd

# Check if user is logged in
if not st.session_state.get("user_id"):
    st.error("🔒 Logg inn først")
    st.stop()


from services.calendar_service import (
    get_all_sessions,
    sessions_to_dicts,
    get_sidebar_first_name,
)
from services.planner_service import build_planner_output

st.title("Treningsplanlegger")

if st.session_state.user_id:
    with st.sidebar:
        first_name = get_sidebar_first_name(
            st.session_state.user_id, st.session_state.username
        )
        st.write(f"👋 Hei, **{first_name}**!")
        if st.button("🚪 Logg ut"):
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()

rows = get_all_sessions(st.session_state.user_id)
sessions = sessions_to_dicts(rows)

st.subheader("Mål for planlegging")

goal_col1, goal_col2, goal_col3 = st.columns(3)
with goal_col1:
    goal_focus = st.selectbox(
        "Hovedmål",
        ["Generell form", "5 km", "10 km", "Halvmaraton", "Maraton"],
    )
with goal_col2:
    goal_weeks = st.number_input("Uker til mål", min_value=1, max_value=52, value=12)
with goal_col3:
    training_days = st.slider("Økter per uke", min_value=3, max_value=7, value=5)

load_col1, load_col2 = st.columns(2)
with load_col1:
    weekly_minutes_target = st.slider(
        "Tilgjengelige minutter per uke",
        min_value=120,
        max_value=900,
        value=300,
        step=15,
    )
with load_col2:
    goal_aggressiveness = st.selectbox(
        "Progresjonsnivå",
        ["Konservativ", "Moderat", "Ambisiøs"],
        index=1,
    )

planner_output = build_planner_output(
    sessions=sessions,
    goal_focus=goal_focus,
    training_days=training_days,
    weekly_minutes_target=weekly_minutes_target,
    goal_aggressiveness=goal_aggressiveness,
)

latest = planner_output["latest"]
weekly_load_7d = planner_output["weekly_load_7d"]
weekly_load_28d_avg = planner_output["weekly_load_28d_avg"]
spike_ratio = planner_output["spike_ratio"]
risk_flag = planner_output["risk_flag"]
next_7d_target = planner_output["next_7d_target"]
planned_load = planner_output["planned_load"]
structured_plan = planner_output["structured_plan"]

st.subheader("Status fra tidligere belastning")
status_col1, status_col2, status_col3, status_col4 = st.columns(4)
status_col1.metric("TSB", round(latest["tsb"], 1))
status_col2.metric("Belastning siste 7 dager", round(weekly_load_7d, 1))
status_col3.metric("4-ukers snitt per uke", round(weekly_load_28d_avg, 1))
status_col4.metric("Belastningsratio", round(spike_ratio, 2))

if risk_flag:
    st.warning(
        "Forhøyet skaderisiko oppdaget. Planen er automatisk gjort mer konservativ."
    )

st.subheader("Plan neste uke")

plan_col1, plan_col2, plan_col3 = st.columns(3)
plan_col1.metric("Anbefalt belastningstak (7d)", f"{next_7d_target:.0f}")
plan_col2.metric("Planlagt belastning (estimat)", f"{planned_load:.0f}")
plan_col3.metric("Uker til mål", int(goal_weeks))

st.markdown("### Estimert ukeplan")

tab1, tab2 = st.tabs(["Tabell", "Kalenderoppsett"])

with tab1:
    plan_df = pd.DataFrame(structured_plan)
    st.dataframe(plan_df, width="content", hide_index=True)

with tab2:
    week_cols = st.columns(7)
    for idx, day_plan in enumerate(structured_plan):
        with week_cols[idx]:
            st.markdown(f"**{day_plan['Dag']}**")
            st.write(day_plan["Okt"])
            st.caption(f"{day_plan['Varighet (min)']} min | {day_plan['Intensitet']}")
            st.caption(day_plan["Beskrivelse"])

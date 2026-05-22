import streamlit as st

# Check if user is logged in
if not st.session_state.get("user_id"):
    st.error("🔒 Logg inn først")
    st.stop()

import plotly.express as px
import plotly.graph_objects as go

from services.calendar_service import get_all_sessions, get_profile, get_sidebar_first_name
from services.analytics_service import badge_for_status, build_analytics_data

st.title("Prestasjonsoversikt")


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
profile = get_profile(st.session_state.user_id)

analytics_data = build_analytics_data(rows)

if not analytics_data["has_sessions"]:
    st.info(
        "Ingen treningsøkter ennå. Legg til noen økter i kalenderen for å låse opp analysen."
    )
    st.stop()

if not analytics_data["has_history"]:
    st.info("Trenger noen flere økter for å beregne trendene i CTL/ATL/TSB.")
    st.stop()

session_df = analytics_data["session_df"]
df = analytics_data["df"]
weekly_chart_df = analytics_data["weekly_chart_df"]
intensity_mix_df = analytics_data["intensity_mix_df"]
recommendations = analytics_data["recommendations"]
key_values_df = analytics_data["key_values_df"]

window_28d_start = analytics_data["window_28d_start"]
today = analytics_data["today"]

weekly_load_7d = analytics_data["weekly_load_7d"]
weekly_load_28d = analytics_data["weekly_load_28d"]
weekly_delta_pct = analytics_data["weekly_delta_pct"]
spike_ratio = analytics_data["spike_ratio"]
spike_light = analytics_data["spike_light"]
consistency_pct = analytics_data["consistency_pct"]
consistency_days = analytics_data["consistency_days"]

running_km_7d = analytics_data["running_km_7d"]
running_minutes_7d = analytics_data["running_minutes_7d"]
running_load_7d = analytics_data["running_load_7d"]

next_7d_max_load = analytics_data["next_7d_max_load"]
planned_next_7d_load = analytics_data["planned_next_7d_load"]
remaining_budget = analytics_data["remaining_budget"]

ctl = analytics_data["ctl"]
atl = analytics_data["atl"]
tsb = analytics_data["tsb"]
ctl_change_pct = analytics_data["ctl_change_pct"]
tsb_light = analytics_data["tsb_light"]

risk_flag = analytics_data["risk_flag"]
risk_level = analytics_data["risk_level"]

tabs = st.tabs(
    [
        "Belastningsoversikt",
        "Anbefalte tiltak",
        "Nøkkelverdier (CTL/ATL/TSB)",
        "Grafer",
    ]
)

with tabs[0]:
    st.subheader("Nåværende belastningsbilde")

    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    kpi_col1.metric(
        "Total belastning (siste 7 d)",
        f"{weekly_load_7d:.1f}",
        f"{weekly_delta_pct:+.1f}%",
    )
    kpi_col2.metric("Snittbelastning per uke (siste 28 d)", f"{weekly_load_28d:.1f}")
    kpi_col3.metric(
        "Belastningsratio (ACWR)", f"{spike_ratio:.2f}", badge_for_status(spike_light)
    )
    kpi_col4.metric(
        "Konsistens (14 d)", f"{consistency_pct:.0f}%", f"{consistency_days}/14 dager"
    )

    st.markdown("### Løpsbelastning (siste 7 dager)")
    run_col1, run_col2, run_col3 = st.columns(3)
    run_col1.metric("Løp km", f"{running_km_7d:.1f} km")
    run_col2.metric("Løp minutter", f"{running_minutes_7d:.0f} min")
    run_col3.metric("Løp total belastning", f"{running_load_7d:.1f}")

    st.markdown("### Kapasitet neste 7 dager")
    budget_col1, budget_col2, budget_col3 = st.columns(3)
    budget_col1.metric("Anbefalt maks belastning", f"{next_7d_max_load:.1f}")
    budget_col2.metric("Planlagt belastning", f"{planned_next_7d_load:.1f}")
    budget_col3.metric("Gjenstående belastningsbudsjett", f"{remaining_budget:.1f}")

    if profile:
        height_cm = profile.get("height_cm")
        weight_kg = profile.get("weight_kg")

        profile_col1, profile_col2 = st.columns(2)
        if height_cm and weight_kg and height_cm > 0:
            bmi = weight_kg / ((height_cm / 100) ** 2)
            profile_col1.metric("BMI", f"{bmi:.1f}")

        if weight_kg and weight_kg > 0:
            load_per_kg = weekly_load_7d / weight_kg
            profile_col2.metric("Belastning per kg (7 d)", f"{load_per_kg:.2f}")

with tabs[1]:
    st.subheader("Anbefalte tiltak")

    for level, message in recommendations:
        if level == "red":
            st.error(message)
        elif level == "yellow":
            st.warning(message)
        else:
            st.success(message)

    if risk_level == "Høy" or risk_flag:
        st.error("Samlet skaderisiko: Høy. Hold denne uken konservativ.")
    elif risk_level == "Moderat":
        st.warning(
            "Samlet skaderisiko: Moderat. Følg med på søvn, ømhet og avstand mellom økter."
        )
    else:
        st.success(
            "Samlet skaderisiko: Lav. Nåværende belastningsprofil er stort sett stabil."
        )

with tabs[2]:
    st.subheader("Nøkkelverdier og trafikklys")

    key_col1, key_col2, key_col3 = st.columns(3)
    key_col1.metric("CTL", f"{ctl:.1f}", f"{ctl_change_pct:+.1f}% vs 14 d")
    key_col2.metric("ATL", f"{atl:.1f}", f"{(atl / max(ctl, 1.0)):.2f} ATL/CTL")
    key_col3.metric("TSB", f"{tsb:.1f}", badge_for_status(tsb_light))

    st.dataframe(key_values_df, hide_index=True, width="content")

    with st.expander("Hva disse verdiene betyr"):
        st.markdown("**CTL:** Langsiktig formutvikling (omtrent 6 uker).")
        st.markdown("**ATL:** Kortsiktig slitasje-trend (omtrent 1 uke).")
        st.markdown(
            "**TSB:** Estimat på friskhet ($TSB = CTL - ATL$). Negativ betyr mer slitasje, positiv betyr friskere."
        )
        st.markdown(
            "**Trafikklys:** Grønn = god sone, gul = vær oppmerksom, rød = juster belastning/restitusjon nå."
        )

with tabs[3]:
    st.subheader("Prestasjonstrender")

    fitness_fig = px.line(df, x="date", y=["ctl", "atl", "tsb"])
    fitness_fig.update_layout(
        title="Form (CTL), slitasje (ATL) og friskhet (TSB)",
        xaxis_title="Dato",
        yaxis_title="Skår",
    )
    st.plotly_chart(fitness_fig, width="content")

    weekly_fig = go.Figure()
    weekly_fig.add_trace(
        go.Bar(
            x=weekly_chart_df["week"],
            y=weekly_chart_df["weekly_load"],
            name="Ukentlig belastning",
        )
    )

    weekly_chart_df["rolling_4w"] = weekly_chart_df["weekly_load"].rolling(4).mean()
    weekly_fig.add_trace(
        go.Scatter(
            x=weekly_chart_df["week"],
            y=weekly_chart_df["rolling_4w"],
            mode="lines+markers",
            name="4-ukers glidende snitt",
        )
    )

    weekly_fig.update_layout(
        title="Ukentlig treningsbelastning",
        xaxis_title="Uke",
        yaxis_title="Belastning",
        bargap=0.2,
    )
    st.plotly_chart(weekly_fig, width="content")

    if not intensity_mix_df.empty:
        intensity_fig = px.pie(
            intensity_mix_df,
            names="intensity",
            values="duration_minutes",
            title="Intensitetsfordeling (siste 28 dager, i minutter)",
        )
        st.plotly_chart(intensity_fig, width="content")

import streamlit as st

# Check if user is logged in
if not st.session_state.get("user_id"):
    st.error("🔒 Logg inn først")
    st.stop()

from streamlit_calendar import calendar

from services.calendar_service import (
    add_training_session,
    get_all_sessions,
    convert_sessions_to_calendar_events,
    update_session,
    delete_session,
    get_templates,
    get_sidebar_first_name,
)
from services.calendar_page_service import (
    build_risk_overlay_events,
    close_dialog,
    initialize_calendar_state,
    normalize_clicked_date,
    open_add_dialog,
    open_choose_dialog,
    open_view_dialog,
)

from utils.ui_styles import inject_calendar_styles
from utils.constants import TIME_SLOTS, ACTIVITIES

st.title("Treningskalender")

inject_calendar_styles()

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

# ==========================================
# INITIALIZE SESSION STATE
# ==========================================
initialize_calendar_state(st.session_state)


# ==========================================
# CALENDAR
# ==========================================

rows = get_all_sessions(st.session_state.user_id)
events = convert_sessions_to_calendar_events(rows)
templates = get_templates(st.session_state.user_id, include_in_calendar=True)
events.extend(build_risk_overlay_events(rows))

calendar_options = {
    "firstDay": 1,
    "timeZone": "local",
    "weekNumbers": True,
    "weekText": "",
    "locale": "nb",
    "initialView": "dayGridMonth",
    "height": 700,
    "selectable": True,
    "editable": True,
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "dayGridMonth,timeGridWeek",
    },
}

calendar_state = calendar(
    events=events, options=calendar_options, key="training_calendar"
)

st.caption(
    "Trafikklys neste 7 dager: Grønn = lav risiko, gul = moderat, rød = høy belastning"
)

# ==========================================
# HANDLE CALENDAR INTERACTIONS
# ==========================================

if calendar_state.get("eventClick"):
    event = calendar_state["eventClick"]["event"]
    open_view_dialog(st.session_state, event)

elif calendar_state.get("dateClick"):
    clicked_date_raw = calendar_state["dateClick"].get(
        "dateStr", calendar_state["dateClick"]["date"]
    )
    clicked_date_str = str(clicked_date_raw)[:10]
    action_key = f"date:{clicked_date_str}"

    if st.session_state["last_calendar_action"] != action_key:
        st.session_state["last_calendar_action"] = action_key
        clicked_date = normalize_clicked_date(clicked_date_str)
        st.session_state["prefill_session"] = None
        open_choose_dialog(st.session_state, clicked_date)

elif calendar_state.get("eventChange"):
    drop_event = calendar_state["eventChange"]["event"]
    event_id = drop_event["id"]
    new_date = drop_event["start"]

    # Get the current session data
    props = drop_event["extendedProps"]

    # Update the session with the new date
    update_session(
        session_id=event_id,
        title=props["raw_title"],
        activity=props["activity"],
        intensity=props["intensity"],
        time_slot=props["time_slot"],
        session_date=new_date,
        duration_minutes=props["duration_minutes"],
        distance_km=props["distance_km"],
        notes=props["notes"],
    )
    st.rerun()


if st.button("➕ Legg til økt"):
    st.session_state["prefill_session"] = None
    open_add_dialog(st.session_state)
    st.rerun()


# ==========================================
# CHOOSE SESSION TYPE DIALOG
# ==========================================

if (
    st.session_state.get("show_dialog", False) == "choose"
    and st.session_state["dialog_mode"] == "choose"
):

    @st.dialog("Velg type økt")
    def choose_session_dialog():
        st.write("Dato:", st.session_state["selected_date"].strftime("%d/%m/%Y"))

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Ny økt", key="choose_new_session"):
                st.session_state["prefill_session"] = None
                st.session_state["show_dialog"] = "add"
                st.session_state["dialog_mode"] = "add"
                st.rerun()
        with col2:
            if st.button("Avbryt", key="choose_cancel"):
                close_dialog(st.session_state)
                st.rerun()

        st.divider()
        st.markdown("**Predefinerte økter**")

        if not templates:
            st.info("Ingen predefinerte økter funnet. Legg til på Bruker-siden.")
        else:
            for template in templates:
                label = (
                    f"{template['name']} - {template['activity']} - "
                    f"{template['intensity']} - {template['duration_minutes']} min"
                )
                if st.button(label, key=f"choose_template_{template['id']}"):
                    st.session_state["prefill_session"] = template
                    st.session_state["show_dialog"] = "add"
                    st.session_state["dialog_mode"] = "add"
                    st.rerun()

    choose_session_dialog()
    st.session_state["show_dialog"] = None


# ==========================================
# ADD SESSION DIALOG
# ==========================================

if (
    st.session_state.get("show_dialog", False) == "add"
    and st.session_state["dialog_mode"] == "add"
):

    @st.dialog("Legg til treningsøkt")
    def add_session_dialog():
        prefill = st.session_state.get("prefill_session") or {}

        default_activity = prefill.get("activity") or list(ACTIVITIES.keys())[0]
        if default_activity not in ACTIVITIES:
            default_activity = list(ACTIVITIES.keys())[0]

        default_intensity = prefill.get("intensity") or "Lett"
        intensity_options = ["Lett", "Moderat", "Hardt"]
        if default_intensity not in intensity_options:
            default_intensity = "Lett"

        default_time_slot = prefill.get("time_slot") or TIME_SLOTS[0]
        if default_time_slot not in TIME_SLOTS:
            default_time_slot = TIME_SLOTS[0]

        with st.form("training_form"):
            title = st.text_input("Tittel", value=prefill.get("name") or "")
            activity = st.selectbox(
                "Aktivitet",
                list(ACTIVITIES.keys()),
                index=list(ACTIVITIES.keys()).index(default_activity),
            )
            intensity = st.selectbox(
                "Intensitet",
                intensity_options,
                index=intensity_options.index(default_intensity),
            )
            time_slot = st.selectbox(
                "Tidspunkt",
                TIME_SLOTS,
                index=TIME_SLOTS.index(default_time_slot),
            )

            session_date = st.date_input(
                "Dato",
                value=st.session_state["selected_date"],
                format="DD/MM/YYYY",
            )

            duration_minutes = st.number_input(
                "Varighet (minutter)",
                min_value=0,
                step=5,
                value=int(prefill.get("duration_minutes") or 0),
            )
            distance_km = st.number_input(
                "Distanse (km)",
                min_value=0.0,
                step=1.0,
                value=float(prefill.get("distance_km") or 0.0),
            )
            notes = st.text_area("Notater", value=prefill.get("notes") or "")

            col1, col2 = st.columns(2)

            with col1:
                submitted = st.form_submit_button("Lagre økt")
            with col2:
                cancel = st.form_submit_button("Avbryt")

            if submitted:
                add_training_session(
                    user_id=st.session_state.user_id,
                    title=title,
                    activity=activity,
                    intensity=intensity,
                    time_slot=time_slot,
                    session_date=str(session_date),
                    duration_minutes=duration_minutes,
                    distance_km=distance_km,
                    notes=notes,
                )
                close_dialog(st.session_state)
                st.rerun()

            if cancel:
                close_dialog(st.session_state)
                st.rerun()

    add_session_dialog()
    st.session_state["show_dialog"] = None


# ==========================================
# VIEW/EDIT SESSION DIALOG
# ==========================================

if (
    st.session_state.get("show_dialog", False) == "view"
    and st.session_state["dialog_mode"] == "view"
    and st.session_state["selected_event"]
):
    event = st.session_state["selected_event"]
    props = event["extendedProps"]
    session_id = event["id"]

    @st.dialog("Treningsøkt")
    def show_event_dialog():
        edit_mode = st.session_state.get("edit_mode", False)

        if not edit_mode:
            # ===== VISNINGS-MODUS =====
            st.subheader(event["title"])

            col1, col2 = st.columns(2)
            with col1:
                st.write("**Aktivitet:**", props["activity"])
                st.write("**Intensitet:**", props["intensity"])
                st.write("**Tidspunkt:**", props["time_slot"])
            with col2:
                st.write(f"**Varighet:** {props['duration_minutes']} min")
                st.write(f"**Distanse:** {props['distance_km']} km")

            if props.get("notes"):
                st.write("**Notater:**")
                st.info(props["notes"])

            st.divider()

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✏️ Endre økt", key="btn_edit"):
                    st.session_state["edit_mode"] = True
                    st.session_state["in_editing"] = True
                    st.session_state["show_dialog"] = "view"
                    st.session_state["selected_event"] = event
                    st.rerun()
            with col2:
                if st.button("🗑️ Fjern økt", key="btn_delete"):
                    with st.spinner("Fjerner økten..."):
                        delete_session(session_id)
                    close_dialog(st.session_state)
                    st.rerun()

        else:
            # ===== REDIGERINGS-MODUS (inline) =====
            st.subheader("Endre treningsøkt")

            with st.form("edit_session_form"):
                title = st.text_input("Tittel", value=props.get("raw_title", ""))

                activity = st.selectbox(
                    "Aktivitet",
                    list(ACTIVITIES.keys()),
                    index=list(ACTIVITIES.keys()).index(props["activity"]),
                )

                intensity_options = ["Lett", "Moderat", "Hardt"]
                intensity = st.selectbox(
                    "Intensitet",
                    intensity_options,
                    index=intensity_options.index(props["intensity"]),
                )

                time_slot = st.selectbox(
                    "Tidspunkt",
                    TIME_SLOTS,
                    index=TIME_SLOTS.index(props["time_slot"]),
                )

                duration_minutes = st.number_input(
                    "Varighet (minutter)",
                    min_value=0,
                    value=props.get("duration_minutes") or 0,
                )

                distance_km = st.number_input(
                    "Distanse (km)",
                    min_value=0.0,
                    value=float(props.get("distance_km") or 0),
                )

                notes = st.text_area("Notater", value=props.get("notes") or "")

                col1, col2 = st.columns(2)
                with col1:
                    save_clicked = st.form_submit_button("💾 Lagre")
                with col2:
                    cancel_clicked = st.form_submit_button("❌ Avbryt")

                if save_clicked:
                    update_session(
                        session_id=session_id,
                        title=title,
                        activity=activity,
                        intensity=intensity,
                        time_slot=time_slot,
                        session_date=props["session_date"],
                        duration_minutes=duration_minutes,
                        distance_km=distance_km,
                        notes=notes,
                    )
                    # close_dialog()
                    st.session_state["edit_mode"] = False
                    st.session_state["show_dialog"] = "view"
                    st.rerun()

                if cancel_clicked:
                    st.session_state["edit_mode"] = False
                    st.session_state["show_dialog"] = "view"
                    st.rerun()

    show_event_dialog()
    st.session_state["show_dialog"] = None

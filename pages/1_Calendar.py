import streamlit as st
from streamlit_calendar import calendar
from datetime import date

from services.calendar_service import (
    add_training_session,
    get_all_sessions,
    convert_sessions_to_calendar_events,
    update_session,
    delete_session,
)

from utils.ui_styles import inject_calendar_styles
from utils.constants import TIME_SLOTS, ACTIVITIES

st.title("Treningskalender")

inject_calendar_styles()

# ==========================================
# INITIALIZE SESSION STATE
# ==========================================

initialize_ss_dict = {
    "dialog_mode": None,  # None, "add", "view"
    "selected_date": date.today(),
    "selected_event": None,
    "edit_mode": False,
    "last_calendar_action": None,
}

for key, default_value in initialize_ss_dict.items():
    if key not in st.session_state:
        st.session_state[key] = default_value


def close_dialog():
    """Lukk dialog og reset state."""
    st.session_state.pop("show_dialog", None)
    st.session_state["dialog_mode"] = None
    st.session_state["selected_event"] = None
    st.session_state["edit_mode"] = False
    st.session_state["selected_date"] = date.today()


def open_add_dialog(selected_date=None):
    """Åpne 'legg til'-dialog, lukk andre dialoger først."""
    st.session_state["show_dialog"] = "add"
    st.session_state["dialog_mode"] = "add"
    st.session_state["selected_event"] = None
    st.session_state["edit_mode"] = False
    st.session_state["selected_date"] = selected_date or date.today()


def open_view_dialog(event):
    """Åpne 'vis økt'-dialog, lukk andre dialoger først."""
    st.session_state["show_dialog"] = "view"
    st.session_state["dialog_mode"] = "view"
    st.session_state["selected_event"] = event
    st.session_state["edit_mode"] = st.session_state.pop("in_editing", False)


# ==========================================
# CALENDAR
# ==========================================

rows = get_all_sessions()
events = convert_sessions_to_calendar_events(rows)

calendar_options = {
    "firstDay": 1,
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

# ==========================================
# HANDLE CALENDAR INTERACTIONS
# ==========================================

calendar_action = None

if calendar_state.get("eventClick"):
    event = calendar_state["eventClick"]["event"]
    open_view_dialog(event)

elif calendar_state.get("dateClick"):
    clicked_date_str = calendar_state["dateClick"]["date"]
    action_key = f"date:{clicked_date_str}"

    if st.session_state["last_calendar_action"] != action_key:
        st.session_state["last_calendar_action"] = action_key

        clicked_date = date.fromisoformat(clicked_date_str[:10])
        open_add_dialog(clicked_date)

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
        session_date=new_date,  # This is the new dragged date
        duration_minutes=props["duration_minutes"],
        distance_km=props["distance_km"],
        notes=props["notes"],
    )
    st.rerun()


# ==========================================
# ADD NEW SESSION BUTTON
# ==========================================

if st.button("➕ Legg til"):
    open_add_dialog()
    st.rerun()


# ==========================================
# ADD SESSION DIALOG
# ==========================================

if (
    st.session_state.get("show_dialog", False) == "add"
    and st.session_state["dialog_mode"] == "add"
):

    @st.dialog("Legg til treningsøkt")
    def add_session_dialog():

        with st.form("training_form"):
            title = st.text_input("Tittel")
            activity = st.selectbox("Aktivitet", list(ACTIVITIES.keys()))
            intensity = st.selectbox("Intensitet", ["Lett", "Moderat", "Hardt"])
            time_slot = st.selectbox("Tidspunkt", TIME_SLOTS)

            session_date = st.date_input(
                "Dato",
                value=st.session_state["selected_date"],
                format="DD/MM/YYYY",
            )

            duration_minutes = st.number_input(
                "Varighet (minutter)", min_value=0, step=5
            )
            distance_km = st.number_input("Distanse (km)", min_value=0.0, step=1.0)
            notes = st.text_area("Notater")

            col1, col2 = st.columns(2)

            with col1:
                submitted = st.form_submit_button("Lagre økt")
            with col2:
                cancel = st.form_submit_button("Avbryt")

            if submitted:
                add_training_session(
                    title=title,
                    activity=activity,
                    intensity=intensity,
                    time_slot=time_slot,
                    session_date=str(session_date),
                    duration_minutes=duration_minutes,
                    distance_km=distance_km,
                    notes=notes,
                )
                close_dialog()
                st.rerun()

            if cancel:
                close_dialog()
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
                    close_dialog()
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

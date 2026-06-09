import streamlit as st
from datetime import date, datetime
import re
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
from services.database import (
    initialize_database,
    get_user_role,
    login_user,
    register_user,
    generate_temporary_password,
    reset_password_for_email,
    touch_user_activity,
    user_exists_for_email,
)
from services.email_service import send_password_reset_email, EmailConfigError
from utils.ui_styles import inject_calendar_styles
from utils.navigation import render_app_sidebar
from utils.constants import (
    TIME_SLOTS,
    ACTIVITIES,
    SESSION_TYPES,
    SESSION_GOALS,
    SESSION_PRIORITIES,
    BODY_FOCUS_AREAS,
    ENERGY_LEVELS,
    PAIN_LEVELS,
    INTENSITIES,
)

st.set_page_config(page_title="Treningskalender", layout="wide")
initialize_database()

if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "active_auth_dialog" not in st.session_state:
    st.session_state.active_auth_dialog = None
if "last_login_email" not in st.session_state:
    st.session_state.last_login_email = ""
if "last_login_password" not in st.session_state:
    st.session_state.last_login_password = ""


@st.dialog("Glemt passord")
def forgot_password_dialog():
    email = st.text_input("E-post", key="forgot_password_email")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Avbryt", key="forgot_password_cancel"):
            st.session_state.active_auth_dialog = None
            st.rerun()
    with col2:
        if st.button("Send nytt passord", key="forgot_password_submit"):
            try:
                if not user_exists_for_email(email):
                    raise ValueError("Fant ingen bruker med denne e-postadressen")
                new_password = generate_temporary_password()
                send_password_reset_email(email, new_password)
                reset_password_for_email(email, new_password)
                st.success("Nytt passord er opprettet og sendt til e-postadressen.")
                st.session_state.active_auth_dialog = None
                st.rerun()
            except EmailConfigError as e:
                st.error(str(e))
            except RuntimeError as e:
                st.error(str(e))
            except ValueError as e:
                st.error(str(e))


@st.dialog("Registrer ny bruker")
def register_dialog():
    reg_email = st.text_input("E-post", key="reg_email")
    reg_password = st.text_input("Passord", type="password", key="reg_password")
    reg_password_confirm = st.text_input(
        "Bekreft passord", type="password", key="reg_password_confirm"
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Avbryt", key="register_cancel"):
            st.session_state.active_auth_dialog = None
            st.rerun()
    with col2:
        if st.button("Registrer", key="register_submit"):
            if not reg_email or not reg_password:
                st.error("E-post og passord er påkrevd")
            elif "@" not in reg_email or "." not in reg_email.split("@")[-1]:
                st.error("Skriv inn en gyldig e-postadresse")
            elif reg_password != reg_password_confirm:
                st.error("Passordene er ikke like")
            elif len(reg_password) < 6:
                st.error("Passordet må være minst 6 tegn")
            else:
                try:
                    user_id = register_user(
                        email=reg_email,
                        password=reg_password,
                    )
                    st.session_state.user_id = user_id
                    st.session_state.username = reg_email
                    st.session_state.user_role = get_user_role(user_id)
                    st.success("Registrering vellykket!")
                    st.session_state.active_auth_dialog = None
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))


if not st.session_state.get("user_id"):
    st.title("🏋️ Treningsplanlegger")

    st.subheader("🔓 Logg inn")
    login_email = st.text_input("E-post", key="login_email")
    login_password = st.text_input("Passord", type="password", key="login_password")

    login_fields_changed = (
        login_email != st.session_state.last_login_email
        or login_password != st.session_state.last_login_password
    )
    if login_fields_changed and st.session_state.active_auth_dialog:
        st.session_state.active_auth_dialog = None

    st.session_state.last_login_email = login_email
    st.session_state.last_login_password = login_password

    if st.button("Logg inn"):
        try:
            user_id = login_user(login_email, login_password)
            st.session_state.user_id = user_id
            st.session_state.username = login_email
            st.session_state.user_role = get_user_role(user_id)
            st.success(f"Velkommen tilbake, {login_email}!")
            st.rerun()
        except ValueError as e:
            st.error(str(e))

    action_col1, action_col2 = st.columns(2)
    with action_col1:
        if st.button("Glemt passord"):
            st.session_state.active_auth_dialog = "forgot"
    with action_col2:
        if st.button("Registrer ny bruker"):
            st.session_state.active_auth_dialog = "register"

    if st.session_state.active_auth_dialog == "forgot":
        forgot_password_dialog()
    elif st.session_state.active_auth_dialog == "register":
        register_dialog()

    st.divider()
    st.info(
        "📝 **Demokonto**: Bruk e-post `demo` og passord `demo123` for å teste appen"
    )
    st.stop()

title_col, settings_col = st.columns([0.96, 0.04], gap="small")
with title_col:
    st.title("Treningskalender")
with settings_col:
    if st.button("⚙️", key="btn_calendar_settings"):
        st.session_state["show_calendar_settings_dialog"] = True

inject_calendar_styles()

if st.session_state.user_id:
    touch_user_activity(st.session_state.user_id)
    if not st.session_state.get("user_role"):
        st.session_state.user_role = get_user_role(st.session_state.user_id)

if st.session_state.user_id:
    first_name = get_sidebar_first_name(
        st.session_state.user_id, st.session_state.username
    )
    render_app_sidebar(first_name, st.session_state.get("user_role"))

# ==========================================
# INITIALIZE SESSION STATE
# ==========================================
initialize_calendar_state(st.session_state)
if "calendar_show_traffic_lights" not in st.session_state:
    st.session_state["calendar_show_traffic_lights"] = True
if "calendar_show_week_numbers" not in st.session_state:
    st.session_state["calendar_show_week_numbers"] = True
if "calendar_mark_completed_sessions" not in st.session_state:
    st.session_state["calendar_mark_completed_sessions"] = True
if "show_calendar_settings_dialog" not in st.session_state:
    st.session_state["show_calendar_settings_dialog"] = False

if st.session_state.get("show_calendar_settings_dialog"):

    @st.dialog("Kalenderinnstillinger")
    def calendar_settings_dialog():
        with st.form("calendar_settings_form"):
            show_traffic_lights = st.toggle(
                "Vis trafikklys for belastning",
                value=st.session_state.get("calendar_show_traffic_lights", True),
            )
            show_week_numbers = st.toggle(
                "Vis ukenummer",
                value=st.session_state.get("calendar_show_week_numbers", True),
            )
            mark_completed_sessions = st.toggle(
                "Markér fullførte økter",
                value=st.session_state.get("calendar_mark_completed_sessions", True),
            )

            col_save, col_cancel = st.columns(2)
            with col_save:
                save_settings = st.form_submit_button(
                    "💾 Lagre", use_container_width=True
                )
            with col_cancel:
                cancel_settings = st.form_submit_button(
                    "❌ Avbryt", use_container_width=True
                )

            if save_settings:
                st.session_state["calendar_show_traffic_lights"] = show_traffic_lights
                st.session_state["calendar_show_week_numbers"] = show_week_numbers
                st.session_state["calendar_mark_completed_sessions"] = (
                    mark_completed_sessions
                )
                st.session_state["show_calendar_settings_dialog"] = False
                st.rerun()

            if cancel_settings:
                st.session_state["show_calendar_settings_dialog"] = False
                st.rerun()

    calendar_settings_dialog()


# ==========================================
# CALENDAR
# ==========================================

rows = get_all_sessions(st.session_state.user_id)
events = convert_sessions_to_calendar_events(
    rows, mark_completed=st.session_state.get("calendar_mark_completed_sessions", True)
)
templates = get_templates(st.session_state.user_id, include_in_calendar=True)
if st.session_state.get("calendar_show_traffic_lights", True):
    events.extend(build_risk_overlay_events(rows))

calendar_options = {
    "firstDay": 1,
    "timeZone": "local",
    "weekNumbers": st.session_state.get("calendar_show_week_numbers", True),
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

if st.session_state.get("calendar_show_traffic_lights", True):
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
        session_type=props.get("session_type"),
        session_goal=props.get("session_goal"),
        planned_structure=props.get("planned_structure"),
        priority=props.get("priority"),
        body_focus=props.get("body_focus"),
        is_completed=props.get("is_completed"),
        rpe=props.get("rpe"),
        energy_level=props.get("energy_level"),
        pain_level=props.get("pain_level"),
        pain_location=props.get("pain_location"),
        diary_comment=props.get("diary_comment"),
        actual_duration_minutes=props.get("actual_duration_minutes"),
        actual_intensity=props.get("actual_intensity"),
        actual_distance_km=props.get("actual_distance_km"),
        post_feeling=props.get("post_feeling"),
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

    @st.dialog("Legg til økt")
    def choose_session_dialog():
        if st.button("Ny økt", key="choose_new_session", width="stretch"):
            st.session_state["prefill_session"] = None
            st.session_state["show_dialog"] = "add"
            st.session_state["dialog_mode"] = "add"
            st.rerun()

        with st.expander("Forhåndsdefinerte økter"):
            if not templates:
                st.info(
                    "Ingen forhåndsdefinerte økter funnet. Legg til på Bruker-siden."
                )
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

    @st.dialog("Legg til treningsøkt", width="large")
    def add_session_dialog():
        prefill = st.session_state.get("prefill_session") or {}

        # Set defaults
        default_activity = prefill.get("activity") or "Løping"
        if default_activity not in ACTIVITIES:
            default_activity = list(ACTIVITIES.keys())[0]

        default_intensity = prefill.get("intensity") or "Lett"
        intensity_options = ["Lett", "Moderat", "Hardt"]
        if default_intensity not in intensity_options:
            default_intensity = "Lett"

        default_time_slot = prefill.get("time_slot") or TIME_SLOTS[0]
        if default_time_slot not in TIME_SLOTS:
            default_time_slot = TIME_SLOTS[0]

        default_session_type = prefill.get("session_type") or "Rolig"
        if default_session_type not in SESSION_TYPES:
            default_session_type = SESSION_TYPES[0]

        goal_options = ["-"] + SESSION_GOALS
        default_session_goal = prefill.get("session_goal") or "-"
        if default_session_goal not in goal_options:
            default_session_goal = "-"

        priority_options = ["-"] + SESSION_PRIORITIES
        default_priority = prefill.get("priority") or "-"
        if default_priority not in priority_options:
            default_priority = "-"

        focus_options = ["-"] + BODY_FOCUS_AREAS
        default_body_focus = prefill.get("body_focus") or "-"
        if default_body_focus not in focus_options:
            default_body_focus = "-"

        # Use a regular container so dependent fields update immediately on change
        with st.container():
            st.markdown("### 🎯 Økt-type")

            col_activity, col_type, col_intensity = st.columns(3)
            with col_activity:
                activity = st.selectbox(
                    "Aktivitet",
                    list(ACTIVITIES.keys()),
                    index=list(ACTIVITIES.keys()).index(default_activity),
                    key="add_activity",
                )
            with col_type:
                session_type = st.selectbox(
                    "Type økt",
                    SESSION_TYPES,
                    index=SESSION_TYPES.index(default_session_type),
                    key="add_session_type",
                )
            with col_intensity:
                intensity_display = [
                    f"{i} {INTENSITIES[i]['emoji']}" for i in intensity_options
                ]
                intensity_label_default = (
                    f"{default_intensity} {INTENSITIES[default_intensity]['emoji']}"
                )
                intensity_label = st.selectbox(
                    "Intensitet",
                    intensity_display,
                    index=intensity_display.index(intensity_label_default),
                    key="add_intensity",
                )
                intensity = intensity_label.split(" ")[0]

            st.write("")
            st.markdown("#### 📋 Grunninfo")

            col_date, col_duration, col_distance = st.columns(3)
            with col_date:
                session_date = st.date_input(
                    "Dato",
                    value=st.session_state["selected_date"],
                    format="DD/MM/YYYY",
                )
            with col_duration:
                duration_minutes = st.number_input(
                    "Varighet (min)",
                    min_value=0,
                    step=5,
                    value=int(prefill.get("duration_minutes") or 0),
                )

            with col_distance:
                distance_km = st.number_input(
                    "Distanse (km)",
                    min_value=0.0,
                    step=0.1,
                    value=float(prefill.get("distance_km") or 0.0),
                    disabled=not ACTIVITIES[activity].get("distance", False),
                )
            if not ACTIVITIES[activity].get("distance", False):
                distance_km = 0.0
                st.caption("Denne aktiviteten bruker ikke distansefelt.")

            interval_structure = None
            if session_type == "Intervall":
                interval_repetitions_default = 10
                interval_work_default = 3.0
                interval_work_unit_default = "minutter"
                interval_pause_seconds_default = 60

                raw_interval = prefill.get("planned_structure") or ""
                if raw_interval:
                    normalized = raw_interval.replace(",", ".")
                    new_match = re.match(
                        r"^\s*(\d+)\s*x\s*(\d+)\s*x\s*([\d.]+)\s*"
                        r"(sekunder|minutter|meter|kilometer)\s*med\s*([\d.]+)\s*sekunder pause\s*$",
                        normalized,
                    )
                    single_new_match = re.match(
                        r"^\s*(\d+)\s*x\s*([\d.]+)\s*"
                        r"(sekunder|minutter|meter|kilometer)\s*med\s*([\d.]+)\s*sekunder pause\s*$",
                        normalized,
                    )
                    old_match = re.match(
                        r"^\s*(\d+)\s*x\s*(\d+)\s*x\s*([\d.]+)\s*min\s*med\s*([\d.]+)\s*min pause\s*$",
                        normalized,
                    )
                    if single_new_match:
                        interval_repetitions_default = int(single_new_match.group(1))
                        interval_work_default = float(single_new_match.group(2))
                        interval_work_unit_default = single_new_match.group(3)
                        interval_pause_seconds_default = int(
                            float(single_new_match.group(4))
                        )
                    elif new_match:
                        interval_repetitions_default = int(new_match.group(1)) * int(
                            new_match.group(2)
                        )
                        interval_work_default = float(new_match.group(3))
                        interval_work_unit_default = new_match.group(4)
                        interval_pause_seconds_default = int(float(new_match.group(5)))
                    elif old_match:
                        interval_repetitions_default = int(old_match.group(1)) * int(
                            old_match.group(2)
                        )
                        interval_work_default = float(old_match.group(3))
                        interval_work_unit_default = "minutter"
                        interval_pause_seconds_default = int(
                            float(old_match.group(4)) * 60
                        )

                st.markdown("#### ⏱️ Intervall")
                col_reps, col_work, col_unit, col_pause = st.columns(4)
                with col_reps:
                    interval_repetitions = st.number_input(
                        "Repetisjoner",
                        min_value=1,
                        value=interval_repetitions_default,
                        step=1,
                    )
                with col_work:
                    interval_work_value = st.number_input(
                        "Arbeid",
                        min_value=0.1,
                        value=float(interval_work_default),
                        step=0.1,
                    )
                with col_unit:
                    interval_work_unit = st.selectbox(
                        "Enhet",
                        ["sekunder", "minutter", "meter", "kilometer"],
                        index=["sekunder", "minutter", "meter", "kilometer"].index(
                            interval_work_unit_default
                        ),
                    )
                with col_pause:
                    interval_pause_seconds = st.number_input(
                        "Pause (sek)",
                        min_value=0,
                        value=interval_pause_seconds_default,
                        step=5,
                    )

                work_value_display = format(float(interval_work_value), "g")
                pause_display = format(float(interval_pause_seconds), "g")

                interval_structure = (
                    f"{interval_repetitions} x "
                    f"{work_value_display} {interval_work_unit} med "
                    f"{pause_display} sekunder pause"
                )
                st.caption(f"Planlagt struktur: {interval_structure}")

            session_goal = default_session_goal
            body_focus = default_body_focus
            priority = default_priority

            st.write("")
            st.markdown("#### 📌 Mål og plan")

            col_goal, col_focus, col_priority = st.columns(3)
            with col_goal:
                session_goal = st.selectbox(
                    "Mål",
                    goal_options,
                    index=goal_options.index(default_session_goal),
                    key="add_session_goal",
                )
            with col_focus:
                body_focus = st.selectbox(
                    "Fokus",
                    focus_options,
                    index=focus_options.index(default_body_focus),
                    key="add_body_focus",
                )
            with col_priority:
                priority = st.selectbox(
                    "Prioritet",
                    priority_options,
                    index=priority_options.index(default_priority),
                    key="add_priority",
                )

            session_goal_value = None if session_goal == "-" else session_goal
            body_focus_value = None if body_focus == "-" else body_focus
            priority_value = None if priority == "-" else priority
            planned_structure = interval_structure if session_type == "Intervall" else None

            st.write("")
            st.markdown("#### 📝 Notater")
            notes = st.text_area(
                "Notater",
                value=prefill.get("notes") or "",
                height=80,
                label_visibility="collapsed",
            )

            st.divider()
            col1, col2 = st.columns(2)

            with col1:
                submitted = st.button("💾 Lagre økt", use_container_width=True)
            with col2:
                cancel = st.button("❌ Avbryt", use_container_width=True)

            if submitted:
                add_training_session(
                    user_id=st.session_state.user_id,
                    title=f"{activity} - {session_type}",
                    activity=activity,
                    intensity=intensity,
                    time_slot=default_time_slot,
                    session_date=str(session_date),
                    duration_minutes=duration_minutes,
                    distance_km=distance_km,
                    notes=notes,
                    session_type=session_type,
                    session_goal=session_goal_value,
                    planned_structure=planned_structure.strip() or None,
                    priority=priority_value,
                    body_focus=body_focus_value,
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

    @st.dialog("Treningsøkt", width="medium")
    def show_event_dialog():
        edit_mode = st.session_state.get("edit_mode", False)
        completion_mode = st.session_state.get("completion_mode", False)
        session_date_obj = datetime.fromisoformat(props["session_date"]).date()
        can_mark_completed = session_date_obj <= date.today()

        if not edit_mode and not completion_mode:
            # ===== VISNINGS-MODUS =====
            activity_name = props.get("activity") or "-"
            activity_icon = ACTIVITIES.get(activity_name, {}).get("icon", "🏋️")
            intensity_name = props.get("intensity") or "-"
            intensity_meta = INTENSITIES.get(intensity_name, {})
            intensity_color = intensity_meta.get("color", "#6c757d")
            intensity_emoji = intensity_meta.get("emoji", "⚪")

            st.subheader(props.get("raw_title") or event["title"])

            summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(
                [1.5, 1, 1, 1.35]
            )
            with summary_col1:
                st.markdown(f"**{activity_icon} {activity_name}**")
            with summary_col2:
                st.markdown(f"**⏱️ {props['duration_minutes']} min**")
            with summary_col3:
                st.markdown(f"**📏 {props['distance_km']} km**")
            with summary_col4:
                st.markdown(
                    (
                        "<span style='display:inline-block;padding:0.2rem 0.6rem;"
                        "font-size:1rem;white-space:nowrap;"
                        f"border-radius:999px;background:{intensity_color};color:white;'>"
                        f"{intensity_emoji} Intensitet: {intensity_name}</span>"
                    ),
                    unsafe_allow_html=True,
                )

            st.markdown("#### Planlagt")
            planned_col1, planned_col2, planned_col3 = st.columns([1, 1, 1])
            with planned_col1:
                st.write(f"**Mål:** {props.get('session_goal') or '-'}")
            with planned_col2:
                st.write(f"**Fokus:** {props.get('body_focus') or '-'}")
            with planned_col3:
                st.write(f"**Prioritet:** {props.get('priority') or '-'}")

            if props.get("session_type") == "Intervall":
                interval_text = props.get("planned_structure") or "-"
                if interval_text != "-":
                    normalized = interval_text.replace(",", ".")
                    single_new_match = re.match(
                        r"^\s*(\d+)\s*x\s*([\d.]+)\s*"
                        r"(sekunder|minutter|meter|kilometer)\s*med\s*([\d.]+)\s*sekunder pause\s*$",
                        normalized,
                    )
                    new_match = re.match(
                        r"^\s*(\d+)\s*x\s*(\d+)\s*x\s*([\d.]+)\s*"
                        r"(sekunder|minutter|meter|kilometer)\s*med\s*([\d.]+)\s*sekunder pause\s*$",
                        normalized,
                    )
                    old_match = re.match(
                        r"^\s*(\d+)\s*x\s*(\d+)\s*x\s*([\d.]+)\s*min\s*med\s*([\d.]+)\s*min pause\s*$",
                        normalized,
                    )
                    if single_new_match:
                        repetitions = single_new_match.group(1)
                        work = format(float(single_new_match.group(2)), "g")
                        work_unit = single_new_match.group(3)
                        pause = format(float(single_new_match.group(4)), "g")
                        interval_text = f"{repetitions} x {work} {work_unit} - Pause: {pause} s"
                    elif new_match:
                        repetitions = str(int(new_match.group(1)) * int(new_match.group(2)))
                        work = format(float(new_match.group(3)), "g")
                        work_unit = new_match.group(4)
                        pause = format(float(new_match.group(5)), "g")
                        interval_text = f"{repetitions} x {work} {work_unit} - Pause: {pause} s"
                    elif old_match:
                        repetitions = str(int(old_match.group(1)) * int(old_match.group(2)))
                        work = format(float(old_match.group(3)), "g")
                        pause_seconds = format(float(old_match.group(4)) * 60, "g")
                        interval_text = f"{repetitions} x {work} minutter - Pause: {pause_seconds} s"
                st.write(f"**Intervall:** {interval_text}")

            if props.get("is_completed"):
                st.markdown("#### ✅ Fullført")
                done_col1, done_col2, done_col3, done_col4 = st.columns(4)
                with done_col1:
                    st.caption("RPE")
                    st.markdown(f"**{props.get('rpe') or '-'}**")
                with done_col2:
                    st.caption("Energi")
                    st.markdown(f"**{props.get('energy_level') or '-'}**")
                with done_col3:
                    st.caption("Smerte")
                    st.markdown(f"**{props.get('pain_level') or '-'}**")
                with done_col4:
                    st.caption("Følelse")
                    st.markdown(f"**{props.get('post_feeling') or '-'}**")

                actual_col1, actual_col2, actual_col3 = st.columns(3)
                with actual_col1:
                    actual_duration = (
                        f"{props.get('actual_duration_minutes')} min"
                        if props.get("actual_duration_minutes") is not None
                        else "-"
                    )
                    st.caption("Faktisk varighet")
                    st.markdown(f"**⏱️ {actual_duration}**")
                with actual_col2:
                    actual_distance = (
                        f"{props.get('actual_distance_km')} km"
                        if props.get("actual_distance_km") is not None
                        else "-"
                    )
                    st.caption("Faktisk distanse")
                    st.markdown(f"**📏 {actual_distance}**")
                with actual_col3:
                    st.caption("Faktisk intensitet")
                    st.markdown(f"**{props.get('actual_intensity') or '-'}**")

                if props.get("pain_location"):
                    st.caption("Hvor på kroppen")
                    st.write(props.get("pain_location"))

                if props.get("diary_comment"):
                    st.caption("Kommentar")
                    st.info(props.get("diary_comment"))

            if props.get("notes"):
                st.caption("Notater")
                st.info(props["notes"])

            st.divider()

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✏️ Endre økt", key="btn_edit"):
                    st.session_state["edit_mode"] = True
                    st.session_state["completion_mode"] = False
                    st.session_state["in_editing"] = True
                    st.session_state["show_dialog"] = "view"
                    st.session_state["selected_event"] = event
                    st.rerun()
            with col2:
                complete_label = (
                    "📝 Oppdater fullført"
                    if bool(props.get("is_completed"))
                    else "✅ Marker som fullført"
                )
                if st.button(
                    complete_label,
                    key="btn_complete",
                    disabled=not can_mark_completed,
                ):
                    st.session_state["edit_mode"] = False
                    st.session_state["completion_mode"] = True
                    st.session_state["in_completion"] = True
                    st.session_state["show_dialog"] = "view"
                    st.session_state["selected_event"] = event
                    st.rerun()

                if not can_mark_completed:
                    st.caption(
                        "Kan kun markeres som fullført for i dag eller tidligere dato."
                    )

            with col3:
                if st.button("🗑️ Fjern økt", key="btn_delete"):
                    with st.spinner("Fjerner økten..."):
                        delete_session(session_id)
                    close_dialog(st.session_state)
                    st.rerun()

        elif edit_mode:
            # ===== REDIGERINGS-MODUS =====
            st.subheader("Endre treningsøkt")
            intensity_options = ["Lett", "Moderat", "Hardt"]
            default_session_type = props.get("session_type") or "Rolig"
            if default_session_type not in SESSION_TYPES:
                default_session_type = SESSION_TYPES[0]

            goal_options = ["-"] + SESSION_GOALS
            default_session_goal = props.get("session_goal") or "-"
            if default_session_goal not in goal_options:
                default_session_goal = "-"

            priority_options = ["-"] + SESSION_PRIORITIES
            default_priority = props.get("priority") or "-"
            if default_priority not in priority_options:
                default_priority = "-"

            focus_options = ["-"] + BODY_FOCUS_AREAS
            default_body_focus = props.get("body_focus") or "-"
            if default_body_focus not in focus_options:
                default_body_focus = "-"

            with st.container():
                st.markdown("### 🎯 Økt-type")

                col_activity, col_type, col_intensity = st.columns(3)
                with col_activity:
                    activity = st.selectbox(
                        "Aktivitet",
                        list(ACTIVITIES.keys()),
                        index=list(ACTIVITIES.keys()).index(props["activity"]),
                        key="edit_activity",
                    )
                with col_type:
                    session_type = st.selectbox(
                        "Type økt",
                        SESSION_TYPES,
                        index=SESSION_TYPES.index(default_session_type),
                        key="edit_session_type",
                    )
                with col_intensity:
                    intensity_display = [
                        f"{i} {INTENSITIES[i]['emoji']}" for i in intensity_options
                    ]
                    intensity_label_default = (
                        f"{props['intensity']} {INTENSITIES[props['intensity']]['emoji']}"
                    )
                    intensity_label = st.selectbox(
                        "Intensitet",
                        intensity_display,
                        index=intensity_display.index(intensity_label_default),
                        key="edit_intensity",
                    )
                    intensity = intensity_label.split(" ")[0]

                st.write("")
                st.markdown("#### 📋 Grunninfo")

                col_date, col_duration, col_distance = st.columns(3)
                with col_date:
                    session_date = st.date_input(
                        "Dato",
                        value=session_date_obj,
                        format="DD/MM/YYYY",
                        key="edit_session_date",
                    )
                with col_duration:
                    duration_minutes = st.number_input(
                        "Varighet (min)",
                        min_value=0,
                        step=5,
                        value=int(props.get("duration_minutes") or 0),
                        key="edit_duration_minutes",
                    )
                with col_distance:
                    distance_km = st.number_input(
                        "Distanse (km)",
                        min_value=0.0,
                        step=0.1,
                        value=float(props.get("distance_km") or 0.0),
                        disabled=not ACTIVITIES[activity].get("distance", False),
                        key="edit_distance_km",
                    )
                if not ACTIVITIES[activity].get("distance", False):
                    distance_km = 0.0
                    st.caption("Denne aktiviteten bruker ikke distansefelt.")

                interval_structure = None
                if session_type == "Intervall":
                    interval_repetitions_default = 10
                    interval_work_default = 3.0
                    interval_work_unit_default = "minutter"
                    interval_pause_seconds_default = 60

                    raw_interval = props.get("planned_structure") or ""
                    if raw_interval:
                        normalized = raw_interval.replace(",", ".")
                        new_match = re.match(
                            r"^\s*(\d+)\s*x\s*(\d+)\s*x\s*([\d.]+)\s*"
                            r"(sekunder|minutter|meter|kilometer)\s*med\s*([\d.]+)\s*sekunder pause\s*$",
                            normalized,
                        )
                        single_new_match = re.match(
                            r"^\s*(\d+)\s*x\s*([\d.]+)\s*"
                            r"(sekunder|minutter|meter|kilometer)\s*med\s*([\d.]+)\s*sekunder pause\s*$",
                            normalized,
                        )
                        old_match = re.match(
                            r"^\s*(\d+)\s*x\s*(\d+)\s*x\s*([\d.]+)\s*min\s*med\s*([\d.]+)\s*min pause\s*$",
                            normalized,
                        )
                        if single_new_match:
                            interval_repetitions_default = int(single_new_match.group(1))
                            interval_work_default = float(single_new_match.group(2))
                            interval_work_unit_default = single_new_match.group(3)
                            interval_pause_seconds_default = int(
                                float(single_new_match.group(4))
                            )
                        elif new_match:
                            interval_repetitions_default = int(new_match.group(1)) * int(
                                new_match.group(2)
                            )
                            interval_work_default = float(new_match.group(3))
                            interval_work_unit_default = new_match.group(4)
                            interval_pause_seconds_default = int(
                                float(new_match.group(5))
                            )
                        elif old_match:
                            interval_repetitions_default = int(old_match.group(1)) * int(
                                old_match.group(2)
                            )
                            interval_work_default = float(old_match.group(3))
                            interval_work_unit_default = "minutter"
                            interval_pause_seconds_default = int(
                                float(old_match.group(4)) * 60
                            )

                    st.markdown("#### ⏱️ Intervall")
                    col_reps, col_work, col_unit, col_pause = st.columns(4)
                    with col_reps:
                        interval_repetitions = st.number_input(
                            "Repetisjoner",
                            min_value=1,
                            value=interval_repetitions_default,
                            step=1,
                            key="edit_interval_repetitions",
                        )
                    with col_work:
                        interval_work_value = st.number_input(
                            "Arbeid",
                            min_value=0.1,
                            value=float(interval_work_default),
                            step=0.1,
                            key="edit_interval_work_value",
                        )
                    with col_unit:
                        interval_work_unit = st.selectbox(
                            "Enhet",
                            ["sekunder", "minutter", "meter", "kilometer"],
                            index=["sekunder", "minutter", "meter", "kilometer"].index(
                                interval_work_unit_default
                            ),
                            key="edit_interval_work_unit",
                        )
                    with col_pause:
                        interval_pause_seconds = st.number_input(
                            "Pause (sek)",
                            min_value=0,
                            value=interval_pause_seconds_default,
                            step=5,
                            key="edit_interval_pause_seconds",
                        )

                    work_value_display = format(float(interval_work_value), "g")
                    pause_display = format(float(interval_pause_seconds), "g")

                    interval_structure = (
                        f"{interval_repetitions} x "
                        f"{work_value_display} {interval_work_unit} med "
                        f"{pause_display} sekunder pause"
                    )
                    st.caption(f"Planlagt struktur: {interval_structure}")

                session_goal = default_session_goal
                body_focus = default_body_focus
                priority = default_priority

                st.write("")
                st.markdown("#### 📌 Mål og plan")

                col_goal, col_focus, col_priority = st.columns(3)
                with col_goal:
                    session_goal = st.selectbox(
                        "Mål",
                        goal_options,
                        index=goal_options.index(default_session_goal),
                        key="edit_session_goal",
                    )
                with col_focus:
                    body_focus = st.selectbox(
                        "Fokus",
                        focus_options,
                        index=focus_options.index(default_body_focus),
                        key="edit_body_focus",
                    )
                with col_priority:
                    priority = st.selectbox(
                        "Prioritet",
                        priority_options,
                        index=priority_options.index(default_priority),
                        key="edit_priority",
                    )

                session_goal_value = None if session_goal == "-" else session_goal
                body_focus_value = None if body_focus == "-" else body_focus
                priority_value = None if priority == "-" else priority
                planned_structure = (
                    interval_structure if session_type == "Intervall" else None
                )

                st.write("")
                st.markdown("#### 📝 Notater")
                notes = st.text_area(
                    "Notater",
                    value=props.get("notes") or "",
                    height=80,
                    label_visibility="collapsed",
                    key="edit_notes",
                )

                st.divider()
                col1, col2 = st.columns(2)
                with col1:
                    save_clicked = st.button("💾 Lagre økt", use_container_width=True)
                with col2:
                    cancel_clicked = st.button("❌ Avbryt", use_container_width=True)

                if save_clicked:
                    update_session(
                        session_id=session_id,
                        title=f"{activity} - {session_type}",
                        activity=activity,
                        intensity=intensity,
                        time_slot=props.get("time_slot"),
                        session_date=str(session_date),
                        duration_minutes=duration_minutes,
                        distance_km=distance_km,
                        notes=notes,
                        session_type=session_type,
                        session_goal=session_goal_value,
                        planned_structure=planned_structure.strip() or None,
                        priority=priority_value,
                        body_focus=body_focus_value,
                    )
                    st.session_state["edit_mode"] = False
                    st.session_state["completion_mode"] = False
                    st.session_state["show_dialog"] = "view"
                    st.rerun()

                if cancel_clicked:
                    st.session_state["edit_mode"] = False
                    st.session_state["completion_mode"] = False
                    st.session_state["show_dialog"] = "view"
                    st.rerun()

        else:
            # ===== COMPLETION MODE (QUICK LOG + FULL LOG) =====
            st.subheader("✅ Marker som fullført")

            # Prep defaults
            intensity_options = ["Lett", "Moderat", "Hardt"]

            actual_duration_default = props.get("actual_duration_minutes")
            if actual_duration_default is None:
                actual_duration_default = props.get("duration_minutes") or 0

            actual_distance_default = props.get("actual_distance_km")
            if actual_distance_default is None:
                actual_distance_default = float(props.get("distance_km") or 0.0)

            actual_intensity_default = props.get("actual_intensity") or props.get(
                "intensity"
            )
            if actual_intensity_default not in intensity_options:
                actual_intensity_default = intensity_options[0]

            with st.form("complete_session_form"):
                # ========================================
                # BLOCK 1: PLANNED VS ACTUAL (COMPACT)
                # ========================================
                st.markdown("### 📊 Plan vs Faktisk")

                col_plan, col_actual = st.columns(2)

                with col_plan:
                    st.markdown("#### 📋 Planlagt")
                    st.markdown(f"**{props.get('duration_minutes')} min**")
                    st.markdown(f"{props.get('distance_km')} km")
                    st.markdown(f"*{props.get('intensity')} - {props.get('activity')}*")

                with col_actual:
                    st.markdown("#### 🎯 Faktisk")
                    actual_duration_minutes = st.number_input(
                        "Faktisk varighet (min)",
                        min_value=0,
                        value=int(actual_duration_default),
                        step=5,
                        label_visibility="collapsed",
                    )
                    actual_distance_km = st.number_input(
                        "Faktisk distanse (km)",
                        min_value=0.0,
                        value=float(actual_distance_default),
                        step=0.1,
                        label_visibility="collapsed",
                    )
                    actual_intensity = st.selectbox(
                        "Faktisk intensitet",
                        intensity_options,
                        index=intensity_options.index(actual_intensity_default),
                        label_visibility="collapsed",
                    )

                st.divider()

                # ========================================
                # BLOCK 2: CORE - "HOW DID IT FEEL?"
                # ========================================
                st.markdown("### 💭 Hvordan føltes økten?")
                st.markdown("*Dette er det viktigste*")

                # RPE Slider (prominent)
                st.markdown("**RPE - Opplevd anstrengelse**")
                rpe_help = "1=veldig lett, 5=moderat, 10=maksimal innsats"
                rpe_value = st.slider(
                    "RPE (1-10)",
                    min_value=1,
                    max_value=10,
                    value=int(props.get("rpe") or 5),
                    help=rpe_help,
                    label_visibility="collapsed",
                )

                st.markdown("**Energi**")
                energy_level = st.select_slider(
                    "Energi",
                    options=ENERGY_LEVELS,
                    value=props.get("energy_level")
                    if props.get("energy_level") in ENERGY_LEVELS
                    else ENERGY_LEVELS[2],
                    label_visibility="collapsed",
                )

                st.markdown("**Smerte/Ubehag**")
                pain_level = st.select_slider(
                    "Smerte/Ubehag",
                    options=PAIN_LEVELS,
                    value=props.get("pain_level")
                    if props.get("pain_level") in PAIN_LEVELS
                    else PAIN_LEVELS[0],
                    label_visibility="collapsed",
                )

                # Vis smertelokasjon kun hvis smerte != "Ingen"
                pain_location = ""
                # Reorder post_feeling: Tappet - Støl - Nøytral - Motivert - Energisk
                post_feeling_order = [
                    "Tappet",
                    "Støl",
                    "Nøytral",
                    "Motivert",
                    "Energisk",
                ]
                st.markdown("**Følelse etter økt**")
                post_feeling = st.select_slider(
                    "Følelse etter økt",
                    options=post_feeling_order,
                    value=props.get("post_feeling")
                    if props.get("post_feeling") in post_feeling_order
                    else "Nøytral",
                    label_visibility="collapsed",
                )

                st.divider()

                # ========================================
                # BLOCK 3: DETAILS (COLLAPSIBLE)
                # ========================================
                with st.expander("📝 **Detaljer** (optional)", expanded=False):
                    if pain_level != "Ingen":
                        st.markdown("**Hvor på kroppen?**")
                        pain_location = st.text_input(
                            "Hvor på kroppen?",
                            value=props.get("pain_location") or "",
                            placeholder="f.eks. høyre kne, skulder",
                            label_visibility="collapsed",
                            key="complete_pain_location",
                        )

                    st.markdown("**Kommentar**")
                    diary_comment = st.text_area(
                        "Kommentar",
                        value=props.get("diary_comment") or "",
                        placeholder="Notater om økten...",
                        height=60,
                        label_visibility="collapsed",
                        key="complete_diary_comment",
                    )

                st.divider()

                st.divider()

                # ========================================
                # BUTTONS
                # ========================================
                col1, col2 = st.columns(2)
                with col1:
                    save_complete_clicked = st.form_submit_button(
                        "✅ Marker som fullført", width="stretch"
                    )
                with col2:
                    cancel_complete_clicked = st.form_submit_button(
                        "❌ Avbryt", width="stretch"
                    )

                if save_complete_clicked:
                    update_session(
                        session_id=session_id,
                        title=props.get("raw_title"),
                        activity=props.get("activity"),
                        intensity=props.get("intensity"),
                        time_slot=props.get("time_slot"),
                        session_date=props.get("session_date"),
                        duration_minutes=props.get("duration_minutes"),
                        distance_km=props.get("distance_km"),
                        notes=props.get("notes"),
                        is_completed=True,
                        rpe=rpe_value,
                        energy_level=energy_level,
                        pain_level=pain_level,
                        pain_location=pain_location.strip() or None,
                        diary_comment=diary_comment.strip() or None,
                        actual_duration_minutes=int(actual_duration_minutes),
                        actual_intensity=actual_intensity,
                        actual_distance_km=float(actual_distance_km),
                        post_feeling=post_feeling,
                    )
                    st.session_state["completion_mode"] = False
                    st.session_state["edit_mode"] = False
                    st.session_state["show_dialog"] = "view"
                    st.rerun()

                if cancel_complete_clicked:
                    st.session_state["completion_mode"] = False
                    st.session_state["edit_mode"] = False
                    st.session_state["show_dialog"] = "view"
                    st.rerun()

    show_event_dialog()
    st.session_state["show_dialog"] = None

from services.database import (
    update_training_session,
    delete_training_session,
    add_training_session_db,
    get_all_sessions_for_user,
    get_user_profile,
    upsert_user_profile,
    add_predefined_session,
    get_predefined_sessions,
    delete_predefined_session,
    update_predefined_session,
)
from utils.constants import INTENSITIES, ACTIVITIES


def add_training_session(
    user_id,
    title,
    activity,
    intensity,
    time_slot,
    session_date,
    duration_minutes,
    distance_km,
    notes,
):
    add_training_session_db(
        user_id,
        title,
        activity,
        intensity,
        time_slot,
        session_date,
        duration_minutes,
        distance_km,
        notes,
    )


def get_all_sessions(user_id):
    return get_all_sessions_for_user(user_id)


def convert_sessions_to_calendar_events(rows):

    events = []

    for row in rows:
        (
            session_id,
            title,
            activity,
            intensity,
            time_slot,
            session_date,
            duration_minutes,
            distance_km,
            notes,
        ) = row

        icon = ACTIVITIES.get(activity, {}).get("icon", "🏃")
        color = INTENSITIES.get(intensity, {}).get("color", "#2196F3")

        events.append(
            {
                "id": session_id,
                "title": f"{icon} {title}",
                "start": session_date,
                "color": color,
                "extendedProps": {
                    "raw_title": title,
                    "activity": activity,
                    "intensity": intensity,
                    "time_slot": time_slot,
                    "session_date": session_date,
                    "duration_minutes": duration_minutes,
                    "distance_km": distance_km,
                    "notes": notes,
                    "tooltip": f"{activity} • {intensity} • {duration_minutes} min",
                },
            }
        )

    return events


def update_session(
    session_id,
    title,
    activity,
    intensity,
    time_slot,
    session_date,
    duration_minutes,
    distance_km,
    notes,
):

    update_training_session(
        session_id,
        title,
        activity,
        intensity,
        time_slot,
        session_date,
        duration_minutes,
        distance_km,
        notes,
    )


def delete_session(session_id):

    delete_training_session(session_id)

    # st.session_state.pop("selected_event", None)
    # st.session_state.pop("edit_mode", None)

    # st.rerun()


def sessions_to_dicts(rows):

    sessions = []

    for r in rows:
        sessions.append(
            {
                "id": r[0],
                "title": r[1],
                "activity": r[2],
                "intensity": r[3],
                "time_slot": r[4],
                "session_date": r[5],
                "duration_minutes": r[6],
                "distance_km": r[7],
                "notes": r[8],
            }
        )

    return sessions


def get_profile(user_id):
    return get_user_profile(user_id)


def save_profile(
    user_id,
    first_name,
    last_name,
    age,
    sex,
    height_cm,
    weight_kg,
    resting_hr,
    max_hr,
    ftp_watts,
    vo2max,
):
    upsert_user_profile(
        user_id,
        first_name,
        last_name,
        age,
        sex,
        height_cm,
        weight_kg,
        resting_hr,
        max_hr,
        ftp_watts,
        vo2max,
    )


def get_sidebar_first_name(user_id, fallback_username):
    profile = get_user_profile(user_id)
    if profile:
        first_name = (profile.get("first_name") or "").strip()
        if first_name:
            return first_name

        legacy_full_name = (profile.get("full_name") or "").strip()
        if legacy_full_name:
            return legacy_full_name.split()[0]

    return fallback_username


def add_template(
    user_id,
    name,
    activity,
    intensity,
    time_slot,
    duration_minutes,
    distance_km,
    notes,
    include_in_calendar,
):
    add_predefined_session(
        user_id,
        name,
        activity,
        intensity,
        time_slot,
        duration_minutes,
        distance_km,
        notes,
        include_in_calendar,
    )


def get_templates(user_id, include_in_calendar=None):
    rows = get_predefined_sessions(user_id, include_in_calendar=include_in_calendar)
    templates = []
    for r in rows:
        templates.append(
            {
                "id": r[0],
                "user_id": r[1],
                "name": r[2],
                "activity": r[3],
                "intensity": r[4],
                "time_slot": r[5],
                "duration_minutes": r[6],
                "distance_km": r[7],
                "notes": r[8],
                "include_in_calendar": bool(r[9]),
            }
        )
    return templates


def delete_template(template_id, user_id):
    delete_predefined_session(template_id, user_id)


def update_template(
    template_id,
    user_id,
    name,
    activity,
    intensity,
    time_slot,
    duration_minutes,
    distance_km,
    notes,
    include_in_calendar,
):
    update_predefined_session(
        session_id=template_id,
        user_id=user_id,
        name=name,
        activity=activity,
        intensity=intensity,
        time_slot=time_slot,
        duration_minutes=duration_minutes,
        distance_km=distance_km,
        notes=notes,
        include_in_calendar=include_in_calendar,
    )

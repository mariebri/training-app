from services.database import (
    get_connection,
    update_training_session,
    delete_training_session,
    add_training_session_db,
    get_all_sessions_for_user,
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

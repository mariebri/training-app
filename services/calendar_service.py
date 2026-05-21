from services.database import (
    get_connection,
    update_training_session,
    delete_training_session,
)
from utils.constants import INTENSITIES, ACTIVITIES


def add_training_session(
    title,
    activity,
    intensity,
    time_slot,
    session_date,
    duration_minutes,
    distance_km,
    notes,
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO training_sessions (
            title,
            activity,
            intensity,
            time_slot,
            session_date,
            duration_minutes,
            distance_km,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            title,
            activity,
            intensity,
            time_slot,
            session_date,
            duration_minutes,
            distance_km,
            notes,
        ),
    )

    conn.commit()
    conn.close()


def get_all_sessions():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            title,
            activity,
            intensity,
            time_slot,
            session_date,
            duration_minutes,
            distance_km,
            notes
        FROM training_sessions
        """
    )

    rows = cursor.fetchall()

    conn.close()

    return rows


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

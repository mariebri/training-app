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
from utils.constants import INTENSITIES


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
    session_type=None,
    session_goal=None,
    planned_structure=None,
    priority=None,
    body_focus=None,
    is_completed=False,
    rpe=None,
    energy_level=None,
    pain_level=None,
    pain_location=None,
    diary_comment=None,
    actual_duration_minutes=None,
    actual_intensity=None,
    actual_distance_km=None,
    post_feeling=None,
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
        session_type,
        session_goal,
        planned_structure,
        priority,
        body_focus,
        is_completed,
        rpe,
        energy_level,
        pain_level,
        pain_location,
        diary_comment,
        actual_duration_minutes,
        actual_intensity,
        actual_distance_km,
        post_feeling,
    )


def get_all_sessions(user_id):
    return get_all_sessions_for_user(user_id)


def convert_sessions_to_calendar_events(rows, mark_completed=False):

    events = []

    for row in rows:
        session_id = row[0]
        title = row[1]
        activity = row[2]
        intensity = row[3]
        time_slot = row[4]
        session_date = row[5]
        duration_minutes = row[6]
        distance_km = row[7]
        notes = row[8]
        session_type = row[9] if len(row) > 9 else None
        session_goal = row[10] if len(row) > 10 else None
        planned_structure = row[11] if len(row) > 11 else None
        priority = row[12] if len(row) > 12 else None
        body_focus = row[13] if len(row) > 13 else None
        is_completed = bool(row[14]) if len(row) > 14 else False
        rpe = row[15] if len(row) > 15 else None
        energy_level = row[16] if len(row) > 16 else None
        pain_level = row[17] if len(row) > 17 else None
        pain_location = row[18] if len(row) > 18 else None
        diary_comment = row[19] if len(row) > 19 else None
        actual_duration_minutes = row[20] if len(row) > 20 else None
        actual_intensity = row[21] if len(row) > 21 else None
        actual_distance_km = row[22] if len(row) > 22 else None
        post_feeling = row[23] if len(row) > 23 else None

        color = INTENSITIES.get(intensity, {}).get("color", "#2196F3")
        completed_prefix = "✅ " if mark_completed and is_completed else ""

        events.append(
            {
                "id": session_id,
            "title": f"{completed_prefix}{title}",
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
                    "session_type": session_type,
                    "session_goal": session_goal,
                    "planned_structure": planned_structure,
                    "priority": priority,
                    "body_focus": body_focus,
                    "is_completed": is_completed,
                    "rpe": rpe,
                    "energy_level": energy_level,
                    "pain_level": pain_level,
                    "pain_location": pain_location,
                    "diary_comment": diary_comment,
                    "actual_duration_minutes": actual_duration_minutes,
                    "actual_intensity": actual_intensity,
                    "actual_distance_km": actual_distance_km,
                    "post_feeling": post_feeling,
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
    session_type=None,
    session_goal=None,
    planned_structure=None,
    priority=None,
    body_focus=None,
    is_completed=None,
    rpe=None,
    energy_level=None,
    pain_level=None,
    pain_location=None,
    diary_comment=None,
    actual_duration_minutes=None,
    actual_intensity=None,
    actual_distance_km=None,
    post_feeling=None,
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
        session_type,
        session_goal,
        planned_structure,
        priority,
        body_focus,
        is_completed,
        rpe,
        energy_level,
        pain_level,
        pain_location,
        diary_comment,
        actual_duration_minutes,
        actual_intensity,
        actual_distance_km,
        post_feeling,
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
                "session_type": r[9] if len(r) > 9 else None,
                "session_goal": r[10] if len(r) > 10 else None,
                "planned_structure": r[11] if len(r) > 11 else None,
                "priority": r[12] if len(r) > 12 else None,
                "body_focus": r[13] if len(r) > 13 else None,
                "is_completed": bool(r[14]) if len(r) > 14 else False,
                "rpe": r[15] if len(r) > 15 else None,
                "energy_level": r[16] if len(r) > 16 else None,
                "pain_level": r[17] if len(r) > 17 else None,
                "pain_location": r[18] if len(r) > 18 else None,
                "diary_comment": r[19] if len(r) > 19 else None,
                "actual_duration_minutes": r[20] if len(r) > 20 else None,
                "actual_intensity": r[21] if len(r) > 21 else None,
                "actual_distance_km": r[22] if len(r) > 22 else None,
                "post_feeling": r[23] if len(r) > 23 else None,
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

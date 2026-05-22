from collections import defaultdict
from datetime import date, datetime, timedelta

from services.performance_model import (
    classify_daily_risk,
    compute_ctl_atl,
    compute_load,
    recommend_next_7d_max_load,
)


def initialize_calendar_state(session_state):
    defaults = {
        "dialog_mode": None,
        "selected_date": date.today(),
        "selected_event": None,
        "edit_mode": False,
        "last_calendar_action": None,
        "prefill_session": None,
    }
    for key, value in defaults.items():
        if key not in session_state:
            session_state[key] = value


def close_dialog(session_state):
    session_state.pop("show_dialog", None)
    session_state["dialog_mode"] = None
    session_state["selected_event"] = None
    session_state["edit_mode"] = False
    session_state["selected_date"] = date.today()
    session_state["prefill_session"] = None


def open_add_dialog(session_state, selected_date=None):
    session_state["show_dialog"] = "add"
    session_state["dialog_mode"] = "add"
    session_state["selected_event"] = None
    session_state["edit_mode"] = False
    session_state["selected_date"] = selected_date or date.today()


def open_choose_dialog(session_state, selected_date=None):
    session_state["show_dialog"] = "choose"
    session_state["dialog_mode"] = "choose"
    session_state["selected_event"] = None
    session_state["edit_mode"] = False
    session_state["selected_date"] = selected_date or date.today()


def open_view_dialog(session_state, event):
    session_state["show_dialog"] = "view"
    session_state["dialog_mode"] = "view"
    session_state["selected_event"] = event
    session_state["edit_mode"] = session_state.pop("in_editing", False)


def normalize_clicked_date(clicked_date_str):
    # Temporary workaround for one-day shift in calendar click payload.
    return datetime.strptime(clicked_date_str, "%Y-%m-%d").date() + timedelta(days=1)


def build_risk_overlay_events(rows):
    sessions = [
        {"session_date": r[5], "duration_minutes": r[6], "intensity": r[3]} for r in rows
    ]

    if not sessions:
        return []

    history = compute_ctl_atl(sessions)
    latest_tsb = history[-1]["tsb"] if history else 0

    today = date.today()
    week_7_start = today - timedelta(days=6)
    week_28_start = today - timedelta(days=27)

    weekly_load_7d = sum(
        compute_load(session)
        for session in sessions
        if week_7_start <= date.fromisoformat(session["session_date"]) <= today
    )
    weekly_load_28d = (
        sum(
            compute_load(session)
            for session in sessions
            if week_28_start <= date.fromisoformat(session["session_date"]) <= today
        )
        / 4
    )

    next_7d_max_load = recommend_next_7d_max_load(
        weekly_load_7d=weekly_load_7d,
        weekly_load_28d_avg=weekly_load_28d,
        tsb=latest_tsb,
    )
    recommended_daily_max = next_7d_max_load / 7

    load_by_day = defaultdict(float)
    next_7_end = today + timedelta(days=6)
    for session in sessions:
        day = date.fromisoformat(session["session_date"])
        if today <= day <= next_7_end:
            load_by_day[day] += compute_load(session)

    risk_colors = {
        "green": "#C8E6C9",
        "yellow": "#FFF9C4",
        "red": "#FFCDD2",
    }

    overlay_events = []
    for day_offset in range(7):
        day = today + timedelta(days=day_offset)
        daily_load = load_by_day.get(day, 0.0)
        risk = classify_daily_risk(daily_load, recommended_daily_max)
        overlay_events.append(
            {
                "start": day.isoformat(),
                "end": (day + timedelta(days=1)).isoformat(),
                "display": "background",
                "overlap": True,
                "color": risk_colors[risk],
            }
        )

    return overlay_events

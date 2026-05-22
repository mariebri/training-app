from datetime import date, timedelta

from services.coach.injury_prevention import compute_spike_ratio, is_injury_risk
from services.coach.workout_generator import build_workout
from services.coach.workout_library import WORKOUT_LIBRARY
from services.performance_model import (
    compute_ctl_atl,
    compute_load,
    recommend_next_7d_max_load,
)


def analyze_planner_history(sessions):
    history = compute_ctl_atl(sessions)
    latest = history[-1] if history else {"ctl": 50, "atl": 50, "tsb": 0}

    today = date.today()
    week_7_start = today - timedelta(days=6)
    week_28_start = today - timedelta(days=27)

    weekly_load_7d = sum(
        compute_load(s)
        for s in sessions
        if week_7_start <= date.fromisoformat(s["session_date"]) <= today
    )
    weekly_load_28d_total = sum(
        compute_load(s)
        for s in sessions
        if week_28_start <= date.fromisoformat(s["session_date"]) <= today
    )
    weekly_load_28d_avg = weekly_load_28d_total / 4 if weekly_load_28d_total > 0 else 0

    spike_ratio = compute_spike_ratio(weekly_load_7d, weekly_load_28d_avg)
    risk_flag = is_injury_risk(spike_ratio, latest["tsb"])

    state = "balanced"
    if latest["tsb"] > 10:
        state = "fresh"
    elif latest["tsb"] < -10:
        state = "fatigued"

    return {
        "latest": latest,
        "weekly_load_7d": weekly_load_7d,
        "weekly_load_28d_avg": weekly_load_28d_avg,
        "spike_ratio": spike_ratio,
        "risk_flag": risk_flag,
        "state": state,
    }


def pick_base_workouts(goal_focus, state, training_days, risk_flag):
    if risk_flag:
        base = ["recovery_run", "Lett_run", "recovery_run", "Lett_run", "long_run"]
    elif state == "fatigued":
        base = ["recovery_run", "Lett_run", "recovery_run", "Lett_run", "tempo_run"]
    elif goal_focus in ("5 km", "10 km"):
        base = ["intervals", "Lett_run", "tempo_run", "Lett_run", "long_run"]
    elif goal_focus in ("Halvmaraton", "Maraton"):
        base = ["Lett_run", "tempo_run", "Lett_run", "long_run", "Lett_run"]
    else:
        base = ["Lett_run", "intervals", "Lett_run", "tempo_run", "long_run"]

    if training_days <= len(base):
        return base[:training_days]

    extension = ["Lett_run", "recovery_run"]
    idx = 0
    while len(base) < training_days:
        base.append(extension[idx % len(extension)])
        idx += 1
    return base


def workout_defaults(workout_key):
    defaults = {
        "Lett_run": {"duration": 45, "intensity": "Lett"},
        "recovery_run": {"duration": 35, "intensity": "Lett"},
        "tempo_run": {"duration": 55, "intensity": "Moderat"},
        "intervals": {"duration": 60, "intensity": "Hardt"},
        "long_run": {"duration": 90, "intensity": "Moderat"},
    }
    return defaults.get(workout_key, {"duration": 45, "intensity": "Lett"})


def workout_label(workout_key):
    labels = {
        "Lett_run": "Rolig lop",
        "recovery_run": "Restitusjonslop",
        "tempo_run": "Tempolop",
        "intervals": "Intervaller",
        "long_run": "Langtur",
    }
    return labels.get(workout_key, workout_key)


def build_planner_sessions(workouts, weekly_minutes_target, next_7d_load_target):
    sessions_out = []
    base_minutes = sum(workout_defaults(w)["duration"] for w in workouts)
    minute_scale = weekly_minutes_target / base_minutes if base_minutes > 0 else 1.0
    minute_scale = max(0.7, min(1.4, minute_scale))

    for workout_key in workouts:
        default_values = workout_defaults(workout_key)
        sessions_out.append(
            {
                "workout": workout_key,
                "duration_minutes": int(
                    round(default_values["duration"] * minute_scale / 5) * 5
                ),
                "intensity": default_values["intensity"],
            }
        )

    estimated_load = sum(
        compute_load(
            {
                "duration_minutes": session["duration_minutes"],
                "intensity": session["intensity"],
            }
        )
        for session in sessions_out
    )

    if estimated_load > next_7d_load_target and estimated_load > 0:
        downscale = max(0.75, next_7d_load_target / estimated_load)
        for session in sessions_out:
            session["duration_minutes"] = int(
                round(session["duration_minutes"] * downscale / 5) * 5
            )

    final_load = sum(
        compute_load(
            {
                "duration_minutes": session["duration_minutes"],
                "intensity": session["intensity"],
            }
        )
        for session in sessions_out
    )

    return sessions_out, final_load


def build_structured_plan(planned_sessions, training_days):
    days = ["Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag", "Lordag", "Sondag"]
    rest_days = max(0, 7 - training_days)
    rest_positions = set()
    if rest_days > 0:
        spacing = 7 / rest_days
        rest_positions = {int(i * spacing) % 7 for i in range(rest_days)}

    session_idx = 0
    structured_plan = []
    for day_idx, day_name in enumerate(days):
        if day_idx in rest_positions or session_idx >= len(planned_sessions):
            structured_plan.append(
                {
                    "Dag": day_name,
                    "Okt": "Hvile / mobilitet",
                    "Varighet (min)": 0,
                    "Intensitet": "-",
                    "Beskrivelse": "Aktiv hvile, mobilitet eller lett gange",
                }
            )
            continue

        planned = planned_sessions[session_idx]
        session_idx += 1

        workout_info = (
            build_workout(planned["workout"])
            if planned["workout"] in WORKOUT_LIBRARY
            else {
                "description": planned["workout"],
                "session": "",
            }
        )

        structured_plan.append(
            {
                "Dag": day_name,
                "Okt": workout_label(planned["workout"]),
                "Varighet (min)": planned["duration_minutes"],
                "Intensitet": planned["intensity"],
                "Beskrivelse": f"{workout_info['description']} | {workout_info['session']}",
            }
        )

    return structured_plan


def build_planner_output(
    sessions,
    goal_focus,
    training_days,
    weekly_minutes_target,
    goal_aggressiveness,
):
    history_stats = analyze_planner_history(sessions)

    aggr_factor = {"Konservativ": 0.95, "Moderat": 1.0, "Ambisiøs": 1.08}[
        goal_aggressiveness
    ]
    base_next_7d_target = recommend_next_7d_max_load(
        weekly_load_7d=history_stats["weekly_load_7d"],
        weekly_load_28d_avg=history_stats["weekly_load_28d_avg"],
        tsb=history_stats["latest"]["tsb"],
    )
    next_7d_target = base_next_7d_target * aggr_factor

    workouts = pick_base_workouts(
        goal_focus=goal_focus,
        state=history_stats["state"],
        training_days=training_days,
        risk_flag=history_stats["risk_flag"],
    )
    planned_sessions, planned_load = build_planner_sessions(
        workouts,
        weekly_minutes_target=weekly_minutes_target,
        next_7d_load_target=next_7d_target,
    )
    structured_plan = build_structured_plan(planned_sessions, training_days)

    return {
        **history_stats,
        "next_7d_target": next_7d_target,
        "planned_load": planned_load,
        "structured_plan": structured_plan,
    }

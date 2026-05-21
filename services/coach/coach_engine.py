from services.coach.injury_prevention import is_injury_risk
from services.coach.progression import compute_next_week_load


def generate_week_plan(
    ctl, atl, tsb, weekly_load_7d, weekly_load_28d, current_week_number, base_load
):

    spike = weekly_load_7d / max(weekly_load_28d, 1)

    # ======================================
    # SAFETY FIRST (INJURY PREVENTION)
    # ======================================
    if is_injury_risk(spike, tsb):
        return {
            "state": "injury_risk",
            "plan": [
                "recovery_run",
                "rest",
                "recovery_run",
                "Lett_run",
                "long_Lett_run",
            ],
            "message": "Load reduced to prevent injury spike",
        }

    # ======================================
    # PROGRESSION ENGINE
    # ======================================
    next_week_load = compute_next_week_load(base_load, tsb)

    # ======================================
    # TRAINING STATE CLASSIFICATION
    # ======================================

    if tsb > 10:
        state = "fresh"

    elif tsb < -10:
        state = "fatigued"

    else:
        state = "balanced"

    # ======================================
    # PLAN GENERATION
    # ======================================

    if state == "fresh":
        plan = ["intervals", "Lett_run", "tempo_run", "Lett_run", "long_run"]

    elif state == "fatigued":
        plan = ["Lett_run", "recovery_run", "Lett_run", "tempo_run", "long_run"]

    else:
        plan = ["Lett_run", "intervals", "Lett_run", "tempo_run", "long_run"]

    return {
        "state": state,
        "next_week_load": next_week_load,
        "spike_ratio": spike,
        "plan": plan,
    }

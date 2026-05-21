from datetime import datetime
from utils.constants import INTENSITIES


def compute_load(session):
    return session["duration_minutes"] * INTENSITIES[session["intensity"]]["load"]


def compute_ctl_atl(sessions):

    ctl = 50  # initial fitness guess
    atl = 50  # initial fatigue guess

    history = []

    sorted_sessions = sorted(sessions, key=lambda x: x["session_date"])

    for s in sorted_sessions:
        load = compute_load(s)

        # CTL (42-day time constant)
        ctl = ctl + (load - ctl) / 42

        # ATL (7-day time constant)
        atl = atl + (load - atl) / 7

        tsb = ctl - atl

        history.append(
            {
                "date": s["session_date"],
                "load": load,
                "ctl": ctl,
                "atl": atl,
                "tsb": tsb,
            }
        )

    return history

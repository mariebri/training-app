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


def recommend_next_7d_max_load(weekly_load_7d, weekly_load_28d_avg, tsb):
    """Recommend a max load target for the next 7 days from ACWR baseline and freshness."""
    baseline = max(float(weekly_load_28d_avg), 1.0)

    # Base target from freshness (TSB): lower when athlete is carrying fatigue.
    if tsb < -20:
        freshness_factor = 0.9
    elif tsb < -10:
        freshness_factor = 1.0
    elif tsb < 5:
        freshness_factor = 1.1
    else:
        freshness_factor = 1.2

    target = baseline * freshness_factor

    # Keep week-to-week progression conservative.
    if weekly_load_7d > 0:
        progressive_cap = weekly_load_7d * 1.15
        target = min(target, progressive_cap)

    return max(target, 1.0)


def classify_daily_risk(daily_load, recommended_daily_max):
    """Return traffic-light risk label for a single day load."""
    if recommended_daily_max <= 0:
        return "green"

    ratio = daily_load / recommended_daily_max

    if ratio > 1.0:
        return "red"
    if ratio >= 0.8:
        return "yellow"
    return "green"

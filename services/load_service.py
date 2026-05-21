from utils.constants import INTENSITIES
from datetime import datetime, timedelta


def compute_session_load(duration_minutes, intensity):

    return duration_minutes * INTENSITIES[intensity]["load"]


def compute_weekly_load(sessions):

    total = 0

    for s in sessions:
        total += compute_session_load(s["duration_minutes"], s["intensity"])

    return total


def compute_fatigue_index(sessions):

    today = datetime.today()

    acute_cutoff = today - timedelta(days=7)
    chronic_cutoff = today - timedelta(days=28)

    acute = 0
    chronic = 0

    for s in sessions:
        d = datetime.strptime(s["session_date"], "%Y-%m-%d")

        load = compute_session_load(s["duration_minutes"], s["intensity"])

        if d >= acute_cutoff:
            acute += load

        if d >= chronic_cutoff:
            chronic += load

    if chronic == 0:
        return 0

    return acute / chronic

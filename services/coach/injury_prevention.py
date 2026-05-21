def compute_spike_ratio(weekly_load_7d, weekly_load_28d):

    if weekly_load_28d == 0:
        return 1

    return weekly_load_7d / weekly_load_28d


def is_injury_risk(spike_ratio, tsb):

    # main risk conditions
    if spike_ratio > 1.5:
        return True

    if tsb < -25:
        return True

    return False
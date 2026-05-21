def suggest_week_plan(fatigue_ratio, goal="running"):

    # plan = []

    # Recovery needed
    if fatigue_ratio > 1.3:
        return ["Lett run", "Rest", "Lett run", "Cross-training", "Lett run"]

    # Normal training
    if fatigue_ratio < 0.8:
        return ["Intervals", "Lett run", "Tempo run", "Lett run", "Long run"]

    # Balanced zone
    return ["Lett run", "Intervals", "Lett run", "Tempo run", "Long run"]


def adaptive_plan(latest_tsb):

    # plan = []

    # Overreaching risk
    if latest_tsb < -20:
        return ["Rest", "Lett run", "Rest", "Lett run", "Long Lett run"]

    # Good fitness / low fatigue
    if latest_tsb > 10:
        return ["Intervals", "Lett run", "Tempo run", "Lett run", "Long run"]

    # Balanced state
    return ["Lett run", "Intervals", "Lett run", "Tempo run", "Long run"]

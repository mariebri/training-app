def classify_state(ctl, atl, tsb):

    if tsb < -20:
        return "overreached"

    if tsb < -5:
        return "fatigued"

    if tsb > 10:
        return "fresh"

    return "balanced"


def intensity_distribution(state):

    if state == "overreached":
        return {"Lett": 0.9, "Hardt": 0.1}

    if state == "fatigued":
        return {"Lett": 0.7, "Hardt": 0.3}

    if state == "fresh":
        return {"Lett": 0.5, "Hardt": 0.5}

    return {"Lett": 0.6, "Hardt": 0.4}

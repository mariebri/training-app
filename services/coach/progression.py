def compute_next_week_load(current_week_load, tsb):

    # If fatigued → no progression
    if tsb < -15:
        return current_week_load * 0.9  # deload

    # If slightly fatigued → maintain
    if tsb < 0:
        return current_week_load

    # If fresh → progressive overload
    return current_week_load * 1.05
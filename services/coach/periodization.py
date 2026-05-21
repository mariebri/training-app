def should_deload(week_number):

    # classic 3:1 model (3 build weeks, 1 deload)
    return week_number % 4 == 0


def adjust_load_for_cycle(target_load, week_number):

    if should_deload(week_number):
        return target_load * 0.7  # deload week

    return target_load

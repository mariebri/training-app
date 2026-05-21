from services.coach.workout_library import WORKOUT_LIBRARY


def build_workout(workout_key):

    base = WORKOUT_LIBRARY[workout_key]

    return {
        "name": workout_key,
        "type": base["type"],
        "description": base["description"],
        "session": base["structure"],
    }

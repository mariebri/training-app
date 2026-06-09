INTENSITIES = {
    "Lett": {"color": "#4CAF50", "load": 1, "emoji": "🟢"},
    "Moderat": {"color": "#FF9800", "load": 2, "emoji": "🟠"},
    "Hardt": {"color": "#F44336", "load": 3, "emoji": "🔴"},
}

ACTIVITIES = {
    "Løping": {"icon": "🏃", "distance": True, "duration": True, "pace": True},
    "Sykling": {"icon": "🚴", "distance": True, "duration": True, "pace": True},
    "SkiErg": {"icon": "🎿", "distance": False, "duration": True, "pace": False},
    "Ellipse": {"icon": "🏋️", "distance": False, "duration": True, "pace": False},
    "Styrke": {"icon": "💪", "distance": False, "duration": True, "pace": False},
}

TIME_SLOTS = ["🌅 Morgen", "🌆 Ettermiddag"]

SESSION_TYPES = [
    "Intervall",
    "Rolig",
    "Terskel",
    "Styrke",
    "Langtur",
    "Mobilitet",
    "Restitusjon",
    "Annet",
]

SESSION_GOALS = [
    "Bygge aerob base",
    "Restitusjon",
    "VO2",
    "Teknikk",
    "Skadeforebygging",
    "Styrkeutvikling",
    "Annet",
]

SESSION_PRIORITIES = ["Nokkelokt", "Kan flyttes", "Bonusokt"]

BODY_FOCUS_AREAS = [
    "Bein",
    "Overkropp",
    "Core",
    "Kondisjon",
    "Helkropp",
    "Mobilitet",
    "Annet",
]

ENERGY_LEVELS = ["Veldig lav", "Lav", "Normal", "Høy"]

PAIN_LEVELS = ["Ingen", "Mild", "Moderat", "Høy"]

POST_SESSION_FEELINGS = ["Energisk", "Tappet", "Støl", "Motivert", "Nøytral"]

RPE_GUIDE = {
    1: "Svært lett (nesten ingen anstrengelse)",
    2: "Meget lett",
    3: "Lett",
    4: "Moderat lett",
    5: "Moderat",
    6: "Noe krevende",
    7: "Krevende",
    8: "Hardt",
    9: "Svært hardt",
    10: "Maksimal innsats",
}

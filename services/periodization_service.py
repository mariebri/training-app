import pandas as pd
from datetime import datetime


def to_week(date_str):

    date = datetime.strptime(date_str, "%Y-%m-%d")

    return date.isocalendar().week


def compute_weekly_load_df(sessions):

    df = pd.DataFrame(sessions)

    df["week"] = df["session_date"].apply(to_week)

    df["load"] = df.apply(
        lambda x: (
            x["duration_minutes"]
            * (
                1
                if x["intensity"] == "Lett"
                else 2
                if x["intensity"] == "Moderat"
                else 3
            )
        ),
        axis=1,
    )

    weekly = df.groupby("week")["load"].sum().reset_index()

    return weekly

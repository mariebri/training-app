import pandas as pd

from services.coach.injury_prevention import compute_spike_ratio, is_injury_risk
from services.performance_model import (
    compute_ctl_atl,
    compute_load,
    recommend_next_7d_max_load,
)


def badge_for_status(status):
    badges = {
        "green": "🟢 Bra",
        "yellow": "🟡 Følg med",
        "red": "🔴 Risiko",
    }
    return badges.get(status, "🟡 Følg med")


def tsb_status(tsb_value):
    if -10 <= tsb_value <= 10:
        return "green", "Balansert treningsfriskhet"
    if (-20 <= tsb_value < -10) or (10 < tsb_value <= 20):
        return "yellow", "Følg med på balansen mellom belastning og restitusjon"
    return "red", "For sliten eller for fersk til kvalitetsprogresjon"


def atl_status(atl_value, ctl_value):
    ctl_safe = max(float(ctl_value), 1.0)
    fatigue_ratio = float(atl_value) / ctl_safe

    if fatigue_ratio <= 1.1:
        return "green", "Belastning og kapasitet er i god balanse"
    if fatigue_ratio <= 1.3:
        return "yellow", "Belastningen oker raskere enn kapasiteten"
    return "red", "Hoyt belastningspress; reduser treningsbelastning"


def ctl_status(ctl_value, ctl_14d_reference):
    reference = max(float(ctl_14d_reference), 1.0)
    change_pct = ((float(ctl_value) - reference) / reference) * 100

    if -2 <= change_pct <= 12:
        return "green", change_pct, "Formutviklingen er stabil og produktiv"
    if change_pct < -2 or change_pct > 20:
        return "red", change_pct, "Formutviklingen faller eller stiger for raskt"
    return "yellow", change_pct, "Formutviklingen er ok, men bor folges"


def spike_status(spike_value):
    if spike_value <= 1.3:
        return "green"
    if spike_value <= 1.5:
        return "yellow"
    return "red"


def build_recommendations(
    remaining_budget, next_7d_max_load, spike_ratio, tsb, consistency_pct
):
    recommendations = []

    if remaining_budget < 0:
        recommendations.append(
            (
                "red",
                "Reduser neste ukes belastning ved a kutte en kvalitetsokt eller korte ned lange okter.",
            )
        )
    elif remaining_budget < 0.15 * next_7d_max_load:
        recommendations.append(
            (
                "yellow",
                "Du er naer ukens belastningstak. Prioriter rolige okter resten av uken.",
            )
        )

    if spike_ratio > 1.5:
        recommendations.append(
            (
                "red",
                "Belastningsspiken er hoy. Hold okningene minimale og legg inn ekstra restitusjon.",
            )
        )
    elif spike_ratio > 1.3:
        recommendations.append(
            (
                "yellow",
                "Mild belastningsspike oppdaget. Hold progresjonen under 10-15 % neste uke.",
            )
        )

    if tsb < -20:
        recommendations.append(
            (
                "red",
                "TSB er svaert negativ, som indikerer hoy slitasje. Vurder en rolig dag umiddelbart.",
            )
        )
    elif tsb < -10:
        recommendations.append(
            (
                "yellow",
                "TSB indikerer opparbeidet slitasje. Bytt en hard okt med rolig aerob trening.",
            )
        )

    if consistency_pct < 40:
        recommendations.append(
            (
                "yellow",
                "Lav konsistens den siste tiden. Legg til en kort, rolig okt for bedre rytme.",
            )
        )

    if not recommendations:
        recommendations.append(
            (
                "green",
                "Treningsbelastningen er godt balansert. Oppretthold progresjonen og behold en kvalitetsdag for restitusjon.",
            )
        )

    return recommendations


def build_analytics_data(rows):
    sessions = [
        {
            "session_date": r[5],
            "duration_minutes": r[6],
            "intensity": r[3],
            "distance_km": r[7],
            "activity": r[2],
            "title": r[1],
        }
        for r in rows
    ]

    if not sessions:
        return {"has_sessions": False}

    session_df = pd.DataFrame(sessions)
    session_df["session_date"] = pd.to_datetime(
        session_df["session_date"], errors="coerce"
    )
    session_df["duration_minutes"] = pd.to_numeric(
        session_df["duration_minutes"], errors="coerce"
    ).fillna(0)
    session_df["distance_km"] = pd.to_numeric(
        session_df["distance_km"], errors="coerce"
    ).fillna(0)
    session_df = session_df.dropna(subset=["session_date"]).copy()

    session_df["load"] = session_df.apply(
        lambda row: compute_load(
            {
                "duration_minutes": row["duration_minutes"],
                "intensity": row["intensity"],
            }
        ),
        axis=1,
    )

    history = compute_ctl_atl(
        session_df[["session_date", "duration_minutes", "intensity"]].to_dict("records")
    )
    df = pd.DataFrame(history)

    if df.empty:
        return {
            "has_sessions": True,
            "has_history": False,
        }

    df["date"] = pd.to_datetime(df["date"])

    today = pd.Timestamp.today().normalize()
    window_7d_start = today - pd.Timedelta(days=6)
    window_28d_start = today - pd.Timedelta(days=27)

    weekly_load_7d = session_df.loc[
        (session_df["session_date"] >= window_7d_start)
        & (session_df["session_date"] <= today),
        "load",
    ].sum()

    load_28d_total = session_df.loc[
        (session_df["session_date"] >= window_28d_start)
        & (session_df["session_date"] <= today),
        "load",
    ].sum()
    weekly_load_28d = load_28d_total / 4 if load_28d_total > 0 else 0

    running_last_7d = session_df.loc[
        (session_df["session_date"] >= window_7d_start)
        & (session_df["session_date"] <= today)
        & (session_df["activity"] == "Løping")
    ]

    running_km_7d = running_last_7d["distance_km"].sum()
    running_minutes_7d = running_last_7d["duration_minutes"].sum()
    running_load_7d = running_last_7d["load"].sum()

    spike_ratio = compute_spike_ratio(weekly_load_7d, weekly_load_28d)

    latest = df.iloc[-1]
    tsb = float(latest["tsb"])
    ctl = float(latest["ctl"])
    atl = float(latest["atl"])

    risk_flag = is_injury_risk(spike_ratio, tsb)
    next_7d_max_load = recommend_next_7d_max_load(weekly_load_7d, weekly_load_28d, tsb)

    future_7d_end = today + pd.Timedelta(days=6)
    planned_next_7d_load = session_df.loc[
        (session_df["session_date"] >= today)
        & (session_df["session_date"] <= future_7d_end),
        "load",
    ].sum()
    remaining_budget = next_7d_max_load - planned_next_7d_load

    consistency_window_start = today - pd.Timedelta(days=13)
    consistency_days = (
        session_df.loc[
            (session_df["session_date"] >= consistency_window_start)
            & (session_df["session_date"] <= today),
            "session_date",
        ]
        .dt.normalize()
        .nunique()
    )
    consistency_pct = (consistency_days / 14) * 100

    weekly_series = (
        session_df.set_index("session_date")["load"]
        .resample("W-MON")
        .sum()
        .rename("weekly_load")
    )
    weekly_chart_df = weekly_series.reset_index().rename(
        columns={"session_date": "week"}
    )

    weekly_delta_pct = 0.0
    if len(weekly_series) >= 2 and weekly_series.iloc[-2] > 0:
        weekly_delta_pct = (
            (weekly_series.iloc[-1] - weekly_series.iloc[-2]) / weekly_series.iloc[-2]
        ) * 100

    risk_score = 0
    if spike_ratio > 1.5:
        risk_score += 2
    elif spike_ratio > 1.3:
        risk_score += 1

    if tsb < -25:
        risk_score += 2
    elif tsb < -10:
        risk_score += 1

    if weekly_delta_pct > 30:
        risk_score += 1

    if risk_score >= 4:
        risk_level = "Høy"
    elif risk_score >= 2:
        risk_level = "Moderat"
    else:
        risk_level = "Lav"

    ctl_reference_candidates = df.loc[
        df["date"] <= (today - pd.Timedelta(days=14)), "ctl"
    ]
    ctl_reference_14d = (
        ctl_reference_candidates.iloc[-1]
        if not ctl_reference_candidates.empty
        else df.iloc[0]["ctl"]
    )

    tsb_light, tsb_text = tsb_status(tsb)
    atl_light, atl_text = atl_status(atl, ctl)
    ctl_light, ctl_change_pct, ctl_text = ctl_status(ctl, ctl_reference_14d)
    spike_light = spike_status(spike_ratio)

    recommendations = build_recommendations(
        remaining_budget=remaining_budget,
        next_7d_max_load=next_7d_max_load,
        spike_ratio=spike_ratio,
        tsb=tsb,
        consistency_pct=consistency_pct,
    )

    intensity_mix_df = (
        session_df.loc[
            (session_df["session_date"] >= window_28d_start)
            & (session_df["session_date"] <= today)
        ]
        .groupby("intensity", as_index=False)["duration_minutes"]
        .sum()
    )

    key_values_df = pd.DataFrame(
        [
            {
                "Metrikk": "CTL (Kronisk treningsbelastning)",
                "Verdi": f"{ctl:.1f}",
                "Trafikklys": badge_for_status(ctl_light),
                "Tolkning": ctl_text,
            },
            {
                "Metrikk": "ATL (Akutt treningsbelastning)",
                "Verdi": f"{atl:.1f}",
                "Trafikklys": badge_for_status(atl_light),
                "Tolkning": atl_text,
            },
            {
                "Metrikk": "TSB (Treningsbalanse)",
                "Verdi": f"{tsb:.1f}",
                "Trafikklys": badge_for_status(tsb_light),
                "Tolkning": tsb_text,
            },
        ]
    )

    return {
        "has_sessions": True,
        "has_history": True,
        "session_df": session_df,
        "df": df,
        "weekly_chart_df": weekly_chart_df,
        "intensity_mix_df": intensity_mix_df,
        "recommendations": recommendations,
        "key_values_df": key_values_df,
        "window_28d_start": window_28d_start,
        "today": today,
        "weekly_load_7d": weekly_load_7d,
        "weekly_load_28d": weekly_load_28d,
        "weekly_delta_pct": weekly_delta_pct,
        "spike_ratio": spike_ratio,
        "spike_light": spike_light,
        "consistency_pct": consistency_pct,
        "consistency_days": consistency_days,
        "running_km_7d": running_km_7d,
        "running_minutes_7d": running_minutes_7d,
        "running_load_7d": running_load_7d,
        "next_7d_max_load": next_7d_max_load,
        "planned_next_7d_load": planned_next_7d_load,
        "remaining_budget": remaining_budget,
        "ctl": ctl,
        "atl": atl,
        "tsb": tsb,
        "ctl_change_pct": ctl_change_pct,
        "tsb_light": tsb_light,
        "risk_flag": risk_flag,
        "risk_level": risk_level,
    }

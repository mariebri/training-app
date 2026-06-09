import streamlit as st
from utils.navigation import require_login_or_redirect, render_app_sidebar

from services.calendar_service import (
    get_profile,
    save_profile,
    add_template,
    get_templates,
    update_template,
    delete_template,
    get_sidebar_first_name,
)
from services.database import get_user_role, touch_user_activity
from utils.constants import ACTIVITIES, TIME_SLOTS

# Check if user is logged in
require_login_or_redirect()

st.title("Bruker")

touch_user_activity(st.session_state.user_id)
if not st.session_state.get("user_role"):
    st.session_state.user_role = get_user_role(st.session_state.user_id)

if st.session_state.user_id:
    first_name = get_sidebar_first_name(
        st.session_state.user_id, st.session_state.username
    )
    render_app_sidebar(first_name, st.session_state.get("user_role"))

profile = get_profile(st.session_state.user_id) or {}

if "profile_edit_mode" not in st.session_state:
    st.session_state.profile_edit_mode = False
if "show_add_template_form" not in st.session_state:
    st.session_state.show_add_template_form = False
if "editing_template_id" not in st.session_state:
    st.session_state.editing_template_id = None

st.subheader("Personlig informasjon")


def profile_name_parts(current_profile):
    first_name = (current_profile.get("first_name") or "").strip()
    last_name = (current_profile.get("last_name") or "").strip()

    if not first_name and not last_name and current_profile.get("full_name"):
        name_parts = str(current_profile.get("full_name")).strip().split(maxsplit=1)
        first_name = name_parts[0] if name_parts else ""
        last_name = name_parts[1] if len(name_parts) > 1 else ""

    return first_name, last_name


if not st.session_state.profile_edit_mode:
    first_name_value, last_name_value = profile_name_parts(profile)

    name_col1, name_col2 = st.columns(2)
    with name_col1:
        st.text_input(
            "Fornavn",
            value=first_name_value,
            disabled=True,
            key="readonly_first_name",
        )
    with name_col2:
        st.text_input(
            "Etternavn",
            value=last_name_value,
            disabled=True,
            key="readonly_last_name",
        )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.number_input(
            "Alder",
            min_value=0,
            max_value=120,
            value=int(profile.get("age") or 0),
            disabled=True,
            key="readonly_age",
        )
    with col2:
        st.selectbox(
            "Kjønn",
            ["Ukjent", "Kvinne", "Mann", "Annet"],
            index=["Ukjent", "Kvinne", "Mann", "Annet"].index(
                profile.get("sex") or "Ukjent"
            ),
            disabled=True,
            key="readonly_sex",
        )
    with col3:
        st.number_input(
            "Høyde (cm)",
            min_value=0.0,
            max_value=250.0,
            value=float(profile.get("height_cm") or 0.0),
            step=0.5,
            disabled=True,
            key="readonly_height",
        )

    col4, col5, col6 = st.columns(3)
    with col4:
        st.number_input(
            "Vekt (kg)",
            min_value=0.0,
            max_value=300.0,
            value=float(profile.get("weight_kg") or 0.0),
            step=0.1,
            disabled=True,
            key="readonly_weight",
        )
    with col5:
        st.number_input(
            "Hvilepuls",
            min_value=0,
            max_value=250,
            value=int(profile.get("resting_hr") or 0),
            disabled=True,
            key="readonly_resting_hr",
        )
    with col6:
        st.number_input(
            "Makspuls",
            min_value=0,
            max_value=250,
            value=int(profile.get("max_hr") or 0),
            disabled=True,
            key="readonly_max_hr",
        )

    col7, col8 = st.columns(2)
    with col7:
        st.number_input(
            "FTP (watt)",
            min_value=0,
            max_value=1500,
            value=int(profile.get("ftp_watts") or 0),
            disabled=True,
            key="readonly_ftp",
        )
    with col8:
        st.number_input(
            "VO2max",
            min_value=0.0,
            max_value=100.0,
            value=float(profile.get("vo2max") or 0.0),
            step=0.1,
            disabled=True,
            key="readonly_vo2max",
        )

    if st.button("✏️ Endre profil"):
        st.session_state.profile_edit_mode = True
        st.rerun()

else:
    with st.form("profile_form"):
        first_name_value, last_name_value = profile_name_parts(profile)

        name_col1, name_col2 = st.columns(2)
        with name_col1:
            first_name = st.text_input("Fornavn", value=first_name_value)
        with name_col2:
            last_name = st.text_input("Etternavn", value=last_name_value)

        col1, col2, col3 = st.columns(3)
        with col1:
            age = st.number_input(
                "Alder", min_value=0, max_value=120, value=int(profile.get("age") or 0)
            )
        with col2:
            sex = st.selectbox(
                "Kjønn",
                ["Ukjent", "Kvinne", "Mann", "Annet"],
                index=["Ukjent", "Kvinne", "Mann", "Annet"].index(
                    profile.get("sex") or "Ukjent"
                ),
            )
        with col3:
            height_cm = st.number_input(
                "Høyde (cm)",
                min_value=0.0,
                max_value=250.0,
                value=float(profile.get("height_cm") or 0.0),
                step=0.5,
            )

        col4, col5, col6 = st.columns(3)
        with col4:
            weight_kg = st.number_input(
                "Vekt (kg)",
                min_value=0.0,
                max_value=300.0,
                value=float(profile.get("weight_kg") or 0.0),
                step=0.1,
            )
        with col5:
            resting_hr = st.number_input(
                "Hvilepuls",
                min_value=0,
                max_value=250,
                value=int(profile.get("resting_hr") or 0),
            )
        with col6:
            max_hr = st.number_input(
                "Makspuls",
                min_value=0,
                max_value=250,
                value=int(profile.get("max_hr") or 0),
            )

        col7, col8 = st.columns(2)
        with col7:
            ftp_watts = st.number_input(
                "FTP (watt)",
                min_value=0,
                max_value=1500,
                value=int(profile.get("ftp_watts") or 0),
            )
        with col8:
            vo2max = st.number_input(
                "VO2max",
                min_value=0.0,
                max_value=100.0,
                value=float(profile.get("vo2max") or 0.0),
                step=0.1,
            )

        save_col1, save_col2 = st.columns(2)
        with save_col1:
            save_profile_clicked = st.form_submit_button("💾 Lagre profil")
        with save_col2:
            cancel_profile_edit = st.form_submit_button("Avbryt")

        if save_profile_clicked:
            save_profile(
                user_id=st.session_state.user_id,
                first_name=first_name.strip() or None,
                last_name=last_name.strip() or None,
                age=age or None,
                sex=sex,
                height_cm=height_cm or None,
                weight_kg=weight_kg or None,
                resting_hr=resting_hr or None,
                max_hr=max_hr or None,
                ftp_watts=ftp_watts or None,
                vo2max=vo2max or None,
            )
            st.session_state.profile_edit_mode = False
            st.success("Profil lagret")
            st.rerun()

        if cancel_profile_edit:
            st.session_state.profile_edit_mode = False
            st.rerun()

st.divider()
st.subheader("Øktbibliotek")
if not st.session_state.show_add_template_form:
    if st.button("➕ Legg til ny økt i biblioteket"):
        st.session_state.show_add_template_form = True
        st.rerun()
else:
    with st.form("template_form"):
        st.markdown("**Ny bibliotekøkt**")
        template_name = st.text_input("Navn på økt")

        col1, col2, col3 = st.columns(3)
        with col1:
            template_activity = st.selectbox("Aktivitet", list(ACTIVITIES.keys()))
        with col2:
            template_intensity = st.selectbox(
                "Intensitet", ["Lett", "Moderat", "Hardt"]
            )
        with col3:
            template_time_slot = st.selectbox("Tidspunkt", TIME_SLOTS)

        col4, col5 = st.columns(2)
        with col4:
            template_duration = st.number_input(
                "Varighet (minutter)", min_value=0, max_value=1440, value=45, step=5
            )
        with col5:
            template_distance = st.number_input(
                "Distanse (km)", min_value=0.0, max_value=500.0, value=0.0, step=0.5
            )

        template_notes = st.text_area("Notater")
        include_in_calendar = st.toggle(
            "Vis som forhåndsdefinert økt i kalenderen",
            value=True,
            help="Hvis aktivert vil økten vises under 'Forhåndsdefinerte økter' når du legger til ny økt i kalenderen.",
        )

        save_col1, save_col2 = st.columns(2)
        with save_col1:
            save_template_clicked = st.form_submit_button("💾 Lagre økt")
        with save_col2:
            cancel_new_template = st.form_submit_button("Avbryt")

        if save_template_clicked:
            if not template_name.strip():
                st.error("Navn på økt er påkrevd")
            else:
                add_template(
                    user_id=st.session_state.user_id,
                    name=template_name.strip(),
                    activity=template_activity,
                    intensity=template_intensity,
                    time_slot=template_time_slot,
                    duration_minutes=template_duration,
                    distance_km=template_distance,
                    notes=template_notes.strip() or None,
                    include_in_calendar=include_in_calendar,
                )
                st.session_state.show_add_template_form = False
                st.success("Økt lagret i biblioteket")
                st.rerun()

        if cancel_new_template:
            st.session_state.show_add_template_form = False
            st.rerun()

templates = get_templates(st.session_state.user_id)

if not templates:
    st.info("Ingen økter i biblioteket ennå.")
else:
    st.markdown("**Dine økter**")
    for template in templates:
        label = (
            f"{template['name']} | {template['activity']} | {template['intensity']} | "
            f"{template['duration_minutes']} min"
        )
        with st.expander(label, expanded=False):
            st.write(f"**Tidspunkt:** {template['time_slot']}")
            st.write(f"**Distanse:** {template['distance_km']} km")
            st.write(
                "**Synlig i kalenderens forhåndsdefinerte økter:** "
                + ("Ja" if template["include_in_calendar"] else "Nei")
            )
            if template.get("notes"):
                st.info(template["notes"])

            row1_col1, row1_col2 = st.columns(2)
            with row1_col1:
                if st.button("✏️ Endre økt", key=f"edit_template_{template['id']}"):
                    st.session_state.editing_template_id = template["id"]
                    st.rerun()
            with row1_col2:
                if st.button("🗑️ Slett økt", key=f"del_template_{template['id']}"):
                    delete_template(template["id"], st.session_state.user_id)
                    if st.session_state.editing_template_id == template["id"]:
                        st.session_state.editing_template_id = None
                    st.rerun()

            if st.session_state.editing_template_id == template["id"]:
                st.divider()
                with st.form(f"edit_template_form_{template['id']}"):
                    st.markdown("**Endre økt**")
                    edit_name = st.text_input("Navn på økt", value=template["name"])

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        activities = list(ACTIVITIES.keys())
                        activity_index = (
                            activities.index(template["activity"])
                            if template["activity"] in activities
                            else 0
                        )
                        edit_activity = st.selectbox(
                            "Aktivitet", activities, index=activity_index
                        )
                    with col2:
                        intensity_options = ["Lett", "Moderat", "Hardt"]
                        intensity_index = (
                            intensity_options.index(template["intensity"])
                            if template["intensity"] in intensity_options
                            else 0
                        )
                        edit_intensity = st.selectbox(
                            "Intensitet", intensity_options, index=intensity_index
                        )
                    with col3:
                        slot_index = (
                            TIME_SLOTS.index(template["time_slot"])
                            if template["time_slot"] in TIME_SLOTS
                            else 0
                        )
                        edit_time_slot = st.selectbox(
                            "Tidspunkt", TIME_SLOTS, index=slot_index
                        )

                    col4, col5 = st.columns(2)
                    with col4:
                        edit_duration = st.number_input(
                            "Varighet (minutter)",
                            min_value=0,
                            max_value=1440,
                            value=int(template["duration_minutes"] or 0),
                            step=5,
                        )
                    with col5:
                        edit_distance = st.number_input(
                            "Distanse (km)",
                            min_value=0.0,
                            max_value=500.0,
                            value=float(template["distance_km"] or 0.0),
                            step=0.5,
                        )

                    edit_notes = st.text_area(
                        "Notater", value=template.get("notes") or ""
                    )
                    edit_include_in_calendar = st.toggle(
                        "Vis som forhåndsdefinert økt i kalenderen",
                        value=template.get("include_in_calendar", True),
                        key=f"toggle_calendar_{template['id']}",
                    )

                    save_col1, save_col2 = st.columns(2)
                    with save_col1:
                        save_edit_clicked = st.form_submit_button("💾 Lagre endringer")
                    with save_col2:
                        cancel_edit_clicked = st.form_submit_button("Avbryt")

                    if save_edit_clicked:
                        if not edit_name.strip():
                            st.error("Navn på økt er påkrevd")
                        else:
                            update_template(
                                template_id=template["id"],
                                user_id=st.session_state.user_id,
                                name=edit_name.strip(),
                                activity=edit_activity,
                                intensity=edit_intensity,
                                time_slot=edit_time_slot,
                                duration_minutes=edit_duration,
                                distance_km=edit_distance,
                                notes=edit_notes.strip() or None,
                                include_in_calendar=edit_include_in_calendar,
                            )
                            st.session_state.editing_template_id = None
                            st.success("Økten er oppdatert")
                            st.rerun()

                    if cancel_edit_clicked:
                        st.session_state.editing_template_id = None
                        st.rerun()

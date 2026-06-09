import pandas as pd
import streamlit as st
from utils.navigation import require_login_or_redirect, render_app_sidebar

from services.calendar_service import get_sidebar_first_name
from services.database import (
    delete_user_account,
    get_user_role,
    list_admin_audit_events,
    list_all_users_with_metadata,
    restore_user_account,
    touch_user_activity,
    update_user_role,
)

# Check if user is logged in
require_login_or_redirect()

touch_user_activity(st.session_state.user_id)

current_role = st.session_state.get("user_role") or get_user_role(
    st.session_state.user_id
)
st.session_state.user_role = current_role

if current_role != "admin":
    st.error("⛔ Denne siden er kun tilgjengelig for admin")
    st.stop()

st.title("Administrasjon")

first_name = get_sidebar_first_name(st.session_state.user_id, st.session_state.username)
render_app_sidebar(first_name, st.session_state.get("user_role"))
with st.sidebar:
    st.caption("Rolle: Admin")

users = list_all_users_with_metadata(include_deleted=True)

if "admin_confirm_action" not in st.session_state:
    st.session_state.admin_confirm_action = None

st.subheader("Brukeroversikt")

if not users:
    st.info("Ingen brukere funnet")
    st.stop()

overview_rows = []
for user in users:
    full_name = " ".join(
        [part for part in [user.get("first_name"), user.get("last_name")] if part]
    ).strip()
    overview_rows.append(
        {
            "ID": user["id"],
            "E-post": user["email"],
            "Navn": full_name or "-",
            "Rolle": user["role"],
            "Status": "Slettet" if user.get("deleted_at") else "Aktiv",
            "Sist aktiv": user.get("last_active_at") or "-",
            "Opprettet": user.get("created_at") or "-",
        }
    )

users_df = pd.DataFrame(overview_rows)

filter_col1, filter_col2, filter_col3 = st.columns(3)
with filter_col1:
    search_query = st.text_input("Søk (e-post/navn)", key="admin_search_query")
with filter_col2:
    role_filter = st.selectbox(
        "Filtrer rolle",
        ["Alle", "default", "premium", "admin"],
        key="admin_role_filter",
    )
with filter_col3:
    status_filter = st.selectbox(
        "Filtrer status",
        ["Alle", "Aktiv", "Slettet"],
        key="admin_status_filter",
    )

filtered_df = users_df.copy()

if search_query:
    q = search_query.strip().lower()
    filtered_df = filtered_df[
        filtered_df["E-post"].str.lower().str.contains(q)
        | filtered_df["Navn"].str.lower().str.contains(q)
    ]

if role_filter != "Alle":
    filtered_df = filtered_df[filtered_df["Rolle"] == role_filter]

if status_filter != "Alle":
    filtered_df = filtered_df[filtered_df["Status"] == status_filter]

st.dataframe(filtered_df, width="stretch", hide_index=True)
st.caption(f"Viser {len(filtered_df)} av {len(users_df)} brukere")

visible_user_ids = set(filtered_df["ID"].tolist())

st.divider()
st.subheader("Administrer brukere")

for user in users:
    if user["id"] not in visible_user_ids:
        continue
    user_id = user["id"]
    email = user["email"]
    display_name = " ".join(
        [part for part in [user.get("first_name"), user.get("last_name")] if part]
    ).strip()
    header = f"{email} ({display_name or 'Ingen navn'})"

    with st.expander(header):
        is_deleted = bool(user.get("deleted_at"))

        st.write(f"**Bruker-ID:** {user_id}")
        st.write(f"**Status:** {'Slettet' if is_deleted else 'Aktiv'}")
        st.write(f"**Sist aktiv:** {user.get('last_active_at') or '-'}")
        st.write(f"**Opprettet:** {user.get('created_at') or '-'}")
        if user.get("deleted_at"):
            st.write(f"**Slettet:** {user.get('deleted_at')}")

        selected_role = st.selectbox(
            "Rolle",
            ["default", "premium", "admin"],
            index=["default", "premium", "admin"].index(user["role"]),
            key=f"role_select_{user_id}",
            disabled=is_deleted,
        )

        action_col1, action_col2 = st.columns(2)

        with action_col1:
            if st.button("Lagre rolle", key=f"save_role_{user_id}"):
                try:
                    update_user_role(
                        user_id,
                        selected_role,
                        actor_user_id=st.session_state.user_id,
                    )
                    st.success("Rolle oppdatert")
                    if user_id == st.session_state.user_id:
                        st.session_state.user_role = selected_role
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

        with action_col2:
            can_delete = user_id != st.session_state.user_id
            if not is_deleted:
                if st.button(
                    "Slett bruker",
                    key=f"delete_user_{user_id}",
                    disabled=not can_delete,
                ):
                    st.session_state.admin_confirm_action = {
                        "action": "soft_delete",
                        "user_id": user_id,
                        "email": email,
                    }
                    st.rerun()
            else:
                if st.button("Gjenopprett bruker", key=f"restore_user_{user_id}"):
                    st.session_state.admin_confirm_action = {
                        "action": "restore",
                        "user_id": user_id,
                        "email": email,
                    }
                    st.rerun()

        if user_id == st.session_state.user_id:
            st.caption("Du kan ikke slette deg selv")

st.divider()
st.subheader("Audit-logg")

audit_rows = list_admin_audit_events(limit=300)
if not audit_rows:
    st.info("Ingen audit-hendelser ennå")
else:
    audit_table = []
    for event in audit_rows:
        audit_table.append(
            {
                "Tid": event.get("created_at") or "-",
                "Handling": event.get("action") or "-",
                "Utført av": event.get("actor_email")
                or f"ID {event.get('actor_user_id')}",
                "Målbruker": event.get("target_email")
                or f"ID {event.get('target_user_id')}",
                "Fra rolle": event.get("old_role") or "-",
                "Til rolle": event.get("new_role") or "-",
                "Detaljer": event.get("details") or "-",
            }
        )

    audit_df = pd.DataFrame(audit_table)
    st.dataframe(audit_df, width="stretch", hide_index=True)

    csv_content = audit_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Eksporter audit-logg (CSV)",
        data=csv_content,
        file_name="admin_audit_log.csv",
        mime="text/csv",
        key="download_audit_csv",
    )


@st.dialog("Bekreft handling")
def confirm_admin_action_dialog(action: str, user_id: int, email: str):
    if action == "soft_delete":
        st.warning(f"Er du sikker på at du vil slette brukeren {email}?")
        st.caption("Brukeren blir soft deleted og kan gjenopprettes senere.")
    elif action == "restore":
        st.info(f"Er du sikker på at du vil gjenopprette brukeren {email}?")
    else:
        st.error("Ukjent handling")
        st.session_state.admin_confirm_action = None
        st.rerun()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Avbryt", key=f"confirm_cancel_{action}_{user_id}"):
            st.session_state.admin_confirm_action = None
            st.rerun()
    with col2:
        if st.button("Bekreft", key=f"confirm_ok_{action}_{user_id}"):
            try:
                if action == "soft_delete":
                    delete_user_account(user_id, actor_user_id=st.session_state.user_id)
                    st.success("Bruker markert som slettet")
                else:
                    restore_user_account(
                        user_id, actor_user_id=st.session_state.user_id
                    )
                    st.success("Bruker gjenopprettet")
                st.session_state.admin_confirm_action = None
                st.rerun()
            except ValueError as e:
                st.error(str(e))


pending_action = st.session_state.get("admin_confirm_action")
if pending_action:
    confirm_admin_action_dialog(
        pending_action["action"],
        pending_action["user_id"],
        pending_action["email"],
    )

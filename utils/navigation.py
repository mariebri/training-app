import streamlit as st


def logout_and_redirect_to_login():
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.user_role = None
    st.switch_page("1_Kalender.py")


def require_login_or_redirect():
    if not st.session_state.get("user_id"):
        st.switch_page("1_Kalender.py")
        st.stop()


def render_app_sidebar(first_name: str, user_role: str):
    with st.sidebar:
        st.write(f"👋 Hei, **{first_name}**!")

        st.page_link("1_Kalender.py", label="Kalender", icon="📅")
        st.page_link("pages/2_Analyse.py", label="Analyse", icon="📈")
        st.page_link("pages/3_Planlegger.py", label="Planlegger", icon="🗓️")
        st.page_link("pages/4_Bruker.py", label="Bruker", icon="👤")

        if (user_role or "").strip().lower() == "admin":
            st.page_link("pages/5_Admin.py", label="Admin", icon="🛡️")

        st.divider()
        if st.button("🚪 Logg ut", width="stretch"):
            logout_and_redirect_to_login()

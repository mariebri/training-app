import streamlit as st
from services.database import (
    initialize_database,
    login_user,
    register_user,
)
from services.calendar_service import get_sidebar_first_name

st.set_page_config(page_title="Treningsplanlegger", layout="wide")

initialize_database()

# Initialize session state
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None

# If user is logged in, show the main content
if st.session_state.user_id:
    with st.sidebar:
        first_name = get_sidebar_first_name(
            st.session_state.user_id, st.session_state.username
        )
        st.write(f"👋 Hei, **{first_name}**!")
        if st.button("🚪 Logg ut"):
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()

    st.title("🏋️ Treningsplanlegger")
    st.write("Velkommen til din personlige treningskalender!")
else:
    # Show login/register page
    st.title("🏋️ Treningsplanlegger")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔓 Logg inn")
        login_username = st.text_input("Brukernavn", key="login_username")
        login_password = st.text_input("Passord", type="password", key="login_password")

        if st.button("Logg inn"):
            try:
                user_id = login_user(login_username, login_password)
                st.session_state.user_id = user_id
                st.session_state.username = login_username
                st.success(f"Velkommen tilbake, {login_username}!")
                st.rerun()
            except ValueError as e:
                st.error(str(e))

    with col2:
        st.subheader("✍️ Registrer")
        reg_username = st.text_input("Nytt brukernavn", key="reg_username")
        reg_password = st.text_input(
            "Nytt passord", type="password", key="reg_password"
        )
        reg_password_confirm = st.text_input(
            "Bekreft passord", type="password", key="reg_password_confirm"
        )

        if st.button("Registrer"):
            if not reg_username or not reg_password:
                st.error("Brukernavn og passord er påkrevd")
            elif reg_password != reg_password_confirm:
                st.error("Passordene er ikke like")
            elif len(reg_password) < 6:
                st.error("Passordet må være minst 6 tegn")
            else:
                try:
                    user_id = register_user(reg_username, reg_password)
                    st.session_state.user_id = user_id
                    st.session_state.username = reg_username
                    st.success(f"Velkommen, {reg_username}! Registrering vellykket!")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

    st.divider()
    st.info(
        "📝 **Demokonto**: Bruk brukernavn `demo` og passord `demo123` for å teste appen"
    )

import streamlit as st
from services.database import (
    initialize_database,
    login_user,
    register_user,
    get_username_by_id,
)

st.set_page_config(page_title="Training Planner", layout="wide")

initialize_database()

# Initialize session state
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None

# If user is logged in, show the main content
if st.session_state.user_id:
    with st.sidebar:
        st.write(f"👤 Logged in as: **{st.session_state.username}**")
        if st.button("🚪 Logout"):
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()

    st.title("🏋️ Training Planner")
    st.write("Welcome to your personal training calendar!")
else:
    # Show login/register page
    st.title("🏋️ Training Planner")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔓 Login")
        login_username = st.text_input("Username", key="login_username")
        login_password = st.text_input(
            "Password", type="password", key="login_password"
        )

        if st.button("Login"):
            try:
                user_id = login_user(login_username, login_password)
                st.session_state.user_id = user_id
                st.session_state.username = login_username
                st.success(f"Welcome back, {login_username}!")
                st.rerun()
            except ValueError as e:
                st.error(str(e))

    with col2:
        st.subheader("✍️ Register")
        reg_username = st.text_input("New Username", key="reg_username")
        reg_password = st.text_input(
            "New Password", type="password", key="reg_password"
        )
        reg_password_confirm = st.text_input(
            "Confirm Password", type="password", key="reg_password_confirm"
        )

        if st.button("Register"):
            if not reg_username or not reg_password:
                st.error("Username and password are required")
            elif reg_password != reg_password_confirm:
                st.error("Passwords do not match")
            elif len(reg_password) < 6:
                st.error("Password must be at least 6 characters")
            else:
                try:
                    user_id = register_user(reg_username, reg_password)
                    st.session_state.user_id = user_id
                    st.session_state.username = reg_username
                    st.success(f"Welcome, {reg_username}! Registration successful!")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

    st.divider()
    st.info(
        "📝 **Demo Account**: Use username `demo` and password `demo123` to test the app"
    )

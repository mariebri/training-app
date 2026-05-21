import streamlit as st
from services.database import initialize_database

st.set_page_config(page_title="Training Planner", layout="wide")

initialize_database()

st.title("Training Planner")

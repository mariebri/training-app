# utils/ui_styles.py

import streamlit as st


def inject_calendar_styles():
    st.markdown(
        """
        <style>
        .fc-event {
            cursor: pointer;
            transition: transform 0.08s ease, box-shadow 0.08s ease;
        }

        .fc-event:hover {
            transform: scale(1.01);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10;
        }

        .fc-daygrid-day {
            transition: background-color 0.15s ease;
        }

        .fc-daygrid-day:hover {
            background-color: rgba(0, 0, 0, 0.03);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

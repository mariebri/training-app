import sqlite3
from pathlib import Path

DB_PATH = Path("data/training.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


def initialize_database():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS training_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            activity TEXT NOT NULL,
            intensity TEXT NOT NULL,
            time_slot TEXT NOT NULL,
            session_date TEXT NOT NULL,
            duration_minutes INTEGER,
            distance_km REAL,
            notes TEXT
        )
        """
    )

    conn.commit()
    conn.close()


def update_training_session(
    session_id,
    title,
    activity,
    intensity,
    time_slot,
    session_date,
    duration_minutes,
    distance_km,
    notes,
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE training_sessions
        SET
            title = ?,
            activity = ?,
            intensity = ?,
            time_slot = ?,
            session_date = ?,
            duration_minutes = ?,
            distance_km = ?,
            notes = ?
        WHERE id = ?
        """,
        (
            title,
            activity,
            intensity,
            time_slot,
            session_date,
            duration_minutes,
            distance_km,
            notes,
            session_id,
        ),
    )

    conn.commit()
    conn.close()


def delete_training_session(session_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM training_sessions
        WHERE id = ?
        """,
        (session_id,),
    )

    conn.commit()
    conn.close()

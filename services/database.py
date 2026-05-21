import sqlite3
from pathlib import Path
import bcrypt

DB_PATH = Path("data/training.db")
DEFAULT_USER = "demo"


def _hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def _verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its bcrypt hash."""
    return bcrypt.checkpw(password.encode(), hashed.encode())


def get_connection():
    return sqlite3.connect(DB_PATH)


def initialize_database():

    conn = get_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    
    # Check if old table needs migration
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='training_sessions'")
    if cursor.fetchone():
        cursor.execute("PRAGMA table_info(training_sessions)")
        columns = {row[1] for row in cursor.fetchall()}
        if "user_id" not in columns:
            try:
                try:
                    register_user(DEFAULT_USER, "demo123")
                except ValueError:
                    pass
                user_id = get_user_id_by_username(DEFAULT_USER)
                cursor.execute("""
                    CREATE TABLE training_sessions_new (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        activity TEXT NOT NULL,
                        intensity TEXT NOT NULL,
                        time_slot TEXT NOT NULL,
                        session_date TEXT NOT NULL,
                        duration_minutes INTEGER,
                        distance_km REAL,
                        notes TEXT,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)
                cursor.execute("""
                    INSERT INTO training_sessions_new
                    SELECT id, ?, title, activity, intensity, time_slot, session_date, duration_minutes, distance_km, notes
                    FROM training_sessions
                """, (user_id,))
                cursor.execute("DROP TABLE training_sessions")
                cursor.execute("ALTER TABLE training_sessions_new RENAME TO training_sessions")
            except Exception as e:
                print(f"Migration error: {e}")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS training_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
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


def register_user(username: str, password: str) -> int:
    """Register a new user. Returns user_id."""
    conn = get_connection()
    cursor = conn.cursor()
    password_hash = _hash_password(password)
    try:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError(f"Username '{username}' already exists")


def login_user(username: str, password: str) -> int:
    """Authenticate a user. Returns user_id if successful."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise ValueError("Invalid username or password")
    user_id, password_hash = row
    if not _verify_password(password, password_hash):
        raise ValueError("Invalid username or password")
    return user_id


def get_user_id_by_username(username: str) -> int:
    """Get user_id by username."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise ValueError(f"User '{username}' not found")
    return row[0]


def get_username_by_id(user_id: int) -> str:
    """Get username by user_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise ValueError(f"User ID {user_id} not found")
    return row[0]


def add_training_session_db(user_id, title, activity, intensity, time_slot, session_date, duration_minutes, distance_km, notes):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO training_sessions (user_id, title, activity, intensity, time_slot, session_date, duration_minutes, distance_km, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, title, activity, intensity, time_slot, session_date, duration_minutes, distance_km, notes))
    conn.commit()
    conn.close()


def get_all_sessions_for_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, activity, intensity, time_slot, session_date, duration_minutes, distance_km, notes
        FROM training_sessions WHERE user_id = ? ORDER BY session_date DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows


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

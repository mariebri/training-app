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


def _ensure_user_profiles_schema(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            full_name TEXT,
            age INTEGER,
            sex TEXT,
            height_cm REAL,
            weight_kg REAL,
            resting_hr INTEGER,
            max_hr INTEGER,
            ftp_watts INTEGER,
            vo2max REAL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )

    cursor.execute("PRAGMA table_info(user_profiles)")
    profile_columns = {row[1] for row in cursor.fetchall()}
    if "first_name" not in profile_columns:
        cursor.execute("ALTER TABLE user_profiles ADD COLUMN first_name TEXT")
    if "last_name" not in profile_columns:
        cursor.execute("ALTER TABLE user_profiles ADD COLUMN last_name TEXT")


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

    _ensure_user_profiles_schema(cursor)

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS predefined_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            activity TEXT NOT NULL,
            intensity TEXT NOT NULL,
            time_slot TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL,
            distance_km REAL,
            notes TEXT,
            include_in_calendar INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )

    # Backward-compatible migration for older databases.
    cursor.execute("PRAGMA table_info(predefined_sessions)")
    predefined_columns = {row[1] for row in cursor.fetchall()}
    if "include_in_calendar" not in predefined_columns:
        cursor.execute(
            "ALTER TABLE predefined_sessions ADD COLUMN include_in_calendar INTEGER NOT NULL DEFAULT 1"
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
        raise ValueError(f"Brukernavnet '{username}' finnes allerede")


def login_user(username: str, password: str) -> int:
    """Authenticate a user. Returns user_id if successful."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise ValueError("Ugyldig brukernavn eller passord")
    user_id, password_hash = row
    if not _verify_password(password, password_hash):
        raise ValueError("Ugyldig brukernavn eller passord")
    return user_id


def get_user_id_by_username(username: str) -> int:
    """Get user_id by username."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise ValueError(f"Fant ikke bruker '{username}'")
    return row[0]


def get_username_by_id(user_id: int) -> str:
    """Get username by user_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise ValueError(f"Fant ikke bruker-ID {user_id}")
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


def upsert_user_profile(
    user_id,
    first_name,
    last_name,
    age,
    sex,
    height_cm,
    weight_kg,
    resting_hr,
    max_hr,
    ftp_watts,
    vo2max,
):
    conn = get_connection()
    cursor = conn.cursor()
    _ensure_user_profiles_schema(cursor)

    first_name_clean = (first_name or "").strip() or None
    last_name_clean = (last_name or "").strip() or None
    full_name_legacy = " ".join(
        [part for part in [first_name_clean, last_name_clean] if part]
    )
    full_name_legacy = full_name_legacy or None

    cursor.execute(
        """
        INSERT INTO user_profiles (
            user_id,
            first_name,
            last_name,
            full_name,
            age,
            sex,
            height_cm,
            weight_kg,
            resting_hr,
            max_hr,
            ftp_watts,
            vo2max,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            first_name = excluded.first_name,
            last_name = excluded.last_name,
            full_name = excluded.full_name,
            age = excluded.age,
            sex = excluded.sex,
            height_cm = excluded.height_cm,
            weight_kg = excluded.weight_kg,
            resting_hr = excluded.resting_hr,
            max_hr = excluded.max_hr,
            ftp_watts = excluded.ftp_watts,
            vo2max = excluded.vo2max,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            user_id,
            first_name_clean,
            last_name_clean,
            full_name_legacy,
            age,
            sex,
            height_cm,
            weight_kg,
            resting_hr,
            max_hr,
            ftp_watts,
            vo2max,
        ),
    )

    conn.commit()
    conn.close()


def get_user_profile(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    _ensure_user_profiles_schema(cursor)

    cursor.execute(
        """
        SELECT
            user_id,
            first_name,
            last_name,
            full_name,
            age,
            sex,
            height_cm,
            weight_kg,
            resting_hr,
            max_hr,
            ftp_watts,
            vo2max,
            updated_at
        FROM user_profiles
        WHERE user_id = ?
        """,
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "user_id": row[0],
        "first_name": row[1],
        "last_name": row[2],
        "full_name": row[3],
        "age": row[4],
        "sex": row[5],
        "height_cm": row[6],
        "weight_kg": row[7],
        "resting_hr": row[8],
        "max_hr": row[9],
        "ftp_watts": row[10],
        "vo2max": row[11],
        "updated_at": row[12],
    }


def add_predefined_session(
    user_id,
    name,
    activity,
    intensity,
    time_slot,
    duration_minutes,
    distance_km,
    notes,
    include_in_calendar,
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO predefined_sessions (
            user_id,
            name,
            activity,
            intensity,
            time_slot,
            duration_minutes,
            distance_km,
            notes,
            include_in_calendar
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            name,
            activity,
            intensity,
            time_slot,
            duration_minutes,
            distance_km,
            notes,
            1 if include_in_calendar else 0,
        ),
    )

    conn.commit()
    conn.close()


def get_predefined_sessions(user_id, include_in_calendar=None):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            id,
            user_id,
            name,
            activity,
            intensity,
            time_slot,
            duration_minutes,
            distance_km,
            notes,
            include_in_calendar
        FROM predefined_sessions
        WHERE user_id = ?
    """
    params = [user_id]
    if include_in_calendar is not None:
        query += " AND include_in_calendar = ?"
        params.append(1 if include_in_calendar else 0)

    query += " ORDER BY name ASC"
    cursor.execute(query, tuple(params))

    rows = cursor.fetchall()
    conn.close()
    return rows


def delete_predefined_session(session_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM predefined_sessions
        WHERE id = ? AND user_id = ?
        """,
        (session_id, user_id),
    )

    conn.commit()
    conn.close()


def update_predefined_session(
    session_id,
    user_id,
    name,
    activity,
    intensity,
    time_slot,
    duration_minutes,
    distance_km,
    notes,
    include_in_calendar,
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE predefined_sessions
        SET
            name = ?,
            activity = ?,
            intensity = ?,
            time_slot = ?,
            duration_minutes = ?,
            distance_km = ?,
            notes = ?,
            include_in_calendar = ?
        WHERE id = ? AND user_id = ?
        """,
        (
            name,
            activity,
            intensity,
            time_slot,
            duration_minutes,
            distance_km,
            notes,
            1 if include_in_calendar else 0,
            session_id,
            user_id,
        ),
    )

    conn.commit()
    conn.close()

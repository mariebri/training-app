import sqlite3
from pathlib import Path
import bcrypt
import secrets
import string

DB_PATH = Path("data/training.db")
DEFAULT_USER = "demo"
DEFAULT_ROLE = "default"
VALID_USER_ROLES = {"default", "premium", "admin"}


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


def _ensure_users_schema(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'default',
            last_active_at TIMESTAMP,
            deleted_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute("PRAGMA table_info(users)")
    users_columns = {row[1] for row in cursor.fetchall()}

    if "role" not in users_columns:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'default'"
        )

    if "last_active_at" not in users_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN last_active_at TIMESTAMP")

    if "deleted_at" not in users_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP")

    cursor.execute(
        "UPDATE users SET role = ? WHERE role IS NULL OR TRIM(role) = ''",
        (DEFAULT_ROLE,),
    )

    cursor.execute(
        """
        UPDATE users
        SET role = 'admin'
                WHERE (LOWER(username) = 'marie' OR LOWER(username) LIKE 'marie@%')
                    AND role = 'default'
        """
    )


def _ensure_admin_audit_log_schema(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS admin_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor_user_id INTEGER,
            target_user_id INTEGER,
            action TEXT NOT NULL,
            old_role TEXT,
            new_role TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (actor_user_id) REFERENCES users(id),
            FOREIGN KEY (target_user_id) REFERENCES users(id)
        )
        """
    )


def _ensure_training_sessions_schema(cursor):
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
            notes TEXT,
            session_type TEXT,
            session_goal TEXT,
            planned_structure TEXT,
            priority TEXT,
            body_focus TEXT,
            is_completed INTEGER NOT NULL DEFAULT 0,
            rpe INTEGER,
            energy_level TEXT,
            pain_level TEXT,
            pain_location TEXT,
            diary_comment TEXT,
            actual_duration_minutes INTEGER,
            actual_intensity TEXT,
            actual_distance_km REAL,
            post_feeling TEXT
        )
        """
    )

    cursor.execute("PRAGMA table_info(training_sessions)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    required_columns = {
        "session_type": "TEXT",
        "session_goal": "TEXT",
        "planned_structure": "TEXT",
        "priority": "TEXT",
        "body_focus": "TEXT",
        "is_completed": "INTEGER NOT NULL DEFAULT 0",
        "rpe": "INTEGER",
        "energy_level": "TEXT",
        "pain_level": "TEXT",
        "pain_location": "TEXT",
        "diary_comment": "TEXT",
        "actual_duration_minutes": "INTEGER",
        "actual_intensity": "TEXT",
        "actual_distance_km": "REAL",
        "post_feeling": "TEXT",
    }
    for column, sql_type in required_columns.items():
        if column not in existing_columns:
            cursor.execute(f"ALTER TABLE training_sessions ADD COLUMN {column} {sql_type}")


def initialize_database():

    conn = get_connection()
    cursor = conn.cursor()
    
    _ensure_users_schema(cursor)
    
    # Check if old table needs migration
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='training_sessions'")
    if cursor.fetchone():
        cursor.execute("PRAGMA table_info(training_sessions)")
        columns = {row[1] for row in cursor.fetchall()}
        if "user_id" not in columns:
            try:
                try:
                    register_user(DEFAULT_USER, "demo123", "Demo")
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

    _ensure_training_sessions_schema(cursor)

    _ensure_user_profiles_schema(cursor)

    _ensure_admin_audit_log_schema(cursor)

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


def register_user(
    email: str,
    password: str,
    first_name: str = None,
    last_name: str = None,
    age: int = None,
    sex: str = None,
    height_cm: float = None,
    weight_kg: float = None,
) -> int:
    """Register a new user with email + password. Returns user_id."""
    conn = get_connection()
    cursor = conn.cursor()
    password_hash = _hash_password(password)

    clean_email = (email or "").strip().lower()
    clean_first_name = (first_name or "").strip()
    clean_last_name = (last_name or "").strip() or None

    if not clean_email:
        conn.close()
        raise ValueError("E-post er påkrevd")
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (clean_email, password_hash, DEFAULT_ROLE),
        )
        conn.commit()
        user_id = cursor.lastrowid

        upsert_user_profile(
            user_id=user_id,
            first_name=clean_first_name,
            last_name=clean_last_name,
            age=age,
            sex=sex,
            height_cm=height_cm,
            weight_kg=weight_kg,
            resting_hr=None,
            max_hr=None,
            ftp_watts=None,
            vo2max=None,
        )

        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError(f"E-postadressen '{clean_email}' finnes allerede")


def login_user(email: str, password: str) -> int:
    """Authenticate a user by email. Returns user_id if successful."""
    conn = get_connection()
    cursor = conn.cursor()
    clean_email = (email or "").strip().lower()
    cursor.execute(
        "SELECT id, password_hash FROM users WHERE username = ? AND deleted_at IS NULL",
        (clean_email,),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise ValueError("Ugyldig e-post eller passord")
    user_id, password_hash = row
    if not _verify_password(password, password_hash):
        raise ValueError("Ugyldig e-post eller passord")
    touch_user_activity(user_id)
    return user_id


def get_user_role(user_id: int) -> str:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE id = ? AND deleted_at IS NULL", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise ValueError(f"Fant ikke bruker-ID {user_id}")
    role = (row[0] or DEFAULT_ROLE).strip().lower()
    return role if role in VALID_USER_ROLES else DEFAULT_ROLE


def touch_user_activity(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET last_active_at = CURRENT_TIMESTAMP WHERE id = ? AND deleted_at IS NULL",
        (user_id,),
    )
    conn.commit()
    conn.close()


def list_all_users_with_metadata(include_deleted: bool = True):
    conn = get_connection()
    cursor = conn.cursor()
    _ensure_users_schema(cursor)
    _ensure_user_profiles_schema(cursor)

    query = """
        SELECT
            u.id,
            u.username,
            u.role,
            u.created_at,
            u.last_active_at,
            u.deleted_at,
            p.first_name,
            p.last_name
        FROM users u
        LEFT JOIN user_profiles p ON p.user_id = u.id
    """
    if not include_deleted:
        query += " WHERE u.deleted_at IS NULL"
    query += " ORDER BY u.id ASC"

    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    users = []
    for row in rows:
        role = (row[2] or DEFAULT_ROLE).strip().lower()
        if role not in VALID_USER_ROLES:
            role = DEFAULT_ROLE
        users.append(
            {
                "id": row[0],
                "email": row[1],
                "role": role,
                "created_at": row[3],
                "last_active_at": row[4],
                "deleted_at": row[5],
                "first_name": row[6],
                "last_name": row[7],
            }
        )
    return users


def _insert_admin_audit_event(
    actor_user_id: int,
    target_user_id: int,
    action: str,
    old_role: str = None,
    new_role: str = None,
    details: str = None,
):
    conn = get_connection()
    cursor = conn.cursor()
    _ensure_admin_audit_log_schema(cursor)
    cursor.execute(
        """
        INSERT INTO admin_audit_log (actor_user_id, target_user_id, action, old_role, new_role, details)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (actor_user_id, target_user_id, action, old_role, new_role, details),
    )
    conn.commit()
    conn.close()


def update_user_role(user_id: int, role: str, actor_user_id: int = None):
    clean_role = (role or "").strip().lower()
    if clean_role not in VALID_USER_ROLES:
        raise ValueError("Ugyldig rolle")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT role, deleted_at FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError("Fant ikke bruker")
    if row[1] is not None:
        conn.close()
        raise ValueError("Kan ikke endre rolle for slettet bruker")

    old_role = (row[0] or DEFAULT_ROLE).strip().lower()
    if old_role not in VALID_USER_ROLES:
        old_role = DEFAULT_ROLE

    cursor.execute("UPDATE users SET role = ? WHERE id = ?", (clean_role, user_id))
    conn.commit()
    conn.close()

    if old_role != clean_role:
        _insert_admin_audit_event(
            actor_user_id=actor_user_id,
            target_user_id=user_id,
            action="role_change",
            old_role=old_role,
            new_role=clean_role,
        )


def delete_user_account(user_id: int, actor_user_id: int = None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT deleted_at FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError("Fant ikke bruker")
    if row[0] is not None:
        conn.close()
        raise ValueError("Brukeren er allerede slettet")

    cursor.execute(
        "UPDATE users SET deleted_at = CURRENT_TIMESTAMP WHERE id = ?",
        (user_id,),
    )

    conn.commit()
    conn.close()

    _insert_admin_audit_event(
        actor_user_id=actor_user_id,
        target_user_id=user_id,
        action="soft_delete",
    )


def restore_user_account(user_id: int, actor_user_id: int = None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT deleted_at FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError("Fant ikke bruker")
    if row[0] is None:
        conn.close()
        raise ValueError("Brukeren er ikke slettet")

    cursor.execute("UPDATE users SET deleted_at = NULL WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    _insert_admin_audit_event(
        actor_user_id=actor_user_id,
        target_user_id=user_id,
        action="restore",
    )


def list_admin_audit_events(limit: int = 200):
    row_limit = max(1, min(limit, 1000))
    conn = get_connection()
    cursor = conn.cursor()
    _ensure_admin_audit_log_schema(cursor)
    cursor.execute(
        """
        SELECT
            l.id,
            l.created_at,
            l.action,
            l.actor_user_id,
            actor.username,
            l.target_user_id,
            target.username,
            l.old_role,
            l.new_role,
            l.details
        FROM admin_audit_log l
        LEFT JOIN users actor ON actor.id = l.actor_user_id
        LEFT JOIN users target ON target.id = l.target_user_id
        ORDER BY l.id DESC
        LIMIT ?
        """,
        (row_limit,),
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "created_at": row[1],
            "action": row[2],
            "actor_user_id": row[3],
            "actor_email": row[4],
            "target_user_id": row[5],
            "target_email": row[6],
            "old_role": row[7],
            "new_role": row[8],
            "details": row[9],
        }
        for row in rows
    ]


def user_exists_for_email(email: str) -> bool:
    """Return True if a user with this email exists."""
    clean_email = (email or "").strip().lower()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM users WHERE username = ? AND deleted_at IS NULL",
        (clean_email,),
    )
    row = cursor.fetchone()
    conn.close()
    return bool(row)


def _generate_temporary_password(length: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_temporary_password(length: int = 10) -> str:
    """Create a random temporary password for reset flows."""
    return _generate_temporary_password(length)


def reset_password_for_email(email: str, temporary_password: str = None) -> str:
    """Set and return a temporary password for the user with this email."""
    clean_email = (email or "").strip().lower()
    if not clean_email:
        raise ValueError("E-post er påkrevd")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (clean_email,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise ValueError("Fant ingen bruker med denne e-postadressen")

    temp_password = temporary_password or _generate_temporary_password()
    password_hash = _hash_password(temp_password)

    cursor.execute(
        "UPDATE users SET password_hash = ? WHERE username = ?",
        (password_hash, clean_email),
    )
    conn.commit()
    conn.close()

    return temp_password


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


def add_training_session_db(
    user_id,
    title,
    activity,
    intensity,
    time_slot,
    session_date,
    duration_minutes,
    distance_km,
    notes,
    session_type=None,
    session_goal=None,
    planned_structure=None,
    priority=None,
    body_focus=None,
    is_completed=0,
    rpe=None,
    energy_level=None,
    pain_level=None,
    pain_location=None,
    diary_comment=None,
    actual_duration_minutes=None,
    actual_intensity=None,
    actual_distance_km=None,
    post_feeling=None,
):
    conn = get_connection()
    cursor = conn.cursor()
    _ensure_training_sessions_schema(cursor)
    cursor.execute("""
        INSERT INTO training_sessions (
            user_id,
            title,
            activity,
            intensity,
            time_slot,
            session_date,
            duration_minutes,
            distance_km,
            notes,
            session_type,
            session_goal,
            planned_structure,
            priority,
            body_focus,
            is_completed,
            rpe,
            energy_level,
            pain_level,
            pain_location,
            diary_comment,
            actual_duration_minutes,
            actual_intensity,
            actual_distance_km,
            post_feeling
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        title,
        activity,
        intensity,
        time_slot,
        session_date,
        duration_minutes,
        distance_km,
        notes,
        session_type,
        session_goal,
        planned_structure,
        priority,
        body_focus,
        1 if is_completed else 0,
        rpe,
        energy_level,
        pain_level,
        pain_location,
        diary_comment,
        actual_duration_minutes,
        actual_intensity,
        actual_distance_km,
        post_feeling,
    ))
    conn.commit()
    conn.close()


def get_all_sessions_for_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    _ensure_training_sessions_schema(cursor)
    cursor.execute("""
        SELECT
            id,
            title,
            activity,
            intensity,
            time_slot,
            session_date,
            duration_minutes,
            distance_km,
            notes,
            session_type,
            session_goal,
            planned_structure,
            priority,
            body_focus,
            is_completed,
            rpe,
            energy_level,
            pain_level,
            pain_location,
            diary_comment,
            actual_duration_minutes,
            actual_intensity,
            actual_distance_km,
            post_feeling
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
    session_type=None,
    session_goal=None,
    planned_structure=None,
    priority=None,
    body_focus=None,
    is_completed=None,
    rpe=None,
    energy_level=None,
    pain_level=None,
    pain_location=None,
    diary_comment=None,
    actual_duration_minutes=None,
    actual_intensity=None,
    actual_distance_km=None,
    post_feeling=None,
):

    conn = get_connection()
    cursor = conn.cursor()
    _ensure_training_sessions_schema(cursor)

    is_completed_db = None
    if is_completed is not None:
        is_completed_db = 1 if is_completed else 0

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
            notes = ?,
            session_type = COALESCE(?, session_type),
            session_goal = COALESCE(?, session_goal),
            planned_structure = COALESCE(?, planned_structure),
            priority = COALESCE(?, priority),
            body_focus = COALESCE(?, body_focus),
            is_completed = COALESCE(?, is_completed),
            rpe = COALESCE(?, rpe),
            energy_level = COALESCE(?, energy_level),
            pain_level = COALESCE(?, pain_level),
            pain_location = COALESCE(?, pain_location),
            diary_comment = COALESCE(?, diary_comment),
            actual_duration_minutes = COALESCE(?, actual_duration_minutes),
            actual_intensity = COALESCE(?, actual_intensity),
            actual_distance_km = COALESCE(?, actual_distance_km),
            post_feeling = COALESCE(?, post_feeling)
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
            session_type,
            session_goal,
            planned_structure,
            priority,
            body_focus,
            is_completed_db,
            rpe,
            energy_level,
            pain_level,
            pain_location,
            diary_comment,
            actual_duration_minutes,
            actual_intensity,
            actual_distance_km,
            post_feeling,
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

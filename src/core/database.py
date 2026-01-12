"""
Database layer for learn_flow - SQLite with CRUD operations
"""
import sqlite3
import hashlib
import json
import re
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, Dict, List, Any
from pathlib import Path

# Database path - always relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_NAME = str(PROJECT_ROOT / "database" / "learnflow.db")
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize database schema"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                tokens_used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create paths table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paths (
                id TEXT PRIMARY KEY,
                user_id INTEGER,
                current_job_title TEXT,
                current_description TEXT,
                current_seniority TEXT,
                target_job_title TEXT,
                target_description TEXT,
                target_seniority TEXT,
                target_company TEXT,
                target_industry TEXT,
                topics JSON,
                global_readiness REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # Create user_skills table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                topic_id TEXT,
                mastery_percent INTEGER,
                last_completed TIMESTAMP,
                modules_complete TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # Phase 3.2: Create user_topic_modules table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_topic_modules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                path_id TEXT NOT NULL,
                topic_id TEXT NOT NULL,
                module_id INTEGER NOT NULL,
                mastery_bonus INTEGER DEFAULT 0,
                completed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, path_id, topic_id, module_id)
            )
        """)

        # Phase 3.2: Create user_answers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                path_id TEXT NOT NULL,
                topic_id TEXT NOT NULL,
                module_id INTEGER NOT NULL,
                question_id TEXT NOT NULL,
                user_answer TEXT NOT NULL,
                is_correct BOOLEAN NOT NULL,
                attempted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_modules
            ON user_topic_modules(user_id, path_id, topic_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_answers
            ON user_answers(user_id, path_id, topic_id, module_id)
        """)


def hash_password(password: str) -> str:
    """Hash password using SHA256 (Phase 1 only - use bcrypt in production)"""
    if not password:
        raise ValueError("Password cannot be empty")
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters")
    return hashlib.sha256(password.encode()).hexdigest()


# User CRUD operations
def create_user(name: str, email: str, password: str, is_admin: bool = False) -> int:
    """Create a new user"""
    # Validate name
    if not name or not name.strip():
        raise ValueError("Name cannot be empty")
    name = name.strip()
    if len(name) > 100:
        raise ValueError(f"Name too long: {len(name)} characters")

    # Validate email format
    if not email or not EMAIL_REGEX.match(email):
        raise ValueError(f"Invalid email format: {email}")
    if len(email) > 254:  # RFC 5321 maximum
        raise ValueError(f"Email too long: {len(email)} characters")

    password_hash = hash_password(password)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, is_admin) VALUES (?, ?, ?, ?)",
            (name, email, password_hash, is_admin)
        )
        return cursor.lastrowid


def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user by ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        return dict(row) if row else None


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate user by email and password

    Args:
        email: User email address
        password: Plain text password

    Returns:
        User dict (without password_hash) if authentication successful, None otherwise
    """
    if not email or not password:
        return None

    # Get user by email
    user = get_user_by_email(email)
    if not user:
        return None

    # Verify password
    password_hash = hash_password(password)
    if user['password_hash'] != password_hash:
        return None

    # Authentication successful - return user without password hash
    user_copy = dict(user)
    del user_copy['password_hash']  # Don't expose password hash
    return user_copy


def list_all_users() -> List[Dict[str, Any]]:
    """List all users"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY id")
        return [dict(row) for row in cursor.fetchall()]


def delete_user(user_id: int) -> bool:
    """Delete user (cascades automatically to paths and user_skills)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        return cursor.rowcount > 0


# Path CRUD operations
def create_path(
    user_id: int,
    current_job_title: str,
    current_description: str,
    current_seniority: str,
    target_job_title: str,
    target_description: str,
    target_seniority: str,
    target_company: str,
    target_industry: str,
    topics: Optional[List[str]] = None
) -> str:
    """Create a new career path"""
    path_id = str(uuid.uuid4())
    topics_json = json.dumps(topics) if topics else json.dumps([])

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Validate user exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            raise ValueError(f"User with id {user_id} does not exist")

        cursor.execute("""
            INSERT INTO paths (
                id, user_id, current_job_title, current_description, current_seniority,
                target_job_title, target_description, target_seniority,
                target_company, target_industry, topics
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            path_id, user_id, current_job_title, current_description, current_seniority,
            target_job_title, target_description, target_seniority,
            target_company, target_industry, topics_json
        ))
        return path_id


def get_path(path_id: str) -> Optional[Dict[str, Any]]:
    """Get path by ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM paths WHERE id = ?", (path_id,))
        row = cursor.fetchone()
        if row:
            path = dict(row)
            path['topics'] = json.loads(path['topics']) if path['topics'] else []
            return path
        return None


def get_paths_by_user(user_id: int) -> List[Dict[str, Any]]:
    """Get all paths for a user, ordered by last accessed (most recent first)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM paths WHERE user_id = ? ORDER BY last_accessed DESC", (user_id,))
        paths = [dict(row) for row in cursor.fetchall()]
        for path in paths:
            path['topics'] = json.loads(path['topics']) if path['topics'] else []
        return paths


def get_path_count(user_id: int) -> int:
    """Get count of paths for a user"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM paths WHERE user_id = ?", (user_id,))
        return cursor.fetchone()[0]


def calculate_path_mastery(path: Dict[str, Any]) -> float:
    """
    Calculate overall path mastery as average of all topic mastery scores,
    including progress from completed modules

    Args:
        path: Path dict with 'id', 'user_id', and 'topics' fields

    Returns:
        Float between 0-100 representing overall path mastery percentage
    """
    topics = path.get('topics', [])
    if not topics:
        return 0.0

    user_id = path.get('user_id')
    path_id = path.get('id')

    if not user_id or not path_id:
        # Fallback to basic calculation if missing IDs
        mastery_scores = [topic.get('mastery', 0) for topic in topics]
        return round(sum(mastery_scores) / len(mastery_scores), 1)

    # Calculate updated mastery for each topic based on completed modules
    updated_mastery_scores = []
    for topic in topics:
        topic_id = topic.get('topic_id')
        initial_mastery = topic.get('mastery', 0)

        # Get completed modules for this topic
        completed_modules = get_completed_modules(user_id, path_id, topic_id)

        # Calculate mastery from completed modules (same logic as dashboard)
        points_per_module = (100 - initial_mastery) / 8.0
        mastery_from_modules = len(completed_modules) * points_per_module
        updated_mastery = min(int(initial_mastery + mastery_from_modules), 100)

        updated_mastery_scores.append(updated_mastery)

    return round(sum(updated_mastery_scores) / len(updated_mastery_scores), 1)


def update_path_last_accessed(path_id: str) -> bool:
    """Update path's last_accessed timestamp to now"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE paths SET last_accessed = CURRENT_TIMESTAMP WHERE id = ?",
            (path_id,)
        )
        return cursor.rowcount > 0


def update_path_readiness(path_id: str, global_readiness: float, topics: list) -> bool:
    """Update path's global readiness and topics"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE paths
               SET global_readiness = ?, topics = ?
               WHERE id = ?""",
            (global_readiness, json.dumps(topics), path_id)
        )
        return cursor.rowcount > 0


# User Skills CRUD operations
def create_user_skill(
    user_id: int,
    topic_id: str,
    mastery_percent: int,
    modules_complete: str = ""
) -> int:
    """Create a new user skill entry"""
    # Validate mastery_percent range
    if not 0 <= mastery_percent <= 100:
        raise ValueError(f"mastery_percent must be 0-100, got {mastery_percent}")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Validate user exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            raise ValueError(f"User with id {user_id} does not exist")

        cursor.execute("""
            INSERT INTO user_skills (
                user_id, topic_id, mastery_percent, modules_complete, last_completed
            ) VALUES (?, ?, ?, ?, ?)
        """, (user_id, topic_id, mastery_percent, modules_complete, datetime.now()))
        return cursor.lastrowid


def upsert_user_skill(
    user_id: int,
    topic_id: str,
    mastery_percent: int,
    modules_complete: str = "0/8",
    estimated_hours: int = 0
) -> int:
    """Insert or update user skill entry"""
    # Validate mastery_percent range
    if not 0 <= mastery_percent <= 100:
        raise ValueError(f"mastery_percent must be 0-100, got {mastery_percent}")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Check if skill already exists
        cursor.execute(
            "SELECT id FROM user_skills WHERE user_id = ? AND topic_id = ?",
            (user_id, topic_id)
        )
        existing = cursor.fetchone()

        if existing:
            # Update existing
            cursor.execute("""
                UPDATE user_skills
                SET mastery_percent = ?, modules_complete = ?, last_completed = ?
                WHERE user_id = ? AND topic_id = ?
            """, (mastery_percent, modules_complete, datetime.now(), user_id, topic_id))
            return existing[0]
        else:
            # Insert new
            cursor.execute("""
                INSERT INTO user_skills (
                    user_id, topic_id, mastery_percent, modules_complete, last_completed
                ) VALUES (?, ?, ?, ?, ?)
            """, (user_id, topic_id, mastery_percent, modules_complete, datetime.now()))
            return cursor.lastrowid


def get_user_skills(user_id: int) -> List[Dict[str, Any]]:
    """Get all skills for a user"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_skills WHERE user_id = ? ORDER BY topic_id", (user_id,))
        return [dict(row) for row in cursor.fetchall()]


# Phase 3.2: Module completion and answer tracking
def complete_module(user_id: int, path_id: str, topic_id: str, module_id: int, mastery_bonus: int = 15) -> int:
    """Mark a module as completed and award mastery bonus"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Insert or ignore (prevent duplicate completions)
        cursor.execute("""
            INSERT OR IGNORE INTO user_topic_modules
            (user_id, path_id, topic_id, module_id, mastery_bonus)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, path_id, topic_id, module_id, mastery_bonus))

        return cursor.lastrowid


def record_answer(
    user_id: int,
    path_id: str,
    topic_id: str,
    module_id: int,
    question_id: str,
    user_answer: str,
    is_correct: bool
) -> int:
    """Record a user's answer to a question"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_answers
            (user_id, path_id, topic_id, module_id, question_id, user_answer, is_correct)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, path_id, topic_id, module_id, question_id, user_answer, is_correct))
        return cursor.lastrowid


def get_completed_modules(user_id: int, path_id: str, topic_id: str) -> List[int]:
    """Get list of completed module IDs for a topic"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT module_id FROM user_topic_modules
            WHERE user_id = ? AND path_id = ? AND topic_id = ?
            ORDER BY module_id
        """, (user_id, path_id, topic_id))
        return [row[0] for row in cursor.fetchall()]


def get_topic_mastery_bonus(user_id: int, path_id: str, topic_id: str) -> int:
    """Calculate total mastery bonus for a topic from completed modules"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT SUM(mastery_bonus) FROM user_topic_modules
            WHERE user_id = ? AND path_id = ? AND topic_id = ?
        """, (user_id, path_id, topic_id))
        result = cursor.fetchone()[0]
        return result if result else 0


def get_total_completed_modules(user_id: int, path_id: str) -> int:
    """Get total count of all completed modules across all topics"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM user_topic_modules
            WHERE user_id = ? AND path_id = ?
        """, (user_id, path_id))
        return cursor.fetchone()[0]


def get_activity_streak(user_id: int, path_id: str) -> int:
    """Calculate current learning streak in days"""
    from datetime import datetime, timedelta

    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Get all unique completion dates, ordered descending
        cursor.execute("""
            SELECT DISTINCT DATE(completed_date) as completion_date
            FROM user_topic_modules
            WHERE user_id = ? AND path_id = ?
            ORDER BY completion_date DESC
        """, (user_id, path_id))

        dates = [row[0] for row in cursor.fetchall()]

        if not dates:
            return 0

        # Calculate streak from most recent date backwards
        streak = 0
        today = datetime.now().date()

        # Convert string dates to date objects
        activity_dates = [datetime.strptime(d, '%Y-%m-%d').date() for d in dates]

        # Check if there's activity today or yesterday (streak continues)
        if activity_dates[0] not in [today, today - timedelta(days=1)]:
            return 0

        # Count consecutive days
        expected_date = activity_dates[0]
        for activity_date in activity_dates:
            if activity_date == expected_date:
                streak += 1
                expected_date -= timedelta(days=1)
            elif activity_date < expected_date:
                # Gap found, break
                break

        return streak


def get_weekly_progress(user_id: int, path_id: str) -> Dict[str, Any]:
    """Get progress statistics for the past 7 days"""
    from datetime import datetime, timedelta

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get modules completed in last 7 days
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute("""
            SELECT COUNT(*) FROM user_topic_modules
            WHERE user_id = ? AND path_id = ? AND completed_date >= ?
        """, (user_id, path_id, seven_days_ago))

        modules_this_week = cursor.fetchone()[0]

        return {
            'modules_completed': modules_this_week,
            'days_active': min(modules_this_week, 7)  # Simple approximation
        }


def get_activity_heatmap(user_id: int, path_id: str, days: int = 28) -> List[Dict[str, Any]]:
    """Get daily activity data for heatmap visualization (last N days)"""
    from datetime import datetime, timedelta

    with get_db_connection() as conn:
        cursor = conn.cursor()

        start_date = (datetime.now() - timedelta(days=days-1)).date()

        # Get modules completed per day
        cursor.execute("""
            SELECT DATE(completed_date) as activity_date, COUNT(*) as module_count
            FROM user_topic_modules
            WHERE user_id = ? AND path_id = ? AND DATE(completed_date) >= ?
            GROUP BY DATE(completed_date)
        """, (user_id, path_id, start_date.strftime('%Y-%m-%d')))

        activity_dict = {row[0]: row[1] for row in cursor.fetchall()}

        # Build complete 28-day array with zeros for missing days
        heatmap_data = []
        for i in range(days):
            date = start_date + timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            heatmap_data.append({
                'date': date_str,
                'count': activity_dict.get(date_str, 0)
            })

        return heatmap_data


if __name__ == "__main__":
    # Initialize database if run directly
    init_db()
    print("Database initialized successfully")

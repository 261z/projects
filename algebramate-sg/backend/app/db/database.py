import sqlite3
from pathlib import Path

from ..config import settings


def database_path() -> Path:
    raw = settings.database_url.removeprefix("sqlite:///")
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[2] / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(database_path())
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _ensure_column(connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row["name"] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db() -> None:
    from ..rag.schemas import load_skills_validated

    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS skills (id TEXT PRIMARY KEY, topic TEXT NOT NULL, subtopic TEXT NOT NULL, school_level TEXT NOT NULL, prerequisite_skill_id TEXT);
            CREATE TABLE IF NOT EXISTS student_mastery (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, skill_id TEXT NOT NULL, mastery_score REAL NOT NULL DEFAULT 0.5, current_difficulty INTEGER NOT NULL DEFAULT 1, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE(user_id, skill_id), FOREIGN KEY(user_id) REFERENCES users(id));
            CREATE TABLE IF NOT EXISTS attempts (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, question_id TEXT NOT NULL, skill_id TEXT NOT NULL, difficulty INTEGER NOT NULL, student_answer TEXT NOT NULL, expected_answer TEXT NOT NULL, correct INTEGER NOT NULL, misconception TEXT, hints_used INTEGER NOT NULL DEFAULT 0, recommended_difficulty INTEGER, selected_difficulty INTEGER, difficulty_overridden INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(user_id) REFERENCES users(id));
            CREATE TABLE IF NOT EXISTS diagnostic_results (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, topic TEXT NOT NULL, raw_score INTEGER NOT NULL, initial_mastery REAL NOT NULL, recommended_starting_difficulty INTEGER NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(user_id) REFERENCES users(id));
            CREATE TABLE IF NOT EXISTS diagnostic_answers (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, topic TEXT NOT NULL, question_id TEXT NOT NULL, student_answer TEXT NOT NULL, correct INTEGER NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE(user_id, topic, question_id), FOREIGN KEY(user_id) REFERENCES users(id));
            CREATE TABLE IF NOT EXISTS generated_questions (question_id TEXT PRIMARY KEY, user_id INTEGER NOT NULL, topic TEXT NOT NULL, subtopic TEXT NOT NULL, skill_id TEXT NOT NULL, difficulty INTEGER NOT NULL, question TEXT NOT NULL, expected_answer TEXT NOT NULL, solution TEXT NOT NULL, marks INTEGER NOT NULL, learning_objective TEXT NOT NULL, source TEXT NOT NULL, verification_status TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(user_id) REFERENCES users(id));
            CREATE TABLE IF NOT EXISTS learning_sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, topic TEXT NOT NULL, started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, ended_at TEXT, questions_attempted INTEGER NOT NULL DEFAULT 0, questions_correct INTEGER NOT NULL DEFAULT 0, mastery_start REAL NOT NULL DEFAULT 0.5, mastery_end REAL, FOREIGN KEY(user_id) REFERENCES users(id));
            """
        )
        _ensure_column(connection, "attempts", "session_id", "INTEGER REFERENCES learning_sessions(id)")
        for skill in load_skills_validated():
            connection.execute(
                "INSERT INTO skills (id, topic, subtopic, school_level, prerequisite_skill_id) VALUES (?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET topic=excluded.topic, subtopic=excluded.subtopic, school_level=excluded.school_level, prerequisite_skill_id=excluded.prerequisite_skill_id",
                (skill.id, skill.topic, skill.subtopic, skill.school_level, skill.prerequisite_skill_id),
            )

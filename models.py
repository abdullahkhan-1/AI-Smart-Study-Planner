# =============================================================================
# models.py — Database Layer (PostgreSQL via Supabase)
# Smart Study Planner | SE Spring 2026
# =============================================================================
# DATABASE  : PostgreSQL (hosted on Supabase)
# DRIVER    : psycopg2
# PATTERN   : Singleton — one shared connection across the entire app
# =============================================================================

import psycopg2
import psycopg2.extras
import os
from datetime import date
from dotenv import load_dotenv

# Load .env file so DATABASE_URL is available
load_dotenv()


# =============================================================================
# Singleton Database Connection
# =============================================================================

class Database:
    """
    Singleton class — only ONE instance ever exists.
    All parts of the app share this same PostgreSQL connection.

    Why Singleton matters for PostgreSQL:
      - Opening a new connection is expensive (~100ms)
      - PostgreSQL has a connection limit (Supabase free = 60 max)
      - One shared connection avoids both problems
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise RuntimeError(
                "DATABASE_URL not found. "
                "Make sure your .env file exists with the Supabase connection string."
            )

        self.connection = psycopg2.connect(db_url)
        self.connection.autocommit = True
        self._initialized = True
        self._create_tables()
        print("✅ Connected to Supabase PostgreSQL successfully.")

    def _create_tables(self):
        """Create tables if they don't exist yet."""
        with self.connection.cursor() as cur:

            cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id          SERIAL PRIMARY KEY,
                    subject     TEXT    NOT NULL,
                    deadline    DATE    NOT NULL,
                    difficulty  INTEGER NOT NULL CHECK (difficulty BETWEEN 1 AND 5),
                    importance  INTEGER NOT NULL CHECK (importance BETWEEN 1 AND 5),
                    study_hours REAL    NOT NULL,
                    created_at  DATE    DEFAULT CURRENT_DATE
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS progress (
                    id          SERIAL PRIMARY KEY,
                    task_id     INTEGER REFERENCES tasks(id) ON DELETE SET NULL,
                    subject     TEXT    NOT NULL,
                    date        DATE    NOT NULL,
                    hours_done  REAL    NOT NULL,
                    completed   INTEGER DEFAULT 0
                )
            """)

    def execute(self, query: str, params: tuple = ()):
        """Run INSERT / UPDATE / DELETE."""
        with self.connection.cursor() as cur:
            cur.execute(query, params)

    def fetchall(self, query: str, params: tuple = ()) -> list:
        """Run SELECT and return all rows as list of dicts."""
        with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]

    def fetchone(self, query: str, params: tuple = ()) -> dict:
        """Run SELECT and return one row as dict."""
        with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            return dict(row) if row else None


# =============================================================================
# Task Model
# =============================================================================

class TaskModel:

    def __init__(self):
        self.db = Database()

    def add_task(self, subject, deadline, difficulty, importance, study_hours):
        self.db.execute(
            """INSERT INTO tasks
               (subject, deadline, difficulty, importance, study_hours)
               VALUES (%s, %s, %s, %s, %s)""",
            (subject, deadline, difficulty, importance, study_hours)
        )

    def get_all_tasks(self) -> list:
        rows = self.db.fetchall(
            "SELECT * FROM tasks ORDER BY deadline ASC"
        )
        # Supabase returns deadline as a date object already — ensure consistency
        for row in rows:
            if isinstance(row["deadline"], str):
                row["deadline"] = date.fromisoformat(row["deadline"])
        return rows

    def delete_task(self, task_id: int):
        self.db.execute("DELETE FROM tasks WHERE id = %s", (task_id,))

    def get_task(self, task_id: int) -> dict:
        row = self.db.fetchone(
            "SELECT * FROM tasks WHERE id = %s", (task_id,)
        )
        if row and isinstance(row["deadline"], str):
            row["deadline"] = date.fromisoformat(row["deadline"])
        return row


# =============================================================================
# Progress Model
# =============================================================================

class ProgressModel:

    def __init__(self):
        self.db = Database()

    def mark_complete(self, subject, session_date, hours_done):
        self.db.execute(
            """INSERT INTO progress (subject, date, hours_done, completed)
               VALUES (%s, %s, %s, 1)""",
            (subject, str(session_date), hours_done)
        )

    def get_completed(self) -> list:
        return self.db.fetchall(
            "SELECT * FROM progress WHERE completed = 1 ORDER BY date DESC"
        )

    def get_summary(self) -> dict:
        rows        = self.get_completed()
        total_hours = sum(r["hours_done"] for r in rows)
        subjects    = list({r["subject"] for r in rows})
        return {
            "total_sessions" : len(rows),
            "total_hours"    : round(total_hours, 2),
            "subjects_done"  : subjects,
        }

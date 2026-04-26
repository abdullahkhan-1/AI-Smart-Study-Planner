# =============================================================================
# models.py — Database Layer
# Smart Study Planner | SE Spring 2026
# =============================================================================
# DESIGN PATTERN USED: Singleton Pattern
#   - Only ONE database connection is ever created
#   - Every part of the app shares the same connection
#   - Prevents conflicts and wasted resources
# =============================================================================

import sqlite3
import os
from datetime import date


# =============================================================================
# Singleton Database Connection
# =============================================================================

class Database:
    """
    Singleton class — only one instance can ever exist.
    All parts of the app use this same instance to talk to the database.
    """
    _instance = None   # Holds the single instance

    def __new__(cls):
        """
        __new__ is called before __init__.
        If an instance already exists, return it.
        If not, create one. This guarantees only ONE instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return   # Already set up — do nothing

        db_path = os.path.join(os.path.dirname(__file__), "study_planner.db")
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row   # Returns rows as dicts
        self._initialized = True
        self._create_tables()

    def _create_tables(self):
        """Create all tables if they don't exist yet."""
        cursor = self.connection.cursor()

        # Tasks table — stores every study task the user enters
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                subject     TEXT    NOT NULL,
                deadline    TEXT    NOT NULL,
                difficulty  INTEGER NOT NULL,   -- 1 (easy) to 5 (hard)
                importance  INTEGER NOT NULL,   -- 1 (low)  to 5 (critical)
                study_hours REAL    NOT NULL,   -- total hours needed
                created_at  TEXT    DEFAULT (date('now'))
            )
        """)

        # Progress table — tracks completed study sessions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS progress (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id     INTEGER REFERENCES tasks(id),
                subject     TEXT    NOT NULL,
                date        TEXT    NOT NULL,
                hours_done  REAL    NOT NULL,
                completed   INTEGER DEFAULT 0   -- 0 = pending, 1 = done
            )
        """)

        self.connection.commit()

    def execute(self, query: str, params: tuple = ()):
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        self.connection.commit()
        return cursor

    def fetchall(self, query: str, params: tuple = ()) -> list:
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def fetchone(self, query: str, params: tuple = ()) -> dict:
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None


# =============================================================================
# Task Model — all database operations for tasks
# =============================================================================

class TaskModel:

    def __init__(self):
        self.db = Database()   # Gets the singleton instance

    def add_task(self, subject, deadline, difficulty, importance, study_hours):
        self.db.execute(
            "INSERT INTO tasks (subject, deadline, difficulty, importance, study_hours) VALUES (?,?,?,?,?)",
            (subject, str(deadline), difficulty, importance, study_hours)
        )

    def get_all_tasks(self) -> list:
        rows = self.db.fetchall("SELECT * FROM tasks ORDER BY deadline ASC")
        # Convert deadline strings back to date objects for the scheduler
        for row in rows:
            row["deadline"] = date.fromisoformat(row["deadline"])
        return rows

    def delete_task(self, task_id: int):
        self.db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    def get_task(self, task_id: int) -> dict:
        row = self.db.fetchone("SELECT * FROM tasks WHERE id = ?", (task_id,))
        if row:
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
            "INSERT INTO progress (subject, date, hours_done, completed) VALUES (?,?,?,1)",
            (subject, str(session_date), hours_done)
        )

    def get_completed(self) -> list:
        return self.db.fetchall("SELECT * FROM progress WHERE completed = 1 ORDER BY date DESC")

    def get_summary(self) -> dict:
        rows = self.get_completed()
        total_hours = sum(r["hours_done"] for r in rows)
        subjects    = list({r["subject"] for r in rows})
        return {
            "total_sessions" : len(rows),
            "total_hours"    : round(total_hours, 2),
            "subjects_done"  : subjects,
        }
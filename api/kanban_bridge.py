"""Project Tracking Kanban Bridge for Hermes AIOS Control Plane."""
import os
import json
import sqlite3
import time
from typing import Any

DB_PATH = os.path.expanduser("~/.hermes/state.db")


def _init_kanban_table():
    """Ensure kanban_tasks table exists in state.db."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kanban_tasks (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                column_id TEXT DEFAULT 'backlog',
                priority TEXT DEFAULT 'medium',
                assignee TEXT DEFAULT 'unassigned',
                created_at REAL,
                updated_at REAL
            );
        """)
        conn.commit()

        # Seed initial default tasks if empty
        cursor.execute("SELECT COUNT(*) FROM kanban_tasks;")
        count = cursor.fetchone()[0]
        if count == 0:
            now = time.time()
            default_tasks = [
                ("task_mkt_1", "market", "Continuous Camera Barcode Scanner", "Auto-rearm scanner for high volume checkout", "in_progress", "high", "Raphael", now, now),
                ("task_mkt_2", "market", "PostgreSQL Migration Audit", "Audit local DB queries vs Supabase references", "backlog", "high", "Antigravity", now, now),
                ("task_rst_1", "resto", "POS Order Sync to Kitchen", "Real-time SSE event stream for kitchen display", "in_progress", "medium", "Raphael", now, now),
                ("task_brb_1", "barber", "Romebois Online Booking Flow", "Customer appointment booking integration", "in_progress", "high", "Raphael", now, now),
                ("task_aios_1", "aios", "AIOS Gauntlet Phase 14 Security Gate", "Audit credential redaction and SSH host pinning", "review", "high", "Antigravity", now, now),
                ("task_aios_2", "aios", "Compact Side-Chat Box Layout", "Floating mini-chat sidebar for cross-feature navigation", "completed", "medium", "Raphael", now, now)
            ]
            cursor.executemany("""
                INSERT INTO kanban_tasks (id, project_id, title, description, column_id, priority, assignee, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, default_tasks)
            conn.commit()

        conn.close()
    except Exception as exc:
        print(f"[KanbanBridge] Table init error: {exc}")


_init_kanban_table()


def list_kanban_tasks(project_id: str = "all") -> dict[str, Any]:
    """Retrieve kanban tasks for a project or all projects."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if project_id == "all" or not project_id:
            cursor.execute("SELECT * FROM kanban_tasks ORDER BY updated_at DESC;")
        else:
            cursor.execute("SELECT * FROM kanban_tasks WHERE project_id = ? ORDER BY updated_at DESC;", (project_id,))

        rows = cursor.fetchall()
        tasks = [dict(r) for r in rows]
        conn.close()

        return {
            "status": "success",
            "project_id": project_id,
            "tasks": tasks
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def save_kanban_task(data: dict[str, Any]) -> dict[str, Any]:
    """Create or update a kanban task."""
    task_id = data.get("id") or f"task_{int(time.time() * 1000)}"
    project_id = data.get("project_id", "aios")
    title = data.get("title", "Untitled Task")
    description = data.get("description", "")
    column_id = data.get("column_id", "backlog")
    priority = data.get("priority", "medium")
    assignee = data.get("assignee", "unassigned")
    now = time.time()

    try:
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO kanban_tasks (id, project_id, title, description, column_id, priority, assignee, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                project_id=excluded.project_id,
                title=excluded.title,
                description=excluded.description,
                column_id=excluded.column_id,
                priority=excluded.priority,
                assignee=excluded.assignee,
                updated_at=excluded.updated_at;
        """, (task_id, project_id, title, description, column_id, priority, assignee, now, now))
        conn.commit()
        conn.close()

        return {
            "status": "success",
            "task_id": task_id,
            "message": "Task saved successfully"
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def delete_kanban_task(task_id: str) -> dict[str, Any]:
    """Delete a kanban task by ID."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM kanban_tasks WHERE id = ?;", (task_id,))
        conn.commit()
        conn.close()
        return {"status": "success", "task_id": task_id}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}

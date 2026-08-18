"""
Global Warning & Error Attention System Engine for Raphael Control Center
"""
import os
import json
import sqlite3
import time
from typing import Any

DB_PATH = os.path.expanduser("~/.hermes/state.db")


def _init_errors_table():
    """Ensure system_errors table exists in state.db."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_errors (
                id TEXT PRIMARY KEY,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                project_id TEXT,
                affected_resource TEXT,
                evidence TEXT,
                related_execution TEXT,
                related_deployment TEXT,
                suggested_action TEXT,
                status TEXT DEFAULT 'OPEN',
                occurrences INTEGER DEFAULT 1,
                created_at REAL,
                last_seen_at REAL
            );
        """)
        conn.commit()
        conn.close()
    except Exception as exc:
        print(f"[ErrorsBridge] Table init error: {exc}")


_init_errors_table()


def register_system_error(
    severity: str,
    title: str,
    source: str,
    project_id: str = None,
    affected_resource: str = None,
    evidence: str = None,
    related_execution: str = None,
    related_deployment: str = None,
    suggested_action: str = None,
    existing_conn: sqlite3.Connection = None
) -> dict[str, Any]:
    """Register or deduplicate a system error or warning."""
    now = time.time()
    err_sig = f"{severity}:{source}:{title}:{project_id or ''}"
    err_id = f"ERR-{abs(hash(err_sig)) % 100000:05d}"

    close_conn = False
    if existing_conn:
        conn = existing_conn
    else:
        try:
            conn = sqlite3.connect(DB_PATH, timeout=10.0)
            conn.execute("PRAGMA journal_mode=WAL;")
            close_conn = True
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, occurrences FROM system_errors WHERE id = ?;", (err_id,))
        row = cursor.fetchone()

        if row:
            occurrences = row[1] + 1
            cursor.execute("""
                UPDATE system_errors
                SET occurrences = ?, last_seen_at = ?, evidence = ?, status = 'OPEN'
                WHERE id = ?;
            """, (occurrences, now, evidence, err_id))
        else:
            cursor.execute("""
                INSERT INTO system_errors (id, severity, title, source, project_id, affected_resource, evidence, related_execution, related_deployment, suggested_action, status, occurrences, created_at, last_seen_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', 1, ?, ?);
            """, (err_id, severity, title, source, project_id, affected_resource, evidence, related_execution, related_deployment, suggested_action, now, now))

        if close_conn:
            conn.commit()
            conn.close()

        return {
            "status": "success",
            "error_id": err_id,
            "severity": severity,
            "title": title
        }
    except Exception as exc:
        if close_conn:
            try: conn.close()
            except Exception: pass
        return {"status": "error", "message": str(exc)}


def get_active_warnings() -> dict[str, Any]:
    """Retrieve all open/active system warnings & errors sorted by severity."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM system_errors 
            WHERE status IN ('OPEN', 'ACKNOWLEDGED', 'INVESTIGATING')
            ORDER BY 
                CASE severity 
                    WHEN 'CRITICAL' THEN 1 
                    WHEN 'ERROR' THEN 2 
                    WHEN 'WARNING' THEN 3 
                    ELSE 4 
                END, last_seen_at DESC;
        """)
        rows = cursor.fetchall()
        errors = [dict(r) for r in rows]
        conn.close()

        counts = {
            "CRITICAL": sum(1 for e in errors if e["severity"] == "CRITICAL"),
            "ERROR": sum(1 for e in errors if e["severity"] == "ERROR"),
            "WARNING": sum(1 for e in errors if e["severity"] == "WARNING"),
            "INFO": sum(1 for e in errors if e["severity"] == "INFO"),
            "TOTAL": len(errors)
        }

        return {
            "status": "success",
            "counts": counts,
            "errors": errors
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def update_error_status(err_id: str, new_status: str) -> dict[str, Any]:
    """Update error operational lifecycle status (ACKNOWLEDGED, INVESTIGATING, RESOLVED, IGNORED)."""
    valid_statuses = {"OPEN", "ACKNOWLEDGED", "INVESTIGATING", "RESOLVED", "IGNORED"}
    if new_status not in valid_statuses:
        return {"status": "error", "message": f"Invalid status '{new_status}'. Allowed: {valid_statuses}"}

    try:
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.cursor()
        cursor.execute("UPDATE system_errors SET status = ? WHERE id = ?;", (new_status, err_id))
        conn.commit()
        conn.close()

        return {
            "status": "success",
            "error_id": err_id,
            "new_status": new_status
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}

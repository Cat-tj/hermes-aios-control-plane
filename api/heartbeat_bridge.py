"""
Agent Liveness & Heartbeat Telemetry Engine for Raphael Control Center
"""
import os
import sqlite3
import time
from typing import Any
from api.errors_bridge import register_system_error

DB_PATH = os.path.expanduser("~/.hermes/state.db")
STALE_THRESHOLD_SEC = 120.0


def _init_agents_table():
    """Ensure specialist_agents table exists in state.db."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS specialist_agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                scope TEXT DEFAULT 'PROJECT',
                project_id TEXT,
                current_mission_id TEXT,
                current_milestone_id TEXT,
                current_task_id TEXT,
                liveness_status TEXT DEFAULT 'IDLE',
                last_heartbeat_at REAL,
                updated_at REAL
            );
        """)
        conn.commit()

        # Seed default agents if empty
        cursor.execute("SELECT COUNT(*) FROM specialist_agents;")
        if cursor.fetchone()[0] == 0:
            now = time.time()
            default_agents = [
                ("ag-raphael-global", "Raphael Master Agent", "Master Orchestrator", "GLOBAL", None, None, None, None, "WORKING", now, now),
                ("ag-gal-fe", "Galaxy Frontend Agent", "UI/UX & Canvas Engineer", "PROJECT", "proj-galaxy", "m-galaxy-mvp", "ms-g4", "t-fe-visualizer", "WORKING", now, now),
                ("ag-gal-be", "Galaxy Backend Agent", "Projection Stream Engineer", "PROJECT", "proj-galaxy", "m-galaxy-mvp", "ms-g4", "t-be-telemetry", "WORKING", now, now),
                ("ag-altora-resto", "Altora Resto Agent", "Backend Developer", "PROJECT", "proj-altora", None, None, None, "IDLE", now - 50, now - 50)
            ]
            cursor.executemany("""
                INSERT INTO specialist_agents (id, name, role, scope, project_id, current_mission_id, current_milestone_id, current_task_id, liveness_status, last_heartbeat_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, default_agents)
            conn.commit()

        conn.close()
    except Exception as exc:
        print(f"[HeartbeatBridge] Table init error: {exc}")


_init_agents_table()


def record_agent_heartbeat(
    agent_id: str,
    liveness_status: str = "WORKING",
    project_id: str = None,
    current_mission_id: str = None,
    current_milestone_id: str = None,
    current_task_id: str = None
) -> dict[str, Any]:
    """Record an incoming agent heartbeat and update liveness status."""
    now = time.time()
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE specialist_agents
            SET liveness_status = ?,
                project_id = COALESCE(?, project_id),
                current_mission_id = COALESCE(?, current_mission_id),
                current_milestone_id = COALESCE(?, current_milestone_id),
                current_task_id = COALESCE(?, current_task_id),
                last_heartbeat_at = ?,
                updated_at = ?
            WHERE id = ?;
        """, (liveness_status, project_id, current_mission_id, current_milestone_id, current_task_id, now, now, agent_id))

        conn.commit()
        conn.close()

        return {
            "status": "success",
            "agent_id": agent_id,
            "liveness_status": liveness_status,
            "last_heartbeat_at": now
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def audit_stale_agent_heartbeats() -> dict[str, Any]:
    """Scan active agents and transition stale ones to OFFLINE, emitting system warnings."""
    now = time.time()
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM specialist_agents WHERE liveness_status IN ('WORKING', 'WAITING', 'BLOCKED');")
        active_agents = [dict(r) for r in cursor.fetchall()]

        stale_count = 0
        stale_agents = []

        for ag in active_agents:
            elapsed = now - ag["last_heartbeat_at"]
            if elapsed > STALE_THRESHOLD_SEC:
                stale_count += 1
                stale_agents.append(ag["name"])
                
                cursor.execute("UPDATE specialist_agents SET liveness_status = 'OFFLINE' WHERE id = ?;", (ag["id"],))
                
                register_system_error(
                    severity="WARNING",
                    title=f"Agent '{ag['name']}' Heartbeat Stale",
                    source="Agent",
                    project_id=ag["project_id"],
                    affected_resource=ag["id"],
                    evidence=f"No liveness heartbeat received for {int(elapsed)} seconds (threshold: {int(STALE_THRESHOLD_SEC)}s)",
                    suggested_action="Inspect agent process health and restart if needed",
                    existing_conn=conn
                )

        conn.commit()
        conn.close()
        return {
            "status": "success",
            "stale_detected": stale_count,
            "stale_agents": stale_agents,
            "checked_at": now
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def list_agent_liveness() -> dict[str, Any]:
    """Retrieve liveness telemetry for all agents."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM specialist_agents ORDER BY scope ASC, liveness_status ASC, name ASC;")
        agents = [dict(r) for r in cursor.fetchall()]

        summary = {
            "WORKING": sum(1 for a in agents if a["liveness_status"] == "WORKING"),
            "IDLE": sum(1 for a in agents if a["liveness_status"] == "IDLE"),
            "WAITING": sum(1 for a in agents if a["liveness_status"] == "WAITING"),
            "BLOCKED": sum(1 for a in agents if a["liveness_status"] == "BLOCKED"),
            "OFFLINE": sum(1 for a in agents if a["liveness_status"] == "OFFLINE"),
            "ERROR": sum(1 for a in agents if a["liveness_status"] == "ERROR"),
            "PAUSED": sum(1 for a in agents if a["liveness_status"] == "PAUSED"),
            "TOTAL": len(agents)
        }

        conn.close()
        return {
            "status": "success",
            "summary": summary,
            "agents": agents
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}

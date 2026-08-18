"""
Ego-Lite Personal AI Agent Identity & Memory Engine Bridge for Raphael Control Center
Inspired by CitroLabs Ego-Lite (https://github.com/citrolabs/ego-lite)
"""
import os
import json
import sqlite3
import time
from typing import Any

DB_PATH = os.path.expanduser("~/.hermes/state.db")


def _init_ego_tables():
    """Ensure ego_profiles and ego_memories tables exist in state.db."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ego_profiles (
                agent_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                scope TEXT DEFAULT 'PROJECT',
                project_id TEXT,
                identity_prompt TEXT,
                reflection_notes TEXT,
                updated_at REAL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ego_memories (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                category TEXT DEFAULT 'fact',
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                created_at REAL,
                updated_at REAL
            );
        """)
        conn.commit()

        # Seed default agent identities if empty
        cursor.execute("SELECT COUNT(*) FROM ego_profiles;")
        if cursor.fetchone()[0] == 0:
            now = time.time()
            default_agents = [
                ("ag-raphael-global", "Raphael Master Agent", "Company Architect & Master Orchestrator", "GLOBAL", None, "You are Raphael, the master orchestrator AI of Raphael Control Center.", "Focus on evidence-based verification and company pillar progress.", now),
                ("ag-gal-fe", "Galaxy Frontend Agent", "UI/UX & WebGL Developer", "PROJECT", "proj-galaxy", "You are Galaxy Frontend Agent, specialized in Project Galaxy 2D/3D graph rendering.", "Uses WebGL and DOM canvas for node visualization.", now),
                ("ag-gal-be", "Galaxy Backend Agent", "Projection Service Engineer", "PROJECT", "proj-galaxy", "You are Galaxy Backend Agent, specialized in Project Galaxy event streams.", "Manages node projections and SQLite state snapshots.", now)
            ]
            cursor.executemany("""
                INSERT INTO ego_profiles (agent_id, name, role, scope, project_id, identity_prompt, reflection_notes, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, default_agents)
            conn.commit()

        conn.close()
    except Exception as exc:
        print(f"[EgoBridge] Table init error: {exc}")


_init_ego_tables()


def get_agent_ego_profile(agent_id: str) -> dict[str, Any]:
    """Retrieve an agent's Ego identity profile and working memories."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM ego_profiles WHERE agent_id = ?;", (agent_id,))
        prof_row = cursor.fetchone()
        if not prof_row:
            conn.close()
            return {"status": "error", "message": f"Agent identity '{agent_id}' not found"}

        profile = dict(prof_row)

        cursor.execute("SELECT * FROM ego_memories WHERE agent_id = ? ORDER BY updated_at DESC;", (agent_id,))
        mem_rows = cursor.fetchall()
        memories = [dict(m) for m in mem_rows]
        conn.close()

        return {
            "status": "success",
            "source": "https://github.com/citrolabs/ego-lite",
            "agent_id": agent_id,
            "profile": profile,
            "memory_count": len(memories),
            "memories": memories
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def save_agent_ego_memory(agent_id: str, key: str, value: str, category: str = "fact") -> dict[str, Any]:
    """Save or update a durable memory entry for an agent."""
    mem_id = f"mem_{agent_id}_{hash(key) & 0xffffffff}"
    now = time.time()
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ego_memories (id, agent_id, category, key, value, confidence, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 1.0, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                value=excluded.value,
                category=excluded.category,
                updated_at=excluded.updated_at;
        """, (mem_id, agent_id, category, key, value, now, now))
        conn.commit()
        conn.close()

        return {
            "status": "success",
            "memory_id": mem_id,
            "agent_id": agent_id,
            "key": key,
            "updated_at": now
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}

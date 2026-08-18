"""Subagents & Multi-Agent Observability Bridge for Hermes AIOS Office Workspace."""
import json
import os
import sqlite3
import time
from typing import Any

STATE_DB_PATH = os.path.expanduser("~/.hermes/state.db")

PROJECT_DESKS = {
    "market": {
        "id": "market",
        "name": "Altora Market Agent Desk",
        "icon": "🛒",
        "path": "/Users/icat/Projects/Altora/apps/market",
        "description": "Monorepo POS & Inventory Engine for Altora Market",
        "color": "#10b981",
    },
    "resto": {
        "id": "resto",
        "name": "Altora Resto Agent Desk",
        "icon": "🍽️",
        "path": "/Users/icat/Projects/altora-resto",
        "description": "Kitchen Display System, Reservations & Resto Operations",
        "color": "#3889fd",
    },
    "barber": {
        "id": "barber",
        "name": "Romebois Barbershop Agent Desk",
        "icon": "💈",
        "path": "/Users/icat/Projects/altora-barber",
        "description": "Barbershop Booking, Queue & Member Management",
        "color": "#a855f7",
    },
    "galaxy": {
        "id": "galaxy",
        "name": "Project Galaxy Agent Desk",
        "icon": "🌌",
        "path": "/Users/icat/workspace/project-galaxy",
        "description": "Codebase Knowledge Graph, Snapshots & Projection Engine",
        "color": "#08ebf1",
    },
    "aios": {
        "id": "aios",
        "name": "AIOS Core Engine Desk",
        "icon": "🤖",
        "path": "/Users/icat/hermes-webui",
        "description": "Hermes AI Operating System, Omniroute & Swarm Control Plane",
        "color": "#f59e0b",
    },
}

ANGEL_AGENTS = {
    "michael": {
        "handle": "@michael",
        "name": "Archangel Michael",
        "title": "Build, Code & Engineering Lead",
        "icon": "⚔️",
        "avatar_color": "#38bdf8",
        "desk_id": "aios",
        "model": "claude-opus-5",
        "key_type": "AgentRouter Primary Key (sk-hhN...)",
        "api_key_env": "AGENTROUTER_API_KEY",
        "system_prompt": "You are Archangel Michael (@michael), Chief Engineering Lead and Warrior Architect of Raphael AI OS. You specialize in high-performance coding, monorepo refactoring, TypeScript, Next.js, and system builds. Respond with decisive, precise engineering excellence.",
    },
    "gabriel": {
        "handle": "@gabriel",
        "name": "Archangel Gabriel",
        "title": "System Architect & Task Communicator",
        "icon": "🎺",
        "avatar_color": "#a855f7",
        "desk_id": "galaxy",
        "model": "claude-sonnet-5",
        "key_type": "AgentRouter Secondary Key (sk-Qvb...)",
        "api_key_env": "AGENTROUTER_API_KEY_SECONDARY",
        "system_prompt": "You are Archangel Gabriel (@gabriel), Messenger and System Architect of Raphael AI OS. You specialize in task decomposition, API contracts, architectural diagrams, and clear technical communication.",
    },
    "uriel": {
        "handle": "@uriel",
        "name": "Archangel Uriel",
        "title": "Security, Audit & Visual Guard",
        "icon": "☀️",
        "avatar_color": "#f59e0b",
        "desk_id": "aios",
        "model": "gpt-5.6-sol",
        "key_type": "OmniRoute Gateway (:20128)",
        "api_key_env": "OMNIROUTE_API_KEY",
        "system_prompt": "You are Archangel Uriel (@uriel), Security Auditor and Visual QA Guard of Raphael AI OS. You illuminate bugs, inspect code quality, verify Safelock vault compliance, and perform visual QA.",
    },
    "jophiel": {
        "handle": "@jophiel",
        "name": "Archangel Jophiel",
        "title": "UI/UX Craft & Motion Engineer",
        "icon": "🎨",
        "avatar_color": "#ec4899",
        "desk_id": "resto",
        "model": "claude-3-5-sonnet-20241022",
        "key_type": "AgentRouter Primary Key (sk-hhN...)",
        "api_key_env": "AGENTROUTER_API_KEY",
        "system_prompt": "You are Archangel Jophiel (@jophiel), Elite UI/UX Engineer and Motion Designer of Raphael AI OS. You enforce anti-slop frontend design, Swiss typography, GSAP motion, and editorial aesthetic craft.",
    },
    "zadkiel": {
        "handle": "@zadkiel",
        "name": "Archangel Zadkiel",
        "title": "Automation & Cron Engine",
        "icon": "⚖️",
        "avatar_color": "#10b981",
        "desk_id": "aios",
        "model": "opencode/mimo-v2.5-free",
        "key_type": "OmniRoute Free Stack Gateway (:20128)",
        "api_key_env": "OMNIROUTE_API_KEY",
        "system_prompt": "You are Archangel Zadkiel (@zadkiel), Mercy Automation & Cron Engine of Raphael AI OS. You handle background watchdogs, database backups, uptime probes, and scheduled tasks using zero-cost free stack execution.",
    },
    "raphael": {
        "handle": "@raphael",
        "name": "Archangel Raphael",
        "title": "Master AI OS Coordinator",
        "icon": "👑",
        "avatar_color": "#6366f1",
        "desk_id": "aios",
        "model": "claude-opus-5",
        "key_type": "OmniRoute Master Router",
        "api_key_env": "OMNIROUTE_API_KEY",
        "system_prompt": "You are Archangel Raphael (@raphael), Master Coordinator and AI OS Control Plane Lead. You orchestrate all Angel Sub-Agents and ensure seamless user collaboration.",
    }
}

def get_angel_agents() -> dict[str, Any]:
    """Return the registry of Angel Sub-Agents with handles, model bindings, and API key assignments."""
    return {
        "status": "success",
        "total_angels": len(ANGEL_AGENTS),
        "angels": list(ANGEL_AGENTS.values())
    }

def parse_angel_summon(prompt_text: str) -> dict[str, Any] | None:
    """Parse text for `@angel` mention (e.g. `@michael refactor this code`)."""
    if not prompt_text:
        return None
    words = prompt_text.strip().split()
    if not words:
        return None
    first = words[0].lower()
    if first.startswith("@"):
        angel_name = first[1:]
        if angel_name in ANGEL_AGENTS:
            task_prompt = " ".join(words[1:])
            return {
                "angel_key": angel_name,
                "angel": ANGEL_AGENTS[angel_name],
                "task_prompt": task_prompt
            }
    return None


def _get_db_connection() -> sqlite3.Connection | None:
    if not os.path.exists(STATE_DB_PATH):
        return None
    try:
        conn = sqlite3.connect(STATE_DB_PATH, timeout=5.0)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None


def get_subagents_list(limit: int = 50) -> dict[str, Any]:
    """Return a list of delegated subagents with status, timing, goals, and results."""
    conn = _get_db_connection()
    if not conn:
        return {"status": "error", "message": "Hermes state database not available", "subagents": []}

    try:
        query = """
        SELECT 
            d.delegation_id,
            d.origin_session,
            d.origin_session_id,
            d.parent_session_id,
            d.state,
            d.dispatched_at,
            d.completed_at,
            d.updated_at,
            d.task_json,
            d.result_json,
            d.delivery_state,
            s.id as child_session_id,
            s.title as child_session_title,
            s.model as child_model,
            s.message_count,
            s.tool_call_count,
            s.input_tokens,
            s.output_tokens
        FROM async_delegations d
        LEFT JOIN sessions s ON s.parent_session_id = d.origin_session AND s.source = 'subagent'
        ORDER BY d.dispatched_at DESC
        LIMIT ?
        """
        cursor = conn.execute(query, (limit,))
        rows = cursor.fetchall()

        subagents = []
        now = time.time()

        for row in rows:
            task_info = {}
            if row["task_json"]:
                try:
                    task_info = json.loads(row["task_json"])
                except Exception:
                    task_info = {}

            result_info = {}
            if row["result_json"]:
                try:
                    result_info = json.loads(row["result_json"])
                except Exception:
                    result_info = {}

            dispatched_at = row["dispatched_at"] or 0
            completed_at = row["completed_at"]
            if completed_at:
                duration = round(completed_at - dispatched_at, 1)
            elif row["state"] == "running":
                duration = round(now - dispatched_at, 1)
            else:
                duration = 0

            goal = task_info.get("goal") or "Subagent task"
            goals = task_info.get("goals") or [goal]
            is_batch = task_info.get("is_batch", False) or len(goals) > 1

            subagents.append({
                "delegation_id": row["delegation_id"],
                "origin_session": row["origin_session"],
                "parent_session_id": row["parent_session_id"],
                "state": row["state"] or "unknown",
                "dispatched_at": dispatched_at,
                "dispatched_at_iso": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(dispatched_at)) if dispatched_at else "",
                "completed_at": completed_at,
                "completed_at_iso": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(completed_at)) if completed_at else "",
                "duration_seconds": duration,
                "goal": goal,
                "goals": goals,
                "is_batch": is_batch,
                "role": task_info.get("role", "leaf"),
                "context": task_info.get("context"),
                "model": task_info.get("model") or row["child_model"] or "default",
                "child_session_id": row["child_session_id"],
                "child_session_title": row["child_session_title"],
                "message_count": row["message_count"] or 0,
                "tool_call_count": row["tool_call_count"] or 0,
                "tokens": {
                    "input": row["input_tokens"] or 0,
                    "output": row["output_tokens"] or 0,
                },
                "result": {
                    "summary": result_info.get("summary") or result_info.get("output") or "",
                    "success": row["state"] == "completed",
                    "error": result_info.get("error") if row["state"] == "failed" else None
                }
            })

        running_count = sum(1 for s in subagents if s["state"] == "running")
        completed_count = sum(1 for s in subagents if s["state"] == "completed")
        failed_count = sum(1 for s in subagents if s["state"] == "failed")

        return {
            "status": "success",
            "timestamp": int(now),
            "summary": {
                "total": len(subagents),
                "running": running_count,
                "completed": completed_count,
                "failed": failed_count
            },
            "subagents": subagents
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc), "subagents": []}
    finally:
        conn.close()


def get_subagent_detail(delegation_id: str) -> dict[str, Any]:
    """Return detailed transcript and execution log for a subagent delegation."""
    conn = _get_db_connection()
    if not conn:
        return {"status": "error", "message": "Database error"}

    try:
        cursor = conn.execute(
            "SELECT * FROM async_delegations WHERE delegation_id = ? OR origin_session = ?",
            (delegation_id, delegation_id),
        )
        row = cursor.fetchone()
        if not row:
            return {"status": "error", "message": "Subagent delegation not found"}

        task_info = json.loads(row["task_json"]) if row["task_json"] else {}
        result_info = json.loads(row["result_json"]) if row["result_json"] else {}

        messages = []
        child_sid = row["origin_session"]
        if child_sid:
            msg_cursor = conn.execute(
                "SELECT id, role, content, timestamp FROM messages WHERE session_id = ? ORDER BY id ASC",
                (child_sid,),
            )
            for m in msg_cursor.fetchall():
                messages.append({
                    "id": m["id"],
                    "role": m["role"],
                    "content": m["content"][:2000] if m["content"] else "",
                    "created_at": m["timestamp"]
                })

        return {
            "status": "success",
            "delegation": {
                "delegation_id": row["delegation_id"],
                "origin_session": row["origin_session"],
                "state": row["state"],
                "dispatched_at": row["dispatched_at"],
                "completed_at": row["completed_at"],
                "task": task_info,
                "result": result_info,
                "messages": messages
            }
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}
    finally:
        conn.close()


def spawn_subagent(goal: str, context: str = "", role: str = "leaf", model: str = "", project_id: str = "aios") -> dict[str, Any]:
    """Spawn an autonomous background subagent via Hermes CLI."""
    if not goal or not goal.strip():
        return {"status": "error", "message": "Goal is required to spawn a subagent"}

    import subprocess
    import uuid

    project = PROJECT_DESKS.get(project_id, PROJECT_DESKS["aios"])
    workdir = project["path"] if os.path.exists(project["path"]) else "/Users/icat/workspace"

    delegation_id = f"deleg_{uuid.uuid4().hex[:8]}"
    cmd = [
        os.path.expanduser("~/.hermes/hermes-agent/venv/bin/hermes"),
        "-z",
        f"Project [{project['name']}] Subagent Task [{delegation_id}]: {goal.strip()}",
        "--in",
        workdir
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
            cwd=workdir
        )
        
        conn = _get_db_connection()
        if conn:
            try:
                now = time.time()
                task_payload = json.dumps({
                    "goal": goal.strip(),
                    "goals": [goal.strip()],
                    "context": context.strip() if context else None,
                    "role": role,
                    "model": model or "default",
                    "project_id": project_id,
                    "project_name": project["name"],
                    "is_batch": False
                })
                conn.execute(
                    """
                    INSERT OR REPLACE INTO async_delegations 
                    (delegation_id, origin_session, origin_session_id, parent_session_id, state, dispatched_at, updated_at, task_json, owner_pid)
                    VALUES (?, ?, ?, ?, 'running', ?, ?, ?, ?)
                    """,
                    (delegation_id, f"webui_{delegation_id}", f"webui_{delegation_id}", f"project_{project_id}_lead", now, now, task_payload, proc.pid)
                )
                conn.commit()
            except Exception:
                pass
            finally:
                conn.close()

        return {
            "status": "success",
            "message": f"Subagent dispatched to project {project['name']} successfully",
            "delegation_id": delegation_id,
            "project_id": project_id,
            "pid": proc.pid
        }
    except Exception as exc:
        return {"status": "error", "message": f"Failed to spawn subagent: {str(exc)}"}


def get_office_state() -> dict[str, Any]:
    """Return the visual agent office state: project desks, lead bots, and active worker subagent trees."""
    subagents_data = get_subagents_list(limit=100)
    all_subagents = subagents_data.get("subagents", [])

    desks = []
    now = time.time()

    for pid, pdata in PROJECT_DESKS.items():
        # Match subagents to project by path, goal, context, or project_id
        matched_subagents = []
        for sa in all_subagents:
            goal_lower = sa["goal"].lower()
            ctx_lower = (sa["context"] or "").lower()
            sa_proj = ""
            if isinstance(sa.get("context"), str) and "project_id" in sa["context"]:
                pass

            if (pid in goal_lower) or (pid in ctx_lower) or (pdata["path"].lower() in ctx_lower) or (pdata["name"].lower() in goal_lower):
                matched_subagents.append(sa)
            elif pid == "aios" and not any(k in goal_lower for k in ["market", "resto", "barber", "galaxy"]):
                matched_subagents.append(sa)

        active_workers = [sa for sa in matched_subagents if sa["state"] == "running"]
        completed_workers = [sa for sa in matched_subagents if sa["state"] == "completed"]
        failed_workers = [sa for sa in matched_subagents if sa["state"] == "failed"]

        is_busy = len(active_workers) > 0
        lead_status = "active_executing" if is_busy else "idle_ready"

        desks.append({
            "id": pid,
            "name": pdata["name"],
            "icon": pdata["icon"],
            "path": pdata["path"],
            "description": pdata["description"],
            "color": pdata["color"],
            "lead_bot": {
                "id": f"bot_{pid}_lead",
                "name": f"{pdata['name']} Lead Bot",
                "status": lead_status,
                "active_subagent_count": len(active_workers),
                "total_subagents_spawned": len(matched_subagents),
            },
            "subagent_workers": matched_subagents[:10],
            "stats": {
                "active": len(active_workers),
                "completed": len(completed_workers),
                "failed": len(failed_workers),
                "total": len(matched_subagents)
            }
        })

    return {
        "status": "success",
        "timestamp": int(now),
        "total_desks": len(desks),
        "active_swarms": sum(d["stats"]["active"] for d in desks),
        "desks": desks
    }

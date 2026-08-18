"""
Core Domain Model & Pillar Hierarchy Engine for Raphael Control Center
"""
import os
import json
import sqlite3
import time
from typing import Any

DB_PATH = os.path.expanduser("~/.hermes/state.db")


def _init_domain_tables():
    """Ensure domain hierarchy tables exist in SQLite."""
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    cursor = conn.cursor()
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS company_pillars (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        lead_person TEXT,
        created_at REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS company_projects (
        id TEXT PRIMARY KEY,
        pillar_id TEXT,
        name TEXT NOT NULL,
        repo_url TEXT,
        description TEXT,
        status TEXT DEFAULT 'active',
        created_at REAL NOT NULL,
        FOREIGN KEY(pillar_id) REFERENCES company_pillars(id)
    );

    CREATE TABLE IF NOT EXISTS company_missions (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        title TEXT NOT NULL,
        objective TEXT,
        status TEXT DEFAULT 'in_progress',
        created_at REAL NOT NULL,
        FOREIGN KEY(project_id) REFERENCES company_projects(id)
    );

    CREATE TABLE IF NOT EXISTS company_milestones (
        id TEXT PRIMARY KEY,
        mission_id TEXT NOT NULL,
        title TEXT NOT NULL,
        order_index INTEGER DEFAULT 0,
        status TEXT DEFAULT 'pending', -- pending, in_progress, completed, blocked
        completed_at REAL,
        FOREIGN KEY(mission_id) REFERENCES company_missions(id)
    );

    CREATE TABLE IF NOT EXISTS specialist_agents (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        scope TEXT DEFAULT 'PROJECT', -- GLOBAL or PROJECT
        project_id TEXT,
        current_mission_id TEXT,
        current_milestone_id TEXT,
        current_task_id TEXT,
        liveness_status TEXT DEFAULT 'IDLE', -- WORKING, IDLE, WAITING, BLOCKED, OFFLINE, ERROR, PAUSED
        last_heartbeat_at REAL NOT NULL,
        useful_work_count INTEGER DEFAULT 0,
        failed_work_count INTEGER DEFAULT 0,
        created_at REAL NOT NULL
    );
    """)

    # Seed initial company pillars & projects if empty
    cursor.execute("SELECT COUNT(*) FROM company_pillars;")
    if cursor.fetchone()[0] == 0:
        now = time.time()
        cursor.execute("INSERT INTO company_pillars VALUES (?, ?, ?, ?, ?)",
                       ("p-tech", "Product & Technology", "Engineering, Infrastructure, and AI OS Development", "ICat", now))
        cursor.execute("INSERT INTO company_pillars VALUES (?, ?, ?, ?, ?)",
                       ("p-ops", "Operations & Services", "Client Services, Barbershop ERP, and POS Solutions", "ICat", now))

        # Seed projects
        cursor.execute("INSERT INTO company_projects VALUES (?, ?, ?, ?, ?, ?, ?)",
                       ("proj-galaxy", "p-tech", "Project Galaxy", "https://github.com/Cat-tj/project-galaxy", "Graph Projections & AI Visualization", "active", now))
        cursor.execute("INSERT INTO company_projects VALUES (?, ?, ?, ?, ?, ?, ?)",
                       ("proj-raphael", "p-tech", "Raphael Control Center", "https://github.com/Cat-tj/hermes-aios-control-plane", "Company Operating Control Plane", "active", now))
        cursor.execute("INSERT INTO company_projects VALUES (?, ?, ?, ?, ?, ?, ?)",
                       ("proj-altora", "p-ops", "Altora ERP Suite", "https://github.com/Cat-tj/altora", "Altora Market, Resto & Barbershop POS", "active", now))

        # Seed initial missions & milestones for Project Galaxy & Raphael CC
        cursor.execute("INSERT INTO company_missions VALUES (?, ?, ?, ?, ?, ?)",
                       ("m-galaxy-mvp", "proj-galaxy", "Finish Project Galaxy MVP", "2D/3D Graph visualization and live agent projection engine", "in_progress", now))
        
        milestones_galaxy = [
            ("ms-g1", "m-galaxy-mvp", "Repository & Architecture Audit", 1, "completed", now),
            ("ms-g2", "m-galaxy-mvp", "Core Graph Renderer", 2, "completed", now),
            ("ms-g3", "m-galaxy-mvp", "Project Workspace Integration", 3, "completed", now),
            ("ms-g4", "m-galaxy-mvp", "Live Agent Visualization", 4, "in_progress", None),
            ("ms-g5", "m-galaxy-mvp", "Runtime Verification", 5, "pending", None),
        ]
        for ms in milestones_galaxy:
            cursor.execute("INSERT INTO company_milestones VALUES (?, ?, ?, ?, ?, ?)", ms)

        cursor.execute("INSERT INTO company_missions VALUES (?, ?, ?, ?, ?, ?)",
                       ("m-raphael-overhaul", "proj-raphael", "Raphael Control Center Master Overhaul", "Comprehensive company control plane with warning center and agent liveness", "in_progress", now))

        milestones_raphael = [
            ("ms-r1", "m-raphael-overhaul", "Repository & Galaxy Audit", 1, "completed", now),
            ("ms-r2", "m-raphael-overhaul", "Domain Model & Hierarchy", 2, "completed", now),
            ("ms-r3", "m-raphael-overhaul", "Command Center & Warning System", 3, "in_progress", None),
            ("ms-r4", "m-raphael-overhaul", "Project Workspaces & Agents", 4, "pending", None),
            ("ms-r5", "m-raphael-overhaul", "Galaxy Integration & Verification", 5, "pending", None),
        ]
        for ms in milestones_raphael:
            cursor.execute("INSERT INTO company_milestones VALUES (?, ?, ?, ?, ?, ?)", ms)

        # Seed initial agents
        agents = [
            ("ag-raphael", "Raphael Master Agent", "Orchestrator", "GLOBAL", None, None, None, None, "WORKING", now, 12, 0, now),
            ("ag-security", "Security Auditor Agent", "Auditor", "GLOBAL", None, None, None, None, "IDLE", now, 8, 0, now),
            ("ag-gal-fe", "Galaxy Frontend Agent", "Frontend Engineer", "PROJECT", "proj-galaxy", "m-galaxy-mvp", "ms-g4", "t-viz-stream", "WORKING", now, 15, 1, now),
            ("ag-gal-be", "Galaxy Backend Agent", "Backend Engineer", "PROJECT", "proj-galaxy", "m-galaxy-mvp", "ms-g4", "t-proj-service", "WORKING", now, 18, 0, now),
            ("ag-alt-resto", "Altora Resto Agent", "POS Specialist", "PROJECT", "proj-altora", None, None, None, "IDLE", now - 300, 5, 2, now),
        ]
        for ag in agents:
            cursor.execute("INSERT INTO specialist_agents VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", ag)

    conn.commit()
    conn.close()


def get_company_hierarchy() -> dict[str, Any]:
    """Retrieve full company domain hierarchy: Pillars -> Projects -> Missions -> Milestones."""
    _init_domain_tables()
    conn = sqlite3.connect(DB_PATH, timeout=3.0)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM company_pillars ORDER BY name ASC;")
    pillars = [dict(r) for r in cursor.fetchall()]

    for p in pillars:
        cursor.execute("SELECT * FROM company_projects WHERE pillar_id = ? ORDER BY name ASC;", (p["id"],))
        projects = [dict(r) for r in cursor.fetchall()]
        
        for proj in projects:
            cursor.execute("SELECT * FROM company_missions WHERE project_id = ? ORDER BY created_at DESC;", (proj["id"],))
            missions = [dict(r) for r in cursor.fetchall()]
            
            for m in missions:
                cursor.execute("SELECT * FROM company_milestones WHERE mission_id = ? ORDER BY order_index ASC;", (m["id"],))
                m["milestones"] = [dict(r) for r in cursor.fetchall()]
                completed = sum(1 for ms in m["milestones"] if ms["status"] == "completed")
                m["milestone_summary"] = f"{completed} / {len(m['milestones'])} milestones"

            proj["missions"] = missions
            cursor.execute("SELECT * FROM specialist_agents WHERE project_id = ?;", (proj["id"],))
            proj["agents"] = [dict(r) for r in cursor.fetchall()]

        p["projects"] = projects

    cursor.execute("SELECT * FROM specialist_agents WHERE scope = 'GLOBAL';")
    global_agents = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return {
        "status": "success",
        "pillars": pillars,
        "global_agents": global_agents
    }

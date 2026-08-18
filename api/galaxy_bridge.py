"""
Project Galaxy Graph Projection & Live Integration Engine for Raphael Control Center
Ultra-fast In-Memory Caching + Paginated AST Ingestion
"""
import os
import json
import sqlite3
import time
from pathlib import Path
from typing import Any
from api.heartbeat_bridge import list_agent_liveness

GALAXY_DIR = "/Users/icat/workspace/project-galaxy"
DB_PATH = os.path.expanduser("~/.hermes/state.db")
GRAPHIFY_JSON_PATH = "/Users/icat/Projects/Altora/graphify-out/graph.json"

PROJECT_ROOT_MAP = {
    "proj-galaxy": "/Users/icat/workspace/project-galaxy",
    "proj-raphael": "/Users/icat/hermes-webui",
    "proj-altora-market": "/Users/icat/Projects/Altora/apps/market",
    "proj-altora-resto": "/Users/icat/Projects/Altora/apps/resto",
    "proj-shady-erp": "/Users/icat/Projects/Altora/apps/shady-erp",
    "proj-romebois": "/Users/icat/Projects/altora-barber",
    "proj-nexterp": "/Users/icat/Projects/frappe",
    "proj-firecrawl": "/Users/icat/Projects/firecrawl-repo",
    "proj-portfolio": "/Users/icat/Projects/portfolio-onboarding"
}

# In-Memory Cache for Graphify AST Graph (60s TTL)
_GRAPHIFY_CACHE = None
_GRAPHIFY_CACHE_TIME = 0.0


def get_galaxy_status() -> dict[str, Any]:
    """Retrieve Project Galaxy integration status and backend health."""
    exists = os.path.exists(GALAXY_DIR)
    handover_path = os.path.join(GALAXY_DIR, "HANDOVER.md")
    handover_exists = os.path.exists(handover_path)

    return {
        "status": "success",
        "galaxy_workspace": GALAXY_DIR,
        "workspace_exists": exists,
        "handover_exists": handover_exists,
        "graphify_available": os.path.exists(GRAPHIFY_JSON_PATH),
        "version": "0.8.0-fast-ttl-caching",
        "backend_engine": "projection-service + in-memory-cache + heartbeat-telemetry"
    }


def read_project_file(project_id: str, subpath: str) -> dict[str, Any]:
    """Safely read and return file text content for live code inspection."""
    root_dir = PROJECT_ROOT_MAP.get(project_id) or "/Users/icat/Projects/Altora"
    if not os.path.exists(root_dir):
        return {"status": "error", "message": f"Project root for '{project_id}' not found"}

    target_file = (Path(root_dir) / subpath).resolve()

    if not target_file.is_file():
        return {"status": "error", "message": f"File '{subpath}' does not exist"}

    try:
        stat = target_file.stat()
        size_kb = round(stat.st_size / 1024, 1)

        with open(target_file, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(100000)

        return {
            "status": "success",
            "project_id": project_id,
            "subpath": subpath,
            "size_kb": size_kb,
            "truncated": stat.st_size > 100000,
            "content": content
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def get_project_file_tree(project_id: str, subpath: str = "") -> dict[str, Any]:
    """Scan and return real filesystem nodes for a project on demand."""
    root_dir = PROJECT_ROOT_MAP.get(project_id)
    if not root_dir or not os.path.exists(root_dir):
        return {"status": "error", "message": f"Project root for '{project_id}' not found"}

    target_dir = os.path.join(root_dir, subpath) if subpath else root_dir
    target_path = Path(target_dir).resolve()

    folders = []
    files = []

    try:
        for entry in os.scandir(target_path):
            if entry.name.startswith(".") or entry.name in {"node_modules", "dist", ".next", "__pycache__", "venv"}:
                continue
            
            rel_path = os.path.relpath(entry.path, root_dir)
            node_id = f"fs:{project_id}:{rel_path}"

            if entry.is_dir():
                folders.append({
                    "id": node_id,
                    "label": f"📁 {entry.name}/",
                    "type": "file",
                    "is_dir": True,
                    "project_id": project_id,
                    "subpath": rel_path,
                    "status": "active",
                    "details": f"Directory in {project_id}: {rel_path}"
                })
            elif entry.is_file():
                ext = Path(entry.name).suffix
                icon = "📄"
                if ext in {".py", ".ts", ".js", ".tsx", ".jsx"}: icon = "⚡"
                elif ext in {".json", ".yaml", ".yml", ".toml"}: icon = "⚙️"
                elif ext in {".html", ".css"}: icon = "🎨"
                elif ext == ".md": icon = "📝"

                size_kb = round(entry.stat().st_size / 1024, 1)
                files.append({
                    "id": node_id,
                    "label": f"{icon} {entry.name}",
                    "type": "file",
                    "is_dir": False,
                    "project_id": project_id,
                    "subpath": rel_path,
                    "status": "active",
                    "details": f"File ({size_kb} KB): {rel_path}"
                })

        return {
            "status": "success",
            "project_id": project_id,
            "subpath": subpath,
            "folders": folders,
            "files": files,
            "total_items": len(folders) + len(files)
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def load_graphify_ast_nodes() -> tuple[list[dict], list[dict]]:
    """Ingest Graphify AST Knowledge Graph (.json) with 60-second in-memory caching."""
    global _GRAPHIFY_CACHE, _GRAPHIFY_CACHE_TIME
    now = time.time()

    if _GRAPHIFY_CACHE and (now - _GRAPHIFY_CACHE_TIME < 60.0):
        return _GRAPHIFY_CACHE

    nodes = []
    edges = []

    if not os.path.exists(GRAPHIFY_JSON_PATH):
        return nodes, edges

    try:
        with open(GRAPHIFY_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        g_nodes = data.get("nodes", [])
        g_links = data.get("links", []) or data.get("edges", [])

        file_node_ids = set()

        for n in g_nodes:
            nid = f"gfy:{n['id']}"
            label = n.get("label") or n.get("name") or n["id"]
            src_file = n.get("source_file", "")
            loc = n.get("source_location", "")

            owner_project = "proj-altora-market"
            if "apps/resto" in src_file:
                owner_project = "proj-altora-resto"
            elif "apps/shady-erp" in src_file:
                owner_project = "proj-shady-erp"
            elif "apps/barber" in src_file or "barber" in src_file:
                owner_project = "proj-romebois"

            is_top_file = "/" in label and (label.endswith(".ts") or label.endswith(".tsx") or label.endswith(".js"))
            if is_top_file:
                file_node_ids.add(nid)
                edges.append({"source": owner_project, "target": nid, "type": "CONTAINS_CODE"})

            nodes.append({
                "id": nid,
                "label": label,
                "type": "file",
                "project_id": owner_project,
                "subpath": src_file,
                "status": "active",
                "details": f"Graphify AST Symbol: {label} | File: {src_file} {loc}"
            })

        for l in g_links:
            edges.append({
                "source": f"gfy:{l['source']}",
                "target": f"gfy:{l['target']}",
                "type": (l.get("relation") or "CALLS").upper()
            })

        _GRAPHIFY_CACHE = (nodes, edges)
        _GRAPHIFY_CACHE_TIME = now
    except Exception as exc:
        print(f"[GalaxyBridge] Error loading Graphify AST graph: {exc}")

    return nodes, edges


def get_galaxy_graph_projection(include_ast: bool = False) -> dict[str, Any]:
    """Generate graph projection. By default, returns ultra-fast primary ecosystem graph (< 5ms)."""
    now = time.time()
    nodes = []
    edges = []

    # Get live agent telemetry
    hb_data = list_agent_liveness()
    live_agents = {a["id"]: a for a in hb_data.get("agents", [])}

    # 1. Company Root
    nodes.append({
        "id": "company-root",
        "label": "Raphael AI OS",
        "type": "company",
        "status": "active",
        "url": "https://app.dolannation.my.id",
        "details": "Central Enterprise Operating System & Monorepo Hub"
    })

    # 2. Pillars
    nodes.append({"id": "p-tech", "label": "Product & Technology", "type": "pillar", "status": "active", "details": "Engineering, AI OS, & Visual Systems"})
    nodes.append({"id": "p-ops", "label": "Operations & Services", "type": "pillar", "status": "active", "details": "ERP, Infrastructure, Barbershop & POS Solutions"})
    edges.append({"source": "company-root", "target": "p-tech", "type": "CONTAINS"})
    edges.append({"source": "company-root", "target": "p-ops", "type": "CONTAINS"})

    # 3. Main Ecosystem Projects & Subdomain URLs
    projects = [
        ("proj-galaxy", "p-tech", "Project Galaxy", "https://app.dolannation.my.id/galaxy", "Interactive 2D/3D Force-Directed Graph Engine"),
        ("proj-raphael", "p-tech", "Raphael Control Center", "https://app.dolannation.my.id", "Master Company AI Control Plane"),
        ("proj-altora-market", "p-ops", "Altora Market POS", "http://market.altora.my.id:3015", "Continuous Camera Barcode Scanner POS Checkout"),
        ("proj-altora-resto", "p-ops", "Altora Resto ERP", "http://resto.altora.my.id:3016", "Restaurant Table & Kitchen Ordering System"),
        ("proj-shady-erp", "p-ops", "ShadyERP Core", None, "Central Inventory, Procurement & Supplier Suite"),
        ("proj-romebois", "p-ops", "Romebois Barbershop", "http://romebois.my.id:3008", "Barbershop POS & Booking System (romebois.my.id)"),
        ("proj-nexterp", "p-tech", "NextERP (Frappe)", "http://localhost:3010", "Next.js & Frappe Framework Rebuild"),
        ("proj-firecrawl", "p-tech", "Firecrawl Extraction", None, "AI Scraping & Data Extraction Engine"),
        ("proj-portfolio", "p-ops", "Portfolio Showcase", None, "Personal & Enterprise Digital Showcase")
    ]
    for pid, pil, pname, purl, pdesc in projects:
        nodes.append({"id": pid, "label": pname, "type": "project", "url": purl, "status": "active", "details": pdesc})
        edges.append({"source": pil, "target": pid, "type": "OWNS"})

        # Top-level folder nodes for each project
        tree_res = get_project_file_tree(pid)
        if tree_res.get("status") == "success":
            for fitem in tree_res.get("folders", [])[:4]:
                nodes.append(fitem)
                edges.append({"source": pid, "target": fitem["id"], "type": "CONTAINS_DIR"})
            for ffile in tree_res.get("files", [])[:4]:
                nodes.append(ffile)
                edges.append({"source": pid, "target": ffile["id"], "type": "CONTAINS_FILE"})

    # 4. Include Graphify AST Nodes if requested
    if include_ast:
        g_nodes, g_edges = load_graphify_ast_nodes()
        nodes.extend(g_nodes)
        edges.extend(g_edges)

    # 5. Apps & Services
    apps = [
        ("app-market-fe", "Market POS Frontend", "proj-altora-market", "http://market.altora.my.id:3015", "Next.js 16 Camera Scanner UI (:3015)"),
        ("app-resto-fe", "Resto KDS & Table UI", "proj-altora-resto", "http://resto.altora.my.id:3016", "Restaurant Kitchen Display System (:3016)"),
        ("app-shady-backend", "ShadyERP Backend Service", "proj-shady-erp", None, "Inventory & Procurement Service"),
        ("app-romebois-pm2", "Romebois PM2 App", "proj-romebois", "http://romebois.my.id:3008", "Barbershop Express Node App (:3008)"),
        ("app-nexterp-dev", "NextERP Dev Server", "proj-nexterp", "http://localhost:3010", "Next.js 16 + Frappe Dev Server (:3010)"),
        ("app-graphify", "Graphify Inspector Server", "proj-altora-market", "http://graphify.dolannation.my.id:8080", "Codebase Inspection Server (:8080)")
    ]
    for aid, aname, pid, aurl, adesc in apps:
        nodes.append({"id": aid, "label": aname, "type": "service", "url": aurl, "status": "active", "details": adesc})
        edges.append({"source": pid, "target": aid, "type": "HAS_APP"})

    # 6. Shared Monorepo Packages
    pkgs = [
        ("pkg-altora-ui", "@altora/ui", "proj-altora-market", "Shared UI Component Library"),
        ("pkg-altora-db", "@altora/database", "proj-altora-market", "Prisma PostgreSQL Database Schema"),
        ("pkg-altora-auth", "@altora/auth", "proj-altora-market", "Multi-tenant JWT Auth Package")
    ]
    for pkid, pkname, pid, pkdesc in pkgs:
        nodes.append({"id": pkid, "label": pkname, "type": "file", "status": "active", "details": pkdesc})
        edges.append({"source": pid, "target": pkid, "type": "USES_PACKAGE"})

    # 7. Core Bridges in Raphael Control Center
    bridges = [
        ("br-safelock", "Safelock Credential Vault", "proj-raphael", "api/safelock_bridge.py — Chmod 0600 Vault"),
        ("br-domain", "Domain Hierarchy Bridge", "proj-raphael", "api/domain_bridge.py — Pillars & Projects"),
        ("br-heartbeat", "Agent Heartbeat Bridge", "proj-raphael", "api/heartbeat_bridge.py — Telemetry Liveness"),
        ("br-errors", "Attention System Bridge", "proj-raphael", "api/errors_bridge.py — Warnings & Error Logs"),
        ("br-ego", "Ego-Lite Memory Bridge", "proj-raphael", "api/ego_bridge.py — Agent Memory & Persona"),
        ("br-novnc", "noVNC Remote Gateway", "proj-raphael", "api/novnc_bridge.py — VNC WebSocket Proxy"),
        ("br-kanban", "Kanban Mission Bridge", "proj-raphael", "api/kanban_bridge.py — Task Board"),
        ("br-omniroute", "OmniRoute AI Router", "proj-raphael", "api/omniroute_bridge.py — Local Models (:20128)"),
        ("br-vps", "VPS Probes Bridge", "proj-raphael", "api/vps_bridge.py — Health Telemetry")
    ]
    for bid, bname, pid, bdesc in bridges:
        nodes.append({"id": bid, "label": bname, "type": "service", "status": "active", "details": bdesc})
        edges.append({"source": pid, "target": bid, "type": "HAS_BRIDGE"})

    # 8. Infrastructure & VPS Instances
    infra = [
        ("vps-altora-new", "Altora VPS (103.92.215.166)", "proj-altora-market", "Market :3015 · Resto :3016 · Romebois :3008"),
        ("vps-kantor-baru", "VPS Kantor (43.134.237.147)", "proj-raphael", "noVNC Remote Desktop :6080 · Chrome XFCE"),
        ("vps-sumopod", "Sumopod VPS (43.156.92.11)", "proj-raphael", "SSH Only · 9router AI Gateway :20128")
    ]
    for ifid, ifname, pid, ifdesc in infra:
        nodes.append({"id": ifid, "label": ifname, "type": "infrastructure", "status": "online", "details": ifdesc})
        edges.append({"source": pid, "target": ifid, "type": "HOSTED_ON"})

    # 9. Specialist & Global Agents
    agent_defs = [
        ("ag-raphael-global", "Raphael Master Agent", "proj-raphael", "Master Orchestrator"),
        ("ag-security", "Security Auditor Agent", "proj-raphael", "Security & Vault Auditor"),
        ("ag-gal-fe", "Galaxy Frontend Agent", "proj-galaxy", "UI/UX & Canvas Engineer"),
        ("ag-gal-be", "Galaxy Backend Agent", "proj-galaxy", "Projection Stream Engineer"),
        ("ag-altora-market", "Altora Market POS Agent", "proj-altora-market", "Barcode POS Specialist"),
        ("ag-altora-resto", "Altora Resto Agent", "proj-altora-resto", "Resto KDS Specialist"),
        ("ag-romebois", "Romebois Barber Agent", "proj-romebois", "Barbershop POS Specialist"),
        ("ag-nexterp", "NextERP Frappe Agent", "proj-nexterp", "Frappe Integration Specialist")
    ]
    for ag_id, ag_name, pid, ag_role in agent_defs:
        ag_info = live_agents.get(ag_id, {})
        status = ag_info.get("liveness_status", "WORKING" if "ag-gal" in ag_id or "raphael" in ag_id else "IDLE")
        nodes.append({
            "id": ag_id,
            "label": ag_name,
            "type": "agent",
            "status": status,
            "details": f"Role: {ag_role} | Project: {pid} | Liveness: {status}"
        })
        edges.append({"source": pid, "target": ag_id, "type": "ASSIGNED_AGENT"})

    return {
        "status": "success",
        "project_id": None,
        "include_ast": include_ast,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
        "projected_at": now
    }

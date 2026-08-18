"""Unified Overview Dashboard Bridge for Hermes AIOS Control Plane."""
import os
import sqlite3
import time
import socket
import urllib.request
from typing import Any


def _probe_tcp_service(host: str, port: int, timeout: float = 1.0) -> tuple[str, float]:
    """Perform a live TCP port probe."""
    start = time.time()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        latency = round((time.time() - start) * 1000, 1)
        if result == 0:
            return "online", latency
        return "offline", latency
    except Exception:
        return "unknown", 0.0


def get_system_overview() -> dict[str, Any]:
    """Gather live observed status across local host, databases, subagents, and probed services."""
    now = time.time()
    
    # 1. VPS Nodes Metrics & Probes
    vps_targets = [
        {"name": "Local Mac Host", "ip": "127.0.0.1", "port": 8787},
        {"name": "VPS Kantor Baru", "ip": "43.134.237.147", "port": 6080},
        {"name": "Altora VPS Production", "ip": "103.92.215.166", "port": 3015}
    ]

    vps_nodes = []
    online_nodes = 0
    for v in vps_targets:
        st, lat = _probe_tcp_service(v["ip"], v["port"])
        if st == "online":
            online_nodes += 1
        vps_nodes.append({
            "name": v["name"],
            "ip": v["ip"],
            "status": st,
            "latency_ms": lat,
            "observed_at": now
        })

    # 2. Live Observed Product Services
    raw_services = [
        {"name": "Hermes AIOS WebUI", "domain": "127.0.0.1", "port": 8787},
        {"name": "OmniRoute Router", "domain": "127.0.0.1", "port": 20128},
        {"name": "Graphify Knowledge Graph", "domain": "127.0.0.1", "port": 8790}
    ]

    services = []
    online_count = 0
    for svc in raw_services:
        status, latency = _probe_tcp_service(svc["domain"], svc["port"])
        if status == "online":
            online_count += 1
        services.append({
            "name": svc["name"],
            "domain": svc["domain"],
            "port": svc["port"],
            "status": status,
            "latency_ms": latency,
            "observed_at": now
        })

    # 3. Active Subagents & Swarms
    db_path = os.path.expanduser("~/.hermes/state.db")
    active_subagents = 0
    total_delegations = 0
    db_healthy = False
    state_db_size = 0.0

    if os.path.exists(db_path):
        try:
            state_db_size = round(os.path.getsize(db_path) / (1024 * 1024), 2)
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=2.0)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM async_delegations WHERE state IN ('running', 'in_progress');")
            active_subagents = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM async_delegations;")
            total_delegations = cursor.fetchone()[0]
            conn.close()
            db_healthy = True
        except Exception:
            db_healthy = False

    # 4. Observed Databases Overview
    databases = [
        {
            "name": "Hermes State DB",
            "path": "~/.hermes/state.db",
            "status": "healthy" if db_healthy else "degraded",
            "size_mb": state_db_size
        }
    ]

    return {
        "status": "success",
        "timestamp": now,
        "summary": {
            "total_nodes": len(vps_nodes),
            "online_nodes": online_nodes,
            "total_services": len(services),
            "online_services": online_count,
            "active_subagents": active_subagents,
            "total_delegations": total_delegations
        },
        "vps_nodes": vps_nodes,
        "services": services,
        "databases": databases,
        "network": {
            "primary_domain": "dolannation.my.id",
            "tunnel_status": "active"
        }
    }

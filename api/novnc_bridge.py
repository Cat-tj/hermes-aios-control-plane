"""noVNC Remote Desktop & VNC Gateway Bridge for Hermes AIOS Control Plane."""
import os
import json
import sqlite3
import time
from typing import Any

DB_PATH = os.path.expanduser("~/.hermes/state.db")


def _init_novnc_table():
    """Ensure novnc_servers table exists in state.db."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS novnc_servers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                host TEXT NOT NULL,
                port INTEGER DEFAULT 5900,
                ws_port INTEGER DEFAULT 6080,
                path TEXT DEFAULT '/websockify',
                requires_auth INTEGER DEFAULT 1,
                target_type TEXT DEFAULT 'office_server',
                status TEXT DEFAULT 'configured',
                updated_at REAL
            );
        """)
        conn.commit()

        # Seed default office server entry if empty
        cursor.execute("SELECT COUNT(*) FROM novnc_servers;")
        count = cursor.fetchone()[0]
        if count == 0:
            now = time.time()
            default_servers = [
                ("srv_office_main", "Server VPS Kantor Baru (43.134.237.147)", "43.134.237.147", 5901, 6080, "/vnc.html", 1, "office_server", "ready", now),
                ("srv_altora_vps", "Altora VPS Production (103.92.215.166)", "103.92.215.166", 5901, 6081, "/websockify", 1, "vps", "configured", now),
                ("srv_local_mac", "Local Mac Screen Share", "127.0.0.1", 5900, 6080, "/websockify", 0, "local", "ready", now)
            ]
            cursor.executemany("""
                INSERT INTO novnc_servers (id, name, host, port, ws_port, path, requires_auth, target_type, status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, default_servers)
            conn.commit()

        conn.close()
    except Exception as exc:
        print(f"[noVNCBridge] Table init error: {exc}")


_init_novnc_table()


def list_novnc_servers() -> dict[str, Any]:
    """Retrieve configured VNC/noVNC servers."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM novnc_servers ORDER BY updated_at DESC;")
        rows = cursor.fetchall()
        servers = [dict(r) for r in rows]
        conn.close()

        return {
            "status": "success",
            "servers": servers
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def save_novnc_server(data: dict[str, Any]) -> dict[str, Any]:
    """Create or update a noVNC server configuration."""
    server_id = data.get("id") or f"srv_{int(time.time() * 1000)}"
    name = data.get("name", "New Office VNC Server")
    host = data.get("host", "127.0.0.1")
    port = int(data.get("port", 5900))
    ws_port = int(data.get("ws_port", 6080))
    path = data.get("path", "/websockify")
    requires_auth = 1 if data.get("requires_auth", True) else 0
    target_type = data.get("target_type", "office_server")
    now = time.time()

    try:
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO novnc_servers (id, name, host, port, ws_port, path, requires_auth, target_type, status, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ready', ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                host=excluded.host,
                port=excluded.port,
                ws_port=excluded.ws_port,
                path=excluded.path,
                requires_auth=excluded.requires_auth,
                target_type=excluded.target_type,
                status='ready',
                updated_at=excluded.updated_at;
        """, (server_id, name, host, port, ws_port, path, requires_auth, target_type, now))
        conn.commit()
        conn.close()

        return {
            "status": "success",
            "server_id": server_id,
            "message": "noVNC server configuration saved"
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}

"""
Omniroute Bridge API for Hermes Web UI / Ultimate AI OS
"""
import os
import json
import sqlite3
import urllib.request
from api.helpers import j, bad

OMNIROUTE_DIR = os.path.expanduser('~/.omniroute')
OMNIROUTE_DB = os.path.join(OMNIROUTE_DIR, 'storage.sqlite')
OMNIROUTE_ENV = os.path.join(OMNIROUTE_DIR, '.env')

def get_omniroute_status(handler):
    """Get Omniroute running status, active models & providers."""
    db_exists = os.path.exists(OMNIROUTE_DB)
    server_online = False
    
    try:
        req = urllib.request.Request('http://127.0.0.1:20128/v1/models', headers={'User-Agent': 'AI-OS-Bridge'})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            if resp.status == 200:
                server_online = True
    except Exception:
        server_online = False

    models_count = 0
    providers = []
    if db_exists:
        try:
            conn = sqlite3.connect(OMNIROUTE_DB)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            if 'models' in tables:
                cursor.execute("SELECT COUNT(*) FROM models")
                models_count = cursor.fetchone()[0]
            if 'provider_connections' in tables:
                cursor.execute("SELECT id, provider, auth_type, name, is_active, test_status FROM provider_connections")
                for row in cursor.fetchall():
                    providers.append({
                        "id": row[0],
                        "provider": row[1],
                        "auth_type": row[2],
                        "name": row[3],
                        "is_active": bool(row[4]),
                        "status": row[5] or "active"
                    })
            conn.close()
        except Exception:
            pass

    return j(handler, {
        "status": "online" if server_online else "local_only",
        "server_online": server_online,
        "database_connected": db_exists,
        "models_count": models_count,
        "providers": providers,
        "port": 20128,
        "claude_code": {
            "version": "2.1.233",
            "integrated": True,
            "vps_kantor": "http://43.134.237.147:20128/v1",
            "vps_altora": "103.92.215.166 (hermes user)",
            "models": ["claude-opus-5", "claude-sonnet-5", "auto/best-coding"]
        }
    })

def get_omniroute_config(handler):
    """Get non-sensitive Omniroute config summary."""
    config_info = {"env_exists": os.path.exists(OMNIROUTE_ENV)}
    if config_info["env_exists"]:
        try:
            with open(OMNIROUTE_ENV, 'r') as f:
                lines = f.readlines()
                config_info["keys_configured"] = [
                    line.split('=')[0].strip() for line in lines if '=' in line and not line.startswith('#')
                ]
        except Exception as e:
            config_info["error"] = str(e)
    return j(handler, config_info)


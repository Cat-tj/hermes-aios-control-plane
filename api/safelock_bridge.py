"""
SafeLock Credentials Bridge API for Hermes Web UI
"""
import os
from api.helpers import j, bad

SAFELOCK_DIR = os.path.expanduser('~/.hermes/safelock')
CREDS_FILE = os.path.join(SAFELOCK_DIR, 'creds.md')

def _ensure_safelock_exists():
    if not os.path.exists(SAFELOCK_DIR):
        os.makedirs(SAFELOCK_DIR, mode=0o700, exist_ok=True)
    if not os.path.exists(CREDS_FILE):
        default_content = """# SafeLock Server Credentials & Secrets

This file stores server access details for Hermes AI OS.
Ensure sensitive variables are populated via environment variables or secure key vaults.

## Managed Node Reference
- VPS Nodes: Configured via environment / Tailscale authentication.
- API Integrations: Configured via local secrets manager.
"""
        with open(CREDS_FILE, 'w', encoding='utf-8') as f:
            f.write(default_content)
        os.chmod(CREDS_FILE, 0o600)

def get_safelock_creds(handler):
    """Read creds.md content safely."""
    _ensure_safelock_exists()
    try:
        with open(CREDS_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        return j(handler, {"status": "success", "content": content, "filepath": CREDS_FILE})
    except Exception as e:
        return bad(handler, str(e), 500)

def save_safelock_creds(handler, body):
    """Save updated creds.md content safely."""
    _ensure_safelock_exists()
    if not isinstance(body, dict):
        return bad(handler, "Invalid JSON body", 400)
    new_content = body.get('content')
    if new_content is None:
        return bad(handler, "Missing content field", 400)
    try:
        with open(CREDS_FILE, 'w', encoding='utf-8') as f:
            f.write(str(new_content))
        os.chmod(CREDS_FILE, 0o600)
        return j(handler, {"status": "success", "message": "Credentials updated successfully"})
    except Exception as e:
        return bad(handler, str(e), 500)

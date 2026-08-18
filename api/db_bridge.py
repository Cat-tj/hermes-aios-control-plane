"""
Safe Read-Only Database Explorer Bridge for Hermes Web UI
"""
import os
import sqlite3
import time
from typing import Any

KNOWN_DBS = {
    "hermes_state": {
        "name": "Hermes Core State DB",
        "path": os.path.expanduser("~/.hermes/state.db")
    },
    "omniroute": {
        "name": "OmniRoute Storage DB",
        "path": os.path.expanduser("~/.omniroute/storage.sqlite")
    },
    "webui_sessions": {
        "name": "WebUI Sessions DB",
        "path": os.path.expanduser("~/.hermes/webui/webui_session_db.sqlite")
    }
}

MAX_QUERY_LEN = 2000
MAX_ROWS = 100
MAX_CELL_BYTES = 50000


def get_db_list() -> dict[str, Any]:
    """Return available read-only databases."""
    available = []
    for db_id, info in KNOWN_DBS.items():
        exists = os.path.exists(info["path"])
        size_mb = round(os.path.getsize(info["path"]) / (1024 * 1024), 2) if exists else 0
        available.append({
            "id": db_id,
            "name": info["name"],
            "path": info["path"],
            "exists": exists,
            "size_mb": size_mb
        })
    return {"status": "success", "databases": available}


def get_db_schema(db_id: str) -> dict[str, Any]:
    """Retrieve schema and tables using read-only URI mode."""
    if db_id not in KNOWN_DBS:
        return {"status": "error", "message": f"Database '{db_id}' not found"}

    db_path = KNOWN_DBS[db_id]["path"]
    if not os.path.exists(db_path):
        return {"status": "error", "message": f"Database file missing: {db_path}"}

    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=3.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
        tables_data = cursor.fetchall()
        
        tables = []
        for row in tables_data:
            table_name = row["name"]
            col_cursor = conn.cursor()
            col_cursor.execute(f"PRAGMA table_info('{table_name}');")
            cols = [{"name": c["name"], "type": c["type"], "notnull": c["notnull"]} for c in col_cursor.fetchall()]
            
            count_cursor = conn.cursor()
            try:
                count_cursor.execute(f"SELECT COUNT(*) FROM '{table_name}';")
                row_count = count_cursor.fetchone()[0]
            except Exception:
                row_count = 0
                
            tables.append({
                "name": table_name,
                "columns": cols,
                "row_count": row_count
            })
            
        conn.close()
        return {
            "status": "success",
            "db_id": db_id,
            "db_name": KNOWN_DBS[db_id]["name"],
            "tables": tables
        }
    except Exception as exc:
        return {"status": "error", "message": f"Failed to read schema: {str(exc)}"}


def execute_safe_query(db_id: str, query: str, limit: int = MAX_ROWS) -> dict[str, Any]:
    """Execute a safe, resource-bounded read-only SELECT query."""
    if db_id not in KNOWN_DBS:
        return {"status": "error", "message": f"Database '{db_id}' not found"}

    if not query or len(query) > MAX_QUERY_LEN:
        return {"status": "error", "message": f"Query exceeds maximum length of {MAX_QUERY_LEN} characters"}

    clean_query = query.strip()
    upper_query = clean_query.upper()

    # Strictly reject PRAGMA, ATTACH, DETACH, VACUUM, DDL, and multi-statements
    if ";" in clean_query[:-1] or ";" in clean_query.rstrip()[:-1]:
        return {"status": "error", "message": "Multiple SQL statements are not permitted"}

    forbidden_keywords = ["PRAGMA", "ATTACH", "DETACH", "VACUUM", "REINDEX", "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "GRANT"]
    for kw in forbidden_keywords:
        if kw in upper_query.split():
            return {"status": "error", "message": f"Keyword '{kw}' is not permitted in read-only queries"}

    if not (upper_query.startswith("SELECT") or upper_query.startswith("EXPLAIN QUERY PLAN SELECT")):
        return {"status": "error", "message": "Only single SELECT or EXPLAIN QUERY PLAN SELECT queries are permitted"}

    db_path = KNOWN_DBS[db_id]["path"]
    if not os.path.exists(db_path):
        return {"status": "error", "message": f"Database file missing: {db_path}"}

    start_time = time.time()
    op_count = [0]

    def _progress_callback():
        op_count[0] += 1000
        if op_count[0] > 100000 or (time.time() - start_time) > 2.0:
            return 1 # Abort query execution
        return 0

    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=3.0)
        conn.set_progress_handler(_progress_callback, 1000)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(clean_query)
        rows_data = cursor.fetchmany(min(limit, MAX_ROWS))
        
        columns = [description[0] for description in cursor.description] if cursor.description else []
        rows = []
        for row in rows_data:
            row_dict = {}
            for col in columns:
                val = row[col]
                if isinstance(val, (str, bytes)) and len(val) > MAX_CELL_BYTES:
                    val = str(val)[:MAX_CELL_BYTES] + "… [TRUNCATED]"
                row_dict[col] = val
            rows.append(row_dict)
        
        conn.close()
        return {
            "status": "success",
            "db_id": db_id,
            "columns": columns,
            "row_count": len(rows),
            "execution_time_ms": round((time.time() - start_time) * 1000, 2),
            "rows": rows
        }
    except Exception as exc:
        return {"status": "error", "message": f"Query execution failed: {str(exc)}"}

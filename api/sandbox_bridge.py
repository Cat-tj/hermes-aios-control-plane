"""
Safe Code & HTML Preview Sandbox Bridge for Hermes Web UI
"""
import html
from api.helpers import t, bad

def render_sandbox_preview(handler, code_input: str):
    """Safely render HTML previews without Reflected XSS execution."""
    if not code_input:
        return bad(handler, "No code provided for preview", 400)
    
    escaped_code = html.escape(code_input)
    safe_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Sandbox Code Preview</title>
    <style>
        body {{ font-family: monospace; background: #0d1117; color: #e8e8f0; padding: 20px; }}
        pre {{ background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px; overflow-x: auto; }}
    </style>
</head>
<body>
    <h3>Code Preview (Escaped)</h3>
    <pre>{escaped_code}</pre>
</body>
</html>"""
    return t(handler, safe_html, content_type='text/html; charset=utf-8')

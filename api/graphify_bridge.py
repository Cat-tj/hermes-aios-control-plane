"""
Graphify Bridge API for Hermes Web UI / Ultimate AI OS
"""
import os
import json
import glob
from urllib.parse import parse_qs
from api.helpers import j, bad, t

PROJECTS_DIR = os.path.expanduser('~/Projects')
ALTORA_GRAPHIFY = os.path.expanduser('~/Projects/Altora/graphify-out')

def list_graphify_projects(handler):
    """Find all projects with graphify output."""
    results = []
    pattern = os.path.join(PROJECTS_DIR, '*', 'graphify-out', 'manifest.json')
    for manifest_path in glob.glob(pattern):
        folder = os.path.dirname(manifest_path)
        project_name = os.path.basename(os.path.dirname(folder))
        results.append({
            "project": project_name,
            "path": folder,
            "has_graph_json": os.path.exists(os.path.join(folder, 'graph.json')),
            "has_graph_html": os.path.exists(os.path.join(folder, 'graph.html')),
            "has_report": os.path.exists(os.path.join(folder, 'GRAPH_REPORT.md'))
        })
    
    # Also check Altora directly if present
    if os.path.exists(ALTORA_GRAPHIFY) and not any(r["project"] == "Altora" for r in results):
        results.append({
            "project": "Altora",
            "path": ALTORA_GRAPHIFY,
            "has_graph_json": os.path.exists(os.path.join(ALTORA_GRAPHIFY, 'graph.json')),
            "has_graph_html": os.path.exists(os.path.join(ALTORA_GRAPHIFY, 'graph.html')),
            "has_report": os.path.exists(os.path.join(ALTORA_GRAPHIFY, 'GRAPH_REPORT.md'))
        })

    return j(handler, {"projects": results})

def get_graphify_data(handler, parsed):
    """Get graph.json content for visualizer."""
    qs = parse_qs(parsed.query or '')
    project = qs.get('project', ['Altora'])[0]
    project_graph_dir = os.path.join(PROJECTS_DIR, project, 'graphify-out')
    if not os.path.exists(project_graph_dir):
        project_graph_dir = ALTORA_GRAPHIFY
        
    graph_json_path = os.path.join(project_graph_dir, 'graph.json')
    if os.path.exists(graph_json_path):
        try:
            with open(graph_json_path, 'r') as f:
                data = json.load(f)
                return j(handler, {"status": "success", "project": project, "data": data})
        except Exception as e:
            return bad(handler, str(e), 500)
            
    return bad(handler, "Graphify output not found for project", 404)

def embed_graphify_html(handler, parsed):
    """Serve standalone graph.html."""
    qs = parse_qs(parsed.query or '')
    project = qs.get('project', ['Altora'])[0]
    project_graph_dir = os.path.join(PROJECTS_DIR, project, 'graphify-out')
    if not os.path.exists(project_graph_dir):
        project_graph_dir = ALTORA_GRAPHIFY
        
    html_path = os.path.join(project_graph_dir, 'graph.html')
    if os.path.exists(html_path):
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return t(handler, content, content_type='text/html; charset=utf-8')
        except Exception as e:
            return bad(handler, str(e), 500)
        
    return bad(handler, "Graphify HTML not found", 404)


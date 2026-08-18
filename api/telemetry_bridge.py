"""
Telemetry Bridge API for Omniroute & Hermes AI OS
"""
import os
import json
import glob
import sqlite3
from api.helpers import j, bad

OMNIROUTE_DIR = os.path.expanduser('~/.omniroute')
CALL_LOGS_DIR = os.path.join(OMNIROUTE_DIR, 'call_logs')
OMNIROUTE_DB = os.path.join(OMNIROUTE_DIR, 'storage.sqlite')

def get_telemetry_stats(handler):
    """Aggregate token usage, latency, model distribution, and savings."""
    total_tokens_in = 0
    total_tokens_out = 0
    total_calls = 0
    models_usage = {}
    recent_latencies = []
    
    # Read call logs from today and recent days
    log_files = glob.glob(os.path.join(CALL_LOGS_DIR, '*', '*.json'))
    # Limit to recent 200 log files for quick calculation
    log_files.sort(key=os.path.getmtime, reverse=True)
    recent_files = log_files[:200]
    
    for filepath in recent_files:
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                summary = data.get('summary', {})
                model = summary.get('model', 'unknown')
                duration = summary.get('duration', 0)
                tokens = summary.get('tokens', {})
                
                in_tok = tokens.get('in', 0) or 0
                out_tok = tokens.get('out', 0) or 0
                
                total_calls += 1
                total_tokens_in += in_tok
                total_tokens_out += out_tok
                
                if model not in models_usage:
                    models_usage[model] = 0
                models_usage[model] += 1
                
                if duration > 0:
                    recent_latencies.append(duration)
        except Exception:
            continue
            
    avg_latency = round(sum(recent_latencies) / len(recent_latencies)) if recent_latencies else 0
    
    # Calculate estimated cost savings vs $0.003/1k tokens standard API
    estimated_savings_usd = round(((total_tokens_in + total_tokens_out) / 1000) * 0.003, 4)
    
    return j(handler, {
        "status": "success",
        "total_calls": total_calls,
        "total_tokens_in": total_tokens_in,
        "total_tokens_out": total_tokens_out,
        "total_tokens": total_tokens_in + total_tokens_out,
        "avg_latency_ms": avg_latency,
        "estimated_savings_usd": estimated_savings_usd,
        "models_distribution": models_usage
    })

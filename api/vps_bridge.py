"""VPS & Infrastructure Health Bridge for Hermes Web UI."""
import socket
import ssl
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from typing import Any
from api.system_health import build_system_health_payload


def _check_tcp(host: str, port: int, timeout: float = 2.5) -> dict[str, Any]:
    start = time.time()
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        latency = int((time.time() - start) * 1000)
        return {"status": "online", "latency_ms": latency}
    except Exception as exc:
        latency = int((time.time() - start) * 1000)
        return {"status": "offline", "latency_ms": latency, "error": str(exc)}


def _check_http(url: str, timeout: float = 3.0) -> dict[str, Any]:
    start = time.time()
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = Request(
            url,
            headers={"User-Agent": "Hermes-VPS-Monitor/1.0"},
        )
        with urlopen(req, timeout=timeout, context=ctx) as resp:
            latency = int((time.time() - start) * 1000)
            return {
                "status": "online",
                "code": resp.status,
                "latency_ms": latency,
            }
    except HTTPError as exc:
        latency = int((time.time() - start) * 1000)
        # 2xx, 3xx, 401, 404, 405 are active HTTP endpoints
        if exc.code in {200, 301, 302, 307, 308, 401, 404, 405, 429}:
            return {
                "status": "online",
                "code": exc.code,
                "latency_ms": latency,
            }
        return {"status": "degraded", "code": exc.code, "latency_ms": latency}
    except Exception as exc:
        latency = int((time.time() - start) * 1000)
        return {"status": "offline", "latency_ms": latency, "error": str(exc)}


def build_vps_status_payload() -> dict[str, Any]:
    local_system = build_system_health_payload()
    
    nodes = [
        {
            "id": "vps-altora",
            "name": "Altora Production VPS",
            "ip": "103.92.215.166",
            "role": "Monorepo & App Host (Market, Resto, Romebois)",
            "services": [
                {
                    "name": "Altora Market",
                    "domain": "market.altora.my.id",
                    "port": 3015,
                    "target": "https://market.altora.my.id",
                    "result": _check_http("https://market.altora.my.id"),
                },
                {
                    "name": "Altora Resto",
                    "domain": "resto.altora.my.id",
                    "port": 3016,
                    "target": "https://resto.altora.my.id",
                    "result": _check_http("https://resto.altora.my.id"),
                },
                {
                    "name": "Romebois Barbershop",
                    "domain": "romebois.my.id",
                    "port": 3008,
                    "target": "https://romebois.my.id",
                    "result": _check_http("https://romebois.my.id"),
                },
            ],
        },
        {
            "id": "vps-sumopod",
            "name": "Sumopod AI Proxy VPS",
            "ip": "43.156.92.11",
            "role": "AI Gateway & 9router Host",
            "services": [
                {
                    "name": "SSH Control Port",
                    "domain": "43.156.92.11:22",
                    "port": 22,
                    "target": "tcp://43.156.92.11:22",
                    "result": _check_tcp("43.156.92.11", 22),
                },
            ],
        },
        {
            "id": "node-dolannation",
            "name": "Dolannation AI & Core Services",
            "ip": "Localhost / Cloudflare Tunnel",
            "role": "Hermes Web UI, Graphify MCP, OmniRoute",
            "services": [
                {
                    "name": "Hermes Web UI",
                    "domain": "app.dolannation.my.id",
                    "port": 8787,
                    "target": "http://127.0.0.1:8787",
                    "result": _check_http("http://127.0.0.1:8787"),
                },
                {
                    "name": "Hermes Dashboard",
                    "domain": "hermes.dolannation.my.id",
                    "port": 9119,
                    "target": "http://127.0.0.1:9119",
                    "result": _check_http("http://127.0.0.1:9119"),
                },
                {
                    "name": "Graphify Knowledge Graph MCP",
                    "domain": "graphify.dolannation.my.id",
                    "port": 8080,
                    "target": "http://127.0.0.1:8080/mcp",
                    "result": _check_http("http://127.0.0.1:8080/mcp"),
                },
                {
                    "name": "OmniRoute AI Engine",
                    "domain": "omniroute.dolannation.my.id",
                    "port": 20128,
                    "target": "http://127.0.0.1:20128",
                    "result": _check_http("http://127.0.0.1:20128"),
                },
                {
                    "name": "API Service",
                    "domain": "api.dolannation.my.id",
                    "port": 3000,
                    "target": "http://127.0.0.1:3000",
                    "result": _check_http("http://127.0.0.1:3000"),
                },
            ],
        },
    ]

    total_services = sum(len(n["services"]) for n in nodes)
    online_services = sum(
        1 for n in nodes for s in n["services"] if s["result"].get("status") == "online"
    )

    return {
        "status": "ok" if online_services == total_services else "degraded" if online_services > 0 else "offline",
        "checked_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "summary": {
            "total_nodes": len(nodes),
            "total_services": total_services,
            "online_services": online_services,
            "offline_services": total_services - online_services,
        },
        "system": local_system,
        "nodes": nodes,
    }

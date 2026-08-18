"""
Integration Hub & Public API Registry Bridge for Raphael Control Center
"""
import os
import json
import sqlite3
import time
from typing import Any

DB_PATH = os.path.expanduser("~/.hermes/state.db")

PUBLIC_APIS_CATALOG = [
    {
        "id": "api-open-ai",
        "name": "OpenAI API",
        "category": "Artificial Intelligence",
        "description": "GPT-4o, DALL-E, & Whisper models for text generation, speech, and vision.",
        "auth": "apiKey",
        "https": True,
        "cors": "yes",
        "link": "https://platform.openai.com/docs/api-reference"
    },
    {
        "id": "api-huggingface",
        "name": "Hugging Face Hub API",
        "category": "Machine Learning",
        "description": "Access 100,000+ open-source ML models, datasets, and inference endpoints.",
        "auth": "apiKey",
        "https": True,
        "cors": "yes",
        "link": "https://huggingface.co/docs/api-inference/index"
    },
    {
        "id": "api-cloudflare",
        "name": "Cloudflare Tunnel & Access API",
        "category": "Infrastructure & Security",
        "description": "Manage DNS, Cloudflare Tunnels, Zero Trust policies, and Workers programmatically.",
        "auth": "apiKey",
        "https": True,
        "cors": "yes",
        "link": "https://developers.cloudflare.com/api/"
    },
    {
        "id": "api-github",
        "name": "GitHub REST & GraphQL API",
        "category": "Development & CI/CD",
        "description": "Interact with repositories, pull requests, issues, actions, and workflows.",
        "auth": "OAuth",
        "https": True,
        "cors": "yes",
        "link": "https://docs.github.com/en/rest"
    },
    {
        "id": "api-tailscale",
        "name": "Tailscale API",
        "category": "Networking & Mesh",
        "description": "Manage devices, ACLs, auth keys, and Tailnet mesh network status.",
        "auth": "apiKey",
        "https": True,
        "cors": "yes",
        "link": "https://tailscale.com/api"
    },
    {
        "id": "api-duckduckgo",
        "name": "DuckDuckGo Instant Answer API",
        "category": "Search & Data",
        "description": "Zero-click searches, definitions, web search results, and instant answers.",
        "auth": "No",
        "https": True,
        "cors": "yes",
        "link": "https://duckduckgo.com/api"
    }
]


def get_public_apis_registry(category_filter: str = None) -> dict[str, Any]:
    """Retrieve public API registry entries from GitHub Public APIs catalog."""
    apis = PUBLIC_APIS_CATALOG
    if category_filter:
        apis = [a for a in apis if a["category"].lower() == category_filter.lower()]
        
    return {
        "status": "success",
        "source": "https://github.com/public-apis/public-apis",
        "count": len(apis),
        "apis": apis
    }

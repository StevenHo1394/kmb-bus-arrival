#!/usr/bin/env python3
"""
KMB Bus Arrival Skill v1.1.6
- Plain text output for getNextArrivals; other tools return JSON
- Auto-direction + alternate stop ID fallback
- Pure Python; security-hardened; no external deps
"""

import json, sys, time, os, re, urllib.request, urllib.error
from datetime import datetime

BASE = "https://data.etabus.gov.hk/v1/transport/kmb"

ROUTE_PATTERN = re.compile(r'^[A-Za-z0-9]+$')
DIRECTION_PATTERN = re.compile(r'^(O|I|outbound|inbound)$', re.IGNORECASE)
STOP_ID_PATTERN = re.compile(r'^[A-Za-z0-9]{1,16}$')

def validate_route(route):
    if not isinstance(route, str) or not ROUTE_PATTERN.match(route):
        raise ValueError("Invalid route")

def validate_direction(direction):
    if not isinstance(direction, str):
        raise ValueError("Direction must be a string")
    if direction.lower() == 'auto':
        return 'auto'
    if not DIRECTION_PATTERN.match(direction):
        raise ValueError("Invalid direction")
    d = direction.upper()
    if d == 'OUTBOUND': return 'O'
    if d == 'INBOUND': return 'I'
    return d

def validate_stop_id(stop_id):
    if not isinstance(stop_id, str) or not STOP_ID_PATTERN.match(stop_id):
        raise ValueError("Invalid stop ID")

def validate_name(name):
    if not isinstance(name, str) or not (1 <= len(name) <= 100):
        raise ValueError("Invalid name")

def fetch_json(url, retries=3, total_timeout=5):
    start = time.time()
    delay = 0.5
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'OpenClaw-kmb-bus-arrival', 'Accept': 'application/json'}
    )
    for attempt in range(1, retries+1):
        try:
            elapsed = time.time() - start
            remaining = total_timeout - elapsed
            if remaining <= 0:
                return {"error": "timeout", "attempts": attempt-1}
            timeout = min(2.0, remaining)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode('utf-8')
                if not raw.strip():
                    raise ValueError("Empty response")
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            return {"error": f"HTTP {e.code}: {e.reason}", "attempts": attempt}
        except urllib.error.URLError as e:
            err_str = str(e.reason) if hasattr(e, 'reason') else str(e)
            if attempt < retries:
                time.sleep(min(delay, remaining if 'remaining' in locals() else delay))
                delay *= 1.5
                continue
            return {"error": f"Network error: {err_str}", "attempts": attempt}
        except Exception as e:
            if attempt < retries:
                elapsed = time.time() - start
                if elapsed >= total_timeout - 0.5:
                    return {"error": "timeout", "attempts": attempt}
                time.sleep(min(delay, total_timeout - elapsed))
                delay *= 1.5
                continue
            return {"error": str(e), "attempts": attempt}
    return {"error": "max retries"}

def bound_to_api_dir(bound):
    if bound == "O": return "outbound"
    if bound == "I": return "inbound"
    return bound

def get_stop_map():
    """Fetch the full stop list from the API"""
    data = fetch_json(f"{BASE}/stop")
    if "error" in data:
        return {}
    stops = data.get("data", [])
    return {s["stop"]: {"name_en": s.get("name_en",""), "name_tc": s.get("name_tc","")} for s in stops}

def get_route_direction(route):
    validate_route(route)
    data = fetch_json(f"{BASE}/route/?route={route}")
    if "error" in data:
        print(json.dumps({"error": data["error"]})); return
    entries = data.get("data") or data
    if not isinstance(entries, list):
        entries = [entries] if entries else []
    matching = [e for e in entries if e.get("route") == route]
    if not matching:
        print(json.dumps({"error": "Route not found"})); return

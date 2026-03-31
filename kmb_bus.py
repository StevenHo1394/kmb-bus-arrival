#!/usr/bin/env python3
"""
KMB Bus Arrival Skill v1.1.4
- Documentation/code aligned (all inconsistencies fixed)
- Plain text output for getNextArrivals; never exposes raw stop IDs
- Direction labels removed; multi-direction shown as separate blocks
- Pure Python; no external deps; security-hardened
- 30min cache TTL, auto-purge; retries 3× ≤5s
- Auto-direction + alternate stop ID fallback
"""

import json, sys, time, os, re, urllib.request, urllib.error
from datetime import datetime

BASE = "https://data.etabus.gov.hk/v1/transport/kmb"
CACHE_DIR = "/tmp/kmb_bus_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Validation patterns
ROUTE_PATTERN = re.compile(r'^[A-Za-z0-9]+$')
DIRECTION_PATTERN = re.compile(r'^(O|I|outbound|inbound)$', re.IGNORECASE)
# Accept either short alphanumeric (e.g., ST871) or 16-char hex
STOP_ID_PATTERN = re.compile(r'^[A-Za-z0-9]{1,16}$')

def validate_route(route: str):
    if not isinstance(route, str) or not ROUTE_PATTERN.match(route):
        raise ValueError(f"Invalid route format: '{route}'")

def validate_direction(direction: str) -> str:
    if not isinstance(direction, str):
        raise ValueError("Direction must be a string")
    # Allow 'auto' for automatic direction detection
    if direction.lower() == 'auto':
        return 'auto'
    if not DIRECTION_PATTERN.match(direction):
        raise ValueError(f"Invalid direction: '{direction}'. Use 'O', 'I', 'outbound', 'inbound', or 'auto'")
    # Normalize to API codes
    d = direction.upper()
    if d == 'OUTBOUND': return 'O'
    if d == 'INBOUND': return 'I'
    return d

def validate_stop_id(stop_id: str):
    if not isinstance(stop_id, str):
        raise ValueError("Stop ID must be a string")
    if not STOP_ID_PATTERN.match(stop_id):
        raise ValueError(f"Stop ID format invalid: '{stop_id}'")
    # Accept any alphanumeric ID up to 16 characters (short IDs like ST871 are allowed)

def validate_name(name: str):
    if not isinstance(name, str) or not (1 <= len(name) <= 100):
        raise ValueError("Stop name must be 1-100 characters")

def cache_path(key):
    return os.path.join(CACHE_DIR, f"{key}.json")

def load_cache(key, ttl_seconds=1800):  # 30 minutes default
    path = cache_path(key)
    if os.path.exists(path):
        if time.time() - os.path.getmtime(path) < ttl_seconds:
            try:
                return json.load(open(path))
            except:
                pass
        else:
            # Delete stale cache file immediately
            try: os.remove(path)
            except: pass
    return None

def save_cache(key, data):
    with open(cache_path(key), 'w') as f:
        json.dump(data, f, ensure_ascii=False)

def fetch_json(url, retries=3, total_timeout=5):
    """Fetch JSON with retries using urllib (no external curl). Total time budget ≤5s."""
    start = time.time()
    delay = 0.5  # initial backoff
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (OpenClaw kmb-bus-arrival)', 'Accept': 'application/json'}
    )
    for attempt in range(1, retries+1):
        try:
            # Compute remaining time for this attempt's timeout
            elapsed = time.time() - start
            remaining = total_timeout - elapsed
            if remaining <= 0:
                return {"error": "timeout", "attempts": attempt-1}
            # Per-attempt timeout = min(2s, remaining)
            timeout = min(2.0, remaining)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode('utf-8')
                if not raw.strip():
                    raise ValueError("Empty response")
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            # 4xx/5xx errors
            return {"error": f"HTTP {e.code}: {e.reason}", "attempts": attempt}
        except urllib.error.URLError as e:
            # Network errors, timeouts
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
    return {"error": "max retries exceeded"}

def bound_to_api_dir(bound):
    if bound == "O": return "outbound"
    if bound == "I": return "inbound"
    return bound

def get_stop_map():
    stops = load_cache("stops_all")  # uses default 1800 sec (30 min)
    if stops is None:
        data = fetch_json(f"{BASE}/stop")
        if "error" not in data:
            stops = data.get("data", [])
            save_cache("stops_all", stops)
    if stops:
        return {s["stop"]: {"name_en": s.get("name_en",""), "name_tc": s.get("name_tc","")} for s in stops}
    return {}

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
    directions = []
    for entry in matching:
        directions.append({
            "bound": entry.get("bound"),
            "name_en": (entry.get("orig_en") + " → " + entry.get("dest_en")) if entry.get("orig_en") and entry.get("dest_en") else "",
            "name_tc": (entry.get("orig_tc") + " → " + entry.get("dest_tc")) if entry.get("orig_tc") and entry.get("dest_tc") else ""
        })
    print(json.dumps({"route": route, "directions": directions}, ensure_ascii=False))

def get_route_info(route, direction):
    validate_route(route)
    direction = validate_direction(direction)
    api_dir = bound_to_api_dir(direction)
    data = fetch_json(f"{BASE}/route-stop/{route}/{api_dir}/1")
    if "error" in data:
        print(json.dumps({"error": data["error"]})); return
    stops = data.get("data", [])
    stop_map = get_stop_map()
    result = []
    for s in stops:
        stop_id = s["stop"]
        names = stop_map.get(stop_id, {"name_en": "", "name_tc": ""})
        result.append({
            "seq": s["seq"],
            "stop": stop_id,
            "name_en": names["name_en"],
            "name_tc": names["name_tc"]
        })
    print(json.dumps({"route": route, "direction": direction, "stops": result}, ensure_ascii=False))

def get_bus_stop_id(name):
    validate_name(name)
    cache_key = "stops_all"
    stops = load_cache(cache_key, ttl_seconds=3600)
    if stops is None:
        data = fetch_json(f"{BASE}/stop")
        if "error" in data:
            print(json.dumps({"error": data["error"]})); return
        stops = data.get("data", [])
        save_cache(cache_key, stops)
    q = name.lower()
    matches = [s for s in stops if q in s.get("name_tc","").lower() or q in s.get("name_en","").lower()]
    print(json.dumps(matches, ensure_ascii=False))

def get_next_arrivals(route, direction, stop_id):
    validate_route(route)
    direction = validate_direction(direction)
    validate_stop_id(stop_id)

    # Determine which directions to try
    directions_to_try = ['I', 'O'] if direction == 'auto' else [direction]

    results = []  # collect per-direction results
    stop_map = get_stop_map()
    stop_name = stop_map.get(stop_id, {}).get("name_tc") or stop_map.get(stop_id, {}).get("name_en", "")
    def strip_code(s):
        import re
        return re.sub(r' \([A-Z0-9]+\)$', '', s)
    names = stop_map.get(stop_id, {"name_tc": "", "name_en": ""})
    name_tc_clean = strip_code(names.get("name_tc", ""))
    name_en_clean = strip_code(names.get("name_en", ""))
    if name_tc_clean and name_en_clean:
        display_name = f"{name_tc_clean} ({name_en_clean})"
    else:
        display_name = name_tc_clean or name_en_clean or stop_name

    for try_dir in directions_to_try:
        api_dir = bound_to_api_dir(try_dir)
        route_stop = fetch_json(f"{BASE}/route-stop/{route}/{api_dir}/1")
        if "error" in route_stop:
            continue
        stops = route_stop.get("data", [])
        seq = None
        # First, try the exact stop_id
        for s in stops:
            if s["stop"] == stop_id:
                seq = int(s["seq"])
                break
        # If not found, try to find an alternate stop ID with the same human-readable name
        if seq is None and (name_tc_clean or name_en_clean):
            # Search the route's stop list for a candidate whose name (from stop_map) matches our intended location
            target_tc = name_tc_clean.lower()
            target_en = name_en_clean.lower()
            for s in stops:
                candidate_id = s["stop"]
                # Get names from stop_map
                names_candidate = stop_map.get(candidate_id, {})
                cand_tc_raw = names_candidate.get("name_tc", "")
                cand_en_raw = names_candidate.get("name_en", "")
                cand_tc = strip_code(cand_tc_raw)
                cand_en = strip_code(cand_en_raw)
                # Match if target Chinese or English appears in candidate's cleaned name
                if (target_tc and target_tc in cand_tc.lower()) or (target_en and target_en in cand_en.lower()):
                    # Use this alternate stop
                    stop_id = candidate_id
                    seq = int(s["seq"])
                    # Update display_name to the candidate's cleaned names
                    if cand_tc and cand_en:
                        display_name = f"{cand_tc} ({cand_en})"
                    else:
                        display_name = cand_tc or cand_en
                    break
        if seq is None:
            continue  # try next direction
        eta_data = fetch_json(f"{BASE}/route-eta/{route}/1")
        arrivals = []
        destination = ""
        def process_eta_items(items):
            nonlocal destination, arrivals
            filtered = [it for it in items if it.get("dir") == try_dir and int(it.get("seq", 0)) == seq]
            filtered.sort(key=lambda x: x.get("eta_seq") or 0)
            if filtered and not destination:
                destination = filtered[0].get("dest_tc", "") or filtered[0].get("dest_en", "")
            for it in filtered[:3]:
                eta_str = it.get("eta")
                if not eta_str:
                    continue
                try:
                    dt = datetime.fromisoformat(eta_str.replace("Z", "+00:00"))
                    arrivals.append(dt.strftime("%H:%M HKT"))
                except Exception:
                    arrivals.append(eta_str)
        if "error" not in eta_data:
            items = eta_data if isinstance(eta_data, list) else eta_data.get("data", [])
            process_eta_items(items)
        if not arrivals:
            stop_eta = fetch_json(f"{BASE}/stop-eta/{stop_id}")
            if "error" not in stop_eta:
                items = stop_eta if isinstance(stop_eta, list) else stop_eta.get("data", [])
                process_eta_items(items)
        if arrivals:
            results.append({
                "direction": try_dir,
                "destination": destination,
                "arrivals": arrivals
            })

    if not results:
        print(json.dumps({"error": "Stop not found on this route"}))
        return

    # Print each direction as a separate block with header, stop, and arrivals
    for d in results:
        dest = d['destination']
        header = f"*{route} (To {dest})*" if dest else f"*{route}*"
        print(header + "\n")
        print(f"Stop: *{display_name}*\n")
        print("Next arrivals:")
        for t in d['arrivals']:
            print(f"- {t}")
        print()  # blank line after each block

def purge_old_cache(ttl_seconds=1800):
    now = time.time()
    for f in os.listdir(CACHE_DIR):
        path = os.path.join(CACHE_DIR, f)
        if os.path.isfile(path) and now - os.path.getmtime(path) > ttl_seconds:
            try:
                os.remove(path)
            except:
                pass

def main():
    # Clean cache older than 30 minutes on every run
    purge_old_cache(1800)
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Missing subcommand"})); return
    cmd = sys.argv[1]
    try:
        if cmd == "getRouteDirection":
            if len(sys.argv) < 3: raise ValueError("Missing route")
            get_route_direction(sys.argv[2])
        elif cmd == "getRouteInfo":
            if len(sys.argv) < 4: raise ValueError("Missing route or direction")
            get_route_info(sys.argv[2], sys.argv[3])
        elif cmd == "getBusStopID":
            if len(sys.argv) < 3: raise ValueError("Missing name")
            get_bus_stop_id(sys.argv[2])
        elif cmd == "getNextArrivals":
            if len(sys.argv) < 5: raise ValueError("Missing route, direction, stopId")
            get_next_arrivals(sys.argv[2], sys.argv[3], sys.argv[4])
        else:
            print(json.dumps({"error": f"Unknown command: {cmd}"}))
    except ValueError as ve:
        print(json.dumps({"error": str(ve)}))
    except Exception as e:
        print(json.dumps({"error": f"Unexpected error: {str(e)}"}))

if __name__ == "__main__":
    main()

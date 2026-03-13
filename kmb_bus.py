#!/usr/bin/env python3
import json, sys, time, os, subprocess
from datetime import datetime

BASE = "https://data.etabus.gov.hk/v1/transport/kmb"
CACHE_DIR = "/tmp/kmb_bus_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def cache_path(key):
    return os.path.join(CACHE_DIR, f"{key}.json")

def load_cache(key, ttl_seconds=60):
    path = cache_path(key)
    if os.path.exists(path):
        if time.time() - os.path.getmtime(path) < ttl_seconds:
            try:
                return json.load(open(path))
            except:
                pass
    return None

def save_cache(key, data):
    with open(cache_path(key), 'w') as f:
        json.dump(data, f, ensure_ascii=False)

def curl_fetch(url, retries=3, delay=2):
    env = os.environ.copy()
    for k in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"]:
        env[k] = ""
    for attempt in range(1, retries+1):
        try:
            cmd = ["curl", "-s", "-S", "-k", "--http1.1", "-4",
                   "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                   "-H", "Accept: application/json", url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15, env=env)
            if result.returncode != 0:
                raise RuntimeError(f"curl error {result.returncode}: {result.stderr}")
            raw = result.stdout
            if not raw.strip():
                raise ValueError("Empty response body")
            return json.loads(raw)
        except Exception as e:
            if attempt < retries:
                time.sleep(delay)
            else:
                return {"error": str(e), "attempts": attempt}

def bound_to_api_dir(bound):
    if bound == "O":
        return "outbound"
    if bound == "I":
        return "inbound"
    return bound

def get_stop_map():
    stops = load_cache("stops_all", ttl_seconds=3600)
    if stops is None:
        data = curl_fetch(f"{BASE}/stop")
        if "error" not in data:
            stops = data.get("data", [])
            save_cache("stops_all", stops)
    if stops:
        return {s["stop"]: {"name_en": s.get("name_en",""), "name_tc": s.get("name_tc","")} for s in stops}
    return {}

def get_route_direction(route):
    data = curl_fetch(f"{BASE}/route/?route={route}")
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
    api_dir = bound_to_api_dir(direction)
    data = curl_fetch(f"{BASE}/route-stop/{route}/{api_dir}/1")
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
    cache_key = "stops_all"
    stops = load_cache(cache_key, ttl_seconds=3600)
    if stops is None:
        data = curl_fetch(f"{BASE}/stop")
        if "error" in data:
            print(json.dumps({"error": data["error"]})); return
        stops = data.get("data", [])
        save_cache(cache_key, stops)
    q = name.lower()
    matches = [s for s in stops if q in s.get("name_tc","").lower() or q in s.get("name_en","").lower()]
    print(json.dumps(matches, ensure_ascii=False))

def get_next_arrivals(route, direction, stop_id):
    api_dir = bound_to_api_dir(direction)
    route_stop = curl_fetch(f"{BASE}/route-stop/{route}/{api_dir}/1")
    if "error" in route_stop:
        print(json.dumps({"error": route_stop["error"]})); return
    stops = route_stop.get("data", [])
    seq = None
    for s in stops:
        if s["stop"] == stop_id:
            seq = int(s["seq"])
            break
    if seq is None:
        print(json.dumps({"error": f"Stop {stop_id} not found on route {route} direction {direction}"})); return
    stop_map = get_stop_map()
    stop_name = stop_map.get(stop_id, {}).get("name_tc") or stop_map.get(stop_id, {}).get("name_en", "")
    eta_data = curl_fetch(f"{BASE}/route-eta/{route}/1")
    arrivals = []
    if "error" not in eta_data:
        items = eta_data if isinstance(eta_data, list) else eta_data.get("data", [])
        filtered = [it for it in items if it.get("dir") == direction and int(it.get("seq", 0)) == seq]
        filtered.sort(key=lambda x: x.get("eta_seq") or 0)
        for it in filtered[:3]:
            eta_str = it.get("eta")
            if not eta_str:
                continue
            try:
                dt = datetime.fromisoformat(eta_str.replace("Z", "+00:00"))
                arrivals.append(dt.strftime("%H:%M HKT"))
            except Exception:
                arrivals.append(eta_str)
    result = {
        "stopId": stop_id,
        "stopName": stop_name,
        "route": route,
        "direction": direction,
        "arrivals": arrivals if arrivals else ["No active ETAs"]
    }
    print(json.dumps(result, ensure_ascii=False))

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Missing subcommand"})); return
    cmd = sys.argv[1]
    if cmd == "getRouteDirection":
        if len(sys.argv) < 3: print(json.dumps({"error": "Missing route"})); return
        get_route_direction(sys.argv[2])
    elif cmd == "getRouteInfo":
        if len(sys.argv) < 4: print(json.dumps({"error": "Missing route or direction"})); return
        get_route_info(sys.argv[2], sys.argv[3])
    elif cmd == "getBusStopID":
        if len(sys.argv) < 3: print(json.dumps({"error": "Missing name"})); return
        get_bus_stop_id(sys.argv[2])
    elif cmd == "getNextArrivals":
        if len(sys.argv) < 5: print(json.dumps({"error": "Missing route, direction, stopId"})); return
        get_next_arrivals(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print(json.dumps({"error": f"Unknown command: {cmd}"}))

if __name__ == "__main__":
    main()
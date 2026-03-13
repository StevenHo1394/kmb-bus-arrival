#!/usr/bin/env bash
set -x
# kmb_bus.sh - KMB Bus Arrival Skill Implementation (curl-based)
# Base URL
BASE="https://data.etabus.gov.hk/v1/transport/kmb"

# Cache directory
CACHE_DIR="/tmp/kmb_bus_cache"
mkdir -p "$CACHE_DIR"

# Helper: curl with proper headers, no proxies
curl_fetch() {
    local url="$1"
    # Clear proxy env for this command
    env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
    curl -s -S -k --http1.1 -4 \
        -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36" \
        -H "Accept: application/json" \
        "$url"
}

# Tools

# getRouteDirection <route>
getRouteDirection() {
    local route="$1"
    local url="$BASE/route/$route"
    local raw
    raw=$(curl_fetch "$url")
    if [ -z "$raw" ]; then
        echo "{\"error\":\"Empty response\"}"
        return
    fi
    # Extract directions: need to find "bounds" array. Use python for JSON parsing (minimal)
    python3 -c "import json,sys; d=json.loads(sys.stdin.read()); routes=d.get('data') or d; obj=routes if isinstance(routes,dict) else next((r for r in routes if r.get('route')=='$route'), None); bounds=obj.get('bounds',[]); dirs=[{\"bound\":b.get('bound'),\"name_en\":b.get('name_en',''),\"name_tc\":b.get('name_tc','')} for b in bounds]; print(json.dumps({'route':'$route','directions':dirs}, ensure_ascii=False))" <<<"$raw"
}

# getRouteInfo <route> <direction>
getRouteInfo() {
    local route="$1" direction="$2"
    local url="$BASE/route-stop/$route/$direction/1"
    local raw
    raw=$(curl_fetch "$url")
    if [ -z "$raw" ]; then
        echo "{\"error\":\"Empty response\"}"
        return
    fi
    python3 -c "import json,sys; d=json.loads(sys.stdin.read()); stops=d.get('data',[]); out=[{'seq':s['seq'],'stop':s['stop'],'name_en':s.get('name_en',''),'name_tc':s.get('name_tc','')} for s in stops]; print(json.dumps({'route':'$route','direction':'$direction','stops':out}, ensure_ascii=False))" <<<"$raw"
}

# getBusStopID <name>
getBusStopID() {
    local name="$1"
    local cache_key="stops_all"
    local cache_file="$CACHE_DIR/$cache_key.json"
    local raw
    if [ -f "$cache_file" ] && [ $(( $(date +%s) - $(stat -c %Y "$cache_file") )) -lt 3600 ]; then
        raw=$(cat "$cache_file")
    else
        raw=$(curl_fetch "$BASE/stop")
        if [ -n "$raw" ]; then
            echo "$raw" > "$cache_file"
        fi
    fi
    if [ -z "$raw" ]; then
        echo "[]"
        return
    fi
    # Filter by name (case-insensitive)
    python3 -c "import json,sys; data=json.loads(sys.stdin.read()); stops=data.get('data',[]); q='$name'.lower(); matches=[s for s in stops if q in s.get('name_tc','').lower() or q in s.get('name_en','').lower()]; print(json.dumps(matches, ensure_ascii=False))" <<<"$raw"
}

# getNextArrivals <route> <direction> <stopId>
getNextArrivals() {
    local route="$1" direction="$2" stop_id="$3"
    # 1. Get route-stop to find seq
    local raw_rs
    raw_rs=$(curl_fetch "$BASE/route-stop/$route/$direction/1")
    if [ -z "$raw_rs" ]; then
        echo "{\"error\":\"Empty route-stop response\"}"
        return
    fi
    # Parse JSON to find seq and stopName (use python)
    local seq stop_name
    read seq stop_name <<EOF
$(python3 -c "import json,sys; d=json.loads(sys.stdin.read()); stops=d.get('data',[]); seq=None; name=None; \nfor s in stops:\n if s.get('stop')=='$stop_id':\n  seq=s.get('seq'); name=s.get('name_tc') or s.get('name_en'); break\nif seq is None:\n exit(1)\nprint(seq); print(name or '')" <<<"$raw_rs")
EOF
    if [ -z "$seq" ] || [ "$seq" = "None" ]; then
        echo "{\"error\":\"Stop $stop_id not found on route $route $direction\"}"
        return
    fi
    # 2. Get route-eta
    local raw_eta
    raw_eta=$(curl_fetch "$BASE/route-eta/$route/1")
    local arrivals=()
    if [ -n "$raw_eta" ]; then
        # Filter items with dir and seq
        IFS=$'\n' read -r -d '' -a filtered_arr <<EOF
$(python3 -c "import json,sys; d=json.loads(sys.stdin.read()); items=d if isinstance(d,list) else d.get('data',[]); filt=[it for it in items if it.get('dir')=='$direction' and it.get('seq')==$seq]; filt.sort(key=lambda x: x.get('eta_seq') or 0); \nfor it in filt[:3]:\n eta=it.get('eta')\n if eta:\n  try:\n   from datetime import datetime; dt=datetime.fromisoformat(eta); print(dt.strftime('%H:%M HKT'))\n  except: print(eta)\n" <<<"$raw_eta")
EOF
        arrivals=($(printf "%s\n" "${filtered_arr[@]}"))
    fi
    # 3. Fallback to stop-eta if none
    if [ ${#arrivals[@]} -eq 0 ]; then
        local raw_se
        raw_se=$(curl_fetch "$BASE/stop-eta/$stop_id/1")
        if [ -n "$raw_se" ]; then
            IFS=$'\n' read -r -d '' -a filtered_arr <<EOF
$(python3 -c "import json,sys; d=json.loads(sys.stdin.read()); items=d if isinstance(d,list) else d.get('data',[]); filt=[it for it in items if it.get('route')=='$route' and it.get('dir')=='$direction']; filt.sort(key=lambda x: x.get('eta_seq') or 0); \nfor it in filt[:3]:\n eta=it.get('eta')\n if eta:\n  try:\n   from datetime import datetime; dt=datetime.fromisoformat(eta); print(dt.strftime('%H:%M HKT'))\n  except: print(eta)\n" <<<"$raw_se")
EOF
            arrivals=($(printf "%s\n" "${filtered_arr[@]}"))
        fi
    fi
    # Build result JSON
    local result
    result=$(python3 -c "import json; print(json.dumps({'stopId':'$stop_id','stopName':'$stop_name','route':'$route','direction':'$direction','arrivals':${arrivals[@]} or []}, ensure_ascii=False))")
    echo "$result"
}

# Main
case "$1" in
    getRouteDirection)
        if [ $# -lt 2 ]; then echo "{\"error\":\"Missing route\"}"; exit 1; fi
        getRouteDirection "$2"
        ;;
    getRouteInfo)
        if [ $# -lt 4 ]; then echo "{\"error\":\"Missing route or direction\"}"; exit 1; fi
        getRouteInfo "$2" "$3"
        ;;
    getBusStopID)
        if [ $# -lt 3 ]; then echo "{\"error\":\"Missing name\"}"; exit 1; fi
        getBusStopID "$2"
        ;;
    getNextArrivals)
        if [ $# -lt 5 ]; then echo "{\"error\":\"Missing route, direction, stopId\"}"; exit 1; fi
        getNextArrivals "$2" "$3" "$4"
        ;;
    *)
        echo "{\"error\":\"Unknown command: $1\"}"
        exit 1
        ;;
esac

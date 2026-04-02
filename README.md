# KMB Bus Arrival Skill v1.1.7

Real-time KMB bus arrival information using the official Hong Kong Data Hub API.

## 🚀 Installation

1. Extract the ZIP file
2. Copy `kmb-bus-arrival/` to your OpenClaw `skills/` directory
3. Restart OpenClaw or reload skills
4. Use the skill with commands like:
   - `getRouteDirection 182`
   - `getNextArrivals 182 I ST871`  (or use 16-hex stop ID like `4ED04A0F5F9FF05F`)

## Usage
- `getNextArrivals <route> <direction> <stopId>` — plain text output
- `getRouteDirection <route>` — JSON
- `getRouteInfo <route> <direction>` — JSON
- `getBusStopID <name>` — JSON

`direction` can be `outbound`, `inbound`, or `auto` (checks both).

The skill auto-detects alternate stop IDs if the given one doesn't match the route, and formats results for direct messaging.

## Requirements

- Python 3 (standard library only)
- Network access to `data.etabus.gov.hk`

## Security

- Input validation (route, stop ID, direction)
- SSL verification
- Timeouts and retries (3 attempts, ≤5s total)
- No external dependencies; no credentials

## Version

**v1.1.7** (2026-04-02)
- Full removal of caching — all API calls are fresh; docs aligned
- Fixed code/docs consistency issues
- Plain‑text errors for getNextArrivals; JSON errors for other tools
- Auto‑direction and alternate stop ID fallback retained

v1.1.6 — Full removal of caching; docs aligned; error handling fixes  
v1.1.5 — Removed all caching (earlier attempt incomplete)  
v1.1.4 — Documentation/code alignment; fixed inconsistencies  
v1.1.3 — Security hardening, removed direction labels  
v1.1.2 — Plain text output, flexible stop IDs  
v1.1.1 — Metadata updates  
v1.1.0 — Security fixes, cache TTL 30min, validate stop id, fix stop-eta endpoint  
v1.0.0 — Initial release
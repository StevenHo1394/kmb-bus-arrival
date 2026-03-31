---
name: kmb-bus-arrival
description: Retrieve real-time KMB bus arrival information. getNextArrivals returns human-readable plain text for direct messaging; other tools return JSON. v1.1.3: Documentation/code aligned; plain text getNextArrivals; no raw stop IDs; 30min cache; security review passed.
version: 1.1.4
author: Steven Ho
repository: https://github.com/StevenHo1394/kmb-bus-arrival
tools:
  - name: getRouteDirection
    description: List available travel directions for a KMB route (e.g., inbound/outbound).
    command: python3 kmb_bus.py getRouteDirection {route}
    inputSchema:
      type: object
      required:
        - route
      properties:
        route:
          type: string
          description: KMB route number (e.g., "1", "5X", "N21")
    output:
      format: json
  - name: getRouteInfo
    description: Get the list of stops for a route with sequence numbers.
    command: python3 kmb_bus.py getRouteInfo {route} {direction}
    inputSchema:
      type: object
      required:
        - route
        - direction
      properties:
        route:
          type: string
        direction:
          type: string
          description: "inbound" or "outbound" as returned by getRouteDirection
    output:
      format: json
  - name: getBusStopID
    description: Find bus stop ID(s) by name (Chinese or English). May return multiple matches.
    command: python3 kmb_bus.py getBusStopID {name}
    inputSchema:
      type: object
      required:
        - name
      properties:
        name:
          type: string
          description: Bus stop name (partial or full, in Chinese or English)
    output:
      format: json
  - name: getNextArrivals
    description: Get the next bus arrival times for a specific route/direction/stop. Returns plain text formatted for direct messaging (markdown-style).
    command: python3 kmb_bus.py getNextArrivals {route} {direction} {stopId}
    inputSchema:
      type: object
      required:
        - route
        - direction
        - stopId
      properties:
        route:
          type: string
        direction:
          type: string
          enum: ["O", "outbound", "I", "inbound", "auto"]
        stopId:
          type: string
          description: KMB bus stop ID (short alphanumeric or 16-hex)
    output:
      format: text

---
# Implementation Notes

## API Endpoints (Base URL: https://data.etabus.gov.hk)

- Route List: `/v1/transport/kmb/route/`
- Route Directions: `/v1/transport/kmb/route/{route}` (returns route details including bound/direction)
- Route‑Stop: `/v1/transport/kmb/route-stop/{route}/{direction}/{service_type}` (service_type=1 normally)
- Stop List: `/v1/transport/kmb/stop` (all stops) or `/v1/transport/kmb/stop?name={name}` to filter
- Route ETA: `/v1/transport/kmb/route-eta/{route}/{service_type}`
- Stop ETA: `/v1/transport/kmb/stop-eta/{stop}/{service_type}`

## Script: kmb_bus.py

Place this Python script in the same directory as this SKILL.md. It will be invoked with subcommands as defined above.

### Behavior

- **getRouteDirection {route}**
  - Fetch `/v1/transport/kmb/route/{route}` (or route list) to determine available directions.
  - Return JSON: `{ "route": "...", "directions": [{ "bound": "O", "name_tc": "往荃灣", "name_en": "Outbound" }, ...] }`

- **getRouteInfo {route} {direction}**
  - Fetch `/v1/transport/kmb/route-stop/{route}/{direction}/1`.
  - For each entry in `data`, extract `seq`, `stop`, `name_tc`, `name_en`.
  - Return JSON list of stops in order.

- **getBusStopID {name}**
  - Fetch `/v1/transport/kmb/stop?name={name}` (simple substring match; the API supports name filtering? Actually the endpoint is `/v1/transport/kmb/stop` which returns all stops; client can filter locally. Better: fetch full stop list once and cache, then filter by name_tc or name_en containing the query. For simplicity, fetch `/v1/transport/kmb/stop` and filter locally by name.
  - Return JSON: `[ { "stop": "ST871", "name_en": "YU CHUI COURT BUS TERMINUS", "name_tc": "愉翠苑巴士總站" }, ... ]`

- **getNextArrivals {route} {direction} {stopId}**
  - Fetch route‑stop for the route/direction to find the `seq` for `stopId`. If not found, try alternate stop ID by matching human-readable name.
  - Fetch `/v1/transport/kmb/route-eta/{route}/1` (or fallback to `/v1/transport/kmb/stop-eta/{stopId}`). Filter by `dir` and `seq`, sort by `eta_seq`, take up to 3.
  - Format each ETA as `HH:MM HKT`.
  - **Output:** Plain text, markdown‑style, e.g.:
    ```
    *68A (To Destination)*

    Stop: *Human Readable Name*

    Next arrivals:
    - 18:58 HKT
    - 19:15 HKT
    - 19:28 HKT
    ```
  - If no arrivals: print a clear plain‑text message (no JSON).

- **getRouteDirection**, **getRouteInfo**, **getBusStopID**
  - Return structured JSON as described in their tool definitions.

### Caching
- Cache full stop list for 30 minutes.
- Cache route‑stop/route‑eta responses for 30 minutes (same TTL).
- Auto‑purge stale cache on each run.

### Error Handling
- JSON‑returning tools output JSON with an `error` field.
- getNextArrivals outputs plain‑text error messages.
- All network errors, invalid inputs, and "not found" cases are handled gracefully.

## Testing
Test the script manually before enabling:
- `python3 kmb_bus.py getRouteDirection 182`
- `python3 kmb_bus.py getRouteInfo 182 outbound` (should include seq for ST871 if it’s on that route)
- `python3 kmb_bus.py getBusStopID "愉翠苑巴士總站"`
- `python3 kmb_bus.py getNextArrivals 182 outbound ST871`

## Integration
Ensure the `command` fields in the tool definitions point to `python3 kmb_bus.py <subcommand> ...` with proper placeholders. The skill directory must contain this `kmb_bus.py` file.

## Notes
- The KMB Data Hub may return no ETAs outside operating hours (approx 06:00–23:00). Handle gracefully.
- Some stops have multiple IDs; prefer the one that appears in the route‑stop list.

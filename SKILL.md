---
name: kmb-bus-arrival
description: Retrieve real-time KMB bus arrival information. getNextArrivals returns plain text (markdown-style); other tools return JSON. v1.1.5: Removed all caching, simplified code; plain-text errors for getNextArrivals; aligned docs.
version: 1.1.5
author: Steven Ho
repository: https://github.com/StevenHo1394/kmb-bus-arrival
tools:
  - name: getRouteDirection
    description: List available travel directions for a KMB route (e.g., inbound/outbound). Returns JSON.
    command: python3 kmb_bus.py getRouteDirection {route}
    inputSchema:
      type: object
      required: [route]
      properties:
        route:
          type: string
          description: KMB route number (e.g., "1", "5X", "N21")
    output:
      format: json

  - name: getRouteInfo
    description: Get the list of stops for a route with sequence numbers. Returns JSON.
    command: python3 kmb_bus.py getRouteInfo {route} {direction}
    inputSchema:
      type: object
      required: [route, direction]
      properties:
        route:
          type: string
        direction:
          type: string
          description: "outbound" or "inbound"
    output:
      format: json

  - name: getBusStopID
    description: Find bus stop ID(s) by name (Chinese or English). May return multiple matches. Returns JSON.
    command: python3 kmb_bus.py getBusStopID {name}
    inputSchema:
      type: object
      required: [name]
      properties:
        name:
          type: string
          description: Bus stop name (partial or full, in Chinese or English)
    output:
      format: json

  - name: getNextArrivals
    description: Get the next bus arrival times for a specific route/direction/stop. Returns plain text formatted for direct messaging.
    command: python3 kmb_bus.py getNextArrivals {route} {direction} {stopId}
    inputSchema:
      type: object
      required: [route, direction, stopId]
      properties:
        route:
          type: string
        direction:
          type: string
          enum: ["O", "outbound", "I", "inbound", "auto"]
        stopId:
          type: string
          description: KMB bus stop ID (short alphanumeric like ST871 or 16-hex)
    output:
      format: text

Implementation Notes:

- getNextArrivals prints plain text with markdown formatting. Example:
  ```
  *68A (To Destination)*

  Stop: *Human Readable Stop Name*

  Next arrivals:
  - 18:58 HKT
  - 19:15 HKT
  ```
  If `direction="auto"` and the stop is served in both directions, multiple blocks are printed.

- Other tools (getRouteDirection, getRouteInfo, getBusStopID) return JSON structures.

- The skill uses the KMB Data Hub API directly (no caching). All calls are made with SSL verification and timeouts. Inputs are validated; route alphanumeric, stop ID 1–16 alphanumeric, direction one of allowed values.

- Auto-direction: `direction="auto"` tries both inbound and outbound; whichever has the stop will be reported. If the stop appears on both directions, both are included.

- Alternate stop ID fallback: If the given stop ID is not found on the route, the skill searches the route's stop list for a stop whose Chinese or English name matches the intended location (based on the provided stop ID's human-readable names) and uses that alternate ID automatically.

- No caching: every invocation fetches fresh data from the API.

- Errors: getNextArrivals prints human-readable messages; other tools output JSON with an `error` field.

- No external dependencies (Python standard library only).

version: 1.1.5
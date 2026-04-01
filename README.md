# 🚌 KMB Bus Arrival Skill v1.1.5

Real-time KMB bus arrival information for Hong Kong using the official government transport API (Data Hub).

**Key features:**
- Plain text output for `getNextArrivals` (markdown-style)
- `direction="auto"` for both inbound/outbound automatically
- Alternate stop ID fallback (handles multiple IDs for same location)
- No caching – all API calls are fresh
- Pure Python – no external dependencies
- Security-hardened (input validation, SSL, timeouts)

## 📁 Package Structure

```
kmb-bus-arrival/
├── kmb_bus.py          (main executable)
├── SKILL.md            (OpenClaw skill definition)
└── README.md           (this file)
```

## 🚀 Quick Start

1. Place the `kmb-bus-arrival` folder in your OpenClaw `skills/` directory.
2. Restart OpenClaw or reload skills.
3. Use the skill with commands like:
   - `getRouteDirection 182`
   - `getRouteInfo 182 outbound`
   - `getBusStopID "Panda Hotel"`
   - `getNextArrivals E31 auto 4ED04A0F5F9FF05F`

## 📊 Features

- ✅ Real-time ETA from HK Government API (no caching)
- ✅ Fast retry (3 attempts, ≤5s total)
- ✅ Accepts both short (e.g., ST871) and 16‑hex stop IDs
- ✅ Auto-direction detection (`direction="auto"`)
- ✅ Alternate stop ID fallback (same location, different IDs)
- ✅ Plain‑text output for messaging; JSON for structured tools
- ✅ No external dependencies (Python stdlib only)
- ✅ Security-hardened (LOW risk)
- ✅ Supports all KMB routes
- ✅ Chinese & English stop names

## 🔒 Security

- Input validation: route (alphanumeric), stop ID (1–16 alphanumeric), direction (O/I/outbound/inbound/auto)
- No command injection (pure Python, no subprocess)
- SSL verification enforced
- Timeouts: per-request ≤2s, total ≤5s
- No sensitive logging; generic errors
- No cache files written

## 📝 Version History

**v1.1.5** (2026-03-31)
- Removed all caching (direct API calls)
- Plain text getNextArrivals; other tools return JSON
- Auto-direction (`direction="auto"`) and alternate stop ID fallback
- Documentation fully aligned; no cache TTL mentions
- Security-hardened; pure Python; no external deps

v1.1.4: Documentation/code alignment; fixed inconsistencies.
v1.1.3: Security hardening, removed direction labels.
v1.1.2: Plain text output, flexible stop IDs.
v1.1.1: Metadata updates.
v1.1.0: Security fixes, cache TTL 30min, validate stop id, fix stop-eta endpoint.
v1.0.0: Initial release.
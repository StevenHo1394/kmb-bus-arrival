# 🚌 KMB Bus Arrival Skill v1.1.4

Real-time KMB bus arrival information for Hong Kong using the official government transport API.

---

## 📁 Package Structure

<pre>
kmb-bus-arrival/
    ├── kmb_bus.py          (main executable)
    ├── SKILL.md            (OpenClaw skill definition)
    └── README.md           (documentation)
</pre>

## 🚀 Quick Start

1. Extract the ZIP file
2. Copy `kmb-bus-arrival/` to your OpenClaw `skills/` directory
3. Restart OpenClaw or reload skills
4. Use the skill with commands like:
   - `getRouteDirection 182`
   - `getNextArrivals 182 I ST871`  (or use 16-hex stop ID like `4ED04A0F5F9FF05F`)

## 📊 Features

- ✅ Real-time ETA from HK Government API
- ✅ 30-minute cache TTL, auto-purge
- ✅ Fast retry (3 attempts, ≤5s total)
- ✅ Accepts both short (e.g., ST871) and 16-hex stop IDs
- ✅ **No external dependencies** (Python stdlib only)
- ✅ Security-hardened (LOW risk)
- ✅ Supports all KMB routes
- ✅ Human-friendly **plain text output** for `getNextArrivals`; other tools return JSON
- ✅ Chinese & English stop names; never exposes raw stop IDs


**Author:** Steven Ho
**Repository:** https://github.com/StevenHo1394/kmb-bus-arrival

## 📄 Output Format (getNextArrivals)

The `getNextArrivals` tool prints human-readable plain text:

```
*68A (To Destination)*

    Stop: *Human Readable Name*

    Next arrivals:
    - 18:58 HKT
    - 19:15 HKT
    - 19:28 HKT
```

If no arrivals: `- No active ETAs`

## 🔒 Security

- Input validation: route (alphanumeric), stop ID (1-16 alphanumeric), direction (O/I/outbound/inbound)
- No command injection (pure Python, no subprocess)
- SSL verification enforced
- Timeouts: per-request ≤2s, total ≤5s
- No sensitive logging; generic errors
- Cache in `/tmp/kmb_bus_cache`; auto-cleaned after 30 min

## 📝 Version History

**v1.1.4** (2026-03-31)
- Fixed all documentation/code inconsistencies: getNextArrivals plain text, other tools JSON; no raw stop IDs in any user output; cache TTL 30min everywhere; error formats aligned.
- Removed direction labels from multi-direction outputs.
- Plain‑text errors for getNextArrivals; JSON errors for other tools.
- Auto‑direction (`direction="auto"`) and alternate stop ID fallback retained.

v1.1.3: Security hardening, consistency fixes, removed outbound/inbound labels.
v1.1.2: Plain text output, flexible stop IDs, never shows raw stop IDs.
v1.1.1: Metadata updates.
v1.1.0: Security fixes, cache TTL 30min, validate stop id, fix stop-eta endpoint.
v1.0.0: Initial release.
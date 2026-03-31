# 🚌 KMB Bus Arrival Skill v1.1.2

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
- ✅ Human-friendly **plain text output** (Ready for WhatsApp)
- ✅ Chinese & English stop names


**Author:** Steven Ho
**Repository:** https://github.com/StevenHo1394/kmb-bus-arrival

## 📄 Output Format (getNextArrivals)

The `getNextArrivals` tool prints human-readable plain text:

```
*68A outbound - 朗屏邨總站 (Long Ping Estate Bus Terminus)*

Stop: *朗屏邨總站 (Long Ping Estate Bus Terminus)*

Next arrivals:
- 16:42 HKT
- 16:56 HKT
- 17:10 HKT
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

**v1.1.2** (2026-03-31)
- Alternate stop ID fallback: If the given stop ID isn't on the route, searches the route's stop list for a matching human-readable name (Chinese/English) and uses that ID automatically. Handles multiple IDs for same location (e.g., Panda Hotel: TW280 on 31, TW281 on E31).
- Auto-direction detection: `direction="auto"` tries both inbound/outbound; shows both if stop serves both directions
- Plain text output with `*Route (To Destination)*` header
- Combined Chinese/English stop names; never exposes raw stop IDs
- Pure Python urllib (no curl); accepts short & 16‑hex stop IDs
- Security review: LOW risk

Earlier versions: Metadata updates, security fixes, cache TTL 30min, validate stop id, fix stop-eta endpoint.
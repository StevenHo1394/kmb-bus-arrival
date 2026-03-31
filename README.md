# 🚌 KMB Bus Arrival Skill v1.1.1

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
   - `getNextArrivals 182 I 4ED04A0F5F9FF05F`

## 📊 Features

- ✅ Real-time ETA from HK Government API
- ✅ 30‑minute cache TTL, auto-purge
- ✅ Fast retry (3 attempts, ≤5s total)
- ✅ Strict 16‑char stop ID validation
- ✅ Security-hardened
- ✅ Supports all KMB routes
- ✅ Chinese & English stop names


**Author:** Steven Ho  
**Repository:** https://github.com/StevenHo1394/kmb-bus-arrival

## 🔒 Security

- Input validation: route (alphanumeric), stop ID (16-char hex), direction (O/I/outbound/inbound)
- No command injection: array-form subprocess, no shell
- SSL verification enforced
- Timeouts: curl max 2s, Python timeout 3s, total ≤5s
- No sensitive logging; generic errors
- Cache in `/tmp/kmb_bus_cache`; auto-cleaned after 30 min

## 📝 Version History

**v1.1.1** (2026-03-31)
- Bump version and metadata (author, repo)
- Security review passed; risk level LOW
- Fast retry with exponential backoff
- Strict 16-char hex stop ID enforcement

v1.1.0: Security fixes, cache TTL 30min, validate stop id length, fix stop-eta endpoint
v1.0.0: Initial release
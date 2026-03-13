markdown
# 🚌 KMB Bus Arrival Skill v1.1.0

Real-time KMB bus arrival information for Hong Kong using the official government transport API.

---

## 📁 Package Structure

<pre>
kmb-bus-arrival/
    ├── kmb_bus.py          (main executable)
    ├── kmb_bus.sh          (shell wrapper)
    ├── SKILL.md            (OpenClaw skill definition)
    └── README.md           (documentation)
</pre>

## 🚀 Quick Start

1. Extract the ZIP file
2. Copy `kmb-bus-arrival/` to your OpenClaw `skills/` directory
3. Restart OpenClaw or reload skills
4. Use the skill with commands like:
   - `getRouteDirection E31`
   - `getNextArrivals E31 I TW281`

## 📊 Features

- ✅ Real-time ETA from HK Government API
- ✅ 5-minute caching
- ✅ Supports all KMB routes
- ✅ Chinese & English stop names
- ✅ Automatic retry on errors

## 📦 Download

File: `kmb-bus-arrival-v1.1.0.zip`

Ready for Clawhub upload!


This will render nicely on GitHub with emojis, code block for the tree, and clear sections.

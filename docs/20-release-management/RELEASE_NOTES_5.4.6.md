# Network Swiss Tool Pro - Release Notes v5.5.0 (Total Dependency Bundle)

## Date: 2026-04-19

### 📦 Total Dependency Bundle Overhaul

Version 5.5.0 addresses the "missing link" in the CLI terminal connectivity. We identified that specific invisible sub-dependencies of Flask-SocketIO (specifically `wsproto`, `bidict`, and `h11`) were being excluded from the standalone binary by the automated scanner.

### 🔧 Key Infrastructure Fixes

- **Deep Collection Hooks**: We have completely reconfigured the build system to use "Collector Hooks." Instead of manually listing modules, the tool now performs a deep recursive scan of the `flask-socketio`, `socketio`, and `engineio` stacks to ensure 100% of their child-libraries are bundled.
- **Explicit Child-Library Injection**: Manually forced the inclusion of `wsproto` (WebSocket protocol support) and `bidict` (Internal mapping) into the core binary.
- **Enhanced Dependency Splash**: The log at `logs/operations.log` now explicitly tracks and reports the presence of `wsproto` and `bidict` at boot time, giving us definitive proof that the library is correctly bundled.
- **Protocol Loop Consistency**: Hardened the internal communication loop to use Port 5051 with the full multi-transport stack verified and active.

### 📦 Build Info
- Rebuilt at **v5.5.0**.
- Dependency Bundle: **Exhaustive**.
- Handshake Reliability: **Maximum**.

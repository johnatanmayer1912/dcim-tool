# Network Swiss Tool Pro - Release Notes v5.5.0 (Infrastructure Stabilization)

## Date: 2026-04-19

### 🛡️ Critical Infrastructure Stabilization

Following persistent reports of SocketIO "staying offline," version 5.5.0 introduces a comprehensive "Deep Dive" diagnostic and stabilization suite. We have left no stone unturned to expose why the handshake is failing in specific Windows environments.

### 🔧 Key Stabilization Features

- **Dependency Splash (Diagnostics)**: At every boot, the tool now generates a technical report in `logs/operations.log` detailing the exact versions of the Flask, SocketIO, and EngineIO libraries in use. This allows us to spot environment-specific library clashes immediately.
- **Pre-Flight Port Probing**: The tool now verifies if Port 5000 is occupied by another process *before* starting. If blocked, it logs a CRITICAL warning to the operations log.
- **Frontend Error Console**: The terminal now features a "Handshake Listener." If connectivity fails, it will display the **Actual Technical Error Code** (e.g., `XHR_POLL_ERROR`, `CONNECTION_TIMEOUT`) directly on your terminal screen for instant troubleshooting.
- **Hardened Handshake Protocol**: We have significantly increased protocol timeouts (30s) and reduced keep-alive intervals (10s) to maintain stability on machines with aggressive local security scanning.
- **Hidden Import Hardening**: Added specialized sub-drivers (`engineio.async_socketio`, `socketio.async_namespace`) to the build system that are required for stable WebSocket communication in compiled binary environments.

### 📦 Build Info
- Rebuilt at **v5.5.0**.
- Massive stabilization overhaul.
- Diagnostics enabled by default.

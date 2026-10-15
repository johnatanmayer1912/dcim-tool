# Network Swiss Tool Pro - Release Notes v5.5.0 (Transport Hardening)

## Date: 2026-04-19

### 🛰️ Transport Hardening & "Offline" Fix

Version 5.5.0 addresses the "Server Offline" issue experienced by users in restricted network environments where WebSocket upgrades are blocked by local security policies or firewalls.

### 🔧 Key Infrastructure Improvements

- **Forced Polling Fallback**: The tool now prioritizes "Long Polling" as the base transport layer. This is universally compatible and ensures the terminal works even when WebSockets are disabled by your organization's security policy.
- **Deep Engine.IO Diagnostics**: We have enabled full backend logging for transport events. The tool now writes granular communication details to `logs/operations.log`, allowing us to debug complex "Offline" scenarios instantly.
- **UI Mode Reporting**: The terminal status bar now shows the active transport method (e.g., **SERVER: OK (POLLING)** or **SERVER: OK (WEBSOCKET)**).
- **Unsafe-Mode Server**: Forced the background server into a high-resiliency mode (`allow_unsafe_werkzeug`), preventing initialization hangs in bundled executable environments.

### 📦 Build Info
- Rebuilt at **v5.5.0**.
- Verified compatibility with local security software (Endpoint Protection).
- Standard bi-directional health checks operational.

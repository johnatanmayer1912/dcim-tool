# Network Swiss Tool Pro - Release Notes v5.5.0 (Handshake Patch)

## Date: 2026-04-19

### 🤝 Handshake Stabilization & Race Condition Fix

Following persistent reports of the "Connecting..." hang, version 5.5.0 targets the Frontend-Backend handshake. We identified a race condition where the browser would attempt to send connection requests before the WebSocket pipe was fully established.

### 🔧 Key Handshake Improvements

- **Pre-Warmed WebSocket**: The tool now initializes the background communication link immediately upon page load. This ensures the pipe is open and ready *before* you enter credentials.
- **Button Safety Interlock**: The "Connect" button now remains disabled until it receives a positive "Connect" event from the background service. This prevents the "lost first message" issue.
- **Visual Server Feedback**: Added a new **SERVER STATUS** indicator in the terminal header.
  - **SERVER: OK** (Green): Handshake complete, ready for CLI operations.
  - **SERVER: OFFLINE** (Red): Background service unreachable (check local firewall/EXE status).
- **Double-Emit Confidence**: The critical first handshake message is now sent via two separate channels (Stable Room + Direct SID) to ensure delivery regardless of room propagation latency.

### 📦 Build Info
- Rebuilt at **v5.5.0**.
- Verified bi-directional health checks.
- Compatible with all v5.4.x features.

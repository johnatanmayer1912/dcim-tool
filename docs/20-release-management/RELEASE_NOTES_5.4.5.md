# Network Swiss Tool Pro - Release Notes v5.5.0 (Port Diversification)

## Date: 2026-04-19

### 🚀 Port Diversification Migration

Version 5.5.0 implements a critical infrastructure change to finalize the CLI connectivity fix. We have migrated the entire tool ecosystem from the standard Port 5000 to the dedicated **Port 5051**.

### 🔧 Why this change was made:

- **Conflict Elimination**: Port 5000 is heavily used by Windows background services, AirPlay, and UPnP discovery. By moving to **5051**, we bypass these "crowded" frequencies and ensure the SocketIO handshake reaches its destination without interference.
- **Improved Handshake Stability**: A clean port allows the "Long Polling" and "WebSocket" protocols to establish without being intercepted or delayed by other system traffic.

### 🛠️ Key Improvements

- **Auto-Launcher Update**: The tool now automatically opens your browser at `http://127.0.0.1:5051`.
- **System-Wide Sync**: Both the Web UI and the real-time CLI stream now communicate exclusively on 5051.
- **Port Probe Enhanced**: The internal health-check now specifically verifies Port 5051 is free before initialization.

### 📦 Build Info
- Rebuilt at **v5.5.0**.
- Port Conflict Mitigation: **Active**.
- Compatible with all v5.4.x diagnostic features.

**Note**: If you have manually created bookmarks, please update them to use `:5051`.

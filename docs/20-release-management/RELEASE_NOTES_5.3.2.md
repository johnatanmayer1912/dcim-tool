# Network Swiss Tool Pro - Release Notes v5.3.2

## Date: 2026-04-19

### 🚀 Performance & UI Patch

Version 5.3.2 addresses the "stuck on connecting" issue experienced during SSH handshakes, particularly on slower devices or those with complex login banners.

### 🔧 Fixes & Refinements

- **Hard Connection Deadlines:** Implemented a `ThreadPoolExecutor` wrapper with a strict 45-second wall-clock timeout. This ensures the application never hangs indefinitely during a stalled SSH handshake.
- **Boot Optimization:** Removed intrusive `find_prompt()` and `enable()` calls during the initial connection phase. The terminal now identifies the host via the non-blocking `base_prompt` attribute, significantly reducing initial RTT.
- **Fast CLI Mode:** Enabled `fast_cli=True` by default for all sessions, drastically reducing internal Netmiko polling delays and improving command responsiveness.
- **Crashes Resolved:** Removed the invalid `read_timeout` parameter from `send_command()` which was incompatible with Netmiko 4.1.2.
- **Live UI Heartbeats:** Added a new `cli_progress` WebSocket event. The terminal now displays real-time connection status messages (e.g., "Initiating SSH handshake...", "Identified as NYC-SW01") while waiting for the session to establish.

### 📦 Build Info
- Rebuilt from source into `NetworkSwissToolPro_v5_3_2_Offline.exe`.
- All dependencies including `flask-socketio` and specialized `engineio` drivers verified.

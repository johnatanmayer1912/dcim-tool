# Network Swiss Tool Pro - Release Notes v5.3.3

## Date: 2026-04-19

### 🛡️ Critical Stability & "Infinite Spin" Fix

Version 5.3.3 is a critical patch that resolves a silent backend failure responsible for the "Stuck in CONNECTING" state in the Web CLI. 

### 🔧 Fixes & Refinements

- **Resolution of Silent Crash**: Fixed a critical `NameError` in the background connection task. Previously, a logic error caused the SSH worker thread to die instantly without reporting failure to the UI, leaving the terminal permanently "Connecting."
- **Internal Watchdog**: Implemented a global exception watchdog for the background connector. Any internal system failure or unexpected thread crash is now intercepted and reported directly to your terminal screen as a technical error message.
- **Real-Time Handshake Streaming**: Revolutionized the connection UX by streaming real-time handshake events. You no longer need to guess the status; the terminal now prints live updates:
  - `[INFO] Authenticating with credentials...`
  - `[INFO] Handshake successful, resolving prompt...`
  - `[INFO] Identified as CORE-SW-01`
- **SSH Deep Debugging**: Enabled granular Netmiko session logging by default. In the event of a connection failure, a detailed trace of the *raw SSH interaction* is now saved to `logs/ssh_debug_[session_id].log`.

### 📦 Build Info
- Rebuilt from source into `NetworkSwissToolPro_v5_3_3_Offline.exe`.
- Re-validated dependency integrity for all air-gapped environment requirements.

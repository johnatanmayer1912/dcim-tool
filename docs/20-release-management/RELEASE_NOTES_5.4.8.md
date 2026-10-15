# Network Swiss Tool Pro - Release Notes v5.5.0 (Connectivity Handshake Hardening)

## Date: 2026-04-19

### 📡 Connectivity Handshake Synchronization

Version 5.5.0 targets the "last mile" connectivity between the browser and the internal server. Even with a perfect library bundle, certain Windows 11 configurations can block the "handshake" if the IP resolution is ambiguous.

### 🔧 Key Connectivity Features

- **Hardcoded IP Binding (`127.0.0.1`)**: We have bypassed the `localhost` name resolution entirely. By hardcoding the browser client to connect specifically to `127.0.0.1:5051`, we eliminate failures caused by IPv6 priority or local DNS mangling.
- **Frontend Technical Log (The "Black Box")**: A new collapsible "Technical Handshake Log" has been added to the CLI terminal. If you see "Offline," click the **[Debug]** toggle to see the real-time technical error codes (e.g., `XHR_POLL_ERROR`, `CONNECTION_REFUSED`) from the browser's perspective.
- **Diagnostics Endpoints**:
    - **Health Check**: Visit `http://127.0.0.1:5051/health` to verify the web server is alive.
    - **Debug Status**: Visit `http://127.0.0.1:5051/debug_status` to see a JSON report of the bundled libraries.
- **Hardened Handshake Protocol**: Handshake timeouts have been increased to **60 seconds** to accommodate systems with aggressive local security scanners that intercept and delay initial traffic.

### 📦 Build Info
- Rebuilt at **v5.5.0**.
- IP Binding: **Explicit 127.0.0.1**.
- Handshake Debugging: **Enabled in UI**.

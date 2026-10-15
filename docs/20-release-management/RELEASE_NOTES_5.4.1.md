# Network Swiss Tool Pro - Release Notes v5.5.0 (Resilience Patch)

## Date: 2026-04-19

### 🛡️ Connectivity & Stability Hardening

Following reports of persistent "Connecting..." hangs, version 5.5.0 introduces mission-critical resiliency features to ensure your terminal session is rock-solid and responsive.

### 🔧 Key Stability Improvements

- **Session-ID Rooms**: We have moved away from tracking browser-specific "Socket IDs." The tool now uses a **Stable Room** based on your unique `session_id`. This means if your browser briefly stutters or reconnects, your terminal updates will persistently find you, eliminating the "frozen" state.
- **Pre-Flight TCP Probe**: Every CLI connection now starts with a **Fast Probe (2-second timeout)**. If the device is down or blocked by a firewall, the tool will now report this **instantly** instead of hanging for 45+ seconds.
- **GSSAPI & DNS Bypass**: We have explicitly disabled GSSAPI authentication and reverse DNS lookups during the SSH handshake. This resolves common "silent hangs" experienced on enterprise networks with complex DNS or Kerberos configurations.
- **Fast Auth Failure**: Shortened authentication and banner timeouts to catch credential or protocol mismatches faster.

### 📦 Build Info
- Rebuilt at **v5.5.0**.
- Enhanced for reliability in unstable or high-latency network environments.
- Offline support verified.

# Network Swiss Tool Pro - Release Notes v5.5.0 (Major Update)

## Date: 2026-04-19

### ⚡ The "Interactive Shell" Revolution

Version 5.5.0 is a complete architectural overhaul of the CLI Terminal feature. We have moved from a "Script Executor" model (which caused hangs) to a **True Interactive Streaming Shell**.

### 🔧 Key Major Changes

- **Paramiko Streaming Engine**: We have bypassed high-level Netmiko logic for the terminal. The tool now uses raw Paramiko `invoke_shell()` to open a direct, persistent bi-directional pipe to the device.
- **Zero-Latency Character Echoing**: Every single keystroke you type is now sent *immediately* to the device. You will experience zero lag for tab-completion, backspacing, or interactive prompts.
- **Background Byte Shuffler**: A dedicated non-blocking reader thread now handles every session. Every byte the device returns is streamed to your browser in real-time, exactly like PuTTY or a native SSH client.
- **PTY Resize Support**: The terminal now synchronizes its column and row dimensions with the backend. This ensures that command output (like `show running-config`) is formatted perfectly regardless of your window size.
- **Resolved Handshake Hangs**: By using a raw transport handshake and eliminating the "prompt identification" phase, we have eliminated the 30-second "Connecting..." hangs that affected legacy or slow devices.

### 📦 Build Info
- Rebuilt at **v5.5.0**.
- Fully optimized for performance and offline/air-gapped usage.
- All technical dependencies for streaming (Socket.IO, Paramiko) verified.

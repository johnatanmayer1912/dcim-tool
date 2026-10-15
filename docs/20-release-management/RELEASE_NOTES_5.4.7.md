# Network Swiss Tool Pro - Release Notes v5.5.0 (Absolute Bundle & Crash Fix)

## Date: 2026-04-19

### 🛡️ Crash-Proof & Absolute Bundling

Version 5.5.0 is a critical stability update that resolves the "Script Exception" crashes seen in v5.5.0 and implements an "Absolute Bundle" strategy to ensure every communication component is included in the standalone executable.

### 🔧 Key Stability Improvements

- **Safe-Bootstrap Logic**: We have completely hardened the startup sequence. The "Dependency Splash" diagnostic logger now uses "Safe Imports." This means **the application will no longer crash at startup with a Windows error window**, even if a library is missing. It will simply log the status and continue, allowing you to access logs and help.
- **Absolute Collection (collect_all)**: We have switched the build system to use the most aggressive collection mechanism available in PyInstaller. This forcefully sweeps every data file, binary binary, and sub-module related to the SocketIO stack into the core binary.
- **Root Package Locking**: Explicitly locked the root packages (`flask_socketio`, `socketio`, `engineio`, `simple_websocket`) into the bundle to prevent the automated scanner from bypassing them.

### 📦 Build Info
- Rebuilt at **v5.5.0**.
- Startup Crash Protection: **Active**.
- Bundling Strategy: **Brute Force (collect_all)**.

**Note**: This version is designed to be the "Final Word" on the connectivity infrastructure failures by eliminating the possibility of a hard crash and maximizing the bundle's integrity.

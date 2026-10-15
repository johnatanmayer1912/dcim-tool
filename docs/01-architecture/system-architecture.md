# Network Swiss Tool Pro - System Architecture

| Metadata | Description |
| :--- | :--- |
| **Purpose** | Technical blueprint of the Network Swiss Tool Pro system design and data flow. |
| **Scope** | Core engine logic, threading model, plugin architecture, and module relationships. |
| **Related Documents** | [Project Overview](../00-overview/project-overview.md), [Backend Architecture](backend-architecture.md), [Plugin Architecture](plugin-architecture.md) |
| **Update Responsibility** | Lead Architect / Senior Software Engineer |
| **Version Awareness** | v6.9.5 |

---

## Table of Contents
1. [High-Level Architecture](#high-level-architecture)
2. [The v6.0 Plugin Platform](#the-v60-plugin-platform)
3. [Data Flow](#data-flow)
4. [Module Relationships](#module-relationships)
5. [Threading Model](#threading-model)
6. [Error Handling Strategy](#error-handling-strategy)
7. [State Management](#state-management)
8. [Security Model](#security-model)

---

## High-Level Architecture

### Supported operator UI: web only

```
┌─────────────────────────────────────────────────────────────┐
│  TIER 1: PRESENTATION                                        │
│  ┌──────────────┐                  ┌──────────────────┐    │
│  │   Web UI     │                  │  CLI Interface   │    │
│  │   (Flask)    │                  │   (Argparse)     │    │
│  │ 127.0.0.1    │                  │ backup/audit     │    │
│  └──────┬───────┘                  └────────┬────────┘    │
└─────────┼───────────────────────────────────┼──────────────┘
```

Tkinter (`vlan_checker_gui.py`) is **out of scope**. G-014 GUI/web parity is closed by design. Do not treat Desktop GUI as a supported operator tier.

```
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  TIER 2: BUSINESS LOGIC (ADAPTERS)                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           modules/adapters.py                        │   │
│  │  • Orchestrates device operations                   │   │
│  │  • Manages threading & concurrency                  │   │
│  │  • Handles report generation                       │   │
│  │  • Implements safety checks (dry-run, backup)      │   │
│  └─────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────┼──────────────────┬──────────────────┐
        │                  │                  │                  │
┌───────▼──────┐  ┌────────▼────────┐  ┌─────▼──────┐  ┌──────▼─────┐
│  OPERATIONS   │  │    UTILITIES    │  │  REPORTING │  │ INTERACTIVE│
│   MODULES     │  │                 │  │            │  │   SHELL    │
│               │  │ • network_base  │  │ • report_  │  │            │
│ • vlan_audit  │  │ • structured   │  │   formatter│  │ • cli_     │
│ • mac_trace   │  │   _logger      │  │            │  │   manager  │
│ • topology_   │  │ • config_backup│  │            │  │            │
│   mapper      │  │   _system      │  │            │  │            │
│ • interfaces  │  │                 │  │            │  │            │
│ • connectivity│  │                 │  │            │  │            │
└───────────────┘  └─────────────────┘  └────────────┘  └────────────┘
```

---

## The v6.0 Plugin Platform

### Overview

The v6.0 release transforms the Network Swiss Tool from a monolithic application into a **dynamic plugin platform**. This enables:

- **Hot Reload**: Add features without server restart
- **Sandboxed Execution**: Safe plugin upload and validation
- **Dynamic UI**: Forms auto-generated from plugin metadata
- **Version Control**: Rollback to previous plugin versions

### Plugin Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                     PLUGIN LIFECYCLE                               │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  DEVELOPER          SCRATCH/              PRODUCTION     VERSION   │
│                     SANDBOX               REGISTRY         VAULT   │
│     │                   │                     │                │   │
│     │  Write Plugin     │                     │                │   │
│     │ ────────────────> │                     │                │   │
│     │                   │                     │                │   │
│     │  Upload .py       │  Validate (AST)     │  Register      │   │
│     │ ──────────────────│────────────────────>│───────────────>│   │
│     │                   │  • Syntax check     │                │   │
│     │                   │  • Security scan    │  • METADATA    │   │
│     │                   │  • Contract check   │  • run() sig   │   │
│     │                   │                     │  • Banned      │   │
│     │                   │                     │    imports     │   │
│     │                   │                     │                │   │
│     │                   │                     │  Execute       │   │
│     │                   │                     │ ─────────────────>  │
│     │                   │                     │                │   │
│     │  Update Plugin    │                     │  Backup        │   │
│     │ ────────────────────────────────────────│───────────────>│   │
│     │                   │                     │                │   │
│     │  Rollback         │                     │  Restore       │   │
│     │ ─────────────────────────────────────────────────────────────>  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Plugin Contract

Every plugin MUST implement:

1. **METADATA Dictionary**: UI generation and discovery info
2. **run() Function**: Entry point with standardized signature
3. **Return Format**: `{"status": "success|fail", "data": {...}, "error": "..."}`
4. **Security Compliance**: No banned imports (os.system, subprocess, eval, exec)

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/plugins/list` | GET | Get all plugin metadata |
| `/api/plugins/reload` | POST | Hot-reload registry |
| `/api/plugins/upload` | POST | Upload and validate new plugin |
| `/api/plugins/history/<id>` | GET | Get version history |
| `/api/plugins/rollback` | POST | Restore previous version |

---

## Data Flow

### Example: VLAN Check Operation

```
User (Web)                    Backend                        Device
   │                            │                             │
   │ POST /api/execute          │                             │
   │ action=vlan_check          │                             │
   │───────────────────────────>│                             │
   │                            │                             │
   │  {"status": "started"}     │                             │
   │<──────────────────────────│                             │
   │                            │                             │
   │ [Thread Spawned]           │                             │
   │                            │ _vlan_check_thread()          │
   │                            │─────────────────────────────>│
   │                            │                             │
   │                            │ adapters.run_vlan_audit()     │
   │                            │─────────────────────────────>│
   │                            │                             │
   │                            │ [For each device]             │
   │                            │                             │
   │                            │ modules.vlan_audit.run()      │
   │                            │─────────────────────────────>│
   │                            │                             │
   │                            │   SSH Connect (Netmiko)       │
   │                            │   send_command: show vlan   │
   │                            │   disconnect                │
   │                            │<─────────────────────────────│
   │                            │                             │
   │                            │ report_formatter.write_...    │
   │                            │ add_log()                    │
   │                            │                             │
   │ GET /api/logs              │                             │
   │──────────────────────────>│                             │
   │  {"logs": ["..."]}         │                             │
   │<──────────────────────────│                             │
```

### Example 2: Topology Transformation Engine (v6.7.0)

When running the Topology Mapper in `vpc` mode, a special transformation pipeline triggers in `modules/adapters.py` before the JSON graph is returned to the frontend:

1. **Pair Detection**: Nodes with matching `vpc_domain_id` metadata are clustered.
2. **Node Abstraction**: Discovered VPC members are removed from the frontend nodes list and replaced by a single logical `VPC_Domain_<ID>` node.
3. **Shared Link Consolidation**: The engine iterates through all connections. Downstream links heading toward both physical switches in a vPC pair are merged into a single `vpc_shared` edge originating from the logical domain node, eliminating visual clutter.
4. **Orphan Identification**: Non-redundant links to single members are flagged as `vpc_orphan` (dashed red line).

### Example 2: Interactive CLI Terminal (v5.5.0)

```
User (Browser)                Backend (Flask)               Device (SSH)
   │                            │                             │
   │ ws.emit('cli_connect')     │                             │
   │───────────────────────────>│                             │
   │                            │ [Spawn ShellReader Thread]  │
   │                            │ cli_manager.connect()       │
   │                            │────────────────────────────>│
   │                            │   paramiko.invoke_shell()   │
   │                            │<────────────────────────────│
   │                            │                             │
   │ ws.emit('cli_data', "ls")  │                             │
   │───────────────────────────>│                             │
   │                            │ chan.send("ls")             │
   │                            │────────────────────────────>│
   │                            │                             │
   │                            │ [Data Ready in Channel]     │
   │ ws.emit('cli_output', "...")│ ShellReader.recv(4096)      │
   │<───────────────────────────│<────────────────────────────│
   │ (xterm.js renders output)  │                             │
```

---

## Module Relationships

### Core Dependencies

```
network_base.py (Foundation)
    ├── Used by: ALL modules
    ├── Provides:
    │   ├── connect_permissive()     # Netmiko connection
    │   ├── safe_connection()        # Context manager
    │   ├── build_json()             # Response formatter
    │   ├── get_devices_from_file()  # Inventory parser
    │   └── parse_vlan_output()      # VLAN parsing
    │
    └── Dependencies:
        └── netmiko

adapters.py (Orchestration Layer)
    ├── Calls:
    │   ├── modules.vlan_audit.run()
    │   ├── modules.mac_trace.run()
    │   ├── modules.topology_mapper.run()
    │   ├── modules.interfaces.run()
    │   ├── modules.connectivity.run()
    │   ├── modules.vlan_mgmt_production.*()
    │   ├── modules.config_backup.run()
    │   ├── modules.network_audit.run()
    │   ├── modules.vlan_compare.run()
    │   └── modules.save_config.run()
    │
    └── Uses:
        ├── utils.report_formatter
        ├── utils.structured_logger
        └── utils.config_backup_system

vlan_checker_web.py (Web Entry)
    ├── Uses:
    │   ├── modules.adapters
    │   ├── modules.cli_manager (for SocketIO events)
    │   ├── modules.vlan_audit
    │   └── utils.report_formatter
    │
    └── Provides:
        ├── Flask routes (/api/*)
        ├── WebSocket Handlers (cli_connect, cli_data)
        ├── Thread spawning
        └── Global log_queue management

modules/cli_manager.py (Shell Engine)
    ├── Uses: 
    │   ├── paramiko (invoke_shell)
    │   ├── threading (ShellReader)
    │   └── telnetlib_compat
    │
    └── Provides:
        ├── CLIConnection class
        ├── Raw byte streaming
        ├── PTY Resizing
        └── Session persistence
```

---

## Threading Model

### Web Edition Threading

```python
# Global state (shared across threads)
log_queue = []          # Thread-safe (append only)
session_log_file = ""   # Persistent log path

# API Handler (Main Thread)
@app.route('/api/execute', methods=['POST'])
def api_execute():
    # Spawn daemon thread
    threading.Thread(
        target=m[action][0], 
        args=m[action][1], 
        daemon=True  # Dies if main dies
    ).start()
    return jsonify({"status": "started"})

# Log Consumer (Main Thread serves via API)
@app.route('/api/logs')
def api_logs():
    global log_queue
    out = list(log_queue)  # Copy
    log_queue.clear()       # Clear
    return jsonify({"logs": out})
```

### Thread Safety Notes

| Resource | Thread Safety | Mechanism |
|----------|--------------|-----------|
| `log_queue` | ✅ Safe | List append + atomic copy/clear |
| `session_log_file` | ✅ Safe | File append is atomic per line |
| Netmiko connections | ✅ Safe | Each thread creates own connection |
| Device iteration | ✅ Safe | Each device processed sequentially |

---

## Error Handling Strategy

### Three-Layer Error Handling

```
Layer 1: Module Level (Per-Device)
├── Try-except around device operations
├── Return {"status": "fail", "error": "..."}
└── One device fails → others continue

Layer 2: Adapter Level (Per-Operation)
├── Try-except in thread functions
├── Log error via log_func
├── Continue with remaining devices
└── Report partial success

Layer 3: Thread Level (Critical)
├── Try-except around entire thread
├── Catch-all for unexpected errors
├── Log traceback
└── Thread dies gracefully
```

### Error Flow Example

```python
# Layer 1: Module
def run(device, user, pwd, enb_pwd, log_func):
    try:
        conn = connect_permissive(...)
        # ... do work ...
        return build_json(host, "success", data)
    except Exception as e:
        if log_func:
            log_func(f"[{host}] Error: {str(e)}")
        return build_json(host, "fail", {}, str(e))
    finally:
        if conn:
            conn.disconnect()  # Always cleanup

# Layer 2: Adapter
def run_vlan_audit(devices, user, pwd, enb_pwd, log):
    for dev in devices:
        res = modules.vlan_audit.run(dev, user, pwd, enb_pwd, log)
        if res['status'] == 'fail':
            log(f"[ERROR] {host}: {res['error']}")
            # Continue to next device!

# Layer 3: Thread
def _vlan_check_thread(devices, user, pwd, enb_pwd):
    try:
        add_log("--- Starting VLAN Check ---")
        modules.adapters.run_vlan_audit(devices, user, pwd, enb_pwd, add_log)
        add_log("--- VLAN Check Complete ---")
    except Exception as e:
        add_log(f"[CRITICAL ERROR] {str(e)}")
        add_log(traceback.format_exc())
```

---

## State Management

### Web Edition State

| State Type | Storage | Scope | Persistence |
|------------|---------|-------|-------------|
| Log Queue | `log_queue` (list) | Global, in-memory | Session only |
| Session Log | `session_log_file` | File on disk | Until deleted |
| Inventory | `inventory.txt` | File on disk | Permanent |
| Backup Configs | `backups/` directory | File on disk | Permanent |
| Reports | `reports/` directory | File on disk | Permanent |

### No Database Design

This application uses **file-based persistence** intentionally:
- No database setup required
- Portable (move files = move state)
- Human-readable
- Version control friendly

### File Locations

```
Project Root/
├── inventory.txt          # Device list
├── session_log_*.txt      # Runtime logs
├── vlan_audit_*.txt       # VLAN reports
├── mac_trace_*.txt        # MAC reports
├── topology_map_*.html    # Topology graphs
├── network_audit_*.csv    # Audit CSV
├── config_backups_*/      # Config snapshots
│   └── *_config.txt
├── backups/               # Structured backups
│   └── {hostname}/
│       └── config_YYYYMMDD_HHMMSS.txt
├── logs/                  # Structured logs
│   └── *.log
└── reports/               # Generated reports
    └── *.txt, *.csv, *.html
```

---

## Network Communication Flow

### Per-Device Connection Lifecycle

```
1. DNS Resolution (hostname → IP)
2. TCP Connect (port 22)
3. SSH Handshake
4. Authentication (user/pwd)
5. Enable Mode (if required, enb_pwd)
6. send_command("show ...")
7. Parse output
8. disconnect()
```

### Connection Timeouts

| Stage | Default | Configurable |
|-------|---------|--------------|
| TCP Connect | 30s | Yes (Netmiko) |
| SSH Auth | 30s | Yes (Netmiko) |
| Command Exec | 60s | Per-command |
| Total per device | ~2-5s typical | - |

---

## Extension Points

### Adding a New Module

1. Create `modules/my_feature.py`
2. Implement `run(device, user, pwd, enb_pwd, log_func=None)`
3. Return standard `{"status": "...", "data": {...}}`
4. Add adapter function in `modules/adapters.py`
5. Add thread function in `vlan_checker_web.py`
6. Add route mapping in `api_execute()`
7. Add UI button in `modules/web/templates/index.html`

### Module Template

```python
# modules/my_feature.py
from .network_base import connect_permissive, build_json

def run(device, user, pwd, enb_pwd="", log_func=None):
    host = device['host']
    conn = None
    
    try:
        if log_func:
            log_func(f"[{host}] Connecting...")
        conn = connect_permissive(device, user, pwd, enb_pwd)
        
        # Execute commands
        output = conn.send_command("show ...")
        
        if log_func:
            log_func(f"[{host}] Disconnecting...")
        conn.disconnect()
        conn = None
        
        return build_json(host, "success", {
            "true_host": hostname,
            "output": output
        })
        
    except Exception as e:
        return build_json(host, "fail", {}, str(e))
    finally:
        if conn:
            try:
                conn.disconnect()
            except:
                pass
```

---

## Performance Characteristics

| Operation | Typical Time | Bottleneck |
|-----------|-------------|------------|
| Connectivity Check | 1-3s per device | Network latency |
| VLAN Audit | 2-5s per device | Command execution |
| MAC Trace | 3-8s per device | MAC table size |
| Topology Map | 5-10s per device | CDP/LLDP parsing |
| Config Backup | 3-7s per device | Config size |

### Scaling Considerations

- **Sequential processing** - One device at a time per operation
- **No connection pooling** - Fresh connection per device
- **Memory efficient** - Results streamed to files, not held in memory
- **Thread-per-operation** - Not thread-per-device (avoid resource exhaustion)

---

## Security Considerations

### Credential Handling

```python
# Credentials flow:
User Input → API Request → Thread Function → Module → Netmiko

# Security measures:
1. Credentials in memory only (not logged)
2. Session logs strip sensitive data
3. No credential storage in reports
4. HTTPS recommended for production (Flask dev server = HTTP)
```

### Network Security

- SSH only (no Telnet in production)
- Enable password required for privileged commands
- Read-only operations preferred (VLAN mgmt is exception)
- Dry-run mode available for all changes

---

## Security Model

### Plugin Security (v6.0)

The Plugin Platform implements defense-in-depth security:

#### 1. Upload Validation (Gatekeeper)

Every plugin uploaded via `/api/plugins/upload` undergoes:

| Check | Method | Failure Action |
|-------|--------|----------------|
| **Syntax Validation** | `ast.parse()` | Reject with syntax error details |
| **METADATA Check** | AST extraction | Reject if required keys missing |
| **Security Scan** | Pattern matching for banned functions | Reject if `eval`, `exec`, `os.system` found |
| **Contract Validation** | Import + function signature check | Reject if `run()` function missing |

#### 2. Sandbox Execution

- Plugins loaded via `importlib.util` with isolated namespace
- No modification to `sys.modules` permanently
- Each plugin gets fresh module instance

#### 3. Rollback Protection

- Automatic backup before any plugin update
- Version vault at `backups/plugins/{plugin_name}/`
- Timestamped backups for audit trail

#### 4. Banned Patterns

The following are blocked by the security scanner:

```python
BANNED_IMPORTS = [
    'os.system', 'os.popen', 'subprocess.call', 'subprocess.Popen',
    'shutil.rmtree', 'eval', 'exec', 'compile', '__import__'
]
```

---

## Next Documentation

→ **For business logic:** Read [Backend Architecture](backend-architecture.md)
→ **For operations:** Read [Troubleshooting Guide](../07-operations/TS_ERROR_INDEX.md)
→ **For plugin development:** Read [Plugin Development Guide](../04-automation/plugin-development-guide.md)
→ **For build procedures:** Read [Exact Rebuild Procedure](../14-roadmap/README.md)

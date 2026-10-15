# Network Swiss Tool Pro - Backend Architecture

| Metadata | Description |
| :--- | :--- |
| **Purpose** | Technical documentation of the application's business logic, workflows, and core operations. |
| **Scope** | Connectivity checks, VLAN management, MAC tracing, topology mapping, and report generation. |
| **Related Documents** | [System Architecture](system-architecture.md), [Plugin Architecture](plugin-architecture.md), [Automation Workflows](../03-infrastructure/parsing-workflows.md) |
| **Update Responsibility** | Senior Software Engineer / Backend Lead |
| **Version Awareness** | v6.9.5 |

---

## Table of Contents
1. [Core Workflows](#core-workflows)
2. [Safety Mechanisms](#safety-mechanisms)
3. [Data Processing Pipeline](#data-processing-pipeline)
4. [Inventory Management](#inventory-management)
5. [Report Generation](#report-generation)

---

## Core Workflows

### 1. Connectivity Check Workflow

**Purpose:** Validate reachability and SSH authentication

```
User Request
    │
    ▼
┌─────────────────────┐
│ Target Scope Engine │ ← Filter inventory by group/target mode
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ For each device:    │
│   1. Ping test      │ ← subprocess.run(['ping', '-n', '1', host])
│   2. SSH connect    │ ← netmiko ConnectHandler
│   3. Auth verify    │ ← conn.find_prompt()
│   4. Logout         │ ← conn.disconnect()
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Report Results      │ ← Per-device PASS/FAIL
│ Summary Stats       │ ← X/Y devices reachable
└─────────────────────┘
```

**Key Logic:**
```python
# Ping check
param = '-n' if windows else '-c'
res = subprocess.run(['ping', param, '1', '-w', '2000', host], ...)
if res.returncode != 0:
    return {"ping": False, "error": "Ping unreachable"}

# SSH check
try:
    conn = connect_permissive(device, user, pwd, enb_pwd)
    conn.disconnect()
    return {"ping": True, "ssh": True}
except Exception as e:
    return {"ping": True, "ssh": False, "error": str(e)}
```

---

### 2. VLAN Audit Workflow

**Purpose:** Discover VLANs on devices and generate reports

```
User Request
    │
    ▼
┌─────────────────────┐
│ Filter Devices      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ For each device:    │
│   1. SSH Connect    │
│   2. Send command   │ ← "show vlan" (Cisco) or "show vlans" (Juniper)
│   3. Parse output   │ ← Regex pattern matching
│   4. Extract VLANs  │ ← (id, name, status) tuples
│   5. Logout         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Generate Reports    │
│ • Raw output (txt)  │
│ • Parsed table (txt)│
└─────────────────────┘
```

**VLAN Parsing Logic:**
```python
# Cisco IOS/NXOS Pattern
^(\d+)\s+([\w-]+)\s+([\w-]+)
# Example: "100   VLAN0100   active"

# Juniper ELS Pattern  
^\S+\s+([\w-]+)\s+(\d+)
# Example: "default   VLAN-Name   100"

# Juniper Legacy Pattern
^([\w-]+)\s+(\d+)
# Example: "VLAN-Name   100"
```

---

### 3. VLAN Management Workflow (Add/Rename/Delete)

**Purpose:** Modify VLANs with safety mechanisms

```
User Request
    │
    ▼
┌─────────────────────┐
│ Pre-Flight Checks   │
│ • Validate VLAN ID  │
│ • Validate name     │
│ • Check backup age  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ For each device:    │
│                     │
│ 1. PRE-CHANGE       │
│    • Backup config  │ ← Save running-config
│    • Record state   │
│                     │
│ 2. EXECUTION        │
│    • Dry-run?       │ ← If yes, simulate only
│    • Check existing │ ← Idempotency check
│    • Send commands  │ ← vlan X / name Y
│                     │
│ 3. POST-CHANGE      │
│    • Verify change  │ ← "show vlan"
│    • Log result     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Generate Reports    │
│ • Change log        │
│ • Pre-change snaps  │
│ • Rollback info     │
└─────────────────────┘
```

**Safety Checks:**

| Check | Purpose | Failure Action |
|-------|---------|----------------|
| Dry-run mode | Preview changes | No commands sent |
| Idempotency | Skip if already correct | Log "skip" |
| Pre-backup | Enable rollback | Store in backups/ |
| Post-verify | Confirm change worked | Log warning if failed |
| Age check | Warn if no recent backup | Warning only |

**Platform persistence (v7.0.48):**

| Platform | `device_type` | Apply | Save / persist |
|----------|---------------|-------|----------------|
| IOS / IOS-XE | `cisco_ios`, `cisco_xe` | config-set | `write memory` |
| NX-OS | `cisco_nxos` | config-set | `copy running-config startup-config` |
| IOS-XR | `cisco_xr`, `ios_xr` | config-set + **commit** | commit (in apply) |
| Junos | `juniper_junos` | set/delete + **commit** | commit (in apply) |

Runbook: [vlan-vendor-matrix.md](../07-operations/vlan-vendor-matrix.md)

---

**Purpose:** Find which port a MAC address is connected to

```
User Request
    │
    ▼
┌─────────────────────┐
│ Normalize MAC       │ ← Handle : . - formats
│ Format: aaaa.bbbb.cccc│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ For each device:    │
│   1. SSH Connect    │
│   2. Send command   │ ← "show mac address-table" (varies by platform)
│   3. Parse table    │ ← Find MAC match
│   4. Extract port   │
│   5. Logout         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Aggregate Results   │
│ • Found locations   │
│ • Not found list    │
│ • Error list        │
└─────────────────────┘
```

**MAC Normalization:**
```python
def normalize_mac(mac):
    # Input: "00:11:22:33:44:55" or "0011.2233.4455" or "00-11-22-33-44-55"
    # Output: "0011.2233.4455" (Cisco format)
    
    # Remove all separators
    clean = mac.replace(':', '').replace('.', '').replace('-', '').lower()
    # Format as aaaa.bbbb.cccc
    return f"{clean[0:4]}.{clean[4:8]}.{clean[8:12]}"
```

---

### 5. Topology Mapping Workflow

**Purpose:** Visualize network topology via CDP/LLDP

```
User Request (map_mode: 'all' | 'vpc')
    │
    ▼
┌─────────────────────┐
│ Filter Devices      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ For each device:    │
│   1. SSH Connect    │
│   2. Get neighbors  │ ← "show cdp neighbors detail"
│   3. Get interface  │ ← "show interface status"
│   4. Get vPC info   │ ← "show vpc" (NXOS only)
│   5. Parse data     │
│   6. Logout         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Deduplicate Links   │ ← Avoid bidirectional duplicates
│ Normalize Names     │ ← Safe node names
│ Color Code          │ ← By status (up/down)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Generate Vis.js     │
│ HTML Graph          │
│ • Nodes = devices   │
│ • Edges = links     │
│ • Tooltips = details│
└─────────────────────┘
```

**Link Deduplication Logic:**
```python
seen_links = set()
for edge in edges:
    # Normalize port names
    p1 = f"{from_node}:{normalize_port(from_port)}"
    p2 = f"{to_node}:{normalize_port(to_port)}"
    
    # Create canonical link key (sorted)
    link_key = tuple(sorted([p1, p2]))
    
    if link_key in seen_links:
        continue  # Skip duplicate
    seen_links.add(link_key)
    final_edges.append(edge)
```

---

## Safety Mechanisms

### 1. Dry-Run Mode

**All VLAN operations support dry-run:**

```python
def run_vlan_management(action, devices, user, pwd, enb_pwd, 
                        vid, vname, log, dry_run=False):
    
    if dry_run:
        log("[DRY-RUN] Commands that WOULD be executed:")
        log(f"  vlan {vid}")
        log(f"  name {vname}")
        # ... skip actual execution ...
        return
```

**User Flow:**
1. Select "Dry Run" checkbox
2. Click operation
3. Review commands that would run
4. If satisfied, uncheck and run live

---

### 2. Automatic Pre-Change Backup

**Before any VLAN modification:**

```python
# In vlan_mgmt_production.py
def add_vlan(device, user, pwd, enb_pwd, vid, vname, 
             dry_run=False, auto_backup=True, ...):
    
    if auto_backup and not dry_run:
        # Capture current config
        backup_result = capture_config(device, user, pwd, enb_pwd)
        backup_path = backup_result['path']
        
        # Now proceed with change
        # If something goes wrong, rollback to backup_path
```

**Backup Storage:**
```
backups/
└── {hostname}/
    └── config_YYYYMMDD_HHMMSS.txt
```

---

### 3. Idempotency Checks

**Don't change what's already correct:**

```python
def add_vlan(...):
    # Check if VLAN already exists with correct name
    existing = get_vlan_info(conn, vid)
    
    if existing and existing['name'] == vname:
        return {
            "status": "success",
            "data": {
                "skipped": True,
                "reason": f"VLAN {vid} already exists with name '{vname}'"
            }
        }
    
    # Only proceed if change is needed
    ...
```

---

### 4. Post-Change Verification

**Verify the change actually worked:**

```python
def add_vlan(...):
    # Execute change
    conn.send_command(f"vlan {vid}")
    conn.send_command(f"name {vname}")
    
    # VERIFY
    post_check = conn.send_command("show vlan brief")
    
    if vlan_id_in_output(post_check, vid):
        return {"status": "success", "verification": "passed"}
    else:
        return {"status": "warning", 
                "error": "VLAN not found after creation"}
```

---

### 5. Error Isolation

**One device failure doesn't stop others:**

```python
# In adapters.py
for dev in devices:
    try:
        res = modules.vlan_audit.run(dev, user, pwd, enb_pwd, log)
        if res['status'] == 'success':
            success_count += 1
        else:
            log(f"[ERROR] {host}: {res['error']}")
            # Continue to next device!
    except Exception as e:
        log(f"[CRITICAL] {host}: {str(e)}")
        # Continue to next device!
```

---

## Data Processing Pipeline

### Raw → Parsed → Report

```
Device Output (Raw Text)
    │
    ▼
┌─────────────────────┐
│ Module Parser       │ ← Regex/line parsing
│ • Extract entities  │
│ • Normalize data    │
└──────────┬──────────┘
           │
           ▼
    Parsed Data (Dict/List)
           │
           ▼
┌─────────────────────┐
│ Adapter Processor   │ ← Business logic
│ • Aggregate         │
│ • Compare           │
│ • Analyze           │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Report Formatter    │ ← Format for output
│ • TXT reports       │
│ • CSV data          │
│ • HTML graphs       │
└─────────────────────┘
```

---

## Inventory Management

### Inventory Format

```
# inventory.txt - Three formats supported:

# Format 1: IP,DeviceType (Default group)
10.1.1.1,cisco_ios
10.1.1.2,juniper_junos

# Format 2: IP,DeviceType,Group
10.1.1.1,cisco_ios,CoreSwitches
10.2.1.1,juniper_junos,AccessLayer

# Format 3: Group Headers
[CoreSwitches]
10.1.1.1,cisco_ios
10.1.1.2,cisco_nxos

[AccessLayer]
10.2.1.1,juniper_junos
```

### Device Types

| Type | Platform | Commands |
|------|----------|----------|
| `cisco_ios` | Cisco IOS/IOS-XE | IOS syntax |
| `cisco_nxos` | Cisco NXOS | NXOS syntax |
| `cisco_xe` | Catalyst IOS-XE | IOS syntax |
| `juniper_junos` | Juniper JunOS | JunOS syntax |
| `hp_comware` | HP/H3C Comware | Comware syntax |

### Target Scope Engine

```python
def filter_inventory(inv_str, target_mode, filter_str, 
                     single_host, group_filter="All"):
    # 1. Parse inventory
    devices = parse_inventory(inv_str)
    
    # 2. Filter by Group
    if group_filter != "All":
        devices = [d for d in devices 
                   if d['group'] == group_filter]
    
    # 3. Filter by Target Mode
    if target_mode == 'single':
        # Return only matching host
        return [d for d in devices 
                if d['host'] == single_host]
    elif filter_str:
        # Return matching host or type
        f = filter_str.lower()
        return [d for d in devices 
                if f in d['host'].lower() 
                or f in d['device_type'].lower()]
    else:
        # Return all
        return devices
```

---

## Report Generation

### Report Types

| Type | Extension | Use Case |
|------|-----------|----------|
| Text Report | `.txt` | Human-readable logs |
| CSV Data | `.csv` | Spreadsheet analysis |
| HTML Graph | `.html` | Visual topology |

### Report Formatter

```python
# utils/report_formatter.py

def write_text_file(filename, content):
    """Write plain text report"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

def write_csv_file(filename, fieldnames, data):
    """Write CSV report"""
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def generate_topology_html(filename, node_count, edge_count,
                           nodes_json, edges_json, vis_js_content, extra_header=""):
    """Generate Vis.js topology graph"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><title>Topology Map</title></head>
    <body>
        <div id="mynetwork"></div>
        <script>{vis_js_content}</script>
        <script>
            var nodes = new vis.DataSet({nodes_json});
            var edges = new vis.DataSet({edges_json});
            // ... Vis.js initialization ...
        </script>
    </body>
    </html>
    """
    with open(filename, 'w') as f:
        f.write(html)
```

### Timestamp Convention

All reports use timestamped filenames:
```python
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"{operation}_{ts}.{ext}"
# Example: vlan_audit_20260414_143022.txt
```

---

## Next Documentation

→ **For troubleshooting:** Read [Troubleshooting Index](../07-operations/TS_ERROR_INDEX.md)
→ **For reference:** Read [Prompt Command Center](../12-master-prompts/PROMPT_COMMAND_CENTER.md)

# Prompt P01: Create Project Foundation

> **Objective:** Establish project structure, core utilities, and base files

---

## 🎯 Goal

Create the foundational structure for Network Swiss Tool Pro v4.5.7 including:
1. Folder structure
2. Report formatter utility
3. VERSION file
4. Basic README
5. Inventory template

---

## ✅ Prerequisites

- Python 3.12+ installed
- Working directory: `Net_mngmnt_tool - windsurf/`

---

## 📁 Step 1: Create Folder Structure

Execute these commands to create the folder hierarchy:

```bash
# Create all necessary directories
New-Item -ItemType Directory -Force -Path "modules", "modules/web", "modules/web/templates", "utils", "docs", "logs", "reports", "backups", "dist"
```

**Expected Structure:**
```
Net_mngmnt_tool/
├── modules/
│   └── web/
│       └── templates/
├── utils/
├── docs/
├── logs/
├── reports/
├── backups/
└── dist/
```

---

## 📝 Step 2: Create VERSION File

Create file: `VERSION`

```
4.5.7
```

---

## 📝 Step 3: Create Report Formatter Utility

Create file: `utils/report_formatter.py`

```python
"""
Report Formatter Utility
Handles TXT, CSV, and HTML report generation.
"""
import csv
import os
from datetime import datetime


def write_text_file(filename, content):
    """Write plain text report to file."""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)


def append_text_file(filename, content):
    """Append to text file (creates if doesn't exist)."""
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(content)


def write_csv_file(filename, fieldnames, data):
    """Write CSV report with headers and data rows."""
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def write_files_in_directory(directory, file_map):
    """Write multiple files to a directory.
    
    Args:
        directory: Target directory path
        file_map: Dict of {filename: content}
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    for filename, content in file_map.items():
        filepath = os.path.join(directory, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)


def init_vlan_parsed_report(filename):
    """Initialize VLAN parsed report with header."""
    header = f"VLAN Parsed Report - Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    header += "=" * 60 + "\n\n"
    write_text_file(filename, header)


def append_vlan_parsed_report(filename, hostname, vlan_list):
    """Append VLAN data for a device to parsed report.
    
    Args:
        filename: Report file path
        hostname: Device hostname
        vlan_list: List of (id, name, status) tuples
    """
    content = f"\n[{hostname}]\n"
    content += "-" * 40 + "\n"
    for vid, name, status in vlan_list:
        content += f"  VLAN {vid}: {name} ({status})\n"
    append_text_file(filename, content)


def generate_topology_html(filename, node_count, edge_count, 
                           nodes_json, edges_json, vis_js_content,
                           extra_header=""):
    """Generate Vis.js topology visualization HTML.
    
    Args:
        filename: Output HTML file path
        node_count: Number of nodes
        edge_count: Number of edges
        nodes_json: JSON string of Vis.js nodes
        edges_json: JSON string of Vis.js edges
        vis_js_content: Vis.js library code
        extra_header: Optional HTML to insert in header
    """
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Network Topology Map</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        #header {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        #mynetwork {{
            width: 100%;
            height: 600px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
        }}
        .stats {{
            color: #7f8c8d;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div id="header">
        <h1>Network Topology Map</h1>
        <div class="stats">Nodes: {node_count} | Links: {edge_count}</div>
        {extra_header}
    </div>
    <div id="mynetwork"></div>
    
    <script>{vis_js_content}</script>
    <script>
        var nodes = new vis.DataSet({nodes_json});
        var edges = new vis.DataSet({edges_json});
        
        var container = document.getElementById('mynetwork');
        var data = {{nodes: nodes, edges: edges}};
        var options = {{
            nodes: {{
                shape: 'box',
                font: {{size: 14}},
                borderWidth: 2,
                shadow: true
            }},
            edges: {{
                width: 2,
                smooth: {{type: 'cubicBezier'}},
                color: {{color: '#607d8b'}}
            }},
            physics: {{
                stabilization: false,
                barnesHut: {{
                    gravitationalConstant: -2000,
                    centralGravity: 0.3,
                    springLength: 95,
                    springConstant: 0.04,
                    damping: 0.09,
                    avoidOverlap: 0.5
                }}
            }},
            interaction: {{
                hover: true,
                tooltipDelay: 200
            }}
        }};
        
        var network = new vis.Network(container, data, options);
    </script>
</body>
</html>"""
    
    write_text_file(filename, html_content)


def _load_vis_js():
    """Load Vis.js library code for embedding in HTML."""
    # Minified Vis.js v9.1.2
    return """
    /*! vis.js 9.1.2 | MIT License */
    // Vis.js library would be here - using CDN version instead
    // In production, this should be the actual library code
    """


# Alias for backward compatibility
def init_report(filename, title="Report"):
    """Initialize a report file with header."""
    header = f"{title}\n"
    header += "=" * 60 + "\n"
    header += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    write_text_file(filename, header)
```

---

## 📝 Step 4: Create Basic README

Create file: `README.md`

```markdown
# Network Swiss Tool Pro

**Version:** 4.5.7  
**A multi-mode network management toolkit for Cisco, Juniper, and NXOS devices.**

## Quick Start

### Web Edition (Recommended)
```bash
python vlan_checker_web.py
# Open browser: http://127.0.0.1:5000
```

### Desktop GUI
```bash
python main.py gui
```

### CLI Mode
```bash
python main.py cli --task connectivity --user admin
```

## Features

- **Connectivity & Auth Check** - Ping + SSH validation
- **VLAN Audit** - Discovery and reporting
- **VLAN Management** - Add/Rename/Delete with dry-run
- **MAC Address Trace** - Find which port a MAC is on
- **Interface Status** - Up/down status with descriptions
- **Topology Mapping** - CDP/LLDP visualization
- **Config Backup** - Automated backups
- **Network Audit** - Hardware/OS inventory

## Inventory Format

Create `inventory.txt`:
```
[CoreSwitches]
10.1.1.1,cisco_ios
10.1.1.2,cisco_nxos

[AccessLayer]
10.2.1.1,juniper_junos
```

## Requirements

- Python 3.12+
- Netmiko: `pip install netmiko`
- Flask: `pip install flask`

## Documentation

See `docs/` folder for full documentation.
```

---

## 📝 Step 5: Create Inventory Template

Create file: `inventory.txt`

```
# Network Swiss Tool Pro - Sample Inventory
# Format: IP,DeviceType,Group (Group is optional)
#
# Device Types:
#   - cisco_ios    (Cisco IOS/IOS-XE)
#   - cisco_nxos   (Cisco NXOS)
#   - cisco_xe     (Catalyst IOS-XE)
#   - juniper_junos (Juniper JunOS)
#   - hp_comware   (HP/H3C Comware)
#
# Lines starting with # are comments
# [GroupName] creates a group header

[CoreSwitches]
#192.168.1.1,cisco_ios,CoreSwitches
#192.168.1.2,cisco_ios,CoreSwitches

[AccessLayer]
#192.168.2.1,cisco_ios,AccessLayer
#192.168.2.2,juniper_junos,AccessLayer

[Distribution]
#10.1.1.1,cisco_nxos,Distribution
#10.1.1.2,cisco_nxos,Distribution
```

---

## ✅ Verification

Run these checks to verify completion:

```bash
# 1. Check folders exist
Test-Path "modules/web/templates"
Test-Path "utils"
Test-Path "logs"

# 2. Check files exist
Test-Path "VERSION"
Test-Path "utils/report_formatter.py"
Test-Path "README.md"
Test-Path "inventory.txt"

# 3. Test Python imports
python -c "from utils import report_formatter; print('✓ report_formatter OK')"
```

**Expected Output:**
```
True
True
True
True
✓ report_formatter OK
```

---

## 🎯 Success Criteria

- [ ] All directories created
- [ ] `VERSION` file contains "4.5.7"
- [ ] `utils/report_formatter.py` created with all functions
- [ ] `README.md` created with basic documentation
- [ ] `inventory.txt` created with template
- [ ] Python imports work without errors

---

## 🚀 Next Step

When this prompt is complete and verified, proceed to:  
→ **P02-NETWORK-BASE.md** (Create network_base.py with connection handling)

---

## 💾 Checkpoint

Before proceeding, commit this work:
```bash
git add .
git commit -m "P01: Created project foundation - folders, utils, base files"
```

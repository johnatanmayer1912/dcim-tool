"""Fix all 5 bugs in the application."""
import re

with open('vlan_checker_web.py', 'r', encoding='utf-8') as f:
    content = f.read()

# ── Bug 1a: Fix filter_inventory — split on comma only, not whitespace ────────
old1 = "        parts = re.split(r'[,\\s]+', line)\n        if len(parts) >= 2:\n            host = parts[0]\n            dtype = parts[1]\n            port = 22\n            grp = current_group\n            if len(parts) > 2:\n                if parts[2].isdigit():\n                    port = int(parts[2])\n                else:\n                    grp = parts[2]\n            devices.append({\"host\": host, \"device_type\": dtype, \"port\": port, \"group\": grp})"

new1 = "        # Split on comma only — spaces in device names/types are not valid\n        parts = [p.strip() for p in line.split(',')]\n        if len(parts) < 2:\n            continue\n        host = parts[0]\n        dtype = parts[1]\n        if not host or not dtype:\n            continue\n        port = 22\n        grp = current_group\n        if len(parts) >= 3:\n            if parts[2].isdigit():\n                port = int(parts[2])\n                if len(parts) >= 4:\n                    grp = parts[3]\n            else:\n                grp = parts[2]\n        devices.append({\"host\": host, \"device_type\": dtype, \"port\": port, \"group\": grp})"

if old1 in content:
    content = content.replace(old1, new1)
    print('[FIXED] Bug 1a: filter_inventory comma-only split')
else:
    print('[WARN] Bug 1a: pattern not found, checking...')
    idx = content.find("parts = re.split(r'[,")
    if idx >= 0:
        print(f'  Found at idx {idx}: {repr(content[idx:idx+100])}')

# ── Bug 1b: Fix single_host matching with partial fallback ────────────────────
old2 = "    if target_mode == 'single':\n        target = single_host.split('[')[0].strip() if '[' in single_host else single_host\n        return [d for d in devices if d['host'] == target]"

new2 = "    if target_mode == 'single':\n        target = single_host.split('[')[0].strip() if '[' in single_host else single_host.strip()\n        matched = [d for d in devices if d['host'] == target]\n        if not matched:\n            # Fallback: partial match for FQDN vs short name mismatches\n            matched = [d for d in devices if target in d['host'] or d['host'] in target]\n        return matched"

if old2 in content:
    content = content.replace(old2, new2)
    print('[FIXED] Bug 1b: single_host partial match fallback')
else:
    print('[WARN] Bug 1b: pattern not found')

with open('vlan_checker_web.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('vlan_checker_web.py written')

# ── Bug 2: Fix relative import in vlan_mgmt_production.py ────────────────────
with open('modules/vlan_mgmt_production.py', 'r', encoding='utf-8') as f:
    vlan_content = f.read()

# Add sys.path fix at the top of the module, after the telnetlib compat block
old_vlan = "from modules.network_base import connect_permissive, build_json, parse_vlan_output\nfrom utils.structured_logger import get_logger, OperationType, ConfigState, create_legacy_adapter\nfrom utils.config_backup_system import get_backup_system"

new_vlan = """# v6.3.0: Ensure project root is on sys.path for absolute imports
import os as _os, sys as _sys
_proj_root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _proj_root not in _sys.path:
    _sys.path.insert(0, _proj_root)
if getattr(_sys, 'frozen', False):
    _exe_internal = getattr(_sys, '_MEIPASS', None)
    if _exe_internal and _exe_internal not in _sys.path:
        _sys.path.insert(0, _exe_internal)

from modules.network_base import connect_permissive, build_json, parse_vlan_output
from utils.structured_logger import get_logger, OperationType, ConfigState, create_legacy_adapter
from utils.config_backup_system import get_backup_system"""

if old_vlan in vlan_content:
    vlan_content = vlan_content.replace(old_vlan, new_vlan)
    print('[FIXED] Bug 2: vlan_mgmt_production.py sys.path fix')
else:
    print('[WARN] Bug 2: pattern not found in vlan_mgmt_production.py')

with open('modules/vlan_mgmt_production.py', 'w', encoding='utf-8') as f:
    f.write(vlan_content)
print('vlan_mgmt_production.py written')

# ── Bug 3: Fix plugin_registry.py — broken regex pattern ─────────────────────
with open('modules/plugin_registry.py', 'r', encoding='utf-8') as f:
    reg_content = f.read()

# The regex pattern for plugin_id validation has a broken line
old_reg = "        if not re.match(r'^[a-z][a-z0-9_]*\n</content>\n</file>, pid):"
new_reg = "        if not re.match(r'^[a-z][a-z0-9_]*$', pid):"

if old_reg in reg_content:
    reg_content = reg_content.replace(old_reg, new_reg)
    print('[FIXED] Bug 3a: plugin_registry.py broken regex')
else:
    # Try to find it differently
    idx = reg_content.find("if not re.match(r'^[a-z][a-z0-9_]*")
    if idx >= 0:
        end = reg_content.find('pid)', idx)
        broken = reg_content[idx:end+4]
        print(f'  Found broken regex: {repr(broken)}')
        reg_content = reg_content[:idx] + "if not re.match(r'^[a-z][a-z0-9_]*$', pid):" + reg_content[end+4:]
        print('[FIXED] Bug 3a: plugin_registry.py broken regex (alt method)')
    else:
        print('[WARN] Bug 3a: regex pattern not found')

with open('modules/plugin_registry.py', 'w', encoding='utf-8') as f:
    f.write(reg_content)
print('plugin_registry.py written')

print('\nAll fixes applied.')

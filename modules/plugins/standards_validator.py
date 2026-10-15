"""
modules/plugins/standards_validator.py
---------------------------------------
Standards Validator Plugin for Network Swiss Tool Pro v6.5.7

Compares live device configuration against a user-defined policy library
(YAML or JSON file) and produces a human-readable gap report with exact
OS-specific remediation commands per device. Read-only — never pushes changes.

WHAT IT DOES:
    For each device:
      1. Load the policy file (YAML or JSON) from policies/ folder or custom path
      2. Run each policy's check_command via SSH
      3. Apply the check_type logic (contains / not_contains / regex_match /
         regex_extract / line_format)
      4. If a violation is found: record current value, expected value,
         and the exact OS-specific remediation commands to fix it
      5. Generate professional HTML gap analysis report (downloadable)
      6. Generate per-device remediation script (ready to paste in config mode)
      7. Validate SSH connection logout after data collection

POLICY FILE FORMATS:
    YAML: policies/standards.yaml (default)
    JSON: policies/standards.json
    Custom: Any path via 'policy_file' parameter

POLICY FLEXIBILITY:
    Users can add custom fields to JSON policies without code changes.
    Standard fields: id, category, description, severity, platforms, 
    check_command, check_type, pattern, remediation
    Custom fields are preserved and accessible in reports.

OS-SPECIFIC REMEDIATION:
    Policies can define platform-specific remediation commands:
    {
        "remediation": {
            "cisco_ios": "ip ssh version 2",
            "cisco_nxos": "ssh version 2",
            "juniper_junos": "set system services ssh protocol-version v2"
        }
    }

CHECK TYPES:
    contains        — output must contain the pattern string/regex
    not_contains    — output must NOT contain the pattern string/regex
    regex_match     — output must match the regex (re.search)
    regex_extract   — extract a value with a capture group, compare to expected_format
    line_format     — every line matching line_filter must also match line_must_match

OUTPUT:
    reports/compliance/standards_{timestamp}.html — Professional HTML gap report
    reports/compliance/standards_{timestamp}.txt  — Human-readable text report
    reports/compliance/remediation_{host}_{ts}.txt — Per-device fix script
    reports/compliance/standards_{timestamp}.csv  — Machine-readable matrix

VERSION HISTORY:
    v1.0.0 (2026-04-28): Initial release
    v2.0.0 (2026-04-29): v6.5.7 - JSON support, OS-specific remediation, 
                        connection audit, professional HTML reports, policy dropdown API
"""

METADATA = {
    "plugin_id"           : "standards_validator",
    "display_name"        : "Standards Validator",
    "version"             : "2.1.0",
    "author"              : "Network Swiss Tool",
    "category"            : "Compliance",
    "description"         : (
        "Compares live device config against your organization's standards policy "
        "library (YAML or JSON). Reports violations with OS-specific remediation "
        "commands per device. Professional HTML gap analysis reports. "
        "Read-only — never pushes changes."
    ),
    "min_platform_version": "6.5.7",

    "required_params": {
        "policy_file": {
            "type"       : "dropdown",
            "label"      : "Policy Library",
            "placeholder": "Select policy file...",
            "default"    : "policies/standards.yaml",
            "required"   : False,
            "description": "Select from available YAML/JSON policy files, or upload custom.",
            "dynamic_options": True,  # Populated from /api/standards/policies
        },
        "severity_filter": {
            "type"   : "dropdown",
            "label"  : "Minimum Severity",
            "options": ["all", "low", "medium", "high", "critical"],
            "default": "all",
            "required": False,
            "description": "Only check policies at or above this severity level.",
        },
        "category_filter": {
            "type"       : "string",
            "label"      : "Category Filter (optional)",
            "placeholder": "Security, NTP, Naming  (comma-separated, blank = all)",
            "default"    : "",
            "required"   : False,
            "description": "Comma-separated list of policy categories to check.",
        },
        "generate_remediation_script": {
            "type"   : "checkbox",
            "label"  : "Generate Per-Device Remediation Scripts",
            "default": True,
            "description": "Write a ready-to-paste fix script for each non-compliant device.",
        },
        "output_format": {
            "type"   : "dropdown",
            "label"  : "Report Format",
            "options": ["html", "text", "both"],
            "default": "html",
            "required": False,
            "description": "Generate HTML report (professional), text report, or both.",
        },
    },

    "supports_parallel" : True,
    "supports_dry_run"  : False,
    "modifies_device"   : False,
    "requires_enable"   : False,
}

# ── Imports ───────────────────────────────────────────────────────────────────
from modules.network_base import safe_connection, build_json, safe_node_name, resolve_hostname_from_prompt
from utils.report_formatter import save_plugin_report, append_to_master_report
from datetime import datetime
import re
import os
import csv
import json
import glob

# yaml is part of PyYAML which is already in requirements.txt (pyyaml)
try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

# ── Path Resolution Helper ─────────────────────────────────────────────────────
def _get_resource_path(relative_path: str) -> str:
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    Matches the web app's _get_resource_path() function for consistency.
    v6.9.21: Checks program directory standards folder for uploaded files.
    """
    import sys
    if getattr(sys, 'frozen', False):
        # 1. Check sys._MEIPASS first (bundled resources)
        if hasattr(sys, '_MEIPASS'):
            bundled_path = os.path.join(sys._MEIPASS, relative_path)
            if os.path.exists(bundled_path):
                return bundled_path
        
        # 2. Check program directory (writable files like standards/ templates/)
        program_dir = os.path.dirname(sys.executable)
        program_path = os.path.join(program_dir, relative_path)
        if os.path.exists(program_path):
            return program_path
            
        # Fallback to bundled path
        return os.path.join(getattr(sys, '_MEIPASS', ''), relative_path)
    else:
        # Dev mode: Resolve relative to project root
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(base_path, relative_path)

# ── Policy File Discovery ─────────────────────────────────────────────────────

def list_available_policies(base_dir: str = None) -> list:
    """
    Scan for available policy files (YAML and JSON) in both the policies directory (bundled)
    and the standards directory (in the program directory for custom/uploaded files).
    
    Returns list of dicts:
        {
            "path": "policies/standards.yaml",
            "name": "Built-in Standards",
            "format": "yaml",
            "description": "...",
            "policy_count": 65
        }
    """
    import sys
    policy_files = []
    seen_paths = set()
    
    # Determine base directories
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        bundled_base = sys._MEIPASS
        program_base = os.path.dirname(sys.executable)
    else:
        # Dev mode: Resolve relative to project root
        bundled_base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        program_base = bundled_base
        
    # Folders to scan
    scan_dirs = [
        (os.path.join(bundled_base, "policies"), "policies"),
        (os.path.join(program_base, "standards"), "standards")
    ]
    
    for dir_path, prefix in scan_dirs:
        if not os.path.exists(dir_path):
            continue
        for ext in ["*.yaml", "*.yml", "*.json"]:
            pattern = os.path.join(dir_path, ext)
            for file_path in glob.glob(pattern):
                try:
                    filename = os.path.basename(file_path)
                    # Relative path prefix
                    rel_path = f"{prefix}/{filename}"
                    if rel_path in seen_paths:
                        continue
                        
                    file_ext = os.path.splitext(file_path)[1].lower()
                    
                    # Try to load and get metadata
                    policies, metadata = _load_policy_file_with_meta(file_path)
                    
                    policy_files.append({
                        "path": rel_path,
                        "name": metadata.get("name", filename),
                        "format": "json" if file_ext == ".json" else "yaml",
                        "description": metadata.get("description", "No description"),
                        "policy_count": len(policies),
                        "version": metadata.get("version", "unknown"),
                        "last_updated": metadata.get("last_updated", "unknown")
                    })
                    seen_paths.add(rel_path)
                except Exception as e:
                    # Skip files that can't be parsed
                    continue
    
    # Sort by name
    policy_files.sort(key=lambda x: x["name"])
    return policy_files


def _load_policy_file_with_meta(file_path: str) -> tuple:
    """
    Load a policy file (YAML or JSON) and return (policies_list, metadata_dict).
    
    v6.5.8: Now properly raises exceptions instead of silently falling back to builtin policies,
    allowing proper debugging of file loading issues.
    """
    print(f"[STANDARDS] _load_policy_file_with_meta: Loading {file_path}")
    
    ext = os.path.splitext(file_path)[1].lower()
    
    # v6.5.8: Read file first, then parse separately for better error handling
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"[STANDARDS] File read successfully: {len(content)} bytes")
    except Exception as e:
        print(f"[STANDARDS] ERROR reading file {file_path}: {e}")
        raise  # Re-raise to let caller handle it
    
    # Parse the content
    try:
        if ext == '.json':
            data = json.loads(content)
            print(f"[STANDARDS] JSON parsed successfully")
        elif _YAML_AVAILABLE:
            data = yaml.safe_load(content)
            print(f"[STANDARDS] YAML parsed successfully")
        else:
            raise RuntimeError("PyYAML is not available, cannot parse YAML policy file")
    except Exception as e:
        print(f"[STANDARDS] ERROR parsing {ext} file: {e}")
        raise  # Re-raise to let caller handle it
    
    # Normalize data structure
    if not isinstance(data, dict):
        print(f"[STANDARDS] Normalizing data: root is {type(data).__name__}, not dict")
        data = {"policies": data if isinstance(data, list) else []}
    
    policies = data.get('policies', [])
    metadata = data.get('metadata', {})
    
    print(f"[STANDARDS] Extracted {len(policies)} policies, metadata keys: {list(metadata.keys())}")
    
    # If no metadata name, use filename
    if not metadata.get('name'):
        metadata['name'] = os.path.basename(file_path)
    
    return policies, metadata


# ── OS-Specific Remediation ─────────────────────────────────────────────────

def _normalize_os_type(device_type: str) -> str:
    """
    Normalize device type to standard OS key for remediation lookup.
    
    Examples:
        'cisco_ios' -> 'cisco_ios'
        'cisco_nxos' -> 'cisco_nxos'
        'cisco_xe' -> 'cisco_xe'
        'juniper_junos' -> 'juniper_junos'
        'cisco_asa' -> 'cisco_asa'
    """
    if not device_type:
        return 'unknown'
    
    dt = device_type.lower()
    
    # Cisco IOS variants
    if any(x in dt for x in ['ios', 'iosxe', 'xe']):
        if 'xe' in dt or 'iosxe' in dt:
            return 'cisco_xe'
        return 'cisco_ios'
    
    # Cisco NX-OS
    if any(x in dt for x in ['nxos', 'nx-os', 'nexus']):
        return 'cisco_nxos'
    
    # Juniper
    if any(x in dt for x in ['juniper', 'junos', 'junos']):
        return 'juniper_junos'
    
    # Cisco ASA
    if 'asa' in dt:
        return 'cisco_asa'
    
    # Arista
    if 'arista' in dt or 'eos' in dt:
        return 'arista_eos'
    
    return dt


def _get_os_specific_remediation(policy: dict, device_type: str) -> str:
    """
    Get OS-specific remediation commands from policy.
    
    Policy remediation can be:
    1. String: Used for all platforms
    2. Dict with OS keys: {"cisco_ios": "cmd", "cisco_nxos": "cmd", "default": "cmd"}
    3. Legacy: "remediation_juniper" field for Juniper
    
    Args:
        policy: Policy dict containing remediation info
        device_type: Device type string (e.g., 'cisco_ios')
    
    Returns:
        Remediation commands string for the specific OS
    """
    os_key = _normalize_os_type(device_type)
    remediation = policy.get('remediation', '')
    
    # Handle dict-style remediation (new in v2.0.0)
    if isinstance(remediation, dict):
        # Try specific OS first
        if os_key in remediation:
            return remediation[os_key].strip()
        # Try fallback variants
        if 'cisco_ios' in remediation and os_key in ['cisco_ios', 'cisco_xe']:
            return remediation['cisco_ios'].strip()
        if 'cisco_nxos' in remediation and os_key == 'cisco_nxos':
            return remediation['cisco_nxos'].strip()
        # Default fallback
        if 'default' in remediation:
            return remediation['default'].strip()
        # Any available key
        if remediation:
            return list(remediation.values())[0].strip()
        return ''
    
    # Handle legacy string remediation with remediation_juniper override
    if isinstance(remediation, str):
        # Legacy Juniper override
        if 'juniper' in os_key:
            juniper_remediation = policy.get('remediation_juniper', '')
            if juniper_remediation:
                return juniper_remediation.strip()
        return remediation.strip()
    
    return ''


def _get_available_os_variants(policy: dict) -> list:
    """
    Return list of OS variants supported by this policy's remediation.
    Used for UI display.
    """
    remediation = policy.get('remediation', '')
    
    if isinstance(remediation, dict):
        variants = list(remediation.keys())
        # Filter out 'default' for display
        return [v for v in variants if v != 'default']
    
    # Legacy
    variants = []
    if remediation:
        variants.append('default')
    if policy.get('remediation_juniper'):
        variants.append('juniper_junos')
    
    return variants


# ── Severity ordering ─────────────────────────────────────────────────────────
_SEVERITY_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}

_SEVERITY_ICONS = {
    "critical": "[CRITICAL]",
    "high"    : "[HIGH    ]",
    "medium"  : "[MEDIUM  ]",
    "low"     : "[LOW     ]",
}


# ── Policy loader ─────────────────────────────────────────────────────────────

def _load_policies(policy_file: str, severity_filter: str, category_filter: str) -> list:
    """
    Load and filter policies from YAML or JSON file.

    Returns a list of policy dicts.
    Raises explicit errors when policy files cannot be resolved or parsed
    so the UI shows actionable failures instead of silently running built-ins.
    """
    # v6.5.8: Enhanced path resolution with extensive debugging
    # v6.9.20: Use _get_resource_path() for PyInstaller compatibility
    print(f"[STANDARDS] _load_policies called with policy_file='{policy_file}', severity='{severity_filter}', category='{category_filter}'")
    
    # Handle None or empty policy_file
    if not policy_file:
        print(f"[STANDARDS] WARNING: policy_file is empty/None, using default")
        policy_file = 'policies/standards.yaml'
    
    original_path = policy_file
    
    if not os.path.isabs(policy_file):
        # v6.9.20: Use _get_resource_path() for consistent path resolution
        # This handles both dev mode and PyInstaller EXE mode
        try:
            policy_file = _get_resource_path(policy_file)
            print(f"[STANDARDS] Resolved using _get_resource_path(): {policy_file}")
        except Exception as e:
            print(f"[STANDARDS] WARNING: _get_resource_path() failed: {e}, falling back to manual resolution")
            # Fallback to manual resolution
            plugin_dir = os.path.dirname(os.path.abspath(__file__))
            modules_dir = os.path.dirname(plugin_dir)
            base = os.path.dirname(modules_dir)
            
            possible_paths = [
                os.path.join(base, policy_file),                    # Relative to project root
                os.path.join(os.getcwd(), policy_file),            # Relative to CWD
                policy_file,                                        # As-is (already relative)
            ]
            
            print(f"[STANDARDS] Resolving relative path '{policy_file}'")
            print(f"[STANDARDS] Base directory: {base}")
            print(f"[STANDARDS] CWD: {os.getcwd()}")
            
            # Find first existing path
            found_path = None
            for i, path in enumerate(possible_paths):
                exists = os.path.exists(path)
                print(f"[STANDARDS]   Try {i+1}: {path} -> {'EXISTS' if exists else 'NOT FOUND'}")
                if exists:
                    found_path = path
                    break
            
            if not found_path:
                print(f"[STANDARDS] ERROR: Policy file not found: {original_path}")
                raise FileNotFoundError(f"Policy file not found: {original_path}")
            policy_file = found_path
            print(f"[STANDARDS] Resolved to: {policy_file}")

    if not os.path.exists(policy_file):
        print(f"[STANDARDS] ERROR: Policy file does not exist after resolution: {policy_file}")
        raise FileNotFoundError(f"Policy file does not exist: {policy_file}")

    try:
        policies, metadata = _load_policy_file_with_meta(policy_file)
        print(f"[STANDARDS] SUCCESS: Loaded {len(policies)} policies from {policy_file}")
        if policies:
            print(f"[STANDARDS] First policy: {policies[0].get('id', 'N/A')}, Last policy: {policies[-1].get('id', 'N/A')}")
    except Exception as e:
        print(f"[STANDARDS] CRITICAL ERROR loading policy file {policy_file}: {e}")
        import traceback
        print(f"[STANDARDS] Traceback: {traceback.format_exc()}")
        raise RuntimeError(f"Failed to load policy file '{policy_file}': {e}")

    # Apply severity filter
    min_sev = _SEVERITY_ORDER.get(severity_filter.lower(), 0)
    if min_sev > 0:
        policies = [
            p for p in policies
            if _SEVERITY_ORDER.get(p.get('severity', 'low').lower(), 1) >= min_sev
        ]

    # Apply category filter
    if category_filter.strip():
        cats = {c.strip().lower() for c in category_filter.split(',')}
        policies = [
            p for p in policies
            if p.get('category', '').lower() in cats
        ]

    return policies


def _builtin_policies() -> list:
    """
    Minimal built-in policy set used when no YAML file is found.
    Covers the most critical security standards.
    """
    return [
        {
            "id": "telnet_disabled",
            "category": "Security",
            "description": "Telnet must be disabled on VTY lines",
            "severity": "critical",
            "platforms": ["cisco_ios", "cisco_nxos"],
            "check_command": "show line vty 0 4",
            "check_type": "not_contains",
            "pattern": "transport input telnet",
            "remediation": "line vty 0 4\n transport input ssh",
        },
        {
            "id": "ssh_version_2",
            "category": "Security",
            "description": "SSH must be version 2 only",
            "severity": "high",
            "platforms": ["cisco_ios", "cisco_nxos"],
            "check_command": "show ip ssh",
            "check_type": "contains",
            "pattern": "SSH Enabled - version 2",
            "remediation": "ip ssh version 2",
        },
        {
            "id": "ntp_synchronized",
            "category": "NTP",
            "description": "NTP must be synchronized",
            "severity": "high",
            "platforms": ["cisco_ios", "cisco_nxos", "juniper_junos"],
            "check_command": "show ntp status",
            "check_type": "contains",
            "pattern": "Clock is synchronized",
            "remediation": "ntp server 0.0.0.0 prefer\n! Replace 0.0.0.0 with your NTP server IP",
        },
        {
            "id": "login_banner",
            "category": "Banner",
            "description": "Login banner must be configured",
            "severity": "high",
            "platforms": ["cisco_ios", "cisco_nxos"],
            "check_command": "show running-config | include banner",
            "check_type": "contains",
            "pattern": "banner login",
            "remediation": (
                "banner login ^\n"
                "*** AUTHORIZED ACCESS ONLY ***\n"
                "Unauthorized access is prohibited and monitored.\n"
                "^"
            ),
        },
        {
            "id": "snmp_contact",
            "category": "SNMP",
            "description": "SNMP contact must be configured",
            "severity": "medium",
            "platforms": ["cisco_ios", "cisco_nxos"],
            "check_command": "show snmp contact",
            "check_type": "regex_match",
            "pattern": r"\S+",
            "remediation": "snmp-server contact noc@company.com",
        },
    ]


# ── Check engine ──────────────────────────────────────────────────────────────

def _apply_check(policy: dict, output: str) -> dict:
    """
    Apply the policy check logic to the command output.

    Returns:
        {
            "passed"  : bool,
            "current" : str,   # what was found on the device
            "expected": str,   # what was expected
        }
    """
    check_type = policy.get('check_type', 'contains').lower()
    pattern    = policy.get('pattern', '')
    output_clean = output.strip() if output else ""

    if check_type == 'contains':
        passed = bool(re.search(pattern, output_clean, re.IGNORECASE | re.MULTILINE))
        current  = _extract_relevant_line(output_clean, pattern) if not passed else "Present"
        expected = f"Must contain: {pattern}"
        return {"passed": passed, "current": current, "expected": expected}

    elif check_type == 'not_contains':
        match = re.search(pattern, output_clean, re.IGNORECASE | re.MULTILINE)
        passed = not bool(match)
        current  = match.group(0).strip() if match else "Not present (OK)"
        expected = f"Must NOT contain: {pattern}"
        return {"passed": passed, "current": current, "expected": expected}

    elif check_type == 'regex_match':
        match = re.search(pattern, output_clean, re.IGNORECASE | re.MULTILINE)
        passed = bool(match)
        current  = match.group(0).strip() if match else _first_line(output_clean)
        expected = f"Must match: {pattern}"
        return {"passed": passed, "current": current, "expected": expected}

    elif check_type == 'regex_extract':
        extract_pattern = policy.get('extract_pattern', pattern)
        expected_format = policy.get('expected_format', '')
        match = re.search(extract_pattern, output_clean, re.IGNORECASE | re.MULTILINE)
        if not match:
            return {
                "passed"  : False,
                "current" : f"Pattern not found: {extract_pattern}",
                "expected": f"Must match format: {expected_format}",
            }
        extracted = match.group(1).strip() if match.lastindex else match.group(0).strip()
        passed = bool(re.match(expected_format, extracted)) if expected_format else True
        return {
            "passed"  : passed,
            "current" : extracted,
            "expected": f"Format: {expected_format}",
        }

    elif check_type == 'line_format':
        line_filter    = policy.get('line_filter', '')
        line_must_match = policy.get('line_must_match', '')
        violations = []
        for line in output_clean.splitlines():
            if line_filter and line_filter.lower() not in line.lower():
                continue
            if line_must_match and not re.search(line_must_match, line, re.IGNORECASE):
                violations.append(line.strip())
        passed = len(violations) == 0
        current  = "; ".join(violations[:3]) if violations else "All lines compliant"
        expected = f"Lines matching '{line_filter}' must match: {line_must_match}"
        return {"passed": passed, "current": current, "expected": expected}

    # Unknown check type — skip (pass)
    return {"passed": True, "current": "N/A", "expected": "Unknown check type"}


def _extract_relevant_line(output: str, pattern: str) -> str:
    """Return the first line that looks most relevant, or first line of output."""
    lines = [l.strip() for l in output.splitlines() if l.strip()]
    if not lines:
        return "(no output)"
    # Try to find a line that partially matches the pattern keywords
    keywords = re.findall(r'\w+', pattern)
    for line in lines:
        if any(kw.lower() in line.lower() for kw in keywords if len(kw) > 3):
            return line[:120]
    return lines[0][:120]


def _first_line(output: str) -> str:
    lines = [l.strip() for l in output.splitlines() if l.strip()]
    return lines[0][:120] if lines else "(no output)"


# ── Platform filter ───────────────────────────────────────────────────────────

def _platform_matches(policy: dict, device_type: str) -> bool:
    """Return True if this policy applies to the device's platform."""
    platforms = policy.get('platforms', [])
    if not platforms:
        return True  # No restriction = applies to all
    dt = device_type.lower()
    for p in platforms:
        if p.lower() in dt or dt in p.lower():
            return True
    return False


# ── Remediation builder ───────────────────────────────────────────────────────

def _get_remediation(policy: dict, device_type: str) -> str:
    """
    Return the appropriate remediation commands for this device type.
    Juniper gets 'remediation_juniper' if defined, otherwise 'remediation'.
    """
    dt = device_type.lower()
    if 'juniper' in dt and policy.get('remediation_juniper'):
        return policy['remediation_juniper'].strip()
    return policy.get('remediation', '').strip()


def _has_placeholders(remediation: str) -> bool:
    """Return True if the remediation contains {VARIABLE} placeholders."""
    return bool(re.search(r'\{[A-Z_]+\}', remediation))


# ── Report formatter ──────────────────────────────────────────────────────────

def _format_standards_report(data: dict, host: str) -> str:
    """
    Format the standards validation result as a human-readable report.
    Same visual style as the VLAN missing report.
    """
    violations = data.get('violations', [])
    compliant  = data.get('compliant', True)
    true_host  = data.get('true_host', host)
    device_type = data.get('device_type', 'unknown')
    ts         = data.get('timestamp', datetime.now().isoformat())
    policies_checked = data.get('policies_checked', 0)
    skipped    = data.get('skipped', 0)

    lines = []
    sep  = "=" * 70
    dash = "-" * 70

    lines.append(sep)
    lines.append("STANDARDS VALIDATION REPORT")
    lines.append(sep)
    lines.append(f"Device Hostname:  {true_host}")
    lines.append(f"Device IP:        {host}")
    lines.append(f"Device Type:      {device_type}")
    lines.append(f"Report Generated: {ts}")
    lines.append(f"Policies Checked: {policies_checked}  |  Skipped (platform): {skipped}")
    lines.append("")

    if compliant:
        lines.append(dash)
        lines.append("RESULT: COMPLIANT")
        lines.append(dash)
        lines.append("  All applicable policies passed. No remediation required.")
    else:
        lines.append(dash)
        lines.append(f"RESULT: NON-COMPLIANT  ({len(violations)} violation(s))")
        lines.append(dash)
        lines.append("")

        # Group by severity for readability
        for sev in ['critical', 'high', 'medium', 'low']:
            sev_violations = [v for v in violations if v.get('severity', '').lower() == sev]
            if not sev_violations:
                continue
            for v in sev_violations:
                icon = _SEVERITY_ICONS.get(sev, f"[{sev.upper():8}]")
                lines.append(f"  {icon}  {v['policy_id']}")
                lines.append(f"  Description: {v['description']}")
                lines.append(f"  Category:    {v.get('category', 'General')}")
                lines.append(f"  Current:     {v['current']}")
                lines.append(f"  Expected:    {v['expected']}")
                remediation = v.get('remediation', '')
                if remediation:
                    if _has_placeholders(remediation):
                        lines.append(f"  Fix:         *** MANUAL ACTION REQUIRED — fill in placeholders ***")
                    else:
                        lines.append(f"  Fix:")
                    for cmd_line in remediation.splitlines():
                        lines.append(f"    {cmd_line}")
                lines.append("")

    # Remediation script section
    if not compliant:
        fix_violations = [v for v in violations if v.get('remediation')]
        if fix_violations:
            lines.append(sep)
            lines.append("REMEDIATION SCRIPT")
            lines.append(sep)
            lines.append(f"! Device: {true_host} ({host})")
            lines.append(f"! Generated: {ts}")
            lines.append(f"! Apply: paste in privileged exec mode (enable mode)")
            lines.append(f"! Review each command before applying.")
            lines.append("!")
            lines.append("configure terminal")
            lines.append("!")
            for v in fix_violations:
                rem = v.get('remediation', '')
                if not rem:
                    continue
                lines.append(f"! Fix: {v['policy_id']} — {v['description']}")
                if _has_placeholders(rem):
                    lines.append(f"! *** MANUAL: fill in placeholders before applying ***")
                for cmd_line in rem.splitlines():
                    lines.append(cmd_line)
                lines.append("!")
            lines.append("end")
            lines.append("write memory")

    lines.append(sep)
    lines.append("END OF REPORT")
    lines.append(sep)

    return '\n'.join(lines)


# ── Main run() ────────────────────────────────────────────────────────────────

def run(device, credentials, params, config, log_func):
    """
    Run standards validation on a single device.

    Args:
        device:      {host, device_type, group, port}
        credentials: {username, password, secret}
        params:      {policy_file, severity_filter, category_filter,
                      generate_remediation_script}
        config:      global app config dict
        log_func:    callable(str) for UI log streaming

    Returns:
        Standard JSON dict {device, status, data, error}
    """
    host        = device.get('host', 'unknown')
    device_type = device.get('device_type', 'unknown')

    policy_file   = params.get('policy_file', 'policies/standards.yaml') or 'policies/standards.yaml'
    sev_filter    = params.get('severity_filter', 'all') or 'all'
    cat_filter    = params.get('category_filter', '') or ''
    gen_script    = params.get('generate_remediation_script', True)

    try:
        if log_func:
            log_func(f"[{host}] Loading policy library: {policy_file}")

        policies = _load_policies(policy_file, sev_filter, cat_filter)

        if not policies:
            if log_func:
                log_func(f"[{host}] No policies matched filters — skipping")
            return build_json(host, "success", {
                "true_host"      : host,
                "compliant"      : True,
                "violations"     : [],
                "policies_checked": 0,
                "skipped"        : 0,
                "note"           : "No policies matched the specified filters",
                "timestamp"      : datetime.now().isoformat(),
            })

        if log_func:
            log_func(f"[{host}] {len(policies)} policies to check (filter: sev={sev_filter}, cat='{cat_filter}')")

        violations     = []
        policies_checked = 0
        skipped        = 0
        
        # Connection audit for validation
        connection_audit = {
            "connected_at": None,
            "disconnected_at": None,
            "commands_executed": 0,
            "connection_error": None
        }

        with safe_connection(
            device,
            credentials['username'],
            credentials['password'],
            credentials.get('secret'),
            log_func,
            fallback_credentials=credentials.get('fallback_credentials'),
        ) as conn:
            connection_audit["connected_at"] = datetime.now().isoformat()

            # Get real hostname
            try:
                true_host = resolve_hostname_from_prompt(conn, host)
            except Exception:
                true_host = host

            if log_func:
                log_func(f"[{true_host}] Connected — running {len(policies)} policy checks...")

            for policy in policies:
                pid = policy.get('id', 'unknown')

                # Skip if platform doesn't match
                if not _platform_matches(policy, device_type):
                    skipped += 1
                    continue

                policies_checked += 1

                # Run the check command
                cmd = policy.get('check_command', '')
                if not cmd:
                    continue

                try:
                    output = conn.send_command(cmd)
                except Exception as cmd_err:
                    # Command failed (e.g. not supported on this platform)
                    output = f"ERROR: {cmd_err}"

                # Apply check logic
                result = _apply_check(policy, output)

                if not result['passed']:
                    # Use OS-specific remediation (v2.0.0)
                    remediation = _get_os_specific_remediation(policy, device_type)
                    violations.append({
                        "policy_id"  : pid,
                        "description": policy.get('description', pid),
                        "category"   : policy.get('category', 'General'),
                        "severity"   : policy.get('severity', 'medium'),
                        "current"    : result['current'],
                        "expected"   : result['expected'],
                        "remediation": remediation,
                        "manual"     : _has_placeholders(remediation),
                        "os_type"    : _normalize_os_type(device_type),  # Track OS for report
                    })
                    if log_func:
                        sev = policy.get('severity', 'medium').upper()
                        log_func(f"[{true_host}]   [{sev}] VIOLATION: {pid}")
                else:
                    if log_func:
                        log_func(f"[{true_host}]   [PASS] {pid}")

        # Connection is automatically logged out by safe_connection's finally block
        connection_audit["disconnected_at"] = datetime.now().isoformat()
        connection_audit["commands_executed"] = policies_checked
        
        if log_func:
            log_func(f"[{true_host}] Logout validated — connection closed properly")

        compliant = len(violations) == 0

        result_data = {
            "true_host"       : true_host,
            "device_type"     : device_type,
            "connection_audit": connection_audit,  # Validate logout occurred
            "compliant"       : compliant,
            "violations"      : violations,
            "policies_checked": policies_checked,
            "skipped"         : skipped,
            "timestamp"       : datetime.now().isoformat(),
        }

        # Generate human-readable report
        report_path = save_plugin_report(
            "standards_validator", host, result_data, _format_standards_report
        )
        result_data["report_path"] = report_path

        # Generate per-device remediation script if requested
        if gen_script and not compliant:
            _write_remediation_script(host, true_host, violations, result_data["timestamp"])

        # Master summary
        if compliant:
            summary = f"COMPLIANT — {policies_checked} policies passed"
        else:
            critical_count = sum(1 for v in violations if v.get('severity') == 'critical')
            high_count     = sum(1 for v in violations if v.get('severity') == 'high')
            summary = (
                f"NON-COMPLIANT — {len(violations)} violations "
                f"({critical_count} critical, {high_count} high)"
            )

        append_to_master_report(
            "standards_validator", host,
            "success" if compliant else "fail",
            summary, report_path
        )

        if log_func:
            log_func(f"[{true_host}] {summary}")
            log_func(f"[{true_host}] Report: {report_path}")

        return build_json(host, "success", result_data)

    except Exception as e:
        error_msg = str(e).splitlines()[0] if str(e).splitlines() else str(e)
        if log_func:
            log_func(f"[{host}] ERROR: {error_msg}")
        try:
            append_to_master_report("standards_validator", host, "fail", error_msg[:60], "N/A")
        except Exception:
            pass
        return build_json(host, "fail", {}, error_msg)


# ── HTML Report Generator ───────────────────────────────────────────────────

def _generate_html_standards_report(all_results: list, policy_file: str, timestamp: str) -> str:
    """
    Generate a professional HTML gap analysis report.
    
    Args:
        all_results: List of result dicts from all devices
        policy_file: Path to the policy file used
        timestamp: ISO timestamp string
    
    Returns:
        HTML string for the complete report
    """
    # Calculate statistics
    total_devices = len(all_results)
    compliant_devices = sum(1 for r in all_results if r.get('compliant', False))
    non_compliant = total_devices - compliant_devices
    
    total_violations = sum(len(r.get('violations', [])) for r in all_results)
    critical_count = sum(
        sum(1 for v in r.get('violations', []) if v.get('severity') == 'critical')
        for r in all_results
    )
    high_count = sum(
        sum(1 for v in r.get('violations', []) if v.get('severity') == 'high')
        for r in all_results
    )
    
    # Group violations by category
    categories = {}
    for result in all_results:
        for v in result.get('violations', []):
            cat = v.get('category', 'General')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append({
                'device': result.get('true_host', result.get('device', 'unknown')),
                'policy_id': v.get('policy_id'),
                'description': v.get('description'),
                'severity': v.get('severity'),
                'current': v.get('current'),
                'expected': v.get('expected'),
                'remediation': v.get('remediation'),
                'manual': v.get('manual', False)
            })
    
    # Build HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Standards Compliance Report - {timestamp[:10]}</title>
    <style>
        :root {{
            --color-critical: #dc2626;
            --color-high: #ea580c;
            --color-medium: #ca8a04;
            --color-low: #16a34a;
            --color-bg: #f8fafc;
            --color-card: #ffffff;
            --color-text: #1e293b;
            --color-text-muted: #64748b;
            --border-color: #e2e8f0;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--color-bg);
            color: var(--color-text);
            line-height: 1.6;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 24px; }}
        
        /* Header */
        .header {{
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            color: white;
            padding: 32px;
            border-radius: 12px;
            margin-bottom: 24px;
        }}
        .header h1 {{ font-size: 28px; font-weight: 600; margin-bottom: 8px; }}
        .header .meta {{ opacity: 0.8; font-size: 14px; }}
        
        /* Summary Cards */
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .summary-card {{
            background: var(--color-card);
            padding: 20px;
            border-radius: 10px;
            border: 1px solid var(--border-color);
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .summary-card .value {{
            font-size: 36px;
            font-weight: 700;
            margin-bottom: 4px;
        }}
        .summary-card .label {{
            font-size: 13px;
            color: var(--color-text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .summary-card.compliant {{ border-left: 4px solid var(--color-low); }}
        .summary-card.compliant .value {{ color: var(--color-low); }}
        .summary-card.violations {{ border-left: 4px solid var(--color-critical); }}
        .summary-card.violations .value {{ color: var(--color-critical); }}
        .summary-card.critical {{ border-left: 4px solid var(--color-critical); }}
        .summary-card.critical .value {{ color: var(--color-critical); }}
        .summary-card.high {{ border-left: 4px solid var(--color-high); }}
        .summary-card.high .value {{ color: var(--color-high); }}
        
        /* Section Headers */
        .section {{
            background: var(--color-card);
            border-radius: 10px;
            border: 1px solid var(--border-color);
            margin-bottom: 24px;
            overflow: hidden;
        }}
        .section-header {{
            background: #f1f5f9;
            padding: 16px 20px;
            border-bottom: 1px solid var(--border-color);
            font-weight: 600;
            font-size: 16px;
        }}
        .section-body {{ padding: 20px; }}
        
        /* Device Cards */
        .device-card {{
            border: 1px solid var(--border-color);
            border-radius: 8px;
            margin-bottom: 16px;
            overflow: hidden;
        }}
        .device-header {{
            background: #f8fafc;
            padding: 12px 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
        }}
        .device-name {{ font-weight: 600; font-size: 15px; }}
        .device-status {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
        }}
        .device-status.compliant {{ background: #dcfce7; color: #166534; }}
        .device-status.non-compliant {{ background: #fee2e2; color: #991b1b; }}
        .device-body {{ padding: 16px; }}
        
        /* Violation Table */
        .violation-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}
        .violation-table th {{
            text-align: left;
            padding: 10px;
            background: #f8fafc;
            font-weight: 600;
            color: var(--color-text-muted);
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.5px;
        }}
        .violation-table td {{ padding: 12px 10px; border-bottom: 1px solid var(--border-color); vertical-align: top; }}
        .violation-table tr:hover {{ background: #f8fafc; }}
        
        /* Severity Badges */
        .severity {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .severity.critical {{ background: #fee2e2; color: #991b1b; }}
        .severity.high {{ background: #ffedd5; color: #9a3412; }}
        .severity.medium {{ background: #fef3c7; color: #92400e; }}
        .severity.low {{ background: #dcfce7; color: #166534; }}
        
        /* Remediation Block */
        .remediation {{
            background: #f8fafc;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 12px;
            margin-top: 8px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 12px;
            white-space: pre-wrap;
        }}
        .remediation.manual {{
            background: #fef3c7;
            border-color: #fbbf24;
        }}
        .remediation-label {{
            font-size: 11px;
            color: var(--color-text-muted);
            margin-bottom: 4px;
            text-transform: uppercase;
        }}
        
        /* Current/Expected */
        .value-current {{ color: var(--color-critical); }}
        .value-expected {{ color: var(--color-low); }}
        
        /* Empty State */
        .empty-state {{
            text-align: center;
            padding: 40px;
            color: var(--color-text-muted);
        }}
        
        /* Print Styles */
        @media print {{
            .container {{ max-width: 100%; }}
            .section {{ break-inside: avoid; }}
            .device-card {{ break-inside: avoid; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>📋 Network Standards Compliance Report</h1>
            <div class="meta">
                Generated: {timestamp.replace('T', ' ')[:19]} | 
                Policy File: {policy_file} |
                Total Devices: {total_devices}
            </div>
        </div>
        
        <!-- Summary Cards -->
        <div class="summary-grid">
            <div class="summary-card compliant">
                <div class="value">{compliant_devices}</div>
                <div class="label">Compliant Devices</div>
            </div>
            <div class="summary-card violations">
                <div class="value">{non_compliant}</div>
                <div class="label">Non-Compliant</div>
            </div>
            <div class="summary-card critical">
                <div class="value">{critical_count}</div>
                <div class="label">Critical Issues</div>
            </div>
            <div class="summary-card high">
                <div class="value">{high_count}</div>
                <div class="label">High Severity</div>
            </div>
        </div>
"""
    
    # Device-by-Device Section
    html += """
        <!-- Device-by-Device Analysis -->
        <div class="section">
            <div class="section-header">🔍 Device-by-Device Gap Analysis</div>
            <div class="section-body">
"""
    
    if non_compliant == 0:
        html += """
                <div class="empty-state">
                    <h3>✅ All Devices Compliant</h3>
                    <p>No violations found across all scanned devices.</p>
                </div>
"""
    else:
        for result in all_results:
            if result.get('compliant', False):
                continue
                
            device = result.get('true_host', result.get('device', 'unknown'))
            violations = result.get('violations', [])
            
            html += f"""
                <div class="device-card">
                    <div class="device-header">
                        <span class="device-name">{device}</span>
                        <span class="device-status non-compliant">{len(violations)} Violations</span>
                    </div>
                    <div class="device-body">
                        <table class="violation-table">
                            <thead>
                                <tr>
                                    <th>Severity</th>
                                    <th>Policy</th>
                                    <th>Issue</th>
                                    <th>Current State</th>
                                    <th>Required Fix</th>
                                </tr>
                            </thead>
                            <tbody>
"""
            for v in violations:
                sev = v.get('severity', 'medium')
                manual = v.get('manual', False)
                rem_classes = 'remediation manual' if manual else 'remediation'
                manual_note = '<div class="remediation-label">⚠️ Manual Action Required - Fill in placeholders</div>' if manual else '<div class="remediation-label">Remediation Commands:</div>'
                
                html += f"""
                                <tr>
                                    <td><span class="severity {sev}">{sev.upper()}</span></td>
                                    <td><strong>{v.get('policy_id', 'N/A')}</strong><br><small>{v.get('category', 'General')}</small></td>
                                    <td>{v.get('description', 'N/A')}</td>
                                    <td class="value-current">{v.get('current', 'N/A')}</td>
                                    <td>
                                        {manual_note}
                                        <div class="{rem_classes}">{v.get('remediation', 'N/A')}</div>
                                    </td>
                                </tr>
"""
            
            html += """
                            </tbody>
                        </table>
                    </div>
                </div>
"""
    
    html += """
            </div>
        </div>
"""
    
    # Category Breakdown Section
    if categories:
        html += """
        <!-- Violations by Category -->
        <div class="section">
            <div class="section-header">📊 Violations by Category</div>
            <div class="section-body">
"""
        for cat, items in sorted(categories.items()):
            html += f"""
                <h4 style="margin: 16px 0 8px 0; color: #334155;">{cat} ({len(items)} issues)</h4>
                <table class="violation-table">
                    <thead>
                        <tr>
                            <th>Severity</th>
                            <th>Device</th>
                            <th>Policy</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody>
"""
            for item in items:
                html += f"""
                        <tr>
                            <td><span class="severity {item['severity']}">{item['severity'].upper()}</span></td>
                            <td>{item['device']}</td>
                            <td>{item['policy_id']}</td>
                            <td>{item['description']}</td>
                        </tr>
"""
            html += """
                    </tbody>
                </table>
"""
        html += """
            </div>
        </div>
"""
    
    # Footer
    html += f"""
        <!-- Footer -->
        <div style="text-align: center; padding: 24px; color: #94a3b8; font-size: 12px; border-top: 1px solid var(--border-color); margin-top: 24px;">
            <p>Network Swiss Tool Pro v6.5.7 - Standards Validator v2.0.0</p>
            <p>Report generated: {timestamp.replace('T', ' ')[:19]} | This report is for compliance assessment only. No changes were made to devices.</p>
        </div>
    </div>
</body>
</html>"""
    
    return html


def _write_html_report(all_results: list, policy_file: str, timestamp: str) -> str:
    """Write the HTML report to file and return the path."""
    try:
        from utils.output_paths import CAT_COMPLIANCE, path_in_run, prepare_run_output, slugify, write_run_manifest
        paths = prepare_run_output(CAT_COMPLIANCE, slugify('gap_analysis'))
        out_path = path_in_run(paths, 'standards_gap_analysis.html')
        
        html = _generate_html_standards_report(all_results, policy_file, timestamp)
        
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        write_run_manifest(paths, {'html_path': out_path, 'policy_file': policy_file})
        return out_path
    except Exception as e:
        return None


# ── Remediation script writer ─────────────────────────────────────────────────

def _write_remediation_script(host: str, true_host: str, violations: list, ts: str):
    """Write a standalone remediation script file for this device."""
    try:
        from utils.output_paths import CAT_COMPLIANCE, path_in_run, prepare_run_output, slugify, write_run_manifest
        safe_host = host.replace('.', '_').replace(':', '_')
        paths = prepare_run_output(CAT_COMPLIANCE, slugify(f'remediation_{safe_host}'))
        out_path = path_in_run(paths, 'remediation_script.txt')

        lines = [
            f"! Standards Validator — Remediation Script",
            f"! Device:    {true_host} ({host})",
            f"! Generated: {ts}",
            f"! IMPORTANT: Review every command before applying.",
            f"!            Commands with {{PLACEHOLDERS}} require manual editing.",
            f"!",
            f"configure terminal",
            f"!",
        ]
        for v in violations:
            rem = v.get('remediation', '')
            if not rem:
                continue
            lines.append(f"! [{v.get('severity','').upper()}] {v['policy_id']}: {v['description']}")
            if _has_placeholders(rem):
                lines.append(f"! *** MANUAL ACTION REQUIRED — fill in {{PLACEHOLDERS}} ***")
            for cmd_line in rem.splitlines():
                lines.append(cmd_line)
            lines.append("!")
        lines += ["end", "write memory", ""]

        with open(out_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        write_run_manifest(paths, {'remediation_path': out_path, 'host': true_host})
    except Exception:
        pass  # Non-critical — don't fail the plugin if script write fails


if __name__ == "__main__":
    print(f"Plugin: {METADATA['display_name']} v{METADATA['version']}")
    print(f"Category: {METADATA['category']}")
    print(f"Policies: load from policies/standards.yaml")

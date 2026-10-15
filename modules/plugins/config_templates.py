"""
modules/plugins/config_templates.py
----------------------------------
Template-Based Configuration Generator Plugin for Network Swiss Tool Pro v6.9.21.

This plugin enables engineers to generate standard network configurations using Jinja2
templates. On startup, it bootstraps common templates under templates/ folder.

=============================================================================
HARDCODED REQUIREMENTS - ALL PLUGINS MUST COMPLY
=============================================================================
1. VERSION REQUIREMENTS (MANDATORY):
   - Version: "1.0.0"
2. DOCUMENTATION REQUIREMENTS (MANDATORY):
   - Located in: docs/plugins/config_templates/
3. CONTRACT COMPLIANCE:
   - Contains METADATA dict
   - Implements run() function
   - Implements validate_plugin() function
=============================================================================
"""

METADATA = {
    "plugin_id": "config_templates",
    "display_name": "Configuration Templates",
    "version": "1.0.0",
    "author": "Network Swiss Tool",
    "category": "Template",
    "description": "Safe, read-only Jinja2 config template generator. Bootstraps and compiles templates with dynamic validation.",
    "min_platform_version": "6.9.21",
    
    "changelog": [
        {
            "version": "1.0.0",
            "date": "2026-05-26",
            "changes": "Initial release of configuration templates engine utilizing Jinja2 and regular expression variable extraction.",
            "author": "Network Swiss Tool Team",
            "qa_status": "approved"
        }
    ],
    
    "documentation": {
        "readme": "docs/plugins/config_templates/README.md",
        "release_notes": "docs/plugins/config_templates/RELEASE_NOTES.md",
        "prompt": "docs/plugins/config_templates/PROMPT.md",
        "changelog": "docs/plugins/config_templates/CHANGELOG.md",
        "test_results": "docs/plugins/config_templates/TEST_RESULTS.md",
        "compatibility": "docs/plugins/config_templates/COMPATIBILITY.md",
        "versions_folder": "docs/plugins/config_templates/versions/",
        "current_version_folder": "docs/plugins/config_templates/versions/v1.0.0/"
    },
    
    "version_archive": {
        "v1.0.0": {
            "file": "docs/plugins/config_templates/versions/v1.0.0/config_templates_v1.0.0.py",
            "manifest": "docs/plugins/config_templates/versions/v1.0.0/manifest.json",
            "date": "2026-05-26",
            "status": "current"
        }
    },
    
    "required_params": {
        "template_name": {
            "type": "string",
            "label": "Template File Name",
            "placeholder": "e.g. cisco_ios_ntp.j2",
            "required": True
        },
        "variables": {
            "type": "string",
            "label": "Template Variables (JSON String)",
            "default": "{}",
            "required": True,
            "description": "JSON serialized key-value pairs representing template variables."
        }
    },
    
    "supports_parallel": True,
    "supports_dry_run": True,
    "modifies_device": False,
    "requires_enable": False
}

from modules.network_base import safe_connection, build_json, safe_node_name
from utils.report_formatter import save_plugin_report, append_to_master_report
from datetime import datetime
import re
import os
import json
import sys

# Jinja2 rendering engine
try:
    from jinja2 import Template as JinjaTemplate, Environment, BaseLoader
    _JINJA_AVAILABLE = True
except ImportError:
    _JINJA_AVAILABLE = False

def run(device, credentials, params, config, log_func):
    host = device.get('host', 'unknown')
    
    template_name = params.get('template_name')
    vars_str = params.get('variables', '{}')
    
    if log_func:
        log_func(f"[{host}] Running configuration template renderer for: {template_name}...")
        
    try:
        variables = json.loads(vars_str)
    except Exception as je:
        return build_json(host, "fail", {}, f"Invalid template variables JSON: {je}")
        
    # Find template path in dev/EXE modes
    if getattr(sys, 'frozen', False):
        p_dir = os.path.dirname(sys.executable)
    else:
        p_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
    template_path = os.path.join(p_dir, "templates", template_name)
    
    if not os.path.exists(template_path):
        return build_json(host, "fail", {}, f"Template file not found: {template_name}")
        
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()
            
        rendered_config = render_template_string(template_content, variables, host)
        
        result_data = {
            "template_name": template_name,
            "variables": variables,
            "rendered_output": rendered_config,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save plugin report
        report_path = save_plugin_report(
            METADATA['plugin_id'], 
            host, 
            result_data, 
            lambda d, h: _format_template_report(d, h)
        )
        result_data["report_path"] = report_path
        
        # Append to master summary
        summary_text = f"Rendered Jinja2 configuration preview successfully for template {template_name}."
        append_to_master_report(METADATA['plugin_id'], host, "success", summary_text, report_path)
        
        return build_json(host, "success", result_data)
        
    except Exception as e:
        if log_func:
            log_func(f"[{host}] Template compilation error: {e}")
        return build_json(host, "fail", {}, str(e))

# ── Dynamic Variable Extractor ───────────────────────────────────────────────
def extract_template_variables(template_content: str) -> list:
    """
    Extract all unique Jinja2 double-brace variables from template.
    Example: {{ ntp_server }} -> 'ntp_server'
    """
    # Regex matching {{ variable }} pattern, ignoring braces and whitespace
    pattern = r'\{\{\s*([a-zA-Z0-9_]+)\s*\}\}'
    vars_found = re.findall(pattern, template_content)
    
    # Filter out common Jinja keywords/builtins if any are caught
    banned_keywords = {'true', 'false', 'none', 'loop'}
    unique_vars = sorted(list(set(v for v in vars_found if v.lower() not in banned_keywords)))
    return unique_vars

# ── Safe Jinja2 Compiler ──────────────────────────────────────────────────────
def render_template_string(template_str: str, variables: dict, host: str = "device") -> str:
    """
    Render a Jinja2 template string using variables.
    Provides robust fallback if jinja2 library is missing.
    """
    # Always supply standard device variables for conveniences
    full_vars = variables.copy()
    full_vars.setdefault("hostname", host)
    full_vars.setdefault("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    if _JINJA_AVAILABLE:
        try:
            env = Environment(loader=BaseLoader())
            template = env.from_string(template_str)
            return template.render(full_vars)
        except Exception as je:
            raise RuntimeError(f"Jinja2 Compilation Error: {je}")
    else:
        # Fallback basic string formatting replacement if Jinja2 is unavailable
        rendered = template_str
        for k, v in full_vars.items():
            pattern = r'\{\{\s*' + re.escape(k) + r'\s*\}\}'
            rendered = re.sub(pattern, str(v), rendered)
        return rendered

# ── Bootstrap Default Templates ──────────────────────────────────────────────
def bootstrap_example_templates(templates_dir: str):
    """Create templates folder on startup with verified boilerplate snippets."""
    os.makedirs(templates_dir, exist_ok=True)
    
    examples = {
        "cisco_ios_ntp.j2": (
            "! Cisco IOS NTP Configuration Template\n"
            "! Generated on {{ timestamp }}\n"
            "!\n"
            "configure terminal\n"
            "ntp server {{ ntp_server_1 }} prefer\n"
            "{% if ntp_server_2 %}\n"
            "ntp server {{ ntp_server_2 }}\n"
            "{% endif %}\n"
            "clock timezone {{ timezone_name }} {{ timezone_offset }}\n"
            "end\n"
            "write memory\n"
        ),
        "cisco_ios_syslog.j2": (
            "! Cisco IOS Logging Configuration Template\n"
            "! Target Device: {{ hostname }}\n"
            "!\n"
            "configure terminal\n"
            "logging source-interface {{ source_interface }}\n"
            "logging host {{ syslog_server }}\n"
            "logging trap {{ logging_level }}\n"
            "logging facility local7\n"
            "end\n"
        ),
        "cisco_nxos_port_channel.j2": (
            "! Cisco NX-OS Port-Channel (LACP) — preview only\n"
            "! Device: {{ hostname }} — {{ timestamp }}\n"
            "configure terminal\n"
            "interface port-channel{{ po_id }}\n"
            "  description {{ description }}\n"
            "  switchport\n"
            "  switchport mode trunk\n"
            "  switchport trunk allowed vlan {{ allowed_vlans }}\n"
            "{% for m in members.split(',') %}\n"
            "interface {{ m.strip() }}\n"
            "  description Po{{ po_id }} member\n"
            "  switchport\n"
            "  switchport mode trunk\n"
            "  switchport trunk allowed vlan {{ allowed_vlans }}\n"
            "  channel-group {{ po_id }} mode active\n"
            "{% endfor %}\n"
            "end\n"
        ),
        "cisco_nxos_trunk.j2": (
            "! Cisco NX-OS trunk interface — preview only\n"
            "! Device: {{ hostname }} — {{ timestamp }}\n"
            "configure terminal\n"
            "interface {{ interface }}\n"
            "  description {{ description }}\n"
            "  switchport\n"
            "  switchport mode trunk\n"
            "  switchport trunk allowed vlan {{ allowed_vlans }}\n"
            "  switchport trunk native vlan {{ native_vlan }}\n"
            "end\n"
        ),
        "cisco_nxos_trunk_vpc.j2": (
            "! Cisco NX-OS trunk + vPC — preview only\n"
            "! Device: {{ hostname }} — {{ timestamp }}\n"
            "configure terminal\n"
            "interface {{ interface }}\n"
            "  description {{ description }}\n"
            "  switchport\n"
            "  switchport mode trunk\n"
            "  switchport trunk allowed vlan {{ allowed_vlans }}\n"
            "  switchport trunk native vlan {{ native_vlan }}\n"
            "  vpc {{ vpc_id }}\n"
            "end\n"
        ),
        "cisco_ios_trunk.j2": (
            "! Cisco IOS/XE trunk — preview only\n"
            "! Device: {{ hostname }} — {{ timestamp }}\n"
            "configure terminal\n"
            "interface {{ interface }}\n"
            " description {{ description }}\n"
            " switchport trunk encapsulation dot1q\n"
            " switchport mode trunk\n"
            " switchport trunk allowed vlan {{ allowed_vlans }}\n"
            " switchport trunk native vlan {{ native_vlan }}\n"
            "end\n"
        ),
        "cisco_ios_port_channel.j2": (
            "! Cisco IOS Port-Channel — preview only\n"
            "! Device: {{ hostname }} — {{ timestamp }}\n"
            "configure terminal\n"
            "interface Port-channel{{ po_id }}\n"
            " description {{ description }}\n"
            " switchport mode trunk\n"
            " switchport trunk allowed vlan {{ allowed_vlans }}\n"
            "{% for m in members.split(',') %}\n"
            "interface {{ m.strip() }}\n"
            " description Po{{ po_id }} member\n"
            " switchport mode trunk\n"
            " switchport trunk allowed vlan {{ allowed_vlans }}\n"
            " channel-group {{ po_id }} mode active\n"
            "{% endfor %}\n"
            "end\n"
        ),
        "juniper_junos_ntp.j2": (
            "# Juniper Junos NTP Configuration Template\n"
            "# Target Device: {{ hostname }}\n"
            "#\n"
            "system {\n"
            "    ntp {\n"
            "        server {{ ntp_server_1 }} prefer;\n"
            "        {% if ntp_server_2 %}\n"
            "        server {{ ntp_server_2 }};\n"
            "        {% endif %}\n"
            "    }\n"
            "}\n"
        )
    }
    
    for filename, content in examples.items():
        filepath = os.path.join(templates_dir, filename)
        if not os.path.exists(filepath):
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
            except:
                pass

# ── Report Formatter ──────────────────────────────────────────────────────────
def _format_template_report(data, host):
    lines = []
    lines.append("=" * 70)
    lines.append("TEMPLATE-BASED CONFIGURATION GENERATION PREVIEW")
    lines.append("=" * 70)
    lines.append(f"Device IP:        {host}")
    lines.append(f"Template Name:    {data.get('template_name', 'N/A')}")
    lines.append(f"Render Date:      {data.get('timestamp', 'N/A')}")
    lines.append("")
    
    lines.append("-" * 70)
    lines.append("TEMPLATE INJECTED VARIABLES")
    lines.append("-" * 70)
    vars_dict = data.get('variables', {})
    for k, v in vars_dict.items():
        lines.append(f"  {k:<20} = {v}")
    lines.append("")
    
    lines.append("-" * 70)
    lines.append("GENERATED READ-ONLY CONFIGURATION PREVIEW")
    lines.append("-" * 70)
    lines.append(data.get('rendered_output', 'No configuration rendered'))
    lines.append("")
    
    lines.append("=" * 70)
    return "\n".join(lines)

# ── Preset builder metadata (web UI) ─────────────────────────────────────────
TEMPLATE_PRESETS = {
    "nxos_trunk": {
        "label": "NX-OS Trunk interface",
        "platform": "cisco_nxos",
        "intent": "trunk",
        "suggested_filename": "cisco_nxos_trunk.j2",
        "variables": {
            "interface": "Ethernet1/10",
            "description": "TRUNK_TO_CORE",
            "allowed_vlans": "10,20,30",
            "native_vlan": "1",
        },
    },
    "nxos_port_channel": {
        "label": "NX-OS Port-Channel (LACP)",
        "platform": "cisco_nxos",
        "intent": "port_channel",
        "suggested_filename": "cisco_nxos_port_channel.j2",
        "variables": {
            "po_id": "10",
            "description": "PO_TO_SERVER",
            "allowed_vlans": "10,20",
            "members": "Ethernet1/1,Ethernet1/2",
        },
    },
    "nxos_trunk_vpc": {
        "label": "NX-OS Trunk + vPC",
        "platform": "cisco_nxos",
        "intent": "trunk_vpc",
        "suggested_filename": "cisco_nxos_trunk_vpc.j2",
        "variables": {
            "interface": "Ethernet1/10",
            "description": "VPC_TRUNK",
            "allowed_vlans": "10,20",
            "native_vlan": "1",
            "vpc_id": "10",
        },
    },
    "ios_trunk": {
        "label": "IOS/XE Trunk interface",
        "platform": "cisco_ios",
        "intent": "trunk",
        "suggested_filename": "cisco_ios_trunk.j2",
        "variables": {
            "interface": "GigabitEthernet1/0/1",
            "description": "TRUNK_UPLINK",
            "allowed_vlans": "10,20,30",
            "native_vlan": "1",
        },
    },
    "ios_port_channel": {
        "label": "IOS Port-Channel",
        "platform": "cisco_ios",
        "intent": "port_channel",
        "suggested_filename": "cisco_ios_port_channel.j2",
        "variables": {
            "po_id": "1",
            "description": "PO_UPLINK",
            "allowed_vlans": "10,20",
            "members": "GigabitEthernet1/0/1,GigabitEthernet1/0/2",
        },
    },
}


def get_template_presets():
    """Return preset catalog for /api/templates/presets."""
    items = []
    for key, meta in TEMPLATE_PRESETS.items():
        items.append({"id": key, **meta})
    return items


# ── Validation Helper ────────────────────────────────────────────────────────
def validate_plugin():
    errors = []
    required_meta_keys = ['plugin_id', 'display_name', 'version', 'category', 'required_params']
    for key in required_meta_keys:
        if key not in METADATA:
            errors.append(f"Missing METADATA key: {key}")
    if 'run' not in globals() or not callable(globals()['run']):
        errors.append("Missing required 'run' function")
    return len(errors) == 0, errors


# ── Class Interface (v6.9.21 API bridge) ─────────────────────────────────────
class ConfigTemplatesPlugin:
    """
    Object-oriented wrapper used by the /api/templates/* REST endpoints.
    Delegates to the module-level helpers for actual processing.
    """

    def list_templates(self, templates_dir: str) -> list:
        """
        Return a list of template metadata dicts for all .j2/.txt files in
        *templates_dir*.  Each entry has: name, description, variables, size.
        """
        results = []
        if not os.path.isdir(templates_dir):
            return results

        for fname in sorted(os.listdir(templates_dir)):
            if not (fname.endswith('.j2') or fname.endswith('.txt')):
                continue
            fpath = os.path.join(templates_dir, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
                variables = extract_template_variables(content)
                # First comment line is the description
                first_line = content.strip().split('\n')[0] if content.strip() else ''
                description = (
                    first_line.lstrip('!#/*').strip()
                    if first_line.startswith(('!', '#', '/', '*'))
                    else f"{fname} configuration template"
                )
                results.append({
                    "name":        fname,
                    "description": description,
                    "variables":   variables,
                    "size":        os.path.getsize(fpath),
                    "path":        fpath,
                })
            except Exception:
                pass
        return results

    def render_template(self, template_content: str, variables: dict) -> tuple:
        """
        Render *template_content* with *variables*.
        Returns (rendered_output: str, variables_used: list).
        """
        vars_used = extract_template_variables(template_content)
        output    = render_template_string(template_content, variables)
        return output, vars_used

    def execute(self, device, credentials, params, config, log_func=None):
        """Plugin contract execute() — delegates to module-level run()."""
        return run(device, credentials, params, config, log_func)


if __name__ == "__main__":
    is_valid, errors = validate_plugin()
    if is_valid:
        print(f"✅ Plugin '{METADATA['plugin_id']}' is valid!")
    else:
        for err in errors:
            print(f"❌ {err}")
        exit(1)


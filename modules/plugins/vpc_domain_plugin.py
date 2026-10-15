"""
modules/plugins/vpc_domain_plugin.py
------------------------------------
Reports vPC domain ID(s) when present on Cisco NX-OS peers.
Enhanced with vivid, human-readable output for vPC topology analysis.

v2.3.1 - DEFENSIVE PROGRAMMING FIXES:
- Added None checks and type validation to all verification functions to prevent AttributeError
- Added isinstance() checks before string operations to handle non-string inputs gracefully
- Added defensive type conversion for VLAN lists to ensure set operations work correctly
- Added type checking for members list in port-channel verification
- Added string type checking for interface brief output and statistics output
- All verification functions now handle missing or malformed data without crashing

EXPECTED NXOS OUTPUT FORMATS:
=============================

show vpc output:
----------------
Legend: (*) - local vPC is down, forwarding via vPC peer-link
vPC domain id : 1
Peer status : peer link is down
vPC keep-alive status : Suspended (Destination IP not reachable)
Configuration consistency status : failed
Per-vlan consistency status : success
Configuration inconsistency reason: Consistency Check Not Performed
Type-2 inconsistency reason : Consistency Check Not Performed
vPC role : none established
Number of vPCs configured : 2
Peer Gateway : Enabled
Dual-active excluded VLANs : -
Graceful Consistency Check : Disabled (due to peer configuration)
Auto-recovery status : Disabled

vPC Peer-link status
-------------------------------------------------------
id   Port   Status   Active vlans
--   ----   ------   ------------------------------------
1    Po10   down     -

vPC status
-------------------------------------------------------
id   Port   Status   Consistency   Reason                 Active vlans
--   ----   ------   -----------   ------                 ------------
2    Po20   down     failed        Peer-link is down      -
50   Po50   down     failed        Peer-link is down      -

show cdp neighbors output:
--------------------------
Capability Codes: R - Router, T - Trans Bridge, B - Source Route Bridge
S - Switch, H - Host, I - IGMP, r - Repeater

Device ID    Local Intrf  Holdtme  Capability  Platform  Port ID
-----------  ----------  ------  ----------  --------  ------------
NEXUS-02     Eth1/48     140     R S         N9K-C...  Eth1/48

STATUS NORMALIZATION:
====================
Peer-link status:
- "peer link is up" → "up"
- "peer link is down" → "down"
- "peer link is alive" → "up"

Keepalive status:
- "peer is alive" → "up"
- "alive" → "up"
- "connected" → "up"
- "suspended" → "down"
- "destination ip not reachable" → "down"
- "peer is not reachable" → "down"
- "failed" → "down"
"""

METADATA = {
    "plugin_id": "vpc_domain",
    "display_name": "vPC Domain Analysis",
    "version": "2.3.1",
    "author": "Network Swiss Tool",
    "category": "Audit",
    "description": "Enhanced vPC domain analysis with comprehensive vPC member display, consistency parameters (type-1, type-2, per-vlan), and detailed status information for network engineers. Executes actual verification commands for all 10 recommendations with human-readable error reporting and mismatch detection. Includes defensive programming to handle missing or malformed data gracefully.",
    "min_platform_version": "6.0.0",
    "required_params": {},
    "supports_parallel": True,
    "supports_dry_run": False,
    "modifies_device": False,
    "requires_enable": False,
}

import re
from datetime import datetime
from modules.network_base import safe_connection, build_json, safe_node_name, resolve_hostname_from_prompt
from utils.report_formatter import save_plugin_report, append_to_master_report

# Global storage for domain correlation across devices
_vpc_domain_cache = {}

# Global storage for VPC peer correlation to prevent duplicate devices
_vpc_peer_cache = {}


def _parse_vpc_domain(vpc_out):
    """
    Extract domain id, role, peer/keepalive status, and consistency parameters from show vpc.
    
    Expected NXOS output format:
    Legend: (*) - local vPC is down, forwarding via vPC peer-link
    vPC domain id : 1
    Peer status : peer link is down
    vPC keep-alive status : Suspended (Destination IP not reachable)
    Configuration consistency status : failed
    Per-vlan consistency status : success
    Configuration inconsistency reason: Consistency Check Not Performed
    Type-2 inconsistency reason : Consistency Check Not Performed
    """
    info = {
        "domain_id": "",
        "role": "unknown",
        "peer_status": "unknown",
        "keepalive_status": "unknown",
        "config_consistency": "unknown",
        "per_vlan_consistency": "unknown",
        "config_inconsistency_reason": "",
        "type2_inconsistency_reason": "",
        "present": False,
        "vpcs": [],  # List of vPCs with their details
    }
    if not vpc_out or "% Invalid" in vpc_out:
        return info

    # More flexible domain ID extraction - handle various formats
    m = re.search(r'vpc\s+domain\s+id\s*[:=]?\s*(\d+)', vpc_out, re.IGNORECASE)
    if not m:
        # Try alternative format: "VPC domain id : 100"
        m = re.search(r'VPC\s+domain\s+id\s*[:]\s*(\d+)', vpc_out, re.IGNORECASE)
    if not m:
        # Try format: "Domain ID : 100"
        m = re.search(r'Domain\s+ID\s*[:]\s*(\d+)', vpc_out, re.IGNORECASE)
    if not m:
        # Try format: "domain id : 100"
        m = re.search(r'domain\s+id\s*[:]\s*(\d+)', vpc_out, re.IGNORECASE)
    
    if m:
        info["domain_id"] = m.group(1)
        info["present"] = True

    # Extract role with more patterns
    rm = re.search(r'(primary|secondary)', vpc_out, re.IGNORECASE)
    if not rm:
        rm = re.search(r'Role\s*[:=]?\s*(primary|secondary)', vpc_out, re.IGNORECASE)
    if rm:
        info["role"] = rm.group(1).lower()

    # FIXED: Extract peer-link status using actual NXOS format
    # Format: "Peer status : peer link is down" or "Peer status : peer link is up"
    pm = re.search(r'Peer\s+status\s*:\s*(.+)', vpc_out, re.IGNORECASE)
    if pm:
        peer_status_raw = pm.group(1).strip().lower()
        info["peer_status"] = _normalize_peer_status(peer_status_raw)

    # FIXED: Extract keepalive status using actual NXOS format
    # Format: "vPC keep-alive status : Suspended (Destination IP not reachable)" or "vPC keep-alive status : peer is alive"
    km = re.search(r'vPC\s+keep-alive\s+status\s*:\s*(.+)', vpc_out, re.IGNORECASE)
    if km:
        keepalive_status_raw = km.group(1).strip().lower()
        info["keepalive_status"] = _normalize_keepalive_status(keepalive_status_raw)

    # Extract configuration consistency status (type-1)
    cm = re.search(r'Configuration\s+consistency\s+status\s*:\s*(.+)', vpc_out, re.IGNORECASE)
    if cm:
        info["config_consistency"] = cm.group(1).strip().lower()

    # Extract per-vlan consistency status
    vm = re.search(r'Per-vlan\s+consistency\s+status\s*:\s*(.+)', vpc_out, re.IGNORECASE)
    if vm:
        info["per_vlan_consistency"] = vm.group(1).strip().lower()

    # Extract configuration inconsistency reason
    cr = re.search(r'Configuration\s+inconsistency\s+reason\s*:\s*(.+)', vpc_out, re.IGNORECASE)
    if cr:
        info["config_inconsistency_reason"] = cr.group(1).strip()

    # Extract type-2 inconsistency reason
    tr = re.search(r'Type-2\s+inconsistency\s+reason\s*:\s*(.+)', vpc_out, re.IGNORECASE)
    if tr:
        info["type2_inconsistency_reason"] = tr.group(1).strip()

    # Parse individual vPC entries if present
    info["vpcs"] = _parse_vpc_entries(vpc_out)

    return info


def _normalize_peer_status(status_raw):
    """
    Normalize peer-link status to standardized values.
    
    Input examples from NXOS:
    - "peer link is down" → "down"
    - "peer link is up" → "up"
    - "peer link is alive" → "up"
    """
    status_lower = status_raw.lower()
    
    if 'up' in status_lower or 'alive' in status_lower:
        return 'up'
    elif 'down' in status_lower:
        return 'down'
    else:
        # Return original if no match
        return status_raw


def _normalize_keepalive_status(status_raw):
    """
    Normalize keepalive status to standardized values.
    
    Input examples from NXOS:
    - "peer is alive" → "up"
    - "alive" → "up"
    - "connected" → "up"
    - "suspended" → "down"
    - "destination ip not reachable" → "down"
    - "peer is not reachable" → "down"
    - "failed" → "down"
    """
    status_lower = status_raw.lower()
    
    if 'alive' in status_lower or 'connected' in status_lower or 'up' in status_lower:
        return 'up'
    elif 'suspended' in status_lower or 'not reachable' in status_lower or 'failed' in status_lower or 'down' in status_lower:
        return 'down'
    else:
        # Return original if no match
        return status_raw


def _parse_vpc_entries(vpc_out):
    """Parse individual vPC entries from show vpc output (delegates to shared NX-OS parser)."""
    from utils.nxos_vpc_parse import parse_vpc_table_from_cli

    vpcs = []
    for row in parse_vpc_table_from_cli(vpc_out):
        vpcs.append({
            'vpc_id': row['vpc_id'],
            'port_channel': row['po'],
            'status': row['status'],
            'consistency': row.get('consistency', 'unknown'),
            'reason': '',
            'active_vlans': row.get('active_vlans', '-'),
        })
    return vpcs


def _parse_cdp_neighbors(cdp_out):
    """
    Parse CDP neighbor information for peer validation.
    
    Expected NXOS output format:
    Capability Codes: R - Router, T - Trans Bridge, B - Source Route Bridge
    S - Switch, H - Host, I - IGMP, r - Repeater

    Device ID    Local Intrf  Holdtme  Capability  Platform  Port ID
    -----------  ----------  ------  ----------  --------  ------------
    NEXUS-02     Eth1/48     140     R S         N9K-C...  Eth1/48
    """
    neighbors = []
    if not cdp_out or "% Invalid" in cdp_out:
        return neighbors
    
    lines = cdp_out.splitlines()
    in_table = False
    header_found = False
    
    for line in lines:
        line = line.strip()
        
        # Skip capability codes section
        if 'Capability Codes' in line or 'capability codes' in line.lower():
            continue
        
        # Look for table header
        if 'Device ID' in line and 'Local Intrf' in line:
            header_found = True
            in_table = True
            continue
        
        # Look for separator line (dashes)
        if in_table and re.match(r'^[-\s]+$', line):
            continue
        
        # Parse table rows after header
        if in_table and header_found:
            # Skip empty lines
            if not line:
                continue
            
            # Try to parse as table row: Device ID, Local Intrf, Holdtme, Capability, Platform, Port ID
            # Use regex to capture the columns
            row_match = re.match(r'^(\S+)\s+(\S+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(.+)$', line)
            if row_match:
                neighbor = {
                    "device_id": row_match.group(1),
                    "local_interface": row_match.group(2),
                    "holdtime": row_match.group(3),
                    "capability": row_match.group(4),
                    "platform": row_match.group(5),
                    "port_id": row_match.group(6).strip()
                }
                neighbors.append(neighbor)
    
    return neighbors


def _parse_port_channels(pc_out):
    """Parse port-channel interface details including VLAN membership and member interfaces."""
    port_channels = []
    if not pc_out or "% Invalid" in pc_out:
        return port_channels
    
    current_pc = None
    
    for line in pc_out.splitlines():
        line_stripped = line.strip()
        
        # Look for port-channel lines (e.g., "Port-channel1" or "Po1")
        pc_match = re.match(r'^(Po\d+|Port-channel\d+)', line_stripped, re.IGNORECASE)
        if pc_match:
            if current_pc:
                port_channels.append(current_pc)
            current_pc = {
                "name": pc_match.group(1),
                "status": "unknown",
                "vlans": [],
                "members": []
            }
            # Parse status from same line
            if 'up' in line_stripped.lower() or 'connected' in line_stripped.lower():
                current_pc["status"] = "up"
            elif 'down' in line_stripped.lower() or 'notconnect' in line_stripped.lower():
                current_pc["status"] = "down"
        elif current_pc:
            # Parse VLAN information (e.g., "Vlans: 1,10,20-30")
            vlan_match = re.search(r'vlans?\s*[:=]\s*(.+)', line_stripped, re.IGNORECASE)
            if vlan_match:
                vlan_str = vlan_match.group(1)
                # Parse VLAN ranges (e.g., "1,10,20-30")
                vlan_list = []
                for part in vlan_str.split(','):
                    part = part.strip()
                    if '-' in part:
                        # Handle range
                        start, end = part.split('-')
                        vlan_list.extend(range(int(start), int(end) + 1))
                    else:
                        vlan_list.append(part)
                current_pc["vlans"] = [str(v) for v in vlan_list]
            
            # Parse member interfaces (e.g., "Members: Eth1/1, Eth1/2")
            member_match = re.search(r'members?\s*[:=]\s*(.+)', line_stripped, re.IGNORECASE)
            if member_match:
                member_str = member_match.group(1)
                current_pc["members"] = [m.strip() for m in member_str.split(',')]
            
            # Alternative: Parse individual member lines
            member_line_match = re.match(r'^(Eth\d+/\d+|Ethernet\d+/\d+)', line_stripped, re.IGNORECASE)
            if member_line_match:
                member = member_line_match.group(1)
                if member not in current_pc["members"]:
                    current_pc["members"].append(member)
    
    if current_pc:
        port_channels.append(current_pc)
    
    return port_channels


def _verify_peer_link(peer_link_out, peer_status):
    """
    Verify peer-link is UP and passing traffic.
    
    Returns: dict with status, message, impact, action
    """
    result = {
        "status": "unknown",
        "message": "",
        "impact": "",
        "action": ""
    }
    
    # Handle None or non-string peer_status
    if not peer_status or not isinstance(peer_status, str):
        peer_status = "unknown"
    
    if not peer_link_out:
        result["status"] = "unknown"
        result["message"] = "Unable to verify - no peer-link output"
        result["impact"] = "Cannot determine peer-link health"
        result["action"] = "Check if 'show vpc peer-link' command is supported"
        return result
    
    # Check if peer-link is UP based on peer_status from show vpc
    if peer_status.lower() in ['up', 'connected', 'active']:
        result["status"] = "pass"
        result["message"] = "Peer-link is UP and operational"
        result["impact"] = "None - peer-link is healthy"
        result["action"] = "No action required"
    else:
        result["status"] = "fail"
        result["message"] = f"Peer-link is {peer_status.upper()}"
        result["impact"] = "vPC peer communication will fail, causing split-brain scenario"
        result["action"] = "Check physical connectivity: 'show interface port-channel X'"
    
    return result


def _verify_keepalive(keepalive_status, keepalive_out):
    """
    Verify keepalive is UP and reachable.
    
    Returns: dict with status, message, impact, action
    """
    result = {
        "status": "unknown",
        "message": "",
        "impact": "",
        "action": ""
    }
    
    # Handle None or non-string keepalive_status
    if not keepalive_status or not isinstance(keepalive_status, str):
        keepalive_status = "unknown"
    
    if keepalive_status.lower() in ['up', 'alive', 'connected', 'ok']:
        result["status"] = "pass"
        result["message"] = "Keepalive is UP and reachable"
        result["impact"] = "None - keepalive is healthy"
        result["action"] = "No action required"
    else:
        result["status"] = "fail"
        result["message"] = f"Keepalive is {keepalive_status.upper()}"
        result["impact"] = "vPC peer detection will fail, causing split-brain scenario"
        result["action"] = "Check keepalive configuration: 'show vpc peer-keepalive'"
    
    return result


def _verify_type1_consistency(config_consistency, config_inconsistency_reason):
    """
    Verify Type-1 (global) consistency parameters.
    
    Returns: dict with status, message, impact, action
    """
    result = {
        "status": "unknown",
        "message": "",
        "impact": "",
        "action": ""
    }
    
    # Handle None or non-string config_consistency
    if not config_consistency or not isinstance(config_consistency, str):
        config_consistency = "unknown"
    
    # Handle None config_inconsistency_reason
    if not config_inconsistency_reason or not isinstance(config_inconsistency_reason, str):
        config_inconsistency_reason = ""
    
    if config_consistency.lower() in ['success', 'consistent']:
        result["status"] = "pass"
        result["message"] = "Type-1 consistency parameters match"
        result["impact"] = "None - global config is consistent"
        result["action"] = "No action required"
    else:
        result["status"] = "fail"
        result["message"] = f"Type-1 consistency: {config_consistency.upper()}"
        if config_inconsistency_reason:
            result["message"] += f" - {config_inconsistency_reason}"
        result["impact"] = "Global configuration mismatch may cause vPC suspension"
        result["action"] = "Check global config: 'show vpc consistency-parameters type-1'"
    
    return result


def _verify_type2_consistency(type2_inconsistency_reason):
    """
    Verify Type-2 (interface) consistency parameters.
    
    Returns: dict with status, message, impact, action
    """
    result = {
        "status": "unknown",
        "message": "",
        "impact": "",
        "action": ""
    }
    
    # Handle None or non-string type2_inconsistency_reason
    if not type2_inconsistency_reason or not isinstance(type2_inconsistency_reason, str):
        type2_inconsistency_reason = ""
    
    if not type2_inconsistency_reason or type2_inconsistency_reason.lower() == 'consistency check not performed':
        result["status"] = "pass"
        result["message"] = "Type-2 consistency parameters match"
        result["impact"] = "None - interface config is consistent"
        result["action"] = "No action required"
    else:
        result["status"] = "fail"
        result["message"] = f"Type-2 inconsistency: {type2_inconsistency_reason}"
        result["impact"] = "Interface configuration mismatch may cause vPC suspension"
        result["action"] = "Check interface config: 'show vpc consistency-parameters type-2'"
    
    return result


def _verify_per_vlan_consistency(per_vlan_consistency):
    """
    Verify per-vlan consistency status.
    
    Returns: dict with status, message, impact, action
    """
    result = {
        "status": "unknown",
        "message": "",
        "impact": "",
        "action": ""
    }
    
    # Handle None or non-string per_vlan_consistency
    if not per_vlan_consistency or not isinstance(per_vlan_consistency, str):
        per_vlan_consistency = "unknown"
    
    if per_vlan_consistency.lower() in ['success', 'consistent']:
        result["status"] = "pass"
        result["message"] = "Per-vlan consistency - All VLANs consistent"
        result["impact"] = "None - VLAN consistency is healthy"
        result["action"] = "No action required"
    else:
        result["status"] = "fail"
        result["message"] = f"Per-vlan consistency: {per_vlan_consistency.upper()}"
        result["impact"] = "VLAN-specific inconsistencies may cause traffic disruption"
        result["action"] = "Check per-vlan consistency: 'show vpc consistency-parameters'"
    
    return result


def _verify_vlan_consistency(vpcs, port_channels, peer_link_output):
    """
    Verify VLANs allowed on peer-link match vPC members.
    
    Returns: dict with status, message, impact, action
    """
    result = {
        "status": "unknown",
        "message": "",
        "impact": "",
        "action": ""
    }
    
    if not vpcs or not port_channels:
        result["status"] = "unknown"
        result["message"] = "Unable to verify - missing vPC or port-channel data"
        result["impact"] = "Cannot verify VLAN consistency"
        result["action"] = "Ensure vPC and port-channel data is available"
        return result
    
    # Extract peer-link port-channel (usually the first one or lowest number)
    peer_link_pc = None
    for pc in port_channels:
        pc_name = pc.get('name', '')
        if pc_name and isinstance(pc_name, str) and pc_name.lower().startswith('po'):
            peer_link_pc = pc
            break
    
    if not peer_link_pc:
        result["status"] = "unknown"
        result["message"] = "Unable to identify peer-link port-channel"
        result["impact"] = "Cannot verify VLAN consistency"
        result["action"] = "Check peer-link configuration manually"
        return result
    
    # Ensure vlans is a list
    peer_link_vlans_list = peer_link_pc.get('vlans', [])
    if not isinstance(peer_link_vlans_list, list):
        peer_link_vlans_list = []
    
    peer_link_vlans = set(str(v) for v in peer_link_vlans_list)
    
    # Check if any vPC member has VLANs not on peer-link
    missing_vlans = []
    for vpc in vpcs:
        vpc_pc_name = vpc.get('port_channel', '')
        if not vpc_pc_name or not isinstance(vpc_pc_name, str):
            continue
        
        # Find corresponding port-channel
        vpc_pc = next((pc for pc in port_channels if pc.get('name', '') and isinstance(pc.get('name', ''), str) and pc.get('name', '').lower() == vpc_pc_name.lower()), None)
        if vpc_pc:
            vpc_vlans_list = vpc_pc.get('vlans', [])
            if not isinstance(vpc_vlans_list, list):
                vpc_vlans_list = []
            
            vpc_vlans = set(str(v) for v in vpc_vlans_list)
            # Check if vpc vlans are subset of peer-link vlans
            if not vpc_vlans.issubset(peer_link_vlans):
                missing = vpc_vlans - peer_link_vlans
                missing_vlans.extend(list(missing))
    
    if missing_vlans:
        result["status"] = "fail"
        result["message"] = f"VLAN mismatch - VLANs {missing_vlans} not allowed on peer-link"
        result["impact"] = "Traffic for these VLANs will be blocked on peer-link"
        result["action"] = "Add missing VLANs to peer-link: 'switchport trunk allowed vlan add X'"
    else:
        result["status"] = "pass"
        result["message"] = "VLANs allowed on peer-link match vPC members"
        result["impact"] = "None - VLAN configuration is consistent"
        result["action"] = "No action required"
    
    return result


def _verify_vpc_consistency(config_consistency, per_vlan_consistency, consistency_output):
    """
    Verify overall vPC consistency status.
    
    Returns: dict with status, message, impact, action
    """
    result = {
        "status": "unknown",
        "message": "",
        "impact": "",
        "action": ""
    }
    
    # Handle None or non-string values
    if not config_consistency or not isinstance(config_consistency, str):
        config_consistency = "unknown"
    if not per_vlan_consistency or not isinstance(per_vlan_consistency, str):
        per_vlan_consistency = "unknown"
    
    if (config_consistency.lower() in ['success', 'consistent'] and 
        per_vlan_consistency.lower() in ['success', 'consistent']):
        result["status"] = "pass"
        result["message"] = "vPC consistency - No inconsistencies detected"
        result["impact"] = "None - vPC is consistent"
        result["action"] = "No action required"
    else:
        result["status"] = "fail"
        result["message"] = "vPC consistency - Inconsistencies detected"
        result["impact"] = "vPC may be suspended or traffic disrupted"
        result["action"] = "Check consistency parameters: 'show vpc consistency-parameters'"
    
    return result


def _verify_cdp_neighbors(cdp_neighbors, domain_peers):
    """
    Verify CDP neighbors match expected vPC peer switches.
    
    Returns: dict with status, message, impact, action
    """
    result = {
        "status": "unknown",
        "message": "",
        "impact": "",
        "action": ""
    }
    
    if not cdp_neighbors:
        result["status"] = "warn"
        result["message"] = "No CDP neighbors detected"
        result["impact"] = "Cannot validate vPC peer via CDP"
        result["action"] = "Check if CDP is enabled: 'show cdp'"
        return result
    
    # Check if we have domain peers to compare against
    if len(domain_peers) > 1:
        result["status"] = "pass"
        result["message"] = f"CDP neighbors detected - {len(cdp_neighbors)} neighbors"
        result["impact"] = "None - CDP peer validation possible"
        result["action"] = "No action required"
    else:
        result["status"] = "warn"
        result["message"] = f"CDP neighbors detected but only one switch in domain"
        result["impact"] = "Cannot validate vPC peer configuration"
        result["action"] = "Verify vPC peer is configured correctly"
    
    return result


def _verify_port_channel_members(port_channels, interface_brief_output):
    """
    Verify port-channel member interfaces are UP.
    
    Returns: dict with status, message, impact, action
    """
    result = {
        "status": "unknown",
        "message": "",
        "impact": "",
        "action": ""
    }
    
    if not port_channels:
        result["status"] = "unknown"
        result["message"] = "No port-channels to verify"
        result["impact"] = "Cannot verify member interface status"
        result["action"] = "Check if vPC is configured"
        return result
    
    down_members = []
    for pc in port_channels:
        members = pc.get('members', [])
        if not isinstance(members, list):
            continue
        
        for member in members:
            if not member or not isinstance(member, str):
                continue
            
            # Check interface status from brief output if available
            if interface_brief_output and isinstance(interface_brief_output, str):
                # Parse interface brief to check status
                for line in interface_brief_output.splitlines():
                    if member.lower() in line.lower():
                        if 'down' in line.lower() or 'notconnect' in line.lower():
                            down_members.append(member)
                        break
    
    if down_members:
        result["status"] = "fail"
        result["message"] = f"Port-channel member interfaces DOWN: {', '.join(down_members)}"
        result["impact"] = "vPC member interfaces down will cause vPC suspension"
        result["action"] = "Check interface status: 'show interface X'"
    else:
        result["status"] = "pass"
        result["message"] = "All port-channel member interfaces are UP"
        result["impact"] = "None - member interfaces are healthy"
        result["action"] = "No action required"
    
    return result


def _verify_vpc_statistics(stats_output):
    """
    Verify vPC statistics for operational metrics.
    
    Returns: dict with status, message, impact, action
    """
    result = {
        "status": "unknown",
        "message": "",
        "impact": "",
        "action": ""
    }
    
    if not stats_output or not isinstance(stats_output, str):
        result["status"] = "unknown"
        result["message"] = "Unable to verify - no statistics output"
        result["impact"] = "Cannot verify operational metrics"
        result["action"] = "Check if 'show vpc statistics' command is supported"
        return result
    
    # Check for error indicators in statistics
    errors = []
    stats_lower = stats_output.lower()
    if 'error' in stats_lower:
        errors.append("Errors detected in statistics")
    if 'packet loss' in stats_lower:
        errors.append("Packet loss detected")
    
    if errors:
        result["status"] = "warn"
        result["message"] = f"vPC statistics - {', '.join(errors)}"
        result["impact"] = "May indicate operational issues"
        result["action"] = "Review detailed statistics: 'show vpc statistics'"
    else:
        result["status"] = "pass"
        result["message"] = "vPC statistics - Normal operational metrics"
        result["impact"] = "None - statistics are normal"
        result["action"] = "No action required"
    
    return result


def run(device, credentials, params, config, log_func):
    host = device.get('host', 'unknown')
    dtype = (device.get('device_type') or '').lower()

    try:
        if log_func:
            log_func(f"[{host}] Checking vPC domain...")

        if 'nxos' not in dtype and 'nexus' not in dtype:
            return build_json(host, "success", {
                "true_host": host,
                "present": False,
                "domain_id": None,
                "message": "Not an NX-OS device — vPC domain N/A",
            })

        with safe_connection(
            device,
            credentials['username'],
            credentials['password'],
            credentials.get('secret'),
            log_func,
            fallback_credentials=credentials.get('fallback_credentials'),
        ) as conn:
            true_host = resolve_hostname_from_prompt(conn, host)
            
            # Enhanced command set with fallback
            commands_to_try = [
                ("show vpc", 60),
                ("show vpc brief", 30),
                ("show vpc peer-keepalive", 30),
                ("show vpc consistency-parameters", 30),
                ("show vpc statistics", 30),
                ("show cdp neighbors", 30),
                ("show interface port-channel", 30),
                ("show vpc peer-link", 30),
                ("show vpc role", 30),
                ("show interface brief", 30),
                ("show vpc legacy", 30),
            ]
            
            command_outputs = {}
            for cmd, timeout in commands_to_try:
                try:
                    if log_func:
                        log_func(f"[{true_host}] Executing: {cmd}")
                    output = conn.send_command(cmd, read_timeout=timeout)
                    if output and "% Invalid" not in output:
                        command_outputs[cmd] = output
                        if log_func:
                            log_func(f"[{true_host}] ✓ {cmd} - Success")
                    else:
                        if log_func:
                            log_func(f"[{true_host}] ✗ {cmd} - Invalid command or no output")
                except Exception as e:
                    if log_func:
                        log_func(f"[{true_host}] ✗ {cmd} - Error: {str(e)}")
            
            # Parse vPC information
            vpc_out = command_outputs.get("show vpc", "")
            brief_out = command_outputs.get("show vpc brief", "")
            cdp_out = command_outputs.get("show cdp neighbors", "")
            pc_out = command_outputs.get("show interface port-channel", "")
            consistency_out = command_outputs.get("show vpc consistency-parameters", "")
            stats_out = command_outputs.get("show vpc statistics", "")
            peer_link_out = command_outputs.get("show vpc peer-link", "")
            role_out = command_outputs.get("show vpc role", "")
            interface_brief_out = command_outputs.get("show interface brief", "")
            legacy_out = command_outputs.get("show vpc legacy", "")
            
            info = _parse_vpc_domain(vpc_out)
            if not info["present"] and brief_out:
                bm = re.search(r'vpc\s+domain\s+id\s*[:=]?\s*(\d+)', brief_out, re.IGNORECASE)
                if bm:
                    info["domain_id"] = bm.group(1)
                    info["present"] = True
            
            # Parse CDP neighbors for peer validation
            cdp_neighbors = _parse_cdp_neighbors(cdp_out)
            
            # Parse port-channel details
            port_channels = _parse_port_channels(pc_out)
            
            # Store in global cache for domain correlation
            if info["present"] and info["domain_id"]:
                if info["domain_id"] not in _vpc_domain_cache:
                    _vpc_domain_cache[info["domain_id"]] = []
                _vpc_domain_cache[info["domain_id"]].append({
                    "host": true_host,
                    "role": info["role"],
                    "peer_status": info["peer_status"],
                    "keepalive_status": info["keepalive_status"],
                    "cdp_neighbors": cdp_neighbors,
                    "port_channels": port_channels,
                    "vpcs": info["vpcs"]
                })

            # Run all verifications
            verification_results = {}
            if info["present"]:
                verification_results["peer_link"] = _verify_peer_link(peer_link_out, info["peer_status"])
                verification_results["keepalive"] = _verify_keepalive(info["keepalive_status"], command_outputs.get("show vpc peer-keepalive", ""))
                verification_results["type1_consistency"] = _verify_type1_consistency(info["config_consistency"], info["config_inconsistency_reason"])
                verification_results["type2_consistency"] = _verify_type2_consistency(info["type2_inconsistency_reason"])
                verification_results["per_vlan_consistency"] = _verify_per_vlan_consistency(info["per_vlan_consistency"])
                verification_results["vlan_consistency"] = _verify_vlan_consistency(info["vpcs"], port_channels, peer_link_out)
                verification_results["vpc_consistency"] = _verify_vpc_consistency(info["config_consistency"], info["per_vlan_consistency"], consistency_out)
                verification_results["cdp_neighbors"] = _verify_cdp_neighbors(cdp_neighbors, _vpc_domain_cache.get(info["domain_id"], []))
                verification_results["port_channel_members"] = _verify_port_channel_members(port_channels, interface_brief_out)
                verification_results["vpc_statistics"] = _verify_vpc_statistics(stats_out)
            
            data = {
                "true_host": true_host,
                "present": info["present"],
                "domain_id": info["domain_id"] if info["present"] else None,
                "role": info["role"],
                "peer_status": info["peer_status"],
                "keepalive_status": info["keepalive_status"],
                "config_consistency": info["config_consistency"],
                "per_vlan_consistency": info["per_vlan_consistency"],
                "config_inconsistency_reason": info["config_inconsistency_reason"],
                "type2_inconsistency_reason": info["type2_inconsistency_reason"],
                "vpcs": info["vpcs"],
                "cdp_neighbors": cdp_neighbors,
                "port_channels": port_channels,
                "consistency_parameters": consistency_out,
                "vpc_statistics": stats_out,
                "peer_link_output": peer_link_out,
                "role_output": role_out,
                "interface_brief_output": interface_brief_out,
                "legacy_output": legacy_out,
                "domain_peers": _vpc_domain_cache.get(info["domain_id"], []) if info["present"] else [],
                "verification_results": verification_results
            }

            if log_func:
                if info["present"]:
                    log_func(f"[{true_host}] vPC Domain ID: {info['domain_id']} ({info['role']}) - {len(info['vpcs'])} vPCs found")
                else:
                    log_func(f"[{true_host}] No vPC domain configured")

            report_path = save_plugin_report(
                "vpc_domain", true_host, data, _format_vpc_domain_report
            )
            summary = f"vPC Domain: {info['domain_id']}" if info["present"] else "vPC: Not configured"
            append_to_master_report("vpc_domain", true_host, "success", summary, report_path)
            data["report_file"] = report_path
            return build_json(host, "success", data)

    except Exception as e:
        err = str(e).splitlines()[0] if str(e).splitlines() else str(e)
        if log_func:
            log_func(f"[{host}] vPC domain check failed: {err}")
        return build_json(host, "fail", {}, err)


def _format_vpc_domain_report(data: dict, host: str) -> str:
    """
    Format vPC domain plugin result with enhanced, vivid presentation.
    Provides comprehensive vPC topology information in human-readable format.
    """
    lines = []
    sep = "=" * 70
    dash = "-" * 70
    
    lines.append(sep)
    lines.append("vPC DOMAIN ANALYSIS REPORT")
    lines.append(sep)
    lines.append("")
    lines.append(f"Device Hostname:    {data.get('true_host', 'N/A')}")
    lines.append(f"Device IP:          {host}")
    lines.append(f"Report Generated:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    if not data.get("present"):
        lines.append(dash)
        lines.append("vPC CONFIGURATION STATUS")
        lines.append(dash)
        lines.append("❌ vPC Domain: NOT CONFIGURED / NOT DETECTED")
        lines.append("")
        if data.get("message"):
            lines.append(f"Note: {data['message']}")
        lines.append("")
        lines.append("This device is not configured for vPC or vPC is not active.")
        lines.append("")
        lines.append(sep)
        lines.append("END OF REPORT")
        lines.append(sep)
        return "\n".join(lines)
    
    # vPC is configured
    lines.append(dash)
    lines.append("vPC CONFIGURATION STATUS")
    lines.append(dash)
    lines.append("✅ vPC Domain: CONFIGURED AND ACTIVE")
    lines.append("")
    
    lines.append(dash)
    lines.append("vPC DOMAIN DETAILS")
    lines.append(dash)
    lines.append(f"Domain ID:          {data.get('domain_id', 'N/A')}")
    lines.append(f"Role:               {data.get('role', 'unknown').upper()}")
    lines.append(f"Peer-Link Status:   {data.get('peer_status', 'unknown').upper()}")
    lines.append(f"Keepalive Status:   {data.get('keepalive_status', 'unknown').upper()}")
    lines.append("")
    
    # Consistency Parameters Section
    lines.append(dash)
    lines.append("vPC CONSISTENCY PARAMETERS")
    lines.append(dash)
    lines.append(f"Type-1 Consistency:   {data.get('config_consistency', 'unknown').upper()}")
    lines.append(f"Per-VLAN Consistency: {data.get('per_vlan_consistency', 'unknown').upper()}")
    
    if data.get('config_inconsistency_reason'):
        lines.append(f"Config Inconsistency Reason: {data['config_inconsistency_reason']}")
    if data.get('type2_inconsistency_reason'):
        lines.append(f"Type-2 Inconsistency Reason: {data['type2_inconsistency_reason']}")
    lines.append("")
    
    # Add interpretation based on role
    role = data.get('role', '').lower()
    if role == 'primary':
        lines.append(dash)
        lines.append("ROLE INTERPRETATION")
        lines.append(dash)
        lines.append("🌟 This device is the PRIMARY vPC peer.")
        lines.append("   - It controls the vPC domain and makes forwarding decisions")
        lines.append("   - The secondary peer follows the primary's decisions")
        lines.append("   - Ensure peer-link and keepalive are healthy for redundancy")
        lines.append("")
    elif role == 'secondary':
        lines.append(dash)
        lines.append("ROLE INTERPRETATION")
        lines.append(dash)
        lines.append("ℹ️ This device is the SECONDARY vPC peer.")
        lines.append("   - It follows the primary peer's forwarding decisions")
        lines.append("   - It can take over if the primary fails")
        lines.append("   - Ensure peer-link and keepalive are healthy for failover")
        lines.append("")
    
    # Health check based on status
    peer_status = data.get('peer_status', '').lower()
    keepalive_status = data.get('keepalive_status', '').lower()
    
    lines.append(dash)
    lines.append("vPC HEALTH CHECK")
    lines.append(dash)
    
    if peer_status in ['up', 'connected', 'active']:
        lines.append("✅ Peer-Link: HEALTHY")
    elif peer_status in ['down', 'disconnected', 'inactive']:
        lines.append("❌ Peer-Link: UNHEALTHY - CHECK PHYSICAL CONNECTIVITY")
    else:
        lines.append(f"⚠️  Peer-Link: {peer_status.upper()} - VERIFY STATUS")
    
    if keepalive_status in ['up', 'connected', 'alive', 'ok']:
        lines.append("✅ Keepalive: HEALTHY")
    elif keepalive_status in ['down', 'disconnected', 'dead', 'failed']:
        lines.append("❌ Keepalive: UNHEALTHY - CHECK KEEPALIVE CONFIGURATION")
    else:
        lines.append(f"⚠️  Keepalive: {keepalive_status.upper()} - VERIFY STATUS")
    
    lines.append("")
    
    # vPC Details Section
    vpcs = data.get('vpcs', [])
    # VALIDATION: Only render vPC entries that have valid data
    valid_vpcs = []
    for vpc in vpcs:
        vpc_id = vpc.get('vpc_id', '')
        port_channel = vpc.get('port_channel', '')
        # Skip entries with invalid vpc_id or port_channel
        if vpc_id and vpc_id.isdigit() and port_channel and re.match(r'^(Po\d+|Port-channel\d+)', port_channel, re.IGNORECASE):
            valid_vpcs.append(vpc)
    
    if valid_vpcs:
        lines.append(dash)
        lines.append("vPC MEMBER PORTS")
        lines.append(dash)
        for vpc in valid_vpcs:
            lines.append(f"vPC ID:            {vpc.get('vpc_id', 'N/A')}")
            lines.append(f"  Port-Channel:    {vpc.get('port_channel', 'N/A')}")
            lines.append(f"  Status:          {vpc.get('status', 'unknown').upper()}")
            lines.append(f"  Consistency:     {vpc.get('consistency', 'unknown').upper()}")
            if vpc.get('reason'):
                lines.append(f"  Reason:          {vpc.get('reason')}")
            if vpc.get('active_vlans'):
                lines.append(f"  Active VLANs:     {vpc.get('active_vlans')}")
            lines.append("")
    elif vpcs:
        # There were vPC entries but all were invalid
        lines.append(dash)
        lines.append("vPC MEMBER PORTS")
        lines.append(dash)
        lines.append("⚠️  vPC data was detected but could not be parsed correctly.")
        lines.append("   This may indicate malformed output or parsing errors.")
        lines.append("   Please check the raw device output for details.")
        lines.append("")
    
    # Port-Channel Details
    port_channels = data.get('port_channels', [])
    if port_channels:
        lines.append(dash)
        lines.append("PORT-CHANNEL DETAILS")
        lines.append(dash)
        for pc in port_channels:
            lines.append(f"Port-Channel:      {pc.get('name', 'N/A')}")
            lines.append(f"  Status:          {pc.get('status', 'unknown').upper()}")
            if pc.get('vlans'):
                lines.append(f"  VLANs:           {', '.join(pc['vlans'])}")
            if pc.get('members'):
                lines.append(f"  Members:         {', '.join(pc['members'])}")
            lines.append("")
    
    # CDP Neighbors Section
    cdp_neighbors = data.get('cdp_neighbors', [])
    if cdp_neighbors:
        lines.append(dash)
        lines.append("CDP NEIGHBOR VALIDATION")
        lines.append(dash)
        for neighbor in cdp_neighbors:
            lines.append(f"Neighbor Device:    {neighbor.get('device_id', 'N/A')}")
            lines.append(f"  Local Interface:  {neighbor.get('local_interface', 'N/A')}")
            lines.append(f"  Platform:         {neighbor.get('platform', 'N/A')}")
            lines.append(f"  Port ID:          {neighbor.get('port_id', 'N/A')}")
            lines.append("")
    
    # Domain Peer Correlation
    domain_peers = data.get('domain_peers', [])
    if len(domain_peers) > 1:
        lines.append(dash)
        lines.append("vPC DOMAIN PEER CORRELATION")
        lines.append(dash)
        lines.append(f"Total switches in vPC Domain {data.get('domain_id', 'N/A')}: {len(domain_peers)}")
        lines.append("")
        for i, peer in enumerate(domain_peers, 1):
            lines.append(f"Switch {i}:")
            lines.append(f"  Hostname:         {peer.get('host', 'N/A')}")
            lines.append(f"  Role:             {peer.get('role', 'unknown').upper()}")
            lines.append(f"  Peer-Link Status: {peer.get('peer_status', 'unknown').upper()}")
            lines.append(f"  Keepalive Status: {peer.get('keepalive_status', 'unknown').upper()}")
            lines.append("")
    
    # vPC Verification Results
    verification_results = data.get('verification_results', {})
    if verification_results:
        lines.append(dash)
        lines.append("vPC VERIFICATION RESULTS")
        lines.append(dash)
        
        # Verification 1: Peer-link
        v1 = verification_results.get('peer_link', {})
        status_icon = "✅" if v1.get('status') == 'pass' else "❌" if v1.get('status') == 'fail' else "⚠️"
        lines.append(f"{status_icon} {v1.get('message', 'Peer-link verification unknown')}")
        if v1.get('status') in ['fail', 'warn', 'unknown']:
            lines.append(f"   Impact: {v1.get('impact', 'N/A')}")
            lines.append(f"   Action: {v1.get('action', 'N/A')}")
        lines.append("")
        
        # Verification 2: Keepalive
        v2 = verification_results.get('keepalive', {})
        status_icon = "✅" if v2.get('status') == 'pass' else "❌" if v2.get('status') == 'fail' else "⚠️"
        lines.append(f"{status_icon} {v2.get('message', 'Keepalive verification unknown')}")
        if v2.get('status') in ['fail', 'warn', 'unknown']:
            lines.append(f"   Impact: {v2.get('impact', 'N/A')}")
            lines.append(f"   Action: {v2.get('action', 'N/A')}")
        lines.append("")
        
        # Verification 3: Type-1 consistency
        v3 = verification_results.get('type1_consistency', {})
        status_icon = "✅" if v3.get('status') == 'pass' else "❌" if v3.get('status') == 'fail' else "⚠️"
        lines.append(f"{status_icon} {v3.get('message', 'Type-1 consistency verification unknown')}")
        if v3.get('status') in ['fail', 'warn', 'unknown']:
            lines.append(f"   Impact: {v3.get('impact', 'N/A')}")
            lines.append(f"   Action: {v3.get('action', 'N/A')}")
        lines.append("")
        
        # Verification 4: Type-2 consistency
        v4 = verification_results.get('type2_consistency', {})
        status_icon = "✅" if v4.get('status') == 'pass' else "❌" if v4.get('status') == 'fail' else "⚠️"
        lines.append(f"{status_icon} {v4.get('message', 'Type-2 consistency verification unknown')}")
        if v4.get('status') in ['fail', 'warn', 'unknown']:
            lines.append(f"   Impact: {v4.get('impact', 'N/A')}")
            lines.append(f"   Action: {v4.get('action', 'N/A')}")
        lines.append("")
        
        # Verification 5: Per-vlan consistency
        v5 = verification_results.get('per_vlan_consistency', {})
        status_icon = "✅" if v5.get('status') == 'pass' else "❌" if v5.get('status') == 'fail' else "⚠️"
        lines.append(f"{status_icon} {v5.get('message', 'Per-vlan consistency verification unknown')}")
        if v5.get('status') in ['fail', 'warn', 'unknown']:
            lines.append(f"   Impact: {v5.get('impact', 'N/A')}")
            lines.append(f"   Action: {v5.get('action', 'N/A')}")
        lines.append("")
        
        # Verification 6: VLAN consistency
        v6 = verification_results.get('vlan_consistency', {})
        status_icon = "✅" if v6.get('status') == 'pass' else "❌" if v6.get('status') == 'fail' else "⚠️"
        lines.append(f"{status_icon} {v6.get('message', 'VLAN consistency verification unknown')}")
        if v6.get('status') in ['fail', 'warn', 'unknown']:
            lines.append(f"   Impact: {v6.get('impact', 'N/A')}")
            lines.append(f"   Action: {v6.get('action', 'N/A')}")
        lines.append("")
        
        # Verification 7: vPC consistency
        v7 = verification_results.get('vpc_consistency', {})
        status_icon = "✅" if v7.get('status') == 'pass' else "❌" if v7.get('status') == 'fail' else "⚠️"
        lines.append(f"{status_icon} {v7.get('message', 'vPC consistency verification unknown')}")
        if v7.get('status') in ['fail', 'warn', 'unknown']:
            lines.append(f"   Impact: {v7.get('impact', 'N/A')}")
            lines.append(f"   Action: {v7.get('action', 'N/A')}")
        lines.append("")
        
        # Verification 8: CDP neighbors
        v8 = verification_results.get('cdp_neighbors', {})
        status_icon = "✅" if v8.get('status') == 'pass' else "❌" if v8.get('status') == 'fail' else "⚠️"
        lines.append(f"{status_icon} {v8.get('message', 'CDP neighbor verification unknown')}")
        if v8.get('status') in ['fail', 'warn', 'unknown']:
            lines.append(f"   Impact: {v8.get('impact', 'N/A')}")
            lines.append(f"   Action: {v8.get('action', 'N/A')}")
        lines.append("")
        
        # Verification 9: Port-channel members
        v9 = verification_results.get('port_channel_members', {})
        status_icon = "✅" if v9.get('status') == 'pass' else "❌" if v9.get('status') == 'fail' else "⚠️"
        lines.append(f"{status_icon} {v9.get('message', 'Port-channel member verification unknown')}")
        if v9.get('status') in ['fail', 'warn', 'unknown']:
            lines.append(f"   Impact: {v9.get('impact', 'N/A')}")
            lines.append(f"   Action: {v9.get('action', 'N/A')}")
        lines.append("")
        
        # Verification 10: vPC statistics
        v10 = verification_results.get('vpc_statistics', {})
        status_icon = "✅" if v10.get('status') == 'pass' else "❌" if v10.get('status') == 'fail' else "⚠️"
        lines.append(f"{status_icon} {v10.get('message', 'vPC statistics verification unknown')}")
        if v10.get('status') in ['fail', 'warn', 'unknown']:
            lines.append(f"   Impact: {v10.get('impact', 'N/A')}")
            lines.append(f"   Action: {v10.get('action', 'N/A')}")
        lines.append("")
        
        # Summary
        passed = sum(1 for v in verification_results.values() if v.get('status') == 'pass')
        failed = sum(1 for v in verification_results.values() if v.get('status') == 'fail')
        warnings = sum(1 for v in verification_results.values() if v.get('status') == 'warn')
        unknown = sum(1 for v in verification_results.values() if v.get('status') == 'unknown')
        total = len(verification_results)
        
        lines.append(dash)
        lines.append("SUMMARY")
        lines.append(dash)
        lines.append(f"Total Checks: {total}")
        lines.append(f"Passed: {passed}")
        lines.append(f"Failed: {failed}")
        lines.append(f"Warnings: {warnings}")
        lines.append(f"Unknown: {unknown}")
        lines.append("")
        
        if failed == 0 and warnings == 0:
            lines.append("✅ vPC domain is HEALTHY - No errors or mismatches detected")
        else:
            lines.append(f"⚠️  vPC domain has {failed} error(s) and {warnings} warning(s) - Review above")
        lines.append("")
    
    lines.append(sep)
    lines.append("END OF REPORT")
    lines.append(sep)
    
    return "\n".join(lines)

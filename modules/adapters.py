# ============================================================================
# AI_NAVIGATION_BREADCRUMBS - modules/adapters.py
# ============================================================================
# PURPOSE: Centralized task orchestration adapter layer.
# REDUCTION: Eliminates ~90% code duplication between web and GUI interfaces.
#
# KEY_FUNCTIONS:
#   - run_generic_plugin(plugin_id, devices, credentials, params, config, log):
#     Generic plugin execution with credential bundling
#   - run_vlan_audit(devices, credentials, params, log): VLAN audit workflow
#   - run_vpc_domain(devices, credentials, params, log): vPC domain workflow
#   - run_interface_discovery(devices, credentials, params, log): Interface discovery
#   - run_network_discovery(devices, credentials, params, log): Network discovery
#
# CONTRACT:
#   - All functions accept a `log` callable: log(msg: str)
#   - All functions return a list of structured JSON results (per device)
#   - All file I/O is delegated to utils/report_formatter.py
#   - All network I/O is delegated to the /modules/ feature modules
#
# CREDENTIAL_BUNDLING:
#   run_generic_plugin() calls bundle_for_plugin() from utils/collection_credentials.py
#   This includes fallback_credentials in the credentials dict passed to plugins
#
# OUTPUT FORMAT (per device):
#   {
#       "device": "x.x.x.x",
#       "status": "success|fail",
#       "data": {},
#       "error": null
#   }
#
# CONNECTIONS:
#   - Called by: vlan_checker_web.py (web API routes)
#   - Called by: vlan_checker_gui.py (GUI actions)
#   - Calls: utils/collection_credentials.py (credential bundling)
#   - Calls: modules/plugin_registry.py (plugin execution)
#   - Calls: modules/network_base.py (network operations)
#
# USAGE_PATTERN:
#   results = run_generic_plugin('cisco_asset_warranty', devices,
#                                 credentials, params, config, log_func)
#
# ============================================================================
"""
modules/adapters.py
-------------------
Centralized Task Orchestration Adapter Layer.

PURPOSE:
    Eliminate ~90% code duplication between vlan_checker_web.py and vlan_checker_gui.py
    by providing a single, shared implementation of every network workflow loop.

CONTRACT:
    - All functions accept a `log` callable: log(msg: str)
    - All functions return a list of structured JSON results (per device)
    - All file I/O is delegated to utils/report_formatter.py
    - All network I/O is delegated to the /modules/ feature modules

OUTPUT FORMAT (per device):
    {
        "device": "x.x.x.x",
        "status": "success|fail",
        "data": {},
        "error": null
    }
"""

import os
import json
from datetime import datetime
import sys

# --- Helpers ---

def _abort_if_cancelled(log) -> bool:
    """Cooperative cancel for long-running multi-device loops."""
    try:
        from utils.task_control_plane import should_abort
        if should_abort():
            log("[Control Plane] Task cancelled — stopping remaining devices.")
            return True
    except Exception:
        pass
    return False


def _device_progress(idx: int, total: int, host: str = '') -> None:
    """Report devices_done / devices_total to the control-plane task registry."""
    try:
        from utils.task_control_plane import update_task_progress
        msg = f'{host} ({idx}/{total})' if host else f'Device {idx}/{total}'
        update_task_progress(devices_done=idx, devices_total=total, message=msg)
    except Exception:
        pass

def _get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def _get_app_working_dir():
    """Writable data root for reports/logs (never the install directory)."""
    from utils.output_paths import get_data_root
    return get_data_root()


def _build_vpc_member_interfaces(member_name, meta):
    """
    Per-switch vPC interface registry for HTML sidebar and diagnostic exports.
    Merges show vpc table rows with port-channel physical members.
    """
    entries = []
    seen = set()

    def _add(entry):
        key = (entry.get('vpc_id'), entry.get('port_channel'), tuple(entry.get('member_interfaces', [])))
        if key in seen:
            return
        seen.add(key)
        entries.append(entry)

    vpc_structured = meta.get('vpc_structured') or {}
    if isinstance(vpc_structured, dict):
        for row in vpc_structured.get('vpc_table', []):
            if not isinstance(row, dict):
                continue
            po = row.get('po') or row.get('port_channel') or ''
            vpc_id = row.get('vpc_id', '')
            members = []
            pc_detail = meta.get('port_channel_detail', {}).get(po, {})
            for mem in pc_detail.get('members', []):
                if isinstance(mem, dict):
                    members.append(mem.get('intf', ''))
                elif isinstance(mem, str):
                    members.append(mem)
            _add({
                'source': 'show_vpc',
                'vpc_id': str(vpc_id),
                'port_channel': po,
                'status': row.get('status', 'unknown'),
                'consistency': row.get('consistency', 'unknown'),
                'active_vlans': row.get('active_vlans', '-'),
                'member_interfaces': [m for m in members if m],
                'role': vpc_structured.get('role', 'unknown'),
                'peer_status': vpc_structured.get('peer_status', 'unknown'),
                'keepalive_status': vpc_structured.get('keepalive_status', 'unknown'),
            })

    vpc_details = meta.get('vpc_details') or {}
    for po_name, details in vpc_details.items():
        if not isinstance(details, dict) or str(po_name).startswith('_'):
            continue
        if details.get('type') != 'vpc':
            continue
        members = []
        pc_detail = meta.get('port_channel_detail', {}).get(po_name, {})
        for mem in pc_detail.get('members', []):
            if isinstance(mem, dict):
                members.append(mem.get('intf', ''))
            elif isinstance(mem, str):
                members.append(mem)
        _add({
            'source': 'vpc_details',
            'vpc_id': str(details.get('vpc_id', '')),
            'port_channel': po_name,
            'status': details.get('status', 'unknown'),
            'consistency': details.get('consistency', 'unknown'),
            'active_vlans': details.get('active_vlans', '-'),
            'member_interfaces': [m for m in members if m],
        })

    peer_po = vpc_structured.get('peer_link_po', '') if isinstance(vpc_structured, dict) else ''
    if peer_po and peer_po in (meta.get('port_channel_detail') or {}):
        members = []
        for mem in meta['port_channel_detail'][peer_po].get('members', []):
            if isinstance(mem, dict):
                members.append(mem.get('intf', ''))
            elif isinstance(mem, str):
                members.append(mem)
        _add({
            'source': 'peer_link',
            'vpc_id': 'peer-link',
            'port_channel': peer_po,
            'status': (vpc_details.get(peer_po) or {}).get('status', 'unknown'),
            'consistency': 'n/a',
            'active_vlans': '-',
            'member_interfaces': [m for m in members if m],
            'entry_type': 'peer-link',
        })

    return {
        'switch': member_name,
        'interface_count': len(entries),
        'entries': entries,
    }


def _build_html_presentation_payload(nodes_json, edges_json, map_mode):
    """Flatten nodes/edges into sections that match the HTML sidebar."""
    payload = {
        '_README': (
            'HTML Presentation Payload — data that maps 1:1 to the topology map UI.\n'
            'Sections: vpc_domains, member_interfaces_by_switch, consistency_tables, graph_edges.\n'
            'Edit vpc_map_data_TEMPLATE.json in this folder to inject lab/production data.'
        ),
        'map_mode': map_mode,
        'vpc_domains': [],
        'member_interfaces_by_switch': {},
        'consistency_tables': [],
        'graph_edges': [],
    }
    for n in nodes_json:
        if not str(n.get('id', '')).startswith('VPC_Domain_'):
            continue
        domain_id = n.get('vpc_domain_id', '')
        members = n.get('vpc_members', [])
        payload['vpc_domains'].append({
            'domain_id': domain_id,
            'node_id': n.get('id'),
            'members': members,
            'health': (n.get('correlation') or {}),
            'vpc_details': n.get('vpc_details', {}),
            'vpc_structured': n.get('vpc_structured', []),
            'vpc_member_interfaces': n.get('vpc_member_interfaces', {}),
        })
        for m in members:
            mi = (n.get('vpc_member_interfaces') or {}).get(m)
            if mi:
                payload['member_interfaces_by_switch'][m] = mi
        for vs in n.get('vpc_structured') or []:
            if not isinstance(vs, dict):
                continue
            peer = vs.get('member', '?')
            table = (vs.get('vpc_structured') or {}).get('vpc_table', [])
            for row in table:
                if isinstance(row, dict):
                    payload['consistency_tables'].append({'member': peer, **row})

    for e in edges_json:
        payload['graph_edges'].append({
            'from': e.get('from'),
            'to': e.get('to'),
            'type': e.get('type') or (e.get('edge_data') or {}).get('type'),
            'label': e.get('label'),
            'bundled_links': e.get('bundled_links')
                or (e.get('edge_data') or {}).get('bundled_links', []),
        })
    if map_mode == 'vpc':
        payload['board_sections'] = _build_vpc_board_sections(nodes_json, edges_json, payload)
    return payload


def _extract_global_consistency_raw(vpc_details):
    """Pull raw CLI text from vpc_details metadata blob."""
    if not isinstance(vpc_details, dict):
        return ''
    block = vpc_details.get('_consistency_global') or vpc_details.get('_consistency_global_raw')
    if isinstance(block, dict):
        return block.get('raw') or block.get('text') or ''
    return str(block) if block else ''


def _build_vpc_board_sections(nodes_json, edges_json, presentation):
    """Structured data for offline Engineering Board (no Vis.js)."""
    domains_out = []
    for dom in presentation.get('vpc_domains', []):
        domain_id = dom.get('domain_id', '')
        node_id = dom.get('node_id') or f'VPC_Domain_{domain_id}'
        node = next((n for n in nodes_json if n.get('id') == node_id), {})
        correlation = node.get('correlation') or dom.get('health') or {}
        peers = []
        for m in dom.get('members', []):
            peer_node = next((n for n in nodes_json if n.get('id') == m), {})
            vs = peer_node.get('vpc_structured') or {}
            if isinstance(vs, list):
                for entry in vs:
                    if entry.get('member') == m:
                        vs = entry.get('vpc_structured') or {}
                        break
            vd = peer_node.get('vpc_details') or {}
            is_scanned = peer_node.get('is_scanned', True) and bool(
                peer_node.get('vpc_details') or peer_node.get('interface_trust_chains')
                or peer_node.get('interfaces')
            )
            peers.append({
                'hostname': m,
                'role': (vs.get('role') if isinstance(vs, dict) else 'unknown') or 'unknown',
                'peer_status': vs.get('peer_status', 'unknown') if isinstance(vs, dict) else 'unknown',
                'keepalive_status': vs.get('keepalive_status', 'unknown') if isinstance(vs, dict) else 'unknown',
                'peer_link_po': vs.get('peer_link_po', '') if isinstance(vs, dict) else '',
                'serial': (peer_node.get('device_info') or {}).get('version', ''),
                'mgmt_ip': (peer_node.get('device_info') or {}).get('mgmt_ip', ''),
                'nxos_version': peer_node.get('nxos_version', ''),
                'is_scanned': is_scanned,
                'global_consistency': _extract_global_consistency_raw(vd),
                'vpc_table': (vs.get('vpc_table', []) if isinstance(vs, dict) else []),
                'port_channels': peer_node.get('port_channels') or peer_node.get('port_channel_detail') or {},
                'member_interfaces': (dom.get('vpc_member_interfaces') or {}).get(m) or {},
                'interface_trust_chains': peer_node.get('interface_trust_chains') or [],
                'trust_alerts': peer_node.get('trust_alerts') or [],
            })
        downstream = []
        member_set = set(dom.get('members', []))
        for e in edges_json:
            et = e.get('type') or ''
            if et not in ('vpc_shared', 'vpc_orphan', 'vpc', 'vpc-peer-link', 'vpc-domain-peer'):
                continue
            bl = e.get('bundled_links') or []
            for link in bl:
                sw = link.get('from') or e.get('from')
                if sw in member_set:
                    downstream.append({
                        'switch': sw,
                        'local_port': link.get('f_port', ''),
                        'remote_host': link.get('to') or e.get('to'),
                        'remote_port': link.get('t_port', ''),
                        'speed': link.get('speed', ''),
                        'status': link.get('status', ''),
                        'edge_type': et,
                        'vpc_label': e.get('label', ''),
                        'confidence': link.get('confidence') or e.get('confidence', ''),
                        'trust_tier': link.get('trust_tier') or e.get('trust_tier', ''),
                        'trust_score': link.get('trust_score') or e.get('trust_score', ''),
                        'bidirectional': link.get('bidirectional', e.get('bidirectional', False)),
                    })
            if et == 'vpc-peer-link':
                downstream.append({
                    'switch': e.get('from'),
                    'local_port': e.get('f_port', ''),
                    'remote_host': e.get('to'),
                    'remote_port': e.get('t_port', ''),
                    'edge_type': 'peer-link',
                    'vpc_label': 'Peer-Link',
                    'confidence': e.get('confidence', ''),
                    'trust_tier': e.get('trust_tier', ''),
                    'trust_score': e.get('trust_score', ''),
                    'bidirectional': e.get('bidirectional', False),
                })
        dom_corr = correlation if isinstance(correlation, dict) else {}
        domains_out.append({
            'domain_id': domain_id,
            'node_id': node_id,
            'members': dom.get('members', []),
            'health': correlation,
            'peers': peers,
            'downstream_links': downstream,
            'interface_trust_chains': dom_corr.get('interface_trust_chains', []),
            'domain_completeness': dom_corr.get('domain_completeness', {}),
            'trust_alerts': dom_corr.get('trust_alerts', []),
            'consistency_rows': [
                r for r in presentation.get('consistency_tables', [])
                if r.get('member') in member_set
            ],
        })
    return {'domains': domains_out, 'default_domain': domains_out[0]['domain_id'] if domains_out else ''}


def _assign_vpc_fixed_positions(nodes_json, edges_json, max_downstream_visible=8):
    """
    Assign fixed x,y for vPC simplified map (physics off).
    Domain center, peers left/right, downstream in a row below.
    """
    domain_nodes = [n for n in nodes_json if str(n.get('id', '')).startswith('VPC_Domain_')]
    for dnode in domain_nodes:
        did = dnode.get('vpc_domain_id') or dnode.get('id', '').replace('VPC_Domain_', '')
        members = list(dnode.get('vpc_members') or [])
        cx, cy = 0, -120
        dnode['x'] = cx
        dnode['y'] = cy
        dnode['fixed'] = True
        peer_positions = {}
        if len(members) >= 1:
            peer_positions[members[0]] = (-320, 80)
        if len(members) >= 2:
            peer_positions[members[1]] = (320, 80)
        for i, m in enumerate(members[2:], start=2):
            peer_positions[m] = (-320 + i * 200, 80)
        for n in nodes_json:
            if n.get('id') in peer_positions:
                n['x'] = peer_positions[n['id']][0]
                n['y'] = peer_positions[n['id']][1]
                n['fixed'] = True
        downstream_hosts = []
        member_set = set(members) | {dnode.get('id')}
        for e in edges_json:
            et = e.get('type', '')
            if et in ('vpc_shared', 'vpc_orphan', 'standard', ''):
                for end in (e.get('to'), e.get('from')):
                    if end and end not in member_set and not str(end).startswith('VPC_Domain_'):
                        if end not in downstream_hosts:
                            downstream_hosts.append(end)
        hidden_downstream = downstream_hosts[max_downstream_visible:]
        visible_downstream = downstream_hosts[:max_downstream_visible]
        row_y = 320
        for i, host in enumerate(visible_downstream):
            n = next((x for x in nodes_json if x.get('id') == host), None)
            if n:
                n['x'] = -400 + (i % 10) * 90
                n['y'] = row_y + (i // 10) * 70
                n['fixed'] = True
        if hidden_downstream:
            collapse_id = f'VPC_Downstream_{did}'
            if not any(n.get('id') == collapse_id for n in nodes_json):
                nodes_json.append({
                    'id': collapse_id,
                    'label': f'+{len(hidden_downstream)} hosts',
                    'shape': 'ellipse',
                    'x': 0,
                    'y': row_y + 80,
                    'fixed': True,
                    'color': {'background': '#64748b', 'border': '#475569'},
                    'font': {'size': 12, 'color': '#fff'},
                    'is_collapsed_meta': True,
                    'hidden_hosts': hidden_downstream,
                })
            for hid in hidden_downstream:
                hn = next((x for x in nodes_json if x.get('id') == hid), None)
                if hn:
                    hn['hidden'] = True
                    hn['vpc_collapsed'] = True

    _ensure_vpc_nodes_positioned(nodes_json, edges_json)


def _dedupe_nodes_json(nodes_json):
    """One vis node per device id (case-insensitive); keep richest record."""
    if not nodes_json:
        return []
    by_key = {}
    order = []
    for n in nodes_json:
        nid = str(n.get('id', '')).strip()
        if not nid:
            continue
        key = nid.lower()
        if key not in by_key:
            by_key[key] = dict(n)
            order.append(key)
            continue
        prev = by_key[key]
        score_prev = len(prev) + (10 if prev.get('is_scanned') else 0)
        score_new = len(n) + (10 if n.get('is_scanned') else 0)
        if score_new >= score_prev:
            merged = dict(prev)
            merged.update(n)
            by_key[key] = merged
    return [by_key[k] for k in order]


def _ensure_vpc_nodes_positioned(nodes_json, edges_json):
    """Assign grid x,y to any node still missing coordinates (physics off requires fixed layout)."""
    import math
    missing = [n for n in nodes_json if n.get('x') is None and n.get('y') is None and not n.get('hidden')]
    if not missing:
        for n in nodes_json:
            if n.get('x') is not None:
                n['fixed'] = True
        return
    ids = [n['id'] for n in missing]
    adj = {i: set() for i in ids}
    for e in edges_json or []:
        f, t = e.get('from'), e.get('to')
        if f in adj and t in adj:
            adj[f].add(t)
            adj[t].add(f)
    placed = {}
    visited = set()

    def _place_component(start_id, base_x, base_y):
        queue = [(start_id, 0)]
        visited.add(start_id)
        placed[start_id] = (base_x, base_y)
        qi = 0
        while qi < len(queue):
            nid, depth = queue[qi]
            qi += 1
            px, py = placed[nid]
            neighbors = sorted(adj.get(nid, []))
            for j, nb in enumerate(neighbors):
                if nb in visited:
                    continue
                visited.add(nb)
                angle = (j / max(len(neighbors), 1)) * math.pi * 2
                placed[nb] = (px + int(180 * math.cos(angle)), py + int(120 * math.sin(angle)) + depth * 40)
                queue.append((nb, depth + 1))

    comp_x = 0
    for nid in ids:
        if nid in visited:
            continue
        _place_component(nid, comp_x, 0)
        comp_x += 520

    if len(placed) < len(missing):
        cols = max(2, int(math.ceil(math.sqrt(len(missing)))))
        for i, n in enumerate(missing):
            if n['id'] not in placed:
                placed[n['id']] = ((i % cols) * 200, (i // cols) * 140)

    for n in nodes_json:
        if n.get('id') in placed:
            n['x'] = placed[n['id']][0]
            n['y'] = placed[n['id']][1]
            n['fixed'] = True
        elif n.get('x') is not None:
            n['fixed'] = True


def _load_vis_js(log):
    candidates = [
        _get_resource_path("vis-network.min.js"),
        _get_resource_path(os.path.join("modules", "web", "vis-network.min.js")),
        os.path.join(os.path.dirname(__file__), "web", "vis-network.min.js"),
    ]
    for vis_js_path in candidates:
        try:
            with open(vis_js_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            continue
    log("  [ERROR] Failed to load offline vis-network library from known paths.")
    return "// Offline library load failed. Please ensure vis-network.min.js is bundled."


def _cfg_state_label(device_type):
    dtype = (device_type or "").lower()
    if "juniper" in dtype:
        return "committed"
    return "running-only"


# === ADAPTER FUNCTIONS ===

def run_connectivity(devices, user, pwd, enb_pwd, log):
    """Connectivity & Auth check across a device list with structured logging."""
    import modules.connectivity
    from utils.structured_logger import get_logger, OperationType, create_legacy_adapter
    
    logger = get_logger()
    log("\n--- Starting Connectivity & Auth Check ---")
    results = []
    success_count = 0
    
    for dev in devices:
        if _abort_if_cancelled(log):
            break
        host = dev['host']
        legacy_log = create_legacy_adapter(OperationType.CONNECTIVITY_CHECK, host)
        
        logger.log_operation_start(OperationType.CONNECTIVITY_CHECK, host, {})
        log(f"Checking {host}...")
        
        # Pass log function for disconnect logging
        res = modules.connectivity.run(dev, user, pwd, enb_pwd, log_func=log)
        results.append(res)
        
        ping_success = res['data'].get('ping_success', res['data'].get('ping', False))
        ssh_success = res['data'].get('ssh_success', res['data'].get('ssh', False))
        
        if res['status'] == 'success':
            success_count += 1
            if ping_success:
                log(f"  [PASS] Ping")
                logger.log_connection_event(host, "ping", True)
            else:
                log(f"  [FAIL] Ping (Host unreachable)")
                logger.log_connection_event(host, "ping", False, {"reason": "Host unreachable"})
            
            if ssh_success:
                log(f"  [PASS] SSH Authentication")
                logger.log_connection_event(host, "ssh_auth", True)
            else:
                log(f"  [FAIL] SSH Authentication")
                logger.log_connection_event(host, "ssh_auth", False, {"reason": "Authentication failed"})
            
            logger.log_operation_complete(
                OperationType.CONNECTIVITY_CHECK, host, 0, "success",
                {"ping": ping_success, "ssh": ssh_success}
            )
        else:
            if not ping_success:
                log(f"  [FAIL] Ping")
            error_msg = res.get('error', 'Unknown error')
            log(f"  [FAIL] {error_msg}")
            logger.error(f"Connectivity check failed: {error_msg}", 
                        OperationType.CONNECTIVITY_CHECK, host)
    
    log(f"[SUMMARY] {success_count}/{len(devices)} devices reachable")
    log("--- Connectivity Check Complete ---\n")
    return results


def run_startup_backup_check(devices, log):
    """
    Run startup backup check for all devices.
    Warns if any device hasn't been backed up in the last 24 hours.
    
    Args:
        devices: List of device dictionaries
        log: Logging callback function
        
    Returns:
        List of warnings for devices with stale/missing backups
    """
    from utils.config_backup_system import get_backup_system
    from utils.structured_logger import get_logger, OperationType
    
    logger = get_logger()
    backup_system = get_backup_system()
    
    log("\n--- Starting Backup Health Check ---")
    logger.info("Running startup backup check", OperationType.CONFIG_BACKUP)
    
    warnings = []
    for dev in devices:
        if _abort_if_cancelled(log):
            break
        host = dev.get('host', 'unknown')
        # Try to get expected hostname (use host if unknown)
        hostname = host
        
        check_result = backup_system.check_backup_age(hostname, max_age_hours=24)
        
        if check_result.get("warning"):
            warning_msg = f"[{host}] {check_result.get('message')}"
            log(f"  [WARNING] {warning_msg}")
            warnings.append({
                "device": host,
                **check_result
            })
            logger.warning(warning_msg, OperationType.CONFIG_BACKUP, host)
        else:
            log(f"  [OK] {host}: {check_result.get('message')}")
    
    if warnings:
        log(
            f"\n[WARNING] {len(warnings)} device(s) need backup. "
            "Use Tools → Config backup & save (or Fleet Backup), then Compare in Evidence/Tools."
        )
    else:
        log("\n[OK] All devices have recent backups.")
    
    log("--- Backup Health Check Complete ---\n")
    return warnings


def run_vlan_audit(devices, user, pwd, enb_pwd, log):
    """VLAN audit across device list. Returns raw/parsed data and saves report files."""
    import modules.vlan_audit
    from utils import report_formatter
    from utils.output_paths import CAT_VLAN_AUDIT, path_in_run, prepare_run_output, write_run_manifest

    log("\n--- Starting VLAN Audit ---")
    paths = prepare_run_output(CAT_VLAN_AUDIT)
    raw_file = path_in_run(paths, 'vlan_raw.txt')
    parsed_file = path_in_run(paths, 'vlan_parsed.txt')
    log(f"[Output] VLAN audit folder: {paths['run_dir']}")
    report_formatter.init_vlan_parsed_report(parsed_file)

    results = []

    def _vlan_audit_worker(dev, _idx):
        return modules.vlan_audit.run(dev, user, pwd, enb_pwd)

    from utils.parallel_device_pool import foreach_device_parallel
    collected = foreach_device_parallel(
        devices, _vlan_audit_worker, log=log, label='VLAN audit',
    )
    for res in collected:
        if res is None:
            continue
        results.append(res)
        host = res.get('device') or res.get('host') or '?'
        if res['status'] == 'success':
            true_host = res['data'].get('true_host', host)
            raw_out = res['data'].get('raw_output', res['data'].get('output', ''))
            parsed = res['data'].get('parsed_vlans', [])
            report_formatter.append_text_file(raw_file, f"\n--- {true_host} ---\n{raw_out}")
            report_formatter.append_vlan_parsed_report(parsed_file, true_host, parsed)
            log(f"  [SUCCESS] {true_host}: Retrieved & Parsed {len(parsed)} VLANs")
        else:
            log(f"  [ERROR] {host}: {res.get('error', 'Unknown error')}")
            report_formatter.append_text_file(raw_file, f"\n--- {host} FAILED ---\n{res.get('error')}")

    write_run_manifest(paths, {'raw_path': raw_file, 'parsed_path': parsed_file})
    log(f"--- VLAN Audit Complete. Raw: {raw_file}, Parsed: {parsed_file} ---\n")
    return results, raw_file, parsed_file


def run_mac_trace(devices, user, pwd, enb_pwd, target_mac, log):
    """MAC trace across device list with persisted TXT + HTML under data root."""
    import modules.mac_trace
    from utils.mac_trace_formatter import write_mac_trace_html
    from utils.output_paths import CAT_MAC_TRACE, path_in_run, prepare_run_output, slugify, write_run_manifest
    from utils import report_formatter
    from utils.task_control_plane import should_abort

    log(f"\n--- Tracing MAC: {target_mac} ---")
    safe_mac = slugify(target_mac.replace(':', '-').replace('.', '-'))
    paths = prepare_run_output(CAT_MAC_TRACE, safe_mac)
    out_file = paths['txt_path']
    html_file = paths['html_path']
    log(f"[Output] MAC trace folder: {paths['run_dir']}")

    total_found = 0
    results = []
    path_hops = []
    endpoint = None
    ambiguous_devices = []
    n_dev = len(devices)

    def _mac_worker(dev, idx):
        return idx, dev['host'], modules.mac_trace.run(dev, user, pwd, enb_pwd, target_mac)

    from utils.parallel_device_pool import foreach_device_parallel, get_max_workers
    log(f"[Parallel SSH] MAC trace: up to {get_max_workers()} concurrent session(s).")
    collected = foreach_device_parallel(
        devices, _mac_worker, log=log, label='MAC trace',
    )

    for item in collected:
        if item is None:
            continue
        idx, host, res = item
        hop_idx = idx + 1
        results.append(res)
        if res['status'] == 'success':
            true_host = res['data'].get('true_host', host)
            found = res['data'].get('found', False)
            ambiguous = res['data'].get('ambiguous', False)
            matches = res['data'].get('results', res['data'].get('matches', []))
            if ambiguous:
                msg = res['data'].get('ambiguous_message', 'Partial MAC matches multiple addresses')
                ambiguous_devices.append({'host': true_host, 'message': msg, 'macs': res['data'].get('distinct_macs', [])})
                hop = {
                    'hop_index': hop_idx,
                    'device_ip': host,
                    'hostname': true_host,
                    'found': False,
                    'ambiguous': True,
                    'distinct_macs': res['data'].get('distinct_macs', []),
                    'vlan': None,
                    'port': None,
                    'status': 'ambiguous',
                    'message': msg,
                }
                path_hops.append(hop)
                log(f"  [AMBIGUOUS] {true_host}: {msg}")
                continue
            hop = {
                'hop_index': hop_idx,
                'device_ip': host,
                'hostname': true_host,
                'found': found or bool(matches),
                'vlan': res['data'].get('vlan'),
                'port': res['data'].get('port'),
                'status': 'found' if (found or matches) else 'not_found',
                'distinct_macs': res['data'].get('distinct_macs') or [],
                'resolved_mac': res['data'].get('resolved_mac'),
            }
            path_hops.append(hop)
            if matches:
                for r in matches:
                    if isinstance(r, dict):
                        log(f"  [FOUND] {host} | VLAN: {r.get('vlan','-')} | Int: {r.get('interface','-')} | Raw: {r.get('raw', '')}")
                    else:
                        log(f"  [FOUND] {host} | {r}")
                    total_found += 1
            elif found:
                resolved = res['data'].get('resolved_mac')
                log(f"  [FOUND] {host} | MAC: {resolved or target_mac} | VLAN: {res['data'].get('vlan','-')} | Int: {res['data'].get('port','-')}")
                total_found += 1
                mac_label = resolved or target_mac
                endpoint = f"{mac_label} @ {true_host} — {res['data'].get('port')} (VLAN {res['data'].get('vlan', 'N/A')})"
            else:
                log(f"  [OK] {host}: MAC not found.")
        else:
            path_hops.append({
                'hop_index': hop_idx,
                'device_ip': host,
                'hostname': host,
                'found': False,
                'status': 'error',
                'vlan': None,
                'port': None,
            })
            log(f"  [ERROR] {host}: {res.get('error', 'Unknown error')}")

    lines = [
        f"MAC ADDRESS TRACE REPORT: {target_mac}",
        "=" * 60,
        f"Devices Scanned: {len(results)}",
        f"Occurrences Found: {total_found}",
        "",
    ]
    if ambiguous_devices:
        lines.append("AMBIGUOUS PARTIAL MAC MATCHES (refine to full MAC):")
        lines.append("-" * 60)
        for ad in ambiguous_devices:
            lines.append(f"  {ad['host']}: {ad['message']}")
        lines.append("")
    for hop in path_hops:
        if hop.get('status') == 'ambiguous':
            lines.append(f"[AMBIGUOUS] {hop['hostname']} — {hop.get('message', 'multiple MAC matches')}")
        elif hop.get('found'):
            mac_part = f" — MAC {hop['resolved_mac']}" if hop.get('resolved_mac') else ''
            lines.append(f"[FOUND] {hop['hostname']}{mac_part} — {hop.get('port')} VLAN {hop.get('vlan')}")
        elif hop.get('status') == 'error':
            lines.append(f"[ERROR] {hop['hostname']}")
        else:
            lines.append(f"[NOT FOUND] {hop['hostname']}")
    report_formatter.write_text_file(out_file, "\n".join(lines))
    amb_summary = None
    if ambiguous_devices:
        amb_summary = '; '.join(
            f"{a['host']}: {len(a.get('macs', []))} distinct MAC(s)" for a in ambiguous_devices
        )
    write_mac_trace_html(
        html_file, target_mac, path_hops,
        found_endpoint=endpoint or ('Ambiguous — refine MAC' if ambiguous_devices else 'Not found'),
        ambiguous_summary=amb_summary,
    )
    write_run_manifest(paths, {
        'target_mac': target_mac,
        'devices_scanned': len(devices),
        'found': total_found > 0,
        'ambiguous': bool(ambiguous_devices),
        'ambiguous_devices': ambiguous_devices,
        'endpoint': endpoint,
        'html_path': html_file,
        'txt_path': out_file,
    })
    log(f"[Output] MAC trace report: {out_file}")
    log(f"[Output] MAC trace HTML: {html_file}")
    log(f"--- Trace Complete. Found {total_found} occurrences. ---\n")
    if ambiguous_devices:
        log("[WARNING] Partial MAC matched multiple distinct addresses — refine to a full MAC.")
    return {
        'results': results,
        'txt_path': out_file,
        'html_path': html_file,
        'run_dir': paths['run_dir'],
        'found': total_found > 0,
        'ambiguous_devices': ambiguous_devices,
        'total_found': total_found,
    }


def run_vlan_management(action, devices, user, pwd, enb_pwd, vid, vname, log, dry_run=False, save_config=False):
    """VLAN add/rename/delete across device list. action: 'add'|'rename'|'delete'"""
    import modules.vlan_mgmt_production as vlan_mgmt_pro
    from utils import report_formatter
    from utils.structured_logger import get_logger, OperationType
    from utils.config_backup_system import get_backup_system

    labels = {'add': 'Adding', 'rename': 'Renaming', 'delete': 'Deleting'}
    mode_label = "DRY-RUN" if dry_run else "LIVE"
    log(f"\n--- {labels.get(action, action.title())} VLAN {vid} [{mode_label}] ---")
    
    # Initialize structured logging
    logger = get_logger()
    operation_map = {
        'add': OperationType.VLAN_ADD,
        'rename': OperationType.VLAN_RENAME,
        'delete': OperationType.VLAN_DELETE
    }
    operation_type = operation_map.get(action)
    
    from utils.output_paths import CAT_VLAN_MANAGEMENT, path_in_run, prepare_run_output, slugify, write_run_manifest

    results = []
    paths = prepare_run_output(CAT_VLAN_MANAGEMENT, slugify(f'{action}_vlan{vid}'))
    snapshot_dir = paths['run_dir']
    snapshot_files = {}
    log(f"[Output] VLAN {action} snapshots: {snapshot_dir}")

    if action == 'rename':
        junos_hosts = [
            d.get('host') for d in devices
            if 'juniper' in (d.get('device_type') or '').lower()
        ]
        if junos_hosts:
            msg = f"Rename VLAN is not supported on Juniper: {', '.join(junos_hosts)}"
            log(f"[ERROR] {msg}")
            for dev in devices:
                results.append({
                    'device': dev.get('host'),
                    'status': 'fail',
                    'data': {},
                    'error': msg,
                })
            try:
                with open(paths['txt_path'], 'w', encoding='utf-8') as tf:
                    tf.write(msg + '\n')
                write_run_manifest(paths, {'action': action, 'vlan_id': vid, 'error': msg})
            except OSError:
                pass
            log(f"[Output] VLAN report: {paths['txt_path']}")
            return results

    if not dry_run:
        from utils.golden_config_gate import evaluate_vlan_change, raise_if_blocked
        golden = evaluate_vlan_change(action, vid, vname)
        try:
            raise_if_blocked(golden)
        except RuntimeError as exc:
            log(f"[ERROR] {exc}")
            for dev in devices:
                results.append({
                    'device': dev.get('host'),
                    'status': 'fail',
                    'data': {'golden_config': golden},
                    'error': str(exc),
                })
            try:
                with open(paths['txt_path'], 'w', encoding='utf-8') as tf:
                    tf.write(str(exc) + '\n')
                write_run_manifest(paths, {'action': action, 'vlan_id': vid, 'error': str(exc)})
            except OSError:
                pass
            return results

    from utils.task_control_plane import should_abort
    from utils.parallel_device_pool import foreach_device_parallel

    if devices:
        backup_system = get_backup_system()
        backup_check = backup_system.check_backup_age(devices[0]['host'])
        if backup_check.get("warning"):
            log(f"  [WARNING] Backup check: {backup_check.get('message')}")

    def _vlan_worker(dev, _idx):
        host = dev['host']
        log(f"Processing {host}...")
        if action == 'add':
            return vlan_mgmt_pro.add_vlan(
                dev, user, pwd, enb_pwd, vid, vname,
                dry_run=dry_run, auto_backup=True, enable_idempotency=True, save_config=save_config,
            )
        if action == 'rename':
            return vlan_mgmt_pro.rename_vlan(
                dev, user, pwd, enb_pwd, vid, vname,
                dry_run=dry_run, auto_backup=True, enable_idempotency=True, save_config=save_config,
            )
        if action == 'delete':
            return vlan_mgmt_pro.delete_vlan(
                dev, user, pwd, enb_pwd, vid, vname,
                dry_run=dry_run, auto_backup=True, enable_idempotency=True, save_config=save_config,
            )
        return {"device": host, "status": "fail", "data": {}, "error": f"Unknown action: {action}"}

    collected = foreach_device_parallel(
        devices, _vlan_worker, log=log, label=f'VLAN {action}',
    )

    for idx, res in enumerate(collected):
        if res is None:
            continue
        dev = devices[idx]
        host = dev['host']
        safe_host = str(host).replace(":", "_").replace("/", "_")
        results.append(res)
        
        # Track backup path for snapshot reporting
        backup_path = res.get("data", {}).get("backup_path")
        if backup_path:
            snapshot_files[f"{safe_host}_prechange.txt"] = f"Backup: {backup_path}"
        
        # Enhanced result logging
        st = res.get('status', 'fail')
        if st == 'skipped' or res.get('data', {}).get('skipped'):
            reason = res.get('data', {}).get('reason', 'No action needed')
            log(f"  [SKIP] {reason}")
            continue

        if st == 'success' and res.get('data', {}).get('dry_run'):
            cmds = res.get("data", {}).get("commands", [])
            if cmds:
                log(f"  [PLAN] Commands: {' ; '.join(cmds)}")
            log("  [DRY-RUN] No configuration changes were sent to the device.")
            log("  [VERIFY] Post-change verification skipped in dry-run mode.")
            continue

        if st in ('success', 'verification_failed'):
            cmds = res.get("data", {}).get("commands", [])
            if cmds:
                log(f"  [PLAN] Commands: {' ; '.join(cmds)}")

            verification_passed = res.get("data", {}).get("verification_passed", False)
            post_check = res.get("data", {}).get("post_check", {})
            
            save_result = res.get("data", {}).get("save_result") or {}
            saved = save_result.get("saved")
            dtype_lower = (dev.get("device_type") or "").lower()

            if st == 'verification_failed' or not verification_passed:
                log(f"  [VERIFY FAILED] {host}: VLAN {vid} {action} — review device and backup.")
            elif verification_passed:
                log(f"  [SUCCESS] {host}: VLAN {vid} {action} complete and verified.")
            
            if action in ("add", "rename"):
                if post_check.get("vlan_exists"):
                    log(f"  [VERIFY] VLAN {vid} present after change.")
                else:
                    log(f"  [VERIFY] VLAN {vid} NOT found after change (review required).")
            elif action == "delete":
                if post_check.get("vlan_removed"):
                    log(f"  [VERIFY] VLAN {vid} removed after change.")
                else:
                    log(f"  [VERIFY] VLAN {vid} still present after delete attempt.")
            
            if saved:
                log("  [CONFIG] Persisted (commit/save complete).")
            elif save_config and save_result:
                log(f"  [CONFIG] Save attempted: {save_result.get('method', 'unknown')}"
                    + ('' if save_result.get('saved') else ' — not confirmed persisted'))
            elif "juniper" in dtype_lower and save_config:
                log("  [CONFIG] Junos commit/save not confirmed — review device.")
            else:
                log("  [CONFIG] Changed in running-config only (not yet saved to startup-config).")
                log("  [HINT] Run 'Save Device Config' for persistent save.")
            
            # Log backup location
            if backup_path:
                log(f"  [BACKUP] Pre-change snapshot: {backup_path}")
            continue

        error_msg = res.get('error', 'Unknown error')
        log(f"  [ERROR] {host}: {error_msg}")
    
    if snapshot_files:
        report_formatter.write_files_in_directory(snapshot_dir, snapshot_files)
        log(f"[System] Pre-change snapshots saved under: {snapshot_dir}/")

    changed = sum(
        1 for r in results
        if r.get('status') == 'success'
        and r.get('data', {}).get('verification_passed')
        and not r.get('data', {}).get('dry_run')
        and not r.get('data', {}).get('skipped')
    )
    skip_count = sum(1 for r in results if r.get('status') == 'skipped' or r.get('data', {}).get('skipped'))
    verify_fail = sum(1 for r in results if r.get('status') == 'verification_failed')
    fail_count = sum(1 for r in results if r.get('status') == 'fail')
    dry_count = sum(1 for r in results if r.get('data', {}).get('dry_run'))

    summary_lines = [
        f"VLAN {action} vlan_id={vid} name={vname or '-'}",
        f"Devices: {len(results)} | Changed+Verified: {changed} | Skipped: {skip_count} | "
        f"Verify failed: {verify_fail} | Failed: {fail_count} | Dry-run: {dry_count}",
        f"Mode: {'DRY-RUN' if dry_run else 'LIVE'}",
    ]
    try:
        with open(paths['txt_path'], 'w', encoding='utf-8') as tf:
            tf.write('\n'.join(summary_lines) + '\n')
            for r in results:
                tf.write(f"{r.get('device', '?')}: {r.get('status')} {r.get('error', '')}\n")
    except OSError:
        pass

    try:
        from utils.vlan_mgmt_formatter import write_vlan_mgmt_html
        write_vlan_mgmt_html(
            paths['html_path'], action, vid, vname or '', results, dry_run=dry_run,
        )
    except OSError as html_err:
        log(f"[WARNING] VLAN HTML report failed: {html_err}")

    write_run_manifest(paths, {
        'action': action,
        'vlan_id': vid,
        'vlan_name': vname,
        'device_count': len(results),
        'dry_run': dry_run,
        'save_config': save_config,
        'html_path': paths.get('html_path'),
    })
    log(f"[Output] VLAN report: {paths['txt_path']}")
    if paths.get('html_path'):
        log(f"[Output] VLAN HTML: {paths['html_path']}")
    
    # Summary
    log(
        f"[SUMMARY] Total: {len(results)}, Changed: {changed}, Skipped: {skip_count}, "
        f"Verify failed: {verify_fail}, Failed: {fail_count}"
    )
    log(f"--- VLAN {action.title()} Complete ---\n")
    
    return results


def run_save_config(devices, user, pwd, enb_pwd, log):
    """Persist active configuration across device list."""
    import modules.save_config

    log("\n--- Saving Device Configuration ---")
    results = []
    success_count = 0
    for dev in devices:
        if _abort_if_cancelled(log):
            break
        host = dev["host"]
        log(f"Saving config on {host}...")
        res = modules.save_config.run(dev, user, pwd, enb_pwd)
        results.append(res)
        if res["status"] == "success":
            success_count += 1
            dtype = (dev.get("device_type") or "").lower()
            if "juniper" in dtype:
                log("  [SUCCESS] Commit complete. Candidate config persisted.")
            else:
                log("  [SUCCESS] Startup-config updated from running-config.")
        else:
            log(f"  [ERROR] {host}: {res.get('error', 'Unknown error')}")

    log(f"--- Save Config Complete ({success_count}/{len(devices)} successful) ---\n")
    return results


def run_interfaces(devices, user, pwd, enb_pwd, filt, log):
    """Interface status & description check across device list."""
    import modules.interfaces
    from utils import report_formatter

    from utils.output_paths import CAT_INTERFACES, path_in_run, prepare_run_output, slugify, write_run_manifest

    log(f"\n--- Checking Interfaces (filter: {filt or 'none'}) ---")
    paths = prepare_run_output(CAT_INTERFACES, slugify(filt or 'all'))
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = path_in_run(paths, 'interfaces_status.txt')
    log(f"[Output] Interfaces report folder: {paths['run_dir']}")
    report_formatter.append_text_file(report_file, f"--- Interface Diagnostics | Date: {ts} ---\n")

    results = []
    success_count = 0

    def _iface_worker(dev, _idx):
        return modules.interfaces.run(dev, user, pwd, enb_pwd, filt, log)

    from utils.parallel_device_pool import foreach_device_parallel
    collected = foreach_device_parallel(
        devices, _iface_worker, log=log, label='interface inventory',
    )
    for res in collected:
        if res is None:
            continue
        results.append(res)
        host = (res.get('device') or res.get('host') or '?')
        if res['status'] == 'success':
            true_host = res['data'].get('true_host', host)
            out = res['data'].get('status_output', '')
            report_formatter.append_text_file(report_file,
                f"\n{'='*40}\nHost: {true_host} ({res.get('device_type', '')})\n{'-'*40}\n{out}")
            log(f"  [SUCCESS] {true_host} gathered.")
            success_count += 1
        else:
            log(f"  [ERROR] {host}: {res.get('error', 'Unknown error')}")
            report_formatter.append_text_file(report_file,
                f"\n{'='*40}\nHost: {host} - FAILED: {res.get('error')}\n")

    write_run_manifest(paths, {'report_path': report_file})
    log(f"\n--- Interfaces Check Complete ({success_count}/{len(devices)} successful). ---")
    log(f"Full output saved to: {report_file}")
    return results, report_file


def run_description_search(devices, user, pwd, enb_pwd, search_term, log, report_txt_path=None, progress_cb=None):
    """Case-insensitive description search across all interfaces on target devices."""
    import re
    import modules.description_search
    from utils import report_formatter

    needle = (search_term or "").strip()
    if not needle:
        log("[ERROR] Description search term is empty.")
        return [], None

    from utils.output_paths import CAT_DESCRIPTION_SEARCH, path_in_run, prepare_run_output, slugify

    log(f"\n--- Description Search (term: '{needle}') ---")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_needle = slugify(needle)[:40]
    paths = None
    if report_txt_path:
        report_file = report_txt_path
        diag_dir = os.path.dirname(report_txt_path)
    else:
        paths = prepare_run_output(CAT_DESCRIPTION_SEARCH, safe_needle)
        report_file = path_in_run(paths, 'report.txt')
        diag_dir = paths['run_dir']
        log(f"[Output] Description search folder: {paths['run_dir']}")
    report_formatter.write_text_file(
        report_file,
        f"--- Interface Description Search ---\n"
        f"Term: {needle} (case-insensitive, any position)\n"
        f"Date: {ts}\n"
        f"{'=' * 60}\n"
    )

    results = []
    total_matches = 0
    total_devs = len(devices)

    def _desc_worker(dev, idx):
        host = dev['host']
        res = modules.description_search.run(
            dev, user, pwd, enb_pwd, needle, log, diag_dir=diag_dir,
        )
        return idx, host, res

    from utils.parallel_device_pool import foreach_device_parallel, get_max_workers
    log(f"[Parallel SSH] Description search: up to {get_max_workers()} concurrent session(s).")
    collected = foreach_device_parallel(
        devices, _desc_worker, log=log, label='description search',
    )

    done = 0
    for item in collected:
        if item is None:
            continue
        idx, host, res = item
        done += 1
        results.append(res)
        if res['status'] == 'success':
            true_host = res['data'].get('true_host', host)
            matches = res['data'].get('matches', [])
            scanned = res['data'].get('total_interfaces_scanned', 0)
            total_matches += len(matches)
            if progress_cb:
                progress_cb(done, total_devs, host, total_matches)
            report_formatter.append_text_file(
                report_file,
                f"\n{'=' * 40}\nHost: {true_host}\n"
                f"Interfaces scanned: {scanned} | Matches: {len(matches)}\n{'-' * 40}\n"
            )
            if matches:
                for m in matches:
                    line = (
                        f"  {m.get('interface', '?'):<16} | "
                        f"{m.get('status', ''):<12} | "
                        f"{m.get('description', '')} "
                        f"[{m.get('source', '')}]"
                    )
                    report_formatter.append_text_file(report_file, line + "\n")
                    log(f"  [MATCH] {true_host} {m.get('interface')}: {m.get('description')}")
            else:
                report_formatter.append_text_file(report_file, "  (no matches)\n")
                log(f"  [OK] {true_host}: no matches ({scanned} interfaces scanned)")
        else:
            err = res.get('error', 'Unknown')
            if progress_cb:
                progress_cb(done, total_devs, host, total_matches)
            log(f"  [ERROR] {host}: {err}")
            report_formatter.append_text_file(
                report_file, f"\n{'=' * 40}\nHost: {host} - FAILED: {err}\n"
            )

    log(f"\n--- Description Search Complete: {total_matches} total match(es) ---")
    log(f"Report saved: {report_file}")

    if paths:
        try:
            from utils.description_search_formatter import write_description_search_html
            device_rows = []
            for res in results:
                if res.get('status') != 'success':
                    continue
                true_host = res.get('data', {}).get('true_host', res.get('device', '?'))
                for m in res.get('data', {}).get('matches', []):
                    device_rows.append({
                        'host': true_host,
                        'interface': m.get('interface', ''),
                        'description': m.get('description', ''),
                        'status': m.get('status', ''),
                        'match_score': m.get('match_score', 0),
                    })
            html_path = path_in_run(paths, 'report.html')
            write_description_search_html(
                html_path, needle, device_rows,
                total_matches=total_matches, devices_scanned=len(devices),
            )
            from utils.output_paths import write_run_manifest
            write_run_manifest(paths, {'html_path': html_path, 'txt_path': report_file})
            log(f"[Output] Description search HTML: {html_path}")
        except Exception as exc:
            log(f"[WARNING] Could not write description search HTML: {exc}")

    return results, report_file


def run_vlan_compare(devices, user, pwd, enb_pwd, log):
    """VLAN compare: finds missing VLANs relative to global union baseline."""
    import modules.vlan_compare
    from utils import report_formatter

    from utils.output_paths import CAT_VLAN_COMPARE, path_in_run, prepare_run_output, write_run_manifest

    log("\n--- Starting VLAN Compare Analysis ---")
    paths = prepare_run_output(CAT_VLAN_COMPARE)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = path_in_run(paths, 'vlan_compare_report.txt')
    log(f"[Output] VLAN compare folder: {paths['run_dir']}")

    device_vlans = {}
    all_vlan_ids = set()
    all_vlan_map = {}
    results = []

    for dev in devices:
        if _abort_if_cancelled(log):
            break
        host = dev['host']
        log(f"Collecting VLANs from {host}...")
        res = modules.vlan_compare.run(dev, user, pwd, enb_pwd, log)
        results.append(res)
        if res['status'] == 'success':
            true_host = res['data'].get('true_host', host)
            parsed = res['data'].get('vlans', [])
            v_ids = set()
            v_map = {}
            for entry in parsed:
                # Handle both (id, name) and (id, name, status) tuples
                vid = entry[0]
                vname = entry[1] if len(entry) > 1 else 'Unknown'
                v_ids.add(vid)
                v_map[vid] = vname
                all_vlan_ids.add(vid)
                if vid not in all_vlan_map:
                    all_vlan_map[vid] = vname
            device_vlans[true_host] = {'vlan_ids': v_ids, 'vlan_map': v_map, 'count': len(v_ids)}
            log(f"  [OK] Found {len(v_ids)} VLANs on {true_host}")
        else:
            log(f"  [ERROR] Failed to fetch from {host}: {res.get('error')}")

    if not device_vlans:
        log("No data collected. Aborting.")
        return results, None

    log(f"\nGlobal Baseline: {len(all_vlan_ids)} unique VLANs across {len(device_vlans)} devices.")

    report_lines = [f"VLAN Comparison Report - {ts}\n{'='*40}\n",
                    f"Total Unique VLANs: {len(all_vlan_ids)} | Devices Scanned: {len(device_vlans)}\n{'='*40}\n\n"]
    issues_found = 0
    for host in sorted(device_vlans.keys()):
        data = device_vlans[host]
        missing = all_vlan_ids - data['vlan_ids']
        report_lines.append(f"Device: {host} (Count: {data['count']})\n{'-'*40}\n")
        if not missing:
            report_lines.append("  [MATCH] Device has all known VLANs.\n")
        else:
            issues_found += len(missing)
            report_lines.append(f"  [MISSING] {len(missing)} VLANs:\n")
            try:
                sorted_missing = sorted(list(missing), key=lambda x: int(x) if str(x).isdigit() else x)
            except Exception:
                sorted_missing = sorted(list(missing))
            for vid in sorted_missing:
                vname = all_vlan_map.get(vid, 'Unknown')
                report_lines.append(f"    - VLAN {vid} ({vname})\n")
        report_lines.append("\n")

    report_formatter.write_text_file(report_file, "".join(report_lines))
    write_run_manifest(paths, {'report_path': report_file, 'discrepancies': issues_found})
    log(f"\nComparison Complete. {issues_found} discrepancies found.")
    log(f"Report saved to: {report_file}")
    return results, report_file


def run_config_backup(devices, user, pwd, enb_pwd, filt, log):
    """Pull running configs and save to timestamped directory."""
    import modules.config_backup
    from utils import report_formatter

    from utils.output_paths import CAT_CONFIG_BACKUP, prepare_run_output, slugify, write_run_manifest

    paths = prepare_run_output(CAT_CONFIG_BACKUP, slugify(filt or 'all'))
    backup_dir = paths['run_dir']
    log(f"\n--- Starting Config Backup into: {backup_dir}/ ---")

    results = []
    file_map = {}
    success_count = 0

    def _backup_worker(dev, _idx):
        return modules.config_backup.run(dev, user, pwd, enb_pwd, filt, log)

    from utils.parallel_device_pool import foreach_device_parallel
    collected = foreach_device_parallel(
        devices, _backup_worker, log=log, label='config backup',
    )
    for res in collected:
        if res is None:
            continue
        results.append(res)
        host = res.get('device') or res.get('host') or '?'
        if res['status'] == 'success':
            config_out = res['data'].get('config', '')
            file_map[f"{host}_config.txt"] = config_out
            log(f"  [SUCCESS] Saved {host} config.")
            success_count += 1
        else:
            log(f"  [ERROR] {host}: {res.get('error', 'Unknown error')}")

    if file_map:
        report_formatter.write_files_in_directory(backup_dir, file_map)
        write_run_manifest(paths, {'backup_dir': backup_dir, 'device_count': success_count})
        # Also register into ConfigBackupSystem so Tools → Compare backups sees them
        # (Oxidized-style catalog under data_root/backups/devices).
        try:
            from utils.config_backup_system import get_backup_system
            from utils.output_paths import get_backups_root
            import os as _os
            bs = get_backup_system()
            # Ensure system points at data-root backups when default relative path was used
            try:
                expected = _os.path.join(get_backups_root(), 'devices')
                if _os.path.abspath(bs.backup_dir) != _os.path.abspath(expected):
                    from utils.config_backup_system import ConfigBackupSystem
                    bs = ConfigBackupSystem(backup_dir=expected)
            except Exception:
                pass
            for res in results:
                if res.get('status') != 'success':
                    continue
                host = res.get('device') or '?'
                true_host = (res.get('data') or {}).get('true_host') or host
                cfg = (res.get('data') or {}).get('config') or ''
                if not cfg:
                    continue
                snap = 'show configuration | display set' if 'juniper' in str(
                    (next((d for d in devices if d.get('host') == host), {}) or {}).get('device_type', '')
                ).lower() else 'show running-config'
                if filt and 'juniper' not in snap:
                    snap = f'{snap} | {filt}'
                reg = bs.create_backup(
                    device=host,
                    hostname=true_host,
                    config_content=cfg,
                    snapshot_command=snap,
                    backup_type='manual',
                    trigger=f'Tools Backup ({filt or "all"})',
                )
                if reg.get('success'):
                    log(f"  [Catalog] Registered {true_host} under backups/devices for compare.")
                else:
                    log(f"  [Catalog] Skip register {true_host}: {reg.get('error') or 'failed'}")
        except Exception as catalog_exc:
            log(f"  [Catalog] Warning: could not register backups for compare: {catalog_exc}")

    log(f"\n--- Config Backup Complete ({success_count}/{len(devices)} successful) ---")
    return results, backup_dir


def run_network_audit(devices, user, pwd, enb_pwd, log):
    """Hardware/OS audit and CSV export."""
    import modules.network_audit
    from utils import report_formatter

    from utils.output_paths import CAT_NETWORK_AUDIT, path_in_run, prepare_run_output, write_run_manifest

    paths = prepare_run_output(CAT_NETWORK_AUDIT)
    csv_file = path_in_run(paths, 'network_audit.csv')
    log(f"\n--- Starting Network Audit -> {csv_file} ---")
    log(f"[Output] Network audit folder: {paths['run_dir']}")

    results = []
    audit_data = []

    def _audit_worker(dev, _idx):
        return modules.network_audit.run(dev, user, pwd, enb_pwd, log)

    from utils.parallel_device_pool import foreach_device_parallel
    collected = foreach_device_parallel(
        devices, _audit_worker, log=log, label='network audit',
    )
    for idx, res in enumerate(collected):
        if res is None:
            continue
        results.append(res)
        dev = devices[idx] if idx < len(devices) else {}
        host = dev.get('host', '?')
        if res['status'] == 'success':
            audit_data.append(res['data']['record'])
            log(f"  [SUCCESS] Audit data extracted for {res['data'].get('true_host', host)}.")
        else:
            log(f"  [ERROR] {host}: {res.get('error', 'Unknown error')}")
            audit_data.append({
                "Hostname": host, "Device Type": dev.get('device_type', 'Unknown'),
                "Model": "ERROR", "OS Version": "ERROR",
                "Serial Number": "ERROR", "Uptime": str(res.get('error', '')).splitlines()[0]
            })

    if audit_data:
        fieldnames = ["Hostname", "Device Type", "Model", "OS Version", "Serial Number", "Uptime"]
        report_formatter.write_csv_file(csv_file, fieldnames, audit_data)
        write_run_manifest(paths, {'csv_path': csv_file, 'devices': len(audit_data)})

    log(f"\n--- Network Audit Complete ---")
    return results, csv_file


def _build_topology_report_header(
    *,
    map_mode,
    devices_requested,
    devices_truncated,
    devices_scanned,
    failed_hosts,
    parallel_workers,
    node_count,
    edge_count,
):
    """Professional L2 map header block embedded in exported HTML (P1)."""
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    mode_label = 'vPC Engineering Board' if map_mode == 'vpc' else 'Standard L2 Map'
    trunc = (
        f"<span style='background:#fef3c7;color:#92400e;padding:4px 10px;border-radius:6px;"
        f"font-size:12px;margin-left:8px;'>⚠ Truncated: {devices_requested} requested → 150 scanned</span>"
        if devices_truncated else ""
    )
    failed = ""
    if failed_hosts:
        failed = (
            f"<span style='background:#fee2e2;color:#991b1b;padding:4px 10px;border-radius:6px;"
            f"font-size:12px;margin-left:8px;'>{len(failed_hosts)} host(s) failed collection</span>"
        )
    return (
        f"<div style='background:linear-gradient(135deg,#1e293b 0%,#0f172a 100%);"
        f"border:1px solid #334155;border-radius:12px;padding:14px 18px;margin:0 0 12px 0;"
        f"font-family:Segoe UI,sans-serif;color:#e2e8f0;font-size:13px;'>"
        f"<div style='display:flex;flex-wrap:wrap;gap:12px;align-items:center;'>"
        f"<strong style='font-size:15px;color:#f8fafc;'>{mode_label}</strong>"
        f"<span>Generated: {ts}</span>"
        f"<span>Devices: {devices_scanned}/{devices_requested or devices_scanned}</span>"
        f"<span>Nodes: {node_count} · Links: {edge_count}</span>"
        f"<span>Parallel SSH: {parallel_workers or 1} workers</span>"
        f"{trunc}{failed}"
        f"</div></div>"
    )


def _detect_device_role(node_name, neighbor_count, int_meta):
    """
    Priority 7: Auto-detect device role based on hostname patterns, neighbor count,
    and interface count. Returns ('core'|'distribution'|'access'|'unknown', color).

    Heuristics (in priority order):
      1. Hostname keyword match  (most reliable)
      2. Neighbor count thresholds
      3. Interface count (high port-count = access layer)
    """
    name_lower = node_name.lower()

    # --- Keyword-based detection ---
    core_keywords = ['core', 'cr', 'bb', 'backbone', 'spine', 'agg', 'aggregation']
    dist_keywords = ['dist', 'distribution', 'dsw', 'dstr', 'leaf', 'border', 'wan']
    access_keywords = ['acc', 'access', 'asw', 'floor', 'closet', 'edge', 'iot', 'dmz']

    for kw in core_keywords:
        if kw in name_lower:
            return 'core', '#c0392b'          # Red — core is critical
    for kw in dist_keywords:
        if kw in name_lower:
            return 'distribution', '#e67e22'  # Orange — distribution
    for kw in access_keywords:
        if kw in name_lower:
            return 'access', '#2980b9'        # Blue — access

    # --- Neighbor-count heuristic ---
    if neighbor_count >= 4:
        return 'core', '#c0392b'
    elif neighbor_count >= 2:
        return 'distribution', '#e67e22'
    elif neighbor_count == 1:
        return 'access', '#2980b9'

    # --- Interface count heuristic (many ports = access switch) ---
    total_ints = len(int_meta) if int_meta else 0
    if total_ints >= 48:
        return 'access', '#2980b9'
    elif total_ints >= 24:
        return 'distribution', '#e67e22'

    return 'unknown', '#607d8b'              # Grey — undetermined


def _node_has_vpc_data(meta):
    """True when switch metadata contains vPC domain, table, or port-channel vPC entries."""
    if not meta:
        return False
    vs = meta.get('vpc_structured') or {}
    if isinstance(vs, dict) and (vs.get('domain_id') or vs.get('vpc_table')):
        return True
    vd = meta.get('vpc_details') or {}
    for key, det in vd.items():
        if str(key).startswith('_'):
            continue
        if isinstance(det, dict) and det.get('type') in ('vpc', 'peer-link'):
            return True
    return bool(meta.get('vpcs'))


def _apply_cable_optics_issues(final_edges, node_metadata, log, diag_folder=None):
    """Stamp description/speed/duplex/DOM witnesses. Does not invent edges."""
    from utils.cable_witness import apply_cable_witnesses
    from utils.optics_dom import apply_optics_to_edges
    from utils.link_issues import build_link_issues

    apply_cable_witnesses(final_edges)
    optics_by_host = {
        host: (meta or {}).get('optics') or {}
        for host, meta in (node_metadata or {}).items()
    }
    apply_optics_to_edges(final_edges, optics_by_host)
    issues = build_link_issues(final_edges)
    if diag_folder:
        try:
            path = os.path.join(diag_folder, 'link_issues.json')
            with open(path, 'w', encoding='utf-8') as fh:
                json.dump({
                    'note': 'Witnesses from last inventory L2 map. Not a certified cable.',
                    'issues': issues,
                }, fh, indent=2, default=str)
        except OSError:
            pass
    if log:
        log(f"[MAP-PIPELINE] Cable witnesses + DOM: {len(issues)} issue row(s)")
    return issues


def _resync_vpc_domain_metadata(node_metadata, log):
    """Resync vpc_domain_id and vpc_details from vpc_structured after SSH collection."""
    from utils.nxos_vpc_parse import vpc_details_from_structured

    for host, meta in node_metadata.items():
        vs = meta.get('vpc_structured') or {}
        if not isinstance(vs, dict):
            continue

        did = str(meta.get('vpc_domain_id') or '').strip()
        vs_did = str(vs.get('domain_id') or '').strip()
        if vs_did and did != vs_did:
            meta['vpc_domain_id'] = vs_did
            log(f"[MAP-PIPELINE] Resync: {host} vpc_domain_id={vs_did}")

        vd = meta.get('vpc_details') or {}
        has_vpc_rows = any(
            isinstance(d, dict) and d.get('type') == 'vpc'
            for k, d in vd.items() if not str(k).startswith('_')
        )
        if not has_vpc_rows and vs.get('vpc_table'):
            _, rebuilt = vpc_details_from_structured(vs)
            for k, v in rebuilt.items():
                vd.setdefault(k, v)
            meta['vpc_details'] = vd
            meta['vpcs'] = [
                k for k, d in vd.items()
                if isinstance(d, dict) and d.get('type') == 'vpc'
            ]
            log(f"[MAP-PIPELINE] Resync: {host} rebuilt vpc_details ({len(vs['vpc_table'])} rows)")

        if meta.get('port_channel_detail') and not meta.get('port_channels'):
            meta['port_channels'] = meta['port_channel_detail']


def _infer_vpc_peers_from_cdp(domain_to_nodes, node_metadata, edges, log):
    """Infer unscanned vPC peer from CDP when only one domain member was collected."""
    for did, members in list(domain_to_nodes.items()):
        uniq = sorted(set(members))
        if len(uniq) != 1:
            continue
        scanned = uniq[0]
        if not _node_has_vpc_data(node_metadata.get(scanned, {})):
            continue
        neighbors = set()
        for e in edges:
            if e.get('from') == scanned:
                neighbors.add(e.get('to'))
            elif e.get('to') == scanned:
                neighbors.add(e.get('from'))
        for peer in sorted(n for n in neighbors if n):
            if peer == scanned or peer in uniq:
                continue
            domain_to_nodes.setdefault(did, []).append(peer)
            log(f"[MAP-PIPELINE] Inferred vPC peer {peer} for domain {did} (CDP adjacency)")
            break


def _finalize_standard_map_edges(final_edges, node_metadata, norm_int_fn, log):
    """Upgrade and synthesize vPC peer-link edges for Standard L2 Map (map_mode=all)."""
    if not final_edges:
        return final_edges

    def _port_in_vpc_details(meta, port):
        if not meta or not port:
            return None
        vd = meta.get('vpc_details') or {}
        for key, det in vd.items():
            if norm_int_fn(str(key)) == norm_int_fn(str(port)) and isinstance(det, dict):
                if det.get('type') == 'peer-link':
                    return key
        return None

    def _peer_link_port_from_meta(meta):
        vs = meta.get('vpc_structured') or {}
        pl = (vs.get('peer_link_po') or '').strip()
        if pl:
            return pl
        for po, det in (meta.get('vpc_details') or {}).items():
            if isinstance(det, dict) and det.get('type') == 'peer-link':
                return po
        return ''

    def _find_edge_between(m1, m2):
        for e in final_edges:
            if set([e['from'], e['to']]) == set([m1, m2]):
                return e
        return None

    for e in final_edges:
        f_meta = node_metadata.get(e['from'], {})
        t_meta = node_metadata.get(e['to'], {})
        if f_meta.get('vpc_domain_id') and f_meta.get('vpc_domain_id') == t_meta.get('vpc_domain_id'):
            if _port_in_vpc_details(f_meta, e.get('f_port')) or _port_in_vpc_details(t_meta, e.get('t_port')):
                e['type'] = 'vpc-peer-link'
                e['is_vpc_peer_link'] = True
                if not e.get('label'):
                    e['label'] = 'Peer-Link'

    domain_members = {}
    for node_name, meta in node_metadata.items():
        did = str(meta.get('vpc_domain_id') or '').strip()
        if did:
            domain_members.setdefault(did, set()).add(node_name)

    existing_peer_pairs = set()
    for e in final_edges:
        if e.get('type') == 'vpc-peer-link' or e.get('is_vpc_peer_link'):
            existing_peer_pairs.add(tuple(sorted([e['from'], e['to']])))

    for did, members in domain_members.items():
        mlist = sorted(members)
        if len(mlist) < 2:
            continue
        for i in range(len(mlist)):
            for j in range(i + 1, len(mlist)):
                m1, m2 = mlist[i], mlist[j]
                pair = tuple(sorted([m1, m2]))
                if pair in existing_peer_pairs:
                    continue
                meta1 = node_metadata.get(m1, {})
                meta2 = node_metadata.get(m2, {})
                pl_po = _peer_link_port_from_meta(meta1) or _peer_link_port_from_meta(meta2)
                existing = _find_edge_between(m1, m2)
                if existing:
                    if existing.get('type') != 'vpc-peer-link':
                        upgrade = bool(pl_po) or bool(
                            _port_in_vpc_details(meta1, existing.get('f_port'))
                            or _port_in_vpc_details(meta2, existing.get('t_port'))
                        )
                        if upgrade or len(mlist) == 2:
                            existing['type'] = 'vpc-peer-link'
                            existing['is_vpc_peer_link'] = True
                            if pl_po:
                                existing['f_port'] = pl_po
                                existing['t_port'] = pl_po
                            if not existing.get('label'):
                                existing['label'] = 'Peer-Link'
                            log(f"[MAP] Upgraded peer-link: {m1} <-> {m2} (domain {did})")
                    existing_peer_pairs.add(pair)
                    continue
                if not pl_po and len(mlist) != 2:
                    continue
                pl_po = pl_po or 'Peer-Link'
                final_edges.append({
                    'from': m1, 'to': m2,
                    'f_port': pl_po, 't_port': pl_po,
                    'type': 'vpc-peer-link',
                    'label': 'Peer-Link',
                    'is_vpc_peer_link': True,
                    'is_vpc_member': False,
                    'vpc_domain_id': did,
                    'confidence': 'High',
                    'f_int_data': {
                        'status': 'up', 'desc': 'vPC Peer-Link',
                        'vlan': '', 'speed': '', 'duplex': '', 'macs': [],
                    },
                    't_int_data': {'status': 'up', 'desc': 'vPC Peer-Link', 'vlan': '', 'speed': ''},
                    'peer_info': {},
                    'bundled_links': [],
                })
                existing_peer_pairs.add(pair)
                log(f"[MAP] Synthesized peer-link: {m1} <-> {m2} (domain {did})")
    return final_edges


def _topology_edge_link_key(f_safe, f_port, t_safe, t_port, norm_int_fn):
    """Port-aware dedup key — keeps parallel links when endpoint ports differ."""

    def _port_label(port):
        raw = str(port or '').strip()
        if not raw or raw.lower() in ('unknown', 'null', 'none', 'n/a', '-'):
            return raw.lower() or 'n/a'
        return norm_int_fn(raw)

    fp = _port_label(f_port)
    tp = _port_label(t_port)
    return tuple(sorted([f"{f_safe}:{fp}", f"{t_safe}:{tp}"]))


def run_topology_mapper(devices, user, pwd, enb_pwd, log, map_mode='all'):
    """CDP/LLDP topology collection and HTML Vis.js diagram generation.

    v6.2.0 Enhancements:
      - Priority 2: Enriched edge tooltips (platform, IOS version, mgmt IP)
      - Priority 5: True multi-device merge — unified graph from all scanned devices
      - Priority 3 (v6.1.1): Port Status Badges on nodes
      - Priority 7 (v6.1.1): Device Role & Grouping + hierarchical layout
      - Priority 10 (v6.1.1): Search & Path Highlighting

    Args:
        map_mode: 'all' for full topology, 'vpc' for vPC-focused view
    """
    import modules.topology_mapper
    from modules.network_base import safe_node_name
    from utils import report_formatter
    import re

    def norm_int(n):
        return (n.replace("Ethernet", "Eth").replace("GigabitEthernet", "Gi")
                 .replace("FastEthernet", "Fa").replace("TenGigabitEthernet", "Te")
                 .replace("HundredGigE", "Hu").replace("FortyGigabitEthernet", "Fo")
                 .replace("TwentyFiveGigE", "Twe")
                 .replace("Port-channel", "Po").replace("port-channel", "Po").strip())

    from utils.output_paths import CAT_TOPOLOGY_MAPPER, path_in_run, prepare_run_output, slugify, write_run_manifest

    paths = prepare_run_output(CAT_TOPOLOGY_MAPPER, slugify(map_mode))
    diag_folder = paths['run_dir']
    html_file = path_in_run(paths, f'topology_map_{map_mode}.html')
    log(f"\n--- Topology Mapper Generating {map_mode.upper()} L2 map (hierarchical layout)... ---")
    log(f"[MAP-PIPELINE] Diagnostic output folder: {diag_folder}")
    log("[MAP-PIPELINE] v6.8.1 Starting 5-Phase Validation Pipeline")
    log("[MAP-PIPELINE] Phase 1: Device Collection - Starting...")
    log(f"[MAP-PIPELINE] Phase 1: Input devices: {len(devices)}, Mode: {map_mode}")

    edges = []
    uniq_nodes = set()
    node_metadata = {}
    results = []
    vpc_adjacency_fallback = False
    vpc_no_domain_banner = ""
    vpc_info_all = {}  # Collect vPC info from all devices
    # Priority 5: peer info registry — keyed by node name
    # Populated from CDP/LLDP detail data of ALL scanned devices
    peer_info_registry = {}  # {node_name: {platform, version, mgmt_ip, caps}}

    devices_requested = len(devices)
    devices_truncated = False
    devices_skipped_hosts = []
    if len(devices) > 150:
        devices_skipped_hosts = [
            str(d.get('host', d.get('ip', '?'))) for d in devices[150:]
        ]
        log(f"\n[WARNING] Topology mapper limited to 150 devices to prevent browser crash.")
        log(f"[WARNING] Truncating input from {len(devices)} down to 150 devices.")
        if devices_skipped_hosts:
            preview = ', '.join(devices_skipped_hosts[:8])
            suffix = f' (+{len(devices_skipped_hosts) - 8} more)' if len(devices_skipped_hosts) > 8 else ''
            log(f"[WARNING] Skipped hosts (not scanned): {preview}{suffix}")
        devices_truncated = True
        devices = devices[:150]

    from utils.parallel_device_pool import foreach_device_parallel, get_max_workers
    parallel_workers = get_max_workers()
    failed_hosts = []

    def _collect_topology(dev, _idx):
        host = dev['host']
        return host, modules.topology_mapper.run(dev, user, pwd, enb_pwd, log)

    collected = foreach_device_parallel(
        devices, _collect_topology, log=log, max_workers=parallel_workers,
        label='topology CDP/LLDP collection',
    )

    for item in collected:
        if item is None:
            continue
        host, res = item
        results.append(res)
        if res['status'] == 'success':
            true_host = res['data']['true_host']
            uniq_nodes.add(true_host)
            node_metadata[true_host] = {
                "interfaces": res['data'].get('int_meta', {}),
                "bundles": res['data'].get('bundles', {}),
                "vpcs": res['data'].get('vpcs', []),
                "vpc_domain_id": res['data'].get('vpc_domain_id', ''),
                "vpc_details": res['data'].get('vpc_details', {}),
                "interface_macs": res['data'].get('interface_macs', {}),
                # v6.9.0: Structured enrichment fields
                "port_channel_detail": res['data'].get('port_channel_detail', {}),
                "port_channels": res['data'].get('port_channels', {})
                    or res['data'].get('port_channel_detail', {}),
                "vpc_structured": res['data'].get('vpc_structured', {}),
                "lacp_neighbors": res['data'].get('lacp_neighbors', {}),
                "cdp_validation_map": res['data'].get('cdp_validation_map', {}),
                "nxos_version": res['data'].get('nxos_version', ''),
                "optics": res['data'].get('optics') or {},
                "interface_trust_chains": [],
                "trust_alerts": [],
            }
            # Collect vPC info
            if res['data'].get('vpc_details'):
                vpc_info_all[true_host] = res['data']['vpc_details']

            # Priority 5 + 2: Collect peer info from enriched edges
            for e in res['data'].get('edges', []):
                peer_name = safe_node_name(e.get('to', ''))
                if peer_name and (
                    e.get('peer_platform') or e.get('peer_version') or e.get('peer_mgmt_ip')
                ):
                    # Merge — don't overwrite richer data with empty
                    existing = peer_info_registry.get(peer_name, {})
                    peer_info_registry[peer_name] = {
                        "platform": e.get('peer_platform') or existing.get('platform', ''),
                        "version":  e.get('peer_version')  or existing.get('version', ''),
                        "mgmt_ip":  e.get('peer_mgmt_ip')  or existing.get('mgmt_ip', ''),
                        "caps":     e.get('peer_caps')      or existing.get('caps', ''),
                    }

            edges.extend(res['data'].get('edges', []))
            log(f"  [SUCCESS] Topology data extracted for {true_host}.")
        else:
            failed_hosts.append(host)
            log(f"  [ERROR] {host}: {res.get('error', 'Unknown error')}")

    # v6.5.0: Add topology summary banner
    success_count = sum(1 for r in results if r['status'] == 'success')
    failure_count = len(results) - success_count
    
    # Phase 1 Validation
    log(f"[MAP-PIPELINE] Phase 1 complete: {len(node_metadata)} devices with valid data")
    if not node_metadata:
        log("[MAP-PIPELINE] ERROR Phase 1: No devices with valid data collected - aborting")
        log("[TOPOLOGY_READY] status=error error=No devices returned topology data")
        return results, None
    
    if failure_count > 0:
        log(f"\n{'='*60}")
        log(f"⚠️  TOPOLOGY PARTIAL: {success_count} succeeded, {failure_count} failed")
        log(f"{'='*60}")
        for r in results:
            if r['status'] != 'success':
                log(f"   ❌ {r.get('host', 'unknown')}: {r.get('error', 'Unknown error')}")
        log(f"{'='*60}\n")
    else:
        log(f"\n✅ Topology complete: All {success_count} devices successful\n")

    _resync_vpc_domain_metadata(node_metadata, log)

    # v7.0.1: Normalize neighbor endpoint names before dedup (Discovery graph parity)
    try:
        from utils.discovery_graph import canonicalize_topology_edge_list
        edges = canonicalize_topology_edge_list(edges)
    except Exception:
        pass

    from utils.topology_trust import apply_topology_trust, validate_vpc_domain_completeness
    trust_summary = apply_topology_trust(edges, node_metadata, norm_int, safe_node_name, log)

    # --- Priority 7: Pre-compute neighbor counts for role detection ---
    node_neighbor_count = {}
    for e in edges:
        f_safe = safe_node_name(e['from'])
        t_safe = safe_node_name(e['to'])
        if f_safe:
            node_neighbor_count[f_safe] = node_neighbor_count.get(f_safe, 0) + 1
        if t_safe:
            node_neighbor_count[t_safe] = node_neighbor_count.get(t_safe, 0) + 1

    # Phase 4 Implementations:
    # 1. Mutual Visibility (Unidirectional Link Detection)
    # Track all reported links as (from, to, f_port, t_port)
    reported_directed_links = set()
    for e in edges:
        f_safe = safe_node_name(e['from'])
        t_safe = safe_node_name(e['to'])
        if f_safe and t_safe:
            reported_directed_links.add((f_safe, norm_int(e['f_port']), t_safe, norm_int(e['t_port'])))

    # v6.5.0: Metadata-merging edge deduplication
    final_edges = []
    edge_registry = {}  # key -> edge_data with merged metadata
    node_connections = {}
    node_port_stats = {}  # {node: {"up": N, "down": N, "err": N, "total": N}}
    
    # Bundle tracking: dict of bundle_key -> list of physical edges
    bundles_map = {}

    for e in edges:
        f_node, f_port = e['from'], e['f_port']
        t_node, t_port = e['to'], e['t_port']
        f_safe = safe_node_name(f_node)
        t_safe = safe_node_name(t_node)
        if not f_safe or not t_safe:
            continue
            
        uniq_nodes.add(f_safe)
        uniq_nodes.add(t_safe)
        
        link_key = _topology_edge_link_key(f_safe, f_port, t_safe, t_port, norm_int)
        
        # v6.5.0: Merge metadata instead of dropping duplicates
        if link_key in edge_registry:
            existing = edge_registry[link_key]
            # Merge: keep non-empty values, prefer richer data
            existing['peer_platform'] = e.get('peer_platform') or existing.get('peer_platform', '')
            existing['peer_version'] = e.get('peer_version') or existing.get('peer_version', '')
            existing['peer_mgmt_ip'] = e.get('peer_mgmt_ip') or existing.get('peer_mgmt_ip', '')
            existing['peer_caps'] = e.get('peer_caps') or existing.get('peer_caps', '')
            # If new data has longer platform string, it's likely richer
            if e.get('peer_platform') and len(e.get('peer_platform', '')) > len(existing.get('peer_platform', '')):
                existing['peer_platform'] = e['peer_platform']
            continue
        
        # First occurrence - store in registry and use as source for edge_data
        # This ensures merged metadata from duplicates is preserved
        edge_registry[link_key] = e.copy()
        source_edge = edge_registry[link_key]  # Use registry entry so duplicates can enrich it

        is_overlay = (
            bool(e.get('not_physical'))
            or str(e.get('layer') or '').lower() == 'overlay'
            or str(e.get('edge_kind') or '') == 'nve-peer'
        )
        if is_overlay:
            final_edges.append({
                "from": f_safe, "to": t_safe, "f_port": f_port, "t_port": t_port,
                "type": "overlay", "label": e.get('label') or 'EVPN',
                "is_vpc_member": False,
                "is_vpc_peer_link": False,
                "vpc_domain_id": "",
                "confidence": e.get('confidence') or 'Overlay',
                "trust_score": e.get('trust_score', 50),
                "trust_tier": e.get('trust_tier') or 'overlay',
                "bidirectional": False,
                "discovery": e.get('discovery') or 'nve',
                "layer": "overlay",
                "edge_kind": e.get('edge_kind') or 'nve-peer',
                "not_physical": True,
                "f_int_data": {"status": "nve", "desc": "overlay", "speed": "", "vlan": "", "macs": []},
                "t_int_data": {"status": "nve", "desc": "overlay", "speed": "", "vlan": "", "macs": []},
                "peer_info": {},
            })
            continue

        f_meta = node_metadata.get(f_safe, {})
        t_meta = node_metadata.get(t_safe, {})
        f_bundle = f_meta.get("bundles", {}).get(norm_int(f_port)) or f_meta.get("bundles", {}).get(f_port)
        vpc_details = f_meta.get("vpc_details", {})

        e_type = "standard"
        bundle_label = ""
        is_vpc_peer_link = False
        is_vpc_member = False

        if f_bundle:
            e_type = "port-channel"
            bundle_label = f_bundle
            if f_bundle in f_meta.get("vpcs", []):
                e_type = "vpc"
                is_vpc_member = True
            
            # Defensive check for vpc_details entries
            f_port_norm = norm_int(f_port)
            v_det = vpc_details.get(f_port_norm) or vpc_details.get(f_port)
            if isinstance(v_det, dict) and v_det.get("type") == "peer-link":
                is_vpc_peer_link = True
                e_type = "vpc-peer-link"

        is_asymmetric = False
        if f_safe in uniq_nodes and t_safe in uniq_nodes:
            expected_return = (t_safe, norm_int(t_port), f_safe, norm_int(f_port))
            if expected_return not in reported_directed_links:
                is_asymmetric = True
                
        if is_asymmetric:
            e_type = "asymmetric"
            bundle_label = ""
            
        f_int_data = f_meta.get("interfaces", {}).get(
            norm_int(f_port),
            f_meta.get("interfaces", {}).get(f_port, {"status": "unknown", "desc": "-", "speed": "", "vlan": "", "macs": []})
        )
        t_int_data = t_meta.get("interfaces", {}).get(
            norm_int(t_port),
            t_meta.get("interfaces", {}).get(t_port, {"status": "unknown", "desc": "-", "speed": "", "vlan": "", "macs": []})
        )
        
        port_status = f_int_data.get('status', 'unknown')

        if f_safe not in node_port_stats:
            node_port_stats[f_safe] = {"up": 0, "down": 0, "err": 0, "total": 0}
        node_port_stats[f_safe]["total"] += 1
        if port_status == 'up':
            node_port_stats[f_safe]["up"] += 1
        elif port_status == 'err-disabled':
            node_port_stats[f_safe]["err"] += 1
        else:
            node_port_stats[f_safe]["down"] += 1

        peer_info = peer_info_registry.get(t_safe, {})
        # Use source_edge (from registry) to get merged metadata from duplicates
        peer_platform = source_edge.get('peer_platform', '') or peer_info.get('platform', '')
        peer_version  = source_edge.get('peer_version', '')  or peer_info.get('version', '')
        peer_mgmt_ip  = source_edge.get('peer_mgmt_ip', '')  or peer_info.get('mgmt_ip', '')
        peer_caps     = source_edge.get('peer_caps', '')      or peer_info.get('caps', '')

        confidence = e.get('confidence') or ("Medium" if is_asymmetric else "High")
        trust_score = e.get('trust_score', 70 if not is_asymmetric else 55)
        trust_tier = e.get('trust_tier', 'high' if not is_asymmetric else 'medium')
        bidirectional = e.get('bidirectional', not is_asymmetric)

        if 'trust_score' not in e:
            # Legacy path when trust pass skipped this edge
            if not is_asymmetric and f_int_data.get('status') == 'up' and t_int_data.get('status') in ['down', 'err-disabled']:
                confidence = "Mismatch"
            elif not is_asymmetric and t_int_data.get('status') == 'up' and f_int_data.get('status') in ['down', 'err-disabled']:
                confidence = "Mismatch"

        edge_data = {
            "from": f_safe, "to": t_safe, "f_port": f_port, "t_port": t_port,
            "type": e_type, "label": bundle_label,
            "is_vpc_member": is_vpc_member,
            "is_vpc_peer_link": is_vpc_peer_link,
            "vpc_domain_id": f_meta.get("vpc_domain_id", ""),
            "confidence": confidence,
            "trust_score": trust_score,
            "trust_tier": trust_tier,
            "bidirectional": bidirectional,
            "discovery": e.get('discovery', 'cdp'),
            "f_int_data": f_int_data,
            "t_int_data": t_int_data,
            "peer_info": {
                "platform": peer_platform,
                "version": peer_version,
                "mgmt_ip": peer_mgmt_ip,
                "caps": peer_caps
            }
        }
        
        if bundle_label:
            b_key = tuple(sorted([f_safe, t_safe, bundle_label]))
            if b_key not in bundles_map:
                bundles_map[b_key] = []
            bundles_map[b_key].append(edge_data)
        else:
            final_edges.append(edge_data)
            
        if f_safe not in node_connections:
            node_connections[f_safe] = []
        node_connections[f_safe].append(t_safe)  # Track connection TO neighbor

    for b_key, b_edges in bundles_map.items():
        if len(b_edges) == 1:
            final_edges.append(b_edges[0])
        else:
            base = b_edges[0]
            f_s, t_s = base['from'], base['to'] 
            
            final_edges.append({
                "from": f_s, "to": t_s, 
                "f_port": f"Bundle ({len(b_edges)})", 
                "t_port": base['label'],
                "type": base['type'], "label": f"{base['label']} ({len(b_edges)}x)",
                "is_vpc_member": base['is_vpc_member'],
                "is_vpc_peer_link": base['is_vpc_peer_link'],
                "vpc_domain_id": base.get('vpc_domain_id', ''),
                "confidence": base['confidence'],
                "trust_score": base.get('trust_score', 70),
                "trust_tier": base.get('trust_tier', 'high'),
                "bidirectional": base.get('bidirectional', True),
                "discovery": base.get('discovery', 'cdp'),
                "f_int_data": base['f_int_data'],
                "t_int_data": base['t_int_data'],
                "peer_info": base['peer_info'],
                "bundled_links": b_edges
            })

    # Phase 2 Validation
    log(f"[MAP-PIPELINE] Phase 2 complete: {len(final_edges)} edges after processing")
    if map_mode == 'all':
        final_edges = _finalize_standard_map_edges(final_edges, node_metadata, norm_int, log)
        log(f"[MAP-PIPELINE] Phase 2b: {len(final_edges)} edges after peer-link finalize")
    if not final_edges:
        log("[MAP-PIPELINE] WARNING Phase 2: No edges detected - devices may be standalone")

    # v6.6.0: VPC Visualization Rewrite
    # If in VPC mode, cluster VPC pairs into a single domain node and consolidate shared downstream edges.
    if map_mode == 'vpc':
        log("[MAP-PIPELINE] Phase 3: VPC Transformation - Starting...")
        domain_to_nodes = {}
        for node_name, meta in node_metadata.items():
            did = str(meta.get("vpc_domain_id", "")).strip()
            if did:
                domain_to_nodes.setdefault(did, []).append(node_name)
            elif _node_has_vpc_data(meta):
                vs = meta.get('vpc_structured') or {}
                fallback_did = str(vs.get('domain_id', '')).strip() if isinstance(vs, dict) else ''
                if fallback_did:
                    domain_to_nodes.setdefault(fallback_did, []).append(node_name)
                    meta['vpc_domain_id'] = fallback_did

        _infer_vpc_peers_from_cdp(domain_to_nodes, node_metadata, edges, log)

        vpc_domains = {}
        for did, members in domain_to_nodes.items():
            uniq = sorted(set(members))
            if len(uniq) >= 2:
                vpc_domains[did] = uniq
            elif len(uniq) == 1 and _node_has_vpc_data(node_metadata.get(uniq[0], {})):
                vpc_domains[did] = uniq

        domain_completeness = validate_vpc_domain_completeness(vpc_domains, node_metadata)
        for did, dc in domain_completeness.items():
            if dc.get('unscanned_members'):
                log(f"[TRUST] Domain {did}: unscanned peer(s) {dc['unscanned_members']}")
        
        # Phase 3 Validation - Domain Detection
        log(f"[MAP-PIPELINE] Phase 3: Detected {len(vpc_domains)} vPC domain(s)")
        log(f"[MAP-PIPELINE] Phase 3 DEBUG: map_mode = {map_mode}")
        log(f"[MAP-PIPELINE] Phase 3 DEBUG: node_metadata count = {len(node_metadata)}")
        log(f"[MAP-PIPELINE] Phase 3 DEBUG: vpc_domain_id values = {[meta.get('vpc_domain_id') for meta in node_metadata.values()]}")
        for did, members in vpc_domains.items():
            log(f"[MAP-PIPELINE] Phase 3:   Domain {did}: members={members}")
        
        if vpc_domains:
            log(f"  > [VPC] Transforming topology for {len(vpc_domains)} vPC Domain(s)...")
            log(f"[MAP-PIPELINE] Phase 3: vpc_domains = {vpc_domains}")
            log(f"[MAP-PIPELINE] Phase 3: Starting edge count = {len(final_edges)}")
            transformed_edges = []
            
            # Map of old node names to their new VPC node representation
            node_to_vpc = {}
            for did, members in vpc_domains.items():
                vpc_node_name = f"VPC_Domain_{did}"
                uniq_nodes.add(vpc_node_name)
                for m in members:
                    # v6.9.3: Keep physical switches in uniq_nodes for Hybrid Observability
                    # (Switch A and Switch B remain visible connected to the virtual Domain Anchor)
                    node_to_vpc[m] = vpc_node_name

            # 1. Add direct Logical Association edges connecting physical switches to their logical VPC Domain Anchor
            for did, members in vpc_domains.items():
                vpc_node_name = f"VPC_Domain_{did}"
                for m in members:
                    transformed_edges.append({
                        "from": vpc_node_name,
                        "to": m,
                        "f_port": "Logical Domain",
                        "t_port": "Physical Node",
                        "type": "vpc-domain-peer",
                        "label": "Logical Association",
                        "is_vpc_member": False,
                        "is_vpc_peer_link": False,
                        "vpc_domain_id": did,
                        "confidence": "High",
                        "f_int_data": {"status": "up", "desc": "Virtual association to logical domain"},
                        "t_int_data": {"status": "up", "desc": "Virtual association to logical domain"},
                        "peer_info": {"platform": "vPC Domain Node", "version": "", "mgmt_ip": "", "caps": "Internal"},
                        "bundled_links": []
                    })
                    
            # Transform edges
            # Group shared edges by (from_vpc, to_device) or (from_device, to_vpc)
            downstream_links_map = {}
            for e in final_edges:
                f_node = e['from']
                t_node = e['to']
                
                f_is_vpc = f_node in node_to_vpc
                t_is_vpc = t_node in node_to_vpc
                
                # Keep internal vPC peer links (between members of the same domain) to represent the physical peer link!
                if f_is_vpc and t_is_vpc and node_to_vpc[f_node] == node_to_vpc[t_node]:
                    e['type'] = 'vpc-peer-link'
                    transformed_edges.append(e)
                    continue
                    
                # Calculate the new from/to
                new_f = node_to_vpc.get(f_node, f_node)
                new_t = node_to_vpc.get(t_node, t_node)
                
                # If this link connects to a VPC domain, we track it to see if it's shared
                if f_is_vpc or t_is_vpc:
                    # To group them, we always sort the connection pair so it's consistent
                    pair_key = tuple(sorted([new_f, new_t]))
                    if pair_key not in downstream_links_map:
                        downstream_links_map[pair_key] = []
                    downstream_links_map[pair_key].append((e, f_node, t_node))
                else:
                    transformed_edges.append(e)
                    
            # Evaluate shared links
            for pair_key, link_entries in downstream_links_map.items():
                node_a, node_b = pair_key
                is_a_vpc = node_a.startswith("VPC_Domain_")
                vpc_node = node_a if is_a_vpc else node_b
                downstream_node = node_b if is_a_vpc else node_a
                
                # Determine which actual vpc members are connected
                connected_vpc_members = set()
                active_links = 0
                total_links = 0
                
                for e, orig_f, orig_t in link_entries:
                    if orig_f in node_to_vpc and node_to_vpc[orig_f] == vpc_node:
                        connected_vpc_members.add(orig_f)
                    if orig_t in node_to_vpc and node_to_vpc[orig_t] == vpc_node:
                        connected_vpc_members.add(orig_t)
                    
                    # Calculate health for the bundled edge
                    underlying = e.get('bundled_links', [e])
                    for l in underlying:
                        total_links += 1
                        # Check status from both ends if available
                        f_stat = l.get('f_int_data', {}).get('status', 'down')
                        if f_stat == 'up':
                            active_links += 1
                        
                # Identify if shared (connects to 2 or more members of the VPC)
                is_shared = len(connected_vpc_members) >= 2
                link_state = 'active' if active_links == total_links and total_links > 0 else 'partial' if active_links > 0 else 'down'
                
                # Attempt to extract the vPC ID for a better label
                detected_vpc_id = None
                for e, orig_f, orig_t in link_entries:
                    # Check source side
                    meta_f = node_metadata.get(orig_f, {})
                    vdet_f = meta_f.get("vpc_details", {})
                    f_p = norm_int(e.get("f_port", ""))
                    if f_p in vdet_f and isinstance(vdet_f[f_p], dict) and vdet_f[f_p].get("vpc_id"):
                        detected_vpc_id = vdet_f[f_p].get("vpc_id")
                        break
                    
                    # Check destination side
                    meta_t = node_metadata.get(orig_t, {})
                    vdet_t = meta_t.get("vpc_details", {})
                    t_p = norm_int(e.get("t_port", ""))
                    if t_p in vdet_t and isinstance(vdet_t[t_p], dict) and vdet_t[t_p].get("vpc_id"):
                        detected_vpc_id = vdet_t[t_p].get("vpc_id")
                        break
                    
                # Consolidate into a single edge
                base_e = link_entries[0][0].copy()
                base_e['from'] = node_a
                base_e['to'] = node_b
                base_e['link_state'] = link_state
                base_e['active_links'] = active_links
                base_e['total_links'] = total_links
                
                if is_shared:
                    base_e['type'] = 'vpc_shared'
                    vpc_label_prefix = f"vPC {detected_vpc_id}" if detected_vpc_id else "vPC"
                    base_e['label'] = f"{vpc_label_prefix} ({active_links}/{total_links} Active)"
                else:
                    base_e['type'] = 'vpc_orphan'
                    base_e['label'] = f"Orphan ({active_links}/{total_links} Active)"
                
                # Compile underlying links into the bundle for tooltip
                bundled = []
                for e, _, _ in link_entries:
                    bundled.extend(e.get('bundled_links', [e]))
                base_e['bundled_links'] = bundled
                
                transformed_edges.append(base_e)

            # Ensure direct peer-links exist if exactly 2 peer switches exist in a domain
            for did, members in vpc_domains.items():
                if len(members) == 2:
                    m1, m2 = members[0], members[1]
                    has_peer_link = False
                    for te in transformed_edges:
                        if te.get('type') == 'vpc-peer-link' and {te['from'], te['to']} == {m1, m2}:
                            has_peer_link = True
                            break
                    if not has_peer_link:
                        transformed_edges.append({
                            "from": m1,
                            "to": m2,
                            "f_port": "Peer-Link",
                            "t_port": "Peer-Link",
                            "type": "vpc-peer-link",
                            "label": "vPC Peer-Link",
                            "is_vpc_member": False,
                            "is_vpc_peer_link": True,
                            "vpc_domain_id": did,
                            "confidence": "Inferred",
                            "f_int_data": {"status": "up", "desc": "Inferred vPC Peer Link"},
                            "t_int_data": {"status": "up", "desc": "Inferred vPC Peer Link"},
                            "peer_info": {"platform": "vPC Peer", "version": "", "mgmt_ip": "", "caps": "Peer-Link"},
                            "bundled_links": []
                        })
                
            final_edges = transformed_edges
            log(f"[MAP-PIPELINE] Phase 3: After transformation, final_edges = {len(final_edges)}")
            
            # Construct node metadata for the new VPC nodes so the frontend doesn't crash
            for did, members in vpc_domains.items():
                vpc_node_name = f"VPC_Domain_{did}"
                
                combined_interfaces = {}
                vpc_domain_id = did
                vpc_details = {}
                interface_macs = {}
                
                # Enhanced Correlation Intelligence
                vpc_health_score = 100
                consistency_alerts = []
                orphan_links = []
                shared_vpc_ids = set()
                peer_mismatches = []
                
                # Track what each peer sees
                peer_vpcs = {}  # {member_name: {vpc_id: status}}

                for m in members:
                    meta = node_metadata.get(m, {})
                    peer_vpcs[m] = {}

                    # Interfaces and MACs
                    for intf_name, intf_data in meta.get("interfaces", {}).items():
                        combined_interfaces[f"{m}: {intf_name}"] = intf_data
                        # Detect potential orphans (active interfaces not in Po and not peer-link)
                        if intf_data.get("status") == "up" and "Po" not in intf_name:
                            # Check if it has a neighbor
                            has_neighbor = False
                            for e in edges:
                                if e['from'] == m and norm_int(e['f_port']) == norm_int(intf_name):
                                    has_neighbor = True
                                    break
                            if has_neighbor:
                                orphan_links.append(f"{m}: {intf_name}")

                    for intf_name, macs in meta.get("interface_macs", {}).items():
                        # v6.9.3: Limit MACs per interface in the aggregated domain node to prevent JSON bloat
                        interface_macs[f"{m}: {intf_name}"] = macs[:50] if isinstance(macs, list) else macs

                    # VPC Details and consistency
                    m_vpc_details = meta.get("vpc_details", {})
                    for vpc_port, details in m_vpc_details.items():
                        if not isinstance(details, dict):
                            continue
                        
                        if details.get("type") == "vpc":
                            vpc_id = details.get("vpc_id")
                            shared_vpc_ids.add(vpc_id)
                            peer_vpcs[m][vpc_id] = details.get("status")

                            if details.get("status") != "up":
                                vpc_health_score -= 5
                                consistency_alerts.append(f"vPC {vpc_id} on {m} is {details.get('status')}")
                            if details.get("consistency") != "success":
                                vpc_health_score -= 10
                                consistency_alerts.append(f"vPC {vpc_id} on {m} consistency: {details.get('consistency')}")

                        vpc_details[f"{m}: {vpc_port}"] = details

                    # Peer-link / Keepalive check
                    for details in m_vpc_details.values():
                        if not isinstance(details, dict):
                            continue
                            
                        if details.get("type") == "peer-link":
                            if details.get("status") != "up":
                                vpc_health_score -= 40
                                consistency_alerts.append(f"Peer-Link on {m} is DOWN")
                            if details.get("keepalive") != "up":
                                vpc_health_score -= 20
                                consistency_alerts.append(f"Keepalive on {m} is DOWN")

                # v6.9.0: Cross-peer validation using cdp_validation_map
                # Build per-member cdp validation map merged into domain node
                combined_cdp_validation = {}
                combined_lacp_neighbors = {}
                combined_vpc_structured = []
                combined_pc_detail = {}
                combined_port_channels = {}
                combined_member_interfaces = {}
                combined_trust_chains = []
                combined_trust_alerts = list(trust_summary.get('trust_alerts', []))
                dom_complete = domain_completeness.get(did, {})
                for m in members:
                    meta = node_metadata.get(m, {})
                    # Merge CDP validation maps (prefix with member name)
                    for port, vdata in meta.get("cdp_validation_map", {}).items():
                        combined_cdp_validation[f"{m}: {port}"] = vdata
                    # Merge LACP neighbor data
                    for po_id, ldata in meta.get("lacp_neighbors", {}).items():
                        combined_lacp_neighbors[f"{m}: {po_id}"] = ldata
                    # Collect vpc_structured entries
                    vs = meta.get("vpc_structured", {})
                    if vs:
                        combined_vpc_structured.append({"member": m, "vpc_structured": vs})
                    # Merge port_channel_detail
                    for po_id, pd in meta.get("port_channel_detail", {}).items():
                        combined_pc_detail[f"{m}: {po_id}"] = pd
                    # v6.9.3: Merge the core port_channels registry for full visibility
                    for po_id, po_data in meta.get("port_channels", {}).items():
                        combined_port_channels[f"{m}: {po_id}"] = po_data
                    combined_member_interfaces[m] = _build_vpc_member_interfaces(m, meta)
                    combined_trust_chains.extend(meta.get('interface_trust_chains', []))
                    combined_trust_alerts.extend(meta.get('trust_alerts', []))

                if dom_complete.get('unscanned_members'):
                    unscanned = dom_complete['unscanned_members']
                    consistency_alerts.append(
                        f"Unscanned vPC peer(s) — scan for full trust: {', '.join(unscanned)}"
                    )
                    vpc_health_score -= min(30, 15 * len(unscanned))
                if dom_complete.get('single_peer_only'):
                    consistency_alerts.append(
                        "Only one peer scanned — domain health is partial; scan both vPC switches."
                    )
                    vpc_health_score -= 10

                # Cross-peer validation
                for vpc_id in shared_vpc_ids:
                    # v6.9.3: Defensive lookup to handle missing peer telemetry without crashing
                    statuses = [peer_vpcs.get(m, {}).get(vpc_id) for m in members]
                    if None in statuses:
                        vpc_health_score -= 15
                        missing_peer = [m for m in members if vpc_id not in peer_vpcs.get(m, {})]
                        peer_mismatches.append(f"vPC {vpc_id} missing on {missing_peer}")
                
                # v6.9.3: Role Consistency Audit (Split-Brain Detection)
                roles = []
                for entry in combined_vpc_structured:
                    m_role = entry.get("vpc_structured", {}).get("role", "unknown").lower()
                    roles.append(m_role)
                
                if roles.count("primary") > 1:
                    vpc_health_score -= 50
                    consistency_alerts.append("CRITICAL: Dual-Active (Split-Brain) detected! Both peers are Primary.")
                elif "primary" not in roles and roles:
                    vpc_health_score -= 30
                    consistency_alerts.append("WARNING: No Primary peer detected in domain.")
                
                vpc_health_score = max(0, vpc_health_score)
                health_label = "HEALTHY" if vpc_health_score > 90 else "WARNING" if vpc_health_score > 60 else "CRITICAL"

                node_metadata[vpc_node_name] = {
                    "interfaces": combined_interfaces,
                    "bundles": {},
                    "vpcs": list(shared_vpc_ids),
                    "vpc_domain_id": vpc_domain_id,
                    "vpc_details": vpc_details,
                    "interface_macs": interface_macs,
                    "vpc_members": members,
                    # v6.9.3: Unified logical interface registry
                    "port_channels": combined_port_channels,
                    "port_channel_detail": combined_pc_detail,
                    "vpc_structured": combined_vpc_structured,
                    "vpc_member_interfaces": combined_member_interfaces,
                    "lacp_neighbors": combined_lacp_neighbors,
                    "cdp_validation_map": combined_cdp_validation,
                    "correlation": {
                        "health_score": vpc_health_score,
                        "health_label": health_label,
                        "consistency_alerts": consistency_alerts[:10],
                        "orphan_links": orphan_links[:10],
                        "peer_mismatches": peer_mismatches,
                        "trust_alerts": list(dict.fromkeys(combined_trust_alerts))[:15],
                        "interface_trust_chains": combined_trust_chains,
                        "domain_completeness": dom_complete,
                    }
                }
                peer_info_registry[vpc_node_name] = {
                    "platform": "vPC Domain", 
                    "version": f"Health: {vpc_health_score}%", 
                    "mgmt_ip": "", 
                    "caps": health_label
                }
            
            # Phase 3 Validation - Check for edges
            log(f"[MAP-PIPELINE] Phase 3 complete: {len(final_edges)} edges after transformation")
            log(f"[MAP-PIPELINE] Phase 3 DEBUG: vpc_domains count = {len(vpc_domains)}, final_edges count = {len(final_edges)}")
            log(f"[MAP-PIPELINE] Phase 3 DEBUG: Condition check: not final_edges = {not final_edges}, bool(vpc_domains) = {bool(vpc_domains)}")
            
            # v6.8.1: CRITICAL FIX - Create placeholder edges for 2-device VPC scenarios
            # When VPC transformation removes internal peer-links but no downstream links exist,
            # we must create placeholder edges so Vis.js has something to render
            if not final_edges and vpc_domains:
                log("[MAP-PIPELINE] Phase 3: CRITICAL - No edges after transformation, CREATING placeholder edges")
                for did, members in vpc_domains.items():
                    vpc_node_name = f"VPC_Domain_{did}"
                    
                    # Create placeholder edges between VPC domain node and each member
                    # This ensures Vis.js can render the graph even with no external connections
                    for member in members:
                        placeholder_edge = {
                            "from": vpc_node_name,
                            "to": member,
                            "f_port": "vPC Domain",
                            "t_port": "Member",
                            "type": "vpc-domain-placeholder",
                            "label": f"Domain {did}",
                            "is_vpc_member": False,
                            "is_vpc_peer_link": False,
                            "vpc_domain_id": did,
                            "confidence": "Domain-Internal",
                            "f_int_data": {"status": "up", "desc": f"Virtual vPC Domain {did}"},
                            "t_int_data": {"status": "up", "desc": f"Member: {member}"},
                            "peer_info": {"platform": "vPC Domain", "version": "", "mgmt_ip": "", "caps": "Internal"},
                            "bundled_links": []
                        }
                        final_edges.append(placeholder_edge)
                        log(f"[MAP-PIPELINE] Phase 3: CREATED placeholder edge {vpc_node_name} -> {member}")
                    
                    # Also create a virtual peer-link edge between members if we have exactly 2
                    if len(members) == 2:
                        peer_edge = {
                            "from": members[0],
                            "to": members[1],
                            "f_port": "Peer-Link",
                            "t_port": "Peer-Link",
                            "type": "vpc-peer-link",
                            "label": "vPC Peer-Link",
                            "is_vpc_member": False,
                            "is_vpc_peer_link": True,
                            "vpc_domain_id": did,
                            "confidence": "Inferred",
                            "f_int_data": {"status": "up", "desc": "vPC peer connection"},
                            "t_int_data": {"status": "up", "desc": "vPC peer connection"},
                            "peer_info": {"platform": "vPC Peer", "version": "", "mgmt_ip": "", "caps": "Peer-Link"},
                            "bundled_links": []
                        }
                        final_edges.append(peer_edge)
                        log(f"[MAP-PIPELINE] Phase 3: CREATED peer-link edge {members[0]} <-> {members[1]}")
                
                log(f"[MAP-PIPELINE] Phase 3: CREATED {len(final_edges)} placeholder edges total")
            elif final_edges:
                log(f"[MAP-PIPELINE] Phase 3: Edges exist ({len(final_edges)}), skipping placeholder creation")
                for i, e in enumerate(final_edges[:3]):  # Log first 3 edges
                    log(f"[MAP-PIPELINE] Phase 3: Edge {i}: {e.get('from')} -> {e.get('to')} type={e.get('type')}")
            elif not vpc_domains:
                log("[MAP-PIPELINE] Phase 3: No vpc_domains, skipping placeholder creation")
        if not vpc_domains:
            vpc_adjacency_fallback = True
            vpc_no_domain_banner = (
                "<div style='background:#fffbeb;border:2px solid #f59e0b;border-radius:10px;"
                "padding:14px 18px;margin:12px 0;color:#92400e;font-size:13px;'>"
                "<b>No vPC domain detected</b> on scanned switches (need two peers with matching "
                "<code>show vpc</code> domain-id). Showing <b>physical adjacency</b> (CDP/LLDP) on the topology map."
                "</div>"
            )
            log("[MAP-PIPELINE] Phase 3: VPC adjacency fallback — edges will remain visible")

    else:
        # Standard mode - v6.5.10 Domain Peer logic
        domain_to_nodes = {}
        for node_name, meta in node_metadata.items():
            did = str(meta.get("vpc_domain_id", "")).strip()
            if did:
                domain_to_nodes.setdefault(did, []).append(node_name)

        existing_pairs = set()
        for e in final_edges:
            pair = tuple(sorted([e.get("from", ""), e.get("to", "")]))
            if all(pair):
                existing_pairs.add(pair)

        for did, members in domain_to_nodes.items():
            unique_members = sorted(set(members))
            if len(unique_members) < 2:
                continue
            for idx in range(len(unique_members) - 1):
                a = unique_members[idx]
                b = unique_members[idx + 1]
                pair = tuple(sorted([a, b]))
                if pair in existing_pairs:
                    continue
                final_edges.append({
                    "from": a,
                    "to": b,
                    "f_port": "vPC-domain",
                    "t_port": "vPC-domain",
                    "type": "vpc-domain-peer",
                    "label": f"Domain {did} Peer Relationship",
                    "is_vpc_member": False,
                    "is_vpc_peer_link": True,
                    "vpc_domain_id": did,
                    "confidence": "Domain-Matched",
                    "f_int_data": {"status": "up", "desc": "Inferred by matching vPC domain-id"},
                    "t_int_data": {"status": "up", "desc": "Inferred by matching vPC domain-id"},
                    "peer_info": {"platform": "", "version": "", "mgmt_ip": "", "caps": ""},
                    "bundled_links": []
                })
                existing_pairs.add(pair)

    log(f"  > Compiled {len(uniq_nodes)} Nodes and {len(final_edges)} Links.")

    vis_js_content = _load_vis_js(log)

    # --- Priority 7: Role-based color scheme ---
    # In vPC mode keep the original vPC-focused palette; in standard mode use role colors
    # v6.6.0: Premium Role-based color scheme
    ROLE_COLORS = {
        'core':         {'bg': '#c0392b', 'border': '#922b21', 'font': '#ffffff', 'shadow': '#c0392b'},
        'distribution': {'bg': '#e67e22', 'border': '#ca6f1e', 'font': '#ffffff', 'shadow': '#e67e22'},
        'access':       {'bg': '#2980b9', 'border': '#1f618d', 'font': '#ffffff', 'shadow': '#2980b9'},
        'unknown':      {'bg': '#607d8b', 'border': '#455a64', 'font': '#ffffff', 'shadow': '#607d8b'},
        'vpc_peer':     {'bg': '#9b59b6', 'border': '#7d3c98', 'font': '#ffffff', 'shadow': '#9b59b6'},
        'vpc_domain':   {'bg': '#e84393', 'border': '#d63031', 'font': '#ffffff', 'shadow': '#e84393'}
    }
    # Fallback palette for vPC mode (keeps original look but more vibrant)
    vpc_colors = ['#e67e22', '#9b59b6', '#3498db', '#1abc9c', '#e74c3c', '#f39c12', '#2ecc71', '#34495e']

    # Phase 4: Node Building
    log("[MAP-PIPELINE] Phase 4: Building node objects...")
    nodes_json = []
    node_roles = {}  # {node_id: role_str}  — used by Priority 10 JS for legend

    for i, n in enumerate(uniq_nodes):
        pstats = node_port_stats.get(n, {"up": 0, "down": 0, "err": 0, "total": 0})
        int_meta_all = node_metadata.get(n, {}).get("interfaces", {})
        
        # ── MAC Address Integration ───────────────────────────────────────────
        # interface_macs is stored separately in node_metadata (from topology_mapper).
        # Merge them into int_meta_all so the JS side panel can read macs per interface.
        # Also ensure every interface dict has all required fields so JS never gets
        # undefined for speed/vlan/duplex/macs regardless of which parse path created it.
        interface_macs = node_metadata.get(n, {}).get("interface_macs", {})
        for intf_name, intf_data in int_meta_all.items():
            # Guarantee all display fields exist
            intf_data.setdefault("speed",  "")
            intf_data.setdefault("vlan",   "")
            intf_data.setdefault("duplex", "")
            intf_data.setdefault("desc",   "")
            intf_data.setdefault("macs",   [])
            # Merge MACs from the separate interface_macs dict
            if intf_name in interface_macs:
                macs = interface_macs[intf_name]
                intf_data['macs'] = macs[:50] if len(macs) > 50 else macs
        
        total_ints = len(int_meta_all)
        up_ints = sum(1 for v in int_meta_all.values() if v.get('status') == 'up')
        down_ints = sum(1 for v in int_meta_all.values()
                        if v.get('status') not in ('up', 'err-disabled', 'unknown') and v.get('status'))
        err_ints = sum(1 for v in int_meta_all.values() if v.get('status') == 'err-disabled')

        if total_ints == 0:
            up_ints = pstats["up"]
            down_ints = pstats["down"]
            err_ints = pstats["err"]
            total_ints = pstats["total"]

        badge_parts = []
        if up_ints: badge_parts.append(f"{up_ints} UP")
        if down_ints: badge_parts.append(f"{down_ints} DOWN")
        if err_ints: badge_parts.append(f"{err_ints} ERR")
        port_badge_str = " | ".join(badge_parts) if badge_parts else ""

        node_label = f"{n}\n{port_badge_str}" if port_badge_str else n
        if map_mode == 'all':
            display_label = n
            title_extra = port_badge_str or ''
        else:
            display_label = node_label
            title_extra = ''

        neighbor_cnt = node_neighbor_count.get(n, 0)
        role, _role_color = _detect_device_role(n, neighbor_cnt, int_meta_all)
        node_roles[n] = role

        if map_mode == 'vpc':
            bg_color = vpc_colors[i % len(vpc_colors)]
            border_color = "#333"
            font_color = "#1a1a2e"
        else:
            rc = ROLE_COLORS.get(role, ROLE_COLORS['unknown'])
            bg_color = rc['bg']
            border_color = rc['border']
            font_color = rc['font']

        level_map = {'core': 0, 'distribution': 1, 'access': 2, 'unknown': 1}
        node_level = level_map.get(role, 1)

        # v6.6.0: Enhanced vPC Peer Clustering logic
        # Peers in the same vPC domain get the same group for visual clustering
        vpc_domain_id = node_metadata.get(n, {}).get("vpc_domain_id", "")
        node_group = role
        if map_mode == 'vpc' and vpc_domain_id:
            # v6.8.2: Distinguish primary (first) and secondary (second) VPC peers
            # Find all members in this VPC domain and assign group based on order
            domain_members = []
            for node_name, meta in node_metadata.items():
                if meta.get("vpc_domain_id") == vpc_domain_id:
                    domain_members.append(node_name)
            domain_members.sort()  # Consistent ordering
            if n in domain_members:
                idx = domain_members.index(n)
                if idx == 0:
                    node_group = 'vpc_primary'
                    role = 'vpc_primary'
                else:
                    node_group = 'vpc_secondary'
                    role = 'vpc_secondary'
            else:
                node_group = f"vpc_domain_{vpc_domain_id}"
                role = 'vpc_peer'
            
        if n.startswith("VPC_Domain_"):
            role = 'vpc_domain'
            node_group = role
            # Extract members to show in label
            members = node_metadata.get(n, {}).get("vpc_members", [])
            members_str = ", ".join(members) if members else ""
            node_label = f"vPC Domain {vpc_domain_id}\n({members_str})"
            if port_badge_str:
                node_label += f"\n{port_badge_str}"

        vpc_count = sum(1 for e in final_edges if e['from'] == n and e.get('is_vpc_member'))

        peer_info_node = peer_info_registry.get(n, {})

        node_obj = {
            "id": n, "label": display_label if map_mode == 'all' else node_label, "shape": "box",
            "color": {
                "background": bg_color, "border": border_color,
                "highlight": {"background": "#ffffff", "border": "#3498db"},
                "hover": {"background": bg_color, "border": "#ffffff"}
            },
            "font": {"color": font_color, "size": 14, "face": "Inter, Segoe UI, sans-serif"},
            "borderWidth": 2, 
            "shadow": {"enabled": True, "color": "rgba(0,0,0,0.3)", "size": 10, "x": 0, "y": 4},
            "margin": 12,
            "level": node_level,
            "role": role,
            "group": node_group,
            # Structured data for JS side-panel
            "port_stats": {
                "up": up_ints,
                "down": down_ints,
                "err": err_ints,
                "total": total_ints
            },
            "vpc_count": vpc_count,
            "vpc_domain_id": node_metadata.get(n, {}).get("vpc_domain_id", ""),
            # v6.7.2: Include vpc_members for VPC domain nodes (critical for v7.0 visualization)
            "vpc_members": node_metadata.get(n, {}).get("vpc_members", []),
            # v6.5.9: Include full vPC details so the frontend can render
            # member ports and peer-links per device without additional lookups.
            "vpc_details": node_metadata.get(n, {}).get("vpc_details", {}),
            "device_info": peer_info_node,
            "interfaces": int_meta_all,
            # v6.9.0: Structured enrichment for side-panel
            "port_channel_detail": node_metadata.get(n, {}).get("port_channel_detail", {}),
            "port_channels": node_metadata.get(n, {}).get("port_channels", {})
                or node_metadata.get(n, {}).get("port_channel_detail", {}),
            "vpc_structured": node_metadata.get(n, {}).get("vpc_structured", {}),
            "vpc_member_interfaces": node_metadata.get(n, {}).get("vpc_member_interfaces", {}),
            "lacp_neighbors": node_metadata.get(n, {}).get("lacp_neighbors", {}),
            "cdp_validation_map": node_metadata.get(n, {}).get("cdp_validation_map", {}),
            "interface_trust_chains": node_metadata.get(n, {}).get("interface_trust_chains", []),
            "trust_alerts": node_metadata.get(n, {}).get("trust_alerts", []),
            "nxos_version": node_metadata.get(n, {}).get("nxos_version", ""),
            "correlation": node_metadata.get(n, {}).get("correlation", {}),
            "is_scanned": n in node_metadata
        }
        if map_mode == 'all':
            node_obj["title"] = n + (f" · {title_extra}" if title_extra else "")
            node_obj["map_label"] = display_label
        if n in node_metadata and not n.startswith("VPC_Domain_"):
            node_obj["vpc_member_interfaces"] = {
                n: _build_vpc_member_interfaces(n, node_metadata[n])
            }
        nodes_json.append(node_obj)
    
    # Phase 4 Validation
    log(f"[MAP-PIPELINE] Phase 4 complete: {len(nodes_json)} nodes built")
    validation_errors = []
    for n in nodes_json:
        if n['id'].startswith('VPC_Domain_'):
            if not n.get('vpc_members'):
                validation_errors.append(f"{n['id']} missing vpc_members")
    if validation_errors:
        log(f"[MAP-PIPELINE] ERROR Phase 4: Node validation failed: {validation_errors}")
    else:
        log("[MAP-PIPELINE] Phase 4: All nodes validated successfully")
    
    if os.environ.get('NST_DEBUG'):
        log(f"  > [DEBUG] Total nodes in nodes_json: {len(nodes_json)}")
        vpc_node_count = sum(1 for n in nodes_json if n['id'].startswith('VPC_Domain_'))
        log(f"  > [DEBUG] VPC domain nodes: {vpc_node_count}")
        for n in nodes_json:
            if n['id'].startswith('VPC_Domain_'):
                members = n.get('vpc_members', [])
                log(f"  > [DEBUG]   {n['id']}: members={members}, domain_id={n.get('vpc_domain_id', 'N/A')}")

    link_issues = _apply_cable_optics_issues(final_edges, node_metadata, log, diag_folder)

    edges_json = []
    for ei, e in enumerate(final_edges):
        estyle = {"color": "#607d8b", "width": 2, "dashes": False}
        trust_tier = (e.get('trust_tier') or '').lower()
        if (
            e.get('not_physical')
            or e.get('type') == 'overlay'
            or str(e.get('layer') or '').lower() == 'overlay'
        ):
            estyle = {"color": "#a855f7", "width": 2, "dashes": [8, 6], "shadow": False}
        elif e.get('confidence') == "Verified" or trust_tier == 'verified':
            estyle = {"color": "#059669", "width": 4, "dashes": False, "shadow": True}
        elif e.get('confidence') == "Mismatch":
            estyle = {"color": "#ff4757", "width": 5, "dashes": False, "shadow": True} # Red
        elif trust_tier in ('inferred', 'untrusted') or e.get('confidence') == "Inferred":
            estyle = {"color": "#94a3b8", "width": 2, "dashes": [6, 6], "shadow": False}
        elif e.get('confidence') == "Low" or trust_tier == 'low':
            estyle = {"color": "#f97316", "width": 3, "dashes": [8, 4], "shadow": False}
        elif e.get('confidence') == "Medium" or e.get('type') == "asymmetric" or trust_tier == 'medium':
            estyle = {"color": "#eccc68", "width": 3, "dashes": [10, 10], "shadow": False} # Yellow
        elif e.get('type') == "port-channel":
            estyle = {"color": "#2ed573", "width": 5, "dashes": False, "shadow": True} # Green
        elif e.get('type') == "vpc":
            estyle = {"color": "#ff7f50", "width": 8, "dashes": False, "shadow": {"enabled": True, "color": "rgba(255,127,80,0.4)", "size": 12}} 
        elif e.get('type') == "vpc-peer-link":
            estyle = {"color": "#a55eea", "width": 10, "dashes": False, "shadow": {"enabled": True, "color": "rgba(165,94,234,0.5)", "size": 15}}
        elif e.get('type') == "vpc-domain-peer":
            estyle = {"color": "#8854d0", "width": 4, "dashes": [12, 6], "shadow": False}
        elif e.get('type') == "vpc_shared":
            estyle = {"color": "#0984e3", "width": 8, "dashes": False, "shadow": {"enabled": True, "color": "rgba(9, 132, 227, 0.4)", "size": 12}}
        elif e.get('type') == "vpc_orphan":
            estyle = {"color": "#d63031", "width": 4, "dashes": [5, 5], "shadow": False}

        edge_hidden = False
        if (
            map_mode == 'vpc'
            and not vpc_adjacency_fallback
            and not (e.get('is_vpc_member') or e.get('is_vpc_peer_link')
                     or e.get('type') in ('vpc-shared', 'vpc_shared', 'vpc_orphan',
                                          'vpc-peer-link', 'vpc-domain-peer', 'vpc',
                                          'vpc-domain-placeholder'))
        ):
            estyle["color"] = "#bdc3c7"
            estyle["width"] = 1
            edge_hidden = True

        # Interface descriptions for edge tooltip and labels
        f_int_data = e.get('f_int_data', {})
        t_int_data = e.get('t_int_data', {})
        f_int_desc = f_int_data.get('desc', '')
        t_int_desc = t_int_data.get('desc', '')
        f_int_speed = f_int_data.get('speed', '')
        f_int_status = f_int_data.get('status', '')
        
        # Build tooltip title (full detail — descriptions live here, not on canvas)
        title_lines = [f"<b>{e['from']}</b> ({e['f_port']}) ↔ <b>{e['to']}</b> ({e['t_port']})"]
        if e.get('type') == 'vpc-peer-link':
            title_lines.append("<b>vPC Peer-Link</b>")
        if e.get('label') and e['label'] not in ('', 'Peer-Link'):
            title_lines.append(f"Bundle: {e['label']}")
        if f_int_status:
            title_lines.append(f"Status: {f_int_status.upper()}" + (f" · {f_int_speed}" if f_int_speed else ""))
        if f_int_desc and f_int_desc != '-':
            title_lines.append(f"{e['from']}: {f_int_desc}")
        if t_int_desc and t_int_desc != '-':
            title_lines.append(f"{e['to']}: {t_int_desc}")
        if e.get('confidence'):
            ts = e.get('trust_score', '')
            title_lines.append(
                f"Trust: {e['confidence']}"
                + (f" ({ts})" if ts != '' else '')
                + (' · bidirectional CDP' if e.get('bidirectional') else '')
            )
        if e.get('cable_issues'):
            title_lines.append("Witness issues: " + ", ".join(e.get('cable_issues') or []))
        if e.get('cable_witnesses'):
            title_lines.append("Witnesses: " + "; ".join((e.get('cable_witnesses') or [])[:4]))
        if e.get('cable_note'):
            title_lines.append(e['cable_note'])
        edge_title = "<br>".join(title_lines)

        # Map canvas label: ports only (never descriptions — prevents text overlap)
        etype = e.get('type', 'standard')
        if map_mode == 'all':
            if etype == 'vpc-peer-link':
                map_label = f"Peer-Link · {e['f_port']}"
            elif etype == 'port-channel':
                map_label = e.get('label') or f"{e['f_port']} ↔ {e['t_port']}"
            elif etype == 'vpc':
                map_label = f"vPC · {e['f_port']}"
            else:
                map_label = f"{e['f_port']} ↔ {e['t_port']}"
            canvas_label = ''  # hidden until user toggles port labels
            final_edge_label = map_label
        else:
            label_lines = [f"{e['f_port']} ↔ {e['t_port']}"]
            if e['label']:
                label_lines.append(e['label'])
            if f_int_status:
                stat_str = f"[{f_int_status.upper()}]"
                if f_int_speed:
                    stat_str += f" {f_int_speed}"
                label_lines.append(stat_str)
            if f_int_desc and f_int_desc != '-':
                trunc_desc = f_int_desc[:25] + "..." if len(f_int_desc) > 25 else f_int_desc
                label_lines.append(f"\"{trunc_desc}\"")
            final_edge_label = "\n".join(label_lines)
            canvas_label = final_edge_label
            map_label = final_edge_label
        if map_mode == 'vpc':
            short = f"{e.get('f_port', '')} → {e.get('t_port', '')}"
            if len(short) > 42:
                short = short[:39] + '...'
            final_edge_label = short
            canvas_label = short
            map_label = short

        # v6.8.2: Enhanced edge styling with curved edges and directionality
        smooth_config = {"type": "cubicBezier", "roundness": 0.5}
        
        # Add curvature offset for VPC edges to prevent overlapping
        if map_mode == 'vpc':
            edge_type = e.get('type', '')
            if edge_type in ['vpc', 'vpc_shared']:
                smooth_config = {"type": "cubicBezier", "roundness": 0.6, "forceDirection": "horizontal"}
            elif edge_type == 'vpc-peer-link':
                smooth_config = {"type": "continuous", "roundness": 0.3}
            elif edge_type == 'vpc_orphan':
                smooth_config = {"type": "cubicBezier", "roundness": 0.7, "forceDirection": "vertical"}
        
        edges_json.append({
            "id": "e%d" % ei,
            "from": e['from'], "to": e['to'],
            "label": canvas_label,
            "map_label": map_label,
            "title": edge_title,
            "type": e.get('type', ''),
            "layer": e.get('layer') or '',
            "edge_kind": e.get('edge_kind') or '',
            "not_physical": bool(e.get('not_physical')),
            "f_port": e.get('f_port', ''),
            "t_port": e.get('t_port', ''),
            "bundled_links": e.get('bundled_links', []),
            "hidden": edge_hidden,
            "is_vpc_member": e.get('is_vpc_member', False),
            "is_vpc_peer_link": e.get('is_vpc_peer_link', False),
            "font": {"align": "middle", "size": 9, "color": "#c9d1d9", "strokeWidth": 0, "background": "rgba(13,17,23,0.85)"},
            "color": estyle["color"], "width": estyle["width"], "dashes": estyle["dashes"],
            "smooth": smooth_config,
            # Add arrows for directionality in VPC mode
            "arrows": {"to": {"enabled": False}, "from": {"enabled": False}} if not map_mode == 'vpc' else 
                      {"to": {"enabled": e.get('is_vpc_member', False), "scaleFactor": 0.5}, "from": {"enabled": False}},
            # Pass all structured data to the frontend
            "edge_data": e
        })

    # Generate vPC summary for vPC mode
    vpc_summary_html = ""
    if map_mode == 'vpc' and vpc_info_all:
        # Build structured vPC domain table
        vpc_rows = ""
        for host, vpc_data in vpc_info_all.items():
            peer_links = [pc for pc, d in vpc_data.items() if isinstance(d, dict) and d.get('type') == 'peer-link']
            vpc_members = [(pc, d) for pc, d in vpc_data.items() if isinstance(d, dict) and d.get('type') == 'vpc']
            peer_link_str = ", ".join(peer_links) if peer_links else "—"
            for pc, details in vpc_members:
                status_icon = "[UP]" if details.get('status') == 'up' else "[DOWN]"
                vpc_rows += (
                    f"<tr style='transition: background 0.2s;'>"
                    f"<td style='padding:10px 14px; border-bottom:1px solid #334155; font-weight:600; color:#f1f5f9;'>{host}</td>"
                    f"<td style='padding:10px 14px; border-bottom:1px solid #334155; color:#94a3b8;'>{details.get('vpc_id','N/A')}</td>"
                    f"<td style='padding:10px 14px; border-bottom:1px solid #334155; font-family:monospace; color:#38bdf8;'>{pc}</td>"
                    f"<td style='padding:10px 14px; border-bottom:1px solid #334155;'>{status_icon} <span style='color:#f1f5f9;'>{details.get('status','unknown')}</span></td>"
                    f"<td style='padding:10px 14px; border-bottom:1px solid #334155; color:#a78bfa; font-family:monospace;'>{peer_link_str}</td>"
                    f"</tr>"
                )
            if not vpc_members:
                # Device has peer-link but no vPC members yet
                for pl in peer_links:
                    vpc_rows += (
                        f"<tr>"
                        f"<td style='padding:10px 14px; border-bottom:1px solid #334155; font-weight:600; color:#f1f5f9;'>{host}</td>"
                        f"<td style='padding:10px 14px; border-bottom:1px solid #334155; color:#475569;'>—</td>"
                        f"<td style='padding:10px 14px; border-bottom:1px solid #334155; color:#475569;'>—</td>"
                        f"<td style='padding:10px 14px; border-bottom:1px solid #334155; color:#475569;'>—</td>"
                        f"<td style='padding:10px 14px; border-bottom:1px solid #334155; color:#a78bfa; font-family:monospace;'>{pl}</td>"
                        f"</tr>"
                    )

        vpc_summary_html = (
            "<div style='background: rgba(30, 41, 59, 0.85); border: 1px solid #475569; border-radius: 16px; "
            "padding:20px; margin-bottom:20px; box-shadow: 0 8px 24px rgba(0,0,0,0.35);'>"
            "<div style='display:flex; flex-wrap:wrap; gap:12px; margin-bottom:16px; font-size:12px;'>"
            "<span style='background:#5f27cd;color:#fff;padding:6px 12px;border-radius:8px;'>🟣 Peer-Link</span>"
            "<span style='background:#ff7f50;color:#fff;padding:6px 12px;border-radius:8px;'>🟠 vPC Member</span>"
            "<span style='background:#0984e3;color:#fff;padding:6px 12px;border-radius:8px;'>🔵 Shared Downstream</span>"
            "<span style='background:#636e72;color:#fff;padding:6px 12px;border-radius:8px;'>⚪ Other L2</span>"
            "<span style='background:#d63031;color:#fff;padding:6px 12px;border-radius:8px;'>🔴 Orphan / Mismatch</span>"
            "</div>"
            "<h3 style='margin:0 0 12px 0; color:#38bdf8; font-size:17px; font-weight:700; display:flex; align-items:center; gap:8px;'>"
            "<span>🧭</span> vPC Domain Intelligence</h3>"
            "<p style='margin:0 0 14px 0;color:#94a3b8;font-size:12px;line-height:1.5;'>"
            "Physical peers stay visible; logical <b>VPC_Domain_*</b> anchors group the pair. "
            "Click a domain node for member interfaces, consistency, and peer-link health. "
            "Diagnostics JSON is written beside this HTML in <code style='color:#e2e8f0'>topology_diagnostics_*</code>.</p>"
            "<table style='width:100%; border-collapse:collapse; font-size:13px;'>"
            "<thead><tr style='text-align:left; color:#94a3b8; font-size:11px; text-transform:uppercase; letter-spacing:0.05em;'>"
            "<th style='padding:8px 14px; border-bottom:2px solid #334155;'>Source Switch</th>"
            "<th style='padding:8px 14px; border-bottom:2px solid #334155;'>vPC ID</th>"
            "<th style='padding:8px 14px; border-bottom:2px solid #334155;'>Port-Channel</th>"
            "<th style='padding:8px 14px; border-bottom:2px solid #334155;'>Status</th>"
            "<th style='padding:8px 14px; border-bottom:2px solid #334155;'>Peer-Link</th>"
            "</tr></thead>"
            f"<tbody>{vpc_rows}</tbody>"
            "</table>"
            "⚪ Grey edges = non-vPC links (dimmed)"
            "</div>"
        )

    # --- Priority 7: Role legend HTML ---
    role_legend_html = ""
    if map_mode != 'vpc':
        role_counts = {}
        for r in node_roles.values():
            role_counts[r] = role_counts.get(r, 0) + 1
        if role_counts:
            role_legend_html = (
                "<div style='background:#f8f9fa; border:1px solid #dee2e6; border-radius:8px; "
                "padding:12px 16px; margin-bottom:16px; display:flex; align-items:center; gap:16px; flex-wrap:wrap;'>"
                "<span style='font-weight:600; font-size:13px; color:#2c3e50;'>\U0001f3f7\ufe0f Device Roles:</span>"
            )
            role_labels = {
                'core': ('\U0001f534 Core', '#c0392b'),
                'distribution': ('\U0001f7e0 Distribution', '#e67e22'),
                'access': ('\U0001f535 Access', '#2980b9'),
                'unknown': ('\u26aa Unknown', '#607d8b'),
            }
            for role_key, (label, color) in role_labels.items():
                cnt = role_counts.get(role_key, 0)
                if cnt:
                    role_legend_html += (
                        f"<span style='background:{color}; color:white; padding:4px 10px; "
                        f"border-radius:12px; font-size:12px;'>{label}: {cnt}</span>"
                    )
            role_legend_html += "</div>"

    extra_header = (
        _build_topology_report_header(
            map_mode=map_mode,
            devices_requested=devices_requested,
            devices_truncated=devices_truncated,
            devices_scanned=len(devices),
            failed_hosts=failed_hosts,
            parallel_workers=parallel_workers,
            node_count=len(uniq_nodes),
            edge_count=len(final_edges),
        )
        + (vpc_no_domain_banner if map_mode == 'vpc' and vpc_adjacency_fallback else "")
        + (vpc_summary_html if map_mode == 'vpc' else "")
        + role_legend_html
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Phase 4.9: DIAGNOSTIC DATA DUMP (v7.0.0)
    # Creates a timestamped folder alongside the HTML output capturing every
    # data stage so engineers can trace gaps between raw collection and rendering.
    # ─────────────────────────────────────────────────────────────────────────
    try:
        diag_ts = ts
        log(f"[MAP-PIPELINE] Phase 4.9: Writing diagnostic dump to {diag_folder}")

        readme_path = os.path.join(diag_folder, "00_README.txt")
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(
                "TOPOLOGY MAP DIAGNOSTIC PACKAGE\n"
                "================================\n\n"
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Mode: {map_mode.upper()}\n"
                f"HTML map: {os.path.basename(html_file)}\n\n"
                "FILE GUIDE (read in this order for troubleshooting):\n"
                "  00_README.txt                  — This navigation guide\n"
                "  vpc_map_data_TEMPLATE.json     — Editable schema; copy values for real network data\n"
                "  01_raw_node_metadata.json      — SSH collection per switch (before graph transform)\n"
                "  02_pre_transform_edges.json  — CDP/LLDP edges before vPC clustering\n"
                "  03_post_transform_edges.json   — Edges after vPC transform (bundled_links here)\n"
                "  04_final_map_data.json         — Exact Vis.js nodes+edges embedded in HTML\n"
                "  link_issues.json               — Description/speed/duplex/DOM/LACP witness rows\n"
                "  05_vpc_domain_summary.txt      — Human-readable domain overview\n"
                "  06_pre_render_presentation.json— UI payload BEFORE HTML (sidebar + board_sections)\n"
                "  07_post_render_manifest.json   — Written AFTER HTML; paths and counts\n"
                "  board_sections (in 06)         — Engineering Board JSON (v6.9.27+ vPC mode)\n"
                "  topology_map_*.html            — Interactive map (open in browser, offline)\n\n"
                "MEMBER INTERFACES EMPTY?\n"
                "  → 01 → devices → <switch> → vpc_structured / port_channel_detail\n"
                "  → 06 → member_interfaces_by_switch\n"
                "  → 03 → edges_by_type → vpc_shared → bundled_links\n"
            )

        # ── FILE 1: Raw Node Metadata ─────────────────────────────────────────
        # Everything collected from SSH: interfaces, MACs, vPC details, port-channels
        f1_path = os.path.join(diag_folder, "01_raw_node_metadata.json")
        f1_content = {
            "_README": (
                "FILE 01 — Raw Node Metadata (Post-Collection, Pre-Transformation)\n"
                "This is the exact data returned from SSH command parsing for every scanned device.\n"
                "Keys per device: interfaces, vpc_details, port_channel_detail, vpc_structured, lacp_neighbors, cdp_validation_map\n"
                "Use this file to verify that SSH collection is returning the expected data for each switch."
            ),
            "_meta": {
                "generated_at": diag_ts,
                "map_mode": map_mode,
                "scanned_devices": list(node_metadata.keys()),
                "total_devices": len(node_metadata)
            },
            "devices": {}
        }
        for dev_name, meta in node_metadata.items():
            # Summarize interface count per status to keep file readable
            ifaces = meta.get("interfaces", {})
            iface_summary = {"up": 0, "down": 0, "err-disabled": 0, "other": 0}
            for idata in ifaces.values():
                st = idata.get("status", "other")
                iface_summary[st] = iface_summary.get(st, 0) + 1

            f1_content["devices"][dev_name] = {
                "_note": f"Device: {dev_name} | {len(ifaces)} interfaces collected",
                "vpc_domain_id": meta.get("vpc_domain_id"),
                "vpc_members": meta.get("vpc_members", []),
                "interface_count": len(ifaces),
                "interface_status_summary": iface_summary,
                "interfaces": ifaces,
                "vpc_details": meta.get("vpc_details", {}),
                "port_channel_detail": meta.get("port_channel_detail", {}),
                "vpc_structured": meta.get("vpc_structured", {}),
                "vpc_member_interfaces": _build_vpc_member_interfaces(dev_name, meta),
                "lacp_neighbors": meta.get("lacp_neighbors", {}),
                "cdp_validation_map": meta.get("cdp_validation_map", {}),
                "port_channels": meta.get("port_channels", {}),
                "correlation": meta.get("correlation", {})
            }
        with open(f1_path, "w", encoding="utf-8") as f:
            json.dump(f1_content, f, indent=2, default=str)

        # ── FILE 2: Pre-Transform Edges ───────────────────────────────────────
        # The raw CDP/LLDP/LACP edges before VPC clustering transformation
        f2_path = os.path.join(diag_folder, "02_pre_transform_edges.json")
        f2_content = {
            "_README": (
                "FILE 02 — Pre-Transform Edge List (CDP/LLDP Raw Adjacency)\n"
                "These are the raw physical edges discovered via CDP/LLDP before any vPC mode transformation.\n"
                "Each edge represents a direct physical or logical link between two devices.\n"
                "Fields: from, to, f_port, t_port, type, confidence, bundled_links (LACP members)\n"
                "Use this to verify CDP/LLDP discovery is accurate and complete."
            ),
            "_meta": {
                "generated_at": diag_ts,
                "map_mode": map_mode,
                "edge_count_before_transform": len(edges),
                "note": "These edges are BEFORE vPC domain clustering. In vpc mode, physical switches get merged."
            },
            "edges": edges
        }
        with open(f2_path, "w", encoding="utf-8") as f:
            json.dump(f2_content, f, indent=2, default=str)

        # ── FILE 3: VPC Transformation Output ────────────────────────────────
        # The final_edges after vPC mode clustering — what the HTML graph is built from
        f3_path = os.path.join(diag_folder, "03_post_transform_edges.json")
        # Group edges by type for readability
        edges_by_type = {}
        for e in final_edges:
            et = e.get("type", "unknown")
            edges_by_type.setdefault(et, []).append(e)

        f3_content = {
            "_README": (
                "FILE 03 — Post-Transform Edge List (After vPC Clustering)\n"
                "These are the final edges after vPC mode transformation has been applied.\n"
                "Physical switch-to-switch edges are replaced by VPC_Domain_XX virtual node edges.\n"
                "Edge types you will see:\n"
                "  vpc-peer-link    : Physical peer-link between the two member switches\n"
                "  vpc-domain-peer  : Logical association from VPC domain node to each physical switch\n"
                "  vpc_shared       : Downstream connection dual-homed to BOTH switches (good!)\n"
                "  vpc_orphan       : Downstream connection to only ONE switch (risk: no redundancy)\n"
                "  standard         : Regular non-vPC link between any two nodes\n"
                "bundled_links inside vpc_shared/vpc_orphan contain the physical per-switch port data."
            ),
            "_meta": {
                "generated_at": diag_ts,
                "map_mode": map_mode,
                "edge_count_after_transform": len(final_edges),
                "edges_by_type": {et: len(elist) for et, elist in edges_by_type.items()}
            },
            "edges_by_type": edges_by_type
        }
        with open(f3_path, "w", encoding="utf-8") as f:
            json.dump(f3_content, f, indent=2, default=str)

        # ── FILE 4: Final Map Data (Nodes + Edges → HTML Input) ──────────────
        # The exact JSON that is embedded into the HTML file for Vis.js rendering
        f4_path = os.path.join(diag_folder, "04_final_map_data.json")
        f4_content = {
            "_README": (
                "FILE 04 — Final Map Data (Exact Input to Vis.js Renderer)\n"
                "This is the EXACT data embedded in the HTML file.\n"
                "If the HTML map shows wrong data, compare this file to FILE 01/03 to locate the gap.\n"
                "\nNode structure fields:\n"
                "  id, label, group, role, vpc_domain_id, vpc_members, port_stats,\n"
                "  device_info, interfaces, vpc_details, port_channel_detail,\n"
                "  vpc_structured, lacp_neighbors, cdp_validation_map, is_scanned\n"
                "\nEdge structure fields:\n"
                "  from, to, label, title, color, width, type, f_port, t_port,\n"
                "  f_int_data, t_int_data, bundled_links, edge_data\n"
                "\nFor vPC shared edges: bundled_links contains per-switch physical port data.\n"
                "Each bundled link has: from (switch name), f_port, to, t_port, f_int_data."
            ),
            "_meta": {
                "generated_at": diag_ts,
                "map_mode": map_mode,
                "node_count": len(nodes_json),
                "edge_count": len(edges_json),
                "html_file": os.path.basename(html_file)
            },
            "nodes": nodes_json,
            "edges": edges_json,
            "link_issues": link_issues,
        }
        with open(f4_path, "w", encoding="utf-8") as f:
            json.dump(f4_content, f, indent=2, default=str)

        if map_mode == 'all':
            try:
                from utils.utilization_overlay.ssh_collector import write_ssh_targets
                tpath = write_ssh_targets(diag_folder, results, devices)
                if tpath:
                    log("[UTIL-LIVE] wrote utilization_ssh_targets.json (map node → inventory SSH host; not a graph)")
            except Exception as _tgt_ex:
                log(f"[UTIL-LIVE] SSH target table skipped: {_tgt_ex}")

        # ── FILE 5: VPC Domain Summary (Human-Readable) ───────────────────────
        f5_path = os.path.join(diag_folder, "05_vpc_domain_summary.txt")
        vpc_domains_used = {}
        for n in nodes_json:
            if n.get("id", "").startswith("VPC_Domain_"):
                did = n.get("vpc_domain_id", "?")
                members = n.get("vpc_members", [])
                vpc_domains_used[did] = members

        lines5 = [
            "=" * 70,
            "  TOPOLOGY MAP DIAGNOSTIC SUMMARY — v7.0.0",
            f"  Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"  Mode      : {map_mode.upper()}",
            f"  HTML File : {os.path.basename(html_file)}",
            "=" * 70,
            "",
            "── FILES IN THIS DIAGNOSTIC FOLDER ──────────────────────────────────",
            "  01_raw_node_metadata.json   — Raw SSH-collected data per device",
            "  02_pre_transform_edges.json — CDP/LLDP edges before vPC clustering",
            "  03_post_transform_edges.json— Edges after vPC transformation",
            "  04_final_map_data.json      — Exact nodes+edges fed into HTML/Vis.js",
            "  05_vpc_domain_summary.txt   — This file: human-readable domain overview",
            "",
            "── NODE INVENTORY ────────────────────────────────────────────────────",
        ]
        for n in nodes_json:
            nid = n.get("id", "?")
            group = n.get("group", "?")
            is_vpc = nid.startswith("VPC_Domain_")
            members = n.get("vpc_members", [])
            ps = n.get("port_stats", {})
            scanned = "✓ Scanned" if n.get("is_scanned") else "○ Discovered"
            if is_vpc:
                lines5.append(f"  [VPC DOMAIN] {nid}")
                lines5.append(f"             Members: {', '.join(members)}")
            else:
                lines5.append(f"  [{group.upper():12}] {nid}  ({scanned})")
                if ps:
                    lines5.append(f"             Ports: {ps.get('up',0)} UP / {ps.get('down',0)} DOWN / {ps.get('err',0)} ERR")

        lines5 += [
            "",
            "── VPC DOMAIN ANALYSIS ───────────────────────────────────────────────",
        ]
        if vpc_domains_used:
            for did, members in vpc_domains_used.items():
                lines5.append(f"  Domain {did}: {' ↔ '.join(members)}")
                # Summarize edges
                peer_links = [e for e in final_edges if e.get("type") == "vpc-peer-link" and set([e["from"], e["to"]]).issubset(set(members))]
                shared_edges = [e for e in final_edges if e.get("type") == "vpc_shared"]
                orphan_edges = [e for e in final_edges if e.get("type") == "vpc_orphan"]
                lines5.append(f"  Peer-Links : {len(peer_links)}")
                lines5.append(f"  Shared (Dual-Homed) Downstream: {len(shared_edges)}")
                lines5.append(f"  Orphan (Single-Homed) Downstream: {len(orphan_edges)}")
                lines5.append("")
                # Per shared edge breakdown
                for se in shared_edges:
                    downstream = se.get("to") if se.get("from", "").startswith("VPC_Domain_") else se.get("from")
                    lines5.append(f"    SHARED → {downstream}  [{se.get('label', '')}]")
                    for bl in se.get("bundled_links", []):
                        sw = bl.get("from", "?")
                        fp = bl.get("f_port", "?")
                        tp = bl.get("t_port", "?")
                        st = bl.get("f_int_data", {}).get("status", "?")
                        spd = bl.get("f_int_data", {}).get("speed", "")
                        lines5.append(f"      {sw} [{fp}] → {downstream} [{tp}]  status={st}  speed={spd}")
                for oe in orphan_edges:
                    downstream = oe.get("to") if oe.get("from", "").startswith("VPC_Domain_") else oe.get("from")
                    lines5.append(f"    ORPHAN → {downstream}  [{oe.get('label', '')}]  ⚠ NOT REDUNDANT")
        else:
            lines5.append("  No vPC domains detected in this map.")

        lines5 += [
            "",
            "── HOW TO USE THESE FILES FOR DEBUGGING ─────────────────────────────",
            "  PROBLEM: Map shows wrong/missing nodes",
            "    → Check FILE 01 to see if the device was collected",
            "  PROBLEM: Interfaces not showing in side panel",
            "    → Check FILE 04 → nodes → find the device → check 'interfaces' key",
            "  PROBLEM: vPC port correlation shows 'No vPC member ports'",
            "    → Check FILE 03 → edges_by_type → vpc_shared → check bundled_links",
            "    → Each bundled_link must have: from (switch name), f_port, t_port",
            "  PROBLEM: vPC table shows 'No structured data'",
            "    → Check FILE 01 → devices → <switch> → vpc_structured",
            "    → This data comes from 'show vpc' command on NX-OS",
            "=" * 70,
        ]
        with open(f5_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines5))

        # ── FILE 6: Pre-render presentation payload (matches HTML sidebar) ───
        f6_path = os.path.join(diag_folder, "06_pre_render_presentation.json")
        presentation = _build_html_presentation_payload(nodes_json, edges_json, map_mode)
        presentation["_meta"] = {
            "generated_at": diag_ts,
            "stage": "pre_render",
            "html_file": os.path.basename(html_file),
            "diagnostic_folder": diag_folder,
        }
        with open(f6_path, "w", encoding="utf-8") as f:
            json.dump(presentation, f, indent=2, default=str)

        # ── Editable template (copy for manual/lab data injection) ───────────
        template_path = os.path.join(diag_folder, "vpc_map_data_TEMPLATE.json")
        template_doc = {
            "_README": (
                "VPC MAP DATA TEMPLATE — fill in real network values, then merge into a map run.\n"
                "Each member switch needs entries under member_interfaces_by_switch.\n"
                "Downstream correlation uses graph_edges[].bundled_links for physical ports."
            ),
            "_instructions": [
                "1. Set domain_id and members under vpc_domains",
                "2. For each switch, add entries with vpc_id, port_channel, member_interfaces[]",
                "3. Add graph_edges with type vpc_shared and bundled_links per switch",
                "4. Use 06_pre_render_presentation.json from a good run as reference"
            ],
            "map_mode": "vpc",
            "vpc_domains": [
                {
                    "domain_id": "10",
                    "members": ["N9K-SW1", "N9K-SW2"],
                    "health": {"health_score": 100, "health_label": "HEALTHY"}
                }
            ],
            "member_interfaces_by_switch": {
                "N9K-SW1": {
                    "switch": "N9K-SW1",
                    "entries": [
                        {
                            "vpc_id": "10",
                            "port_channel": "Po10",
                            "status": "up",
                            "consistency": "success",
                            "member_interfaces": ["Eth1/10"],
                            "source": "manual"
                        }
                    ]
                },
                "N9K-SW2": {
                    "switch": "N9K-SW2",
                    "entries": []
                }
            },
            "consistency_tables": [],
            "graph_edges": []
        }
        with open(template_path, "w", encoding="utf-8") as f:
            json.dump(template_doc, f, indent=2, default=str)

        log(f"[MAP-PIPELINE] Phase 4.9: Diagnostic dump complete — {diag_folder}")
        log(f"[MAP-PIPELINE] Phase 4.9: Files: 00_README.txt, 01-06 JSON/TXT, vpc_map_data_TEMPLATE.json")

    except Exception as diag_e:
        log(f"[MAP-PIPELINE] WARNING Phase 4.9: Diagnostic dump failed (non-critical): {diag_e}")
        # Diagnostic failure must NEVER crash the map generation

    board_payload_json = None
    presentation_json = None
    if map_mode == 'vpc':
        nodes_json = _dedupe_nodes_json(nodes_json)
        _assign_vpc_fixed_positions(nodes_json, edges_json)
        presentation = _build_html_presentation_payload(nodes_json, edges_json, map_mode)
        board_payload_json = json.dumps(presentation.get('board_sections') or {})
        presentation_json = json.dumps(presentation)
        nd = len(presentation.get('vpc_domains') or [])
        log(f"[VPC_MAP] domains={nd} nodes={len(nodes_json)} edges={len(final_edges)}")

    # Phase 5: HTML Generation
    log("[MAP-PIPELINE] Phase 5: Generating HTML...")
    try:
        overlay_src = None
        if map_mode == 'all':
            try:
                from utils.utilization_overlay import resolve_replay_overlay_source
                overlay_src = resolve_replay_overlay_source(html_file=html_file)
                if overlay_src:
                    log("[UTIL-OVERLAY] overlay JSON resolved (paint only; not topology; not SNMP)")
            except Exception as _ov_ex:
                log(f"[UTIL-OVERLAY] replay resolve skipped: {_ov_ex}")
        report_formatter.generate_topology_html(
            html_file, len(uniq_nodes), len(final_edges),
            json.dumps(nodes_json), json.dumps(edges_json), vis_js_content,
            extra_header=extra_header,
            map_mode=map_mode,
            board_payload_json=board_payload_json,
            presentation_json=presentation_json,
            briefing_extra={
                'failed_hosts': len(failed_hosts),
                'truncated': devices_truncated,
                'trust_verified': trust_summary.get('verified_edges', 0),
                'trust_bidirectional': trust_summary.get('bidirectional_edges', 0),
                'trust_alerts': len(trust_summary.get('trust_alerts', [])),
            },
            utilization_overlay=overlay_src,
        )
        log(f"[MAP-PIPELINE] Phase 5 complete: HTML file created: {html_file}")

        # ── FILE 7: Post-render manifest ─────────────────────────────────────
        try:
            f7_path = os.path.join(diag_folder, "07_post_render_manifest.json")
            manifest = {
                "_README": (
                    "Post-render manifest — confirms HTML was written and summarizes final counts.\n"
                    "Compare with 06_pre_render_presentation.json to find render-time gaps."
                ),
                "_meta": {
                    "generated_at": datetime.now().strftime("%Y%m%d_%H%M%S"),
                    "stage": "post_render",
                    "html_file": html_file,
                    "html_exists": os.path.isfile(html_file),
                    "html_size_bytes": os.path.getsize(html_file) if os.path.isfile(html_file) else 0,
                    "node_count": len(nodes_json),
                    "edge_count": len(edges_json),
                    "vpc_domain_nodes": sum(1 for n in nodes_json if str(n.get('id', '')).startswith('VPC_Domain_')),
                    "vpc_adjacency_fallback": vpc_adjacency_fallback,
                    "devices_requested": devices_requested,
                    "devices_scanned": len(devices),
                    "devices_truncated": devices_truncated,
                    "devices_skipped_hosts": devices_skipped_hosts,
                    "parallel_workers": parallel_workers,
                    "failed_hosts": failed_hosts,
                },
                "presentation_summary": _build_html_presentation_payload(nodes_json, edges_json, map_mode),
            }
            with open(f7_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, default=str)
            log(f"[MAP-PIPELINE] Phase 5.1: Post-render manifest: {f7_path}")
            if failed_hosts:
                fh_path = os.path.join(diag_folder, "failed_hosts.txt")
                with open(fh_path, "w", encoding="utf-8") as ff:
                    ff.write("FAILED HOSTS — topology CDP/LLDP collection\n")
                    ff.write(f"Generated: {datetime.now().isoformat()}\n")
                    ff.write("=" * 50 + "\n\n")
                    for r in results:
                        if r.get("status") == "success":
                            continue
                        h = r.get("device") or r.get("host") or "?"
                        ff.write(f"{h}\t{r.get('error', 'Unknown error')}\n")
                log(f"[MAP-PIPELINE] failed_hosts.txt written ({len(failed_hosts)} host(s))")
        except Exception as man_e:
            log(f"[MAP-PIPELINE] WARNING Phase 5.1: Post-render manifest failed: {man_e}")

    except Exception as e:
        log(f"[MAP-PIPELINE] ERROR Phase 5: HTML generation failed: {str(e)}")
        raise
    
    write_run_manifest(paths, {
        'html_path': html_file,
        'diag_folder': diag_folder,
        'map_mode': map_mode,
        'nodes': len(uniq_nodes),
        'edges': len(final_edges),
    })
    try:
        summary = (
            f"Topology Mapper — mode={map_mode}\n"
            f"Devices scanned: {len(devices)}\n"
            f"Nodes: {len(uniq_nodes)} | Edges: {len(final_edges)}\n"
            f"HTML: {html_file}\n"
        )
        report_formatter.write_text_file(paths['txt_path'], summary)
        log(f"[Output] Topology TXT summary: {paths['txt_path']}")
    except OSError:
        pass
    log(f"--- Topology Graph Generated: {html_file} ---")
    try:
        import json as _json
        vpc_domain_count = sum(
            1 for n in nodes_json if str(n.get('id', '')).startswith('VPC_Domain_')
        ) if map_mode == 'vpc' else 0
        ready = {
            "status": "complete",
            "map_mode": map_mode,
            "html_path": html_file,
            "diag_folder": diag_folder,
            "nodes": len(uniq_nodes),
            "edges": len(final_edges),
            "vpc_domains": vpc_domain_count,
            "vpc_adjacency_fallback": vpc_adjacency_fallback,
        }
        log(f"[TOPOLOGY_READY] {_json.dumps(ready)}")
    except Exception:
        log(f"[TOPOLOGY_READY] status=complete map_mode={map_mode} html={html_file}")
    return results, html_file


def run_node_interface_topology(devices, user, pwd, enb_pwd, log):
    """
    Per-node interface map with color-coded Vis.js output.

    v6.2.0 Interface Map Improvements (network engineer perspective):
      - Summary stats bar: total / up / down / err-disabled / MAC-occupied counts
      - Speed & duplex displayed on each port node
      - VLAN assignment shown per port
      - Grouped layout: connected ports clustered near center, down ports outer ring
      - Search/filter box to find ports by name, description, VLAN, or MAC
      - Color-coded by status + occupancy (5 distinct states)
      - Port count badge on central switch node
    """
    import modules.node_interface_topology
    from utils import report_formatter
    from utils.mac_utils import macs_search_blob
    import re

    def natural_sort_key(s):
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

    if not devices:
        return [], None

    from utils.output_paths import CAT_NODE_INTERFACE, path_in_run, prepare_run_output, slugify, write_run_manifest
    from utils.parallel_device_pool import foreach_device_parallel, get_max_workers

    batch_label = slugify(devices[0]['host']) + (f"_plus{len(devices)-1}" if len(devices) > 1 else "")
    paths = prepare_run_output(CAT_NODE_INTERFACE, batch_label)
    log(f"\n--- Generating Port Interface Map(s) for {len(devices)} device(s) ---")
    log(f"[Output] Port map folder: {paths['run_dir']}")
    if len(devices) > 1:
        log(f"[Port Map] Multi-device: parallel SSH (max {get_max_workers()} workers) — one HTML per switch.")

    def _port_map_collect(dev, _idx):
        return dev, modules.node_interface_topology.run(dev, user, pwd, enb_pwd)

    collected = foreach_device_parallel(
        devices, _port_map_collect, log=log, label='port interface map',
    )

    all_results = []
    html_files = []

    for item in collected:
        if item is None:
            continue
        dev, res = item
        host = dev['host']
        all_results.append(res)
        if res['status'] != 'success':
            log(f"[{host}] [ERROR] {res.get('error', 'Unknown error')}")
            continue

        html_file = path_in_run(paths, f"{slugify(host)}_node_interfaces.html")
        ok, _ = _write_single_port_interface_html(res, host, html_file, paths, log)
        if ok:
            html_files.append({'host': host, 'path': html_file, 'basename': os.path.basename(html_file)})
            log(f"  [SUCCESS] Port map: {html_file}")

    if not html_files:
        return all_results, None

    if len(html_files) == 1:
        write_run_manifest(paths, {
            'html_path': html_files[0]['path'],
            'host': html_files[0]['host'],
            'device_count': 1,
        })
        return all_results, html_files[0]['path']

    index_html = path_in_run(paths, 'index.html')
    _write_port_map_index_html(index_html, html_files, paths['run_dir'])
    write_run_manifest(paths, {
        'index_html': index_html,
        'maps': html_files,
        'device_count': len(html_files),
    })
    log(f"--- Port Interface Maps: {len(html_files)} device(s) — index: {index_html} ---")
    return all_results, index_html


def _write_port_map_index_html(index_path, html_files, run_dir):
    """Index page linking per-switch port maps."""
    from html import escape
    rows = []
    for m in html_files:
        bn = escape(m['basename'])
        host = escape(m['host'])
        rows.append(
            f"<li><a href=\"{bn}\">{host}</a> "
            f"<span style=\"color:#64748b;font-size:12px;\">{bn}</span></li>"
        )
    run_dir_esc = escape(str(run_dir))
    html = (
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\">"
        "<title>Port Interface Maps</title>"
        "<style>body{font-family:Segoe UI,sans-serif;margin:40px;background:#0f172a;color:#e2e8f0;}"
        "a{color:#38bdf8;}ul{line-height:2;}</style></head><body>"
        f"<h1>Port Interface Maps</h1>"
        f"<p>{len(html_files)} switch(es) in scope · folder: {run_dir_esc}</p>"
        f"<ul>{''.join(rows)}</ul></body></html>"
    )
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html)


def _write_single_port_interface_html(res, host, html_file, paths, log):
    """Render one switch port map HTML from node_interface_topology result."""
    from utils import report_formatter
    from utils.mac_utils import macs_search_blob
    import re

    def natural_sort_key(s):
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

    try:
        true_host = res['data']['true_host']
        int_meta = res['data']['int_meta']
        interface_macs = res['data']['interface_macs']
        sorted_interfaces = sorted(int_meta.keys(), key=natural_sort_key)

        # ── Summary stats ─────────────────────────────────────────────────────
        total_ports = len(sorted_interfaces)
        up_ports = sum(1 for m in int_meta.values() if m.get('op_status') in ('up', 'connected'))
        down_ports = sum(1 for m in int_meta.values() if m.get('op_status') == 'down')
        err_ports = sum(1 for m in int_meta.values() if m.get('op_status') == 'err-disabled')
        mac_ports = sum(1 for p in sorted_interfaces if interface_macs.get(p))
        unused_ports = total_ports - up_ports - down_ports - err_ports

        # ── Central switch node ───────────────────────────────────────────────
        switch_tooltip = (
            f"<div style='padding:12px; font-family:sans-serif; min-width:280px;'>"
            f"<b style='font-size:15px;'>\U0001f5a5\ufe0f {true_host}</b>"
            f"<div style='margin:10px 0; display:grid; grid-template-columns:1fr 1fr; gap:6px;'>"
            f"<div style='background:#27ae60; color:white; padding:6px 10px; border-radius:8px; text-align:center;'>"
            f"<div style='font-size:18px; font-weight:700;'>{up_ports}</div>"
            f"<div style='font-size:10px;'>Up / Connected</div></div>"
            f"<div style='background:#e74c3c; color:white; padding:6px 10px; border-radius:8px; text-align:center;'>"
            f"<div style='font-size:18px; font-weight:700;'>{down_ports}</div>"
            f"<div style='font-size:10px;'>Down</div></div>"
            f"<div style='background:#f39c12; color:white; padding:6px 10px; border-radius:8px; text-align:center;'>"
            f"<div style='font-size:18px; font-weight:700;'>{err_ports}</div>"
            f"<div style='font-size:10px;'>Err-Disabled</div></div>"
            f"<div style='background:#1abc9c; color:white; padding:6px 10px; border-radius:8px; text-align:center;'>"
            f"<div style='font-size:18px; font-weight:700;'>{mac_ports}</div>"
            f"<div style='font-size:10px;'>MAC Learned</div></div>"
            f"</div>"
            f"<div style='font-size:11px; color:#7f8c8d; text-align:center;'>Total: {total_ports} ports</div>"
            f"</div>"
        )

        nodes_json = [{
            "id": "switch",
            "label": f"{true_host}\n{up_ports}\u2191 {down_ports}\u2193 {err_ports}\u26a0",
            "shape": "box", "size": 40,
            "color": {"background": "#2c3e50", "border": "#1a252f"},
            "font": {"size": 16, "color": "white", "face": "Segoe UI Bold"},
            "title": switch_tooltip,
            "shadow": True, "borderWidth": 3,
            "group": "switch"
        }]
        edges_json = []

        for pname in sorted_interfaces:
            meta = int_meta[pname]
            p_macs = list(set(interface_macs.get(pname, [])))
            has_macs = len(p_macs) > 0
            is_connected = meta['op_status'] in ['up', 'connected']
            is_err = meta['op_status'] == 'err-disabled'
            is_admin_down = meta['admin_status'] == 'down'
            is_configured = meta.get('desc') and meta.get('desc') != '-'
            speed = meta.get('speed', '')
            duplex = meta.get('duplex', '')
            vlan = meta.get('vlan', '')

            # ── Color coding (5 states) ───────────────────────────────────────
            if is_err:
                node_color = {"background": "#c0392b", "border": "#96281b"}
                group = "err"
            elif is_admin_down:
                node_color = {"background": "#7f8c8d", "border": "#636e72"}
                group = "admin_down"
            elif is_connected and has_macs:
                node_color = {"background": "#1abc9c", "border": "#16a085"}
                group = "occupied"
            elif is_connected:
                node_color = {"background": "#2ecc71", "border": "#27ae60"}
                group = "connected"
            elif is_configured and not is_connected:
                node_color = {"background": "#e67e22", "border": "#d35400"}
                group = "configured_down"
            else:
                node_color = {"background": "#ecf0f1", "border": "#bdc3c7"}
                group = "unused"

            # ── Node label: port name + speed ─────────────────────────────────
            label_parts = [pname]
            if speed:
                label_parts.append(speed)
            if has_macs:
                label_parts.append("\U0001f3f4")
            node_label = "\n".join(label_parts)

            # ── MAC display ───────────────────────────────────────────────────
            mac_display = "<ul style='margin:5px 0; padding-left:15px; font-size:11px;'>"
            if len(p_macs) > 3:
                for mm in p_macs[:3]:
                    mac_display += f"<li style='font-family:monospace;'>{mm}</li>"
                mac_display += (
                    f"<li style='color:#e67e22; font-weight:bold;'>"
                    f"\u26a0\ufe0f +{len(p_macs)-3} more MACs (possible hub/AP)</li>"
                )
            elif has_macs:
                for mm in p_macs:
                    mac_display += f"<li style='font-family:monospace;'>{mm}</li>"
            else:
                mac_display += "<li style='color:#95a5a6;'>No MACs learned</li>"
            mac_display += "</ul>"

            # ── Status badges ─────────────────────────────────────────────────
            admin_cls = (
                "background:#e8f5e9; color:#2e7d32;"
                if meta['admin_status'] == 'up'
                else "background:#fbe9e7; color:#c62828;"
            )
            op_cls = (
                "background:#e8f5e9; color:#2e7d32;"
                if is_connected
                else "background:#fbe9e7; color:#c62828;"
            )
            if is_err:
                op_cls = "background:#c0392b; color:white;"

            # ── Tooltip ───────────────────────────────────────────────────────
            tooltip_rows = ""
            if speed or duplex:
                tooltip_rows += (
                    f"<tr><td style='color:#7f8c8d; padding:3px 8px 3px 0;'>Speed/Duplex:</td>"
                    f"<td style='font-weight:600; color:#2c3e50;'>"
                    f"{speed}{' / ' + duplex if duplex else ''}</td></tr>"
                )
            if vlan:
                tooltip_rows += (
                    f"<tr><td style='color:#7f8c8d; padding:3px 8px 3px 0;'>VLAN:</td>"
                    f"<td style='font-weight:600; color:#8e44ad;'>{vlan}</td></tr>"
                )
            if meta.get('desc') and meta.get('desc') != '-':
                tooltip_rows += (
                    f"<tr><td style='color:#7f8c8d; padding:3px 8px 3px 0;'>Description:</td>"
                    f"<td style='font-style:italic; color:#555;'>{meta['desc']}</td></tr>"
                )
            
            # v6.7.5: Traffic statistics display
            in_rate = meta.get('input_rate', 0)
            out_rate = meta.get('output_rate', 0)
            if in_rate or out_rate:
                def fmt_rate(bps):
                    if bps >= 1_000_000_000:
                        return f"{bps/1_000_000_000:.1f} Gbps"
                    elif bps >= 1_000_000:
                        return f"{bps/1_000_000:.1f} Mbps"
                    elif bps >= 1_000:
                        return f"{bps/1_000:.1f} Kbps"
                    else:
                        return f"{bps} bps"
                
                tooltip_rows += (
                    f"<tr><td style='color:#7f8c8d; padding:3px 8px 3px 0;'>Traffic:</td>"
                    f"<td style='font-weight:600; color:#2980b9;'>↓{fmt_rate(in_rate)} ↑{fmt_rate(out_rate)}</td></tr>"
                )

            tooltip = (
                f"<div style='min-width:280px; font-family:Segoe UI,sans-serif; padding:12px; background:white;'>"
                f"<div style='display:flex; justify-content:space-between; align-items:center;'>"
                f"<b style='font-size:14px; color:#2c3e50;'>{pname}</b>"
                f"<div style='display:flex; gap:4px;'>"
                f"<span style='font-size:9px; {admin_cls} padding:2px 6px; border-radius:10px;'>"
                f"Admin: {meta['admin_status'].upper()}</span>"
                f"<span style='font-size:9px; {op_cls} padding:2px 6px; border-radius:10px;'>"
                f"Link: {meta['op_status'].upper()}</span>"
                f"</div></div>"
                f"<table style='margin-top:8px; font-size:11px; width:100%;'>{tooltip_rows}</table>"
                f"<hr style='margin:8px 0; border:0; border-top:1px solid #eee;'>"
                f"<b style='font-size:11px; color:#2c3e50;'>\U0001f4bb Connected Clients:</b>"
                f"{mac_display}</div>"
            )

            nodes_json.append({
                "id": pname,
                "label": node_label,
                "shape": "dot",
                "size": 20 if is_connected else 14,
                "color": node_color,
                "title": tooltip,
                "font": {"size": 11, "color": "#2c3e50", "face": "Segoe UI"},
                "borderWidth": 2,
                "shadow": is_connected,
                "group": group,
                # Store searchable metadata for JS filter (incl. format-agnostic MAC)
                "desc": meta.get('desc', ''),
                "vlan": vlan,
                "speed": speed,
                "macs": p_macs,
                "macs_search": macs_search_blob(p_macs),
            })

            # Edge color matches port status
            edge_color = "#27ae60" if is_connected else ("#e74c3c" if is_err else "#bdc3c7")
            edge_width = 3 if is_connected else 1
            edges_json.append({
                "from": "switch",
                "to": pname,
                "color": {"color": edge_color, "highlight": "#3498db"},
                "width": edge_width,
                "length": 200 if is_connected else 280,
                "smooth": {"type": "dynamic"},
                "dashes": not is_connected,
            })

        vis_js_content = _load_vis_js(log)
        report_formatter.generate_node_interface_html(
            html_file, true_host, nodes_json, edges_json, vis_js_content,
            stats={
                "total": total_ports, "up": up_ports, "down": down_ports,
                "err": err_ports, "mac": mac_ports, "unused": unused_ports
            }
        )
        log(f"--- Node Interface Topology Generated: {html_file} ---")
        return True, html_file
    except Exception as e:
        import traceback
        log(f"[{host}] [ERROR] {str(e)}\n{traceback.format_exc()}")
        return False, None


# =============================================================================
# V6.0 GENERIC PLUGIN ORCHESTRATOR
# =============================================================================

def run_generic_plugin(plugin_id, devices, user, pwd, enb_pwd, params, log_func, config=None, vault_extras=None):
    """
    The universal orchestrator for ALL v6.0 plugins.
    
    This function replaces hard-coded dispatch logic with dynamic plugin execution.
    It uses the PluginRegistry to discover and execute plugins in parallel.
    
    Args:
        plugin_id: The plugin identifier (e.g., 'vlan_audit', 'mac_trace')
        devices: List of device dicts [{'host': '...', 'device_type': '...'}]
        user: SSH username
        pwd: SSH password
        enb_pwd: Enable/secret password
        params: Plugin-specific parameters dict
        log_func: Callable for UI logging
        config: Optional global config dict
    
    Returns:
        List of result dicts, one per device
    """
    from modules.plugin_registry import get_registry
    
    if config is None:
        config = {
            'timeout': 30,
            'max_retries': 3,
            'log_level': 'INFO',
            'parallel_workers': 10
        }
    
    registry = get_registry()
    
    # Check if plugin exists
    if not registry.exists(plugin_id):
        log_func(f"[ERROR] Plugin '{plugin_id}' not found in registry")
        return [{'status': 'fail', 'error': f"Plugin '{plugin_id}' not found"} for _ in devices]
    
    plugin = registry.get_plugin(plugin_id)
    metadata = plugin['metadata']
    
    log_func(f"\n--- Starting {metadata['display_name']} ---")
    log_func(f"[System] Executing plugin '{plugin_id}' on {len(devices)} device(s)...")
    
    # Build credentials dict
    credentials = {
        'username': user,
        'password': pwd,
        'secret': enb_pwd if enb_pwd else None,
    }
    if vault_extras:
        from utils.collection_credentials import bundle_for_plugin
        credentials = bundle_for_plugin(vault_extras)
        if enb_pwd:
            credentials['secret'] = enb_pwd
    
    # Execute with parallel support if plugin allows
    if metadata.get('supports_parallel', True):
        results = registry.execute_parallel(
            plugin_id, devices, credentials, params, config, 
            log_func, max_workers=config.get('parallel_workers', 10)
        )
    else:
        # Sequential execution
        results = []
        for device in devices:
            result = registry.execute(plugin_id, device, credentials, params, config, log_func)
            results.append(result)
    
    # Summarize results
    success_count = sum(1 for r in results if r.get('status') == 'success')
    fail_count = len(results) - success_count
    
    log_func(f"\n[Summary] Completed: {success_count} success, {fail_count} failed")
    log_func(f"--- {metadata['display_name']} Complete ---")
    
    return results


def run_l3_topology_mapper(devices, user, pwd, enb_pwd, log, map_kind='l3'):
    """Collect routing tables from inventory devices and build offline L3/Flow HTML map."""
    from utils.output_paths import (
        CAT_L3_TOPOLOGY, CAT_FLOW_MAP, path_in_run, prepare_run_output, slugify, write_run_manifest,
    )
    from utils.parallel_device_pool import foreach_device_parallel, get_max_workers
    from modules.l3_topology_runner import (
        collect_device_routing,
        build_l3_topology_bundle,
        build_flow_topology_bundle,
        write_l3_diagnostics,
    )
    from utils.l3_map_formatter import l3_bundle_to_vis, flow_bundle_to_vis
    from utils.l3_map_shell_enhanced import render_l3_map_html_enhanced

    cat = CAT_FLOW_MAP if map_kind == 'flow' else CAT_L3_TOPOLOGY
    paths = prepare_run_output(cat, slugify(map_kind))
    run_dir = paths['run_dir']
    html_file = path_in_run(paths, f'{map_kind}_routing_map.html')

    log(f"\n--- L3 Cartography ({map_kind.upper()}) — SSH routing collection ---")
    log(f"[L3-MAP] Output folder: {run_dir}")

    devices_requested = len(devices)
    devices_truncated = False
    devices_skipped_hosts = []
    if len(devices) > 150:
        devices_skipped_hosts = [str(d.get('host', d.get('ip', '?'))) for d in devices[150:]]
        log(f"[WARNING] L3 map limited to 150 devices (truncating from {devices_requested}).")
        devices_truncated = True
        devices = devices[:150]

    parallel_workers = get_max_workers()
    results = []

    def _collect_l3(dev, _idx):
        host = dev.get('host') or dev.get('ip') or '?'
        return host, collect_device_routing(dev, user, pwd, enb_pwd, log=log)

    collected = foreach_device_parallel(
        devices, _collect_l3, log=log, max_workers=parallel_workers,
        label=f'L3 routing collection ({map_kind})',
    )

    failed_hosts = []
    for item in collected:
        if item is None:
            continue
        host, res = item
        results.append(res)
        if res.get('status') != 'success':
            failed_hosts.append(res.get('true_host') or host)

    l3_bundle = build_l3_topology_bundle(results)
    l3_bundle['failed_hosts'] = list(set(failed_hosts + (l3_bundle.get('failed_hosts') or [])))
    l3_bundle['devices_truncated'] = devices_truncated
    l3_bundle['devices_requested'] = devices_requested
    l3_bundle['devices_skipped_hosts'] = devices_skipped_hosts

    if map_kind == 'flow':
        flow_bundle = build_flow_topology_bundle(l3_bundle)
        flow_bundle['failed_hosts'] = l3_bundle['failed_hosts']
        vis_payload = flow_bundle_to_vis(flow_bundle)
        title = 'Network Flow Map'
        subtitle = 'Gateway & inter-subnet logical flows (Netdisco-inspired)'
        write_l3_diagnostics(run_dir, {**flow_bundle, 'route_count': l3_bundle.get('route_count', 0)}, map_kind='flow')
    else:
        vis_payload = l3_bundle_to_vis(l3_bundle)
        title = 'L3 Routing Map'
        subtitle = 'Routing tables · gateways · subnets (SSH, offline)'
        write_l3_diagnostics(run_dir, l3_bundle, map_kind='l3')

    html_content = render_l3_map_html_enhanced(vis_payload, title=title, subtitle=subtitle, map_kind=map_kind)
    with open(html_file, 'w', encoding='utf-8') as hf:
        hf.write(html_content)

    ok = sum(1 for r in results if r.get('status') == 'success')
    log(f"[SUCCESS] {map_kind.upper()} map written: {html_file}")
    log(f"[L3-MAP] {ok}/{len(results)} devices OK · {vis_payload.get('route_count', 0)} routes")

    write_run_manifest(paths, {
        'feature': map_kind,
        'devices_scanned': len(results),
        'devices_ok': ok,
        'html': os.path.basename(html_file),
        'route_count': vis_payload.get('route_count', 0),
    })

    meta = {
        'html_path': html_file,
        'diag_folder': run_dir,
        'devices_scanned': len(results),
        'devices_ok': ok,
        'failed_hosts': l3_bundle['failed_hosts'],
        'node_count': len(vis_payload.get('nodes') or []),
        'edge_count': len(vis_payload.get('edges') or []),
        'route_count': vis_payload.get('route_count', 0),
        'map_kind': map_kind,
        'devices_truncated': devices_truncated,
        'devices_requested': devices_requested,
        'devices_skipped_hosts': devices_skipped_hosts,
        'parallel_workers': parallel_workers,
    }
    return results, html_file, meta


def run_failure_correlation_mapper(devices, user, pwd, enb_pwd, log):
    """SSH log + interface/vPC correlation → offline HTML explanation pack."""
    from utils.output_paths import (
        CAT_FAILURE_CORRELATION,
        path_in_run,
        prepare_run_output,
        write_run_manifest,
    )
    from modules.failure_correlation import run_failure_correlation

    paths = prepare_run_output(CAT_FAILURE_CORRELATION, 'fleet')
    run_dir = paths['run_dir']
    log(f"\n--- Failure Correlation Engine — SSH evidence collection ---")
    log(f"[CORR] Output folder: {run_dir}")
    bundle = run_failure_correlation(devices, user, pwd, enb_pwd, log, run_dir)
    html_file = bundle.get('html_path') or path_in_run(paths, 'failure_correlation.html')
    hyp = (bundle.get('rollups') or {}).get('hypothesis_count', 0)
    log(f"[SUCCESS] Correlation report: {html_file} · {hyp} hypotheses")
    write_run_manifest(paths, {
        'feature': 'failure_correlation',
        'devices_scanned': len(devices),
        'hypothesis_count': hyp,
        'html': os.path.basename(html_file) if html_file else '',
    })
    return bundle, html_file


def run_advanced_l2_map(devices, user, pwd, enb_pwd, log, enable_l3_correlation=True):
    """
    Enriched L2 map (Secure Cartography style) from CDP/LLDP neighbor collection
    with optional L3 routing correlation.
    
    Parameters
    ----------
    enable_l3_correlation : bool
        If True, collects L3 routing data and creates combined L2+L3 view
    """
    import modules.topology_mapper
    from modules.l3_topology_runner import collect_device_routing
    from utils.output_paths import CAT_ADVANCED_L2, path_in_run, prepare_run_output, slugify, write_run_manifest
    from utils.parallel_device_pool import foreach_device_parallel, get_max_workers
    from modules.discovery.advanced_mapper import AdvancedMapper
    from utils.l3_map_shell import render_l3_map_html
    from utils.l3_map_formatter import flow_bundle_to_vis
    from utils.combined_l2l3_shell import render_combined_l2l3_html

    paths = prepare_run_output(CAT_ADVANCED_L2, slugify('advanced_l2'))
    run_dir = paths['run_dir']
    html_file = path_in_run(paths, 'advanced_l2_map.html')

    log("\n--- Advanced L2 Map (Secure Cartography style) — CDP/LLDP enrichment ---")
    if enable_l3_correlation:
        log("[ADV-L2] L3 routing correlation ENABLED")
    log(f"[ADV-L2] Output folder: {run_dir}")

    if len(devices) > 150:
        log(f"[WARNING] Advanced L2 limited to 150 devices (from {len(devices)}).")
        devices = devices[:150]

    parallel_workers = get_max_workers()
    results = []
    enriched_devices = []

    def _collect_neighbors(dev, _idx):
        host = dev['host']
        return host, modules.topology_mapper.run(dev, user, pwd, enb_pwd, log)

    collected = foreach_device_parallel(
        devices, _collect_neighbors, log=log, max_workers=parallel_workers,
        label='Advanced L2 CDP/LLDP collection',
    )

    device_by_host = {d.get('host'): d for d in devices}

    for item in collected:
        if item is None:
            continue
        host, res = item
        results.append(res)
        if res.get('status') != 'success':
            continue
        data = res.get('data') or {}
        true_host = data.get('true_host') or host
        dev_info = device_by_host.get(host) or {}
        neighbors = []
        for edge in data.get('edges') or []:
            neighbors.append({
                'ip': edge.get('remote_host') or edge.get('to') or '',
                'local_port': edge.get('local_port') or '',
                'remote_port': edge.get('remote_port') or '',
                'protocol': edge.get('protocol') or 'CDP/LLDP',
            })
        enriched_devices.append({
            'ip': host,
            'hostname': true_host,
            'device_type': dev_info.get('device_type') or '',
            'neighbors': neighbors,
        })

    mapper = AdvancedMapper()
    
    # If L3 correlation is enabled, collect routing data and build combined map
    if enable_l3_correlation:
        log("[ADV-L2] Collecting L3 routing data for correlation...")
        l3_results = []
        l3_devices = []
        
        def _collect_routing(dev, _idx):
            return collect_device_routing(dev, user, pwd, enb_pwd, log)
        
        l3_collected = foreach_device_parallel(
            devices, _collect_routing, log=log, max_workers=parallel_workers,
            label='L3 routing collection for correlation',
        )
        
        for l3_res in l3_collected:
            if l3_res and l3_res.get('status') in ('success', 'partial'):
                hostname = l3_res.get('true_host') or l3_res.get('host')
                l3_devices.append({
                    'hostname': hostname,
                    'routes': l3_res.get('routes_normalized') or [],
                })
                l3_results.append(l3_res)
        
        log(f"[ADV-L2] L3 data collected from {len(l3_devices)} devices")
        
        # Build combined L2+L3 map
        combined_model = mapper.build_combined_l2l3_map(enriched_devices, l3_devices)
        
        # Render combined view
        html_content = render_combined_l2l3_html(
            combined_model,
            title='Combined L2+L3 Topology',
            subtitle='Physical (CDP/LLDP) + Logical (Routing) correlation',
            map_kind='combined',
        )
        
        # Also save L2-only view for comparison
        l2_model = mapper.build_l2_map(enriched_devices)
        l2_vis_payload = flow_bundle_to_vis({
            'nodes': [{'id': n['id'], 'label': n['label'], 'group': n.get('group', 'switch'), 'title': n.get('platform', '')} for n in l2_model['nodes']],
            'edges': l2_model['edges'],
            'device_count': l2_model.get('node_count', 0),
            'gateway_count': 0,
            'subnet_count': 0,
        })
        l2_html_file = path_in_run(paths, 'l2_only_map.html')
        l2_html_content = render_l3_map_html(
            l2_vis_payload,
            title='L2 Physical Topology Only',
            subtitle='CDP/LLDP adjacency (no L3 correlation)',
            map_kind='l2',
        )
        with open(l2_html_file, 'w', encoding='utf-8') as hf:
            hf.write(l2_html_content)
        log(f"[ADV-L2] L2-only view saved: {l2_html_file}")
        
        analysis = combined_model.get('analysis', {})
        meta = {
            'html_path': html_file,
            'l2_only_path': l2_html_file,
            'diag_folder': run_dir,
            'devices_scanned': len(results),
            'devices_ok': sum(1 for r in results if r.get('status') == 'success'),
            'l3_devices_scanned': len(l3_results),
            'l3_devices_ok': sum(1 for r in l3_results if r.get('status') == 'success'),
            'node_count': analysis.get('total_nodes', 0),
            'edge_count': analysis.get('total_edges', 0),
            'l2_edge_count': analysis.get('l2_edge_count', 0),
            'l3_edge_count': analysis.get('l3_edge_count', 0),
            'correlated_edges': analysis.get('correlated_edges', 0),
            'gateway_count': analysis.get('gateway_count', 0),
            'map_kind': 'combined_l2l3',
            'failed_hosts': [r.get('host') for r in results if r.get('status') != 'success'],
            'l3_failed_hosts': [r.get('host') for r in l3_results if r.get('status') not in ('success', 'partial')],
        }
    else:
        # Original L2-only behavior
        l2_model = mapper.build_l2_map(enriched_devices)
        vis_payload = flow_bundle_to_vis({
            'nodes': [{'id': n['id'], 'label': n['label'], 'group': n.get('group', 'switch'), 'title': n.get('platform', '')} for n in l2_model['nodes']],
            'edges': l2_model['edges'],
            'device_count': l2_model.get('node_count', 0),
            'gateway_count': 0,
            'subnet_count': 0,
        })
        html_content = render_l3_map_html(
            vis_payload,
            title='Advanced L2 Map',
            subtitle='CDP/LLDP enriched adjacency (Secure Cartography inspired)',
            map_kind='l2',
        )
        
        meta = {
            'html_path': html_file,
            'diag_folder': run_dir,
            'devices_scanned': len(results),
            'devices_ok': sum(1 for r in results if r.get('status') == 'success'),
            'node_count': l2_model.get('node_count', 0),
            'edge_count': l2_model.get('edge_count', 0),
            'map_kind': 'advanced_l2',
            'failed_hosts': [r.get('host') for r in results if r.get('status') != 'success'],
        }
    
    with open(html_file, 'w', encoding='utf-8') as hf:
        hf.write(html_content)

    ok = sum(1 for r in results if r.get('status') == 'success')
    log(f"[SUCCESS] Advanced L2 map: {html_file} ({ok}/{len(results)} devices)")
    if enable_l3_correlation:
        log(f"[SUCCESS] Combined L2+L3 correlation: {meta.get('correlated_edges', 0)} edges correlated")

    write_run_manifest(paths, {
        'feature': 'advanced_l2',
        'l3_correlation_enabled': enable_l3_correlation,
        'devices_scanned': len(results),
        'devices_ok': ok,
        'html': os.path.basename(html_file),
        'l2_only_html': os.path.basename(meta.get('l2_only_path', '')) if enable_l3_correlation else '',
    })

    return results, html_file, meta

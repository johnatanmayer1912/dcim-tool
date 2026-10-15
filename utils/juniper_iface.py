"""Juniper interface normalization — physical vs logical (unit) correlation."""
import re

# Physical / AE: ge-0/0/0, ae0, xe-…
# IRB / L3 SVI: irb.100 (common) and irb-0/0/0 (rare hyphenated form)
_JUNOS_IFACE = re.compile(
    r'^((?:ge|xe|et|fe|em|lo|vlan)-[\w./]+|irb(?:-[\w./]+|\.[\w]+)|ae\d+(?:\.[\w]+)?)\*?$',
    re.I,
)
_JUNOS_IRB = re.compile(r'^irb(?:-[\w./]+|\.[\w]+)\*?$', re.I)
_JUNOS_VLAN_IF = re.compile(r'^vlan(?:-[\w./]+|\.[\w]+)\*?$', re.I)


def split_junos_unit(name):
    """Return (physical, logical) where logical may include .0 unit suffix."""
    n = (name or '').strip().rstrip('*')
    if '.' in n:
        base, unit = n.rsplit('.', 1)
        if unit.isdigit():
            return base, n
    return n, n


def is_junos_interface(name):
    return bool(_JUNOS_IFACE.match((name or '').strip().rstrip('*')))


def is_junos_irb(name: str) -> bool:
    """True for Junos IRB / L3 SVI ifNames (irb.100 or irb-…)."""
    return bool(_JUNOS_IRB.match((name or '').strip().rstrip('*')))


def is_junos_vlan_l3_if(name: str) -> bool:
    """True for legacy Junos vlan.* L3 interfaces (not VLAN membership evidence)."""
    return bool(_JUNOS_VLAN_IF.match((name or '').strip().rstrip('*')))


def is_junos_irb_or_l3_svi(name: str) -> bool:
    """Routed IRB/VLAN-if — not a physical switch-switch cable attachment."""
    return is_junos_irb(name) or is_junos_vlan_l3_if(name)


def classify_junos_port_role(name: str) -> str:
    """
    Return one of: physical | ae_bundle | irb_l3 | vlan_l3 | unknown.
    Does not invent roles — unknown when the token is empty or unrecognized.
    """
    n = (name or '').strip().rstrip('*')
    if not n:
        return 'unknown'
    if is_junos_irb(n):
        return 'irb_l3'
    if is_junos_vlan_l3_if(n):
        return 'vlan_l3'
    if re.match(r'^ae\d+', n, re.I):
        return 'ae_bundle'
    if is_junos_interface(n):
        return 'physical'
    return 'unknown'


def resolve_junos_iface_key(name, int_meta_keys):
    """
    Map a MAC-table interface (often ge-0/0/0.0) to an int_meta key (ge-0/0/0).
    Returns matching key from int_meta_keys or None.
    """
    if not name or not int_meta_keys:
        return None
    physical, logical = split_junos_unit(name)
    candidates = [name.rstrip('*'), logical, physical]
    keys_lower = {k.lower(): k for k in int_meta_keys}
    for cand in candidates:
        hit = keys_lower.get(cand.lower())
        if hit:
            return hit
    for key in int_meta_keys:
        key_phys, _ = split_junos_unit(key)
        if key_phys.lower() == physical.lower():
            return key
    return None


def collect_juniper_lag_detail(conn):
    """Fetch LACP / AE bundle membership from a Junos device."""
    from modules.topology_mapper import _parse_juniper_lag_detail

    lag_detail = {}
    try:
        lag_out = conn.send_command("show lacp interfaces")
        if lag_out and "Invalid" not in lag_out and "not found" not in lag_out.lower():
            lag_detail = _parse_juniper_lag_detail(lag_out)
        if not lag_detail:
            ae_out = conn.send_command("show aggregated-ethernet detail")
            if ae_out:
                lag_detail = _parse_juniper_lag_detail(ae_out)
    except Exception:
        pass
    return lag_detail


def apply_juniper_bundles(int_meta, lag_detail):
    """
    Enrich int_meta with ae bundles and member→ae mapping.
    Returns bundles dict {physical_member: ae_name}.
    """
    bundles = {}
    if not lag_detail:
        return bundles

    for ae_id, ae_data in lag_detail.items():
        ae_key = ae_id
        members = ae_data.get('members', [])
        member_names = [m.get('intf', '') for m in members if m.get('intf')]

        if ae_key not in int_meta:
            int_meta[ae_key] = {
                "desc": f"Aggregated Ethernet ({ae_data.get('protocol', 'LACP')})",
                "op_status": "up" if members else "down",
                "admin_status": "up" if members else "down",
                "speed": "Aggregated",
                "duplex": "",
                "vlan": "",
                "interface_type": "ae_bundle",
                "ae_members": member_names,
            }
        else:
            int_meta[ae_key]["interface_type"] = "ae_bundle"
            int_meta[ae_key]["ae_members"] = member_names

        for mem in members:
            mem_intf = mem.get('intf', '')
            if not mem_intf:
                continue
            bundles[mem_intf] = ae_key
            if mem_intf in int_meta:
                int_meta[mem_intf]["ae_bundle"] = ae_key
                int_meta[mem_intf]["interface_type"] = "ae_member"

    return bundles

"""Shared MAC address normalization and vendor-specific search helpers."""
import re

_MAC_SEP = re.compile(r'[.:\-\s_]')
_MAC_HEX_ONLY = re.compile(r'^[0-9a-fA-F]+$')
_MAC_IN_LINE = re.compile(
    r'([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}'
    r'|[0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4}',
    re.I,
)
_JUNOS_IFACE = re.compile(
    r'\b((?:ge|xe|et|fe|em|lo|irb|vlan)-[\w./]+|ae\d+(?:\.[\w]+)?)\*?\b',
    re.I,
)


def normalize_mac_hex(mac):
    """Strip separators and return lowercase hex (supports partial MACs)."""
    clean = _MAC_SEP.sub('', (mac or '').strip()).lower()
    if not clean or not _MAC_HEX_ONLY.match(clean):
        raise ValueError(f"Invalid MAC address format: '{mac}'")
    return clean


def to_cisco_dotted(mac):
    """Cisco CAM tables use aabb.ccdd.eeff notation."""
    h = normalize_mac_hex(mac)
    if len(h) >= 12:
        return f"{h[0:4]}.{h[4:8]}.{h[8:12]}"
    if len(h) >= 8:
        return f"{h[0:4]}.{h[4:8]}"
    if len(h) >= 4:
        return f"{h[0:4]}"
    return h


def to_junos_colon(mac):
    """Junos ethernet-switching tables use aa:bb:cc:dd:ee:ff notation."""
    h = normalize_mac_hex(mac)
    if len(h) % 2:
        h = h  # odd length partial — pair what we can
    pairs = [h[i:i + 2] for i in range(0, len(h), 2)]
    return ':'.join(pairs)


def cisco_search_terms(mac):
    """Search tokens for 'show mac address-table | include'."""
    h = normalize_mac_hex(mac)
    terms = []
    if len(h) >= 12:
        terms.append(f"{h[0:4]}.{h[4:8]}.{h[8:12]}")
        terms.append(f"{h[4:8]}.{h[8:12]}")
        terms.append(f"{h[8:12]}")
    elif len(h) >= 8:
        terms.append(f"{h[0:4]}.{h[4:8]}")
        terms.append(h[4:8])
    elif len(h) >= 4:
        terms.append(h[0:4])
    terms.append(h)
    return list(dict.fromkeys(t for t in terms if t))


def junos_search_terms(mac):
    """Search tokens for 'show ethernet-switching table | match'."""
    h = normalize_mac_hex(mac)
    terms = []
    if len(h) >= 12:
        terms.append(':'.join(h[i:i + 2] for i in range(0, 12, 2)))
    if len(h) >= 2:
        terms.append(':'.join(h[i:i + 2] for i in range(0, len(h), 2)))
    terms.append(h)
    return list(dict.fromkeys(t for t in terms if t))


def line_contains_mac(line, mac):
    """Return True if line contains the target MAC in any common format."""
    h = normalize_mac_hex(mac)
    compact = re.sub(r'[.:\-\s]', '', line).lower()
    return h in compact


def extract_junos_interface(line):
    """Extract Junos interface name from a MAC table row."""
    m = _JUNOS_IFACE.findall(line)
    if m:
        return m[-1].rstrip('*')
    return None


def mac_in_line(line):
    return _MAC_IN_LINE.search(line or '')


def extract_macs_from_line(line: str) -> list:
    """Extract normalized MAC hex strings from a CAM/MAC table line."""
    if not line:
        return []
    found = []
    for m in _MAC_IN_LINE.finditer(line):
        raw = m.group(0)
        try:
            found.append(normalize_mac_hex(raw))
        except ValueError:
            compact = _MAC_SEP.sub('', raw).lower()
            if _MAC_HEX_ONLY.match(compact):
                found.append(compact)
    return list(dict.fromkeys(found))


def distinct_macs_matching_query(lines, query: str) -> list:
    """Return unique full MACs in lines that match a (possibly partial) query."""
    try:
        q = normalize_mac_hex(query)
    except ValueError:
        q = _MAC_SEP.sub('', (query or '')).lower()
    if not q:
        return []
    seen = set()
    for line in lines or []:
        for mac in extract_macs_from_line(line):
            if mac == q or mac.startswith(q) or q in mac:
                seen.add(mac)
        compact = _MAC_SEP.sub('', (line or '')).lower()
        if q in compact and not extract_macs_from_line(line):
            seen.add(q)
    return sorted(seen)


def is_partial_mac_query(query: str) -> bool:
    try:
        h = normalize_mac_hex(query)
    except ValueError:
        return True
    return len(h) < 12


def format_mac_for_display(mac_hex: str) -> str:
    """Format 12-char hex MAC as aa:bb:cc:dd:ee:ff for operator display."""
    h = (mac_hex or '').lower()
    if len(h) == 12:
        return ':'.join(h[i:i + 2] for i in range(0, 12, 2))
    return h


def mac_search_blob(mac: str) -> str:
    """Concatenate common MAC string forms for client-side / filter search."""
    raw = (mac or '').strip()
    if not raw:
        return ''
    try:
        h = normalize_mac_hex(raw)
    except ValueError:
        h = _MAC_SEP.sub('', raw).lower()
    if not h:
        return ''
    blobs = [h, raw.lower()]
    if len(h) >= 4:
        blobs.append(h[-4:])
        blobs.append(h[:4])
    if len(h) >= 8:
        blobs.append(f"{h[0:4]}.{h[4:8]}")
        blobs.append(h[4:8])
    if len(h) >= 12:
        dotted = f"{h[0:4]}.{h[4:8]}.{h[8:12]}"
        blobs.extend([
            dotted,
            f"{h[4:8]}.{h[8:12]}",
            h[8:12],
            ':'.join(h[i:i + 2] for i in range(0, 12, 2)),
        ])
    else:
        pairs = [h[i:i + 2] for i in range(0, len(h), 2)]
        if pairs:
            blobs.append(':'.join(pairs))
    return ' '.join(dict.fromkeys(b for b in blobs if b))


def macs_search_blob(macs) -> str:
    """Search haystack for a list of MAC addresses (all formats)."""
    return ' '.join(
        mac_search_blob(m) for m in (macs or []) if m
    ).strip()


def mac_query_matches(haystack: str, query: str) -> bool:
    """True if query matches any MAC substring in haystack (format-agnostic)."""
    q = (query or '').strip()
    if not q:
        return True
    try:
        qh = normalize_mac_hex(q)
    except ValueError:
        qh = _MAC_SEP.sub('', q).lower()
    if not qh:
        return False
    compact = _MAC_SEP.sub('', (haystack or '')).lower()
    return qh in compact


def attach_learned_macs(conn, interfaces, device_type, vendor, log_func=None):
    """
    Fetch CAM/MAC table and attach learned_macs[] per interface (IOS/NX-OS/Junos).
    """
    if not interfaces:
        return
    from modules.topology_mapper import _parse_mac_table

    dtype = (device_type or '').lower()
    if vendor == 'juniper_junos' or 'juniper' in dtype:
        mac_cmd = 'show ethernet-switching table'
    elif 'nxos' in dtype:
        mac_cmd = 'show mac address-table'
    else:
        mac_cmd = 'show mac address-table'

    try:
        mac_out = conn.send_command(mac_cmd, read_timeout=60)
    except Exception as exc:
        if log_func:
            log_func(f"WARNING: MAC table command failed: {exc}")
        return

    if ('juniper' in dtype or vendor == 'juniper_junos') and (
        not mac_out.strip() or 'error:' in mac_out.lower()[:80]
    ):
        try:
            mac_out = conn.send_command('show bridge mac-table', read_timeout=60)
        except Exception:
            pass

    int_meta = {i.get('name', ''): {} for i in interfaces if i.get('name')}
    interface_macs = _parse_mac_table(mac_out, device_type, int_meta, log_func)

    # Build case-insensitive lookup for interface names
    by_lower = {k.lower(): k for k in int_meta}

    for iface in interfaces:
        name = iface.get('name', '')
        learned = list(interface_macs.get(name, []))
        if not learned:
            learned = list(interface_macs.get(by_lower.get(name.lower(), ''), []))
        # Fuzzy: MAC table may use abbreviated names (Gi1/0/1 vs GigabitEthernet1/0/1)
        if not learned:
            for mac_name, macs in interface_macs.items():
                if mac_name.lower() == name.lower() or name.lower().endswith(mac_name.lower()):
                    learned.extend(macs)
        iface['learned_macs'] = sorted(set(learned))
        if log_func and iface['learned_macs']:
            log_func(f"[{name}] {len(iface['learned_macs'])} learned MAC(s)")

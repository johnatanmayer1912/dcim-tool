"""Debug NX-OS via-line regex directly (no module import)."""
import re

line1 = "    *via 10.1.1.1, Eth1/1, [0/0], 00:05:00, direct"
line2 = "    *via 10.0.0.1, Eth1/2, [110/20], 00:01:00, ospf-1, intra"
line3 = "    *via 10.0.0.1, Eth1/3, [1/0], 00:01:00, static"

# New corrected regex
nxos_via_re = re.compile(
    r'^\s+\*?via\s+(?P<nhop>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    r'(?:,\s*(?P<iface>[^,\[]+?))?'
    r'(?:,\s*\[(?P<ad>\d+)/(?P<metric>\d+)\])?'
    r'(?:,\s*(?P<uptime>\d[\d:hwdms]+))?'
    r'(?:,\s*(?P<proto>[^,\s]+))?',
)
print("=== regex v1 (lazy [^,\\[]+?) ===")
for l in (line1, line2, line3):
    m = nxos_via_re.match(l)
    if m:
        print(f"  nhop={m.group('nhop')} iface={m.group('iface')!r} "
              f"ad={m.group('ad')} metric={m.group('metric')} "
              f"uptime={m.group('uptime')!r} proto={m.group('proto')!r}")
    else:
        print(f"  NO MATCH: {l!r}")

# Try non-lazy
nxos_via_re2 = re.compile(
    r'^\s+\*?via\s+(?P<nhop>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    r'(?:,\s*(?P<iface>[^,\[]+))?'
    r'(?:,\s*\[(?P<ad>\d+)/(?P<metric>\d+)\])?'
    r'(?:,\s*(?P<uptime>[\d:hwdms]+))?'
    r'(?:,\s*(?P<proto>[^,\s]+))?',
)
print("\n=== regex v2 (greedy [^,\\[]+) ===")
for l in (line1, line2, line3):
    m = nxos_via_re2.match(l)
    if m:
        print(f"  nhop={m.group('nhop')} iface={m.group('iface')!r} "
              f"ad={m.group('ad')} metric={m.group('metric')} "
              f"uptime={m.group('uptime')!r} proto={m.group('proto')!r}")
    else:
        print(f"  NO MATCH: {l!r}")

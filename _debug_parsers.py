"""Debug parser behaviour — run directly to see what each platform returns."""
import sys
sys.path.insert(0, '.')
from modules.routing_analyzer.parser import (
    RoutingParser, _parse_cisco_regex, _parse_juniper_regex,
)
from modules.routing_analyzer.collector import RoutingCollector, _is_valid_output

# ── NX-OS ──────────────────────────────────────────────────────────────────
NXOS = (
    "IP Route Table for VRF default\n"
    "10.1.1.0/24, ubest/mbest: 1/0, attached\n"
    "    *via 10.1.1.1, Eth1/1, [0/0], 00:05:00, direct\n"
    "10.1.2.0/24, ubest/mbest: 1/0\n"
    "    *via 10.0.0.1, Eth1/2, [110/20], 00:01:00, ospf-1, intra\n"
    "0.0.0.0/0, ubest/mbest: 1/0\n"
    "    *via 10.0.0.1, Eth1/3, [1/0], 00:01:00, static\n"
)

print("=== NX-OS ===")
r = _parse_cisco_regex(NXOS, 'cisco_nxos')
print(f"  count={len(r)}")
for x in r:
    print(f"  {x}")

# ── Junos ──────────────────────────────────────────────────────────────────
JUNOS = (
    "inet.0: 5 destinations, 5 routes (5 active, 0 holddown, 0 hidden)\n"
    "+ = Active Route, - = Last Active, * = Both\n\n"
    "10.1.1.0/24        *[Direct/0] 1w6d\n"
    "                    > via ge-0/0/0.0\n"
    "10.0.0.0/8         *[Static/5] 1w6d\n"
    "                    > to 10.1.1.1 via ge-0/0/0.0\n"
    "0.0.0.0/0          *[Static/5] 1w6d\n"
    "                    > to 10.1.1.1 via ge-0/0/0.0\n"
    "192.168.1.0/24     *[OSPF/10] 00:01:23, metric 2\n"
    "                    > to 10.1.1.1 via ge-0/0/0.0\n"
    "203.0.113.0/24     *[BGP/170] 00:05:30, localpref 100\n"
    "                    > to 10.1.1.1 via ge-0/0/0.0\n"
)

print("\n=== Junos ===")
r2 = _parse_juniper_regex(JUNOS)
print(f"  count={len(r2)}")
for x in r2:
    print(f"  {x}")

# ── VRF parsing ──────────────────────────────────────────────────────────
print("\n=== VRF name parsing ===")
col = RoutingCollector('cisco_ios')
vrf_out = "Name\nVRF_PROD\nVRF_DEV\n"
vrfs = col._parse_vrf_names(vrf_out)
print(f"  input: {repr(vrf_out)}")
print(f"  result: {vrfs}")

# Show what the line.lower().startswith check does
for line in vrf_out.splitlines():
    line = line.strip()
    print(f"    line={repr(line)} | startswith_name={line.lower().startswith('name')} | startswith_vrf={line.lower().startswith('vrf')}")

# ── is_valid_output ────────────────────────────────────────────────────────
print("\n=== _is_valid_output ===")
print(f"  '' -> {_is_valid_output('')}")
print(f"  '% Invalid' -> {_is_valid_output('% Invalid input')}")
# NX-OS output has a header — is it valid?
print(f"  NXOS header -> {_is_valid_output(NXOS)}")
print(f"  Junos header -> {_is_valid_output(JUNOS)}")

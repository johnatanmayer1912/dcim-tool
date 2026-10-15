import re

cisco_pattern = re.compile(r'^(\d+)\s+([\w-]+)\s+([\w-]+)')
legacy_pattern = re.compile(r'^([\w-]+)\s+(\d+)\s+')

cisco_out = """
10   VLAN0010                         active
20   VLAN0020                         active
30   VLAN0030                         active
"""

juniper_out = """
VLAN0010 10
VLAN0040 40
"""

print("--- Testing Cisco ---")
for line in cisco_out.splitlines():
    line = line.strip()
    if not line: continue
    match = cisco_pattern.search(line)
    if match:
        print(f"Matched: {match.groups()}")
    else:
        print(f"No match: '{line}'")

print("\n--- Testing Juniper ---")
for line in juniper_out.splitlines():
    line = line.strip()
    if not line: continue
    match = legacy_pattern.search(line)
    if match:
        print(f"Matched: {match.groups()}")
    else:
        print(f"No match: '{line}'")

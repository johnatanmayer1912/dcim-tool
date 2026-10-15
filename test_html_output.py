"""
Test script to generate actual HTML output and check data embedding.
"""
from modules.l3_topology_runner import build_l3_topology_bundle
from utils.l3_map_formatter import l3_bundle_to_vis
from utils.l3_map_shell import render_l3_map_html

# Create test data
device_results = [
    {
        'status': 'success',
        'true_host': 'sw-01.example.com',
        'host': 'sw-01.example.com',
        'routes_normalized': [
            {
                'device_id': 'sw-01.example.com',
                'destination': '192.168.1.0/24',
                'next_hop': '0.0.0.0',
                'protocol': 'Connected',
                'interface': 'Vlan10',
                'vrf': 'default',
                'route_type': 'Connected',
            },
            {
                'device_id': 'sw-01.example.com',
                'destination': '0.0.0.0/0',
                'next_hop': '10.0.0.1',
                'protocol': 'Static',
                'interface': 'Vlan1',
                'vrf': 'default',
                'route_type': 'Dynamic',
            },
        ],
    }
]

# Build bundle
bundle = build_l3_topology_bundle(device_results)
print(f"Bundle route_count: {bundle['route_count']}")
print(f"Bundle devices: {list(bundle['devices'].keys())}")
print(f"Bundle topology nodes: {len(bundle['topology']['nodes'])}")
print(f"Bundle topology edges: {len(bundle['topology']['edges'])}")

# Convert to vis payload
vis_payload = l3_bundle_to_vis(bundle)
print(f"\nVis payload nodes: {len(vis_payload['nodes'])}")
print(f"Vis payload edges: {len(vis_payload['edges'])}")
print(f"Vis payload analysis: {vis_payload['analysis']}")

# Render HTML
html = render_l3_map_html(vis_payload, map_kind='l3')

# Check HTML content
print(f"\nHTML length: {len(html)}")
print(f"Contains RAW_NODES: {'RAW_NODES' in html}")
print(f"Contains sw-01.example.com: {'sw-01.example.com' in html}")
print(f"Contains 192.168.1.0/24: {'192.168.1.0/24' in html}")
print(f"Contains 10.0.0.1: {'10.0.0.1' in html}")

# Save HTML to file for inspection (with UTF-8 encoding)
with open('test_l3_map_output.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("\nHTML saved to test_l3_map_output.html")

# Check if RAW_NODES has actual data
import re
nodes_match = re.search(r'const RAW_NODES\s*=\s*(\[.*?\]);', html, re.DOTALL)
if nodes_match:
    nodes_content =	nodes_match.group(1)
    print(f"\nRAW_NODES content length: {len(nodes_content)}")
    print(f"RAW_NODES is empty array: {nodes_content.strip() == '[]'}")
    print(f"RAW_NODES first 200 chars: {nodes_content[:200]}")
else:
    print("\nCould not find RAW_NODES in HTML")

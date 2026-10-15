"""Generate DEMO_DISCOVERY_COMMAND_CENTER_v7.0.4.html for offline QA."""
import os

from utils.discovery_map_formatter import generate_discovery_html


def main():
    nodes = [
        {
            'id': 'CORE-NXOS-01',
            'ip': '10.10.1.1',
            'platform': 'N9K-C93180YC',
            'device_type': 'cisco_nxos',
            'depth': 0,
            'is_scanned': True,
            'scan_state': 'seed',
            'discovered_via': 'Seed',
        },
        {
            'id': 'DIST-IOS-02',
            'ip': '10.10.1.2',
            'platform': 'C9300-48P',
            'device_type': 'cisco_ios',
            'depth': 1,
            'is_scanned': True,
            'scan_state': 'scanned',
        },
        {
            'id': 'ACCESS-03',
            'ip': '10.10.1.3',
            'platform': 'C9200',
            'device_type': 'cisco_ios',
            'depth': 2,
            'is_scanned': False,
            'scan_state': 'neighbor_only',
        },
        {
            'id': 'FAILED-04',
            'ip': '10.10.1.4',
            'platform': 'unknown',
            'device_type': 'cisco_ios',
            'depth': 2,
            'is_scanned': False,
            'scan_state': 'failed',
            'status': 'Failed: timeout',
        },
    ]
    edges = [
        {
            'from': 'CORE-NXOS-01',
            'to': 'DIST-IOS-02',
            'f_port': 'Eth1/49',
            't_port': 'Gi1/1',
            'protocol': 'CDP',
        },
        {
            'from': 'DIST-IOS-02',
            'to': 'ACCESS-03',
            'f_port': 'Gi1/48',
            't_port': 'Gi0/1',
            'protocol': 'LLDP',
        },
        {
            'from': 'DIST-IOS-02',
            'to': 'FAILED-04',
            'f_port': 'Gi1/47',
            't_port': 'Gi0/2',
            'protocol': 'CDP',
        },
    ]
    out = 'DEMO_DISCOVERY_COMMAND_CENTER_v7.0.4.html'
    generate_discovery_html(out, nodes, edges)
    print(f'Wrote {os.path.abspath(out)} ({os.path.getsize(out)} bytes)')


if __name__ == '__main__':
    main()

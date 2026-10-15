"""Cisco-like CLI responses for offline SSH lab simulators."""
from __future__ import annotations

import os
from typing import Dict, Optional

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_LAB_FIXTURE_ROOT = os.path.join(_PROJECT_ROOT, 'lab', 'fixtures')
_ASSET_FIXTURE_ROOT = os.path.join(_PROJECT_ROOT, 'tests', 'fixtures', 'asset')

# Canonical NST Docker lab: 1× IOS C9300 + 2× NX-OS N9K-C93180YC-EX
LAB_DEVICES: Dict[str, Dict[str, str]] = {
    'ios_access': {
        'device_type': 'cisco_ios',
        'hostname': 'LAB-IOS-ACCESS1',
        'version_fixture': 'ios_access_show_version.txt',
        'inventory_fixture': 'ios_access_show_inventory.txt',
        'cdp_fixture': 'ios_access_cdp_detail.txt',
        'route_fixture': 'ios_access_show_ip_route.txt',
        'logging_fixture': 'ios_access_show_logging.txt',
        'prompt': 'LAB-IOS-ACCESS1#',
        'pid': 'C9300-24P',
    },
    'nxos_leaf1': {
        'device_type': 'cisco_nxos',
        'hostname': 'LAB-NXOS-LEAF1',
        'version_fixture': 'nxos_leaf1_show_version.txt',
        'inventory_fixture': 'nxos_leaf1_show_inventory.txt',
        'cdp_fixture': 'nxos_leaf1_cdp_detail.txt',
        'route_fixture': 'nxos_leaf1_show_ip_route.txt',
        'logging_fixture': 'nxos_leaf1_show_logging.txt',
        'vpc_fixture': 'nxos_leaf1_show_vpc_degraded.txt',
        'prompt': 'LAB-NXOS-LEAF1# ',
        'pid': 'N9K-C93180YC-EX',
    },
    'nxos_leaf2': {
        'device_type': 'cisco_nxos',
        'hostname': 'LAB-NXOS-LEAF2',
        'version_fixture': 'nxos_leaf2_show_version.txt',
        'inventory_fixture': 'nxos_leaf2_show_inventory.txt',
        'cdp_fixture': 'nxos_leaf2_cdp_detail.txt',
        'route_fixture': 'nxos_leaf2_show_ip_route.txt',
        'logging_fixture': 'nxos_leaf2_show_logging.txt',
        'prompt': 'LAB-NXOS-LEAF2# ',
        'pid': 'N9K-C93180YC-EX',
    },
    # Legacy aliases (older docs / single-port tests)
    'ios12': {
        'device_type': 'cisco_ios',
        'hostname': 'LAB-IOS12-01',
        'version_fixture': 'ios_show_version.txt',
        'inventory_fixture': 'ios_show_inventory.txt',
        'prompt': 'LAB-IOS12-01>',
        '_root': 'asset',
    },
    'ios17': {
        'device_type': 'cisco_ios',
        'hostname': 'LAB-IOS17-01',
        'version_fixture': 'ios_show_version.txt',
        'inventory_fixture': 'ios_show_inventory.txt',
        'prompt': 'LAB-IOS17-01#',
        '_root': 'asset',
    },
    'nxos7': {
        'device_type': 'cisco_nxos',
        'hostname': 'LAB-NXOS7-01',
        'version_fixture': '../discovery/nxos_show_version.txt',
        'inventory_fixture': 'nxos_show_inventory.txt',
        'prompt': 'LAB-NXOS7-01# ',
        '_root': 'asset',
    },
    'nxos9': {
        'device_type': 'cisco_nxos',
        'hostname': 'LAB-NXOS9-01',
        'version_fixture': '../discovery/nxos_show_version.txt',
        'inventory_fixture': 'nxos_show_inventory.txt',
        'prompt': 'LAB-NXOS9-01# ',
        '_root': 'asset',
    },
}

DEFAULT_PORT_MAP = {
    2201: 'ios_access',
    2202: 'nxos_leaf1',
    2203: 'nxos_leaf2',
}


def device_for_port(port: int) -> Optional[str]:
    return DEFAULT_PORT_MAP.get(int(port))


def read_fixture(name: str, root: str = 'lab') -> str:
    base = _LAB_FIXTURE_ROOT if root == 'lab' else _ASSET_FIXTURE_ROOT
    path = os.path.normpath(os.path.join(base, name))
    with open(path, 'r', encoding='utf-8', errors='replace') as fh:
        return fh.read()


def handle_command(device_key: str, command: str) -> str:
    """Return deterministic CLI output for lab devices."""
    meta = LAB_DEVICES.get(device_key) or {}
    root = meta.get('_root', 'lab')
    cmd = (command or '').strip().lower()
    # Netmiko session prep (must succeed quickly; echo handled by server).
    if (
        not cmd
        or cmd.startswith('terminal length')
        or cmd.startswith('terminal width')
        or cmd.startswith('term length')
        or cmd.startswith('term width')
        or cmd in ('no logging console', 'terminal pager 0')
    ):
        return ''
    if cmd.startswith('show version') or cmd.startswith('show ver'):
        return read_fixture(meta.get('version_fixture', 'ios_access_show_version.txt'), root)
    if cmd.startswith('show inventory') or cmd.startswith('show diag'):
        return read_fixture(meta.get('inventory_fixture', 'ios_access_show_inventory.txt'), root)
    if 'cdp neighbors detail' in cmd or cmd.startswith('show cdp entry'):
        fix = meta.get('cdp_fixture')
        if fix:
            return read_fixture(fix, root)
        return ''
    if cmd.startswith('show cdp neighbors') or cmd.startswith('show cdp nei'):
        fix = meta.get('cdp_fixture')
        if fix:
            return read_fixture(fix, root)
        return ''
    if 'lldp neighbors detail' in cmd or cmd.startswith('show lldp neighbors'):
        # Lab is CDP-primary; empty LLDP is honest (not invented).
        return ''
    if cmd.startswith('show hostname') or cmd == 'show run | include hostname':
        return f"hostname {meta.get('hostname', 'LAB')}"
    if cmd.startswith('show spanning-tree') or cmd.startswith('show stp'):
        return 'VLAN0001\n  Spanning tree enabled protocol rstp\n'
    if cmd.startswith('show mac address-table') or cmd.startswith('show mac address') or cmd.startswith('show mac-address-table'):
        return (
            "          Mac Address Table\n"
            "-------------------------------------------\n"
            "Vlan    Mac Address       Type        Ports\n"
            "----    -----------       --------    -----\n"
            "   1    0011.2233.4455    DYNAMIC     Gi1/0/1\n"
        )
    if cmd.startswith('show vlan') or cmd.startswith('show vlan brief'):
        return (
            "VLAN Name                             Status    Ports\n"
            "---- -------------------------------- --------- -------------------------------\n"
            "1    default                          active    Eth1/1\n"
            "10   USERS                            active\n"
            "20   SERVERS                          active\n"
        )
    # L3 cartography — must return parseable route tables (not "% Invalid input")
    if cmd.startswith('show ip route') or cmd.startswith('show ipv4 route'):
        if 'summary' in cmd:
            return (
                "IP Route Table for VRF \"default\"\n"
                "Total number of routes: 8\n"
                "Total number of paths: 8\n"
            )
        fix = meta.get('route_fixture')
        if fix:
            return read_fixture(fix, root)
        return ''
    if cmd.startswith('show ipv6 route') or cmd.startswith('show route'):
        # Lab fabric is IPv4-only — empty is honest (not invented).
        return ''
    if cmd.startswith('show logging'):
        fix = meta.get('logging_fixture')
        if fix:
            return read_fixture(fix, root)
        return ''
    if cmd.startswith('show vpc'):
        if meta.get('device_type') == 'cisco_nxos':
            # Leaf1 lab scenario: degraded vPC for correlation engine demos.
            fix = meta.get('vpc_fixture')
            if fix:
                return read_fixture(fix, root)
            return (
                "Legend:\n"
                "                (*) - local vPC is down, forwarding via vPC peer-link\n\n"
                "vPC domain id : None\n"
                "Peer status   : peer adjacency formed ok\n"
                "vPC role      : none established\n"
                "Number of vPCs configured : 0\n"
            )
        return '% Invalid input detected at \'^\' marker.\n'
    if cmd.startswith('show errdisable'):
        return (
            "ErrDisable Reason            Timer Status\n"
            "-----------------            --------------\n"
            "link-flap                    Enabled\n"
            "bpduguard                    Enabled\n"
        )
    if cmd.startswith('show port-channel') or cmd.startswith('show etherchannel'):
        return 'Number of channel-groups in use: 0\n'
    if cmd.startswith('show interface') and 'brief' in cmd:
        if meta.get('hostname') == 'LAB-NXOS-LEAF1':
            return (
                "--------------------------------------------------------------------------------\n"
                "Ethernet      VLAN    Type Mode   Status  Reason                   Speed     Port\n"
                "Interface                                                                    Ch #\n"
                "--------------------------------------------------------------------------------\n"
                "Eth1/1        1       eth  access down    linkFailure                1000(D) --\n"
                "Eth1/49       1       eth  trunk  down    linkFailure               auto(D) 1\n"
                "mgmt0         --      eth  routed up      none                        1000 --\n"
            )
        if meta.get('hostname') == 'LAB-NXOS-LEAF2':
            return (
                "--------------------------------------------------------------------------------\n"
                "Ethernet      VLAN    Type Mode   Status  Reason                   Speed     Port\n"
                "Interface                                                                    Ch #\n"
                "--------------------------------------------------------------------------------\n"
                "Eth1/5        1       eth  access down    Administratively down      auto(D) --\n"
                "Eth1/10       1       eth  access down    errDisabled                auto(D) --\n"
                "Eth1/49       1       eth  trunk  down    linkFailure               auto(D) 1\n"
                "mgmt0         --      eth  routed up      none                        1000 --\n"
            )
        return (
            "--------------------------------------------------------------------------------\n"
            "Ethernet      VLAN    Type Mode   Status  Reason                   Speed     Port\n"
            "Interface                                                                    Ch #\n"
            "--------------------------------------------------------------------------------\n"
            "Eth1/1        1       eth  access up      none                       1000(D) --\n"
            "mgmt0         --      eth  routed up      none                        1000 --\n"
        )
    if cmd.startswith('show interfaces status') or cmd.startswith('show interface status'):
        return (
            "Port      Name               Status       Vlan       Duplex  Speed Type\n"
            "Gi1/0/1                      err-disabled 1          auto    auto 10/100/1000BaseTX\n"
            "Gi1/0/24                     notconnect   1          auto    auto 10/100/1000BaseTX\n"
        )
    if cmd.startswith('show ip interface brief') or cmd.startswith('show ip int brief'):
        return (
            "Interface              IP-Address      OK? Method Status                Protocol\n"
            "mgmt0                  127.0.0.1       YES NVRAM  up                    up\n"
        )
    if cmd.startswith('show running-config') or cmd.startswith('show run'):
        return (
            f"! lab fixture running-config\n"
            f"hostname {meta.get('hostname', 'LAB')}\n"
            f"!\n"
            f"vlan 10\n"
            f"  name USERS\n"
            f"!\n"
            f"end\n"
        )
    if cmd in ('configure terminal', 'conf t', 'config t', 'configure'):
        return 'Enter configuration commands, one per line.  End with CNTL/Z.\n'
    if cmd.startswith('vlan ') or cmd == 'exit' or cmd == 'end' or cmd.startswith('name '):
        return ''
    if cmd.startswith('copy running') or cmd.startswith('write memory') or cmd == 'write':
        return 'Copy complete.\n'
    return f"% Invalid input detected at '^' marker.\n"

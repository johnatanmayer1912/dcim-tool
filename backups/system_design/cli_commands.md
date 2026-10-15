# CLI Command Knowledge Base

This document catalogs the exact CLI commands used by the system for each vendor/OS to enable a 1:1 reconstruction of the data collection layer.

## Cisco IOS / XE
| Command | Purpose | Extraction Strategy |
|---------|---------|---------------------|
| `show vlan brief` | VLAN Audit | ID, Name, Status |
| `show version` | Inventory Audit | Model, Version, Serial, Uptime |
| `show cdp neighbors detail`| Topology Mapping | Neighbor Hostname, Local Port, Remote Port |
| `show interface status` | Diagnostics | Admin/Op Status, Speed, Duplex |
| `show mac-address-table` | MAC Tracking | MAC, Port, VLAN |
| `show running-config` | Config Backup | Full Blob |

## Cisco NX-OS (Nexus)
| Command | Purpose | Extraction Strategy |
|---------|---------|---------------------|
| `show vlan` | VLAN Audit | ID, Name, Status |
| `show port-channel summary` | Topology | Port-Channel ID, Member Ports |
| `show vpc` | Topology | vPC ID, Status |
| `show mac address-table` | MAC Tracking | Note the extra space vs. IOS |

## Juniper Junos
| Command | Purpose | Extraction Strategy |
|---------|---------|---------------------|
| `show vlans` | VLAN Audit | Name, ID |
| `show system uptime` | Inventory Audit | Uptime |
| `show version` | Inventory Audit | Model, Version, Serial |
| `show lldp neighbors` | Topology Mapping | Neighbor Name, Local Port, Remote Port |
| `show interfaces terse` | Diagnostics | Admin/Op Status |
| `show ethernet-switching table` | MAC Tracking | CAM table |

---

## Command Selection Rationale
- **Detail vs. Standard**: `detail` is preferred for Neighbors as it provides full hostnames and interface names which are often truncated in standard view.
- **Brief vs. Full**: `brief` is preferred for VLANs on IOS to minimize output processing time on large databases.
- **Terse**: On Juniper, `terse` provides the most reliable column-based status output for programmatic parsing.

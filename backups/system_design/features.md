# Feature Catalog: Network Swiss Tool Pro

## 1. Connectivity Check
- **Purpose**: Rapidly verify L3 (ICMP) and L7 (SSH Auth) accessibility.
- **Commands**: `ping -n 1`, `SSH Connection`.
- **Logic**: Pings target; if reachable, attempts Netmiko connection. Returns boolean for both.

## 2. VLAN Audit
- **Purpose**: Extract the full VLAN database for audit/compliance.
- **Commands**:
  - Cisco: `show vlan brief` (Standard) or `show vlan` (Nexus).
  - Juniper: `show vlans`.
- **Logic**: Captures raw CLI output and uses `parse_vlan_output` (regex-based) to extract ID, Name, and Status.

## 3. VLAN Compare
- **Purpose**: Identify configuration drift across multiple switches.
- **Logic**:
  1. Collects VLAN lists from ALL target switches.
  2. Creates a "Global Union" of every VLAN ID found in the network.
  3. Iterates through each switch and identifies which IDs from the Global Union are missing.
  4. Generates a discrepancy report.

## 4. Topology Mapping
- **Purpose**: Visualize physical and logical connections.
- **Commands**: `show cdp neighbors detail`, `show lldp neighbors detail`, `show port-channel summary`, `show vpc`.
- **Logic**:
  - Extracts Neighbor Name, Local Port, and Remote Port.
  - Normalizes Port names (`GigabitEthernet` -> `Gi`).
  - Identifies Port-Channels and vPCs to group links visually.
  - Generates HTML using Vis.js for interactive physics diagrams.

## 5. Network Inventory Audit
- **Purpose**: Fleet-wide visibility into hardware and software versions.
- **Commands**: `show version`, `show system uptime` (Juniper).
- **Logic**: Uses extensive regex to pinpoint Model, OS Version, Serial Number, and Uptime from multi-line blobs.

## 6. Interface Diagnostics
- **Purpose**: Map Admin vs. Operational status of all physical ports.
- **Commands**: `show interface status`, `show interfaces description`.
- **Logic**: Cross-references status output with description output to provide a "Single Pane of Glass" view of interface health.

## 7. MAC Tracker
- **Purpose**: Locate a specific device (MAC) within the switched fabric.
- **Commands**: `show mac-address-table` (Cisco), `show ethernet-switching table` (Juniper).
- **Logic**: Normalizes the target MAC (removing `:`, `.`, or `-`) and searches the CAM table across all targeted switches.

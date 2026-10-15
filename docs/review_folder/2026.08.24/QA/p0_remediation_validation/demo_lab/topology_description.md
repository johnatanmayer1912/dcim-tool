# Offline 8-vendor demo topology

Offline fixture lab. Not live vendor evidence. Not a certified cable plant.

## Devices (8)
- 3× Cisco Nexus (`NX-CORE-01`, `NX-CORE-02`, `NX-AGG-01`)
- 2× Cisco IOS (`IOS-DIST-01`, `IOS-ACC-01`)
- 1× Cisco IOS-XE (`IOS-XE-DIST-02`)
- 2× Juniper Junos (`JN-ACC-01`, `JN-ACC-02`)

## L2 cables (7) — CDP/LLDP only
- NX-CORE-01 Eth1/1 ↔ NX-CORE-02 Eth1/1 (CDP)
- NX-CORE-01 Eth1/49 ↔ IOS-DIST-01 Te1/1/1 (CDP)
- NX-CORE-02 Eth1/49 ↔ IOS-XE-DIST-02 Te1/1/1 (LLDP)
- NX-AGG-01 Eth1/1 ↔ NX-CORE-01 Eth1/2 (CDP)
- IOS-DIST-01 Gi1/0/48 ↔ IOS-ACC-01 Gi1/0/1 (LLDP) ONE-SIDED
- IOS-DIST-01 Gi1/0/47 ↔ JN-ACC-01 ge-0/0/0 (LLDP)
- IOS-XE-DIST-02 Gi1/0/24 ↔ JN-ACC-02 ge-0/0/1 (LLDP)

## Not cables
- EVPN NVE peer NX-CORE-01 nve1 ↔ NX-CORE-02 nve1
- STP-blocked IOS-DIST-01 Gi1/0/2 ↔ IOS-ACC-01 Gi1/0/2
- Incomplete CDP on IOS-ACC-01 Gi1/0/24 (diagnostics only)

Do not treat this as live-vendor proof.

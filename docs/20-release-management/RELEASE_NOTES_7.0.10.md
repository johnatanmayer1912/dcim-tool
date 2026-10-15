# Release Notes — v7.0.10

**Date:** 2026-05-31  
**Artifact:** `dist/NetworkSwissToolPro_v7.0.10_OFFLINE.exe`

## Summary

Fixes Discovery link inventory for **NX-OS LLDP** when neighbors advertise incomplete TLVs (common on single-switch and fabric edge scans).

## Root causes addressed

1. Parser required `System Name` in every block — MAC-only neighbors were dropped or misparsed by brief fallback.
2. `\S+` on `System Name: not advertised` captured **`not`** as hostname.
3. NX-OS uses **`Local Port id:`** not only `Local Intf:` → local port stayed `unknown`.
4. **`Port id`** sometimes carries a **MAC**; real interface is in **`Port Description`**.
5. API/export showed JSON **`null`** for missing remote ports.

## Verification

```text
python _prebuild.py
py -3.12 -m unittest tests.test_network_discovery.TestDiscoveryParsers -v
```

Fixtures: `tests/fixtures/discovery/nxos_lldp_*.txt`

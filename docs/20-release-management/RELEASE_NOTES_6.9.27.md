# Network Swiss Tool Pro v6.9.27 Release Notes

**Release Date:** 2026-05-31  
**Version:** v6.9.27  
**Codename:** vPC Engineering Board

---

## Summary

Redesigns the **vPC Map** for offline NOC use on older hardware: readable tables first, simplified static graph second.

### Highlights

- **Engineering Board** (default tab): peer-link Po, keepalive, vPC table, members, downstream links, global consistency CLI, health alerts.
- **Simplified Map**: fixed layout, physics off, hidden non-vPC links by default.
- **Parsing**: NX-OS `Peer status` / `vPC keep-alive status` in topology mapper.
- **Payload**: `port_channels` on nodes; board data in diagnostics `06` → `board_sections`.

---

## Artifact

`dist/NetworkSwissToolPro_v6.9.27_OFFLINE.exe`

## Validation

```bash
python tests/validate_vpc_member_interfaces.py
python -m unittest tests.test_vpc_board_html tests.test_network_discovery -v
python create_demo_map_v7.py
```

# Network Swiss Tool Pro v6.9.28 Release Notes

**Release Date:** 2026-05-31  
**Version:** v6.9.28

## Summary

Discovery reliability and NOC-friendly crawl output, plus expanded config template presets.

### Highlights

- **BUG-0006 fixed:** NX-OS devices show real hostnames (not `show version` banner text).
- **Discovery map:** Default **Link Inventory** table + static topology tab (offline, no external fonts).
- **Templates:** Trunk, port-channel, trunk+vPC presets for IOS and NX-OS with web builder.

## Artifact

`dist/NetworkSwissToolPro_v6.9.28_OFFLINE.exe`

## Validation

```bash
python -m unittest tests.test_network_discovery tests.test_config_templates_presets tests.test_vpc_board_html -v
python _prebuild.py
```

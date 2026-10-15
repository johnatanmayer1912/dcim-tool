# EXE smoke checklist (v7.0.51)

Use after building `dist/NetworkSwissToolPro_v7.0.51_OFFLINE.exe`. Record results in a release action log or bug sweep report.

## Automated simulation (NEW-C1)

```text
python scripts/audit_frozen_plugin_sim.py
```

| Check | Bare EXE dir (read-only) | Writable sidecar |
|-------|--------------------------|------------------|
| `plugins_dir` | `_MEIPASS/modules/plugins` (bundled) | `{exe}/plugins` (bootstrapped) |
| `loaded_count` | ≥ 10 bundled plugins | ≥ 10 after bootstrap copy |
| Health quick check | Plugin registry line **pass** | Plugin registry line **pass** |

## Manual: bare EXE only

1. Copy **only** `NetworkSwissToolPro_v7.0.51_OFFLINE.exe` to an empty folder.
2. Run the EXE; open browser `http://127.0.0.1:5051`.
3. **Plugins tab** → expect full plugin count.
4. `/api/plugins/debug` — `plugins_dir`, `loaded_plugins` ≥ 10.

## Standard L2 Map (v7.0.49–7.0.51)

| ID | Steps | Pass when |
|----|-------|-----------|
| SM-01 | Run Standard L2 Map on lab inventory | Split pane: map + connection index visible |
| SM-02 | Check legend | Readable pills in top chrome (not black-on-black) |
| SM-03 | vPC peer pair in topology | Purple peer-link on map; **Peer** row in index |
| SM-04 | Long interface descriptions | No text stacked on map edges; detail in index/tooltip |
| SM-05 | Toggle **Show port labels** | Short port names appear; hide restores clean map |
| SM-06 | Map styles | Tier, Radial, Focus, Schematic switch without blank canvas |
| SM-07 | Offline export | Open exported HTML without network — map renders |

## vPC Command Center

| ID | Steps | Pass when |
|----|-------|-----------|
| VPC-01 | vPC map mode | Overview tab shows `#mynetwork.vpc-map-pane` |
| VPC-02 | Engineering board | Peer strip + Po table visible beside map |

## Automated tests (release gate)

```powershell
python -m pytest tests/test_standard_map_v7049.py tests/test_vpc_map_html_contract.py -q
python _prebuild.py
```

## Council sign-off

| Role | Sign-off |
|------|----------|
| QA | Standard Map + VPC contract tests; prebuild PASS |
| Release | `NetworkSwissToolPro_v7.0.51_OFFLINE.exe` built |
| R-LIB | Documentation synced 2026-06-18 |

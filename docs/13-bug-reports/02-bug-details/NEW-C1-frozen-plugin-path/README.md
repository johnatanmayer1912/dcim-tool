# NEW-C1 — Frozen EXE plugin path mismatch

| Field | Value |
|-------|-------|
| **ID** | NEW-C1 |
| **Severity** | Critical (EXE-only deploy) |
| **Status** | **open** |
| **Owner** | Lead Developer |

## Description

`PluginRegistry` in frozen mode sets `plugins_dir = os.path.join(exe_dir, 'plugins')`. PyInstaller bundles plugins under `_MEIPASS/modules/plugins`. A standalone EXE copied without a sidecar `plugins/` folder loads **zero** plugins.

## Repro

```text
python scripts/audit_frozen_plugin_sim.py
```

Expect: `loaded_count: 0`, `bundled_py_count: 12`, verdict CONFIRMED.

Manual: [`exe-smoke-checklist.md`](../../../08-operations/exe-smoke-checklist.md).

## Evidence

- `modules/plugin_registry.py` lines 62–65
- `NetworkSwissToolPro_v7.0.2.spec` datas include `modules/plugins`

## Fix direction (future)

On frozen init: if `exe_dir/plugins` is empty, copy or point registry at `_MEIPASS/modules/plugins`.

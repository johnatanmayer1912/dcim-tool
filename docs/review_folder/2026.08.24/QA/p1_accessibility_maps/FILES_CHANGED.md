# Files changed — P1 accessibility + maps

## Operator UI
- `modules/web/templates/index.html`

## Map shells
- `utils/discovery_map_shell.py` (light CC contrast + CSS order after shared topo tokens)
- Prior P1 map landmark/lang/scroll work already in `utils/standard_map_shell.py`, `utils/topo_map_shell.py`, `utils/l3_map_shell.py`, `utils/combined_l2l3_shell.py`, `utils/l3_map_shell_enhanced.py`, `utils/report_formatter.py`

## Tests
- `tests/test_p1_a11y_maps_7_2_4.py`
- `tests/qa/test_06_ui_ux_clarity.py` (`test_p1_operator_headings_skip_h5_h6`)
- `tests/test_rb_zt_04_confirm_modals.py` (closed dialog = `hidden`+`inert`, no first-paint `tabindex`)
- `tests/qa/MANDATORY_MANIFEST.yaml` (`last_reviewed`)

## Docs
- `CHANGELOG.md` (Unreleased)
- This folder

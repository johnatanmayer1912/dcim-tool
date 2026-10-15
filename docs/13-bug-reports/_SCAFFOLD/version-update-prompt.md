# VERSION UPDATE PROMPT — [BUG-ID] (copy-paste into AI IDE)

```
RESYNC per INDEX_PROMPT. Release Manager (R-REL) for [BUG-ID] fix release.

## Scope
- Bug fixed: [BUG-ID]
- VERSION bump: patch | minor (justify)

## Checklist (G-09)
- [ ] U-QA validation evidence linked
- [ ] U-LIB docs / CHANGELOG complete
- [ ] U-SEC / U-OBS if applicable
- [ ] VERSION file updated
- [ ] PROMPT_REGISTRY application sync line if behavior changed
- [ ] Rollback note in CHANGELOG if non-trivial risk

## Build (only if user requests EXE)
- _prebuild.py green
- NetworkSwissToolPro spec / dist per project practice

Do not git commit or push unless user explicitly asks.
```

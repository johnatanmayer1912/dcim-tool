# Release Notes — v7.0.9

**Date:** 2026-05-31  
**Artifact:** `dist/NetworkSwissToolPro_v7.0.9_OFFLINE.exe`

## Summary

UX refinement release: approved sidebar branding, cleaner header, **Network Search** tab rename, and operational UI polish.

## Highlights

- Sidebar brand block: logo, version, short updated date, Made by AI IDE; opens About on click.
- Top header: traffic lights + chrome only (no duplicate title/badges).
- **Network Search** tab (formerly `search_it` in the UI).
- Tab strip, content cards, and console header visual refresh.

## Documentation

- Canonical ops guides: `docs/08-operations/network-search-workflow.md`, `network-search-reports-guide.md`.
- Redirect stubs: `search-it-*.md` → new names.
- Librarian audit: `docs/00-overview/LIBRARIAN_AUDIT_v7.0.9.md`.

## Verification

```text
python _prebuild.py
python -m pytest tests/test_search_it_progress.py tests/test_search_report_output.py -q
pyinstaller --clean --noconfirm NetworkSwissToolPro_v7.0.9.spec
```

## Upgrade

Replace prior `NetworkSwissToolPro_v7.0.x_OFFLINE.exe` with v7.0.9. No config migration required.

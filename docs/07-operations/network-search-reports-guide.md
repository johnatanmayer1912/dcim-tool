# Network Search — reports folder layout (v7.0.7+)

All **Network Search** tools (MAC trace, Description search, Network ping scan) write outputs under **`reports/`** next to the app or EXE — not the project root.

> **UI name (v7.0.9+):** **Network Search** tab. Internal APIs still use `/api/search-it/` for compatibility.

## Folder pattern

```
reports/
  mac_trace/
    YYYYMMDD/
      HHMMSS_<slug>/
        report.txt
        report.html
        manifest.json
  description_search/
    YYYYMMDD/
      HHMMSS_<slug>/
        ...
  ping_scan/
    YYYYMMDD/
      HHMMSS_<slug>/
        ...
```

- **`report.txt`** — full text log for the run.
- **`report.html`** — offline HTML opened from the UI (**View report (HTML)**).
- **`manifest.json`** — run metadata (term, MAC, network, counts, paths).

Implementation: `utils/search_report_output.py`.

## UI (Network Search tab)

| Tool | Button | API (browser) |
|------|--------|----------------|
| MAC Address Search | View path report (HTML) | `GET /api/mac-trace/report` |
| Description Search | View report (HTML) | `GET /api/description-search/report` |
| Network Ping Scan | View report (HTML) | `GET /api/ping-scan/report` |

After each run completes, the matching summary panel shows a short preview and the **Reports:** folder path.

## Live progress bar

Each tool shows a **discovery-style** progress bar while running. The UI polls `GET /api/search-it/progress` every ~600ms. State: `utils/search_it_progress.py`.

## Tab switching and page load (v7.0.7+)

- Scans **continue in the background** when you open other tabs.
- Returning to **Network Search** runs **`searchItInit()`**:
  - Refreshes progress bars from the server.
  - **Resumes polling** if any tool is still `running`.
  - Restores **last-run** summaries and **View report** strips.
- Tab label may show `● running` or `✓ ready` (`#network-search-tab-badge`).

## JSON last-run APIs

- `GET /api/mac-trace/last`
- `GET /api/description-search/last`
- `GET /api/ping-scan/last`

## Related docs

- [Network Search workflow](network-search-workflow.md)
- [MAC trace how-to](mac-trace-howto.md)

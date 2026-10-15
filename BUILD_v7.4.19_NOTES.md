# Build Network Swiss Tool Pro v7.4.19 (Windows offline)

```bat
python -m pip install -r requirements.txt pyinstaller
python build.py
```

Or: `python -m PyInstaller --clean --noconfirm NetworkSwissToolPro_v7.4.19.spec`

Artifact: `dist/NetworkSwissToolPro_v7.4.19_OFFLINE.exe`

### Post-Deploy Validation Checks:
1. **Version Gate**: `/api/version` → `7.4.19`.
2. **L3 Path Tracer (Item 1.1)**:
   - In Swiss Tools L3 Topology map, enter Source IP & Destination IP in `⚡ PATH TRACER`.
   - Click `Trace Flow`: highlights hop path on Vis.js canvas in green/amber and renders hop sequence card in sidebar.
   - API `POST /api/l3/trace-path` returns deterministic LPM hop array.
3. **Unified Multi-Layer Canvas (Item 1.2)**:
   - Layer switch bar includes `Physical`, `L2`, `L3`, `Overlay`, and `STP`.
   - Clicking `STP` highlights Root Bridge devices, green forwarding links, and red dashed blocking ports.
4. **Quad-Format Consolidated Inventory Export (Item 3.7)**:
   - Consolidating Asset & Warranty reports emits HTML, CSV, JSON, and XLSX (`openpyxl` styled with auto-width and colored status cells).
   - In-browser UI displays direct download links: `[📄 HTML] [📊 CSV] [📦 JSON] [📑 XLSX]`.
5. **Architectural Breadcrumbs**:
   - `AI_NAVIGATION_BREADCRUMBS` present across core and utility modules.

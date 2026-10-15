# Build Network Swiss Tool Pro v7.4.20 (Windows offline)

```bat
python -m pip install -r requirements.txt pyinstaller
python build.py
```

Or: `python -m PyInstaller --clean --noconfirm NetworkSwissToolPro_v7.4.20.spec`

Artifact: `dist/NetworkSwissToolPro_v7.4.20_OFFLINE.exe`

### Post-Deploy Validation Checks:
1. **Version Gate**: `/api/version` → `7.4.20`.
2. **Hardware UUID Deduplication & Discrepancy Tracking**:
   - Ingest multiple Asset Warranty reports (CSV, HTML, JSON, TXT) with identical or overlapping hardware devices.
   - Click `Generate Consolidated Report` in Reports workspace.
   - Status badge displays unique devices count along with amber `⚠️ N duplicates merged` badge.
3. **Statistical Integrity**:
   - Verify `model_counts` and `warranty_status_counts` reflect only deduplicated hardware devices without count inflation.
4. **Dedicated Duplicates Audit Across Quad Exports**:
   - **HTML**: Amber "⚠️ Duplicate Hardware Audit" section displays device UUID, occurrence count, source files, and conflict alerts.
   - **XLSX**: Second tab `"Duplicates Audit"` details all duplicate occurrences with freeze panes and styled headers.
   - **JSON**: Contains `duplicates_summary` and `duplicates_audit` arrays.
   - **CSV**: Emits clean consolidated master rows without duplicated records.
5. **Quality Assurance & Verification**:
   - Automated tests: `pytest tests/test_asset_warranty_uuid_dedup.py tests/test_asset_warranty_quad_export.py tests/test_asset_warranty_multi_file_consolidator.py` (17 passed).
   - Playwright E2E: `node tests/browser/l3_path_tracer_and_quad_export.spec.mjs` (All passed).
   - Prebuild verification: `python3 _prebuild.py` (All checks passed).

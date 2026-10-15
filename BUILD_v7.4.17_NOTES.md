# Build Network Swiss Tool Pro v7.4.17 (Windows offline)

```bat
python -m pip install -r requirements.txt pyinstaller
python build.py
```

Or: `python -m PyInstaller --clean --noconfirm NetworkSwissToolPro_v7.4.17.spec`

Artifact: `dist/NetworkSwissToolPro_v7.4.17_OFFLINE.exe`

Post-deploy checks:
1. `/api/version` → 7.4.17
2. Sidebar Secondary/Third credential dropdowns are **enabled** (optional fallback)
3. Juniper inventory + Cisco Asset & Warranty → report says `not a cisco device`
4. Consolidate multi-file HTML/CSV → non-empty mutual HTML + CSV

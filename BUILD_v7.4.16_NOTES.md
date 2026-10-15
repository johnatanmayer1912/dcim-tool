# Build Network Swiss Tool Pro v7.4.16 (Windows offline)

On a Windows build host with Python 3.11–3.14 and project deps installed:

```bat
python -m pip install -r requirements.txt pyinstaller
python build.py
```

Or directly:

```bat
python -m PyInstaller --clean --noconfirm NetworkSwissToolPro_v7.4.16.spec
```

Expected artifact: `dist/NetworkSwissToolPro_v7.4.16_OFFLINE.exe`

Operator checklist after deploy:
1. Confirm UI footer / `/api/version` shows **7.4.16**
2. Settings → select Primary + Secondary (+ optional Third) vault credentials
3. Run any Tool / Plugin / Discovery — auth failures should retry Secondary/Third
4. Asset Warranty Reports: copy HTML/CSV into `reports/asset_warranty_input/`, Generate Consolidated — expect devices > 0 and both HTML + CSV outputs

# Build Instructions — Network Swiss Tool Pro v7.0.65
# EXE offline build — single file, no internet required at runtime

---

## Prerequisites — one-time check

Open **Command Prompt** (not PowerShell) in the project folder:

```
cd "c:\Users\bbb12\OneDrive\Desktop\Antigravity Projects Folder\net_mng_tool_cartography"
```

Confirm you are in the right folder:

```
dir VERSION
```

Should print `VERSION` and show content `7.0.65`.

---

## Step 1 — Activate the virtual environment

```
.venv\Scripts\activate.bat
```

Your prompt should change to `(.venv)`.

Confirm Python version (must be 3.12.x, NOT 3.14):

```
python --version
```

If it says 3.14, stop. The EXE must be built with the `.venv` Python 3.12 interpreter.
Run this instead:

```
.venv\Scripts\python.exe --version
```

---

## Step 2 — Install / update all dependencies into .venv

This downloads every package listed in `requirements.txt` into the virtual environment.
Run with internet access. After this step, the build itself works offline.

```
.venv\Scripts\python.exe -m pip install -r requirements.txt --upgrade
```

Watch the output. Every line should say `Successfully installed` or `already satisfied`.

**Key packages to confirm are installed:**

```
.venv\Scripts\python.exe -m pip show netmiko flask networkx textfsm ntc-templates pyinstaller
```

Expected: each package shows a `Version:` line. If any is missing, install it:

```
.venv\Scripts\python.exe -m pip install netmiko==4.1.2 networkx==3.2.1 textfsm==1.1.3 ntc-templates==4.1.0
```

Also install paramiko dependencies (needed for offline SSH in EXE):

```
.venv\Scripts\python.exe -m pip install -r paramiko_deps\requirements.txt
```

If `paramiko_deps\requirements.txt` does not exist, install manually:

```
.venv\Scripts\python.exe -m pip install paramiko cryptography bcrypt PyNaCl cffi pycparser
```

---

## Step 3 — Run the pre-build syntax check

This catches any Python syntax errors before wasting build time:

```
.venv\Scripts\python.exe _prebuild.py
```

Expected output: `All OK` or `0 errors`. Fix any syntax errors reported before continuing.

---

## Step 4 — Build the EXE

This is the main build command. It takes 3–10 minutes depending on machine speed.
The `--clean` flag removes any previous build cache first.
The `--noconfirm` flag skips the "overwrite?" prompt.
The `2>&1` redirects all output (including errors) to a log file AND shows it on screen.

**Run the build and save the full log:**

```
.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm NetworkSwissToolPro_v7.0.65.spec > build_v7.0.65.log 2>&1
```

This saves everything to `build_v7.0.65.log` in the project folder.

**Watch the build live (alternative — shows on screen AND saves):**

```
.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm NetworkSwissToolPro_v7.0.65.spec
```

---

## Step 5 — Read the build log

After the build finishes, check the log for warnings and errors:

```
type build_v7.0.65.log | more
```

Or open `build_v7.0.65.log` in Notepad.

**What to look for in the log:**

### GOOD lines (expected):
```
INFO: PyInstaller: 6.x.x, contrib hooks: ...
INFO: Python: 3.12.x
INFO: Building COLLECT ...
INFO: Building EXE from EXE-00.toc
INFO: Appending archive to EXE ...
INFO: Building EXE ... completed successfully.
```

### WARNING lines (safe to ignore):
```
WARNING: Hidden import "X" not found
WARNING: lib not found: ...dll
```
These are almost always harmless — PyInstaller being cautious.

### ERROR lines (must fix before using EXE):
```
ERROR: ...
ModuleNotFoundError: ...
```
If you see errors, scroll to the first one and fix that module first.

**Find errors quickly:**

```
findstr /i "ERROR" build_v7.0.65.log
```

**Find missing modules:**

```
findstr /i "not found" build_v7.0.65.log
```

---

## Step 6 — Verify the EXE was created

```
dir dist\NetworkSwissToolPro_v7.0.65_OFFLINE.exe
```

Expected:
- File exists in `dist\`
- Size is between **80 MB and 140 MB**

If the file is smaller than 80 MB, something was missed — re-check Step 2.

---

## Step 7 — Test the EXE

**Basic launch test:**

```
dist\NetworkSwissToolPro_v7.0.65_OFFLINE.exe
```

The browser should open automatically to `http://127.0.0.1:5000` within 5–10 seconds.

**Test with console visible (shows startup errors):**

```
dist\NetworkSwissToolPro_v7.0.65_OFFLINE.exe --debug
```

Or temporarily change `console=False` to `console=True` in the spec file, rebuild,
and run — you'll see all Python output directly.

**Test offline (disconnect from internet, then run the EXE):**
- It should start with no network errors
- The web UI should load fully
- The Swiss Tools tab should show all 5 map buttons

---

## Step 8 — Copy EXE to distribution folder (optional)

```
copy dist\NetworkSwissToolPro_v7.0.65_OFFLINE.exe dist_package_web\NetworkSwissToolPro_v7.0.65_OFFLINE.exe
```

---

## Troubleshooting common issues

### "ModuleNotFoundError: No module named 'X'" at runtime
- Add `'X'` to the `hiddenimports` list in `NetworkSwissToolPro_v7.0.65.spec`
- Rebuild from Step 4

### EXE launches but browser shows blank page
- Run with console=True and check for Flask startup errors
- Usually a missing template file — check `datas` in the spec file includes `modules/web/templates`

### "vis.Network is not defined" in L3 map
- `modules/web/vis-network.min.js` must be in `datas` — it is in the spec
- Confirm the file exists: `dir modules\web\vis-network.min.js`

### Build fails: "copy_metadata('X') failed"
- The package is not installed in `.venv`
- Run: `.venv\Scripts\python.exe -m pip install X`

### PyInstaller version mismatch
- Confirm: `.venv\Scripts\python.exe -m pip show pyinstaller` → should be 6.x
- If wrong: `.venv\Scripts\python.exe -m pip install pyinstaller==6.19.0`

### "UPX is not available" warning
- Safe to ignore — UPX compression is disabled (`upx=False`) in the spec file

---

## Quick reference — all commands in order

```
cd "c:\Users\bbb12\OneDrive\Desktop\Antigravity Projects Folder\net_mng_tool_cartography"
.venv\Scripts\activate.bat
.venv\Scripts\python.exe -m pip install -r requirements.txt --upgrade
.venv\Scripts\python.exe _prebuild.py
.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm NetworkSwissToolPro_v7.0.65.spec
dir dist\NetworkSwissToolPro_v7.0.65_OFFLINE.exe
dist\NetworkSwissToolPro_v7.0.65_OFFLINE.exe
```

---

## Files created by this build

| File | Description |
|------|-------------|
| `dist\NetworkSwissToolPro_v7.0.65_OFFLINE.exe` | The final offline EXE |
| `build\NetworkSwissToolPro_v7.0.65_OFFLINE\` | Intermediate build folder (safe to delete) |
| `build_v7.0.65.log` | Full build log (if you used the redirect command) |
| `NetworkSwissToolPro_v7.0.65.spec` | The PyInstaller spec used for this build |

---

*Version 7.0.65 — L3 cartography integration (IOS, NX-OS, Junos), routing parser fixes,
 VRF-aware collection, offline vis.js map rendering.*

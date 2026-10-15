@echo off
chcp 65001 >nul
echo ============================================================
echo  Network Swiss Tool Pro v6.5.3 - Build Script
echo ============================================================
echo.
echo  Fixes in v6.5.3:
echo   - Plugin registry syntax error fixed (all 9 plugins load)
echo   - Missing plugin report functions added to report_formatter
echo   - Single device VLAN scope fix (no more 0 target devices)
echo   - vPC topology map: hierarchical layout + structured table
echo   - Topology side panel: speed, VLAN, duplex, MAC per interface
echo.
echo ============================================================
echo.

REM Robustly find the project root
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%.."
echo [INFO] Working directory: %CD%

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH
    pause
    exit /b 1
)

echo [1/6] Verifying requirements...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [WARNING] Some packages may not have installed correctly, continuing...
)
echo [OK] Requirements ready
echo.

echo [2/6] Validating source files...
if not exist "vlan_checker_web.py" (
    echo [ERROR] vlan_checker_web.py not found!
    pause
    exit /b 1
)
if not exist "modules\web\templates\index.html" (
    echo [ERROR] Web templates not found!
    pause
    exit /b 1
)
if not exist "modules\plugin_registry.py" (
    echo [ERROR] plugin_registry.py not found!
    pause
    exit /b 1
)
if not exist "utils\report_formatter.py" (
    echo [ERROR] report_formatter.py not found!
    pause
    exit /b 1
)
echo [OK] Source files validated
echo.

echo [3/6] Running pre-build syntax check...
python -c "
import sys, ast
files = [
    'vlan_checker_web.py',
    'modules/plugin_registry.py',
    'modules/adapters.py',
    'modules/topology_mapper.py',
    'utils/report_formatter.py',
]
ok = True
for f in files:
    try:
        ast.parse(open(f, encoding='utf-8').read())
        print(f'  OK: {f}')
    except SyntaxError as e:
        print(f'  SYNTAX ERROR: {f} line {e.lineno}: {e.msg}')
        ok = False
sys.exit(0 if ok else 1)
"
if errorlevel 1 (
    echo [ERROR] Syntax check failed! Fix errors before building.
    pause
    exit /b 1
)
echo [OK] Syntax check passed
echo.

echo [4/6] Running plugin load check...
python -c "
import sys
sys.path.insert(0, '.')
from modules.plugin_registry import get_registry
r = get_registry()
count = len(r.get_all_metadata())
errors = len(r.get_errors())
print(f'  Plugins loaded: {count}')
print(f'  Load errors:    {errors}')
if errors > 0:
    for e in r.get_errors():
        print(f'  ERROR: {e[\"file\"]}: {e[\"error\"]}')
    sys.exit(1)
sys.exit(0)
" 2>&1
if errorlevel 1 (
    echo [ERROR] Plugin load check failed!
    pause
    exit /b 1
)
echo [OK] All plugins load successfully
echo.

echo [5/6] Building EXE with PyInstaller...
echo This will take several minutes...
echo.

python -m PyInstaller --clean --noconfirm build_scripts\NetworkSwissToolPro_v6_5_3.spec

if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller build failed!
    echo Check output above for details.
    pause
    exit /b 1
)
echo.
echo [OK] EXE built successfully
echo.

echo [6/6] Creating distribution package...
set DIST_NAME=dist_package_v6_5_3
if exist "%DIST_NAME%" rd /s /q "%DIST_NAME%"
mkdir "%DIST_NAME%"
mkdir "%DIST_NAME%\logs"
mkdir "%DIST_NAME%\reports"
mkdir "%DIST_NAME%\backups\plugins"
mkdir "%DIST_NAME%\scratch\uploads"
mkdir "%DIST_NAME%\plugins"

copy /Y "dist\NetworkSwissToolPro_v6_5_3.exe" "%DIST_NAME%\" >nul
copy /Y "README.md" "%DIST_NAME%\" >nul
copy /Y "CHANGELOG.md" "%DIST_NAME%\" >nul
copy /Y "VERSION" "%DIST_NAME%\" >nul
copy /Y "PLUGINS_INCLUDED.txt" "%DIST_NAME%\" >nul
copy /Y "inventory.txt" "%DIST_NAME%\" >nul
copy /Y "walkthrough_v6.txt" "%DIST_NAME%\" >nul
xcopy /E /I /Y "docs" "%DIST_NAME%\docs" >nul 2>&1
xcopy /E /I /Y "modules\plugins" "%DIST_NAME%\plugins" >nul 2>&1
xcopy /E /I /Y "policies" "%DIST_NAME%\policies" >nul 2>&1

echo [OK] Distribution package created: %DIST_NAME%
echo.

echo ============================================================
echo  BUILD SUCCESSFUL: v6.5.3
echo ============================================================
echo.
echo  EXE:      %DIST_NAME%\NetworkSwissToolPro_v6_5_3.exe
echo  Plugins:  9 bundled
echo  Offline:  Yes (all dependencies bundled)
echo.
echo  Fixes applied:
echo   [P0] Plugin registry syntax error fixed
echo   [P0] Missing plugin report functions added
echo   [P1] Single device VLAN scope fixed
echo   [P1] vPC topology layout improved
echo   [P1] Topology side panel speed/VLAN/MAC added
echo.
echo ============================================================
echo.

explorer "%DIST_NAME%"
pause

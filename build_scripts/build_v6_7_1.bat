@echo off
chcp 65001 >nul
echo ============================================================
echo  Network Swiss Tool Pro v6.7.1 - Build Script
echo ============================================================
echo.
echo  Fixes in v6.7.1:
echo   - Fixed AttributeError in Flask-SocketIO (Flask 3.1)
echo   - Hardened CLI WebSocket routing (Hybrid Room+SID)
echo   - Standardized SSH background handshake reporting
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
echo [OK] Source files validated
echo.

echo [3/6] Running pre-build validation...
python build_scripts\prebuild_checks.py
if errorlevel 1 (
    echo [ERROR] Pre-build validation failed! Fix errors before building.
    pause
    exit /b 1
)
echo [OK] Validation passed
echo.

echo [5/6] Building EXE with PyInstaller...
echo This will take several minutes...
echo.

python -m PyInstaller --clean --noconfirm build_scripts\NetworkSwissToolPro_v6_7_1.spec

if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller build failed!
    pause
    exit /b 1
)
echo.
echo [OK] EXE built successfully
echo.

echo [6/6] Creating distribution package...
set DIST_NAME=dist_package_v6.7.1
if exist "%DIST_NAME%" rd /s /q "%DIST_NAME%"
mkdir "%DIST_NAME%"
mkdir "%DIST_NAME%\logs"
mkdir "%DIST_NAME%\reports"
mkdir "%DIST_NAME%\backups\plugins"
mkdir "%DIST_NAME%\scratch\uploads"
mkdir "%DIST_NAME%\plugins"

copy /Y "dist\NetworkSwissToolPro_v6.7.1.exe" "%DIST_NAME%\" >nul
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
echo  BUILD SUCCESSFUL: v6.7.1
echo ============================================================
echo.
echo  EXE:      %DIST_NAME%\NetworkSwissToolPro_v6.7.1.exe
echo  Status:   Resilient CLI Fix Applied
echo.
echo ============================================================
echo.

explorer "%DIST_NAME%"
pause

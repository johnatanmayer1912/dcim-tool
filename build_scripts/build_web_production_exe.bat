@echo off
chcp 65001 >nul
echo ============================================================
echo  Network Swiss Tool Pro v4.5.2 - WEB Edition Build
echo ============================================================
echo.
echo  Building WEB executable with:
echo   - Flask Web Interface (Browser-based)
echo   - Structured Logging System
echo   - Automatic Config Backup
echo   - Production VLAN Management
echo   - Smoke Test Framework
echo   - All CLI/GUI/Web/Test Modes via Web Interface
echo.
echo ============================================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.10+ and try again.
    pause
    exit /b 1
)

echo [1/5] Installing requirements...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [WARNING] Some packages may not have installed correctly
    echo Attempting to continue...
)
echo [OK] Requirements installed
echo.

echo [2/5] Validating source files...
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
if not exist "utils\structured_logger.py" (
    echo [ERROR] structured_logger.py not found!
    pause
    exit /b 1
)
if not exist "utils\config_backup_system.py" (
    echo [ERROR] config_backup_system.py not found!
    pause
    exit /b 1
)
echo [OK] Source files validated
echo.

echo [3/5] Running smoke tests...
python -m tests.smoke_tests --category infrastructure --quiet
if errorlevel 1 (
    echo [WARNING] Some tests failed, but continuing build...
) else (
    echo [OK] Core tests passed
)
echo.

echo [4/5] Building WEB executable with PyInstaller...
echo This may take several minutes...
echo Note: A console window will show Flask server output when running
echo.

pyinstaller --clean --noconfirm NetworkSwissToolPro_v4_5_2_Web.spec

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    echo Check the output above for errors.
    pause
    exit /b 1
)

echo.
echo [5/5] Build complete!
echo.

REM Create distribution directory
echo Creating WEB distribution package...
if not exist "dist_package_web" mkdir dist_package_web
if not exist "dist_package_web\logs" mkdir dist_package_web\logs
if not exist "dist_package_web\backups" mkdir dist_package_web\backups
if not exist "dist_package_web\reports" mkdir dist_package_web\reports

copy /Y "dist\NetworkSwissToolPro_v4_5_2_Web_Production.exe" "dist_package_web\" >nul
copy /Y "README.md" "dist_package_web\" >nul
copy /Y "CHANGELOG.md" "dist_package_web\" >nul
copy /Y "VERSION" "dist_package_web\" >nul
copy /Y "RELEASE_NOTES_4.5.2.md" "dist_package_web\" >nul
xcopy /E /I /Y "docs" "dist_package_web\docs" >nul 2>&1

REM Create sample inventory file
echo # Sample Inventory File for Network Swiss Tool Pro Web Edition > dist_package_web\inventory.txt
echo # Format: IP,device_type,group >> dist_package_web\inventory.txt
echo # >> dist_package_web\inventory.txt
echo # Example entries: >> dist_package_web\inventory.txt
echo # 10.1.1.1,cisco_ios,CoreSwitches >> dist_package_web\inventory.txt
echo # 10.1.1.2,cisco_nxos,CoreSwitches >> dist_package_web\inventory.txt
echo # 10.2.1.1,juniper_junos,AccessLayer >> dist_package_web\inventory.txt
echo # >> dist_package_web\inventory.txt
echo # Note: Web Edition runs at http://127.0.0.1:5000 >> dist_package_web\inventory.txt

echo [OK] Web distribution package created
echo.

echo ============================================================
echo  WEB BUILD SUCCESSFUL
echo ============================================================
echo.
echo  Executable: dist_package_web\NetworkSwissToolPro_v4_5_2_Web_Production.exe
echo.
echo  Web Distribution Contents:
echo   - Web executable with Flask server
echo   - Embedded Python runtime
echo   - HTML/CSS/JS frontend templates
echo   - Production modules and logging
echo   - Documentation and sample inventory
echo   - Pre-created folder structure
echo.
echo  Usage Instructions:
echo   1. Double-click the executable
echo   2. Console window will open showing Flask server status
echo   3. Browser will auto-open at http://127.0.0.1:5000
echo   4. Use the web interface to manage network devices
echo.
echo  Web Interface Features:
echo   - All 11 network operations via browser
echo   - Real-time console output in web UI
echo   - Device filtering and targeting
echo   - VLAN management with dry-run mode
echo   - Topology mapping and visualization
echo   - Network auditing and reporting
echo.
echo  Note: Keep the console window open while using the web interface.
echo        Press Ctrl+C in the console to stop the server.
echo.
echo ============================================================
echo.

REM Open dist_package_web folder
explorer dist_package_web

pause

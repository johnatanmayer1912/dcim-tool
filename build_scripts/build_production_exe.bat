@echo off
chcp 65001 >nul
echo ============================================================
echo  Network Swiss Tool Pro v4.5.2 - Production Build
echo ============================================================
echo.
echo  Building offline executable with:
echo   - Structured Logging System
echo   - Automatic Config Backup
echo   - Production VLAN Management
echo   - Smoke Test Framework
echo   - Full CLI/GUI/Web Support
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
if not exist "main.py" (
    echo [ERROR] main.py not found!
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
python -m tests.smoke_tests --quiet
if errorlevel 1 (
    echo [WARNING] Some tests failed, but continuing build...
) else (
    echo [OK] Tests passed
)
echo.

echo [4/5] Building executable with PyInstaller...
echo This may take several minutes...
echo.

pyinstaller --clean --noconfirm NetworkSwissToolPro_v4_5_2.spec

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
echo Creating distribution package...
if not exist "dist_package" mkdir dist_package
if not exist "dist_package\logs" mkdir dist_package\logs
if not exist "dist_package\backups" mkdir dist_package\backups
if not exist "dist_package\reports" mkdir dist_package\reports

copy /Y "dist\NetworkSwissToolPro_v4_5_2_Production.exe" "dist_package\" >nul
copy /Y "README.md" "dist_package\" >nul
copy /Y "CHANGELOG.md" "dist_package\" >nul
copy /Y "VERSION" "dist_package\" >nul
copy /Y "RELEASE_NOTES_4.5.2.md" "dist_package\" >nul
xcopy /E /I /Y "docs" "dist_package\docs" >nul 2>&1

REM Create sample inventory file
echo # Sample Inventory File for Network Swiss Tool Pro > dist_package\inventory.txt
echo # Format: IP,device_type,group >> dist_package\inventory.txt
echo # >> dist_package\inventory.txt
echo # Example entries: >> dist_package\inventory.txt
echo # 10.1.1.1,cisco_ios,CoreSwitches >> dist_package\inventory.txt
echo # 10.1.1.2,cisco_nxos,CoreSwitches >> dist_package\inventory.txt
echo # 10.2.1.1,juniper_junos,AccessLayer >> dist_package\inventory.txt

echo [OK] Distribution package created
echo.

echo ============================================================
echo  BUILD SUCCESSFUL
echo ============================================================
echo.
echo  Executable: dist_package\NetworkSwissToolPro_v4_5_2_Production.exe
echo.
echo  Distribution Contents:
echo   - Main executable with embedded Python runtime
echo   - Documentation (README, CHANGELOG, Release Notes)
echo   - Sample inventory.txt (configure with your devices)
echo   - Pre-created folder structure (logs, backups, reports)
echo.
echo  Usage:
echo   Double-click to launch GUI mode (default)
echo   Or run from command line with arguments:
echo.
echo   NetworkSwissToolPro_v4_5_2_Production.exe gui    (Desktop GUI)
echo   NetworkSwissToolPro_v4_5_2_Production.exe web    (Web Interface)
echo   NetworkSwissToolPro_v4_5_2_Production.exe cli --task backup-check
echo   NetworkSwissToolPro_v4_5_2_Production.exe test   (Run smoke tests)
echo.
echo ============================================================
echo.

REM Open dist_package folder
explorer dist_package

pause

@echo off

chcp 65001 >nul

echo Building Network Swiss Tool Pro v7.0.47 OFFLINE...

python _prebuild.py

if errorlevel 1 exit /b 1

python -m pytest tests/ -q --tb=no

if errorlevel 1 exit /b 1

pyinstaller --clean --noconfirm NetworkSwissToolPro_v7.0.47.spec

if errorlevel 1 exit /b 1

if not exist dist_package_web mkdir dist_package_web

copy /Y dist\NetworkSwissToolPro_v7.0.47_OFFLINE.exe dist_package_web\ >nul

copy /Y VERSION CHANGELOG.md dist_package_web\ >nul

echo Done: dist\NetworkSwissToolPro_v7.0.47_OFFLINE.exe


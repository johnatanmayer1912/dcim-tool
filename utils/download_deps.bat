@echo off
set "DEPS_DIR=paramiko_deps"

if not exist "%DEPS_DIR%" (
    mkdir "%DEPS_DIR%"
)

echo Downloading dependencies to %DEPS_DIR%...
pip download -r requirements.txt -d "%DEPS_DIR%"

echo.
echo Dependencies downloaded. To install offline, use:
echo pip install --no-index --find-links="%DEPS_DIR%" -r requirements.txt
pause

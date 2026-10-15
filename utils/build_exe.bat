@echo off
echo Installing requirements...
pip install -r requirements.txt

echo.
echo Building executable...
pyinstaller --onefile --noconsole --add-data "modules/web/vis-network.min.js;." --name VlanCheckerGUI vlan_checker_gui.py

echo.
echo Build complete.
echo The executable is located at: %CD%\dist\VlanCheckerGUI.exe
pause

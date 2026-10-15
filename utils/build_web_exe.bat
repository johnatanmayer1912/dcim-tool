@echo off
echo Building VlanCheckerWeb.exe...
pyinstaller --noconfirm --onefile --windowed --add-data "modules/web/templates;templates" --add-data "modules/web/vis-network.min.js;." --add-data "README.md;." --name "VlanCheckerWeb" "vlan_checker_web.py"
echo Build complete.

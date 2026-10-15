"""
Build script for Network Swiss Tool Pro
Runs pre-build validation and creates Windows EXE via PyInstaller
"""

import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and display output"""
    print(f"\n{description}...")
    print(f"Command: {' '.join(command)}")
    
    result = subprocess.run(command, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    
    if result.stderr:
        print(result.stderr)
    
    return result.returncode == 0

def main():
    """Main build process"""
    print("=" * 60)
    print("NETWORK SWISS TOOL PRO BUILD PROCESS")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    
    # Step 1: Run pre-build validation
    print("\n[1/4] Running pre-build validation...")
    if not run_command([sys.executable, "_prebuild.py"], "Pre-build validation"):
        print("\n[FAIL] PRE-BUILD VALIDATION FAILED - ABORTING BUILD")
        sys.exit(1)
    
    print("\n[PASS] Pre-build validation passed")
    
    # Step 2: Get version from VERSION file
    print("\n[2/4] Reading version...")
    version_file = base_dir / "VERSION"
    if version_file.exists():
        version = version_file.read_text(encoding='utf-8').strip()
        print(f"  Version: {version}")
    else:
        print("  [FAIL] VERSION file not found")
        sys.exit(1)
    
    # Step 3: Build EXE with PyInstaller
    print("\n[3/4] Building Windows EXE...")
    spec_file = base_dir / f"NetworkSwissToolPro_v{version}.spec"
    if spec_file.exists():
        if not run_command([sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", str(spec_file)], "PyInstaller build"):
            print("\n[FAIL] PYINSTALLER BUILD FAILED")
            sys.exit(1)
    else:
        print(f"  [FAIL] Spec file not found: {spec_file}")
        sys.exit(1)
    
    # Step 4: Copy data files to dist
    print("\n[4/4] Copying data files to dist...")
    import shutil
    dist_dir = base_dir / "dist"
    
    # Copy config directory
    config_dir = base_dir / "config"
    if config_dir.exists():
        shutil.copytree(config_dir, dist_dir / "config", dirs_exist_ok=True)
        print("[PASS] config directory copied")
    
    # Copy policies directory
    policies_dir = base_dir / "policies"
    if policies_dir.exists():
        shutil.copytree(policies_dir, dist_dir / "policies", dirs_exist_ok=True)
        print("[PASS] policies directory copied")
    
    # Copy standards directory
    standards_dir = base_dir / "standards"
    if standards_dir.exists():
        shutil.copytree(standards_dir, dist_dir / "standards", dirs_exist_ok=True)
        print("[PASS] standards directory copied")
    
    # Copy inventory directory
    inventory_dir = base_dir / "inventory"
    if inventory_dir.exists():
        shutil.copytree(inventory_dir, dist_dir / "inventory", dirs_exist_ok=True)
        print("[PASS] inventory directory copied")

    # Copy plugins directory
    plugins_dir = base_dir / "modules" / "plugins"
    if plugins_dir.exists():
        shutil.copytree(plugins_dir, dist_dir / "plugins", dirs_exist_ok=True)
        print("[PASS] plugins directory copied")

    # Copy tests/qa readiness register into dist
    readiness_json = base_dir / "tests" / "qa" / "PHASE5_DISCOVERY_READINESS.json"
    if readiness_json.exists():
        (dist_dir / "tests" / "qa").mkdir(parents=True, exist_ok=True)
        shutil.copy2(readiness_json, dist_dir / "tests" / "qa" / "PHASE5_DISCOVERY_READINESS.json")
        print("[PASS] PHASE5_DISCOVERY_READINESS.json copied")

    # Copy VERSION file
    if version_file.exists():
        shutil.copy2(version_file, dist_dir / "VERSION")
        print("[PASS] VERSION copied")
    
    print("\n" + "=" * 60)
    print("[PASS] BUILD SUCCESSFUL")
    print("=" * 60)
    print(f"\nExecutable location: dist/NetworkSwissToolPro_v{version}.exe")
    print(f"Version: {version}")
    print(f"\nTo run the application:")
    print("  1. Navigate to dist/")
    print("  2. Run NetworkSwissToolPro_v{version}.exe")
    print("  3. Open browser to http://127.0.0.1:4444")
    print("\nOr copy the entire dist/ directory to target machine.")

if __name__ == "__main__":
    main()
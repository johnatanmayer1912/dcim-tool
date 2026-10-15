"""Simulate frozen EXE plugin registry path for audit NEW-C1 (no GUI)."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# Reset singleton for clean test
import modules.plugin_registry as pr
pr.PluginRegistry._instance = None
pr.PluginRegistry._initialized = False


def simulate_frozen(exe_dir: str, meipass: str):
    sys.frozen = True  # type: ignore
    sys._MEIPASS = meipass  # type: ignore
    sys.executable = os.path.join(exe_dir, "NetworkSwissToolPro_v7.0.2_OFFLINE.exe")

    pr.PluginRegistry._instance = None
    pr.PluginRegistry._initialized = False
    reg = pr.get_registry()
    py_files = []
    if os.path.isdir(reg.plugins_dir):
        py_files = [f for f in os.listdir(reg.plugins_dir) if f.endswith(".py") and not f.startswith("_")]
    bundled = os.path.join(meipass, "modules", "plugins")
    bundled_count = 0
    if os.path.isdir(bundled):
        bundled_count = len([f for f in os.listdir(bundled) if f.endswith(".py") and f != "base_template.py"])
    return {
        "exe_dir": exe_dir,
        "plugins_dir": reg.plugins_dir,
        "plugins_dir_exists": os.path.isdir(reg.plugins_dir),
        "py_in_plugins_dir": len(py_files),
        "loaded_count": len(reg.get_all_metadata()),
        "load_errors": len(reg.get_errors()),
        "bundled_meipass_plugins": bundled,
        "bundled_py_count": bundled_count,
    }


if __name__ == "__main__":
    import tempfile
    bare_exe_dir = tempfile.mkdtemp(prefix="nst_audit_bare_")
    # PyInstaller one-file extracts to _MEIPASS; use project modules/plugins as bundle stand-in
    meipass = ROOT
    bare = simulate_frozen(bare_exe_dir, meipass)
    # Dev layout for comparison
    sys.frozen = False
    if hasattr(sys, "_MEIPASS"):
        delattr(sys, "_MEIPASS")
    pr.PluginRegistry._instance = None
    pr.PluginRegistry._initialized = False
    dev_reg = pr.get_registry()
    dev = {
        "plugins_dir": dev_reg.plugins_dir,
        "loaded_count": len(dev_reg.get_all_metadata()),
    }
    print("=== NEW-C1 frozen simulation (bare dist/, no sidecar plugins/) ===")
    for k, v in bare.items():
        print(f"  {k}: {v}")
    print("=== Dev mode (reference) ===")
    for k, v in dev.items():
        print(f"  {k}: {v}")
    print("=== Verdict ===")
    if bare["loaded_count"] < 10 and bare["bundled_py_count"] >= 10:
        print("  CONFIRMED NEW-C1: registry scans empty exe_dir/plugins while bundle has plugins")
    elif bare["loaded_count"] >= 10:
        print("  NOT REPRODUCED: plugins loaded in simulated bare layout")
    else:
        print("  INCONCLUSIVE: check build/_MEIPASS path or run live EXE smoke")

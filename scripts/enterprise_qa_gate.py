#!/usr/bin/env python3
"""Enterprise QA gate — delegates to mandatory_release_qa orchestrator."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(cmd, label):
    print(f"\n{'=' * 60}\n{label}\n{'=' * 60}")
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode != 0:
        print(f"FAIL: {label}")
        return False
    print(f"PASS: {label}")
    return True


def main():
    ok = True
    ok &= run(
        [sys.executable, "scripts/mandatory_release_qa.py", "--phase", "pre_release"],
        "mandatory release QA (pre_release)",
    )
    print("\n" + "=" * 60)
    if ok:
        print("ENTERPRISE QA GATE: PASS")
        return 0
    print("ENTERPRISE QA GATE: FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())

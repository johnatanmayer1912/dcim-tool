import sys
import ast
import os

def run_checks():
    print("[Pre-build] Running syntax checks...")
    files = [
        'vlan_checker_web.py',
        'modules/plugin_registry.py',
        'modules/adapters.py',
        'modules/topology_mapper.py',
        'utils/report_formatter.py',
    ]
    ok = True
    for f in files:
        if not os.path.exists(f):
            print(f"  MISSING: {f}")
            ok = False
            continue
        try:
            ast.parse(open(f, encoding='utf-8').read())
            print(f"  OK (Syntax): {f}")
        except SyntaxError as e:
            print(f"  SYNTAX ERROR: {f} line {e.lineno}: {e.msg}")
            ok = False
            
    print("\n[Pre-build] Running plugin load check...")
    sys.path.insert(0, '.')
    try:
        from modules.plugin_registry import get_registry
        r = get_registry()
        count = len(r.get_all_metadata())
        errors = len(r.get_errors())
        print(f"  Plugins loaded: {count}")
        print(f"  Load errors:    {errors}")
        if errors > 0:
            for e in r.get_errors():
                print(f"  ERROR: {e['file']}: {e['error']}")
            ok = False
    except Exception as e:
        print(f"  FATAL: Could not load plugin registry: {e}")
        ok = False

    return ok

if __name__ == "__main__":
    if run_checks():
        print("\n[Pre-build] ALL CHECKS PASSED")
        sys.exit(0)
    else:
        print("\n[Pre-build] CHECKS FAILED")
        sys.exit(1)

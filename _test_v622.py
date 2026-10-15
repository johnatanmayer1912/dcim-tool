"""Validation for v6.2.2 fixes."""
import sys, re, inspect
errors = []

print("=" * 60)
print("  v6.2.2 Validation")
print("=" * 60)
print()

# Test 1: topology_mapper dtype is pre-lowercased
print("Test 1: topology_mapper — dtype pre-lowercased, no NoneType crash")
try:
    import modules.topology_mapper as tm
    with open('modules/topology_mapper.py', 'r', encoding='utf-8') as f:
        src = f.read()
    assert "dtype = (device.get('device_type') or 'cisco_ios').lower()" in src, \
        "dtype not pre-lowercased"
    assert "dtype.lower()" not in src, "dtype.lower() still present"
    assert "if not true_host:" in src, "true_host None guard missing"
    print("  [PASS] dtype pre-lowercased at assignment")
    print("  [PASS] true_host None guard present")
    print("  [PASS] No dtype.lower() calls remaining")
except Exception as e:
    errors.append(f"topology_mapper: {e}")
    print(f"  [FAIL] {e}")
print()

# Test 2: cli_manager — no ThreadPoolExecutor
print("Test 2: cli_manager — ThreadPoolExecutor removed from connect()")
try:
    with open('modules/cli_manager.py', 'r', encoding='utf-8') as f:
        cli_src = f.read()
    assert 'from concurrent.futures import ThreadPoolExecutor' not in cli_src, \
        "ThreadPoolExecutor import still present"
    assert 'FuturesTimeout' not in cli_src, "FuturesTimeout still present"
    assert 'threading.Timer' in cli_src, "Watchdog timer missing"
    assert '_watchdog' in cli_src, "_watchdog function missing"
    print("  [PASS] ThreadPoolExecutor removed")
    print("  [PASS] Watchdog timer added")
except Exception as e:
    errors.append(f"cli_manager ThreadPoolExecutor: {e}")
    print(f"  [FAIL] {e}")
print()

# Test 3: cli_manager imports cleanly
print("Test 3: cli_manager imports cleanly")
try:
    import modules.cli_manager as cm
    assert hasattr(cm, 'CLIConnection')
    assert hasattr(cm, 'create_cli_session')
    # Test CLIConnection instantiation
    device = {'host': '10.0.0.1', 'device_type': 'cisco_ios', 'port': 22}
    cli = cm.CLIConnection('test', device, 'user', 'pass', '')
    assert cli.port == 22
    assert cli.connected == False
    print("  [PASS] cli_manager imports cleanly")
    print("  [PASS] CLIConnection instantiates correctly")
except Exception as e:
    errors.append(f"cli_manager import: {e}")
    print(f"  [FAIL] {e}")
print()

# Test 4: topology_mapper imports cleanly
print("Test 4: topology_mapper imports cleanly")
try:
    import modules.topology_mapper as tm
    assert hasattr(tm, 'run')
    assert hasattr(tm, 'safe_node_name')
    assert hasattr(tm, '_parse_cdp_detail')
    # Test safe_node_name with edge cases
    assert tm.safe_node_name(None) == "unknown"
    assert tm.safe_node_name("") == "unknown"
    assert tm.safe_node_name("switch") is None  # blacklisted
    assert tm.safe_node_name("CORE-SW-01") == "core-sw-01"
    print("  [PASS] topology_mapper imports cleanly")
    print("  [PASS] safe_node_name handles None/empty/blacklisted correctly")
except Exception as e:
    errors.append(f"topology_mapper import: {e}")
    print(f"  [FAIL] {e}")
print()

# Test 5: double-emit still present in vlan_checker_web.py
print("Test 5: double-emit (room + SID) still present")
try:
    with open('vlan_checker_web.py', 'r', encoding='utf-8') as f:
        web = f.read()
    bg_start = web.find('def background_connect()')
    bg_end = web.find('\n        socketio.start_background_task(background_connect)', bg_start)
    bg_code = web[bg_start:bg_end]
    assert bg_code.count("socketio.emit('cli_status'") >= 2, "cli_status not double-emitted"
    assert bg_code.count("socketio.emit('cli_error'") >= 2, "cli_error not double-emitted"
    print("  [PASS] cli_status double-emitted")
    print("  [PASS] cli_error double-emitted")
except Exception as e:
    errors.append(f"double-emit: {e}")
    print(f"  [FAIL] {e}")
print()

# Test 6: VERSION updated
print("Test 6: VERSION updated to 6.2.2")
try:
    m = re.search(r'VERSION = "(.+?)"', web)
    assert m and '6.2.2' in m.group(1), f"VERSION not 6.2.2: {m.group(1) if m else 'not found'}"
    print(f"  [PASS] VERSION = {m.group(1)}")
except Exception as e:
    errors.append(f"VERSION: {e}")
    print(f"  [FAIL] {e}")
print()

# Test 7: Regression — two-pass SSH still intact
print("Test 7: Regression — two-pass SSH still intact")
try:
    assert 'Pass 1' in cli_src and 'Pass 2' in cli_src
    assert 'AuthenticationException' in cli_src
    print("  [PASS] Two-pass SSH intact")
except Exception as e:
    errors.append(f"two-pass SSH: {e}")
    print(f"  [FAIL] {e}")
print()

print("=" * 60)
if not errors:
    print("  ALL TESTS PASSED ✓")
    print()
    print("  Fixes:")
    print("  [CLI]  Removed nested ThreadPoolExecutor — connect() now direct")
    print("  [CLI]  Watchdog timer replaces executor timeout")
    print("  [TOPO] dtype pre-lowercased — no more NoneType.lower() crash")
    print("  [TOPO] true_host None guard added")
    sys.exit(0)
else:
    print(f"  FAILED: {len(errors)} test(s):")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

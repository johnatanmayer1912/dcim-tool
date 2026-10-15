"""
Basic Lab Tests - Simple validation of Docker SSH simulator
Tests connectivity and basic functionality without full UI
"""
import paramiko
import time
import sys

# Lab configuration
LAB_DEVICES = {
    'ios_access': {'host': '127.0.0.1', 'port': 2201, 'username': 'admin', 'password': 'admin', 'device_type': 'cisco_ios'},
    'nxos_leaf1': {'host': '127.0.0.1', 'port': 2202, 'username': 'admin', 'password': 'admin', 'device_type': 'cisco_nxos'},
    'nxos_leaf2': {'host': '127.0.0.1', 'port': 2203, 'username': 'admin', 'password': 'admin', 'device_type': 'cisco_nxos'},
}

def test_ssh_connection(device_name, device_config):
    """Test SSH connection to a lab device."""
    print(f"\n[TEST] Connecting to {device_name} ({device_config['host']}:{device_config['port']})...")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=device_config['host'],
            port=device_config['port'],
            username=device_config['username'],
            password=device_config['password'],
            timeout=10
        )
        
        # Run a simple command
        stdin, stdout, stderr = ssh.exec_command('show version')
        output = stdout.read().decode('utf-8')
        
        ssh.close()
        
        print(f"✓ PASS: Connected to {device_name}")
        print(f"  Output length: {len(output)} characters")
        return True
    except Exception as e:
        print(f"✗ FAIL: Could not connect to {device_name}")
        print(f"  Error: {e}")
        return False

def test_lab_inventory():
    """Test lab inventory setup."""
    print("\n[TEST] Lab Inventory Configuration")
    print(f"  Total devices: {len(LAB_DEVICES)}")
    for name, config in LAB_DEVICES.items():
        print(f"  - {name}: {config['host']}:{config['port']} ({config['device_type']})")
    return True

def main():
    print("=" * 60)
    print("BASIC LAB VALIDATION TESTS")
    print("=" * 60)
    
    results = []
    
    # Test 1: Lab inventory
    results.append(("Lab Inventory", test_lab_inventory()))
    
    # Test 2-4: SSH connections
    for device_name, device_config in LAB_DEVICES.items():
        results.append((f"SSH Connection - {device_name}", test_ssh_connection(device_name, device_config)))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All basic lab tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())

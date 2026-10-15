"""
API-based Lab Tests - Tests NST application against Docker SSH simulator
Tests basic functionality without UI interaction
"""
import requests
import json
import time
import sys

# Configuration
BASE_URL = "http://127.0.0.1:5051"
LAB_INVENTORY = """127.0.0.1,cisco_ios
127.0.0.1,cisco_nxos
127.0.0.1,cisco_nos"""

def test_health_endpoint():
    """TEST-001: Health check"""
    print("\n[TEST-001] Health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200 and response.text == "OK":
            print("  PASS: Health endpoint returned OK")
            return True
        else:
            print(f"  FAIL: Status {response.status_code}, response: {response.text}")
            return False
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def test_vault_status():
    """TEST-002: Vault status"""
    print("\n[TEST-002] Vault status...")
    try:
        response = requests.get(f"{BASE_URL}/api/credentials/master-password/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  PASS: Vault status: {data.get('status', 'unknown')}")
            return True
        else:
            print(f"  FAIL: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def test_add_credential():
    """TEST-003: Add lab credential"""
    print("\n[TEST-003] Add lab credential...")
    try:
        # First check if credential already exists
        response = requests.get(f"{BASE_URL}/api/credentials/list", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                creds = data.get('credentials', [])
            else:
                creds = data if isinstance(data, list) else []
            
            for cred in creds:
                if isinstance(cred, dict) and cred.get('label') == 'Lab Device':
                    print("  SKIP: Lab Device credential already exists")
                    return True
        
        # Add new credential
        payload = {
            "username": "admin",
            "password": "admin",
            "enable_password": "admin",
            "label": "Lab Device",
            "profile": "ssh only"
        }
        response = requests.post(f"{BASE_URL}/api/credentials/add", json=payload, timeout=5)
        if response.status_code == 200:
            print("  PASS: Lab credential added successfully")
            return True
        else:
            print(f"  FAIL: Status {response.status_code}, response: {response.text}")
            return False
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def test_inventory_api():
    """TEST-004: Inventory API"""
    print("\n[TEST-004] Inventory API...")
    try:
        response = requests.get(f"{BASE_URL}/api/inventory", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  PASS: Inventory API returned {len(data.get('hosts', []))} hosts")
            return True
        else:
            print(f"  FAIL: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def test_inventory_preview():
    """TEST-005: Inventory preview with lab inventory"""
    print("\n[TEST-005] Inventory preview...")
    try:
        payload = {"inventory": LAB_INVENTORY}
        response = requests.post(f"{BASE_URL}/api/inventory/preview", json=payload, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  PASS: Preview returned {len(data.get('hosts', []))} hosts")
            for host in data.get('hosts', []):
                print(f"    - {host.get('host')}: {host.get('status')}")
            return True
        else:
            print(f"  FAIL: Status {response.status_code}, response: {response.text}")
            return False
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def test_inventory_commit():
    """TEST-006: Inventory commit"""
    print("\n[TEST-006] Inventory commit...")
    try:
        payload = {
            "inventory": LAB_INVENTORY,
            "mode": "replace",
            "confirm": True
        }
        response = requests.post(f"{BASE_URL}/api/inventory/commit", json=payload, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  PASS: Commit successful, {data.get('committed_count', 0)} hosts committed")
            return True
        else:
            print(f"  FAIL: Status {response.status_code}, response: {response.text}")
            return False
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def test_session_credentials():
    """TEST-007: Session credentials API"""
    print("\n[TEST-007: Session credentials API...")
    try:
        response = requests.get(f"{BASE_URL}/api/session/credentials", timeout=5)
        if response.status_code == 200:
            print("  PASS: Session credentials API accessible")
            return True
        else:
            print(f"  FAIL: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def test_capabilities_parsers():
    """TEST-008: Capabilities parsers API"""
    print("\n[TEST-008: Capabilities parsers API...")
    try:
        response = requests.get(f"{BASE_URL}/api/capabilities/parsers", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  PASS: Parsers API returned {len(data.get('parsers', []))} parsers")
            return True
        else:
            print(f"  FAIL: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def test_standards_policies():
    """TEST-009: Standards policies API"""
    print("\n[TEST-009: Standards policies API...")
    try:
        response = requests.get(f"{BASE_URL}/api/standards/policies?list_files=true", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  PASS: Policies API returned {len(data.get('files', []))} policy files")
            return True
        else:
            print(f"  FAIL: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def test_release_notes():
    """TEST-010: Release notes API"""
    print("\n[TEST-010: Release notes API...")
    try:
        response = requests.get(f"{BASE_URL}/api/release-notes", timeout=5)
        if response.status_code == 200:
            print("  PASS: Release notes API accessible")
            return True
        else:
            print(f"  FAIL: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def main():
    print("=" * 60)
    print("API-BASED LAB TESTS")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print(f"Lab Inventory: {LAB_INVENTORY}")
    
    results = []
    
    # Run tests
    results.append(("Health Endpoint", test_health_endpoint()))
    results.append(("Vault Status", test_vault_status()))
    results.append(("Add Lab Credential", test_add_credential()))
    results.append(("Inventory API", test_inventory_api()))
    results.append(("Inventory Preview", test_inventory_preview()))
    results.append(("Inventory Commit", test_inventory_commit()))
    results.append(("Session Credentials", test_session_credentials()))
    results.append(("Capabilities Parsers", test_capabilities_parsers()))
    results.append(("Standards Policies", test_standards_policies()))
    results.append(("Release Notes", test_release_notes()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All API tests passed!")
        return 0
    else:
        print(f"\n[FAILURE] {total - passed} test(s) failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())

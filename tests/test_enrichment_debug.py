"""Debug test for Cisco EOL enrichment - validates database lookup and enrichment flow."""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.cisco_eol_database import init_database, get_model_info, enrich_asset_data, get_all_models


def test_database_connection():
    """Test that database can be initialized and queried."""
    print("\n=== TEST 1: Database Connection ===")
    try:
        conn = init_database()
        print("✓ Database initialized successfully")
        
        # Get all models to verify database has data
        models = get_all_models()
        print(f"✓ Database contains {len(models)} models")
        
        # Check for specific requested models
        requested_pids = ['N9K-C9348GC-FXP', 'N9K-C9336C-FX2', 'N9K-C93180YC-FX3']
        for pid in requested_pids:
            found = any(m['pid'] == pid for m in models)
            status = "✓" if found else "✗"
            print(f"{status} {pid}: {'FOUND' if found else 'NOT FOUND'}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


def test_model_lookup():
    """Test direct model lookup by PID."""
    print("\n=== TEST 2: Model Lookup by PID ===")
    
    test_cases = [
        ('N9K-C9348GC-FXP', 'Should be in database'),
        ('N9K-C9336C-FX2', 'Should be in database'),
        ('N9K-C93180YC-FX3', 'Should be in database'),
        ('C9300-48P', 'Should be in database'),
        ('INVALID-PID', 'Should not be found'),
    ]
    
    all_passed = True
    for pid, description in test_cases:
        result = get_model_info(pid)
        if result:
            print(f"✓ {pid}: FOUND - {result.get('model_name', 'N/A')}")
            print(f"  EOL: {result.get('end_of_life', 'N/A')}")
            print(f"  EOS: {result.get('end_of_support', 'N/A')}")
        else:
            expected_fail = pid == 'INVALID-PID'
            status = "✓" if expected_fail else "✗"
            print(f"{status} {pid}: NOT FOUND ({description})")
            if not expected_fail:
                all_passed = False
    
    return all_passed


def test_enrichment_with_valid_pid():
    """Test enrichment with a valid PID that should be in database."""
    print("\n=== TEST 3: Enrichment with Valid PID ===")
    
    test_asset = {
        'hostname': 'test-switch',
        'pid': 'N9K-C9348GC-FXP',
        'serial_number': 'FOC1234ABC',
    }
    
    print(f"Input asset PID: {test_asset['pid']}")
    enriched = enrich_asset_data(test_asset, lambda msg: print(f"  LOG: {msg}"))
    
    print(f"Enriched asset keys: {list(enriched.keys())}")
    print(f"end_of_life: {enriched.get('end_of_life', 'MISSING')}")
    print(f"end_of_support: {enriched.get('end_of_support', 'MISSING')}")
    print(f"model_name: {enriched.get('model_name', 'MISSING')}")
    print(f"warranty_status: {enriched.get('warranty_status', 'MISSING')}")
    
    # Check if enrichment worked
    has_eol = bool(enriched.get('end_of_life') or enriched.get('model_name'))
    if has_eol:
        print("✓ Enrichment successful - EOL data found")
        return True
    else:
        print("✗ Enrichment failed - No EOL data found")
        return False


def test_enrichment_with_missing_pid():
    """Test enrichment when PID is missing (should use demo data)."""
    print("\n=== TEST 4: Enrichment with Missing PID ===")
    
    test_asset = {
        'hostname': 'test-switch',
        'serial_number': 'FOC1234ABC',
    }
    
    print(f"Input asset PID: {test_asset.get('pid', 'MISSING')}")
    enriched = enrich_asset_data(test_asset, lambda msg: print(f"  LOG: {msg}"))
    
    print(f"Enriched asset keys: {list(enriched.keys())}")
    print(f"end_of_life: {enriched.get('end_of_life', 'MISSING')}")
    print(f"model_name: {enriched.get('model_name', 'MISSING')}")
    print(f"warranty_status: {enriched.get('warranty_status', 'MISSING')}")
    
    # When PID is missing, should use demo data or set to unknown
    status = enriched.get('warranty_status', '')
    if status in ('demo', 'unknown'):
        print(f"✓ Enrichment handled missing PID correctly (status: {status})")
        return True
    else:
        print(f"✗ Unexpected warranty status: {status}")
        return False


def test_enrichment_with_invalid_pid():
    """Test enrichment with invalid PID (should set to unknown)."""
    print("\n=== TEST 5: Enrichment with Invalid PID ===")
    
    test_asset = {
        'hostname': 'test-switch',
        'pid': 'INVALID-NOT-IN-DB',
        'serial_number': 'FOC1234ABC',
    }
    
    print(f"Input asset PID: {test_asset['pid']}")
    enriched = enrich_asset_data(test_asset, lambda msg: print(f"  LOG: {msg}"))
    
    print(f"Enriched asset keys: {list(enriched.keys())}")
    print(f"end_of_life: {enriched.get('end_of_life', 'MISSING')}")
    print(f"model_name: {enriched.get('model_name', 'MISSING')}")
    print(f"warranty_status: {enriched.get('warranty_status', 'MISSING')}")
    
    # When PID is invalid, should set to unknown
    status = enriched.get('warranty_status', '')
    if status == 'unknown':
        print(f"✓ Enrichment handled invalid PID correctly (status: {status})")
        return True
    else:
        print(f"✗ Unexpected warranty status: {status}")
        return False


def test_enrichment_with_active_model_no_eol():
    """Test enrichment with active model in database but no EOL dates (should show active)."""
    print("\n=== TEST 6: Enrichment with Active Model (No EOL Dates) ===")
    
    test_asset = {
        'hostname': 'test-switch',
        'pid': 'N9K-C9336C-FX2',
        'serial_number': 'FOC1234ABC',
    }
    
    print(f"Input asset PID: {test_asset['pid']}")
    enriched = enrich_asset_data(test_asset, lambda msg: print(f"  LOG: {msg}"))
    
    print(f"Enriched asset keys: {list(enriched.keys())}")
    print(f"end_of_life: {enriched.get('end_of_life', 'MISSING')}")
    print(f"model_name: {enriched.get('model_name', 'MISSING')}")
    print(f"warranty_status: {enriched.get('warranty_status', 'MISSING')}")
    
    # When model is in database but has no EOL dates, should show active
    status = enriched.get('warranty_status', '')
    if status == 'active':
        print(f"✓ Enrichment handled active model correctly (status: {status})")
        return True
    else:
        print(f"✗ Unexpected warranty status: {status} (expected 'active')")
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("CISCO EOL ENRICHMENT DEBUG TESTS")
    print("=" * 60)
    
    results = []
    results.append(("Database Connection", test_database_connection()))
    results.append(("Model Lookup", test_model_lookup()))
    results.append(("Enrichment with Valid PID", test_enrichment_with_valid_pid()))
    results.append(("Enrichment with Missing PID", test_enrichment_with_missing_pid()))
    results.append(("Enrichment with Invalid PID", test_enrichment_with_invalid_pid()))
    results.append(("Enrichment with Active Model (No EOL)", test_enrichment_with_active_model_no_eol()))
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(passed for _, passed in results)
    print("=" * 60)
    if all_passed:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
    print("=" * 60)

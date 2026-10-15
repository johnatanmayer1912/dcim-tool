#!/usr/bin/env python3
"""Test database path resolution in simulated frozen environment."""

import sys
import os

# Simulate frozen environment
sys.frozen = True
sys._MEIPASS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist')

print("=" * 60)
print("TESTING DATABASE PATH RESOLUTION")
print("=" * 60)
print(f"sys.frozen: {getattr(sys, 'frozen', False)}")
print(f"sys._MEIPASS: {getattr(sys, '_MEIPASS', 'NOT SET')}")
print(f"sys.executable: {getattr(sys, 'executable', 'NOT SET')}")

# Import and test the database path function
from modules.cisco_eol_database import _get_database_path

db_path = _get_database_path()
print(f"\nDatabase path resolved: {db_path}")
print(f"Database exists: {os.path.exists(db_path)}")

if os.path.exists(db_path):
    print(f"Database size: {os.path.getsize(db_path)} bytes")
else:
    print("\n❌ DATABASE FILE NOT FOUND!")
    
    # Check alternative paths
    print("\nChecking alternative paths:")
    alt_paths = [
        os.path.join(sys._MEIPASS, 'config', 'cisco_eol_database.db'),
        os.path.join(os.path.dirname(sys.executable) if hasattr(sys, 'executable') else '.', 'config', 'cisco_eol_database.db'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'cisco_eol_database.db'),
    ]
    
    for path in alt_paths:
        print(f"  {path}: {'EXISTS' if os.path.exists(path) else 'NOT FOUND'}")

# Test database initialization
print("\n" + "=" * 60)
print("TESTING DATABASE INITIALIZATION")
print("=" * 60)

try:
    from modules.cisco_eol_database import init_database, get_all_models
    
    def log_func(msg):
        print(f"[LOG] {msg}")
    
    conn = init_database(log_func)
    models = get_all_models(log_func)
    
    print(f"\n✅ Database initialized successfully")
    print(f"✅ Retrieved {len(models)} models from database")
    
    if len(models) > 0:
        print(f"✅ First model: {models[0]['pid']} - {models[0]['model_name']}")
    else:
        print("❌ NO MODELS RETRIEVED - Database may be empty or not loading")
    
    conn.close()
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)

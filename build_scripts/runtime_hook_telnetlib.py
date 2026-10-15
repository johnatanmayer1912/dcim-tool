"""
runtime_hook_telnetlib.py
-------------------------
Runtime hook for PyInstaller to ensure telnetlib_compat is loaded before any other imports.
This must be loaded before netmiko or paramiko are imported.
"""

import sys

# Install telnetlib compatibility before any other imports
try:
    import telnetlib
except ImportError:
    # telnetlib was removed in Python 3.13+
    # Import our compatibility shim
    import telnetlib_compat
    # Install it in sys.modules so subsequent imports find it
    sys.modules['telnetlib'] = telnetlib_compat

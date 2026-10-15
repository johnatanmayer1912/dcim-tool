"""
tests/routing_analyzer/conftest.py
-----------------------------------
Shared fixtures and path setup for routing_analyzer tests.
"""
import sys
import os

# Ensure project root is on sys.path so module imports work without install
_proj_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _proj_root not in sys.path:
    sys.path.insert(0, _proj_root)

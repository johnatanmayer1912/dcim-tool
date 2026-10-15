"""
Interface Adapter

Orchestrates network interface operations.

v7.0.0 - Enterprise Architecture Refactor
"""

from typing import List, Dict, Any, Optional

from src.network.interfaces import InterfaceManager


class InterfaceAdapter:
    """Adapter for interface operations."""
    
    def __init__(self):
        self.manager = InterfaceManager()
    
    def audit_interfaces(self, devices: List[Dict], username: str, password: str) -> List[Dict]:
        """Audit interfaces across devices."""
        results = []
        for device in devices:
            result = self.manager.get_interface_status(device, username, password)
            results.append(result)
        return results

"""
Backup Adapter

Orchestrates configuration backup operations.

v7.0.0 - Enterprise Architecture Refactor
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from src.backup.manager import BackupManager


class BackupAdapter:
    """Adapter for backup operations."""
    
    def __init__(self):
        self.manager = BackupManager()
    
    def backup_configs(
        self,
        devices: List[Dict],
        username: str,
        password: str,
        enable_password: str = ""
    ) -> List[Dict]:
        """Backup configurations from devices."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results = []
        
        for device in devices:
            result = self.manager.backup(
                device=device,
                username=username,
                password=password,
                enable_password=enable_password,
                timestamp=timestamp
            )
            results.append(result)
        
        return results

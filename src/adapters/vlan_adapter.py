"""
VLAN Adapter

Orchestrates VLAN operations across multiple devices.

v7.0.0 - Enterprise Architecture Refactor
Split from adapters.py for maintainability.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from src.network.vlan.audit import VlanAuditor
from src.network.vlan.compare import VlanComparator
from src.network.vlan.management import VlanManager
from src.network.base import ConnectionManager


class VlanAdapter:
    """
    Adapter for VLAN operations.
    
    Responsibilities:
    - VLAN audit across multiple devices
    - VLAN comparison between devices
    - VLAN management (add/remove/change)
    - Report generation
    """
    
    def __init__(self, connection_manager: Optional[ConnectionManager] = None):
        self.connection_manager = connection_manager or ConnectionManager()
        self.auditor = VlanAuditor()
        self.comparator = VlanComparator()
        self.manager = VlanManager()
    
    def audit_vlans(
        self,
        devices: List[Dict[str, Any]],
        username: str,
        password: str,
        enable_password: str = "",
        log_func: Optional[callable] = None
    ) -> Tuple[List[Dict], str]:
        """
        Perform VLAN audit across multiple devices.
        
        Args:
            devices: List of device dictionaries with host, device_type
            username: SSH username
            password: SSH password
            enable_password: Enable password (optional)
            log_func: Logging function (optional)
            
        Returns:
            Tuple of (results, report_file_path)
        """
        if log_func is None:
            log_func = print
        
        log_func("Starting VLAN audit...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        results = []
        for device in devices:
            host = device.get('host', 'unknown')
            log_func(f"Auditing {host}...")
            
            try:
                vlans = self.auditor.audit_device(
                    device=device,
                    username=username,
                    password=password,
                    enable_password=enable_password
                )
                results.append({
                    'host': host,
                    'status': 'success',
                    'vlans': vlans,
                    'count': len(vlans)
                })
                log_func(f"  Found {len(vlans)} VLANs")
            except Exception as e:
                results.append({
                    'host': host,
                    'status': 'error',
                    'error': str(e)
                })
                log_func(f"  Error: {e}")
        
        # Generate report
        from utils.output_paths import CAT_VLAN_AUDIT, prepare_run_output, slugify
        paths = prepare_run_output(CAT_VLAN_AUDIT, slugify('audit'))
        report_path = paths['html_path']
        self._generate_audit_report(results, report_path)
        
        log_func(f"VLAN audit complete. Report: {report_path}")
        return results, report_path
    
    def compare_vlans(
        self,
        baseline_device: Dict[str, Any],
        compare_devices: List[Dict[str, Any]],
        username: str,
        password: str,
        enable_password: str = ""
    ) -> Dict[str, Any]:
        """
        Compare VLANs between baseline and other devices.
        
        Args:
            baseline_device: Device to use as baseline
            compare_devices: Devices to compare against baseline
            username: SSH username
            password: SSH password
            enable_password: Enable password (optional)
            
        Returns:
            Comparison results dictionary
        """
        return self.comparator.compare(
            baseline=baseline_device,
            others=compare_devices,
            username=username,
            password=password,
            enable_password=enable_password
        )
    
    def _generate_audit_report(
        self,
        results: List[Dict],
        output_path: str
    ) -> None:
        """Generate HTML audit report."""
        from src.reporting.formatters.vlan_report import VlanReportFormatter
        formatter = VlanReportFormatter()
        formatter.generate(results, output_path)

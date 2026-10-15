import unittest
from unittest.mock import MagicMock, patch
import os
import sys
import tkinter as tk
from datetime import datetime

# Import the app class - adjust path if needed or just copy robustly
# Assuming we are running in the same dir
sys.path.append(os.getcwd())
try:
    from vlan_checker_gui import VlanCheckerApp
except ImportError:
    print("Could not import VlanCheckerApp. Ensure you are in the correct directory.")
    sys.exit(1)

class TestVlanCompare(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.app = VlanCheckerApp(self.root)
        self.app.log = MagicMock()
        self.app.show_info_safe = MagicMock()
        
    def tearDown(self):
        self.root.destroy()
        # Cleanup reports
        for f in os.listdir('.'):
            if f.startswith("vlan_compare_report_") and f.endswith(".txt"):
                try:
                    os.remove(f)
                except:
                    pass

    @patch('vlan_checker_gui.ConnectHandler')
    def test_compare_logic(self, mock_ch):
        # Setup Mock Devices
        devices = [
            {'host': 'DeviceA', 'device_type': 'cisco_ios', 'group': 'Core'}, # Baseline (3 VLANs)
            {'host': 'DeviceB', 'device_type': 'cisco_ios', 'group': 'Access'}, # Missing 30
            {'host': 'DeviceC', 'device_type': 'juniper_junos', 'group': 'Access'} # Missing 20, 30; Extra 40
        ]
        
        # Setup Mock Connection and Outputs
        mock_conn = MagicMock()
        mock_ch.return_value = mock_conn
        
        def side_effect_send(cmd):
            # Return different output based on the 'host' of the current processing
            # We can't easily retrieve 'host' from just send_command call without context
            # So we rely on the order of execution or mock specifically.
            return ""

        # We need to mock _connect_permissive to return a mock that knows who it is
        # Or better, just patch logic inside _vlan_compare_thread loop? 
        # No, let's mock _connect_permissive on the app instance.
        
        def mock_connect(device, u, p):
            conn = MagicMock()
            host = device['host']
            
            if host == 'DeviceA':
                # Baseline
                # 10, 20, 30
                conn.send_command.return_value = """
10   VLAN0010                         active
20   VLAN0020                         active
30   VLAN0030                         active
"""
            elif host == 'DeviceB':
                # Missing 30
                # 10, 20
                conn.send_command.return_value = """
10   VLAN0010                         active
20   VLAN0020                         active
"""
            elif host == 'DeviceC':
                # Missing 20, 30; Extra 40
                # Juniper: Name Tag (needs trailing space for regex match)
                conn.send_command.return_value = """
VLAN0010 10 
VLAN0040 40 
"""
            return conn

        self.app._connect_permissive = mock_connect
        
        # Run comparison directly (not threaded for test)
        self.app._vlan_compare_thread(devices, "user", "pass")
        
        # Check if report was generated
        report_files = [f for f in os.listdir('.') if f.startswith("vlan_compare_report_")]
        self.assertTrue(len(report_files) > 0, "Report file should have been created")
        
        latest_report = max(report_files, key=os.path.getctime)
        with open(latest_report, 'r') as f:
            content = f.read()
            
        print(f"--- Report Content ---\n{content}\n----------------------")
        
        # verifications
        self.assertIn("Combined Network Baseline", content)
        self.assertIn("Total Unique VLANs: 4", content) # 10, 20, 30, 40
        
        # Device A (10, 20, 30) - Missing 40
        self.assertIn("Device: DeviceA", content)
        self.assertIn("[MISSING] 1 VLANs", content)
        self.assertIn("VLAN 40", content)

        # Device B (10, 20) - Missing 30, 40
        self.assertIn("Device: DeviceB", content)
        self.assertIn("[MISSING] 2 VLANs", content)
        self.assertIn("VLAN 30", content)
        self.assertIn("VLAN 40", content)
        
        # Device C (10, 40) - Missing 20, 30
        self.assertIn("Device: DeviceC", content)
        self.assertIn("[MISSING] 2 VLANs", content)
        self.assertIn("VLAN 20", content)
        self.assertIn("VLAN 30", content)

if __name__ == '__main__':
    unittest.main()

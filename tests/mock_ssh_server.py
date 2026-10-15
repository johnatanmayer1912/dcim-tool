"""Mock SSH server for testing credential fallback scenarios.

This module provides a simple mock SSH server that can simulate:
- Successful authentication with correct credentials
- Failed authentication with wrong credentials
- Multiple credential attempts (primary, secondary, tertiary)
"""
from __future__ import annotations

import socket
import threading
import time
from typing import Dict, Optional, Callable
from unittest.mock import MagicMock, patch


class MockSSHServer:
    """Mock SSH server for testing credential fallback."""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 2222):
        self.host = host
        self.port = port
        self.valid_credentials: Dict[str, str] = {}
        self.connection_attempts: list = []
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
    def add_valid_credential(self, username: str, password: str):
        """Add a valid username/password pair."""
        self.valid_credentials[username] = password
        
    def clear_credentials(self):
        """Clear all valid credentials."""
        self.valid_credentials.clear()
        
    def get_connection_attempts(self) -> list:
        """Get list of connection attempts."""
        return self.connection_attempts.copy()
        
    def clear_attempts(self):
        """Clear connection attempt history."""
        self.connection_attempts.clear()
        
    def start(self):
        """Start the mock SSH server in a background thread."""
        self.running = True
        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()
        time.sleep(0.5)  # Give server time to start
        
    def stop(self):
        """Stop the mock SSH server."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
            
    def _run_server(self):
        """Run the mock server (simplified for testing)."""
        # This is a simplified mock - in real testing we'd use paramiko server
        # For now, we'll just simulate the behavior through mocking
        pass
        
    def validate_credentials(self, username: str, password: str) -> bool:
        """Validate credentials against the valid credentials list."""
        self.connection_attempts.append({
            'username': username,
            'password': password,
            'timestamp': time.time()
        })
        return self.valid_credentials.get(username) == password


def mock_connect_permissive_with_fallback(
    mock_server: MockSSHServer,
    log_func: Optional[Callable[[str], None]] = None
):
    """
    Mock function that simulates connect_permissive with credential fallback.
    
    This function will:
    1. Check credentials against the mock server
    2. Log each attempt
    3. Raise exception on failure
    4. Return mock connection on success
    """
    def _mock_connect(target_dict, user, pwd, enb_pwd, log_func=None):
        host = target_dict.get('host', 'unknown')
        
        if log_func:
            log_func(f"[{host}] Attempting connection with user: {user}")
        
        if mock_server.validate_credentials(user, pwd):
            if log_func:
                log_func(f"[{host}] Authentication successful for user: {user}")
            # Return mock connection
            mock_conn = MagicMock()
            mock_conn.find_prompt.return_value = f'{host}#'
            mock_conn.send_command.side_effect = lambda cmd: 'Cisco Nexus' if 'version' in cmd.lower() else 'NAME: "Chassis"'
            return mock_conn
        else:
            if log_func:
                log_func(f"[{host}] Authentication failed for user: {user}")
            raise Exception(f'Authentication failed for user {user}')
    
    return _mock_connect


def test_credential_fallback_scenarios():
    """Test all three credential fallback scenarios."""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from modules.network_base import safe_connection
    
    # Create mock server
    server = MockSSHServer()
    
    # Scenario 1: Primary succeeds (1 correct pass)
    print("\n=== Scenario 1: Primary succeeds ===")
    server.clear_credentials()
    server.clear_attempts()
    server.add_valid_credential('primary_user', 'primary_pass')
    
    device = {'host': '1.1.1.1', 'device_type': 'cisco_nxos'}
    credentials = {
        'username': 'primary_user',
        'password': 'primary_pass',
        'secret': None,
        'fallback_credentials': []
    }
    
    log_messages = []
    def log_func(msg):
        log_messages.append(msg)
        print(f"LOG: {msg}")
    
    with patch('modules.network_base.connect_permissive', 
               side_effect=mock_connect_permissive_with_fallback(server, log_func)):
        try:
            with safe_connection(device, credentials['username'], credentials['password'], 
                               credentials.get('secret'), log_func=log_func) as conn:
                print("✓ Scenario 1 PASSED: Primary credential succeeded")
                print(f"  Attempts: {len(server.get_connection_attempts())}")
                print(f"  Logs: {len([m for m in log_messages if 'Authentication' in m])} auth logs")
        except Exception as e:
            print(f"✗ Scenario 1 FAILED: {e}")
    
    # Scenario 2: Primary fails, secondary succeeds
    print("\n=== Scenario 2: Primary fails, secondary succeeds ===")
    server.clear_credentials()
    server.clear_attempts()
    server.add_valid_credential('secondary_user', 'secondary_pass')
    
    credentials = {
        'username': 'primary_user',
        'password': 'wrong_pass',
        'secret': None,
        'fallback_credentials': [
            {'username': 'secondary_user', 'password': 'secondary_pass', 
             'enable_pwd': None, 'label': 'Secondary'}
        ]
    }
    
    log_messages = []
    def log_func2(msg):
        log_messages.append(msg)
        print(f"LOG: {msg}")
    
    with patch('modules.network_base.connect_permissive',
               side_effect=mock_connect_permissive_with_fallback(server, log_func2)):
        try:
            with safe_connection(device, credentials['username'], credentials['password'],
                               credentials.get('secret'), log_func=log_func2,
                               fallback_credentials=credentials['fallback_credentials']) as conn:
                print("✓ Scenario 2 PASSED: Secondary credential succeeded after primary failed")
                print(f"  Attempts: {len(server.get_connection_attempts())}")
                print(f"  Logs: {len([m for m in log_messages if 'Authentication' in m])} auth logs")
                print(f"  Fallback attempts logged: {len([m for m in log_messages if 'Secondary' in m])}")
        except Exception as e:
            print(f"✗ Scenario 2 FAILED: {e}")
    
    # Scenario 3: Primary fails, secondary fails, third succeeds
    print("\n=== Scenario 3: Primary fails, secondary fails, third succeeds ===")
    server.clear_credentials()
    server.clear_attempts()
    server.add_valid_credential('third_user', 'third_pass')
    
    credentials = {
        'username': 'primary_user',
        'password': 'wrong_pass',
        'secret': None,
        'fallback_credentials': [
            {'username': 'secondary_user', 'password': 'wrong_pass',
             'enable_pwd': None, 'label': 'Secondary'},
            {'username': 'third_user', 'password': 'third_pass',
             'enable_pwd': None, 'label': 'Third'}
        ]
    }
    
    log_messages = []
    def log_func3(msg):
        log_messages.append(msg)
        print(f"LOG: {msg}")
    
    with patch('modules.network_base.connect_permissive',
               side_effect=mock_connect_permissive_with_fallback(server, log_func3)):
        try:
            with safe_connection(device, credentials['username'], credentials['password'],
                               credentials.get('secret'), log_func=log_func3,
                               fallback_credentials=credentials['fallback_credentials']) as conn:
                print("✓ Scenario 3 PASSED: Third credential succeeded after primary and secondary failed")
                print(f"  Attempts: {len(server.get_connection_attempts())}")
                print(f"  Logs: {len([m for m in log_messages if 'Authentication' in m])} auth logs")
                print(f"  Secondary attempts logged: {len([m for m in log_messages if 'Secondary' in m])}")
                print(f"  Third attempts logged: {len([m for m in log_messages if 'Third' in m])}")
        except Exception as e:
            print(f"✗ Scenario 3 FAILED: {e}")


if __name__ == '__main__':
    test_credential_fallback_scenarios()

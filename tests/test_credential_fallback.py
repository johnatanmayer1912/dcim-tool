"""Test credential fallback logic with 0 trust policy.

Tests simulate real-life scenarios:
1. Primary credential fails, secondary succeeds
2. Primary and secondary fail, third succeeds
3. All credentials fail
4. No fallback credentials configured
5. Duplicate credentials (deduplication)
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch, call
from typing import Dict, Any


class TestCredentialFallback:
    """Test primary -> secondary -> tertiary credential fallback."""

    def test_primary_succeeds_no_fallback_needed(self):
        """When primary credentials work, no fallback should be attempted."""
        from modules.network_base import safe_connection
        from netmiko import ConnectHandler
        
        device = {'host': '1.1.1.1', 'device_type': 'cisco_nxos'}
        primary_user = 'correct_user'
        primary_pass = 'correct_pass'
        
        mock_conn = MagicMock()
        mock_conn.find_prompt.return_value = 'switch#'
        
        with patch('modules.network_base.ConnectHandler', return_value=mock_conn) as mock_connect:
            with patch('modules.network_base.resolve_hostname_from_prompt', return_value='switch'):
                log_messages = []
                def log_func(msg):
                    log_messages.append(msg)
                
                with safe_connection(device, primary_user, primary_pass, None, log_func=log_func) as conn:
                    assert conn == mock_conn
                
                # Should only attempt primary connection
                assert mock_connect.call_count == 1
                # Should log successful connection
                assert any('Successfully connected' in msg for msg in log_messages)

    def test_primary_fails_secondary_succeeds(self):
        """When primary fails, secondary should be attempted and succeed."""
        from modules.network_base import safe_connection
        
        device = {'host': '1.1.1.1', 'device_type': 'cisco_nxos'}
        primary_user = 'wrong_user'
        primary_pass = 'wrong_pass'
        secondary_user = 'correct_user'
        secondary_pass = 'correct_pass'
        
        mock_conn = MagicMock()
        mock_conn.find_prompt.return_value = 'switch#'
        
        call_count = [0]
        def mock_connect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call (primary) - fail
                raise Exception('Authentication failed')
            else:
                # Second call (secondary) - succeed
                return mock_conn
        
        fallback_creds = [
            {'username': secondary_user, 'password': secondary_pass, 'enable_pwd': None, 'label': 'Secondary'}
        ]
        
        with patch('modules.network_base.ConnectHandler', side_effect=mock_connect) as mock_connect:
            with patch('modules.network_base.resolve_hostname_from_prompt', return_value='switch'):
                log_messages = []
                def log_func(msg):
                    log_messages.append(msg)
                
                with safe_connection(device, primary_user, primary_pass, None, log_func=log_func, fallback_credentials=fallback_creds) as conn:
                    assert conn == mock_conn
                
                # Should attempt both primary and secondary
                assert mock_connect.call_count == 2
                # Should log both attempts
                assert any('Primary' in msg for msg in log_messages)
                assert any('Secondary' in msg for msg in log_messages)
                assert any('Successfully connected' in msg for msg in log_messages)

    def test_all_credentials_fail(self):
        """When all credentials fail, exception should be raised."""
        from modules.network_base import safe_connection
        
        device = {'host': '1.1.1.1', 'device_type': 'cisco_nxos'}
        
        fallback_creds = [
            {'username': 'secondary_user', 'password': 'wrong_pass', 'enable_pwd': None, 'label': 'Secondary'},
            {'username': 'third_user', 'password': 'wrong_pass', 'enable_pwd': None, 'label': 'Third'}
        ]
        
        with patch('modules.network_base.ConnectHandler', side_effect=Exception('Authentication failed')):
            log_messages = []
            def log_func(msg):
                log_messages.append(msg)
            
            with pytest.raises(Exception, match='Authentication failed'):
                with safe_connection(device, 'wrong_user', 'wrong_pass', None, log_func=log_func, fallback_credentials=fallback_creds) as conn:
                    pass
            
            # Should log all three attempts
            assert any('Primary' in msg for msg in log_messages)
            assert any('Secondary' in msg for msg in log_messages)
            assert any('Third' in msg for msg in log_messages)
            assert any('connection failed' in msg for msg in log_messages)

    def test_duplicate_credentials_deduplicated(self):
        """When secondary is identical to primary, it should be deduplicated."""
        from modules.network_base import safe_connection
        
        device = {'host': '1.1.1.1', 'device_type': 'cisco_nxos'}
        user = 'user'
        password = 'pass'
        
        # Secondary is identical to primary
        fallback_creds = [
            {'username': user, 'password': password, 'enable_pwd': None, 'label': 'Secondary'}
        ]
        
        mock_conn = MagicMock()
        mock_conn.find_prompt.return_value = 'switch#'
        
        with patch('modules.network_base.ConnectHandler', return_value=mock_conn) as mock_connect:
            with patch('modules.network_base.resolve_hostname_from_prompt', return_value='switch'):
                log_messages = []
                def log_func(msg):
                    log_messages.append(msg)
                
                with safe_connection(device, user, password, None, log_func=log_func, fallback_credentials=fallback_creds) as conn:
                    assert conn == mock_conn
                
                # Should only attempt once (deduplicated)
                assert mock_connect.call_count == 1

    def test_no_fallback_credentials(self):
        """When no fallback credentials, only primary should be attempted."""
        from modules.network_base import safe_connection
        
        device = {'host': '1.1.1.1', 'device_type': 'cisco_nxos'}
        
        with patch('modules.network_base.ConnectHandler', side_effect=Exception('Authentication failed')):
            log_messages = []
            def log_func(msg):
                log_messages.append(msg)
            
            with pytest.raises(Exception, match='Authentication failed'):
                with safe_connection(device, 'user', 'pass', None, log_func=log_func, fallback_credentials=None) as conn:
                    pass
            
            # Should only log primary attempt
            assert any('Connecting to device' in msg for msg in log_messages)
            # Should not log any fallback attempts
            assert not any('Secondary' in msg for msg in log_messages)
            assert not any('Third' in msg for msg in log_messages)

    def test_logging_shows_attempt_numbers(self):
        """Log messages should show attempt numbers when multiple credentials are used."""
        from modules.network_base import safe_connection
        
        device = {'host': '1.1.1.1', 'device_type': 'cisco_nxos'}
        
        fallback_creds = [
            {'username': 'secondary', 'password': 'wrong', 'enable_pwd': None, 'label': 'Secondary'},
            {'username': 'third', 'password': 'wrong', 'enable_pwd': None, 'label': 'Third'}
        ]
        
        with patch('modules.network_base.ConnectHandler', side_effect=Exception('Authentication failed')):
            log_messages = []
            def log_func(msg):
                log_messages.append(msg)
            
            with pytest.raises(Exception):
                with safe_connection(device, 'primary', 'wrong', None, log_func=log_func, fallback_credentials=fallback_creds):
                    pass
            
            # Should show attempt numbers
            assert any('attempt 1/3' in msg for msg in log_messages)
            assert any('attempt 2/3' in msg for msg in log_messages)
            assert any('attempt 3/3' in msg for msg in log_messages)


class TestAssetCollectionWithCredentialFallback:
    """Test asset collection with credential fallback."""

    def test_collection_uses_fallback_credentials(self):
        """Asset collection should pass fallback credentials to safe_connection."""
        from modules.asset_collection_policy import collect_device_assets
        
        device = {'host': '1.1.1.1', 'device_type': 'cisco_nxos'}
        credentials = {
            'username': 'primary',
            'password': 'wrong',
            'fallback_credentials': [
                {'username': 'secondary', 'password': 'correct', 'enable_pwd': None, 'label': 'Secondary'}
            ]
        }
        params = {'include_modules': True, 'collection_policy': 'ssh_first'}
        
        mock_conn = MagicMock()
        mock_conn.find_prompt.return_value = 'switch'
        mock_conn.send_command.side_effect = lambda cmd: 'Cisco Nexus' if 'version' in cmd.lower() else 'NAME: "Chassis"'
        
        call_count = [0]
        def mock_safe_connection(*args, **kwargs):
            call_count[0] += 1
            # Check that fallback_credentials are passed
            assert 'fallback_credentials' in kwargs
            assert kwargs['fallback_credentials'] == credentials['fallback_credentials']
            return mock_conn
        
        with patch('modules.asset_collection_policy.safe_connection', side_effect=mock_safe_connection):
            with patch('modules.asset_collection_policy.is_mock_host', return_value=False):
                log_messages = []
                def log_func(msg):
                    log_messages.append(msg)
                
                result = collect_device_assets(device, credentials, params, log_func)
                
                # Should have attempted connection
                assert call_count[0] > 0
                # Should have logged attempts
                assert len(log_messages) > 0

    def test_connection_failure_no_demo_report(self):
        """When all credentials fail, no demo report should be created."""
        from modules.asset_collection_policy import collect_device_assets
        
        device = {'host': '1.1.1.1', 'device_type': 'cisco_nxos'}
        credentials = {
            'username': 'wrong',
            'password': 'wrong',
            'fallback_credentials': [
                {'username': 'secondary', 'password': 'wrong', 'enable_pwd': None, 'label': 'Secondary'}
            ]
        }
        params = {'include_modules': True, 'collection_policy': 'ssh_only'}
        
        with patch('modules.asset_collection_policy.safe_connection', side_effect=Exception('Authentication failed')):
            with patch('modules.asset_collection_policy.is_mock_host', return_value=False):
                log_messages = []
                def log_func(msg):
                    log_messages.append(msg)
                
                result = collect_device_assets(device, credentials, params, log_func)
                
                # Should return error without demo enrichment
                assert result['collection_summary'] == 'ssh_failed'
                assets = result.get('assets', [])
                assert len(assets) == 1
                assert assets[0]['severity'] == 'critical'
                assert 'error' in assets[0]
                # Should NOT have demo EOL data
                assert not assets[0].get('end_of_life') or assets[0].get('end_of_life') == ''
                # Should log that all attempts exhausted
                assert any('All credential attempts exhausted' in msg for msg in log_messages)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

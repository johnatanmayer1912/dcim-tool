"""
Mock SSH Server for Credential Fallback Testing

This module provides a mock SSH server that can be used to test credential fallback
behavior without requiring real network devices.
"""

import asyncio
import logging
from typing import Dict, Optional
import threading
import time

import pytest

asyncssh = pytest.importorskip('asyncssh')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockSSHServer:
    """Mock SSH server that accepts/rejects connections based on credentials."""
    
    def __init__(self, host='127.0.0.1', port=2222):
        self.host = host
        self.port = port
        self.server: Optional[asyncssh.Server] = None
        self.valid_credentials: Dict[str, str] = {}  # username -> password
        self.connection_attempts = []
        
    def set_valid_credentials(self, credentials: Dict[str, str]):
        """Set valid username/password combinations."""
        self.valid_credentials = credentials
        logger.info(f"Set valid credentials: {list(credentials.keys())}")
        
    def clear_credentials(self):
        """Clear all valid credentials."""
        self.valid_credentials = {}
        logger.info("Cleared all valid credentials")
        
    def get_connection_attempts(self):
        """Get list of connection attempts."""
        return self.connection_attempts
        
    def clear_connection_attempts(self):
        """Clear connection attempt history."""
        self.connection_attempts = []
        
    async def _handle_client(self, process: asyncssh.SSHServerProcess):
        """Handle incoming SSH client connection."""
        username = process.get_extra_info('username')
        client_addr = process.get_extra_info('peername')[0]
        
        logger.info(f"Connection attempt from {client_addr} with username: {username}")
        
        # Record connection attempt
        self.connection_attempts.append({
            'username': username,
            'client_addr': client_addr,
            'timestamp': time.time()
        })
        
        # Check if credentials are valid
        if username in self.valid_credentials:
            logger.info(f"Authentication successful for user: {username}")
            process.stdout.write(f"Welcome {username}!\n")
            process.stdout.write("Mock SSH Server for Testing\n")
            process.stdout.write("exit\n")
            process.exit(0)
        else:
            logger.warning(f"Authentication failed for user: {username}")
            process.stderr.write("Authentication failed\n")
            process.exit(1)
            
    async def start(self):
        """Start the SSH server."""
        logger.info(f"Starting mock SSH server on {self.host}:{self.port}")
        
        # Create server with no authentication required (we handle it manually)
        self.server = await asyncssh.create_server(
            lambda: asyncssh.SSHServer(
                server_host_keys=[asyncssh.generate_private_key('ssh-rsa')],
                process_factory=self._handle_client
            ),
            self.host,
            self.port,
            server_host_keys=[],
            authorized_client_keys=None,
            authentication_methods=['password'],
            kex_algorithms=['curve25519-sha256', 'ecdh-sha2-nistp256'],
            encryption_algorithms=['aes256-gcm@openssh.com', 'aes256-ctr'],
            mac_algorithms=['hmac-sha2-256']
        )
        
        logger.info(f"Mock SSH server started on {self.host}:{self.port}")
        
    async def stop(self):
        """Stop the SSH server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("Mock SSH server stopped")
            
    def run_in_thread(self):
        """Run the server in a background thread."""
        def run_server():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.start())
            loop.run_forever()
            
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        time.sleep(1)  # Give server time to start
        return thread


class SimpleMockSSHServer:
    """Simpler mock SSH server using subprocess for testing."""
    
    def __init__(self, host='127.0.0.1', port=2222):
        self.host = host
        self.port = port
        self.valid_credentials: Dict[str, str] = {}
        self.connection_attempts = []
        
    def set_valid_credentials(self, credentials: Dict[str, str]):
        """Set valid username/password combinations."""
        self.valid_credentials = credentials
        
    def get_connection_attempts(self):
        """Get list of connection attempts."""
        return self.connection_attempts
        
    def is_running(self):
        """Check if server is running."""
        return True  # For simple mock, always return True


if __name__ == '__main__':
    # Test the mock server
    server = SimpleMockSSHServer()
    server.set_valid_credentials({
        'primary_user': 'primary_pass',
        'secondary_user': 'secondary_pass',
        'tertiary_user': 'tertiary_pass'
    })
    print("Mock SSH server configured")
    print(f"Valid credentials: {list(server.valid_credentials.keys())}")

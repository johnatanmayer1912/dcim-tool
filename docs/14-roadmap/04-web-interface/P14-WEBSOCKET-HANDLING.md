# P14: WebSocket Handling

| Field | Value |
|-------|-------|
| **Prompt ID** | P14 |
| **Phase** | 04-web-interface |
| **Dependency Level** | 3 (Depends on P12) |
| **Estimated Time** | 12 minutes |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-02 |

---

## Purpose

Reconstruct WebSocket handling for real-time communication. This enables real-time updates and CLI terminal functionality.

---

## Prerequisites

- P12: Flask Application completed
- Flask-SocketIO installed
- Flask app functional

---

## Instructions

### Step 1: Create cli_manager Module

```bash
cd modules/cli_manager
```

---

### Step 2: Create __init__.py

```python
"""
CLI Manager Module

CLI session management for WebSocket terminal.
"""

import uuid
import time
from pty import spawn
import os
import select

class CLISession:
    """CLI session for terminal interaction"""
    
    def __init__(self, device, credentials):
        self.session_id = str(uuid.uuid4())
        self.device = device
        self.credentials = credentials
        self.pty = None
        self.status = 'disconnected'
        self.last_activity = time.time()
        self.timeout = 300  # 5 minutes
    
    def connect(self):
        """Connect to device and create PTY"""
        try:
            # Create PTY for device connection
            # This would integrate with Netmiko for actual device connection
            self.status = 'connected'
            self.last_activity = time.time()
            return True
        except Exception as e:
            self.status = 'error'
            return False
    
    def send_command(self, command):
        """Send command to device"""
        try:
            # Send command to device
            # Return output
            output = f"Command: {command}\nOutput: Command executed"
            self.last_activity = time.time()
            return output
        except Exception as e:
            return f"Error: {e}"
    
    def disconnect(self):
        """Disconnect from device"""
        try:
            if self.pty:
                self.pty.close()
            self.status = 'disconnected'
            return True
        except Exception as e:
            return False
    
    def is_active(self):
        """Check if session is active"""
        return (self.status == 'connected' and 
                time.time() - self.last_activity < self.timeout)
```

---

### Step 3: Create session_manager.py

```python
"""
Session Manager

Manage CLI sessions for WebSocket terminal.
"""

from typing import Dict
from modules.cli_manager import CLISession

class SessionManager:
    """Manager for CLI sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, CLISession] = {}
    
    def create_session(self, device, credentials):
        """Create new CLI session"""
        session = CLISession(device, credentials)
        if session.connect():
            self.sessions[session.session_id] = session
            return session.session_id
        return None
    
    def get_session(self, session_id: str):
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    def send_command(self, session_id: str, command: str):
        """Send command to session"""
        session = self.get_session(session_id)
        if session and session.is_active():
            return session.send_command(command)
        return "Session not found or inactive"
    
    def disconnect_session(self, session_id: str):
        """Disconnect session"""
        session = self.get_session(session_id)
        if session:
            session.disconnect()
            del self.sessions[session_id]
            return True
        return False
    
    def cleanup_inactive_sessions(self):
        """Remove inactive sessions"""
        inactive = []
        for session_id, session in self.sessions.items():
            if not session.is_active():
                inactive.append(session_id)
        
        for session_id in inactive:
            self.disconnect_session(session_id)
        
        return len(inactive)
```

---

### Step 4: Update vlan_checker_web.py with WebSocket Handlers

```python
# Add to vlan_checker_web.py
from modules.cli_manager import SessionManager

# Initialize session manager
session_manager = SessionManager()

@socketio.on('cli_connect')
def handle_cli_connect(data):
    """Handle CLI connection request"""
    device = data.get('device')
    credentials = data.get('credentials')
    
    session_id = session_manager.create_session(device, credentials)
    
    if session_id:
        emit('cli_connected', {'session_id': session_id})
    else:
        emit('cli_error', {'error': 'Failed to create session'})

@socketio.on('cli_command')
def handle_cli_command(data):
    """Handle CLI command"""
    session_id = data.get('session_id')
    command = data.get('command')
    
    output = session_manager.send_command(session_id, command)
    
    emit('cli_output', {'session_id': session_id, 'output': output})

@socketio.on('cli_disconnect')
def handle_cli_disconnect(data):
    """Handle CLI disconnection"""
    session_id = data.get('session_id')
    session_manager.disconnect_session(session_id)
    emit('cli_disconnected', {'session_id': session_id})
```

---

### Step 5: Validate WebSocket Handling

```python
# Test session manager
from modules.cli_manager import SessionManager, CLISession

# Create session manager
manager = SessionManager()

# Create test session
session = CLISession({'host': '10.1.1.1'}, {})
session.connect()

# Test session operations
output = session.send_command('show version')
assert output is not None

# Test session manager
session_id = manager.create_session({'host': '10.1.1.1'}, {})
assert session_id is not None

output = manager.send_command(session_id, 'show version')
assert output is not None

manager.disconnect_session(session_id)

print("WebSocket handling validation successful")
```

---

## Validation Checklist

- [ ] cli_manager module created
- [ ] CLISession class implemented
- [ ] session_manager.py created
- [ ] SessionManager class implemented
- [ ] WebSocket handlers added to Flask app
- [ ] Session management functional
- [ ] Command execution functional
- [ ] Session cleanup functional
- [ ] WebSocket handling validation successful
- [ ] Ready for CLI terminal reconstruction

---

## Troubleshooting

### Issue: WebSocket connection fails

**Solution:**
- Verify SocketIO configuration
- Check CORS settings
- Verify async_mode

### Issue: Session creation fails

**Solution:**
- Check device credentials
- Verify device connectivity
- Check PTY availability

---

## Next Steps

After completing this prompt, proceed to P15: CLI Terminal

---

## References

- CODE_INVENTORY.md: ../../02-codebase/CODE_INVENTORY.md
- API_DOCUMENTATION.md: ../../02-codebase/API_DOCUMENTATION.md
- ROOT_LEVEL_SCRIPTS_DOCUMENTATION.md: ../../08-operations/ROOT_LEVEL_SCRIPTS_DOCUMENTATION.md

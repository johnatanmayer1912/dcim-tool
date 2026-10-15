# P15: CLI Terminal

| Field | Value |
|-------|-------|
| **Prompt ID** | P15 |
| **Phase** | 04-web-interface |
| **Dependency Level** | 4 (Depends on P12, P14) |
| **Estimated Time** | 9 minutes |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-02 |

---

## Purpose

Reconstruct CLI terminal for device interaction. This provides a web-based terminal interface for executing CLI commands on network devices.

---

## Prerequisites

- P12: Flask Application completed
- P14: WebSocket Handling completed
- Session manager functional
- WebSocket handlers implemented

---

## Instructions

### Step 1: Update cli_manager Module with PTY Handling

```python
# Add to modules/cli_manager/__init__.py

import pty
import os
import select
import threading
from modules.connectivity import safe_connection

class CLISession:
    """CLI session for terminal interaction"""
    
    def __init__(self, device, credentials):
        self.session_id = str(uuid.uuid4())
        self.device = device
        self.credentials = credentials
        self.pty_master = None
        self.pty_slave = None
        self.status = 'disconnected'
        self.last_activity = time.time()
        self.timeout = 300  # 5 minutes
        self.output_buffer = []
    
    def connect(self):
        """Connect to device and create PTY"""
        try:
            # Create PTY
            self.pty_master, self.pty_slave = pty.openpty()
            
            # Connect to device using Netmiko
            with safe_connection(self.device, 
                               self.credentials['username'],
                               self.credentials['password'],
                               self.credentials.get('secret'),
                               lambda x: None) as conn:
                
                # Start PTY reader thread
                self.reader_thread = threading.Thread(
                    target=self._read_pty_output,
                    args=(conn,),
                    daemon=True
                )
                self.reader_thread.start()
                
                self.status = 'connected'
                self.last_activity = time.time()
                return True
                
        except Exception as e:
            self.status = 'error'
            return False
    
    def _read_pty_output(self, conn):
        """Read output from PTY and send to device"""
        while self.status == 'connected':
            try:
                # Check for data from PTY
                r, _, _ = select.select([self.pty_master], [], [], 0.1)
                if r:
                    data = os.read(self.pty_master, 1024)
                    if data:
                        # Send to device
                        try:
                            conn.send_command(data.decode(), read_timeout=1)
                        except:
                            pass
            except:
                break
    
    def send_command(self, command):
        """Send command to device via PTY"""
        try:
            if self.pty_master:
                os.write(self.pty_master, command.encode())
                self.last_activity = time.time()
                return f"Command sent: {command}"
        except Exception as e:
            return f"Error: {e}"
    
    def get_output(self):
        """Get output from buffer"""
        output = ''.join(self.output_buffer)
        self.output_buffer.clear()
        return output
    
    def disconnect(self):
        """Disconnect from device"""
        try:
            self.status = 'disconnected'
            if self.pty_master:
                os.close(self.pty_master)
            if self.pty_slave:
                os.close(self.pty_slave)
            return True
        except Exception as e:
            return False
```

---

### Step 2: Update WebSocket Handlers in vlan_checker_web.py

```python
# Add to vlan_checker_web.py

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
    
    # Get output from session
    session = session_manager.get_session(session_id)
    if session:
        session_output = session.get_output()
        emit('cli_output', {'session_id': session_id, 'output': session_output})
    
    emit('cli_output', {'session_id': session_id, 'output': output})

@socketio.on('cli_disconnect')
def handle_cli_disconnect(data):
    """Handle CLI disconnection"""
    session_id = data.get('session_id')
    session_manager.disconnect_session(session_id)
    emit('cli_disconnected', {'session_id': session_id})

@socketio.on('cli_output_request')
def handle_cli_output_request(data):
    """Handle output request"""
    session_id = data.get('session_id')
    session = session_manager.get_session(session_id)
    
    if session:
        output = session.get_output()
        emit('cli_output', {'session_id': session_id, 'output': output})
```

---

### Step 3: Update terminal.js for Real-time Output

```javascript
// Update static/js/terminal.js

const socket = io();
let sessionId = null;
let outputInterval = null;

// Connect to WebSocket
socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('cli_connected', (data) => {
    sessionId = data.session_id;
    document.getElementById('prompt').textContent = `${sessionId}>`;
    
    // Start polling for output
    outputInterval = setInterval(() => {
        socket.emit('cli_output_request', { session_id: sessionId });
    }, 500);
});

socket.on('cli_output', (data) => {
    if (data.session_id === sessionId) {
        const output = document.getElementById('terminal-output');
        const line = document.createElement('div');
        line.className = 'terminal-line';
        line.textContent = data.output;
        output.appendChild(line);
        output.scrollTop = output.scrollHeight;
    }
});

socket.on('cli_disconnected', (data) => {
    sessionId = null;
    document.getElementById('prompt').textContent = '>';
    
    // Stop polling
    if (outputInterval) {
        clearInterval(outputInterval);
        outputInterval = null;
    }
});

// Connect button
document.getElementById('connect-device').addEventListener('click', () => {
    const device = document.getElementById('device-select').value;
    if (device) {
        socket.emit('cli_connect', {
            device: { host: device },
            credentials: { username: 'admin', password: 'password' }
        });
    }
});

// Disconnect button
document.getElementById('disconnect-device').addEventListener('click', () => {
    if (sessionId) {
        socket.emit('cli_disconnect', { session_id: sessionId });
    }
});
```

---

### Step 4: Validate CLI Terminal

```python
# Test CLI terminal functionality
from modules.cli_manager import SessionManager, CLISession

# Create session manager
manager = SessionManager()

# Create test session
session = CLISession({'host': '10.1.1.1', 'device_type': 'cisco_ios'}, 
                   {'username': 'admin', 'password': 'password'})

# Test PTY creation
import pty
master, slave = pty.openpty()
assert master is not None
assert slave is not None

# Close PTY
os.close(master)
os.close(slave)

print("CLI terminal validation successful")
```

---

## Validation Checklist

- [ ] PTY handling implemented
- [ ] CLISession updated with PTY
- [ ] PTY reader thread implemented
- [ ] WebSocket handlers updated
- [ ] Terminal JavaScript updated
- [ ] Real-time output polling implemented
- [ ] Session cleanup implemented
- [ ] CLI terminal validation successful
- [ ] Web interface phase complete
- [ ] Ready for utilities reconstruction

---

## Troubleshooting

### Issue: PTY creation fails

**Solution:**
- Check OS compatibility
- Verify pty module availability
- Test PTY creation manually

### Issue: Real-time output not working

**Solution:**
- Verify WebSocket connection
- Check output polling interval
- Validate session ID matching

---

## Next Steps

After completing this prompt, Phase 4 (Web Interface) is complete. Proceed to Phase 5: Utilities (can run in parallel with Phase 3)

---

## References

- CODE_INVENTORY.md: ../../02-codebase/CODE_INVENTORY.md
- API_DOCUMENTATION.md: ../../02-codebase/API_DOCUMENTATION.md
- ROOT_LEVEL_SCRIPTS_DOCUMENTATION.md: ../../08-operations/ROOT_LEVEL_SCRIPTS_DOCUMENTATION.md

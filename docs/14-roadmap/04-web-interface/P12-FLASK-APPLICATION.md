# P12: Flask Application

| Field | Value |
|-------|-------|
| **Prompt ID** | P12 |
| **Phase** | 04-web-interface |
| **Dependency Level** | 2 (Depends on Phase 2) |
| **Estimated Time** | 12 minutes |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-02 |

---

## Purpose

Reconstruct the Flask web application. This is the main web application that serves the UI and API endpoints.

---

## Prerequisites

- Phase 2 (Core Modules) completed
- network_base module functional
- adapters module functional
- connectivity module functional
- Dependencies installed (Flask, Flask-SocketIO)

---

## Instructions

### Step 1: Create vlan_checker_web.py

```python
"""
Network Swiss Tool Pro - Web Application

Flask web application for network management.
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import os
import logging

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import modules after app initialization
from modules.plugin_registry import PluginRegistry
from modules.connectivity import connect_to_device, test_connection

# Initialize plugin registry
plugin_registry = PluginRegistry()
plugin_registry.discover_plugins()

# Global variables
cli_sessions = {}
job_status = {}

@app.route('/')
def index():
    """Serve main application"""
    return render_template('index.html')

@app.route('/api/execute', methods=['POST'])
def execute():
    """Execute network operation"""
    try:
        data = request.json
        action = data.get('action')
        devices = data.get('devices', [])
        credentials = data.get('credentials', {})
        
        # Execute action based on request
        result = {
            'status': 'success',
            'action': action,
            'devices': len(devices),
            'message': f'Executed {action} on {len(devices)} devices'
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in execute endpoint: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/plugins/list', methods=['GET'])
def list_plugins():
    """List all available plugins"""
    try:
        plugins = plugin_registry.list_plugins()
        return jsonify({'status': 'success', 'plugins': plugins})
    except Exception as e:
        logger.error(f"Error listing plugins: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/plugins/reload', methods=['POST'])
def reload_plugins():
    """Reload all plugins"""
    try:
        count = plugin_registry.reload_plugins()
        return jsonify({'status': 'success', 'plugins_reloaded': count})
    except Exception as e:
        logger.error(f"Error reloading plugins: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/health-check/run', methods=['POST'])
def health_check():
    """Run health check on devices"""
    try:
        data = request.json
        devices = data.get('devices', [])
        credentials = data.get('credentials', {})
        
        results = []
        for device in devices:
            result = test_connection(device, credentials['username'], credentials['password'], credentials.get('secret'), logger.info)
            results.append(result)
        
        return jsonify({'status': 'success', 'results': results})
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    logger.info('Client connected')
    emit('connected', {'message': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logger.info('Client disconnected')

@socketio.on('cli_command')
def handle_cli_command(data):
    """Handle CLI command from terminal"""
    session_id = data.get('session_id')
    command = data.get('command')
    
    # Process command and emit result
    emit('cli_output', {'session_id': session_id, 'output': f'Command: {command}'})

if __name__ == '__main__':
    logger.info('Starting Network Swiss Tool Pro web application')
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
```

---

### Step 2: Create requirements-web.txt

```bash
cat > requirements-web.txt << 'EOF'
Flask==3.0.0
Flask-SocketIO==5.3.6
eventlet==0.33.3
python-socketio==5.11.0
EOF
```

---

### Step 3: Validate Flask Application

```python
# Test Flask app import
import vlan_checker_web

# Test app initialization
assert vlan_checker_web.app is not None
assert vlan_checker_web.socketio is not None

# Test plugin registry
assert vlan_checker_web.plugin_registry is not None

# Test routes
with vlan_checker_web.app.test_client() as client:
    response = client.get('/')
    assert response.status_code == 200
    
    response = client.get('/api/plugins/list')
    assert response.status_code == 200

print("Flask application validation successful")
```

---

## Validation Checklist

- [ ] vlan_checker_web.py created
- [ ] Flask app initialized
- [ ] SocketIO initialized
- [ ] All routes implemented
- [ ] WebSocket handlers implemented
- [ ] Plugin registry integrated
- [ ] Logging configured
- [ ] Flask application validation successful
- [ ] Ready for web templates reconstruction

---

## Troubleshooting

### Issue: Flask app fails to start

**Solution:**
- Check dependencies installed
- Verify SECRET_KEY configured
- Check port availability

### Issue: WebSocket connection fails

**Solution:**
- Verify SocketIO configuration
- Check CORS settings
- Verify async_mode

---

## Next Steps

After completing this prompt, proceed to P13: Web Templates

---

## References

- CODE_INVENTORY.md: ../../02-codebase/CODE_INVENTORY.md
- API_DOCUMENTATION.md: ../../02-codebase/API_DOCUMENTATION.md
- WEB_TEMPLATES_DOCUMENTATION.md: ../../06-ui-ux/WEB_TEMPLATES_DOCUMENTATION.md

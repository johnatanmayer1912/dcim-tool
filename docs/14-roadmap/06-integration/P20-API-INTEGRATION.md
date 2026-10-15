# P20: API Integration

| Field | Value |
|-------|-------|
| **Prompt ID** | P20 |
| **Phase** | 06-integration |
| **Dependency Level** | 5 (Depends on Phase 4) |
| **Estimated Time** | 10 minutes |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-02 |

---

## Purpose

Reconstruct API integration for REST and WebSocket APIs. This module provides the API layer that connects the web interface to the backend modules.

---

## Prerequisites

- Phase 4 (Web Interface) completed
- Flask app functional
- SocketIO functional
- Module integration functional

---

## Instructions

### Step 1: Create api_integration Module

```bash
cd modules
```

---

### Step 2: Create api_integration.py

```python
"""
API Integration

REST and WebSocket API integration layer.
"""

from flask import jsonify, request
from flask_socketio import emit
from typing import Dict, List, Any
from modules.module_integration import ModuleIntegrator
from modules.logging_utilities import get_logger

class APIIntegrator:
    """Integrator for REST and WebSocket APIs"""
    
    def __init__(self, app, socketio):
        self.app = app
        self.socketio = socketio
        self.module_integrator = ModuleIntegrator()
        self.logger = get_logger('api_integration')
        
        # Register API routes
        self._register_rest_routes()
        self._register_websocket_handlers()
    
    def _register_rest_routes(self):
        """Register REST API routes"""
        
        @self.app.route('/api/v1/plugins', methods=['GET'])
        def list_plugins():
            """List all available plugins"""
            try:
                plugins = self.module_integrator.plugin_registry.list_plugins()
                return jsonify({
                    'status': 'success',
                    'plugins': plugins
                })
            except Exception as e:
                self.logger.error(f"Error listing plugins: {e}")
                return jsonify({
                    'status': 'error',
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/v1/plugins/<plugin_id>/execute', methods=['POST'])
        def execute_plugin(plugin_id):
            """Execute plugin on device"""
            try:
                data = request.json
                device = data.get('device')
                credentials = data.get('credentials')
                params = data.get('params', {})
                
                result = self.module_integrator.execute_plugin_on_device(
                    plugin_id,
                    device,
                    credentials,
                    params
                )
                
                return jsonify(result)
                
            except Exception as e:
                self.logger.error(f"Error executing plugin: {e}")
                return jsonify({
                    'status': 'error',
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/v1/devices/vlan-info', methods=['POST'])
        def get_vlan_info():
            """Get VLAN information from device"""
            try:
                data = request.json
                device = data.get('device')
                credentials = data.get('credentials')
                
                result = self.module_integrator.get_device_vlan_info(device, credentials)
                
                return jsonify(result)
                
            except Exception as e:
                self.logger.error(f"Error getting VLAN info: {e}")
                return jsonify({
                    'status': 'error',
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/v1/devices/validate-config', methods=['POST'])
        def validate_config():
            """Validate device configuration"""
            try:
                data = request.json
                device = data.get('device')
                credentials = data.get('credentials')
                config_data = data.get('config')
                
                result = self.module_integrator.validate_device_config(
                    device,
                    credentials,
                    config_data
                )
                
                return jsonify(result)
                
            except Exception as e:
                self.logger.error(f"Error validating config: {e}")
                return jsonify({
                    'status': 'error',
                    'error': str(e)
                }), 500
    
    def _register_websocket_handlers(self):
        """Register WebSocket handlers"""
        
        @self.socketio.on('execute_plugin')
        def handle_execute_plugin(data):
            """Handle plugin execution via WebSocket"""
            try:
                plugin_id = data.get('plugin_id')
                device = data.get('device')
                credentials = data.get('credentials')
                params = data.get('params', {})
                
                result = self.module_integrator.execute_plugin_on_device(
                    plugin_id,
                    device,
                    credentials,
                    params
                )
                
                emit('plugin_result', result)
                
            except Exception as e:
                self.logger.error(f"WebSocket plugin execution error: {e}")
                emit('plugin_error', {'error': str(e)})
        
        @self.socketio.on('get_vlan_info')
        def handle_get_vlan_info(data):
            """Handle VLAN info request via WebSocket"""
            try:
                device = data.get('device')
                credentials = data.get('credentials')
                
                result = self.module_integrator.get_device_vlan_info(device, credentials)
                
                emit('vlan_info_result', result)
                
            except Exception as e:
                self.logger.error(f"WebSocket VLAN info error: {e}")
                emit('vlan_info_error', {'error': str(e)})
```

---

### Step 3: Update vlan_checker_web.py with API Integration

```python
# Add to vlan_checker_web.py after app initialization
from modules.api_integration import APIIntegrator

# Initialize API integrator
api_integrator = APIIntegrator(app, socketio)
```

---

### Step 4: Validate API Integration

```python
# Test API integration
from flask import Flask
from flask_socketio import SocketIO
from modules.api_integration import APIIntegrator

# Create test app
test_app = Flask(__name__)
test_app.config['SECRET_KEY'] = 'test-secret'
test_socketio = SocketIO(test_app)

# Create API integrator
integrator = APIIntegrator(test_app, test_socketio)

# Test route registration
with test_app.test_client() as client:
    response = client.get('/api/v1/plugins')
    assert response.status_code in [200, 500]

print("API integration validation successful")
```

---

## Validation Checklist

- [ ] api_integration.py created
- [ ] APIIntegrator class implemented
- [ ] REST routes registered
- [ ] Plugin execution endpoint implemented
- [ ] VLAN info endpoint implemented
- [ ] Config validation endpoint implemented
- [ ] WebSocket handlers registered
- [ ] WebSocket plugin execution implemented
- [ ] WebSocket VLAN info implemented
- [ ] API integration validation successful
- [ ] Ready for database integration reconstruction

---

## Troubleshooting

### Issue: API route not registered

**Solution:**
- Verify Flask app initialization
- Check route registration order
- Test route with test client

### Issue: WebSocket handler not working

**Solution:**
- Verify SocketIO initialization
- Check handler registration
- Test WebSocket connection

---

## Next Steps

After completing this prompt, proceed to P21: Database Integration

---

## References

- CODE_INVENTORY.md: ../../02-codebase/CODE_INVENTORY.md
- API_DOCUMENTATION.md: ../../02-codebase/API_DOCUMENTATION.md

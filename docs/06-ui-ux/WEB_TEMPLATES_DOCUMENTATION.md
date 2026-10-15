# Web Templates Documentation

## Overview

Network Swiss Tool Pro uses Flask templates for the web interface. This document provides comprehensive documentation for all web templates.

**Generated:** 2026-06-02  
**Purpose:** UI/UX documentation for web templates  
**Templates Location:** modules/web/templates/

---

## index.html

### Purpose
Main single-page application (SPA) interface for Network Swiss Tool Pro.

### File Location
`modules/web/templates/index.html`

### File Size
~203,945 bytes (~200KB)

### Architecture
- Single-page application (SPA) design
- All UI components in one file
- JavaScript for dynamic functionality
- CSS for styling
- WebSocket integration for real-time updates
- API integration for backend operations

### Key Sections

#### 1. Header Section
- Application title and branding
- Version display
- Navigation menu
- User interface controls

#### 2. Main Content Area
- Tab-based interface for different operations
- Dynamic content loading
- Plugin integration panels
- Status indicators

#### 3. JavaScript Logic
- Socket.IO client initialization
- API call functions
- Event handlers
- Data processing
- UI updates
- Error handling

#### 4. CSS Styling
- Responsive design
- Theme styling
- Component styling
- Layout styling
- Utility classes

### JavaScript Functions

#### Socket.IO Integration
```javascript
// Socket.IO client initialization
const socket = io();

// Connection event
socket.on('connect', function() {
    console.log('Connected to server');
});

// Disconnect event
socket.on('disconnect', function() {
    console.log('Disconnected from server');
});
```

#### API Call Functions
```javascript
// Generic API call function
async function apiCall(endpoint, method, data) {
    const response = await fetch(endpoint, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    });
    return response.json();
}
```

#### Plugin Integration
```javascript
// Load plugin list
async function loadPlugins() {
    const response = await apiCall('/api/plugins/list', 'GET');
    renderPlugins(response.plugins);
}

// Execute plugin
async function executePlugin(pluginId, params) {
    const response = await apiCall('/api/plugins/execute', 'POST', {
        plugin_id: pluginId,
        params: params
    });
    return response;
}
```

#### UI Update Functions
```javascript
// Update status indicator
function updateStatus(status) {
    document.getElementById('status').textContent = status;
}

// Render plugin list
function renderPlugins(plugins) {
    const container = document.getElementById('plugins');
    plugins.forEach(plugin => {
        // Render plugin card
    });
}
```

### CSS Styling

#### Responsive Design
```css
/* Mobile-first responsive design */
@media (max-width: 768px) {
    /* Mobile styles */
}

@media (min-width: 769px) {
    /* Desktop styles */
}
```

#### Theme Styling
```css
/* Dark theme variables */
:root {
    --primary-color: #007bff;
    --secondary-color: #6c757d;
    --background-color: #1e1e1e;
    --text-color: #ffffff;
}
```

#### Component Styling
```css
/* Button styles */
.btn {
    padding: 10px 20px;
    border-radius: 5px;
    cursor: pointer;
}

/* Card styles */
.card {
    background-color: var(--background-color);
    border-radius: 10px;
    padding: 20px;
}
```

### API Integration

#### REST API Endpoints Used
- `GET /api/plugins/list` - Load plugin list
- `POST /api/plugins/execute` - Execute plugin
- `GET /api/inventory` - Load inventory
- `POST /api/execute` - Execute operation
- `GET /api/logs` - Load logs
- `GET /api/version` - Get version

#### WebSocket Events Used
- `connect` - Connection established
- `disconnect` - Connection lost
- `cli_output` - CLI terminal output
- `cli_status` - CLI terminal status
- `log_update` - Log update notification

### Plugin Integration

#### Plugin Loading
- Plugins loaded dynamically from `/api/plugins/list`
- Plugin metadata displayed in UI
- Plugin execution triggered via API

#### Plugin Execution
- Plugin parameters collected from UI
- Plugin execution via `/api/plugins/execute`
- Plugin results displayed in UI
- Plugin reports rendered in dedicated panel

### User Workflow

#### 1. Application Startup
1. User opens application
2. Index.html loads
3. Socket.IO client initializes
4. API calls load initial data
5. UI renders with current state

#### 2. Operation Execution
1. User selects operation from UI
2. User provides parameters
3. User clicks execute button
4. API call made to backend
5. Results displayed in UI
6. Reports rendered in dedicated panel

#### 3. Plugin Execution
1. User selects plugin from plugin list
2. User provides plugin parameters
3. User clicks execute button
4. Plugin execution via API
5. Results displayed in UI
6. Plugin reports rendered

### Dependencies

#### External Libraries
- Socket.IO client (via CDN)
- jQuery (for DOM manipulation)
- Bootstrap (for styling)

#### Internal Dependencies
- Flask backend
- Socket.IO backend
- Plugin system
- API endpoints

### Configuration

#### Socket.IO Configuration
```javascript
const socket = io({
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionAttempts: 5
});
```

#### API Configuration
```javascript
const API_BASE_URL = 'http://127.0.0.1:5051';
```

### Error Handling

#### API Error Handling
```javascript
try {
    const response = await apiCall(endpoint, method, data);
    if (response.error) {
        showError(response.error);
    }
} catch (error) {
    showError('API call failed: ' + error.message);
}
```

#### WebSocket Error Handling
```javascript
socket.on('error', function(error) {
    console.error('WebSocket error:', error);
    showError('WebSocket connection error');
});
```

### Performance Considerations

#### Optimizations
- Lazy loading of plugin data
- Caching of API responses
- Debouncing of user input
- Efficient DOM updates

#### Best Practices
- Minimize DOM manipulation
- Use event delegation
- Implement proper error handling
- Use async/await for API calls

---

## cli_terminal.html

### Purpose
CLI terminal UI component for interactive device sessions via WebSocket.

### File Location
`modules/web/templates/cli_terminal.html`

### File Size
~32,960 bytes (~32KB)

### Architecture
- Terminal emulation interface
- WebSocket integration for real-time communication
- PTY handling for terminal resizing
- Command history
- Terminal styling

### Key Sections

#### 1. Terminal Container
- Terminal display area
- Command input field
- Control buttons
- Status indicators

#### 2. JavaScript Logic
- Socket.IO client initialization
- Terminal emulation
- PTY handling
- Command history management
- WebSocket event handling

#### 3. CSS Styling
- Terminal styling
- Cursor styling
- Command styling
- Control button styling

### JavaScript Functions

#### Socket.IO Integration
```javascript
// CLI Socket.IO client
const cliSocket = io('/cli');

// Connect to CLI session
function connectCLI(sessionId, host, deviceType, username, password) {
    cliSocket.emit('cli_connect', {
        session_id: sessionId,
        host: host,
        device_type: deviceType,
        username: username,
        password: password
    });
}

// Send command to CLI
function sendCLICommand(sessionId, command) {
    cliSocket.emit('cli_data', {
        session_id: sessionId,
        data: command
    });
}

// Resize CLI terminal
function resizeCLITerminal(sessionId, cols, rows) {
    cliSocket.emit('cli_resize', {
        session_id: sessionId,
        cols: cols,
        rows: rows
    });
}

// Disconnect CLI session
function disconnectCLI(sessionId) {
    cliSocket.emit('cli_disconnect', {
        session_id: sessionId
    });
}
```

#### Terminal Emulation
```javascript
// Handle CLI output
cliSocket.on('cli_output', function(data) {
    appendToTerminal(data.output);
});

// Handle CLI status
cliSocket.on('cli_status', function(data) {
    updateCLIStatus(data.status);
});

// Handle CLI errors
cliSocket.on('cli_error', function(data) {
    showCLIError(data.error);
});
```

#### Command History
```javascript
let commandHistory = [];
let historyIndex = -1;

// Add command to history
function addToHistory(command) {
    commandHistory.push(command);
    historyIndex = commandHistory.length;
}

// Navigate history
function navigateHistory(direction) {
    if (direction === 'up' && historyIndex > 0) {
        historyIndex--;
        setInputValue(commandHistory[historyIndex]);
    } else if (direction === 'down' && historyIndex < commandHistory.length - 1) {
        historyIndex++;
        setInputValue(commandHistory[historyIndex]);
    }
}
```

### CSS Styling

#### Terminal Styling
```css
.terminal {
    background-color: #000000;
    color: #00ff00;
    font-family: 'Courier New', monospace;
    font-size: 14px;
    padding: 10px;
    border-radius: 5px;
    overflow-y: auto;
    height: 400px;
}
```

#### Cursor Styling
```css
.cursor {
    display: inline-block;
    width: 10px;
    height: 18px;
    background-color: #00ff00;
    animation: blink 1s step-end infinite;
}

@keyframes blink {
    50% { opacity: 0; }
}
```

#### Command Styling
```css
.command-input {
    background-color: #000000;
    color: #00ff00;
    font-family: 'Courier New', monospace;
    font-size: 14px;
    border: none;
    outline: none;
    width: 100%;
}
```

### WebSocket Events

#### Client Events
- `cli_connect` - Connect to CLI session
- `cli_data` - Send command to CLI
- `cli_resize` - Resize CLI terminal
- `cli_disconnect` - Disconnect CLI session

#### Server Events
- `cli_output` - CLI output from device
- `cli_status` - CLI connection status
- `cli_error` - CLI error messages

### Dependencies

#### External Libraries
- Socket.IO client (via CDN)
- xterm.js (for terminal emulation, if used)

#### Internal Dependencies
- Flask backend
- Socket.IO backend
- CLI manager (modules/cli_manager.py)

### Configuration

#### Socket.IO Configuration
```javascript
const cliSocket = io('/cli', {
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionAttempts: 5
});
```

#### Terminal Configuration
```javascript
const terminalConfig = {
    cols: 80,
    rows: 24,
    fontSize: 14,
    fontFamily: 'Courier New',
    backgroundColor: '#000000',
    textColor: '#00ff00'
};
```

### Error Handling

#### Connection Error Handling
```javascript
cliSocket.on('connect_error', function(error) {
    console.error('CLI connection error:', error);
    showCLIError('Failed to connect to CLI session');
});
```

#### Command Error Handling
```javascript
cliSocket.on('cli_error', function(data) {
    console.error('CLI command error:', data.error);
    showCLIError(data.error);
});
```

### Performance Considerations

#### Optimizations
- Efficient terminal rendering
- Debouncing of resize events
- Command history caching
- Efficient WebSocket communication

#### Best Practices
- Limit terminal buffer size
- Implement proper cleanup on disconnect
- Use efficient DOM updates for terminal output
- Implement proper error handling

---

## Integration with Backend

### Flask Integration
Both templates are served by Flask via `render_template()`:

```python
@app.route('/')
def index():
    return render_template('index.html', ...)
```

### Socket.IO Integration
Both templates use Socket.IO for real-time communication:

```python
@socketio.on('cli_connect')
def handle_cli_connect(data):
    # Handle CLI connection
    ...
```

### API Integration
index.html uses REST API endpoints for backend communication:

```python
@app.route('/api/plugins/list')
def api_plugins_list():
    # Return plugin list
    ...
```

---

## Security Considerations

### Input Validation
- All user input validated on backend
- XSS prevention via proper escaping
- CSRF protection via Flask-WTF

### WebSocket Security
- WebSocket connections authenticated
- Session-based authentication
- Secure WebSocket configuration

### API Security
- API endpoints protected
- Rate limiting (if implemented)
- Input sanitization

---

## Browser Compatibility

### Supported Browsers
- Chrome 90+
- Firefox 88+
- Edge 90+
- Safari 14+

### Required Features
- WebSocket support
- ES6 JavaScript support
- CSS Grid support
- Flexbox support

---

## Accessibility

### Keyboard Navigation
- Full keyboard navigation support
- Tab order logical and consistent
- Keyboard shortcuts documented

### Screen Reader Support
- ARIA labels on interactive elements
- Semantic HTML structure
- Alt text on images

### High Contrast Mode
- Support for high contrast mode
- Color contrast ratios meet WCAG AA standards

---

## Maintenance

### Version Control
- Templates versioned with application
- Changes tracked in CHANGELOG.md
- Breaking changes documented

### Testing
- Manual testing of UI components
- Integration testing with backend
- Cross-browser testing

### Updates
- Regular updates to dependencies
- Security patches applied promptly
- Feature additions documented

---

## Troubleshooting

### Common Issues

#### Socket.IO Connection Failed
**Symptom:** WebSocket connection fails  
**Solution:** Check backend Socket.IO server is running, check firewall settings

#### API Calls Failing
**Symptom:** API calls return errors  
**Solution:** Check backend server is running, check API endpoint configuration

#### Terminal Not Responding
**Symptom:** CLI terminal not responding to input  
**Solution:** Check WebSocket connection, check CLI manager backend

#### UI Not Updating
**Symptom:** UI not updating with new data  
**Solution:** Check JavaScript console for errors, check API responses

---

## Future Enhancements

### Planned Improvements
- Separate CSS file for better maintainability
- Separate JavaScript file for better maintainability
- Component-based architecture (React/Vue migration)
- Enhanced accessibility features
- Performance optimizations
- Additional keyboard shortcuts
- Enhanced error handling
- Better mobile support

---

## References

- Flask Documentation: https://flask.palletsprojects.com/
- Socket.IO Documentation: https://socket.io/docs/
- xterm.js Documentation: https://xtermjs.org/
- Bootstrap Documentation: https://getbootstrap.com/

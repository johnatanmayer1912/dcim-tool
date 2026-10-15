# P13: Web Templates

| Field | Value |
|-------|-------|
| **Prompt ID** | P13 |
| **Phase** | 04-web-interface |
| **Dependency Level** | 3 (Depends on P12) |
| **Estimated Time** | 12 minutes |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-02 |

---

## Purpose

Reconstruct web templates (HTML/Jinja2) for the web interface. This includes the main application interface and CLI terminal interface.

---

## Prerequisites

- P12: Flask Application completed
- Flask app functional
- Templates directory created

---

## Instructions

### Step 1: Create templates/index.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Network Swiss Tool Pro</title>
    <link rel="stylesheet" href="/static/css/style.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
</head>
<body>
    <div class="container">
        <header>
            <h1>Network Swiss Tool Pro</h1>
            <nav>
                <a href="#discovery">Discovery</a>
                <a href="#topology">Topology</a>
                <a href="#standards">Standards</a>
                <a href="#health-check">Health Check</a>
                <a href="#cli-terminal">CLI Terminal</a>
            </nav>
        </header>
        
        <main>
            <section id="discovery">
                <h2>Network Discovery</h2>
                <div class="controls">
                    <button id="run-discovery">Run Discovery</button>
                </div>
                <div id="discovery-results"></div>
            </section>
            
            <section id="topology">
                <h2>Topology Visualization</h2>
                <div class="controls">
                    <button id="run-topology">Generate Topology</button>
                </div>
                <div id="topology-results"></div>
            </section>
            
            <section id="standards">
                <h2>Standards Validation</h2>
                <div class="controls">
                    <button id="run-standards">Validate Standards</button>
                </div>
                <div id="standards-results"></div>
            </section>
            
            <section id="health-check">
                <h2>Health Check</h2>
                <div class="controls">
                    <button id="run-health-check">Run Health Check</button>
                </div>
                <div id="health-check-results"></div>
            </section>
            
            <section id="cli-terminal">
                <h2>CLI Terminal</h2>
                <div class="terminal-container">
                    <div id="terminal-output"></div>
                    <div class="terminal-input">
                        <input type="text" id="cli-command" placeholder="Enter command...">
                        <button id="send-command">Send</button>
                    </div>
                </div>
            </section>
        </main>
        
        <footer>
            <p>&copy; 2026 Network Swiss Tool Pro v7.0.10</p>
        </footer>
    </div>
    
    <script src="/static/js/app.js"></script>
</body>
</html>
```

---

### Step 2: Create templates/cli_terminal.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CLI Terminal - Network Swiss Tool Pro</title>
    <link rel="stylesheet" href="/static/css/terminal.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
</head>
<body>
    <div class="terminal-container">
        <div class="terminal-header">
            <h2>CLI Terminal</h2>
            <select id="device-select">
                <option value="">Select Device</option>
            </select>
            <button id="connect-device">Connect</button>
            <button id="disconnect-device">Disconnect</button>
        </div>
        
        <div class="terminal-output" id="terminal-output">
            <div class="terminal-line">Welcome to CLI Terminal</div>
            <div class="terminal-line">Select a device and connect to begin</div>
        </div>
        
        <div class="terminal-input">
            <span class="prompt" id="prompt">&gt;</span>
            <input type="text" id="cli-command" placeholder="Enter command..." autocomplete="off">
        </div>
    </div>
    
    <script src="/static/js/terminal.js"></script>
</body>
</html>
```

---

### Step 3: Create static/css/style.css

```css
/* Main Styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: Arial, sans-serif;
    background-color: #f5f5f5;
    color: #333;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

header {
    background-color: #2c3e50;
    color: white;
    padding: 20px;
    border-radius: 5px;
    margin-bottom: 20px;
}

header h1 {
    margin-bottom: 10px;
}

nav a {
    color: white;
    text-decoration: none;
    margin-right: 20px;
    padding: 5px 10px;
    border-radius: 3px;
}

nav a:hover {
    background-color: #34495e;
}

section {
    background-color: white;
    padding: 20px;
    margin-bottom: 20px;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

section h2 {
    margin-bottom: 15px;
    color: #2c3e50;
}

.controls {
    margin-bottom: 15px;
}

button {
    background-color: #3498db;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 3px;
    cursor: pointer;
    font-size: 14px;
}

button:hover {
    background-color: #2980b9;
}

footer {
    text-align: center;
    padding: 20px;
    color: #7f8c8d;
}
```

---

### Step 4: Create static/css/terminal.css

```css
/* Terminal Styles */
.terminal-container {
    background-color: #1e1e1e;
    color: #00ff00;
    padding: 20px;
    border-radius: 5px;
    font-family: 'Courier New', monospace;
}

.terminal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
    padding-bottom: 10px;
    border-bottom: 1px solid #333;
}

.terminal-header h2 {
    color: #00ff00;
    margin: 0;
}

.terminal-header select,
.terminal-header button {
    margin-left: 10px;
    padding: 5px 10px;
    border-radius: 3px;
    border: 1px solid #333;
    background-color: #333;
    color: #00ff00;
    cursor: pointer;
}

.terminal-output {
    height: 400px;
    overflow-y: auto;
    padding: 10px;
    background-color: #000;
    border: 1px solid #333;
    margin-bottom: 10px;
    border-radius: 3px;
}

.terminal-line {
    margin-bottom: 5px;
    white-space: pre-wrap;
}

.terminal-input {
    display: flex;
    align-items: center;
}

.prompt {
    margin-right: 10px;
    color: #00ff00;
}

#cli-command {
    flex: 1;
    background-color: #000;
    border: 1px solid #333;
    color: #00ff00;
    padding: 10px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
    font-size: 14px;
}

#cli-command:focus {
    outline: none;
    border-color: #00ff00;
}
```

---

### Step 5: Create static/js/app.js

```javascript
// Main Application JavaScript
const socket = io();

// Connect to WebSocket
socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
});

// Discovery
document.getElementById('run-discovery').addEventListener('click', () => {
    fetch('/api/execute', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            action: 'discovery',
            devices: [],
            credentials: {}
        })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('discovery-results').innerHTML = 
            `<pre>${JSON.stringify(data, null, 2)}</pre>`;
    });
});

// Topology
document.getElementById('run-topology').addEventListener('click', () => {
    fetch('/api/execute', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            action: 'topology',
            devices: [],
            credentials: {}
        })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('topology-results').innerHTML = 
            `<pre>${JSON.stringify(data, null, 2)}</pre>`;
    });
});

// Standards
document.getElementById('run-standards').addEventListener('click', () => {
    fetch('/api/execute', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            action: 'standards',
            devices: [],
            credentials: {}
        })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('standards-results').innerHTML = 
            `<pre>${JSON.stringify(data, null, 2)}</pre>`;
    });
});

// Health Check
document.getElementById('run-health-check').addEventListener('click', () => {
    fetch('/api/health-check/run', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            devices: [],
            credentials: {}
        })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('health-check-results').innerHTML = 
            `<pre>${JSON.stringify(data, null, 2)}</pre>`;
    });
});
```

---

### Step 6: Create static/js/terminal.js

```javascript
// CLI Terminal JavaScript
const socket = io();
let sessionId = null;

// Connect to WebSocket
socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('cli_output', (data) => {
    const output = document.getElementById('terminal-output');
    const line = document.createElement('div');
    line.className = 'terminal-line';
    line.textContent = data.output;
    output.appendChild(line);
    output.scrollTop = output.scrollHeight;
});

// Send command
document.getElementById('send-command').addEventListener('click', () => {
    const command = document.getElementById('cli-command').value;
    if (command) {
        socket.emit('cli_command', {
            session_id: sessionId,
            command: command
        });
        document.getElementById('cli-command').value = '';
    }
});

// Enter key to send command
document.getElementById('cli-command').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        document.getElementById('send-command').click();
    }
});
```

---

## Validation Checklist

- [ ] templates/index.html created
- [ ] templates/cli_terminal.html created
- [ ] static/css/style.css created
- [ ] static/css/terminal.css created
- [ ] static/js/app.js created
- [ ] static/js/terminal.js created
- [ ] Templates validated
- [ ] CSS validated
- [ ] JavaScript validated
- [ ] Ready for WebSocket handling reconstruction

---

## Troubleshooting

### Issue: Template rendering fails

**Solution:**
- Verify template directory structure
- Check Flask template configuration
- Validate Jinja2 syntax

### Issue: CSS not loading

**Solution:**
- Verify static directory structure
- Check Flask static file configuration
- Validate CSS syntax

---

## Next Steps

After completing this prompt, proceed to P14: WebSocket Handling

---

## References

- CODE_INVENTORY.md: ../../02-codebase/CODE_INVENTORY.md
- WEB_TEMPLATES_DOCUMENTATION.md: ../../06-ui-ux/WEB_TEMPLATES_DOCUMENTATION.md
- JINJA2_TEMPLATES_DOCUMENTATION.md: ../../06-ui-ux/JINJA2_TEMPLATES_DOCUMENTATION.md

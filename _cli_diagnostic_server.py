"""
Minimal CLI diagnostic server to test the exact connect flow.
This will show us EXACTLY where it's failing.
"""
import sys
sys.path.insert(0, '.')

# Import telnetlib compat first
try:
    import telnetlib
except ImportError:
    import telnetlib_compat

import time
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

@app.route('/')
def index():
    return """
    <html><body>
    <h1>CLI Diagnostic</h1>
    <button onclick="testConnect()">Test Connect</button>
    <div id="log" style="font-family:monospace; white-space:pre; margin-top:20px;"></div>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script>
    var socket = io("http://127.0.0.1:5052");
    var sessionId = 'test_' + Date.now();

    socket.on('connect', () => {
        log('Socket connected via ' + socket.io.engine.transport.name);
    });

    socket.on('cli_progress', (data) => {
        log('[PROGRESS] ' + data.message);
    });

    socket.on('cli_status', (data) => {
        log('[STATUS] ' + data.status + ' - ' + (data.message || ''));
    });

    socket.on('cli_error', (data) => {
        log('[ERROR] ' + data.message);
    });

    function testConnect() {
        log('Emitting cli_connect with session_id=' + sessionId);
        socket.emit('cli_connect', {
            session_id: sessionId,
            host: '127.0.0.1',  // localhost for testing
            port: 22,
            device_type: 'cisco_ios',
            username: 'test',
            password: 'test',
            enable_password: ''
        });
    }

    function log(msg) {
        document.getElementById('log').textContent += '[' + new Date().toLocaleTimeString() + '] ' + msg + '\\n';
    }
    </script>
    </body></html>
    """

@socketio.on('cli_connect')
def handle_cli_connect(data):
    from flask import request
    session_id = data.get('session_id')
    device_host = data.get('host')
    username = data.get('username')
    password = data.get('password')
    device_port = int(data.get('port', 22))

    print(f"[SERVER] Received cli_connect: session_id={session_id}, host={device_host}:{device_port}")

    join_room(session_id)
    print(f"[SERVER] Joined room: {session_id}")

    sid = request.sid
    print(f"[SERVER] Client SID: {sid}")

    def background_connect():
        print(f"[SERVER] background_connect started")

        # Test 1: Emit to room only
        print(f"[SERVER] Emitting cli_progress to room={session_id}")
        socketio.emit('cli_progress', {'message': 'Test 1: Room only'}, to=session_id)
        time.sleep(0.5)

        # Test 2: Emit to SID only
        print(f"[SERVER] Emitting cli_progress to sid={sid}")
        socketio.emit('cli_progress', {'message': 'Test 2: SID only'}, to=sid)
        time.sleep(0.5)

        # Test 3: Double-emit
        print(f"[SERVER] Emitting cli_progress to BOTH room and SID")
        socketio.emit('cli_progress', {'message': 'Test 3: Room'}, to=session_id)
        socketio.emit('cli_progress', {'message': 'Test 3: SID'}, to=sid)
        time.sleep(0.5)

        # Test 4: Final status
        print(f"[SERVER] Emitting cli_status (double)")
        socketio.emit('cli_status', {'status': 'connected', 'message': 'Test complete'}, to=session_id)
        socketio.emit('cli_status', {'status': 'connected', 'message': 'Test complete'}, to=sid)

        print(f"[SERVER] background_connect finished")

    socketio.start_background_task(background_connect)
    print(f"[SERVER] Background task started")

if __name__ == '__main__':
    print("Starting diagnostic server on http://127.0.0.1:5052")
    print("Open browser to http://127.0.0.1:5052 and click 'Test Connect'")
    print("Watch the console and browser log to see which emits are received")
    socketio.run(app, host='127.0.0.1', port=5052, allow_unsafe_werkzeug=True)

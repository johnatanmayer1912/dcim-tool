import time
import socketio
import threading
import urllib.request

def start_server():
    import vlan_checker_web
    # Suppress werkzeug logging
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    vlan_checker_web.run_web()

server_thread = threading.Thread(target=start_server, daemon=True)
server_thread.start()

# Wait for server to start
for _ in range(20):
    try:
        urllib.request.urlopen("http://127.0.0.1:5051/health", timeout=1)
        break
    except:
        time.sleep(0.5)
else:
    print("Server failed to start")
    exit(1)

print("Server started, connecting client...")

sio = socketio.Client()
events = []

@sio.on('cli_status')
def on_cli_status(data):
    print("Received cli_status:", data)
    events.append(('cli_status', data))

@sio.on('cli_progress')
def on_cli_progress(data):
    print("Received cli_progress:", data)
    events.append(('cli_progress', data))

@sio.on('cli_error')
def on_cli_error(data):
    print("Received cli_error:", data)
    events.append(('cli_error', data))

try:
    sio.connect('http://127.0.0.1:5051', transports=['polling'])
    print("Client connected")
    
    sio.emit('cli_connect', {
        'session_id': 'test-session-123',
        'host': '1.1.1.1', # public dummy IP
        'port': 2222,
        'username': 'admin',
        'password': 'password',
        'device_type': 'cisco_ios'
    })
    print("Emitted cli_connect")
    
    # Wait for response
    for _ in range(10):
        time.sleep(1)
        if any(e[0] == 'cli_error' or e[0] == 'cli_status' for e in events):
            break
            
    print("Test finished. Events:", events)
    sio.disconnect()
except Exception as e:
    print("Error:", e)

import socket
import paramiko
import threading
import json
import os
import sys
import time

# Host key for the server
HOST_KEY = paramiko.RSAKey.generate(2048)

class MockSSHServer(paramiko.ServerInterface):
    def __init__(self, device_data):
        self.event = threading.Event()
        self.device_data = device_data
        self.selected_type = "cisco_ios" # Default

    def check_auth_password(self, username, password):
        print(f"[SSH] Auth attempt for user: {username}")
        # Identify device type by username for simulation flexibility
        # e.g. user 'juniper' triggers junos responses
        if "juniper" in username.lower() or "srx" in username.lower():
            self.selected_type = "juniper_junos"
        else:
            self.selected_type = "cisco_ios"
        return paramiko.AUTH_SUCCESSFUL

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True

def handle_connection(client, addr, device_data):
    try:
        transport = paramiko.Transport(client)
        transport.add_server_key(HOST_KEY)
        server = MockSSHServer(device_data)
        
        try:
            transport.start_server(server=server)
        except paramiko.SSHException:
            return

        chan = transport.accept(20)
        if chan is None:
            return

        server.event.wait(10)
        if not server.event.is_set():
            chan.close()
            return

        # Send initial prompt
        prompt = "Switch#" if server.selected_type == "cisco_ios" else "user@SRX-SIM-01> "
        chan.send(prompt)

        buffer = ""
        while True:
            data = chan.recv(1024).decode('utf-8', errors='ignore')
            if not data:
                break
            
            buffer += data
            if '\r' in data or '\n' in data:
                command = buffer.strip()
                print(f"[CMD] {server.selected_type} executing: {command}")
                
                response = "\n% Invalid input detected at '^' marker."
                
                # Check for matches in our mock data
                matched = False
                for cmd, output in device_data.get(server.selected_type, {}).items():
                    if command.lower().startswith(cmd.lower()):
                        response = "\n" + output
                        matched = True
                        break
                
                # Special cases for navigation/boilerplate
                if command.lower() in ["exit", "quit"]:
                    chan.send("\nClosing connection...\n")
                    break
                if command.lower() in ["conf t", "configure"]:
                    response = "\nEnter configuration commands, one per line. End with CNTL/Z."
                    prompt = "Switch(config)# " if server.selected_type == "cisco_ios" else "user@SRX-SIM-01# "
                if command.lower() == "end" or command.lower() == "exit":
                    prompt = "Switch#" if server.selected_type == "cisco_ios" else "user@SRX-SIM-01> "

                chan.send(response + "\n" + prompt)
                buffer = ""

        chan.close()
    except Exception as e:
        print(f"[ERR] Connection dropped: {e}")
    finally:
        transport.close()

def start_simulation(port=2222):
    # Load data
    data_path = os.path.join(os.path.dirname(__file__), "device_data.json")
    try:
        with open(data_path, 'r') as f:
            device_data = json.load(f)
    except Exception as e:
        print(f"Failed to load device_data.json: {e}")
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('127.0.0.1', port))
    sock.listen(100)
    print(f"\n[SYSTEM] Internal Simulation Server Started on 127.0.0.1:{port}")
    print(f"[INFO] Using {data_path} for command responses.")
    print(f"[HINT] Use username 'cisco' for IOS behavior, 'juniper' for JUNOS behavior.")
    print("-" * 60)

    while True:
        client, addr = sock.accept()
        print(f"[CONN] Received from {addr[0]}:{addr[1]}")
        threading.Thread(target=handle_connection, args=(client, addr, device_data), daemon=True).start()

if __name__ == "__main__":
    p = 2222
    if len(sys.argv) > 1:
        p = int(sys.argv[1])
    start_simulation(p)

# 🌐 Network Swiss Tool — Internal Simulation Guide

This folder contains a local "Mock SSH Server" that allows you to test 100% of the program's functionality (Parsers, UI, Topology, MAC Tracing, Reporting) without needing real hardware or an internet connection.

## 📁 Included Files
- `mock_ssh_server.py`: The Python script that simulates a Cisco/Juniper device.
- `device_data.json`: A database of command outputs (`show vlan`, `show version`, etc.) that the mock server uses to respond.
- `sim_inventory.txt`: A pre-configured inventory file pointing to your local machine.

## 🚀 How to Run the Simulation

### Step 1: Start the Mock Server
You need to run the mock server on your local machine. By default, it uses port 2222.
```powershell
python simulation/mock_ssh_server.py
```

### Step 2: Handle the Port Mapping (Critical)
Since the tool is hardcoded to use SSH Port 22, you have two choices:

**Option A (Recommended for Admin users)**:
Run the mock server on Port 22 directly (requires admin rights and stopping any existing SSH services).
```powershell
# Run as Administrator
python simulation/mock_ssh_server.py 22
```

**Option B (Port Forwarding)**:
If you cannot run on Port 22, use Windows `netsh` to forward traffic from `127.0.0.1:22` to `127.0.0.1:2222`.
```powershell
netsh interface portproxy add v4tov4 listenport=22 listenaddress=127.0.0.1 connectport=2222 connectaddress=127.0.0.1
```

### Step 3: Run the Network Swiss Tool
1.  Copy `simulation/sim_inventory.txt` to the root folder and rename it to `inventory.txt`.
2.  Launch `VlanCheckerWeb.exe` or `VlanCheckerGUI.exe`.
3.  Use the following credentials:
    - **Username**: `cisco` (triggers Cisco IOS simulation)
    - **Password**: `any`
    - **Username**: `juniper` (triggers Junos SRX simulation)
4.  Run any action:
    - **MAC Trace**: Search for `0011.2233.4455` to see it found on Gi1/1/1.
    - **Topology**: Run it to see a link between `Switch01` and `Switch02`.
    - **Interfaces**: Run with the `notconnect` filter to see it work.

## 🛠️ Customizing the Simulation
You can edit `simulation/device_data.json` to add more commands or change existing outputs. Any changes take effect the next time a command is run in the tool (no need to restart the mock server).

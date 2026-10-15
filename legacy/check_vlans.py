import csv
import getpass
import os
import sys
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException

def get_credentials():
    """Prompts for username and password."""
    username = input("Enter SSH Username: ")
    password = getpass.getpass("Enter SSH Password: ")
    return username, password

def process_inventory(inventory_file):
    """Reads the inventory CSV file."""
    devices = []
    if not os.path.exists(inventory_file):
        print(f"Error: Inventory file '{inventory_file}' not found.")
        return []
    
    try:
        with open(inventory_file, mode='r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Basic validation
                if 'host' in row and 'device_type' in row:
                    devices.append(row)
                else:
                    print(f"Skipping invalid row: {row}")
    except Exception as e:
        print(f"Error reading inventory: {e}")
        return []

    return devices

def check_vlans(device, username, password):
    """Connects to a device and checks VLANs."""
    host = device['host']
    device_type = device['device_type']
    port = device.get('port', 22)

    print(f"\nConnecting to {host} ({device_type})...")

    netmiko_device = {
        'device_type': device_type,
        'host': host,
        'username': username,
        'password': password,
        'port': port,
        # 'global_delay_factor': 2, # Uncomment for slower devices
    }

    try:
        with ConnectHandler(**netmiko_device) as net_connect:
            print(f"Connected to {host}. retrieving VLAN info...")
            
            # Determine command based on device type
            cmd = "show vlan"
            if "juniper" in device_type.lower():
                cmd = "show vlans"
            elif "nxos" in device_type.lower():
                 cmd = "show vlan brief"
            elif "ios" in device_type.lower():
                 cmd = "show vlan brief"
            
            output = net_connect.send_command(cmd)
            return f"--- {host} ({device_type}) VLAN Check ---\n{output}\n"

    except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
        error_msg = f"Failed to connect to {host}: {str(e)}"
        print(error_msg)
        return f"--- {host} ({device_type}) FAILED ---\n{error_msg}\n"
    except Exception as e:
        error_msg = f"Error processing {host}: {str(e)}"
        print(error_msg)
        return f"--- {host} ({device_type}) ERROR ---\n{error_msg}\n"

def main():
    inventory_file = 'inventory.csv'
    output_file = 'vlan_report.txt'

    print("Network Device VLAN Checker (Offline Mode)")
    print("------------------------------------------")

    devices = process_inventory(inventory_file)
    if not devices:
        print("No devices found in inventory. Exiting.")
        return

    username, password = get_credentials()

    results = []
    
    for device in devices:
        result = check_vlans(device, username, password)
        results.append(result)

    # Write output to file
    try:
        with open(output_file, 'w') as f:
            f.write("VLAN Check Report\n")
            f.write("=================\n\n")
            for res in results:
                f.write(res + "\n")
        print(f"\nReport saved to {output_file}")
    except Exception as e:
        print(f"Error writing report: {e}")

if __name__ == "__main__":
    main()

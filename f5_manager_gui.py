import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
import re
import threading
import sys
import subprocess
import platform
import time
import queue
import ipaddress
from datetime import datetime

# External library
try:
    from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
except ImportError:
    messagebox.showerror("Dependency Error", "Netmiko is required. Please install it via 'pip install netmiko'")
    sys.exit(1)

# --- Configuration & Constants ---
DEFAULT_F5_PORT = 22
DEVICE_TYPE = 'f5_tmsh' 

class F5ManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("F5 BIG-IP Management Tool (v2.1)")
        self.root.geometry("1200x900")
        
        # --- Variables ---
        self.inventory_path = tk.StringVar(value="f5_inventory.txt")
        self.username = tk.StringVar()
        self.password = tk.StringVar()
        
        # Finder
        self.search_query = tk.StringVar()
        self.search_type_var = tk.StringVar(value="Virtual Server")
        self.ip_segment_var = tk.StringVar()
        
        # Config - VS
        self.vs_name_input = tk.StringVar()
        self.vs_ip_input = tk.StringVar()
        self.vs_ports_input = tk.StringVar() # CSV
        self.monitor_var = tk.StringVar(value="gateway_icmp")
        
        # Config - Pool for VS
        self.vs_pool_choice = tk.StringVar(value="Create New")
        self.vs_node_mode = tk.StringVar(value="No Nodes") # No Nodes, Add Nodes
        self.vs_nodes_input = tk.StringVar() # Input for members
        
        # Config - Pool Management
        self.pm_pool_mode = tk.StringVar(value="Existing") # Existing, New
        self.pm_pool_name = tk.StringVar() # Typed or Selected
        self.pm_node_mode = tk.StringVar(value="Existing") # Existing, New
        self.pm_node_input = tk.StringVar() 
        self.pm_node_port = tk.StringVar(value="80")

        # Config - Delete Node
        self.del_node_name = tk.StringVar()

        # State
        self.session_changes = [] 
        self.active_device_cache = None
        self.cached_nodes = [] # Cache for dropdowns
        self.cached_pools = []
        
        # Logging Queue
        self.log_queue = queue.Queue()
        self.root.after(100, self.check_log_queue)

        # --- UI Build ---
        self.create_widgets()
        
    def create_widgets(self):
        # 1. Top Panel
        self.create_top_panel()
        
        # 2. Main Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(side=tk.TOP, padx=10, pady=5, expand=True, fill=tk.BOTH)
        
        self.tab_connect = tk.Frame(self.notebook)
        self.tab_finder = tk.Frame(self.notebook)
        self.tab_config = tk.Frame(self.notebook)
        self.tab_sync = tk.Frame(self.notebook)
        
        self.notebook.add(self.tab_connect, text="Connectivity Check")
        self.notebook.add(self.tab_finder, text="Finder & Search")
        self.notebook.add(self.tab_config, text="Configuration")
        self.notebook.add(self.tab_sync, text="Sync & Operations")
        
        self.build_connectivity_tab()
        self.build_finder_tab()
        self.build_config_tab()
        self.build_sync_tab()
        
        # 3. Log Area
        self.log_frame = tk.LabelFrame(self.root, text="Logs & Output", padx=5, pady=5)
        self.log_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=False, padx=10, pady=10)
        
        btn_frame = tk.Frame(self.log_frame)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Button(btn_frame, text="Clear Logs", command=self.clear_logs).pack(side=tk.RIGHT)
        
        self.log_area = scrolledtext.ScrolledText(self.log_frame, state='disabled', height=12)
        self.log_area.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.log_area.tag_config("PASS", foreground="green")
        self.log_area.tag_config("FAIL", foreground="red")
        self.log_area.tag_config("INFO", foreground="blue")
        self.log_area.tag_config("CMD", foreground="purple")

    def create_top_panel(self):
        frame = tk.LabelFrame(self.root, text="Connection Details", padx=10, pady=10)
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Inventory
        tk.Label(frame, text="Inventory File:").grid(row=0, column=0, sticky="w")
        tk.Entry(frame, textvariable=self.inventory_path, width=40).grid(row=0, column=1, padx=5)
        tk.Button(frame, text="Browse", command=self.browse_file).grid(row=0, column=2, padx=5)
        
        # Auth
        tk.Label(frame, text="Username:").grid(row=0, column=3, sticky="w", padx=(20, 5))
        tk.Entry(frame, textvariable=self.username, width=20).grid(row=0, column=4, padx=5)
        tk.Label(frame, text="Password:").grid(row=0, column=5, sticky="w", padx=(20, 5))
        tk.Entry(frame, textvariable=self.password, show="*", width=20).grid(row=0, column=6, padx=5)

    def create_scrollable_frame(self, parent):
        canvas = tk.Canvas(parent, borderwidth=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        return scrollable_frame

    def build_config_tab(self):
        # Scrollable Main Area
        main_frame = self.create_scrollable_frame(self.tab_config)
        
        tk.Label(main_frame, text="Note: All configurations are applied to the ACTIVE device.", fg="red", font=("Arial", 10, "bold")).pack(anchor="w", pady=10, padx=10)
        
        # --- 1. VS CREATION ---
        vs_frame = tk.LabelFrame(main_frame, text="1. Create Virtual Server & Pool", padx=10, pady=10, bg="#f1f8e9")
        vs_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # VS Details
        g1 = tk.Frame(vs_frame, bg="#f1f8e9")
        g1.pack(fill=tk.X, pady=5)
        tk.Label(g1, text="VS Name (e.g. Web_App):", bg="#f1f8e9").grid(row=0, column=0, sticky="w")
        tk.Entry(g1, textvariable=self.vs_name_input, width=25).grid(row=0, column=1, padx=5)
        
        tk.Label(g1, text="VS IP:", bg="#f1f8e9").grid(row=0, column=2, sticky="w")
        tk.Entry(g1, textvariable=self.vs_ip_input, width=15).grid(row=0, column=3, padx=5)
        
        tk.Label(g1, text="Ports (e.g. 80, 443):", bg="#f1f8e9").grid(row=0, column=4, sticky="w")
        tk.Entry(g1, textvariable=self.vs_ports_input, width=15).grid(row=0, column=5, padx=5)
        
        # Monitor
        tk.Label(g1, text="Monitor:", bg="#f1f8e9").grid(row=1, column=0, sticky="w", pady=5)
        monitors = ["gateway_icmp", "http", "https", "tcp", "tcp_half_open", "icmp"]
        ttk.Combobox(g1, textvariable=self.monitor_var, values=monitors).grid(row=1, column=1, padx=5)
        
        # Pool Members for this VS
        p_frame = tk.LabelFrame(vs_frame, text="Pool Members", bg="#f1f8e9", padx=5, pady=5)
        p_frame.pack(fill=tk.X, pady=10)
        
        tk.Radiobutton(p_frame, text="Empty Pool (No Nodes)", variable=self.vs_node_mode, value="No Nodes", bg="#f1f8e9").pack(anchor="w")
        tk.Radiobutton(p_frame, text="Add Nodes (Comma separated IPs/Names)", variable=self.vs_node_mode, value="Add Nodes", bg="#f1f8e9").pack(anchor="w")
        
        tk.Entry(p_frame, textvariable=self.vs_nodes_input, width=60).pack(fill=tk.X, padx=20, pady=5)
        tk.Label(p_frame, text="Format: '192.168.1.50' or 'NodeName' (If new, IP required in Name field? No, just IP for auto-creation)", bg="#f1f8e9", fg="#666").pack(anchor="w", padx=20)
        
        tk.Button(vs_frame, text="GENERATE & CREATE VS", command=self.run_create_vs, bg="#009688", fg="white", font=("Arial", 10, "bold"), height=2).pack(fill=tk.X, pady=10)

        # --- 2. POOL MANAGEMENT ---
        pm_frame = tk.LabelFrame(main_frame, text="2. Pool Management (Add Nodes to Pool)", padx=10, pady=10, bg="#fff3e0")
        pm_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Select Pool
        r1 = tk.Frame(pm_frame, bg="#fff3e0")
        r1.pack(fill=tk.X)
        tk.Label(r1, text="Target Pool:", bg="#fff3e0", font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        
        tk.Radiobutton(r1, text="Use Existing:", variable=self.pm_pool_mode, value="Existing", bg="#fff3e0").pack(side=tk.LEFT, padx=10)
        self.combo_pools = ttk.Combobox(r1, textvariable=self.pm_pool_name, width=20)
        self.combo_pools.pack(side=tk.LEFT, padx=5)
        tk.Button(r1, text="↻ Load Pools", command=self.refresh_cache, bg="#e0e0e0").pack(side=tk.LEFT)
        
        tk.Radiobutton(r1, text="Create New:", variable=self.pm_pool_mode, value="New", bg="#fff3e0").pack(side=tk.LEFT, padx=20)
        
        # Select Nodes
        r2 = tk.Frame(pm_frame, bg="#fff3e0", pady=10)
        r2.pack(fill=tk.X)
        tk.Label(r2, text="Node Source:", bg="#fff3e0", font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        
        tk.Radiobutton(r2, text="Select Existing Node:", variable=self.pm_node_mode, value="Existing", bg="#fff3e0").pack(side=tk.LEFT, padx=10)
        self.combo_nodes = ttk.Combobox(r2, textvariable=self.pm_node_input, width=20) # We'll put name/ip here
        self.combo_nodes.pack(side=tk.LEFT, padx=5)
        
        tk.Radiobutton(r2, text="Create New (IP):", variable=self.pm_node_mode, value="New", bg="#fff3e0").pack(side=tk.LEFT, padx=20)
        
        tk.Label(r2, text="Port:", bg="#fff3e0").pack(side=tk.LEFT, padx=(20, 5))
        tk.Entry(r2, textvariable=self.pm_node_port, width=6).pack(side=tk.LEFT)
        
        tk.Button(pm_frame, text="ADD NODE TO POOL", command=self.run_add_to_pool, bg="#ff9800", fg="white", height=2).pack(fill=tk.X, pady=10)
        
        # --- 3. NODE DELETE ---
        del_frame = tk.LabelFrame(main_frame, text="3. Delete Node", padx=10, pady=10)
        del_frame.pack(fill=tk.X, padx=10, pady=10)
        tk.Label(del_frame, text="Node Name:").pack(side=tk.LEFT)
        tk.Entry(del_frame, textvariable=self.del_node_name).pack(side=tk.LEFT, padx=5)
        tk.Button(del_frame, text="Delete Node", command=self.run_delete_node_gui, bg="#f44336", fg="white").pack(side=tk.LEFT, padx=10)
    
    def build_connectivity_tab(self):
        frame = tk.Frame(self.tab_connect, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(frame, text="Check SSH connectivity, Cluster Status, and Sync Status.", fg="#555").pack(anchor="w", pady=(0, 20))
        tk.Button(frame, text="RUN COMPLETE HEALTH CHECK", command=self.run_health_check, bg="#4caf50", fg="white", height=2, font=("Arial", 11, "bold")).pack(fill=tk.X)

    def build_finder_tab(self):
        frame = tk.Frame(self.tab_finder, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Search
        search = tk.LabelFrame(frame, text="Search Objects", padx=10, pady=10)
        search.pack(fill=tk.X)
        
        tk.Label(search, text="Type:").grid(row=0, column=0)
        types = ["Virtual Server", "Pool", "Node", "IP Address Usage", "Connection Table"]
        ttk.Combobox(search, textvariable=self.search_type_var, values=types, state="readonly").grid(row=0, column=1, padx=5)
        
        tk.Label(search, text="Query:").grid(row=0, column=2)
        tk.Entry(search, textvariable=self.search_query, width=30).grid(row=0, column=3, padx=5)
        
        tk.Button(search, text="SEARCH", command=self.run_finder, bg="#2196f3", fg="white").grid(row=0, column=4, padx=20)
        
        # IP Scan
        ip_frame = tk.LabelFrame(frame, text="IP Availability Scanner", padx=10, pady=10, bg="#e3f2fd")
        ip_frame.pack(fill=tk.X, pady=20)
        tk.Label(ip_frame, text="IP Segment (e.g. 192.168.10.):", bg="#e3f2fd").grid(row=0, column=0)
        tk.Entry(ip_frame, textvariable=self.ip_segment_var).grid(row=0, column=1, padx=5)
        tk.Button(ip_frame, text="Scan (Ping + Config)", command=self.run_ip_scan, bg="#ff9800", fg="white").grid(row=0, column=2, padx=20)

    def build_sync_tab(self):
        frame = tk.Frame(self.tab_sync, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # History
        history_frame = tk.LabelFrame(frame, text="Session Changes (Applied to Active)", padx=10, pady=10)
        history_frame.pack(fill=tk.BOTH, expand=True)
        
        self.history_list = tk.Listbox(history_frame, height=10)
        self.history_list.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        scrollbar = tk.Scrollbar(history_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_list.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.history_list.yview)

        # Sync Actions
        action_frame = tk.LabelFrame(frame, text="Cluster Operations", padx=10, pady=10, bg="#fff3e0")
        action_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(action_frame, text="1. Save Config (sys config)", command=self.run_save_config, bg="#795548", fg="white").pack(side=tk.LEFT, padx=10)
        tk.Button(action_frame, text="2. Create Backup (UCS)", command=self.run_backup, bg="#607d8b", fg="white").pack(side=tk.LEFT, padx=10)
        
        ttk.Separator(action_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=20)
        
        tk.Button(action_frame, text="SYNC TO PEER (Active -> Standby)", command=self.run_sync, bg="#d32f2f", fg="white", font=("Arial", 10, "bold"), height=2).pack(side=tk.RIGHT, padx=10)


    # --- HELPERS ---
    def log(self, message, tag=None):
        self.log_queue.put({"type": "log", "message": message, "tag": tag})
        
    def check_log_queue(self):
        try:
            while True:
                item = self.log_queue.get_nowait()
                if item['type'] == 'log':
                    self.log_area.config(state='normal')
                    self.log_area.insert(tk.END, str(item['message']) + "\n", item.get('tag'))
                    self.log_area.see(tk.END)
                    self.log_area.config(state='disabled')
                elif item['type'] == 'msgbox':
                     messagebox.showinfo(item['title'], item['message'])
        except queue.Empty: pass
        finally: self.root.after(100, self.check_log_queue)

    def clear_logs(self):
        self.log_area.config(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state='disabled')

    def browse_file(self):
        f = filedialog.askopenfilename()
        if f: self.inventory_path.set(f)

    # --- INVENTORY & CACHE ---
    def get_devices(self):
        devices = []
        current_group = "Default"
        try:
            with open(self.inventory_path.get(), 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'): continue
                    
                    if line.startswith('[') and line.endswith(']'):
                        current_group = line[1:-1]
                        continue
                        
                    parts = re.split(r'[,\s]+', line)
                    if len(parts) >= 2:
                        devices.append({
                            'host': parts[0],
                            'device_type': parts[1], # 'f5_tmsh' usually
                            'port': parts[2] if len(parts)>2 else DEFAULT_F5_PORT,
                            'group': current_group
                        })
            return devices
        except Exception as e:
            self.log(f"Inventory Error: {e}", "FAIL")
            return []

    def connect_device(self, device):
        return ConnectHandler(
            device_type=device['device_type'],
            host=device['host'],
            username=self.username.get(),
            password=self.password.get(),
            port=device['port']
        )

    def refresh_cache(self):
        # Fetches Pools and Nodes from Active Device to populate Dropdowns
        threading.Thread(target=self._refresh_cache_thread, daemon=True).start()

    def _refresh_cache_thread(self):
        active = self.get_active_blocking()
        if not active: return
        
        try:
            self.log("Refreshing Cache from Active Device...", "INFO")
            nc = self.connect_device(active)
            
            # Pools
            out_p = nc.send_command("tmsh list ltm pool recursive one-line")
            self.cached_pools = self._extract_names(out_p, "ltm pool")
            
            # Nodes
            out_n = nc.send_command("tmsh list ltm node recursive one-line")
            self.cached_nodes = self._extract_names(out_n, "ltm node")
            
            nc.disconnect()
            
            # Update UI
            self.root.after(0, self._update_dropdowns)
            self.log(f"Cache Updated: {len(self.cached_pools)} Pools, {len(self.cached_nodes)} Nodes", "PASS")
        except Exception as e:
            self.log(f"Cache Refresh Failed: {e}", "FAIL")

    def _extract_names(self, output, type_prefix):
        names = []
        for line in output.splitlines():
             # "ltm pool /Common/MyPool {"
             if line.strip().startswith(type_prefix):
                 parts = line.strip().split()
                 if len(parts) >= 3:
                     names.append(parts[2])
        return sorted(names)

    def _update_dropdowns(self):
        self.combo_pools['values'] = self.cached_pools
        self.combo_nodes['values'] = self.cached_nodes

    # --- ACTIVE DEVICE DETECTION ---
    def get_active_blocking(self):
        if self.active_device_cache: return self.active_device_cache
        devices = self.get_devices()
        for dev in devices:
            try:
                nc = self.connect_device(dev)
                out = nc.send_command("tmsh show sys failover")
                nc.disconnect()
                if "active" in out.lower():
                    self.active_device_cache = dev
                    return dev
            except Exception as e:
                self.log(f"Check {dev['host']} failed: {e}")
        return None

    # --- LOGIC HANDLERS ---
    def run_health_check(self):
        threading.Thread(target=self._health_check_thread, daemon=True).start()

    def _health_check_thread(self):
        devices = self.get_devices()
        self.log("\n--- Health & Cluster Status ---", "INFO")
        for dev in devices:
            try:
                self.log(f"Checking {dev['host']}...", "INFO")
                subprocess.run(['ping', '-n', '1', dev['host']], stdout=subprocess.DEVNULL)
                nc = self.connect_device(dev)
                failover = nc.send_command("tmsh show sys failover")
                sync = nc.send_command("tmsh show cm sync-status")
                nc.disconnect()
                status = "ACTIVE" if "active" in failover.lower() else "STANDBY"
                tag = "PASS" if status == "ACTIVE" else "INFO"
                self.log(f"  [{status}] {dev['host']}", tag)
                if "In Sync" in sync: self.log("  Sync Status: In Sync", "PASS")
                else: self.log(f"  Sync Status: Not Synced / Pending", "FAIL")
                if status == "ACTIVE": self.active_device_cache = dev
            except Exception as e: self.log(f"  Error {dev['host']}: {e}", "FAIL")

    def run_finder(self):
        q = self.search_query.get()
        t = self.search_type_var.get()
        threading.Thread(target=self._finder_thread, args=(q, t), daemon=True).start()

    def _finder_thread(self, query, stype):
        # 2-step finder logic (List -> Show Status)
        devices = self.get_devices()
        self.log(f"\n--- Finding {stype}: {query} ---")
        cmd_map = {"Virtual Server": "ltm virtual", "Pool": "ltm pool", "Node": "ltm node"}
        
        for dev in devices:
            try:
                nc = self.connect_device(dev)
                if stype in cmd_map:
                    comp = cmd_map[stype]
                    # Simple find for now, advanced parsing can be added
                    out = nc.send_command(f"tmsh list {comp} recursive")
                    for line in out.splitlines():
                        if f"{comp} " in line and query in line and "{" in line:
                             name = line.split()[2]
                             status = nc.send_command(f"tmsh show {comp} {name}")
                             avail = "Available" if "available" in status.lower() else "Offline"
                             self.log(f"  [FOUND] {dev['host']} | {name} | {avail}", "PASS" if avail=="Available" else "FAIL")
                nc.disconnect()
            except Exception as e: self.log(f"Error {dev['host']}: {e}")

    def run_ip_scan(self):
        seg = self.ip_segment_var.get()
        threading.Thread(target=self._ip_scan_thread, args=(seg,), daemon=True).start()

    def _ip_scan_thread(self, segment):
        self.log(f"Scanning {segment}...", "INFO")
        for i in range(1, 20):
            ip = f"{segment}{i}" if segment.endswith('.') else f"{segment}.{i}"
            res = subprocess.run(['ping', '-n', '1', '-w', '200', ip], stdout=subprocess.DEVNULL)
            if res.returncode != 0: self.log(f"  {ip} - No Ping (Potential Free)", "PASS")

    # --- CONFIGURATION HANDLERS ---
    def run_create_vs(self):
        name = self.vs_name_input.get()
        ip = self.vs_ip_input.get()
        ports_str = self.vs_ports_input.get()
        mon = self.monitor_var.get()
        mode = self.vs_node_mode.get()
        nodes_str = self.vs_nodes_input.get()
        
        if not all([name, ip, ports_str]):
            messagebox.showwarning("Input", "Name, IP, and Ports are required.")
            return
            
        ports = [p.strip() for p in ports_str.split(',') if p.strip()]
        node_list = [n.strip() for n in nodes_str.split(',') if n.strip()] if mode == "Add Nodes" else []
        
        cmds = []
        for port in ports:
            vs_final = f"VS_{name}_Port_{port}"
            pool_final = f"POOL_{name}_Port_{port}"
            
            members_cmd = ""
            if node_list:
                m_list = []
                for n in node_list:
                     if re.match(r'^\d+\.\d+\.\d+\.\d+$', n):
                         node_name = f"Node_{n}"
                         cmds.append(f"tmsh create ltm node {node_name} address {n}")
                         m_list.append(f"{node_name}:{port}")
                     else:
                         m_list.append(f"{n}:{port}")
                members_cmd = "members add { " + " ".join(m_list) + " }"
            
            cmds.append(f"tmsh create ltm pool {pool_final} monitor {mon} {members_cmd}")
            cmds.append(f"tmsh create ltm virtual {vs_final} destination {ip}:{port} pool {pool_final} profiles add {{ tcp }}")

        self.confirm_and_execute(cmds, f"Create VS {name} ({len(ports)} ports)")

    def run_add_to_pool(self):
        pool_mode = self.pm_pool_mode.get()
        node_mode = self.pm_node_mode.get()
        pool_val = self.pm_pool_name.get().strip()
        node_val = self.pm_node_input.get().strip()
        port = self.pm_node_port.get().strip()
        
        if not pool_val or not node_val: return
        
        cmds = []
        final_node_name = node_val
        if node_mode == "New":
            if re.match(r'^\d+\.\d+\.\d+\.\d+$', node_val):
                final_node_name = f"Node_{node_val}"
                cmds.append(f"tmsh create ltm node {final_node_name} address {node_val}")
        
        if pool_mode == "New":
            cmds.append(f"tmsh create ltm pool {pool_val} monitor gateway_icmp members add {{ {final_node_name}:{port} }}")
        else:
            cmds.append(f"tmsh modify ltm pool {pool_val} members add {{ {final_node_name}:{port} }}")
            
        self.confirm_and_execute(cmds, f"Add Node to Pool {pool_val}")

    def run_delete_node_gui(self):
        n = self.del_node_name.get()
        if n: self.confirm_and_execute([f"tmsh delete ltm node {n}"], f"Delete Node {n}")

    def confirm_and_execute(self, cmds, action_desc):
        msg = f"Action: {action_desc}\n\nCommands:\n" + "\n".join(cmds)
        if not messagebox.askyesno("Confirm Active Config", msg): return
        threading.Thread(target=self._exec_active_thread, args=(cmds, action_desc), daemon=True).start()

    def _exec_active_thread(self, cmds, desc):
        self.log(f"\n--- Executing: {desc} ---", "CMD")
        active = self.get_active_blocking()
        if not active:
            self.log("  [ABORT] No Active Device Found!", "FAIL")
            return
        
        try:
            nc = self.connect_device(active)
            failed = False
            for cmd in cmds:
                self.log(f"    Running: {cmd}")
                out = nc.send_command(cmd)
                if "error" in out.lower() or "syntax" in out.lower():
                    self.log(f"    [ERROR] {out}", "FAIL")
                    failed = True
                    break
                else: self.log("    [OK]", "PASS")
            nc.disconnect()
            
            if not failed:
                ts = datetime.now().strftime("%H:%M:%S")
                record = f"[{ts}] {active['host']}: {desc}"
                self.session_changes.append(record)
                self.root.after(0, self.history_list.insert, tk.END, record)
        except Exception as e: self.log(f"  Execution Error: {e}", "FAIL")

    # --- SYNC HANDLERS ---
    def run_save_config(self):
        self.confirm_and_execute(["tmsh save sys config"], "Save Config")

    def run_backup(self):
        name = f"backup_{datetime.now().strftime('%Y%m%d')}"
        self.confirm_and_execute([f"tmsh save sys ucs {name}"], "Create Backup UCS")

    def run_sync(self):
        if not self.session_changes:
             if not messagebox.askyesno("Confirm", "No changes recorded. Sync anyway?"): return
        else:
             if not messagebox.askyesno("Confirm Sync", f"Sync changes?\n\nRecorded Changes:\n{len(self.session_changes)} items"): return
        threading.Thread(target=self._sync_thread, daemon=True).start()

    def _sync_thread(self):
        self.log("\n--- Starting Sync (Active -> Peer) ---", "CMD")
        active = self.get_active_blocking()
        if not active: return
        try:
            nc = self.connect_device(active)
            out = nc.send_command("tmsh list cm device-group one-line") 
            group_name = "device-group-failover" # Default
            if "device-group" in out:
                 # heuristic to find sync-failover group
                 pass
            
            self.log(f"  Syncing Group: {group_name}")
            res = nc.send_command(f"tmsh run cm config-sync to-group {group_name}")
            self.log(f"  Result: {res}")
            
            time.sleep(2)
            check = nc.send_command("tmsh show cm sync-status")
            if "In Sync" in check: self.log("  [SUCCESS] Config Copied to Peer.", "PASS")
            else: self.log("  [WARNING] Sync Status not green yet.", "FAIL")
            nc.disconnect()
        except Exception as e: self.log(f"Sync Error: {e}", "FAIL")

if __name__ == "__main__":
    root = tk.Tk()
    app = F5ManagerApp(root)
    root.mainloop()

# CRITICAL: Install telnetlib compatibility for Python 3.13+
import sys
try:
    import telnetlib
except ImportError:
    import telnetlib_compat  # noqa: F401

import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
import re
import threading
import os
import csv
import webbrowser
from datetime import datetime
import queue

import modules.adapters

def _get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
class VlanCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Network Device VLAN Checker (Enhanced)")
        self.root.geometry("900x700")

        # --- Variables ---
        self.inventory_path = tk.StringVar(value="inventory.txt")
        self.username = tk.StringVar()
        self.password = tk.StringVar()
        self.enable_password = tk.StringVar()
        self.mac_input = tk.StringVar()
        self.vlan_dry_run_var = tk.BooleanVar(value=False)
        self.vlan_save_config_var = tk.BooleanVar(value=True)
        
        # Filtering & Target Variables
        self.target_mode_var = tk.StringVar(value="Bulk (All/Group/Filter)")
        self.target_single_var = tk.StringVar()
        
        self.filter_group_var = tk.StringVar(value="All")
        self.filter_text_var = tk.StringVar()
        self.available_groups = ["All"]
        self.available_hosts = []
        self.device_stats_var = tk.StringVar(value="Loaded: 0")

        self.parsed_results = []
        
        # Logging Queue and File Logging
        self.log_queue = queue.Queue()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.session_log_file = f"app_session_log_{timestamp}.txt"
        
        # Write initial header to session log
        with open(self.session_log_file, "a") as f:
            f.write(f"--- Session Log Started: {timestamp} ---\n\n")

        self.root.after(100, self.check_log_queue)
        
        # --- UI Components ---
        self.create_widgets()

    def create_widgets(self):
        # 1. Common Inputs (Inventory, Auth)
        self.create_common_inputs()
        
        # 1.5 Filter Controls
        self.create_filter_controls()
        
        # 2. Tabs
        # 3. Common Log Area (Pack at BOTTOM first so it stays visible)
        self.log_frame = tk.Frame(self.root)
        self.log_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=False, padx=10, pady=10)
        
        tk.Button(self.log_frame, text="Clear Logs", command=self.clear_logs).pack(side=tk.BOTTOM, pady=5)
        
        self.log_area = scrolledtext.ScrolledText(self.log_frame, state='disabled', height=12)
        self.log_area.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # 2. Tabs (Pack remaining space)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(side=tk.TOP, padx=10, pady=5, expand=True, fill=tk.BOTH)
        
        self.vlan_frame = tk.Frame(self.notebook)
        self.mac_frame = tk.Frame(self.notebook)
        self.vlan_mgmt_frame = tk.Frame(self.notebook)
        self.compare_frame = tk.Frame(self.notebook)
        
        self.notebook.add(self.vlan_frame, text="VLAN Checker")
        self.notebook.add(self.mac_frame, text="MAC Checker")
        self.notebook.add(self.vlan_mgmt_frame, text="VLAN Management")
        self.notebook.add(self.compare_frame, text="VLAN Compare")
        
        self.interfaces_frame = tk.Frame(self.notebook)
        self.notebook.add(self.interfaces_frame, text="Interfaces")
        
        self.tools_frame = tk.Frame(self.notebook)
        self.notebook.add(self.tools_frame, text="Network Tools")
        
        self.create_vlan_tab()
        self.create_mac_tab()
        self.create_vlan_mgmt_tab()
        self.create_compare_tab()
        self.create_interfaces_tab()
        self.create_tools_tab()
        
        # Bind Tab Change to handle state freezing (e.g. VLAN Compare)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def create_common_inputs(self):
        input_frame = tk.Frame(self.root, padx=10, pady=10)
        input_frame.pack(fill=tk.X)
        
        # Inventory
        tk.Label(input_frame, text="Inventory File (.txt):").grid(row=0, column=0, sticky="w")
        tk.Entry(input_frame, textvariable=self.inventory_path, width=40).grid(row=0, column=1, padx=5)
        tk.Button(input_frame, text="Browse & Load", command=self.browse_file).grid(row=0, column=2)

        # Credentials
        tk.Label(input_frame, text="Username:").grid(row=1, column=0, sticky="w", pady=5)
        tk.Entry(input_frame, textvariable=self.username, width=30).grid(row=1, column=1, padx=5, sticky="w")
        
        tk.Label(input_frame, text="Password:").grid(row=2, column=0, sticky="w")
        tk.Entry(input_frame, textvariable=self.password, show="*", width=30).grid(row=2, column=1, padx=5, sticky="w")
        
        tk.Label(input_frame, text="Enable Password (IOS):").grid(row=3, column=0, sticky="w", pady=5)
        tk.Entry(input_frame, textvariable=self.enable_password, show="*", width=30).grid(row=3, column=1, padx=5, sticky="w")
        
    def create_filter_controls(self):
        f_frame = tk.LabelFrame(self.root, text="Inventory Filter", padx=10, pady=5)
        f_frame.pack(fill=tk.X, padx=10, pady=5)
        # Target Mode (Bulk vs Single)
        mode_frame = tk.Frame(f_frame)
        mode_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))
        
        tk.Label(mode_frame, text="Execute On:").pack(side=tk.LEFT)
        self.mode_combo = ttk.Combobox(mode_frame, textvariable=self.target_mode_var, values=["Bulk (All/Group/Filter)", "Single Device"], state="readonly", width=25)
        self.mode_combo.pack(side=tk.LEFT, padx=5)
        self.mode_combo.bind("<<ComboboxSelected>>", self.on_target_mode_change)
        
        # Single Device Dropdown (Hidden initially, shown conditionally)
        self.single_host_lbl = tk.Label(mode_frame, text="Device:")
        self.single_host_combo = ttk.Combobox(mode_frame, textvariable=self.target_single_var, state="readonly", width=25)
        
        filter_subframe = tk.Frame(f_frame)
        filter_subframe.pack(side=tk.TOP, fill=tk.X)
        
        # Group Filter
        tk.Label(filter_subframe, text="Group:").pack(side=tk.LEFT)
        self.group_combo = ttk.Combobox(filter_subframe, textvariable=self.filter_group_var, values=self.available_groups, state="readonly", width=20)
        self.group_combo.pack(side=tk.LEFT, padx=5)
        self.group_combo.bind("<<ComboboxSelected>>", self.update_stats)
        
        # Text Filter
        tk.Label(filter_subframe, text="Search (IP/Name):").pack(side=tk.LEFT, padx=(10,0))
        entry = tk.Entry(filter_subframe, textvariable=self.filter_text_var, width=20)
        entry.pack(side=tk.LEFT, padx=5)
        entry.bind("<KeyRelease>", self.update_stats)
        
        # Stats
        tk.Label(filter_subframe, textvariable=self.device_stats_var, fg="blue").pack(side=tk.RIGHT)

    def create_vlan_tab(self):
        btn_frame = tk.Frame(self.vlan_frame, padx=10, pady=20)
        btn_frame.pack(fill=tk.X)
        
        tk.Button(btn_frame, text="1. Test Connectivity & Auth", command=self.run_connectivity_check, bg="#dddddd", height=2).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        tk.Button(btn_frame, text="2. Check VLANs", command=self.run_vlan_check, bg="#aaddaa", height=2).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

    def create_mac_tab(self):
        frame = tk.Frame(self.mac_frame, padx=10, pady=20)
        frame.pack(fill=tk.X)
        
        tk.Label(frame, text="MAC Address to Find:").pack(anchor="w")
        tk.Entry(frame, textvariable=self.mac_input, width=40).pack(pady=5, fill=tk.X)
        tk.Label(frame, text="(Formats: aabb.ccdd.eeff, aa:bb:cc:dd:ee:ff, aabbccddeeff; partial OK — ambiguous matches flagged)").pack(anchor="w", pady=(0, 10))
        
        tk.Button(frame, text="Search MAC in Network", command=self.run_mac_check, bg="#add8e6", height=2).pack(fill=tk.X)

    def create_vlan_mgmt_tab(self):
        # Main container with scrollbar
        container = tk.Frame(self.vlan_mgmt_frame)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # === ADD VLAN Section ===
        add_frame = tk.LabelFrame(container, text="Add VLAN", padx=10, pady=10, bg="#e8f5e9")
        add_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(add_frame, text="VLAN ID:", bg="#e8f5e9").grid(row=0, column=0, sticky="w", pady=5)
        self.add_vlan_id = tk.Entry(add_frame, width=15)
        self.add_vlan_id.grid(row=0, column=1, sticky="w", padx=5)
        
        tk.Label(add_frame, text="VLAN Name:", bg="#e8f5e9").grid(row=1, column=0, sticky="w", pady=5)
        self.add_vlan_name = tk.Entry(add_frame, width=30)
        self.add_vlan_name.grid(row=1, column=1, sticky="w", padx=5)
        
        tk.Button(add_frame, text="Add VLAN to Selected Devices", command=self.run_add_vlan, 
                 bg="#4caf50", fg="white", height=2).grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)
        
        # === RENAME VLAN Section ===
        rename_frame = tk.LabelFrame(container, text="Rename VLAN", padx=10, pady=10, bg="#fff3e0")
        rename_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(rename_frame, text="VLAN ID:", bg="#fff3e0").grid(row=0, column=0, sticky="w", pady=5)
        self.rename_vlan_id = tk.Entry(rename_frame, width=15)
        self.rename_vlan_id.grid(row=0, column=1, sticky="w", padx=5)
        
        tk.Label(rename_frame, text="New Name:", bg="#fff3e0").grid(row=1, column=0, sticky="w", pady=5)
        self.rename_vlan_name = tk.Entry(rename_frame, width=30)
        self.rename_vlan_name.grid(row=1, column=1, sticky="w", padx=5)
        
        tk.Button(rename_frame, text="Rename VLAN", command=self.run_rename_vlan,
                 bg="#ff9800", fg="white", height=2).grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)
        
        # === DELETE VLAN Section ===
        delete_frame = tk.LabelFrame(container, text="Delete VLAN", padx=10, pady=10, bg="#ffebee")
        delete_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(delete_frame, text="VLAN ID:", bg="#ffebee").grid(row=0, column=0, sticky="w", pady=5)
        self.delete_vlan_id = tk.Entry(delete_frame, width=15)
        self.delete_vlan_id.grid(row=0, column=1, sticky="w", padx=5)
        
        tk.Button(delete_frame, text="Delete VLAN", command=self.run_delete_vlan,
                 bg="#f44336", fg="white", height=2).grid(row=1, column=0, columnspan=2, sticky="ew", pady=10)

        dryrun_frame = tk.LabelFrame(container, text="Execution Mode", padx=10, pady=8, bg="#f5f5f5")
        dryrun_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Checkbutton(
            dryrun_frame,
            text="Dry-Run (preview commands only, no device changes)",
            variable=self.vlan_dry_run_var,
            bg="#f5f5f5"
        ).pack(anchor="w")
        tk.Checkbutton(
            dryrun_frame,
            text="Save to startup-config after change (same as web default)",
            variable=self.vlan_save_config_var,
            bg="#f5f5f5"
        ).pack(anchor="w")

        quick_save_frame = tk.LabelFrame(container, text="Config Persistence (Quick Access)", padx=10, pady=8, bg="#ede7f6")
        quick_save_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Button(
            quick_save_frame,
            text="Save Device Config (Single/Bulk/Group)",
            command=self.run_save_config,
            bg="#7e57c2",
            fg="white",
            height=2
        ).pack(fill=tk.X)

    def create_interfaces_tab(self):
        container = tk.Frame(self.interfaces_frame, padx=10, pady=10)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Filter options for the show commands
        filter_frame = tk.LabelFrame(container, text="Output Filter", padx=10, pady=5)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.int_filter_var = tk.StringVar(value="None")
        tk.Label(filter_frame, text="Preset:").grid(row=0, column=0, sticky="w", padx=5)
        ttk.Combobox(filter_frame, textvariable=self.int_filter_var, values=["None", "connected", "notconnect", "disabled", "err-disabled", "Custom"], state="readonly", width=15).grid(row=0, column=1, padx=5)
        
        self.int_custom_filter = tk.StringVar()
        tk.Label(filter_frame, text="Custom (| include):").grid(row=0, column=2, sticky="w", padx=(15, 5))
        tk.Entry(filter_frame, textvariable=self.int_custom_filter, width=20).grid(row=0, column=3, padx=5)
        
        # Action Buttons
        btn_frame = tk.Frame(container)
        btn_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(btn_frame, text="Show Interfaces Status", command=self.run_show_int_status, bg="#4fc3f7", height=2).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Button(btn_frame, text="Show Interfaces Description", command=self.run_show_int_desc, bg="#81c784", height=2).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("CSV Files", "*.csv"), ("All Files", "*.*")])
        if filename:
            self.inventory_path.set(filename)
            self.refresh_inventory()

    def refresh_inventory(self):
        """Reloads inventory and populates groups."""
        devices = self.get_devices() # This parses groups now
        groups = set()
        for d in devices:
            groups.add(d.get('group', 'Default'))
        
        sorted_groups = ["All"] + sorted(list(groups))
        self.available_groups = sorted_groups
        self.group_combo['values'] = self.available_groups
        self.group_combo.current(0)
        self.update_stats()

    def on_tab_changed(self, event=None):
        """Handle logic constraints when tabs change."""
        current_tab_id = self.notebook.select()
        if not current_tab_id:
            return
            
        tab_text = self.notebook.tab(current_tab_id, "text")
        
        if tab_text == "VLAN Compare":
            # Force Bulk Mode
            self.target_mode_var.set("Bulk (All/Group/Filter)")
            self.on_target_mode_change()
            # Disable dropdown to prevent changing it while on this tab
            self.mode_combo.config(state="disabled")
        else:
            # Re-enable if we leave the tab
            self.mode_combo.config(state="readonly")

    def validate_and_start_thread(self, target, args):
        pass # placeholder for potential future generic wrapper

    def create_tools_tab(self):
        container = tk.Frame(self.tools_frame, padx=10, pady=10)
        container.pack(fill=tk.BOTH, expand=True)
        
        # 1. Config Backup / Show Run
        config_frame = tk.LabelFrame(container, text="Bulk Config Backup (Show Run)", padx=10, pady=10, bg="#e3f2fd")
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.config_filter_var = tk.StringVar(value="None")
        tk.Label(config_frame, text="Filter:", bg="#e3f2fd").grid(row=0, column=0, sticky="w", padx=5)
        ttk.Combobox(config_frame, textvariable=self.config_filter_var, values=["None", "section interface", "section router", "begin bgp", "Custom"], state="readonly", width=15).grid(row=0, column=1, padx=5)
        self.config_custom_var = tk.StringVar()
        tk.Label(config_frame, text="Custom (|):", bg="#e3f2fd").grid(row=0, column=2, sticky="w", padx=(15, 5))
        tk.Entry(config_frame, textvariable=self.config_custom_var, width=20).grid(row=0, column=3, padx=5)
        
        tk.Button(config_frame, text="Execute Config Backup", command=self.run_config_backup, bg="#2196f3", fg="white", height=2).grid(row=1, column=0, columnspan=4, sticky="ew", pady=(10, 0))

        save_frame = tk.LabelFrame(container, text="Persist Device Config", padx=10, pady=10, bg="#ede7f6")
        save_frame.pack(fill=tk.X, pady=(0, 10))
        save_lbl = tk.Label(
            save_frame,
            text="Writes current running/candidate config to persistent storage using the selected target scope.",
            justify=tk.LEFT,
            bg="#ede7f6"
        )
        save_lbl.pack(anchor="w", pady=(0, 10))
        tk.Button(
            save_frame,
            text="Save Device Config (Single/Bulk/Group)",
            command=self.run_save_config,
            bg="#7e57c2",
            fg="white",
            height=2
        ).pack(fill=tk.X)

        # 2. Topology Mapper
        topo_frame = tk.LabelFrame(container, text="Automated Topology Mapper (CDP/LLDP)", padx=10, pady=10, bg="#e8f5e9")
        topo_frame.pack(fill=tk.X, pady=(0, 10))
        
        info_lbl = tk.Label(topo_frame, text="Aggregates CDP/LLDP neighbors from targeted devices and generates a visual Mermaid.js HTML diagram.", justify=tk.LEFT, bg="#e8f5e9")
        info_lbl.pack(anchor="w", pady=(0, 10))
        tk.Button(topo_frame, text="Generate Interactive Topology Map", command=self.run_topology_mapper, bg="#4caf50", fg="white", height=2).pack(fill=tk.X)

        # 3. Network Inventory Audit
        audit_frame = tk.LabelFrame(container, text="Network Inventory Audit (OS/Serial)", padx=10, pady=10, bg="#fff3e0")
        audit_frame.pack(fill=tk.X, pady=(0, 10))
        
        audit_lbl = tk.Label(audit_frame, text="Runs 'show version' across network devices to extract Hostname, OS Version, Serial Number, Uptime, and Hardware Model into a sorted CSV.", justify=tk.LEFT, bg="#fff3e0")
        audit_lbl.pack(anchor="w", pady=(0, 10))
        tk.Button(audit_frame, text="Execute Inventory Audit (Export CSV)", command=self.run_network_audit, bg="#ff9800", fg="white", height=2).pack(fill=tk.X)

        desc_frame = tk.LabelFrame(container, text="Description Search (web parity)", padx=10, pady=10, bg="#fce4ec")
        desc_frame.pack(fill=tk.X, pady=(0, 10))
        self.desc_search_var = tk.StringVar()
        tk.Label(desc_frame, text="Search term (substring or regex):", bg="#fce4ec").pack(anchor="w")
        tk.Entry(desc_frame, textvariable=self.desc_search_var, width=50).pack(fill=tk.X, pady=5)
        tk.Label(
            desc_frame,
            text="Results ranked by relevance (exact > prefix > partial). HTML report opens when complete.",
            justify=tk.LEFT, bg="#fce4ec", fg="#555",
        ).pack(anchor="w", pady=(0, 8))
        tk.Button(
            desc_frame, text="Search Interface Descriptions",
            command=self.run_description_search, bg="#e91e63", fg="white", height=2,
        ).pack(fill=tk.X)

    def run_description_search(self):
        term = self.desc_search_var.get().strip()
        if not term:
            messagebox.showwarning("Input Error", "Enter a description search term.")
            return
        devices = self.get_targeted_devices()
        if not devices:
            messagebox.showwarning("Warning", "No devices selected.")
            return
        threading.Thread(
            target=self._desc_search_thread,
            args=(term, devices, self.username.get(), self.password.get(), self.enable_password.get()),
            daemon=True,
        ).start()

    def _desc_search_thread(self, term, devices, username, password, enable_pwd):
        self.log(f"\n--- Description Search: '{term}' ---")
        try:
            modules.adapters.run_description_search(
                devices, username, password, enable_pwd, term, self.log,
            )
            self.log("--- Description Search Complete ---")
        except Exception as exc:
            self.log(f"[ERROR] Description search failed: {exc}")

    def _offer_open_report(self, path):
        if path and os.path.isfile(path):
            if messagebox.askyesno("Report Ready", f"Open HTML report in browser?\n\n{path}"):
                webbrowser.open(path if path.startswith('file:') else f"file:///{path.replace(chr(92), '/')}")

    def on_target_mode_change(self, event=None):
        if self.target_mode_var.get() == "Single Device":
            self.single_host_lbl.pack(side=tk.LEFT, padx=(10, 0))
            self.single_host_combo.pack(side=tk.LEFT, padx=5)
        else:
            self.single_host_lbl.pack_forget()
            self.single_host_combo.pack_forget()
        self.update_stats()

    def update_stats(self, event=None):
        filtered = self.get_filtered_devices()
        
        # Update single dropdown valid options
        hosts = [d['host'] for d in filtered]
        self.single_host_combo['values'] = hosts
        
        if hosts and self.target_single_var.get() not in hosts:
            self.target_single_var.set(hosts[0])
        elif not hosts:
            self.target_single_var.set("")
            
        targeted = self.get_targeted_devices()
        total = len(self.get_devices())
        mode = self.target_mode_var.get()
        c = len(targeted)
        self.device_stats_var.set(f"Selected: {c} ({'Single' if 'Single' in mode else 'Bulk'}) / Total: {total}")

    def get_targeted_devices(self):
        """Returns either all filtered devices or just the single selected device based on Target Mode."""
        filtered = self.get_filtered_devices()
        
        if self.target_mode_var.get() == "Single Device":
            target_host = self.target_single_var.get()
            return [d for d in filtered if d['host'] == target_host]
        return filtered

    def log(self, message):
        """Thread-safe logging via Queue."""
        self.log_queue.put({"type": "log", "message": message})
        
    def show_info_safe(self, title, message):
        """Thread-safe info messagebox."""
        self.log_queue.put({"type": "msgbox", "title": title, "message": message, "icon": "info"})
        
    def show_warning_safe(self, title, message):
        """Thread-safe warning messagebox."""
        self.log_queue.put({"type": "msgbox", "title": title, "message": message, "icon": "warning"})
        
    def show_error_safe(self, title, message):
        """Thread-safe error messagebox."""
        self.log_queue.put({"type": "msgbox", "title": title, "message": message, "icon": "error"})

    def check_log_queue(self):
        """Polls the log queue and updates the GUI."""
        try:
            while True:
                item = self.log_queue.get_nowait()
                
                # Handle dictionary items (structured messages)
                if isinstance(item, dict):
                    msg_type = item.get("type")
                    if msg_type == "log":
                        self._append_to_log(item.get("message", ""))
                    elif msg_type == "msgbox":
                        title = item.get("title", "Info")
                        message = item.get("message", "")
                        icon = item.get("icon", "info")
                        if icon == "warning":
                            messagebox.showwarning(title, message)
                        elif icon == "error":
                            messagebox.showerror(title, message)
                        else:
                            messagebox.showinfo(title, message)
                    elif msg_type == "askyesno":
                        # This is tricky because askyesno is blocking and returns a value.
                        # We generally shouldn't trigger this from a thread if we need the answer back in the thread.
                        # For now, confirmation dialogs are already in the main thread (run_* methods), 
                        # so we don't need to handle them here.
                        pass
                # Handle plain strings (legacy compatibility)
                elif isinstance(item, str):
                    self._append_to_log(item)
                    
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.check_log_queue)

    def _append_to_log(self, message):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')
        
        # Also write to session log file for permanent record
        try:
            with open(self.session_log_file, "a", encoding='utf-8') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] {message}\n")
        except Exception:
            pass # Failsafe against write errors blocking GUI

    def clear_logs(self):
        self.log_area.config(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state='disabled')

    def get_devices(self):
        from modules.network_base import get_devices_from_file
        return get_devices_from_file(self.inventory_path.get())

    def get_filtered_devices(self):
        all_devices = self.get_devices()
        group_filter = self.filter_group_var.get()
        text_filter = self.filter_text_var.get().strip().lower()
        
        filtered = []
        for d in all_devices:
            # 1. Group Check
            if group_filter != "All" and d.get('group') != group_filter:
                continue
            
            # 2. Text Check
            if text_filter:
                # Search in host or group
                if (text_filter not in d['host'].lower()) and (text_filter not in d.get('group', '').lower()):
                    continue
            
            filtered.append(d)
        return filtered

    def create_compare_tab(self):
        container = tk.Frame(self.compare_frame, padx=10, pady=20)
        container.pack(fill=tk.BOTH, expand=True)

        info_lbl = tk.Label(container, text="Compare VLANs across devices.\nA combined baseline will be created from ALL VLANs found across all devices.\nThe report will show missing VLANs on each device relative to this global list.", justify=tk.LEFT, bg="#f0f0f0", padx=10, pady=10, relief=tk.RIDGE)
        info_lbl.pack(fill=tk.X, pady=(0, 20))

        tk.Button(container, text="Run VLAN Compare Analysis", command=self.run_vlan_compare, bg="#9c27b0", fg="white", height=2).pack(fill=tk.X)



    # --- Actions ---
    def run_connectivity_check(self):
        # Gather data in Main Thread
        devices = self.get_targeted_devices()
        username = self.username.get()
        password = self.password.get()
        enable_pwd = self.enable_password.get()
        dry_run = self.vlan_dry_run_var.get()
        
        if not devices:
            messagebox.showwarning("Warning", "No devices selected (check filters).")
            return
            
        threading.Thread(target=self._connectivity_check_thread, args=(devices, username, password, enable_pwd), daemon=True).start()

    def _connectivity_check_thread(self, devices, username, password, enable_pwd):
        modules.adapters.run_connectivity(devices, username, password, enable_pwd, self.log)

    def run_vlan_check(self):
        devices = self.get_targeted_devices()
        username = self.username.get()
        password = self.password.get()
        enable_pwd = self.enable_password.get()
        
        if not devices:
            messagebox.showwarning("Warning", "No devices selected.")
            return

        threading.Thread(target=self._vlan_check_thread, args=(devices, username, password, enable_pwd), daemon=True).start()

    def _vlan_check_thread(self, devices, username, password, enable_pwd=""):
        modules.adapters.run_vlan_audit(devices, username, password, enable_pwd, self.log)

    # --- MAC Checker Logic ---
    def run_mac_check(self):
        target_mac = self.mac_input.get().strip()
        if not target_mac:
            messagebox.showwarning("Input Error", "Please enter a MAC address.")
            return
        
        norm_mac = self.normalize_mac(target_mac)
        if not norm_mac:
             messagebox.showwarning("Input Error", "Invalid MAC address format.")
             return
             
        self.log(f"Searching for MAC: {target_mac} (normalized: {norm_mac})")
        
        devices = self.get_targeted_devices()
        username = self.username.get()
        password = self.password.get()
        enable_pwd = self.enable_password.get()
        
        threading.Thread(target=self._mac_check_thread, args=(norm_mac, devices, username, password, enable_pwd), daemon=True).start()

    def normalize_mac(self, mac):
        # Remove common separators
        clean = re.sub(r'[.:\-\s]', '', mac).lower()
        # Relaxed check: allow any alphanumeric (for partial/non-hex search like "ddrr")
        if not re.match(r'^[0-9a-z]+$', clean):
            return None
        return clean

    def _mac_check_thread(self, target_mac_clean, devices, username, password, enable_pwd):
        result = modules.adapters.run_mac_trace(
            devices, username, password, enable_pwd, target_mac_clean, self.log,
        )
        if isinstance(result, dict):
            amb = result.get('ambiguous_devices') or []
            if amb:
                summary = "\n\n".join(a.get('message', '') for a in amb[:3])
                self.root.after(0, lambda: messagebox.showwarning(
                    "Ambiguous Partial MAC",
                    "Your partial MAC matched multiple distinct addresses.\n\n"
                    f"{summary}\n\n"
                    "Refine to a full MAC (aa:bb:cc:dd:ee:ff) for a unique result.",
                ))
            html = result.get('html_path')
            if html:
                self.root.after(0, lambda p=html: self._offer_open_report(p))

    # --- VLAN Management Operations ---
    def _gui_validate_vlan(self, action, devices, vid, vname, username, password, enable_pwd):
        from utils.vlan_validate import validate_vlan_operation
        amap = {'add': 'add_vlan', 'rename': 'rename_vlan', 'delete': 'delete_vlan'}
        if self.vlan_dry_run_var.get():
            return True
        result = validate_vlan_operation(
            amap[action], devices, username, password, enable_pwd, vid, vname or '', self.log,
        )
        if result.get('overall_status') != 'passed':
            self.log("[ERROR] VLAN validation failed — fix issues before live execution.")
            messagebox.showerror(
                "VLAN Validation Failed",
                "Validation pipeline failed. Review the log console for details.",
            )
            return False
        self.log("[OK] VLAN validation passed (same pipeline as web UI).")
        return True

    def run_add_vlan(self):
        vlan_id = self.add_vlan_id.get().strip()
        vlan_name = self.add_vlan_name.get().strip()
        
        if not vlan_id or not vlan_name:
            messagebox.showwarning("Input Error", "Please enter both VLAN ID and Name.")
            return
        
        if not vlan_id.isdigit():
            messagebox.showwarning("Input Error", "VLAN ID must be a number.")
            return
            
        devices = self.get_targeted_devices()
        username = self.username.get()
        password = self.password.get()
        enable_pwd = self.enable_password.get()
        
        if not devices:
            messagebox.showwarning("Warning", "No devices selected.")
            return

        dry_run = self.vlan_dry_run_var.get()
        if not self._gui_validate_vlan('add', devices, vlan_id, vlan_name, username, password, enable_pwd):
            return

        threading.Thread(target=self._add_vlan_thread, args=(vlan_id, vlan_name, devices, username, password, enable_pwd, dry_run), daemon=True).start()
    
    def _add_vlan_thread(self, vlan_id, vlan_name, devices, username, password, enable_pwd, dry_run):
        modules.adapters.run_vlan_management(
            'add', devices, username, password, enable_pwd, vlan_id, vlan_name, self.log,
            dry_run=dry_run, save_config=self.vlan_save_config_var.get(),
        )
    
    def run_rename_vlan(self):
        vlan_id = self.rename_vlan_id.get().strip()
        new_name = self.rename_vlan_name.get().strip()
        
        if not vlan_id or not new_name:
            messagebox.showwarning("Input Error", "Please enter both VLAN ID and New Name.")
            return
        
        if not vlan_id.isdigit():
            messagebox.showwarning("Input Error", "VLAN ID must be a number.")
            return
        
        # Confirmation dialog
        devices = self.get_targeted_devices()
        device_list = "\n".join([f"  - {d['host']}" for d in devices])
        
        confirm = messagebox.askyesno(
            "Confirm Rename",
            f"Are you sure you want to rename VLAN {vlan_id} to '{new_name}' on the following devices?\n\n{device_list}"
        )
        
        if confirm:
            username = self.username.get()
            password = self.password.get()
            enable_pwd = self.enable_password.get()
            dry_run = self.vlan_dry_run_var.get()
            if not self._gui_validate_vlan('rename', devices, vlan_id, new_name, username, password, enable_pwd):
                return
            threading.Thread(target=self._rename_vlan_thread, args=(vlan_id, new_name, devices, username, password, enable_pwd, dry_run), daemon=True).start()
    
    def _rename_vlan_thread(self, vlan_id, new_name, devices, username, password, enable_pwd, dry_run):
        modules.adapters.run_vlan_management(
            'rename', devices, username, password, enable_pwd, vlan_id, new_name, self.log,
            dry_run=dry_run, save_config=self.vlan_save_config_var.get(),
        )
    
    def run_delete_vlan(self):
        vlan_id = self.delete_vlan_id.get().strip()
        
        if not vlan_id:
            messagebox.showwarning("Input Error", "Please enter VLAN ID.")
            return
        
        if not vlan_id.isdigit():
            messagebox.showwarning("Input Error", "VLAN ID must be a number.")
            return
        
        # Confirmation dialog
        devices = self.get_targeted_devices()
        device_list = "\n".join([f"  - {d['host']}" for d in devices])
        
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"⚠️ WARNING: You are about to DELETE VLAN {vlan_id} from the following devices:\n\n{device_list}\n\nThis action cannot be undone. Continue?",
            icon='warning'
        )
        
        if confirm:
            username = self.username.get()
            password = self.password.get()
            enable_pwd = self.enable_password.get()
            dry_run = self.vlan_dry_run_var.get()
            if not self._gui_validate_vlan('delete', devices, vlan_id, '', username, password, enable_pwd):
                return
            threading.Thread(target=self._delete_vlan_thread, args=(vlan_id, devices, username, password, enable_pwd, dry_run), daemon=True).start()
    
    def _delete_vlan_thread(self, vlan_id, devices, username, password, enable_pwd, dry_run):
        modules.adapters.run_vlan_management(
            'delete', devices, username, password, enable_pwd, vlan_id, None, self.log,
            dry_run=dry_run, save_config=self.vlan_save_config_var.get(),
        )
    
    # Helper methods for VLAN operations

    # --- VLAN Compare Logic ---
    def run_vlan_compare(self):
        devices = self.get_targeted_devices()
        username = self.username.get()
        password = self.password.get()
        enable_pwd = self.enable_password.get()
        
        if not devices:
            messagebox.showwarning("Warning", "No devices selected.")
            return

        threading.Thread(target=self._vlan_compare_thread, args=(devices, username, password, enable_pwd), daemon=True).start()

    def _vlan_compare_thread(self, devices, username, password, enable_pwd):
        modules.adapters.run_vlan_compare(devices, username, password, enable_pwd, self.log)

    # --- Interfaces Logic ---
    def _build_int_filter(self):
        preset = self.int_filter_var.get()
        custom = self.int_custom_filter.get().strip()
        
        if preset == "Custom" and custom:
            return custom
        elif preset != "None" and preset != "Custom":
            return preset
        return ""

    def run_show_int_status(self):
        self._run_interfaces_command("status")
        
    def run_show_int_desc(self):
        self._run_interfaces_command("description")
        
    def _run_interfaces_command(self, cmd_type):
        devices = self.get_targeted_devices()
        username = self.username.get()
        password = self.password.get()
        enable_pwd = self.enable_password.get()
        filt = self._build_int_filter()
        
        if not devices:
            messagebox.showwarning("Warning", "No devices selected.")
            return

        threading.Thread(target=self._interfaces_check_thread, args=(devices, username, password, enable_pwd, cmd_type, filt), daemon=True).start()

    def _interfaces_check_thread(self, devices, username, password, enable_pwd, cmd_type, filt):
        modules.adapters.run_interfaces(devices, username, password, enable_pwd, filt, self.log)


    # --- Network Swiss Tool Logic ---
    def run_config_backup(self):
        devices = self.get_targeted_devices()
        username = self.username.get()
        password = self.password.get()
        enable_pwd = self.enable_password.get()
        
        preset = self.config_filter_var.get()
        custom = self.config_custom_var.get().strip()
        
        filt = custom if preset == "Custom" and custom else (preset if preset != "None" and preset != "Custom" else "")
        
        if not devices:
            messagebox.showwarning("Warning", "No devices selected.")
            return

        threading.Thread(target=self._config_backup_thread, args=(devices, username, password, enable_pwd, filt), daemon=True).start()

    def _config_backup_thread(self, devices, username, password, enable_pwd, filt):
        modules.adapters.run_config_backup(devices, username, password, enable_pwd, filt, self.log)

    def run_save_config(self):
        devices = self.get_targeted_devices()
        username = self.username.get()
        password = self.password.get()
        enable_pwd = self.enable_password.get()

        if not devices:
            messagebox.showwarning("Warning", "No devices selected.")
            return

        threading.Thread(
            target=self._save_config_thread,
            args=(devices, username, password, enable_pwd),
            daemon=True
        ).start()

    def _save_config_thread(self, devices, username, password, enable_pwd):
        modules.adapters.run_save_config(devices, username, password, enable_pwd, self.log)
        
    def run_topology_mapper(self):
        devices = self.get_targeted_devices()
        username = self.username.get()
        password = self.password.get()
        enable_pwd = self.enable_password.get()
        
        if not devices:
            messagebox.showwarning("Warning", "No devices selected.")
            return

        threading.Thread(target=self._topology_mapper_thread, args=(devices, username, password, enable_pwd), daemon=True).start()

    def _topology_mapper_thread(self, devices, username, password, enable_pwd):
        modules.adapters.run_topology_mapper(devices, username, password, enable_pwd, self.log)
        
    def run_network_audit(self):
        devices = self.get_targeted_devices()
        username = self.username.get()
        password = self.password.get()
        enable_pwd = self.enable_password.get()
        
        if not devices:
            messagebox.showwarning("Warning", "No devices selected.")
            return

        threading.Thread(target=self._network_audit_thread, args=(devices, username, password, enable_pwd), daemon=True).start()

    def _network_audit_thread(self, devices, username, password, enable_pwd):
        modules.adapters.run_network_audit(devices, username, password, enable_pwd, self.log)

def run_gui():
    root = tk.Tk()
    app = VlanCheckerApp(root)
    root.mainloop()

if __name__ == "__main__":
    run_gui()

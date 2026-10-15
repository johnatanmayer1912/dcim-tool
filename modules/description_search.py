"""
modules/description_search.py
-------------------------------
Regex and substring search across interface descriptions (physical + port-channel).
Supports NXOS, IOS, and JUNOS with comprehensive diagnostic logging and command fallback.
Searches both interface names and descriptions with full output for partial matches.
Implements robust command fallback mechanism with error detection for all OS types.
"""
import re
import os
from datetime import datetime
from .network_base import connect_device, build_json, resolve_hostname_from_prompt


def _norm_int(name):
    return (name.replace("Ethernet", "Eth").replace("GigabitEthernet", "Gi")
            .replace("FastEthernet", "Fa").replace("TenGigabitEthernet", "Te")
            .replace("Port-channel", "Po").replace("port-channel", "Po").strip())


def _parse_descriptions(desc_out, dtype, log_func=None):
    """Return list of {interface, description, status, source} with flexible parsing for NXOS/IOS/JUNOS."""
    results = []
    
    if not desc_out or desc_out.strip() == "":
        if log_func:
            log_func("[DEBUG] Empty command output received")
        return results
    
    # Skip header lines - more comprehensive list
    header_keywords = [
        '--', 'Interface', 'Status', 'Description', 'Admin', 'Port', 'Vlan', 'Name',
        'Protocol', 'Duplex', 'Speed', 'Type', 'IP Address', 'HWaddr', 'VLAN',
        'Interface', 'Admin', 'Oper', 'Description', 'Port', 'Mode', 'Encapsulation',
        'interface', 'status', 'description', 'admin', 'oper'
    ]
    
    # Determine parsing strategy based on device type
    dtype_lower = dtype.lower() if dtype else ""
    
    for line in desc_out.splitlines():
        line = line.strip()
        if not line:
            continue
        
        # Skip headers - only skip if line is primarily header keywords
        line_lower = line.lower()
        header_count = sum(1 for hk in header_keywords if hk.lower() in line_lower)
        # If line is mostly header keywords (more than 50% of words), skip it
        words = line.split()
        if words and header_count > len(words) / 2:
            continue
        
        # Skip separator lines
        if re.match(r'^[-=+\s]+$', line):
            continue
        
        # Skip lines that are too short to be interface data
        if len(line.split()) < 2:
            continue
        
        # Strategy 1: IOS format (Interface Status Protocol Description)
        # Example: "Fa0/0 up up Central LAN" or "Se0/0/0.100 up up Link to B1"
        # Matches: interface, status, protocol, optional description
        m = re.match(r'^(\S+)\s+(\S+)\s+(\S+)(?:\s+(.*))?$', line)
        if m and dtype_lower and "ios" in dtype_lower:
            iface = _norm_int(m.group(1))
            status = m.group(2)
            desc = (m.group(4) or "").strip()
            results.append({
                "interface": iface,
                "description": desc,
                "status": status,
                "source": "show interfaces description",
            })
            continue
        
        # Strategy 2: NXOS format (Interface Status Speed Description)
        # Example: "Ethernet1/1 connected auto Description here"
        # Matches: interface, status, speed, optional description
        m = re.match(r'^(\S+)\s+(\S+)\s+(\S+)(?:\s+(.*))?$', line)
        if m and dtype_lower and "nxos" in dtype_lower:
            iface = _norm_int(m.group(1))
            status = m.group(2)
            desc = (m.group(4) or "").strip()
            results.append({
                "interface": iface,
                "description": desc,
                "status": status,
                "source": "show interfaces description",
            })
            continue
        
        # Strategy 3: JUNOS format (Interface Admin Link Description)
        # Example: "ge-0/0/0 up up Description here"
        # Matches: interface, admin, link, optional description
        m = re.match(r'^(\S+)\s+(\S+)\s+(\S+)(?:\s+(.*))?$', line)
        if m and dtype_lower and ("junos" in dtype_lower or "juniper" in dtype_lower):
            iface = _norm_int(m.group(1))
            status = m.group(2)
            desc = (m.group(4) or "").strip()
            results.append({
                "interface": iface,
                "description": desc,
                "status": status,
                "source": "show interfaces description",
            })
            continue
        
        # Strategy 4: Generic flexible fallback for any OS type
        # Match interface pattern followed by optional status and description
        # Supports: Ethernet1/1, Gi1/0/1, Fa0/0, ge-0/0/0, lo0, etc.
        interface_pattern = r'^([a-zA-Z]+\d+/\d+/\d+|[a-zA-Z]+\d+/\d+|[a-zA-Z]+\d+\.?\d*|[a-zA-Z]+\d+)\s*(.*)$'
        m = re.match(interface_pattern, line)
        if m:
            iface = _norm_int(m.group(1))
            rest = m.group(2).strip()
            
            # Try to extract status from rest (first word is usually status)
            status_parts = rest.split()
            status = status_parts[0] if status_parts else "unknown"
            desc = " ".join(status_parts[1:]) if len(status_parts) > 1 else ""
            
            # Only add if it looks like a valid interface (has status-like word)
            valid_status = ['up', 'down', 'connected', 'disconnected', 'admin', 'administratively', 
                          'notconnect', 'not-connected', 'disabled', 'err-disabled', 'unknown']
            if any(vs in status.lower() for vs in valid_status):
                results.append({
                    "interface": iface,
                    "description": desc,
                    "status": status,
                    "source": "show interfaces description (fallback)",
                })
            continue
    
    return results


def _is_command_error(output):
    """Check if command output indicates an error (invalid command, unrecognized, etc.)."""
    if not output or output.strip() == "":
        return True
    
    error_patterns = [
        r'Invalid command',
        r'Unrecognized command',
        r'Error:',
        r'syntax error',
        r'% Invalid',
        r'% Unrecognized',
        r'% Unknown',
        r'^\s*\^',
        r'incomplete command',
        r'Ambiguous command'
    ]
    
    output_lower = output.lower()
    for pattern in error_patterns:
        if re.search(pattern, output, re.IGNORECASE):
            return True
    
    # Check if output is too short to be valid interface data
    if len(output.strip()) < 50:
        return True
    
    # Check if output contains only error-like content
    lines = output.strip().splitlines()
    if len(lines) < 3:
        return True
    
    return False


def _has_interface_data(output):
    """Check if output contains interface-like patterns."""
    interface_patterns = [
        r'[a-zA-Z]+\d+/\d+/\d+',  # Ethernet1/1/1
        r'[a-zA-Z]+\d+/\d+',       # Ethernet1/1
        r'[a-zA-Z]+\d+\.\d+',      # Ethernet1.1
        r'[a-zA-Z]+\d+',           # Ethernet1
        r'ge-\d+/\d+/\d+',         # Juniper format
        r'xe-\d+/\d+/\d+',         # Juniper format
        r'et-\d+/\d+/\d+',         # Juniper format
    ]
    
    for pattern in interface_patterns:
        if re.search(pattern, output):
            return True
    
    return False


def _try_command_with_fallback(conn, command_list, log_func=None, diagnostic_log=None):
    """
    Try commands in priority order until one succeeds.
    Returns (output, successful_command, attempts_log)
    """
    attempts_log = []
    
    for i, cmd in enumerate(command_list):
        attempt_info = {
            "attempt": i + 1,
            "command": cmd,
            "success": False,
            "error": None
        }
        
        try:
            if log_func:
                log_func(f"Attempting command {i+1}/{len(command_list)}: {cmd}")
            
            if diagnostic_log:
                diagnostic_log.append(f"[INFO] Attempting command {i+1}/{len(command_list)}: {cmd}")
            
            output = conn.send_command(cmd)
            
            # Check if command succeeded
            if _is_command_error(output):
                error_msg = "Command returned error or invalid output"
                attempt_info["error"] = error_msg
                attempt_info["output_sample"] = output[:200] if output else ""
                
                if diagnostic_log:
                    diagnostic_log.append(f"[WARNING] Command failed: {cmd}")
                    diagnostic_log.append(f"[DEBUG] Error reason: {error_msg}")
                    diagnostic_log.append(f"[DEBUG] Output sample: {output[:200]}")
                
                attempts_log.append(attempt_info)
                continue
            
            # Check if output contains interface data
            if not _has_interface_data(output):
                error_msg = "Command succeeded but no interface data found"
                attempt_info["error"] = error_msg
                attempt_info["output_sample"] = output[:200] if output else ""
                
                if diagnostic_log:
                    diagnostic_log.append(f"[WARNING] Command succeeded but no interface data: {cmd}")
                    diagnostic_log.append(f"[DEBUG] Output sample: {output[:200]}")
                
                attempts_log.append(attempt_info)
                continue
            
            # Command succeeded
            attempt_info["success"] = True
            attempt_info["output_length"] = len(output)
            attempts_log.append(attempt_info)
            
            if diagnostic_log:
                diagnostic_log.append(f"[SUCCESS] Command succeeded: {cmd}")
                diagnostic_log.append(f"[DEBUG] Output length: {len(output)} characters")
            
            return output, cmd, attempts_log
            
        except Exception as e:
            error_msg = str(e)
            attempt_info["error"] = error_msg
            
            if diagnostic_log:
                diagnostic_log.append(f"[ERROR] Exception executing command: {cmd}")
                diagnostic_log.append(f"[DEBUG] Exception: {error_msg}")
            
            attempts_log.append(attempt_info)
            continue
    
    # All commands failed
    return None, None, attempts_log


def _parse_port_channel_descriptions(pc_out, log_func=None):
    """Extract Po descriptions from NX-OS port-channel summary when present with enhanced parsing."""
    entries = []
    current_po = None
    
    if not pc_out or pc_out.strip() == "":
        if log_func:
            log_func("[DEBUG] Empty port-channel output received")
        return entries
    
    for line in pc_out.splitlines():
        line = line.strip()
        if not line:
            continue
        
        # Skip headers
        if any(hk.lower() in line.lower() for hk in ['Port', 'Channel', 'Interface', 'Status', 'port', 'channel']):
            continue
        
        # Match port-channel interface
        m = re.match(r'(Po\d+|port-channel\d+|Port-channel\d+)', line, re.IGNORECASE)
        if m:
            current_po = _norm_int(m.group(1))
            continue
        
        # Extract description for current port-channel
        if current_po and 'description' in line.lower():
            dm = re.search(r'description\s*[:=]?\s*(.+)', line, re.IGNORECASE)
            if dm:
                entries.append({
                    "interface": current_po,
                    "description": dm.group(1).strip(),
                    "status": "",
                    "source": "show port-channel summary",
                })
    
    return entries


def run(device, user, pwd, enb_pwd, search_term, log_func=None, diag_dir=None):
    """Search interface descriptions on one device (case-insensitive substring) with comprehensive diagnostics."""
    host = device.get('host', 'unknown')
    dtype = (device.get('device_type') or '').lower()
    conn = None
    needle = (search_term or "").strip()
    
    if not needle:
        return build_json(host, "fail", {}, "Search term is empty")

    if not diag_dir:
        from utils.output_paths import CAT_DESCRIPTION_SEARCH, prepare_run_output, slugify
        _paths = prepare_run_output(CAT_DESCRIPTION_SEARCH, slugify(f'{host}_{needle}'))
        diag_dir = _paths['run_dir']
    os.makedirs(diag_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    diag_file = os.path.join(diag_dir, f'{host}_diagnostic.txt')
    
    diagnostic_log = []
    diagnostic_log.append(f"=== Interface Search Diagnostic Report ===")
    diagnostic_log.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    diagnostic_log.append(f"Device: {host}")
    diagnostic_log.append(f"Device Type: {dtype}")
    diagnostic_log.append(f"Search Term: {needle}")
    diagnostic_log.append("=" * 50)
    
    try:
        if log_func:
            log_func(f"[{host}] Connecting for description search...")
        diagnostic_log.append(f"[INFO] Connecting to device...")
        
        conn = connect_device(device, user, pwd, enb_pwd)
        true_host = resolve_hostname_from_prompt(conn, host)
        diagnostic_log.append(f"[INFO] Connected successfully. True hostname: {true_host}")

        # Determine command priority lists based on device type
        if "juniper" in dtype or "junos" in dtype:
            desc_cmd_list = [
                "show interfaces descriptions",  # Primary - correct for JUNOS
                "show interfaces description",   # Fallback - without 's'
                "show interfaces terse"           # Last resort - parse for descriptions
            ]
            pc_cmd_list = None
            diagnostic_log.append(f"[INFO] Device type: JUNOS - command priority list: {desc_cmd_list}")
        elif "nxos" in dtype:
            desc_cmd_list = [
                "show interface description",    # Primary - CORRECT for NXOS (singular)
                "show interfaces description",   # Fallback - for older NXOS versions
                "show interface brief"           # Last resort - parse for descriptions
            ]
            pc_cmd_list = [
                "show port-channel summary",
                "show interface port-channel brief"
            ]
            diagnostic_log.append(f"[INFO] Device type: NXOS - description command priority list: {desc_cmd_list}")
            diagnostic_log.append(f"[INFO] Device type: NXOS - port-channel command priority list: {pc_cmd_list}")
        else:
            desc_cmd_list = [
                "show interfaces description",   # Primary - correct for IOS
                "show interface description",    # Fallback - for older IOS versions
                "show interface brief"           # Last resort - parse for descriptions
            ]
            pc_cmd_list = None
            diagnostic_log.append(f"[INFO] Device type: IOS/Other - command priority list: {desc_cmd_list}")

        # Execute commands with fallback
        diagnostic_log.append(f"[INFO] Executing description commands with fallback...")
        desc_out, successful_desc_cmd, desc_attempts = _try_command_with_fallback(
            conn, desc_cmd_list, log_func, diagnostic_log
        )
        
        # Log command attempts
        diagnostic_log.append(f"[INFO] Description command attempts summary:")
        for attempt in desc_attempts:
            status = "SUCCESS" if attempt["success"] else "FAILED"
            diagnostic_log.append(f"  [{status}] Command: {attempt['command']}")
            if attempt["error"]:
                diagnostic_log.append(f"         Error: {attempt['error']}")
        
        if successful_desc_cmd:
            diagnostic_log.append(f"[INFO] Successful description command: {successful_desc_cmd}")
        else:
            diagnostic_log.append(f"[ERROR] All description commands failed!")
        
        pc_out = ""
        successful_pc_cmd = None
        pc_attempts = []
        
        if pc_cmd_list:
            diagnostic_log.append(f"[INFO] Executing port-channel commands with fallback...")
            pc_out, successful_pc_cmd, pc_attempts = _try_command_with_fallback(
                conn, pc_cmd_list, log_func, diagnostic_log
            )
            
            # Log port-channel command attempts
            diagnostic_log.append(f"[INFO] Port-channel command attempts summary:")
            for attempt in pc_attempts:
                status = "SUCCESS" if attempt["success"] else "FAILED"
                diagnostic_log.append(f"  [{status}] Command: {attempt['command']}")
                if attempt["error"]:
                    diagnostic_log.append(f"         Error: {attempt['error']}")
            
            if successful_pc_cmd:
                diagnostic_log.append(f"[INFO] Successful port-channel command: {successful_pc_cmd}")
            else:
                diagnostic_log.append(f"[WARNING] All port-channel commands failed, continuing without port-channel data")

        # Parse with logging
        diagnostic_log.append(f"[INFO] Parsing interface descriptions...")
        
        # Check if we have valid output to parse
        if not desc_out:
            diagnostic_log.append(f"[ERROR] No valid description output received from any command")
            diagnostic_log.append(f"[ERROR] Cannot proceed with search - all commands failed")
            
            # Write diagnostic file even on failure
            with open(diag_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(diagnostic_log))
                f.write("\n\n=== COMMAND ATTEMPTS LOG ===\n")
                for attempt in desc_attempts:
                    f.write(f"Attempt {attempt['attempt']}: {attempt['command']}\n")
                    f.write(f"  Success: {attempt['success']}\n")
                    if attempt['error']:
                        f.write(f"  Error: {attempt['error']}\n")
                    if 'output_sample' in attempt:
                        f.write(f"  Output Sample: {attempt['output_sample']}\n")
                    f.write("\n")
            
            if log_func:
                log_func(f"[{host}] Error: All description commands failed")
                log_func(f"[{host}] Diagnostic log saved to: {diag_file}")
            return build_json(host, "fail", {}, "All description commands failed - check diagnostic log")
        
        all_entries = _parse_descriptions(desc_out, dtype, log_func)
        diagnostic_log.append(f"[DEBUG] Parsed {len(all_entries)} interfaces from description output")
        
        if pc_out:
            pc_entries = _parse_port_channel_descriptions(pc_out, log_func)
            all_entries.extend(pc_entries)
            diagnostic_log.append(f"[DEBUG] Parsed {len(pc_entries)} port-channel entries")

        diagnostic_log.append(f"[INFO] Total interfaces scanned: {len(all_entries)}")
        
        # Log sample of parsed entries
        if all_entries:
            diagnostic_log.append(f"[DEBUG] Sample parsed entries (first 5):")
            for i, entry in enumerate(all_entries[:5]):
                diagnostic_log.append(f"  [{i}] Interface: {entry.get('interface')}, Status: {entry.get('status')}, Desc: {entry.get('description')[:50]}")
        else:
            diagnostic_log.append(f"[WARNING] No interfaces parsed from output")
            diagnostic_log.append(f"[DEBUG] First 10 lines of raw output:")
            for i, line in enumerate(desc_out.splitlines()[:10]):
                diagnostic_log.append(f"  Line {i}: {line}")

        # Search with regex support
        needle_lower = needle.lower()
        matches = []
        search_method = "substring"
        regex_error = None
        
        # Try regex pattern matching first
        try:
            pattern = re.compile(needle, re.IGNORECASE)
            search_method = "regex"
            diagnostic_log.append(f"[INFO] Using regex pattern matching: {needle}")
            
            for ent in all_entries:
                desc = ent.get("description") or ""
                iface = ent.get("interface") or ""
                # Search in both description and interface name using regex
                if pattern.search(desc) or pattern.search(iface):
                    matches.append(ent)
                    
        except re.error as e:
            # Fallback to substring if regex is invalid
            regex_error = str(e)
            search_method = "substring (regex fallback)"
            diagnostic_log.append(f"[INFO] Regex pattern invalid, using substring fallback: {regex_error}")
            
            for ent in all_entries:
                desc = ent.get("description") or ""
                iface = ent.get("interface") or ""
                # Search in both description and interface name (case-insensitive substring)
                if needle_lower in desc.lower() or needle_lower in iface.lower():
                    matches.append(ent)

        diagnostic_log.append(f"[INFO] Search method: {search_method}")
        diagnostic_log.append(f"[INFO] Search matches found: {len(matches)}")

        from utils.search_relevance import description_row_score, sort_description_rows
        for ent in matches:
            ent['match_score'] = description_row_score(needle, ent)
        matches = sort_description_rows(needle, matches)
        diagnostic_log.append(f"[INFO] Matches ranked by relevance (exact > prefix > partial)")

        if matches:
            diagnostic_log.append(f"[DEBUG] Matched interfaces:")
            for i, match in enumerate(matches):
                diagnostic_log.append(f"  [{i}] Interface: {match.get('interface')}")
                diagnostic_log.append(f"      Full Description: {match.get('description')}")
                diagnostic_log.append(f"      Status: {match.get('status')}")
                diagnostic_log.append(f"      Source: {match.get('source')}")

        # Write diagnostic file
        with open(diag_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(diagnostic_log))
            f.write("\n\n=== COMMAND ATTEMPTS LOG ===\n")
            f.write("Description Commands:\n")
            for attempt in desc_attempts:
                f.write(f"  Attempt {attempt['attempt']}: {attempt['command']}\n")
                f.write(f"    Success: {attempt['success']}\n")
                if attempt['error']:
                    f.write(f"    Error: {attempt['error']}\n")
                if 'output_sample' in attempt:
                    f.write(f"    Output Sample: {attempt['output_sample']}\n")
                f.write("\n")
            
            if pc_attempts:
                f.write("Port-Channel Commands:\n")
                for attempt in pc_attempts:
                    f.write(f"  Attempt {attempt['attempt']}: {attempt['command']}\n")
                    f.write(f"    Success: {attempt['success']}\n")
                    if attempt['error']:
                        f.write(f"    Error: {attempt['error']}\n")
                    if 'output_sample' in attempt:
                        f.write(f"    Output Sample: {attempt['output_sample']}\n")
                    f.write("\n")
            
            f.write("\n\n=== RAW COMMAND OUTPUT ===\n")
            f.write(f"Successful Command: {successful_desc_cmd}\n")
            f.write(desc_out)
            if pc_out:
                f.write(f"\n\nSuccessful Port-Channel Command: {successful_pc_cmd}\n")
                f.write(pc_out)

        if log_func:
            log_func(f"[{host}] Diagnostic log saved to: {diag_file}")
            log_func(f"[{host}] Scanned {len(all_entries)} interfaces, found {len(matches)} matches")
            log_func(f"[{host}] Logging out from device...")
        conn.disconnect()
        conn = None
        if log_func:
            log_func(f"[{host}] Successfully logged out")
        return build_json(host, "success", {
            "true_host": true_host,
            "search_term": needle,
            "total_interfaces_scanned": len(all_entries),
            "match_count": len(matches),
            "matches": matches,
            "diagnostic_file": diag_file,
        })
    except Exception as e:
        err = str(e).splitlines()[0] if str(e).splitlines() else str(e)
        diagnostic_log.append(f"[ERROR] Exception occurred: {err}")
        diagnostic_log.append(f"[ERROR] Full traceback: {str(e)}")
        
        # Write diagnostic file even on error
        try:
            with open(diag_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(diagnostic_log))
        except:
            pass
        
        if log_func:
            log_func(f"[{host}] Error: {err}")
            log_func(f"[{host}] Diagnostic log saved to: {diag_file}")
        return build_json(host, "fail", {}, err)
    finally:
        if conn:
            try:
                if log_func:
                    log_func(f"[{host}] Logging out (cleanup)...")
                conn.disconnect()
                if log_func:
                    log_func(f"[{host}] Logged out (cleanup)")
            except Exception:
                pass

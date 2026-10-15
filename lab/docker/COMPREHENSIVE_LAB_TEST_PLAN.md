# Network Swiss Tool Pro - Comprehensive Lab Test Plan (500 Tests)

**Lab Configuration:**
- 1× IOS Device: C9300-24P (Catalyst 9300)
- 2× NX-OS Devices: N9K-C93180YC-EX (Nexus 93180YC-EX), N9K-C9348GC-XP (Nexus 9348GC-XP)
- Port Mapping: 2201 (IOS), 2202 (NX-OS Leaf1), 2203 (NX-OS Leaf2)
- Lab Network: 192.168.100.0/24 management VLAN

**Test Objective:**
Validate every aspect of Network Swiss Tool Pro through physical device testing with expert team review.

---

## Test Categories

### 1. Authentication & Vault (25 Tests)

#### 1.1 Vault Initialization (5 tests)
- [ ] TEST-001: Verify vault initializes on first launch without master password
- [ ] TEST-002: Verify local machine key is created automatically
- [ ] TEST-003: Verify vault can be unlocked with machine key on subsequent launches
- [ ] TEST-004: Verify vault lockout after failed attempts (10 attempts threshold)
- [ ] TEST-005: Verify vault encryption key is stored securely (file permissions check)

#### 1.2 Credential Management (10 tests)
- [ ] TEST-006: Add SSH credential with username/password/enable secret
- [ ] TEST-007: Add credential with become password (Junos)
- [ ] TEST-008: Add SNMP v2c credential with community string
- [ ] TEST-009: Add SNMP v3 credential with auth/priv protocols
- [ ] TEST-010: Edit existing credential password
- [ ] TEST-011: Delete credential from vault
- [ ] TEST-012: Export credentials with password encryption
- [ ] TEST-013: Import credentials from encrypted file
- [ ] TEST-014: Verify credentials are never logged in plaintext
- [ ] TEST-015: Verify credentials are not exposed in API responses

#### 1.3 Session Credentials (5 tests)
- [ ] TEST-016: Use session credentials for one-time execution
- [ ] TEST-017: Verify session credentials are not persisted
- [ ] TEST-018: Verify session credentials override vault credentials temporarily
- [ ] TEST-019: Verify session credentials are cleared after browser refresh
- [ ] TEST-020: Verify session credentials are cleared after job completion

#### 1.4 Credential Fallback (5 tests)
- [ ] TEST-021: Verify fallback to session credentials when vault credential_id is missing
- [ ] TEST-022: Verify fallback to secondary credential when primary fails
- [ ] TEST-023: Verify fallback to third credential when primary/secondary fail
- [ ] TEST-024: Verify job fails when all credentials fail
- [ ] TEST-025: Verify credential_id validation rejects empty/invalid IDs

---

### 2. Inventory Management (40 Tests)

#### 2.1 Inventory File Operations (10 tests)
- [ ] TEST-026: Load inventory.txt file from disk
- [ ] TEST-027: Preview inventory parse with current file
- [ ] TEST-028: Commit inventory (replace mode)
- [ ] TEST-029: Commit inventory (merge mode)
- [ ] TEST-030: Verify inventory.txt backup is created on commit
- [ ] TEST-031: Restore inventory from backup file
- [ ] TEST-032: Import inventory from file dialog
- [ ] TEST-033: Verify DNS hostnames are rejected on preview
- [ ] TEST-034: Verify IPv4 addresses are accepted
- [ ] TEST-035: Verify IPv6 addresses are accepted

#### 2.2 Inventory Validation (10 tests)
- [ ] TEST-036: Verify duplicate IP detection
- [ ] TEST-037: Verify invalid IP format rejection
- [ ] TEST-038: Verify empty line handling
- [ ] TEST-039: Verify comment line handling (# prefix)
- [ ] TEST-040: Verify device_type column parsing
- [ ] TEST-041: Verify group column parsing
- [ ] TEST-042: Verify inventory source chip updates
- [ ] TEST-043: Verify unsaved vs committed indicator
- [ ] TEST-044: Verify inventory scope source selection (committed/unsaved)
- [ ] TEST-045: Verify Run unsaved checkbox behavior

#### 2.3 Inventory UI (10 tests)
- [ ] TEST-046: Verify parsed hosts table renders correctly
- [ ] TEST-047: Verify table columns: Host, Type, Group, Status
- [ ] TEST-048: Verify accept/reject status display
- [ ] TEST-049: Verify horizontal scrollbar on wide tables
- [ ] TEST-050: Verify table row hover effect
- [ ] TEST-051: Verify empty inventory state display
- [ ] TEST-052: Verify inventory text area resize
- [ ] TEST-053: Verify inventory format help text
- [ ] TEST-054: Verify backup file dropdown population
- [ ] TEST-055: Verify backup file timestamp display

#### 2.4 Inventory API (10 tests)
- [ ] TEST-056: GET /api/inventory returns committed inventory
- [ ] TEST-057: POST /api/inventory/preview validates format
- [ ] TEST-058: POST /api/inventory/commit replaces inventory
- [ ] TEST-059: POST /api/inventory/commit merges inventory
- [ ] TEST-060: GET /api/inventory/backups lists backups
- [ ] TEST-061: POST /api/inventory/restore restores backup
- [ ] TEST-062: Verify inventory API rejects DNS hostnames
- [ ] TEST-063: Verify inventory API validates IPv4/IPv6
- [ ] TEST-064: Verify inventory API returns parsing errors
- [ ] TEST-065: Verify inventory API authentication required

---

### 3. Device Connectivity (35 Tests)

#### 3.1 SSH Connection (15 tests)
- [ ] TEST-066: Connect to IOS device with valid credentials
- [ ] TEST-067: Connect to NX-OS device with valid credentials
- [ ] TEST-068: Verify connection timeout (30s default)
- [ ] TEST-069: Verify connection fails with wrong username
- [ ] TEST-070: Verify connection fails with wrong password
- [ ] TEST-071: Verify connection fails with wrong enable secret
- [ ] TEST-072: Verify connection persists for job duration
- [ ] TEST-073: Verify connection closes after job completion
- [ ] TEST-074: Verify connection retry on temporary failure
- [ ] TEST-075: Verify connection failure is logged
- [ ] TEST-076: Verify concurrent connections to multiple devices
- [ ] TEST-077: Verify SSH key authentication (if supported)
- [ ] TEST-078: Verify SSH port customization
- [ ] TEST-079: Verify SSH banner handling
- [ ] TEST-080: Verify SSH cipher negotiation

#### 3.2 SNMP Connection (10 tests)
- [ ] TEST-081: Connect to device with SNMP v2c
- [ ] TEST-082: Connect to device with SNMP v3 (authNoPriv)
- [ ] TEST-083: Connect to device with SNMP v3 (authPriv)
- [ ] TEST-084: Verify SNMP timeout handling
- [ ] TEST-085: Verify SNMP community string validation
- [ ] TEST-086: Verify SNMP v3 auth protocol (MD5/SHA)
- [ ] TEST-087: Verify SNMP v3 priv protocol (DES/AES)
- [ ] TEST-088: Verify SNMP port customization (161 default)
- [ ] TEST-089: Verify SNMP bulk walk optimization
- [ ] TEST-090: Verify SNMP error handling (no response)

#### 3.3 Connection Status (10 tests)
- [ ] TEST-091: Verify connection status indicator in UI
- [ ] TEST-092: Verify connection failure error message
- [ ] TEST-093: Verify connection success confirmation
- [ ] TEST-094: Verify connection timeout notification
- [ ] TEST-095: Verify connection retry UI option
- [ ] TEST-096: Verify connection history in logs
- [ ] TEST-097: Verify concurrent connection limit (5 default)
- [ ] TEST-098: Verify connection pool reuse
- [ ] TEST-099: Verify connection cleanup on session end
- [ ] TEST-100: Verify connection state persistence across tabs

---

### 4. VLAN Operations (50 Tests)

#### 4.1 VLAN Provisioning (15 tests)
- [ ] TEST-101: Add VLAN 10 with name "DATA" on IOS
- [ ] TEST-102: Add VLAN 20 with name "VOICE" on NX-OS
- [ ] TEST-103: Verify VLAN ID validation (1-4094)
- [ ] TEST-104: Verify VLAN name length limit (32 chars)
- [ ] TEST-105: Verify VLAN name special character handling
- [ ] TEST-106: Add VLAN with dry-run mode
- [ ] TEST-107: Verify dry-run shows CLI preview
- [ ] TEST-108: Verify dry-run does not execute
- [ ] TEST-109: Verify VLAN add validation step 1 (dry-run)
- [ ] TEST-110: Verify VLAN add validation step 2 (syntax)
- [ ] TEST-111: Verify VLAN add validation step 3 (platform)
- [ ] TEST-112: Verify VLAN add validation step 4 (conflict)
- [ ] TEST-113: Verify VLAN add validation step 5 (golden-config)
- [ ] TEST-114: Verify VLAN add validation step 6 (approval)
- [ ] TEST-115: Verify VLAN add approval modal

#### 4.2 VLAN Rename (10 tests)
- [ ] TEST-116: Rename VLAN 10 from "DATA" to "DATA-NEW" on IOS
- [ ] TEST-117: Rename VLAN 20 on NX-OS
- [ ] TEST-118: Verify Junos rename limitation (delete + add)
- [ ] TEST-119: Verify rename validation gates
- [ ] TEST-120: Verify rename dry-run preview
- [ ] TEST-121: Verify rename executes only after approval
- [ ] TEST-122: Verify rename error handling
- [ ] TEST-123: Verify rename logs
- [ ] TEST-124: Verify rename evidence artifact
- [ ] TEST-125: Verify rename rollback (if supported)

#### 4.3 VLAN Delete (10 tests)
- [ ] TEST-126: Delete VLAN 10 from IOS
- [ ] TEST-127: Delete VLAN 20 from NX-OS
- [ ] TEST-128: Verify delete confirmation modal
- [ ] TEST-129: Verify delete validation gates
- [ ] TEST-130: Verify delete removes from interfaces
- [ ] TEST-131: Verify delete dry-run preview
- [ ] TEST-132: Verify delete cannot be undone
- [ ] TEST-133: Verify delete error handling
- [ ] TEST-134: Verify delete logs
- [ ] TEST-135: Verify delete evidence artifact

#### 4.4 VLAN Comparison (15 tests)
- [ ] TEST-136: Run VLAN compare against golden CSV
- [ ] TEST-137: Verify missing VLAN detection
- [ ] TEST-138: Verify extra VLAN detection
- [ ] TEST-139: Verify name mismatch detection
- [ ] TEST-140: Verify CSV format validation
- [ ] TEST-141: Verify compare output HTML generation
- [ ] TEST-142: Verify compare output CSV generation
- [ ] TEST-143: Verify compare scope selection
- [ ] TEST-144: Verify compare dry-run (no changes)
- [ ] TEST-145: Verify compare evidence artifact
- [ ] TEST-146: Verify compare error handling
- [ ] TEST-147: Verify compare on single device
- [ ] TEST-148: Verify compare on multiple devices
- [ ] TEST-149: Verify compare with empty golden CSV
- [ ] TEST-150: Verify compare with malformed CSV

---

### 5. Interface Management (45 Tests)

#### 5.1 Interface Discovery (15 tests)
- [ ] TEST-151: Discover interfaces on IOS device
- [ ] TEST-152: Discover interfaces on NX-OS device
- [ ] TEST-153: Verify interface count matches device
- [ ] TEST-154: Verify interface type detection (Gig/Eth/Port-channel)
- [ ] TEST-155: Verify interface status (up/down/admin-down)
- [ ] TEST-156: Verify interface description parsing
- [ ] TEST-157: Verify interface MAC address
- [ ] TEST-158: Verify interface MTU
- [ ] TEST-159: Verify interface speed/duplex
- [ ] TEST-160: Verify interface VLAN assignment
- [ ] TEST-161: Verify interface trunk allowed VLANs
- [ ] TEST-162: Verify interface error count
- [ ] TEST-163: Verify interface discovery timeout
- [ [ ] TEST-164: Verify interface discovery error handling
- [ ] TEST-165: Verify interface discovery logs

#### 5.2 Interface Status Check (10 tests)
- [ ] TEST-166: Check interface status for connected ports
- [ ] TEST-167: Check interface status for notconnected ports
- [ ] TEST-168: Check interface status for down ports
- [ ] TEST-169: Verify status filter functionality
- [ ] TEST-170: Verify description search functionality
- [ ] TEST-171: Verify regex filter support
- [ ] TEST-172: Verify status report HTML generation
- [ ] TEST-173: Verify status report CSV generation
- [ ] TEST-174: Verify status report evidence artifact
- [ ] TEST-175: Verify status report scope selection

#### 5.3 Interface Manager (20 tests)
- [ ] TEST-176: Discover interfaces for single host (Interface Manager)
- [ ] TEST-177: Verify interface map grid display
- [ ] TEST-178: Verify interface card click to open details
- [ ] TEST-179: Verify interface details panel (current config)
- [ ] TEST-180: Verify interface details panel (proposed config)
- [ ] TEST-181: Edit interface configuration in text area
- [ ] TEST-182: Validate interface configuration syntax
- [ ] TEST-183: Verify platform-specific validation (IOS vs NX-OS)
- [ ] TEST-184: Deploy interface configuration (dry-run)
- [ ] TEST-185: Deploy interface configuration (actual)
- [ ] TEST-186: Verify deployment confirmation modal
- [ ] TEST-187: Verify deployment logs
- [ ] TEST-188: Verify deployment evidence artifact
- [ ] TEST-189: Verify interface filter in map
- [ ] TEST-190: Verify interface export
- [ ] TEST-191: Verify interface device type selection
- [ ] TEST-192: Verify interface operation mode (discover/validate/deploy)
- [ ] TEST-193: Verify interface target source (single/committed/unsaved)
- [ ] TEST-194: Verify interface status dashboard
- [ ] TEST-195: Verify interface command output logs

---

### 6. Network Discovery (50 Tests)

#### 6.1 Discovery Configuration (15 tests)
- [ ] TEST-196: Configure seed hosts (IP format)
- [ ] TEST-197: Configure seed hosts (hostname format)
- [ ] TEST-198: Configure seed hosts with device_type
- [ ] TEST-199: Select seed source (explicit/committed/unsaved)
- [ ] TEST-200: Select scan profile (conservative/standard/wide)
- [ ] TEST-201: Configure hop depth (1/2/3)
- [ ] TEST-202: Select protocol (CDP/LLDP/Both)
- [ ] TEST-203: Configure SSH timeout
- [ ] TEST-204: Enable demo mode
- [ ] TEST-205: Verify demo mode does not use SSH
- [ ] TEST-206: Verify discovery scope limits
- [ ] TEST-207: Verify discovery seed validation
- [ ] TEST-208: Verify discovery seed source chip
- [ ] TEST-209: Verify discovery profile description
- [ ] TEST-210: Verify discovery configuration persistence

#### 6.2 Discovery Execution (15 tests)
- [ ] TEST-211: Start discovery run
- [ ] TEST-212: Verify discovery progress bar
- [ ] TEST-213: Verify discovery progress label
- [ ] TEST-214: Stop discovery run mid-execution
- [ ] TEST-215: Verify stop button appears during run
- [ ] TEST-216: Verify discovery completes on all hosts
- [ ] TEST-217: Verify discovery partial results on stop
- [ [ ] TEST-218: Verify discovery logs during run
- [ ] TEST-219: Verify discovery error handling
- [ ] TEST-220: Verify discovery timeout handling
- [ ] TEST-221: Verify discovery credential authentication
- [ ] TEST-222: Verify discovery credential fallback
- [ ] TEST-223: Verify discovery concurrent connections
- [ ] TEST-224: Verify discovery evidence artifact
- [ ] TEST-225: Verify discovery job index entry

#### 6.3 Discovery Results (20 tests)
- [ ] TEST-226: Verify discovered devices table
- [ ] TEST-227: Verify hostname column
- [ ] TEST-228: Verify management IP column
- [ ] TEST-229: Verify OS family column
- [ ] TEST-230: Verify hop column
- [ ] TEST-231: Verify state column (scanned/seed/neighbor_only/failed/timeout)
- [ ] TEST-232: Verify neighbors count column
- [ ] TEST-233: Verify evidence column
- [ ] TEST-234: Filter by hop level
- [ ] TEST-235: Filter by scan state
- [ ] TEST-236: Search by hostname/IP
- [ ] TEST-237: Verify incomplete observations panel
- [ ] TEST-238: Verify incomplete observations summary
- [ ] TEST-239: Open Discovery Command Center
- [ ] TEST-240: Verify Command Center topology map
- [ ] TEST-241: Verify Command Center link inventory
- [ ] TEST-242: Export discovery JSON
- [ ] TEST-243: Copy discovery links CSV
- [ ] TEST-244: Re-run discovery from results
- [ ] TEST-245: Verify discovery results persistence

---

### 7. Topology Maps (60 Tests)

#### 7.1 Standard L2 Map (20 tests)
- [ ] TEST-246: Build Standard L2 Map from inventory
- [ ] TEST-247: Verify map includes all inventory devices
- [ ] TEST-248: Verify CDP edges are rendered
- [ ] TEST-249: Verify LLDP edges are rendered
- [ ] TEST-250: Verify node labels (hostname)
- [ ] TEST-251: Verify edge labels (port/vlan)
- [ ] TEST-252: Click node to open side panel
- [ ] TEST-253: Verify node side panel details
- [ ] TEST-254: Verify node side panel VLAN info
- [ ] TEST-255: Verify node side panel MAC info
- [ ] TEST-256: Verify node side panel port info
- [ ] TEST-257: Verify map background
- [ ] TEST-258: Verify map zoom controls
- [ ] TEST-259: Verify map pan controls
- [ ] TEST-260: Verify map fit-to-screen
- [ ] TEST-261: Verify map export to PNG
- [ ] TEST-262: Verify map layer toggle (physical/L2/L3/overlay)
- [ ] TEST-263: Verify map search functionality
- [ ] TEST-264: Verify map evidence artifact
- [ ] TEST-265: Verify map HTML offline rendering

#### 7.2 vPC Command Center (15 tests)
- [ ] TEST-266: Build vPC Command Center
- [ ] TEST-267: Verify vPC domain detection
- [ ] TEST-268: Verify vPC peer-link rendering
- [ ] TEST-269: Verify vPC member ports rendering
- [ ] TEST-270: Verify vPC shared downstream rendering
- [ ] TEST-271: Verify vPC consistency check
- [ ] TEST-272: Verify vPC type-1 inconsistency detection
- [ ] TEST-273: Verify vPC type-2 inconsistency detection
- [ ] TEST-274: Verify vPC orphan port detection
- [ ] TEST-275: Verify vPC VLAN consistency
- [ ] TEST-276: Click vPC domain to open details
- [ ] TEST-277: Verify vPC domain side panel
- [ ] TEST-278: Verify vPC domain board display
- [ ] TEST-279: Verify vPC map tab
- [ ] TEST-280: Verify vPC evidence artifact

#### 7.3 Advanced L3 Map (10 tests)
- [ ] TEST-281: Build Advanced L3 Map
- [ ] TEST-282: Verify routing topology rendering
- [ ] TEST-283: Verify IP subnet display
- [ ] TEST-284: Verify routing protocol detection (OSPF/BGP/Static)
- [ ] TEST-285: Verify L3 edge labels
- [ ] TEST-286: Verify subnet aggregation
- [ ] TEST-287: Verify AS number display
- [ ] TEST-288: Verify map layer selection
- [ ] TEST-289: Verify map evidence artifact
- [ ] TEST-290: Verify map HTML offline rendering

#### 7.4 Network Flows Map (10 tests)
- [ ] TEST-291: Build Network Flows Map
- [ ] TEST-292: Verify gateway display
- [ ] TEST-293: Verify inter-VLAN flows
- [ ] TEST-294: Verify flow arrow direction
- [ ] TEST-295: Verify flow label (VLAN IDs)
- [ ] TEST-296: Verify flow path visualization
- [ ] TEST-297: Verify flow color coding
- [ ] TEST-298: Verify map legend
- [ ] TEST-299: Verify map evidence artifact
- [ ] TEST-300: Verify map HTML offline rendering

#### 7.5 Map UI (5 tests)
- [ ] TEST-301: Verify map status message
- [ ] TEST-302: Verify map stop button
- [ ] TEST-303: Verify map open in browser button
- [ ] TEST-304: Verify map open diagnostics folder
- [ ] TEST-305: Verify map download export ZIP

---

### 8. Swiss Tools Operations (45 Tests)

#### 8.1 MAC Address Search (10 tests)
- [ ] TEST-306: Search MAC address in inventory scope
- [ ] TEST-307: Verify MAC format acceptance (colon/dot/hyphen)
- [ ] TEST-308: Verify MAC format validation
- [ ] TEST-309: Verify MAC trace progress bar
- [ ] TEST-310: Verify MAC trace hop table
- [ ] TEST-311: Verify MAC trace path summary
- [ ] TEST-312: Open MAC trace HTML report
- [ ] TEST-313: Verify MAC trace evidence artifact
- [ ] TEST-314: Verify MAC trace on single device
- [ ] TEST-315: Verify MAC trace on multiple devices

#### 8.2 Path Reconstruct (10 tests)
- [ ] TEST-316: Run path reconstruct after MAC trace
- [ ] TEST-317: Verify path reconstruct gate (requires MAC + L2 edges)
- [ ] TEST-318: Verify path reconstruct hop table
- [ ] TEST-319: Verify path reconstruct evidence column
- [ ] TEST-320: Verify path reconstruct without MAC (label only)
- [ ] TEST-321: Verify path reconstruct CLI note
- [ ] TEST-322: Verify path reconstruct not forwarding path
- [ ] TEST-323: Verify path reconstruct requires L2 edges
- [ ] TEST-324: Verify path reconstruct on offline HTML
- [ ] TEST-325: Verify path reconstruct error handling

#### 8.3 Description Search (10 tests)
- [ ] TEST-326: Search interface description
- [ ] TEST-327: Verify description search is case-insensitive
- [ ] TEST-328: Verify description search matches beginning
- [ ] TEST-329: Verify description search matches middle
- [ ] TEST-330: Verify description search matches end
- [ ] TEST-331: Verify description search progress bar
- [ ] TEST-332: Verify description search results table
- [ ] TEST-333: Open description search HTML report
- [ ] TEST-334: Verify description search evidence artifact
- [ ] TEST-335: Verify description search on multiple devices

#### 8.4 Network Ping Scan (10 tests)
- [ ] TEST-336: Run CIDR ping scan
- [ ] TEST-337: Verify CIDR format validation
- [ ] TEST-338: Verify CIDR size limit (256 hosts max)
- [ ] TEST-339: Verify ping scan progress bar
- [ ] TEST-340: Verify ping scan results table
- [ ] TEST-341: Verify ping scan responsive IPs
- [ ] TEST-342: Open ping scan HTML report
- [ ] TEST-343: Verify ping scan evidence artifact
- [ ] TEST-344: Verify ping scan timeout handling
- [ ] TEST-345: Verify ping scan source chip

#### 8.5 Other Tools (5 tests)
- [ ] TEST-346: Run failure correlation
- [ ] TEST-347: Verify failure correlation logs analysis
- [ ] TEST-348: Run STP topology scan
- [ ] TEST-349: Verify STP root/bridge port detection
- [ ] TEST-350: Verify STP evidence artifact

---

### 9. Utilities (40 Tests)

#### 9.1 OS Audit (10 tests)
- [ ] TEST-351: Run OS audit (hardware, version, serial)
- [ ] TEST-352: Verify OS audit CSV output
- [ ] TEST-353: Verify OS audit includes serial numbers
- [ ] TEST-354: Verify OS audit includes software version
- [ ] TEST-355: Verify OS audit includes hardware model
- [ ] TEST-356: Verify OS audit evidence artifact
- [ ] TEST-357: Verify OS audit on IOS
- [ ] TEST-358: Verify OS audit on NX-OS
- [ ] TEST-359: Verify OS audit on multiple devices
- [ ] TEST-360: Verify OS audit error handling

#### 9.2 Config Backup (10 tests)
- [ ] TEST-361: Run config backup with filter
- [ ] TEST-362: Verify config backup saves to outputs/
- [ ] TEST-363: Verify config backup file naming
- [ ] TEST-364: Verify config backup timestamp
- [ ] TEST-365: Save running config (scope)
- [ ] TEST-366: Verify save running config evidence
- [ ] TEST-367: Compare two backup files
- [ ] TEST-368: Verify backup diff display
- [ ] TEST-369: Verify backup diff export
- [ ] TEST-370: Verify backup list refresh

#### 9.3 Asset Warranty (10 tests)
- [ ] TEST-371: Run Cisco asset warranty check
- [ ] TEST-372: Verify SSH collection
- [ ] TEST-373: Verify SNMP fallback
- [ ] TEST-374: Verify asset warranty HTML output
- [ ] TEST-375: Verify asset warranty CSV output
- [ ] TEST-376: Verify asset warranty PDF output
- [ ] TEST-377: Verify asset warranty evidence artifact
- [ ] TEST-378: Verify asset warranty on IOS
- [ ] TEST-379: Verify asset warranty on NX-OS
- [ ] TEST-380: Verify asset warranty error handling

#### 9.4 Port Interface Map (10 tests)
- [ ] TEST-381: Run port interface map
- [ ] TEST-382: Verify port map on all devices in scope
- [ ] TEST-383: Verify port map parallel execution
- [ ] TEST-384: Open port map HTML report
- [ ] TEST-385: Verify port map evidence artifact
- [ ] TEST-386: Verify port map on IOS
- [ ] TEST-387: Verify port map on NX-OS
- [ ] TEST-388: Verify port map error handling
- [ ] TEST-389: Verify port map timeout
- [ ] TEST-390: Verify port map logs

---

### 10. Standards Validator (35 Tests)

#### 10.1 Policy Library (10 tests)
- [ ] TEST-391: Load policy library (golden_gate.yaml)
- [ ] TEST-392: Load policy library (standards.json)
- [ ] TEST-393: Load policy library (standards.yaml)
- [ ] TEST-394: Upload custom policy (YAML)
- [ ] TEST-395: Upload custom policy (JSON)
- [ ] TEST-396: Verify policy format detection
- [ ] TEST-397: Verify policy description display
- [ ] TEST-398: Verify policy category extraction
- [ ] TEST-399: Verify policy count display
- [ ] TEST-400: Verify policy validation

#### 10.2 Validation Execution (15 tests)
- [ ] TEST-401: Run standards validation
- [ ] TEST-402: Select min severity (all/low/medium/high/critical)
- [ ] TEST-403: Select report format (HTML/text/both)
- [ ] TEST-404: Select categories to include
- [ ] TEST-405: Enable generate fix scripts
- [ ] TEST-406: Verify validation progress bar
- [ ] TEST-407: Verify validation status display
- [ ] TEST-408: Verify validation summary bar (devices/compliant/violations)
- [ ] TEST-409: Verify validation results table
- [ ] TEST-410: Download consolidated TXT report
- [ ] TEST-411: Download HTML report
- [ ] TEST-412: Export CSV
- [ ] TEST-413: Clear validation results
- [ ] TEST-414: Verify validation evidence artifact
- [ ] TEST-415: Verify validation on single device

#### 10.3 Validation Results (10 tests)
- [ ] TEST-416: Verify compliant device count
- [ ] TEST-417: Verify non-compliant device count
- [ ] TEST-418: Verify total issues count
- [ ] TEST-419: Verify critical issues count
- [ ] TEST-420: Verify severity filtering
- [ ] TEST-421: Verify category filtering
- [ ] TEST-422: Verify device filtering
- [ ] TEST-423: Verify issue details display
- [ ] TEST-424: Verify fix script generation
- [ ] TEST-425: Verify validation error handling

---

### 11. Templates (25 Tests)

#### 11.1 Template Management (10 tests)
- [ ] TEST-426: Load template list
- [ ] TEST-427: Create new template
- [ ] TEST-428: Save template
- [ ] TEST-429: Edit template
- [ ] TEST-430: Delete template
- [ ] TEST-431: Verify template filename validation
- [ ] TEST-432: Verify template editor
- [ ] TEST-433: Verify template variable scanning
- [ ] TEST-434: Verify template variable form
- [ ] TEST-435: Verify template refresh

#### 11.2 Template Rendering (10 tests)
- [ ] TEST-436: Select template from dropdown
- [ ] TEST-437: Apply preset template
- [ ] TEST-438: Fill template variables
- [ ] TEST-439: Render template
- [ ] TEST-440: Verify rendered output
- [ ] TEST-441: Copy rendered output
- [ ] TEST-442: Verify Jinja2 syntax
- [ ] TEST-443: Verify template error handling
- [ ] TEST-444: Verify template variable types
- [ ] TEST-445: Verify template evidence artifact

#### 11.3 Template Presets (5 tests)
- [ ] TEST-446: Load preset template list
- [ ] TEST-447: Generate preset into editor
- [ ] TEST-448: Verify preset template variables
- [ ] TEST-449: Verify preset template rendering
- [ ] TEST-450: Verify preset template documentation

---

### 12. Plugin Platform (30 Tests)

#### 12.1 Plugin Discovery (10 tests)
- [ ] TEST-451: Reload plugin registry
- [ ] TEST-452: Verify plugin list display
- [ ] TEST-453: Verify plugin name display
- [ ] TEST-454: Verify plugin description display
- [ ] TEST-455: Verify plugin version display
- [ ] TEST-456: Verify plugin type display
- [ ] TEST-457: Select plugin from list
- [ ] TEST-458: Verify plugin details panel
- [ ] TEST-459: Verify plugin history
- [ ] TEST-460: Clear plugin selection

#### 12.2 Plugin Execution (10 tests)
- [ ] TEST-461: Execute base_template plugin
- [ ] TEST-462: Execute cisco_asset_warranty plugin
- [ ] TEST-463: Execute config_templates plugin
- [ ] TEST-464: Execute network_discovery plugin
- [ ] TEST-465: Execute standards_validator plugin
- [ ] TEST-466: Verify plugin execution progress
- [ ] TEST-467: Verify plugin execution logs
- [ ] TEST-468: Verify plugin execution evidence
- [ ] TEST-469: Verify plugin error handling
- [ TEST-470: Verify plugin timeout

#### 12.3 Plugin Security (10 tests)
- [ ] TEST-471: Verify HTTP upload is disabled
- [ ] TEST-472: Verify upload button is disabled
- [ ] TEST-473: Verify plugin install model (offline_local_directory)
- [ ] TEST-474: Verify plugin AST denylist
- [ ] TEST-475: Verify plugin sandbox limitations
- [ ] TEST-476: Verify plugin runs in-process
- [ ] TEST-477: Verify plugin credential access
- [ ] TEST-478: Verify plugin API access
- [ ] TEST-479: Verify plugin file system access
- [ ] TEST-480: Verify plugin code review requirement

---

### 13. UI/UX & Accessibility (20 Tests)

#### 13.1 Navigation (10 tests)
- [ ] TEST-481: Verify tab navigation (Network Search/Interfaces/VLAN/etc.)
- [ ] TEST-482: Verify sidebar navigation
- [ ] TEST-483: Verify keyboard navigation (Tab/Shift+Tab)
- [ ] TEST-484: Verify keyboard navigation (Enter/Space)
- [ ] TEST-485: Verify focus indicators
- [ ] TEST-486: Verify ARIA labels
- [ ] TEST-487: Verify button labels
- [ ] TEST-488: Verify form labels
- [ ] TEST-489: Verify link text
- [ ] TEST-490: Verify heading hierarchy

#### 13.2 Responsive Design (10 tests)
- [ ] TEST-491: Verify UI at 1920px width
- [ ] TEST-492: Verify UI at 1440px width
- [ ] TEST-493: Verify UI at 1024px width
- [ ] TEST-494: Verify UI at 768px width
- [ ] TEST-495: Verify horizontal scrollbar on narrow screens
- [ ] TEST-496: Verify middle screen scrolling
- [ ] TEST-497: Verify Settings credential scrolling
- [ ] TEST-498: Verify table column visibility
- [ ] TEST-499: Verify Action column accessibility
- [ ] TEST-500: Verify mobile layout (if applicable)

---

## Test Execution Workflow

### Pre-Test Setup
1. Start Docker lab: `cd lab/docker && docker-compose up -d`
2. Verify lab connectivity: `telnet 127.0.0.1 2201`, `2202`, `2203`
3. Start NST application: `python vlan_checker_web.py`
4. Verify health endpoint: `curl http://127.0.0.1:5051/health`

### Test Execution Order
1. **Phase 1: Authentication & Vault** (TEST-001 to TEST-025)
2. **Phase 2: Inventory Management** (TEST-026 to TEST-065)
3. **Phase 3: Device Connectivity** (TEST-066 to TEST-100)
4. **Phase 4: VLAN Operations** (TEST-101 to TEST-150)
5. **Phase 5: Interface Management** (TEST-151 to TEST-195)
6. **Phase 6: Network Discovery** (TEST-196 to TEST-245)
7. **Phase 7: Topology Maps** (TEST-246 to TEST-305)
8. **Phase 8: Swiss Tools** (TEST-306 to TEST-350)
9. **Phase 9: Utilities** (TEST-351 to TEST-390)
10. **Phase 10: Standards Validator** (TEST-391 to TEST-425)
11. **Phase 11: Templates** (TEST-426 to TEST-450)
12. **Phase 12: Plugin Platform** (TEST-451 to TEST-480)
13. **Phase 13: UI/UX & Accessibility** (TEST-481 to TEST-500)

### Post-Test Cleanup
1. Stop Docker lab: `cd lab/docker && docker-compose down`
2. Review evidence artifacts in `outputs/`
3. Generate test report: Aggregate all test results
4. Team review: Network Engineer Council, Product Architect, NOC Operator

---

## Expert Team Review Requirements

### Network Engineer Council Review
- Verify all CLI commands are vendor-appropriate
- Validate parsing output matches device reality
- Confirm topology honesty (no invented links)
- Review evidence artifacts for completeness
- Sign off on TEAM_VALIDATION_REGISTER

### Product Architect Review
- Verify API contracts are honored
- Validate zero-trust invariants
- Review UI/UX consistency
- Confirm offline capability
- Sign off on GAP_REGISTER

### NOC Operator Review
- Verify workflows match operational reality
- Validate error messages are actionable
- Confirm output formats are usable
- Review time to complete typical tasks
- Sign off on operational readiness

### UI/UX Professional Review
- Verify accessibility compliance (WCAG 2.1 AA)
- Validate responsive design
- Review color contrast
- Confirm keyboard navigation
- Sign off on UI readiness

---

## Test Result Template

```markdown
## Test Execution Report - [Date]

### Lab Configuration
- IOS Device: C9300-24P (127.0.0.1:2201) - Status: [PASS/FAIL]
- NX-OS Device 1: N9K-C93180YC-EX (127.0.0.1:2202) - Status: [PASS/FAIL]
- NX-OS Device 2: N9K-C9348GC-XP (127.0.0.1:2203) - Status: [PASS/FAIL]

### Test Results Summary
- Total Tests: 500
- Passed: [count]
- Failed: [count]
- Skipped: [count]
- Blocked: [count]

### Failed Tests
- [List failed test IDs with error details]

### Blocked Tests
- [List blocked test IDs with dependency details]

### Expert Sign-Off
- Network Engineer Council: [Name] - [Date]
- Product Architect: [Name] - [Date]
- NOC Operator: [Name] - [Date]
- UI/UX Professional: [Name] - [Date]
```

---

## Notes

1. All tests require valid credentials for lab devices
2. Evidence artifacts are stored in `outputs/` directory
3. Test IDs are unique for traceability
4. Tests should be executed in order due to dependencies
5. Failed tests must be triaged and re-tested after fixes
6. This test plan evolves with product features - update MANDATORY_MANIFEST.yaml accordingly

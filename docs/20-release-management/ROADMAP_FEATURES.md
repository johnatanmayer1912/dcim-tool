# Feature Recommendations Roadmap

> **7 Prioritized Features for Network Swiss Tool Pro**  
> **Prioritized by:** Business Value (Time Saved, Risk Reduced)  
> **Constraint:** Standalone Only (No External Dependencies)

---

## Executive Summary

| Priority | Feature | Time Saved | Risk Reduction | Complexity |
|----------|---------|------------|----------------|------------|
| 🔥 1 | Config Drift Detection | 8 hrs/week | High | Medium |
| 🔥 2 | Bulk Config Deployment | 12 hrs/week | High | High |
| 3 | Real-time Health Dashboard | 4 hrs/week | Medium | Medium |
| 4 | Interface Utilization Monitor | 6 hrs/week | Medium | Medium |
| 5 | Compliance Scanner | 10 hrs/week | High | Medium |
| 6 | Troubleshooting Assistant | 5 hrs/week | Low | High |
| 7 | Automated VLAN Provisioning | 15 hrs/week | High | High |

**Total Potential Time Savings:** 50+ hours/week for large networks

---

## 🔥 Priority 1: Configuration Drift Detection & Alerting

### What It Does
Automatically compares device configurations against a "golden baseline" and alerts when unauthorized changes occur.

### Business Value
- **Time Saved:** 8 hours/week (reduces "what changed?" investigations)
- **Risk Reduction:** High - catches unauthorized changes before they cause outages
- **Use Case:** Friday 5 PM change that breaks something Monday morning

### User Workflow
```
1. Run "Capture Baseline" → Stores all device configs as reference
2. Schedule "Drift Check" (daily/hourly)
3. Receive alerts: "Switch-Core-01: Lines 45-52 added by user admin"
4. View diff in web UI
5. Approve (update baseline) or Revert
```

### Technical Implementation

**Files to Create:**
- `modules/config_drift_detector.py` - Core detection logic
- `modules/baseline_manager.py` - Baseline storage/comparison
- UI additions in `vlan_checker_web.py`

**Files to Modify:**
- `modules/adapters.py` - Add `run_drift_check()` function
- `modules/web/templates/index.html` - Add drift dashboard

**Key Components:**
```python
def capture_baseline(devices, user, pwd, enb_pwd, log_func):
    """Capture current configs as golden baseline."""
    for dev in devices:
        config = get_running_config(dev, user, pwd, enb_pwd)
        save_baseline(dev['host'], config)

def check_drift(device, user, pwd, enb_pwd, log_func):
    """Compare current config vs baseline."""
    current = get_running_config(device, user, pwd, enb_pwd)
    baseline = load_baseline(device['host'])
    
    diff = generate_diff(baseline, current)
    if diff:
        return {
            "status": "drift_detected",
            "diff": diff,
            "lines_added": diff['added'],
            "lines_removed": diff['removed']
        }
    return {"status": "no_drift"}
```

**Storage:**
```
baselines/
└── {hostname}_baseline.txt           # Golden reference
└── {hostname}_last_check.txt         # Last comparison point
```

### Complexity Assessment
| Factor | Rating | Notes |
|--------|--------|-------|
| Code Complexity | Medium | Diff algorithm + storage |
| QA Required | High | Must not miss changes |
| Network Risk | Low | Read-only operation |
| UI Changes | Medium | New dashboard needed |

**Implementation Time:** 2-3 days
**Risk of Implementation:** Low (read-only)

---

## 🔥 Priority 2: Bulk Config Deployment with Auto-Rollback

### What It Does
Deploy configuration snippets to multiple devices with automatic pre-change backup and rollback capability if verification fails.

### Business Value
- **Time Saved:** 12 hours/week (mass changes without manual per-device work)
- **Risk Reduction:** High - automatic rollback prevents failed changes
- **Use Case:** Enable SNMPv3 on 200 switches, NTP update across all devices

### User Workflow
```
1. Upload or paste config template
2. Select target devices (group or filter)
3. Enable "Dry Run" → Preview commands per device
4. Disable "Dry Run" → Execute
5. System automatically:
   - Backs up each device
   - Deploys config
   - Verifies deployment (show commands)
   - If verification fails → Auto-rollback
6. Generate deployment report
```

### Technical Implementation

**Files to Create:**
- `modules/bulk_config_deploy.py` - Core deployment logic
- `modules/config_verifier.py` - Post-deployment verification
- `modules/rollback_manager.py` - Rollback orchestration

**Files to Modify:**
- `modules/adapters.py` - Add `run_bulk_deploy()` function
- `modules/vlan_mgmt_production.py` - Reuse backup logic

**Key Components:**
```python
def deploy_config(device, user, pwd, enb_pwd, config_snippet, 
                  auto_rollback=True, verify_commands=None):
    """Deploy config with backup and verification.
    
    Args:
        verify_commands: List of "show" commands to verify success
    """
    # 1. Pre-backup
    backup_path = capture_config(device, user, pwd, enb_pwd)
    
    try:
        # 2. Deploy
        conn = connect_permissive(device, user, pwd, enb_pwd)
        conn.send_config_set(config_snippet.split('\n'))
        conn.disconnect()
        
        # 3. Verify
        if verify_commands:
            verification_passed = run_verification(
                device, user, pwd, enb_pwd, verify_commands
            )
            if not verification_passed and auto_rollback:
                # 4. Rollback if failed
                rollback_config(device, user, pwd, enb_pwd, backup_path)
                return {"status": "rollback", "reason": "verification_failed"}
        
        return {"status": "success", "backup": backup_path}
        
    except Exception as e:
        if auto_rollback:
            rollback_config(device, user, pwd, enb_pwd, backup_path)
        return {"status": "fail", "error": str(e)}
```

### Safety Features
1. **Dry-run mode** - Preview commands
2. **Per-device backup** - Rollback to exact pre-change state
3. **Verification commands** - "show" commands to validate
4. **Auto-rollback** - On verification failure
5. **Batch size limit** - Configurable max devices per batch
6. **Pause on error** - Stop if X% of devices fail

### Complexity Assessment
| Factor | Rating | Notes |
|--------|--------|-------|
| Code Complexity | High | Transaction management |
| QA Required | Very High | Can break networks |
| Network Risk | High | Deploys actual config |
| UI Changes | Medium | Upload + preview interface |

**Implementation Time:** 4-5 days
**Risk of Implementation:** High (must be dry-run by default)

**Recommended Safety:**
- Default to dry-run mode
- Require explicit "--live" flag
- Maximum 5 devices for first live test
- Admin approval workflow

---

## Priority 3: Real-Time Network Health Dashboard

### What It Does
Web dashboard showing real-time device health, interface status, and recent alerts with auto-refresh.

### Business Value
- **Time Saved:** 4 hours/week (no need to manually check devices)
- **Risk Reduction:** Medium - early warning of issues
- **Use Case:** NOC monitoring, quick health checks before changes

### User Workflow
```
1. Open "Health Dashboard" tab
2. See at-a-glance status:
   - Device reachability (green/red)
   - Interface up/down summary
   - Recent VLAN changes
   - Config backup status
3. Click device → Detailed view
4. Auto-refresh every 60 seconds
```

### Technical Implementation

**Files to Create:**
- `modules/health_collector.py` - Data collection
- `modules/web/templates/dashboard.html` - Dashboard UI

**Files to Modify:**
- `vlan_checker_web.py` - Add `/api/health` endpoint

**Key Components:**
```python
@app.route('/api/health')
def api_health():
    """Return current health status of all devices."""
    devices = get_devices_from_file('inventory.txt')
    
    health_data = []
    for dev in devices:
        # Quick ping check
        ping_result = quick_ping(dev['host'])
        
        # Get last known interface status (from cache/file)
        int_status = get_cached_interface_status(dev['host'])
        
        # Get last backup time
        last_backup = get_last_backup_time(dev['host'])
        
        health_data.append({
            "host": dev['host'],
            "reachable": ping_result,
            "interfaces_up": int_status['up'],
            "interfaces_down": int_status['down'],
            "last_backup": last_backup,
            "health_score": calculate_health_score(...)
        })
    
    return jsonify({"health": health_data})
```

**Dashboard UI Features:**
- Device status grid (green/yellow/red)
- Interface up/down counts
- Last backup timestamp
- Quick action buttons (connectivity check, backup)

### Complexity Assessment
| Factor | Rating | Notes |
|--------|--------|-------|
| Code Complexity | Medium | Polling + caching |
| QA Required | Medium | UI responsiveness |
| Network Risk | Low | Read-only |
| UI Changes | High | New dashboard page |

**Implementation Time:** 3-4 days
**Risk of Implementation:** Low

---

## Priority 4: Interface Utilization Monitoring & Reporting

### What It Does
Collect interface statistics (input/output rates, errors, drops) over time and generate capacity reports.

### Business Value
- **Time Saved:** 6 hours/week (automated capacity planning)
- **Risk Reduction:** Medium - proactive capacity management
- **Use Case:** Identify top talkers, find underutilized links, plan upgrades

### User Workflow
```
1. Schedule "Interface Stats Collection" (daily/weekly)
2. System collects:
   - Interface counters (in/out bytes, packets)
   - Error counters (CRC, drops, overruns)
   - Utilization percentages
3. Generate reports:
   - Top 10 most utilized interfaces
   - Interfaces with errors
   - Historical trending (7/30/90 days)
4. Export to CSV for capacity planning
```

### Technical Implementation

**Files to Create:**
- `modules/interface_stats.py` - Stats collection
- `modules/capacity_analyzer.py` - Trend analysis

**Storage:**
```
stats/
└── {hostname}/
    └── interface_stats_YYYYMMDD.csv
```

**Key Components:**
```python
def collect_interface_stats(device, user, pwd, enb_pwd):
    """Collect interface statistics."""
    conn = connect_permissive(device, user, pwd, enb_pwd)
    
    # Cisco command
    output = conn.send_command("show interfaces summary")
    
    # Parse stats
    stats = parse_interface_summary(output)
    
    conn.disconnect()
    
    # Store with timestamp
    store_stats(device['host'], datetime.now(), stats)
    
    return stats
```

### Complexity Assessment
| Factor | Rating | Notes |
|--------|--------|-------|
| Code Complexity | Medium | Time-series data |
| QA Required | Medium | Data accuracy |
| Network Risk | Low | Read-only |
| UI Changes | Medium | Reports + charts |

**Implementation Time:** 2-3 days
**Risk of Implementation:** Low

---

## Priority 5: Network Baseline Compliance Scanner

### What It Does
Audit devices against organizational standards (SNMP config, NTP, logging, security policies) and generate compliance reports.

### Business Value
- **Time Saved:** 10 hours/week (automated audit)
- **Risk Reduction:** High - ensures security posture
- **Use Case:** Security audits, pre-change validation, compliance reporting

### User Workflow
```
1. Define compliance policies in config file:
   - SNMP must use v3 with auth
   - NTP must be configured
   - Syslog must point to collector
   - Telnet must be disabled
2. Run "Compliance Scan"
3. Get report per device:
   - Pass/Fail per policy
   - Current vs expected config
   - Remediation commands
4. Export audit report (CSV/PDF)
```

### Technical Implementation

**Files to Create:**
- `modules/compliance_scanner.py` - Scan logic
- `modules/policy_engine.py` - Policy definitions
- `compliance_policies.yaml` - Configurable policies

**Policy Definition Example:**
```yaml
policies:
  snmp_v3_required:
    description: "SNMP must be v3 with authentication"
    check_commands:
      - "show snmp"
    expected_patterns:
      - "snmp-server group.*v3.*auth"
    severity: high
  
  ntp_configured:
    description: "NTP must be configured and synced"
    check_commands:
      - "show ntp status"
    expected_patterns:
      - "Clock is synchronized"
    severity: medium
```

### Complexity Assessment
| Factor | Rating | Notes |
|--------|--------|-------|
| Code Complexity | Medium | Pattern matching engine |
| QA Required | High | False positives bad |
| Network Risk | Low | Read-only |
| UI Changes | Medium | Compliance report view |

**Implementation Time:** 3-4 days
**Risk of Implementation:** Low

---

## Priority 6: Intelligent Troubleshooting Assistant

### What It Does
Guided troubleshooting wizard: user inputs symptoms → system runs diagnostics → suggests fixes.

### Business Value
- **Time Saved:** 5 hours/week (faster MTTR)
- **Risk Reduction:** Low (but captures tribal knowledge)
- **Use Case:** Junior engineers learning, complex issues, 3 AM pages

### User Workflow
```
1. Select symptom category:
   - "User can't reach server"
   - "Interface flapping"
   - "High latency"
   - "VLAN mismatch"
2. Answer clarifying questions
3. System runs automated diagnostics:
   - Ping tests
   - MAC table checks
   - Interface status
   - Routing table checks
4. View diagnostic results
5. Get suggested fixes with commands
```

### Technical Implementation

**Files to Create:**
- `modules/troubleshooter.py` - Core engine
- `modules/diagnostic_rules.py` - Rule database
- `modules/suggestion_engine.py` - Fix generator

**Diagnostic Rules Example:**
```python
DIAGNOSTIC_RULES = {
    "connectivity_issue": {
        "questions": [
            "Source IP:",
            "Destination IP:",
            "Is destination on same VLAN?"
        ],
        "diagnostics": [
            "ping_test",
            "mac_table_check",
            "arp_table_check",
            "routing_table_check"
        ],
        "suggestions": {
            "mac_not_found": "Check if source is connected. Run MAC trace.",
            "arp_missing": "Check if devices are on same subnet.",
            "route_missing": "Check routing table for destination prefix."
        }
    }
}
```

### Complexity Assessment
| Factor | Rating | Notes |
|--------|--------|-------|
| Code Complexity | High | Rule engine + NLP |
| QA Required | High | Accuracy critical |
| Network Risk | Low | Recommendations only |
| UI Changes | High | Wizard interface |

**Implementation Time:** 5-7 days
**Risk of Implementation:** Low (suggestions only, no auto-fix)

---

## Priority 7: Automated VLAN Provisioning Workflow

### What It Does
End-to-end workflow for VLAN provisioning: request → approval → validation → deployment → verification with full audit trail.

### Business Value
- **Time Saved:** 15 hours/week (streamlined provisioning)
- **Risk Reduction:** High - eliminates manual errors
- **Use Case:** New VLAN requests, automated provisioning

### User Workflow
```
1. User submits VLAN request:
   - VLAN ID
   - Name
   - Target devices/groups
   - Purpose/business justification
2. Approver receives notification
3. Approver reviews and approves/rejects
4. If approved:
   - System validates no conflicts
   - Dry-run preview
   - Deploy with verification
   - Generate completion report
5. Full audit trail saved
```

### Technical Implementation

**Files to Create:**
- `modules/vlan_workflow.py` - Workflow engine
- `modules/approval_system.py` - Approval logic
- `modules/audit_logger.py` - Audit trail

**Workflow State Machine:**
```
SUBMITTED → PENDING_APPROVAL → APPROVED → VALIDATING → DEPLOYING → VERIFIED
                ↓                   ↓
            REJECTED           VALIDATION_FAILED
```

### Complexity Assessment
| Factor | Rating | Notes |
|--------|--------|-------|
| Code Complexity | High | Workflow engine |
| QA Required | Very High | Business critical |
| Network Risk | Medium | Deploys VLANs |
| UI Changes | High | Workflow UI |

**Implementation Time:** 5-7 days
**Risk of Implementation:** Medium (requires approval workflow)

---

## Implementation Recommendations

### Phase 1 (Immediate - Weeks 1-2)
1. **Config Drift Detection** - High value, low risk
2. **Compliance Scanner** - High value for audits

### Phase 2 (Short-term - Weeks 3-4)
3. **Health Dashboard** - Improves daily workflow
4. **Interface Utilization** - Capacity planning

### Phase 3 (Medium-term - Weeks 5-6)
5. **Troubleshooting Assistant** - Knowledge capture
6. **Bulk Config Deploy** - With heavy safety guards

### Phase 4 (Long-term - Weeks 7-8)
7. **VLAN Provisioning Workflow** - Requires approval system

---

## Detailed Specifications

Each feature has a detailed specification:
- `FEATURE-01-DRIFT-DETECTION.md`
- `FEATURE-02-BULK-DEPLOY.md`
- `FEATURE-03-HEALTH-DASHBOARD.md`
- `FEATURE-04-UTILIZATION-MONITOR.md`
- `FEATURE-05-COMPLIANCE-SCANNER.md`
- `FEATURE-06-TROUBLESHOOTER.md`
- `FEATURE-07-VLAN-WORKFLOW.md`

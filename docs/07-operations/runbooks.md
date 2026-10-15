# Runbooks

| Metadata | Description |
| :--- | :--- |
| **Purpose** | Operational runbooks for common NetworkSwissToolPro tasks, procedures, and troubleshooting scenarios. |
| **Scope** | Daily operations, common tasks, standard procedures, and routine troubleshooting. |
| **Responsibilities** | Operational procedures, task execution, and incident response. |
| **Dependencies** | System architecture, operational workflows, troubleshooting guides. |
| **Related Documents** | [production-operations.md](production-operations.md), [service-recovery.md](service-recovery.md), [troubleshooting.md](troubleshooting.md) |
| **Operational Impact** | Standardizes operations, reduces errors, improves efficiency, enables knowledge transfer. |
| **Failure Conditions** | Outdated procedures, missing steps, incorrect information. |
| **Recovery Notes** | Update runbooks after procedure changes, validate runbooks quarterly, train operators on runbook usage. |
| **Version Awareness** | v6.9.5 |
| **Last Synchronization Timestamp** | 2026-05-25 |
| **Maintainer** | LIBRARIAN / Operations Lead |

---

# RUNBOOK OVERVIEW

## Runbook Categories

### Daily Operations
- Application startup and shutdown
- Health checks
- Log monitoring
- Backup verification

### Network Operations
- VLAN management
- Device configuration
- Topology mapping
- MAC address operations

### Maintenance Operations
- System updates
- Configuration changes
- Plugin management
- Performance tuning

### Incident Response
- Service failures
- Performance issues
- Security incidents
- Data recovery

---

# DAILY OPERATIONS

## RB-001: Application Startup

### Purpose
Standard procedure for starting NetworkSwissToolPro application.

### Prerequisites
- Python 3.12+ installed
- Dependencies installed
- Configuration files present
- Inventory file configured

### Procedure

#### Step 1: Pre-Start Checks
```powershell
# Verify Python installation
python --version

# Verify dependencies
pip list

# Verify configuration
Test-Path "inventory.txt"
Test-Path "policies\standards.yaml"
Test-Path "modules"
Test-Path "utils"
```

#### Step 2: Start Application
```powershell
# Navigate to application directory
cd "C:\Net_mngmnt_tool - V6 - cursor"

# Launch application
python vlan_checker_web.py
```

#### Step 3: Verify Startup
```powershell
# Check web UI accessible
# Open browser to http://127.0.0.1:5051

# Check for errors in console
# Review logs\startup.log
```

### Validation Criteria
- [ ] Application launches without errors
- [ ] Web UI accessible at http://127.0.0.1:5051
- [ ] All tabs load correctly
- [ ] No console errors
- [ ] Logs show successful startup

### Troubleshooting
- **Application won't start**: Check Python version, dependencies, configuration files
- **Web UI not accessible**: Check port 5051 availability, firewall settings
- **Console errors**: Review error logs, check missing modules

---

## RB-002: Application Shutdown

### Purpose
Standard procedure for gracefully shutting down NetworkSwissToolPro.

### Prerequisites
- Application running
- No active operations in progress

### Procedure

#### Step 1: Check Active Operations
```powershell
# Check for active SSH connections
# Review CLI Terminal tab

# Check for running operations
# Review operation status in logs
```

#### Step 2: Graceful Shutdown
```powershell
# Close browser tabs
# Press Ctrl+C in terminal running application
# Wait for graceful shutdown
```

#### Step 3: Verify Shutdown
```powershell
# Verify process terminated
Get-Process | Where-Object {$_.ProcessName -like "*python*"}

# Verify port released
netstat -ano | findstr :5051
```

### Validation Criteria
- [ ] Application shuts down gracefully
- [ ] No active connections remain
- [ ] Port 5051 released
- [ ] Logs show clean shutdown

### Troubleshooting
- **Application won't shut down**: Force kill process, check for hung operations
- **Port still in use**: Kill process using port, restart system if needed

---

## RB-003: Health Check

### Purpose
Routine health check to verify application operational status.

### Frequency
- Daily: Automated health check
- Weekly: Comprehensive health check

### Procedure

#### Basic Health Check (Daily)
```powershell
# Check application running
Get-Process | Where-Object {$_.ProcessName -like "*python*"}

# Check web UI accessible
# Open browser to http://127.0.0.1:5051

# Check log files
Test-Path "logs\operations.log"
```

#### Comprehensive Health Check (Weekly)
```powershell
# Check all dependencies
pip list

# Check disk space
Get-PSDrive C

# Check memory usage
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Select-Object ProcessName, CPU, WorkingSet

# Check log file sizes
Get-ChildItem logs\ | Select-Object Name, Length

# Test critical imports
python -c "import netmiko; print('✓ netmiko OK')"
python -c "import flask; print('✓ flask OK')"
python -c "from modules import network_base; print('✓ network_base OK')"
```

### Validation Criteria
- [ ] Application process running
- [ ] Web UI accessible
- [ ] Log files writable
- [ ] Dependencies installed
- [ ] Sufficient disk space
- [ ] Memory usage normal
- [ ] All imports successful

### Troubleshooting
- **Application not running**: Start application, check for errors
- **Web UI not accessible**: Check network, firewall, port availability
- **Dependencies missing**: Reinstall dependencies
- **Disk space low**: Clean up logs, old reports

---

# NETWORK OPERATIONS

## RB-010: VLAN Management

### Purpose
Standard procedure for VLAN operations (add, modify, delete).

### Prerequisites
- Application running
- Device connectivity verified
- Inventory configured
- Appropriate permissions

### Procedure

#### Add VLAN
```powershell
# 1. Open VLAN Management tab
# 2. Select target devices
# 3. Enter VLAN ID and name
# 4. Configure optional parameters (description, state)
# 5. Review changes
# 6. Execute operation
# 7. Verify results
```

#### Modify VLAN
```powershell
# 1. Open VLAN Management tab
# 2. Select target devices
# 3. Select VLAN to modify
# 4. Update VLAN parameters
# 5. Review changes
# 6. Execute operation
# 7. Verify results
```

#### Delete VLAN
```powershell
# 1. Open VLAN Management tab
# 2. Select target devices
# 3. Select VLAN to delete
# 4. Confirm deletion
# 5. Execute operation
# 6. Verify removal
```

### Validation Criteria
- [ ] Operation completes without errors
- [ ] VLAN changes applied to all target devices
- [ ] Device configurations updated
- [ ] No unintended changes
- [ ] Logs show successful operation

### Troubleshooting
- **Operation fails**: Check device connectivity, permissions, device state
- **Partial success**: Check failed devices, retry operation
- **Unintended changes**: Review logs, rollback if needed

---

## RB-011: Device Configuration

### Purpose
Standard procedure for device configuration operations.

### Prerequisites
- Application running
- Device connectivity verified
- Inventory configured
- Configuration backup available

### Procedure

#### Backup Configuration
```powershell
# 1. Open Configuration Backup tab
# 2. Select target devices
# 3. Choose backup location
# 4. Execute backup
# 5. Verify backup files created
```

#### Restore Configuration
```powershell
# 1. Open Configuration Backup tab
# 2. Select target devices
# 3. Select backup file
# 4. Review changes
# 5. Execute restore
# 6. Verify configuration applied
```

### Validation Criteria
- [ ] Backup files created successfully
- [ ] Backup files contain valid configuration
- [ ] Restore operation completes
- [ ] Configuration applied correctly
- [ ] Device operational after restore

### Troubleshooting
- **Backup fails**: Check device connectivity, permissions, disk space
- **Restore fails**: Verify backup file integrity, device state
- **Device unresponsive after restore**: Check configuration validity, rollback

---

## RB-012: Topology Mapping

### Purpose
Standard procedure for generating network topology maps.

### Prerequisites
- Application running
- Device connectivity verified
- CDP/LLDP enabled on devices
- Sufficient device coverage

### Procedure

#### Generate Topology Map
```powershell
# 1. Open MAPS tab
# 2. Select devices for mapping
# 3. Configure map options
# 4. Execute topology discovery
# 5. Wait for discovery completion
# 6. Review generated map
# 7. Export map if needed
```

#### Validate Topology Map
```powershell
# 1. Verify all expected devices shown
# 2. Verify connections accurate
# 3. Check vPC domains correct
# 4. Verify interface information
# 5. Validate link types
```

### Validation Criteria
- [ ] Topology discovery completes
- [ ] All expected devices discovered
- [ ] Connections accurately represented
- [ ] vPC domains correctly identified
- [ ] Interface information accurate
- [ ] Map exports successfully

### Troubleshooting
- **Discovery incomplete**: Check device connectivity, CDP/LLDP status
- **Missing devices**: Verify device in inventory, check connectivity
- **Incorrect connections**: Verify CDP/LLDP data, device configurations
- **Map won't render**: Check browser compatibility, JavaScript errors

---

# MAINTENANCE OPERATIONS

## RB-020: System Update

### Purpose
Standard procedure for updating NetworkSwissToolPro to new version.

### Prerequisites
- Current version backup
- Update package available
- Maintenance window scheduled
- Rollback plan prepared

### Procedure

#### Pre-Update Preparation
```powershell
# 1. Backup current installation
xcopy /E /I "Net_mngmnt_tool - V6 - cursor" "backup\v6.9.5\"

# 2. Backup configuration files
copy inventory.txt backup\
xcopy /E /I policies backup\policies\

# 3. Backup logs
xcopy /E /I logs backup\logs\

# 4. Document current state
# Note current version, configuration, any customizations
```

#### Update Execution
```powershell
# 1. Stop application
# Close browser, terminate process

# 2. Extract update package
# Extract new version to temporary location

# 3. Copy new files
# Copy new files to installation directory
# Preserve configuration files

# 4. Update dependencies
pip install -r requirements.txt --upgrade

# 5. Start application
python vlan_checker_web.py
```

#### Post-Update Validation
```powershell
# 1. Verify version
# Check VERSION file, application UI

# 2. Verify functionality
# Test critical features

# 3. Verify configuration
# Check inventory, policies load correctly

# 4. Review logs
# Check for errors, warnings
```

### Validation Criteria
- [ ] Update completes without errors
- [ ] New version verified
- [ ] Application starts successfully
- [ ] Critical features operational
- [ ] Configuration preserved
- [ ] No data loss

### Troubleshooting
- **Update fails**: Restore from backup, check update package integrity
- **Application won't start**: Restore from backup, check dependencies
- **Configuration lost**: Restore configuration files from backup
- **Features broken**: Check release notes, restore from backup if needed

---

## RB-021: Log Management

### Purpose
Standard procedure for managing application log files.

### Frequency
- Weekly: Log rotation
- Monthly: Log archival
- Quarterly: Log cleanup

### Procedure

#### Log Rotation
```powershell
# 1. Stop application
# 2. Rename current log files
# 3. Create new log files
# 4. Start application
```

#### Log Archival
```powershell
# 1. Identify logs for archival
# 2. Compress logs
# 3. Move to archive location
# 4. Update archive index
```

#### Log Cleanup
```powershell
# 1. Identify logs older than retention period
# 2. Verify logs not needed for active investigations
# 3. Delete old logs
# 4. Update cleanup log
```

### Validation Criteria
- [ ] Log rotation completes
- [ ] New log files created
- [ ] Archived logs accessible
- [ ] Cleanup follows retention policy
- [ ] No critical logs deleted

### Troubleshooting
- **Rotation fails**: Check file permissions, disk space
- **Archival fails**: Check archive location, permissions
- **Cleanup fails**: Verify retention policy, check file locks

---

# INCIDENT RESPONSE

## RB-030: Service Failure

### Purpose
Standard procedure for responding to application service failures.

### Severity Levels
- **P0**: Critical - Application completely down
- **P1**: High - Major functionality impaired
- **P2**: Medium - Partial functionality impaired
- **P3**: Low - Minor functionality impaired

### Procedure

#### Initial Response (All Severities)
```powershell
# 1. Assess impact
# Determine affected users, functionality, data

# 2. Check application status
# Verify process running, web UI accessible

# 3. Check logs
# Review logs for errors, exceptions

# 4. Notify stakeholders
# Inform affected users, management
```

#### P0 Critical Response
```powershell
# 1. Immediate restart attempt
# Stop and start application

# 2. If restart fails
# Check system resources, dependencies

# 3. If still failing
# Restore from backup, escalate to senior staff

# 4. Document incident
# Record timeline, actions taken, root cause
```

#### P1 High Severity Response
```powershell
# 1. Attempt restart
# Stop and start application

# 2. If restart fails
# Check logs, configuration

# 3. Implement workaround
# Provide alternative access if possible

# 4. Document incident
# Record timeline, actions taken
```

### Validation Criteria
- [ ] Service restored
- [ ] Functionality verified
- [ ] Impact assessed
- [ ] Stakeholders notified
- [ ] Incident documented

### Troubleshooting
- **Service won't restart**: Check system resources, dependencies, configuration
- **Recurring failures**: Investigate root cause, implement permanent fix
- **Data corruption**: Restore from backup, investigate cause

---

## RB-031: Performance Issues

### Purpose
Standard procedure for responding to application performance issues.

### Symptoms
- Slow response times
- High CPU/memory usage
- Timeout errors
- Unresponsive interface

### Procedure

#### Performance Assessment
```powershell
# 1. Measure performance
# Check response times, CPU, memory, disk I/O

# 2. Identify bottlenecks
# Review logs, monitor system resources

# 3. Determine scope
# Single user, all users, specific features
```

#### Performance Remediation
```powershell
# 1. Optimize configuration
# Adjust timeouts, cache settings

# 2. Optimize operations
# Reduce concurrent operations, batch processing

# 3. System optimization
# Clear logs, free disk space, restart application
```

### Validation Criteria
- [ ] Performance improved
- [ ] Resource usage normal
- [ ] No timeout errors
- [ ] User experience acceptable

### Troubleshooting
- **Persistent performance issues**: Investigate code optimization, hardware upgrade
- **Specific feature slow**: Optimize feature implementation, review algorithms
- **Memory leaks**: Investigate memory usage patterns, restart application periodically

---

# RUNBOOK MAINTENANCE

## Review Schedule
- **Monthly**: Review runbook accuracy
- **Quarterly**: Update runbooks based on procedure changes
- **Annually**: Comprehensive runbook audit

## Update Process
1. Identify runbook requiring update
2. Document current procedure
3. Identify changes needed
4. Update runbook
5. Validate updated procedure
6. Train operators on changes
7. Archive old version

## Validation
- Test runbook procedures
- Verify step accuracy
- Check for missing steps
- Validate troubleshooting guidance

---

**Document Status:** ACTIVE
**Classification:** TIER-0 OPERATIONAL DOCUMENTATION
**Enforcement:** MANDATORY
**Drift Tolerance:** ZERO
**Next Review:** 2026-06-25

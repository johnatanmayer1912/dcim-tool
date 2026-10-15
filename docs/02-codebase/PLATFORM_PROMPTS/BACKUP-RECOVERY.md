# Backup & Recovery Procedures

> **How to backup before changes and recover when things go wrong**

---

## 🎯 Philosophy

### The Golden Rules

1. **Backup Before Change** - Always capture current state
2. **Test Recovery** - Know your backups work
3. **Keep Multiple Copies** - Recent + older backups
4. **Document Everything** - What changed, when, why

---

## Pre-Change Backup Procedures

### Automatic Backups (v4.5.7+)

The application **automatically** creates backups before VLAN changes:

```
backups/
└── {hostname}/
    └── config_YYYYMMDD_HHMMSS.txt
```

**This happens automatically when:**
- Adding VLANs (if auto_backup=True)
- Renaming VLANs
- Deleting VLANs

**Verify automatic backup:**
```bash
# After VLAN operation, check backups folder
ls backups/Switch-Core-01/
# Should see: config_20260414_143022.txt
```

### Manual Pre-Change Backup

**Before ANY manual changes:**

1. **Open Web UI**
2. **Go to "Config Backup" section**
3. **Click "Run Config Backup"**
4. **Wait for completion**
5. **Note backup directory name**

**Or via CLI:**
```bash
python main.py cli --task backup
```

### Bulk Operation Backup

**For bulk operations (affecting many devices):**

1. **Full Network Backup**
   ```bash
   # Backup all devices
   # Use Config Backup feature on all devices
   ```

2. **Store Backup Location**
   ```bash
   # Note the directory
   echo "Backup location: config_backups_YYYYMMDD_HHMMSS"
   ```

---

## Backup Storage Strategy

### Local Storage Structure

```
backups/
├── daily/              # Daily snapshots
│   └── YYYYMMDD/
├── prechange/          # Pre-change backups
│   └── {hostname}_YYYYMMDD_HHMMSS.txt
└── golden/             # Known-good baselines
    └── {hostname}_baseline.txt
```

### Retention Policy

| Backup Type | Retention | Example |
|-------------|-----------|---------|
| Session auto-backup | 30 days | config_20260414_143022.txt |
| Manual full backup | 90 days | config_backups_20260414_143022/ |
| Golden baseline | Permanent | Switch-Core-01_baseline.txt |

### External Backup

**For production environments:**

```bash
# Sync to external storage
rsync -av backups/ /mnt/backup-storage/network-tool/

# Or cloud sync
aws s3 sync backups/ s3://company-backups/network/
```

---

## Recovery Procedures

### Scenario 1: Single Device Rollback

**When:** VLAN change failed on one device

**Recovery Steps:**

1. **Find Latest Backup**
   ```bash
   ls -la backups/Switch-Core-01/
   # Pick most recent (or pre-change)
   ```

2. **Manual Restore**
   ```bash
   # SSH to device
   ssh admin@Switch-Core-01
   
   # For Cisco IOS
   copy tftp://your-server/backups/Switch-Core-01/config_20260414_143022.txt running-config
   
   # For Juniper
   load replace /var/tmp/config_backup.txt
   commit
   ```

3. **Verify Restoration**
   ```bash
   show vlan
   # Compare to expected state
   ```

---

### Scenario 2: Bulk Rollback

**When:** Bulk operation failed on multiple devices

**Recovery Steps:**

1. **Identify Affected Devices**
   ```bash
   # From session log
   grep "ERROR\|SUCCESS" app_session_log_*.txt
   ```

2. **Find Pre-Operation Backup**
   ```bash
   # Look for backups created just before operation
   ls -lt backups/ | head -20
   ```

3. **Batch Restore**
   ```bash
   # Create restore script
   for host in Switch-01 Switch-02 Switch-03; do
       echo "Restoring $host..."
       # Add restore commands here
   done
   ```

---

### Scenario 3: Complete Application Loss

**When:** Application deleted or corrupted

**Recovery Steps:**

1. **Preserve Critical Files**
   ```bash
   # Before any recovery, save these:
   cp inventory.txt /safe/location/
   cp -r backups/ /safe/location/
   cp -r config_backups_*/ /safe/location/
   ```

2. **Rebuild Application**
   ```bash
   # Follow prompts in order:
   # docs/prompts/P01-FOUNDATION.md through P10-BUILD.md
   ```

3. **Restore State**
   ```bash
   # Copy back critical files
   cp /safe/location/inventory.txt .
   cp -r /safe/location/backups/ .
   ```

4. **Verify**
   ```bash
   python -c "from modules import vlan_audit; print('OK')"
   python vlan_checker_web.py  # Test startup
   ```

---

### Scenario 4: Configuration Drift Recovery

**When:** Unknown changes were made to devices

**Recovery Steps:**

1. **Find Last Known Good**
   ```bash
   # From backups, find config from known-good date
   ls backups/Switch-Core-01/
   ```

2. **Compare Current vs Good**
   ```bash
   diff backups/Switch-Core-01/config_good.txt current_config.txt
   ```

3. **Selective Restore**
   - Don't blindly restore entire config
   - Identify specific sections that changed
   - Restore only necessary parts

---

## Git-Based Recovery

### Using Git for Version Control

**If using git (recommended):**

```bash
# Check status
git status

# See recent changes
git log --oneline -10

# Revert to last known good
git reset --hard HEAD~1

# Or revert specific file
git checkout HEAD -- modules/vlan_audit.py
```

### Commit Strategy

**Before major changes:**
```bash
git add .
git commit -m "Before feature X implementation"
```

**After successful implementation:**
```bash
git add .
git commit -m "Feature X complete and tested"
```

---

## Testing Recovery

### Monthly Recovery Test

**Procedure:**

1. **Pick Random Backup**
   ```bash
   ls backups/*/
   # Pick one config file
   ```

2. **Verify Backup Readable**
   ```bash
   head backups/Switch-01/config_*.txt
   # Should see valid config commands
   ```

3. **Test Restore Process**
   ```bash
   # In lab environment:
   # 1. Make a change
   # 2. Restore from backup
   # 3. Verify restored correctly
   ```

4. **Document Results**
   ```
   Recovery test: YYYY-MM-DD
   Backup tested: config_YYYYMMDD_HHMMSS.txt
   Result: SUCCESS/FAILURE
   Notes: ...
   ```

---

## Checklists

### Before Major Change

- [ ] Full config backup created
- [ ] Backup files readable (not corrupted)
- [ ] Git commit made ("Before X operation")
- [ ] Inventory file backed up
- [ ] Rollback procedure reviewed
- [ ] Maintenance window active
- [ ] Rollback team on standby

### After Change

- [ ] Verify change on all devices
- [ ] Run connectivity check
- [ ] Run VLAN audit (if VLAN change)
- [ ] Document what changed
- [ ] Update golden baseline (if new standard)
- [ ] Git commit ("After X operation - SUCCESS")

---

## Emergency Quick Commands

```bash
# Quick full backup
python main.py cli --task backup

# Check what backups exist
find backups/ -type f -name "*.txt" | head -10

# Check backup age
ls -lt backups/*/

# View backup content
head backups/Switch-Core-01/config_*.txt

# Copy backups to safe location
cp -r backups/ /external/storage/
```

---

## Best Practices

### DO:
- ✅ Backup before every change
- ✅ Test restore quarterly
- ✅ Keep backups off-device
- ✅ Name backups clearly (hostname + timestamp)
- ✅ Document what each backup contains

### DON'T:
- ❌ Rely solely on automatic backups
- ❌ Keep only one backup copy
- ❌ Store backups only on the tool's machine
- ❌ Skip verification
- ❌ Forget to backup inventory.txt

---

## Summary

**Remember:**
1. **Backup is cheap, recovery is expensive**
2. **Untested backup = no backup**
3. **Multiple copies = peace of mind**
4. **Document everything**

**Your backups are your safety net. Treat them with respect.**

# AI Behavior Guide for Network Swiss Tool Pro

> **How AI should think, code, and behave when building this application**

---

## 🧠 Core Philosophy

### Think Like a Network Engineer First, Developer Second

1. **Safety Above All** - One bad command can take down a network
2. **Visibility is Critical** - Log everything, show everything
3. **Errors are Isolated** - One device failure doesn't cascade
4. **Dry-Run is Default** - Never surprise the operator

---

## 🎯 Decision Making Framework

### When Making ANY Code Change, Ask:

1. **Could this break a network device?**
   - YES → Add dry-run mode first
   - YES → Add backup/rollback capability
   - YES → Add explicit confirmation

2. **Will the operator know what's happening?**
   - NO → Add logging
   - NO → Add progress indicators
   - NO → Add result summaries

3. **What if this fails halfway through?**
   - Need cleanup → Add try-finally
   - Need recovery → Add rollback
   - Need audit → Add logging

---

## 📝 Coding Standards

### 1. Function Signatures

**Always include logging function:**
```python
# ✅ CORRECT
def run(device, user, pwd, enb_pwd, log_func=None):
    """Execute operation with optional logging."""
    if log_func:
        log_func(f"[{device['host']}] Starting operation...")

# ❌ WRONG
def run(device, user, pwd, enb_pwd):
    """No visibility into what's happening."""
```

### 2. Return Contract

**Always return standardized dict:**
```python
# ✅ CORRECT
return {
    "status": "success" | "fail",
    "data": {
        "true_host": hostname,
        "results": [...]
    },
    "error": "..."  # Only if fail
}

# ❌ WRONG
return True  # Or return None, or raise exception
```

### 3. Connection Handling

**Always use try-finally for connections:**
```python
# ✅ CORRECT
conn = None
try:
    if log_func:
        log_func(f"[{host}] Connecting...")
    conn = connect_permissive(device, user, pwd, enb_pwd)
    # ... do work ...
    if log_func:
        log_func(f"[{host}] Disconnecting...")
    conn.disconnect()
    conn = None
    return build_json(host, "success", data)
except Exception as e:
    return build_json(host, "fail", {}, str(e))
finally:
    if conn:
        try:
            conn.disconnect()
        except:
            pass

# ❌ WRONG
conn = connect_permissive(device, user, pwd, enb_pwd)
output = conn.send_command("show vlan")
conn.disconnect()
# What if exception? Connection leaks!
```

### 4. Error Handling

**Three-layer approach:**
```python
# Layer 1: Module (per-device)
try:
    result = operation()
    return {"status": "success", "data": result}
except Exception as e:
    return {"status": "fail", "error": str(e)}

# Layer 2: Adapter (per-batch)
for dev in devices:
    res = module.run(dev, ...)
    if res['status'] == 'fail':
        log(f"[ERROR] {dev['host']}: {res['error']}")
        # Continue to next device!

# Layer 3: Thread (critical)
try:
    adapters.run_operation(devices, ...)
except Exception as e:
    log(f"[CRITICAL ERROR] {str(e)}")
    log(traceback.format_exc())
```

### 5. Documentation

**Every function gets a docstring:**
```python
def run(device, user, pwd, enb_pwd, log_func=None):
    """Execute operation on device.
    
    Args:
        device: Dict with 'host', 'device_type', 'port'
        user: SSH username
        pwd: SSH password
        enb_pwd: Enable password (optional)
        log_func: Logging callback function (optional)
    
    Returns:
        Dict with 'status', 'data', 'error'
    
    Example:
        >>> result = run({'host': '10.1.1.1', 'device_type': 'cisco_ios'}, 
        ...              'admin', 'pass', '', log_func=print)
        >>> print(result['status'])
        'success'
    """
```

---

## 🔄 Workflow Patterns

### When Adding a New Feature:

**Step-by-step:**
1. **Design the user flow** - How will operator use this?
2. **Design the module** - Core logic in `modules/my_feature.py`
3. **Add adapter function** - Orchestration in `modules/adapters.py`
4. **Add web thread** - Thread function in `vlan_checker_web.py`
5. **Add UI element** - Button/form in `index.html`
6. **Test dry-run first** - Always!
7. **Add to documentation** - Update docs/

### When Fixing a Bug:

**Step-by-step:**
1. **Reproduce the bug** - Understand the failure
2. **Add logging** - Where did it fail? Why?
3. **Fix with minimal change** - Don't refactor while fixing
4. **Test the fix** - Verify it works
5. **Test for regressions** - Did you break anything else?
6. **Document the fix** - Update CHANGELOG.md

---

## 🧪 Testing Philosophy

### Levels of Testing

1. **Import Test** (Always)
   ```bash
   python -c "from modules import X; print('OK')"
   ```

2. **Dry-Run Test** (For write operations)
   - Run with dry_run=True
   - Verify commands that would be sent
   - Check no actual changes made

3. **Single Device Test** (Before batch)
   - Test on 1 device first
   - Verify output correct
   - Then scale to batch

4. **Rollback Test** (For write operations)
   - Make a change
   - Verify it worked
   - Rollback
   - Verify rolled back

### Test Devices

**Always have test devices:**
- Lab switch (not production)
- Or: First device in inventory is lab
- Or: "--test-mode" flag for simulation

---

## 🎨 UI/UX Guidelines

### Web Interface Principles

1. **Progress Visibility**
   - Show current operation
   - Show device being processed
   - Show completion percentage

2. **Result Clarity**
   - ✅ Green for success
   - ⚠️ Yellow for warnings
   - ❌ Red for errors
   - Summary at end

3. **Safety Controls**
   - Dry-run checkbox (checked by default)
   - Confirmation for destructive ops
   - "Stop" button for long operations

4. **Log Accessibility**
   - Real-time log streaming
   - Download session log button
   - Copy-to-clipboard button

### Log Message Format

**Standard format:**
```
[timestamp] [hostname] [STATUS] Message
```

**Examples:**
```
[14:32:01] [10.1.1.1] Connecting...
[14:32:03] [10.1.1.1] Connected successfully
[14:32:04] [10.1.1.1] Executing: show vlan
[14:32:05] [10.1.1.1] Command completed
[14:32:06] [10.1.1.1] Found 42 VLANs
[14:32:07] [10.1.1.1] Disconnecting...
[14:32:08] [10.1.1.1] Disconnected
```

---

## 🔒 Security Guidelines

### Credential Handling

1. **Never log credentials**
   ```python
   # ✅ CORRECT
   log(f"Connecting to {host} as {username}")
   # NOT: log(f"Connecting with password {password}")
   ```

2. **Never store credentials in reports**
   ```python
   # In report generation
   config_output = config_output.replace(pwd, '***REDACTED***')
   ```

3. **Session logs are local only**
   - No cloud uploading
   - No remote logging servers
   - User controls log retention

### Network Safety

1. **Read-only first** - Audit before modify
2. **Dry-run default** - Preview before execute
3. **Backup before change** - Always
4. **Verification after change** - Confirm success
5. **Rollback on failure** - Automatic if possible

---

## 📊 Performance Guidelines

### Optimization Rules

1. **Don't optimize prematurely**
   - Working code > fast code
   - 5 seconds per device is acceptable

2. **Connection reuse where safe**
   ```python
   # If doing multiple commands on same device:
   conn = connect(device)
   try:
       for cmd in commands:
           output = conn.send_command(cmd)
   finally:
       conn.disconnect()
   ```

3. **Don't hold all data in memory**
   - Stream to files
- Process one device at a time
   - Clear log queue periodically

4. **Thread safety**
   - One thread per operation (not per device)
   - Avoid shared mutable state
   - Use daemon threads

---

## 🆘 Emergency Procedures

### When Something Goes Wrong

**If a network device stops responding:**
1. Don't panic
2. Check if it's just one device or many
3. Check physical connections
4. Use console access if available
5. Consider rollback from backup

**If the application crashes:**
1. Check session log file
2. Check exception in console
3. Restart application
4. Re-run operation (dry-run first!)

**If you need to rollback:**
```bash
# Use the backup file created before change
cp backups/Switch-Core-01/config_20260414_143022.txt restore.txt
# Then manually restore or use restore function
```

---

## 📝 Documentation Requirements

### Every Code Change Must Include:

1. **Code comments** - Why, not what
2. **Docstrings** - Function purpose, args, returns
3. **CHANGELOG entry** - What changed, why
4. **Test notes** - How it was tested

### Documentation Files to Maintain:

| File | When to Update |
|------|----------------|
| `CHANGELOG.md` | Every change |
| `docs/03-MODULE-REFERENCE.md` | New module or API change |
| `docs/prompts/*.md` | New rebuild procedure |
| `README.md` | User-facing changes |

---

## ✅ Checklist Before Commit

- [ ] Code follows style guide
- [ ] Docstrings added
- [ ] Error handling complete (3 layers)
- [ ] Logging added
- [ ] Dry-run mode works (if write operation)
- [ ] Tested on at least 1 device
- [ ] No credentials in code or logs
- [ ] CHANGELOG.md updated
- [ ] Documentation updated

---

## 🎯 Success Metrics

### How to Know You've Done Good Work:

1. **Operator can see everything** - Full visibility
2. **Failures are isolated** - One device ≠ all devices
3. **Recovery is possible** - Rollback works
4. **Code is readable** - Comments and docs
5. **Tests pass** - Manual verification complete

---

## 📚 Learning Resources

### Network Engineering Concepts to Understand:

1. **SSH vs Telnet** - Always use SSH
2. **Enable mode** - Privileged commands require it
3. **Running vs Startup config** - Change ≠ Persist
4. **VLAN basics** - Tagged/untagged, trunk/access
5. **CDP/LLDP** - Neighbor discovery
6. **MAC table** - Switch forwarding

### Python Patterns to Know:

1. **Context managers** - `with` statement
2. **Exception handling** - try-except-finally
3. **Threading** - Thread, Queue, Lock
4. **JSON** - Dictionaries as data structure
5. **Regex** - Pattern matching for CLI output

---

**Remember:** This tool manages production networks. Act accordingly.

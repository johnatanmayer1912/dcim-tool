# Advanced Debugging Guide

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Status** | active |
| **Owner** | System Architect (R-ARCH) + QA Engineer (R-QA) |
| **Last Updated** | 2026-06-02 |
| **Application Version** | 7.0.10 |

---

## Overview

This document provides comprehensive advanced debugging techniques and troubleshooting procedures for Network Swiss Tool Pro, including diagnostic tools, debugging strategies, common issues, and resolution procedures.

---

## Debugging Tools

### 1. Python Debugger (pdb)

**Purpose:** Interactive debugging of Python code

**Usage:**
```python
import pdb

def debug_function():
    pdb.set_trace()  # Set breakpoint
    # Code to debug
    result = perform_operation()
    return result
```

**Common pdb Commands:**
- `n` - Next line
- `s` - Step into function
- `c` - Continue execution
- `p variable` - Print variable value
- `pp variable` - Pretty print variable
- `l` - List code around current line
- `b line_number` - Set breakpoint
- `b function_name` - Set breakpoint at function
- `cl` - Clear all breakpoints
- `q` - Quit debugger

---

### 2. Logging Configuration

**Purpose:** Configure detailed logging for debugging

**Implementation:**
```python
import logging

def setup_debug_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('debug.log'),
            logging.StreamHandler()
        ]
    )
    
    # Set specific logger levels
    logging.getLogger('paramiko').setLevel(logging.DEBUG)
    logging.getLogger('netmiko').setLevel(logging.DEBUG)
    logging.getLogger('flask').setLevel(logging.DEBUG)
```

**Log Levels:**
- DEBUG - Detailed diagnostic information
- INFO - General informational messages
- WARNING - Warning messages for potential issues
- ERROR - Error messages for failures
- CRITICAL - Critical errors requiring immediate attention

---

### 3. Memory Profiling

**Purpose:** Identify memory leaks and memory usage patterns

**Tool:** memory_profiler

**Usage:**
```python
from memory_profiler import profile

@profile
def memory_intensive_operation():
    data = load_large_dataset()
    process_data(data)
    return result
```

**Execution:**
```bash
python -m memory_profiler script.py
```

---

### 4. CPU Profiling

**Purpose:** Identify CPU bottlenecks and performance issues

**Tool:** cProfile

**Usage:**
```python
import cProfile

def profile_operation():
    cProfile.run('operation()')
```

**Execution:**
```bash
python -m cProfile -s cumtime script.py
```

---

### 5. Thread Debugging

**Purpose:** Debug threading issues and race conditions

**Tool:** threading module with logging

**Implementation:**
```python
import threading
import logging

logging.basicConfig(level=logging.DEBUG)

def debug_thread_operation():
    thread_id = threading.get_ident()
    logging.debug(f"Thread {thread_id} starting")
    
    # Operation code
    result = perform_operation()
    
    logging.debug(f"Thread {thread_id} completed")
    return result
```

---

## Diagnostic Procedures

### 1. Connection Issues

**Symptoms:**
- Connection timeout
- Authentication failure
- Connection dropped mid-operation
- Slow connection establishment

**Diagnostic Steps:**
1. Verify network connectivity
```bash
ping <device_ip>
telnet <device_ip> 22
```

2. Check device accessibility
```python
from netmiko import ConnectHandler

device = {
    'device_type': 'cisco_ios',
    'host': '10.1.1.1',
    'username': 'admin',
    'password': 'password'
}

try:
    conn = ConnectHandler(**device)
    print("Connection successful")
    conn.disconnect()
except Exception as e:
    print(f"Connection failed: {e}")
```

3. Enable debug logging
```python
logging.getLogger('paramiko').setLevel(logging.DEBUG)
logging.getLogger('netmiko').setLevel(logging.DEBUG)
```

4. Check firewall rules
- Verify SSH port (22) is open
- Check for network ACLs
- Verify no rate limiting

**Resolution:**
- Verify credentials
- Check device status
- Increase timeout values
- Use connection pooling
- Implement retry logic

---

### 2. Plugin Loading Issues

**Symptoms:**
- Plugin fails to load
- Import errors
- Validation errors
- Plugin not appearing in list

**Diagnostic Steps:**
1. Check plugin metadata
```python
import importlib

plugin_module = importlib.import_module('modules.plugins.network_discovery')
print(plugin_module.METADATA)
```

2. Validate plugin structure
```python
from plugin_registry import PluginRegistry

registry = PluginRegistry()
errors = registry.get_errors()
print(f"Plugin errors: {errors}")
```

3. Check dependencies
```python
import sys
print(f"Python path: {sys.path}")
```

4. Enable plugin debug logging
```python
logging.getLogger('plugin_registry').setLevel(logging.DEBUG)
```

**Resolution:**
- Fix METADATA structure
- Install missing dependencies
- Check Python path
- Validate plugin code
- Use plugin backup/restore

---

### 3. Performance Issues

**Symptoms:**
- Slow operation execution
- High CPU usage
- High memory usage
- Timeout errors

**Diagnostic Steps:**
1. Profile operation
```python
import cProfile

def profile_slow_operation():
    cProfile.run('slow_operation()', sort='cumtime')
```

2. Monitor memory usage
```python
import psutil

def monitor_memory():
    process = psutil.Process()
    print(f"Memory usage: {process.memory_info().rss / 1024 / 1024} MB")
```

3. Check thread count
```python
import threading

print(f"Active threads: {threading.active_count()}")
for thread in threading.enumerate():
    print(f"Thread: {thread.name}")
```

4. Monitor network I/O
```python
import psutil

def monitor_network():
    net_io = psutil.net_io_counters()
    print(f"Bytes sent: {net_io.bytes_sent}")
    print(f"Bytes received: {net_io.bytes_recv}")
```

**Resolution:**
- Optimize slow operations
- Implement caching
- Use connection pooling
- Process data in chunks
- Implement lazy loading

---

### 4. Data Parsing Issues

**Symptoms:**
- Parsing errors
- Incorrect data extraction
- Missing fields
- Type conversion errors

**Diagnostic Steps:**
1. Check raw output
```python
output = conn.send_command('show interface')
print(f"Raw output:\n{output}")
```

2. Test parsing
```python
from textfsm import TextFSM

template = TextFSM(open('template.textfsm'))
parsed = template.ParseText(output)
print(f"Parsed data: {parsed}")
```

3. Validate data structure
```python
def validate_parsed_data(data):
    if not isinstance(data, list):
        print("Expected list, got", type(data))
        return False
    
    for item in data:
        if not isinstance(item, dict):
            print("Expected dict, got", type(item))
            return False
    
    return True
```

**Resolution:**
- Update TextFSM templates
- Handle edge cases
- Add fallback parsing
- Validate output structure
- Log parsing errors

---

### 5. WebSocket Issues

**Symptoms:**
- Connection drops
- Message not received
- Session timeout
- PTY errors

**Diagnostic Steps:**
1. Check WebSocket connection
```python
from flask_socketio import SocketIO

socketio = SocketIO()
print(f"SocketIO initialized: {socketio}")
```

2. Monitor session status
```python
def check_session_status(session_id):
    session = cli_sessions.get(session_id)
    if session:
        print(f"Session status: {session['status']}")
        print(f"Last activity: {session['last_activity']}")
    else:
        print("Session not found")
```

3. Enable WebSocket debug logging
```python
logging.getLogger('engineio').setLevel(logging.DEBUG)
logging.getLogger('socketio').setLevel(logging.DEBUG)
```

**Resolution:**
- Implement keepalive messages
- Increase session timeout
- Handle connection drops
- Validate PTY allocation
- Monitor session health

---

## Advanced Debugging Techniques

### 1. Conditional Breakpoints

**Purpose:** Break only when specific condition is met

**Implementation:**
```python
import pdb

def debug_with_condition(data):
    for item in data:
        if item['status'] == 'error':
            pdb.set_trace()  # Break only on error
        process_item(item)
```

---

### 2. Post-Mortem Debugging

**Purpose:** Debug after exception occurs

**Implementation:**
```python
import pdb
import sys

def debug_post_mortem():
    try:
        operation_that_might_fail()
    except Exception:
        pdb.post_mortem(sys.exc_info()[2])
```

---

### 3. Remote Debugging

**Purpose:** Debug running application remotely

**Tool:** rpdb (remote pdb)

**Implementation:**
```python
import rpdb

def debug_remote():
    rpdb.set_trace(host='0.0.0.0', port=4444)
    # Code to debug
    result = perform_operation()
    return result
```

**Connection:**
```bash
telnet localhost 4444
```

---

### 4. Trace Function Calls

**Purpose:** Trace function execution flow

**Implementation:**
```python
import sys

def trace_calls(frame, event, arg):
    if event == 'call':
        func_name = frame.f_code.co_name
        filename = frame.f_code.co_filename
        print(f"Calling: {func_name} in {filename}")
    return trace_calls

sys.settrace(trace_calls)
```

---

### 5. Memory Leak Detection

**Purpose:** Detect memory leaks in long-running processes

**Tool:** tracemalloc

**Implementation:**
```python
import tracemalloc

tracemalloc.start()

# Run operation
operation()

# Get memory snapshot
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

for stat in top_stats[:10]:
    print(stat)
```

---

## Common Issues and Solutions

### Issue 1: Device Connection Timeout

**Symptoms:** Connection timeout after 30 seconds

**Diagnosis:**
1. Check network connectivity
2. Verify device is reachable
3. Check firewall rules
4. Verify credentials

**Solution:**
```python
# Increase timeout
device = {
    'device_type': 'cisco_ios',
    'host': '10.1.1.1',
    'username': 'admin',
    'password': 'password',
    'timeout': 60  # Increase to 60 seconds
}

# Or use permissive connection
conn = ConnectHandler(**device, global_delay_factor=2)
```

---

### Issue 2: Plugin Not Loading

**Symptoms:** Plugin not appearing in plugin list

**Diagnosis:**
1. Check plugin METADATA
2. Validate plugin structure
3. Check for import errors
4. Verify dependencies

**Solution:**
```python
# Check plugin errors
registry = PluginRegistry()
errors = registry.get_errors()

for plugin_id, error in errors.items():
    print(f"Plugin {plugin_id}: {error}")

# Reload plugins
registry.discover_plugins()
```

---

### Issue 3: Memory Exhaustion

**Symptoms:** Application crashes with out of memory error

**Diagnosis:**
1. Monitor memory usage
2. Profile memory allocation
3. Check for memory leaks
4. Identify large data structures

**Solution:**
```python
# Process data in chunks
def process_large_data(data, chunk_size=100):
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i+chunk_size]
        process_chunk(chunk)
        del chunk  # Free memory

# Use generators
def generate_data():
    for item in large_dataset:
        yield process_item(item)
```

---

### Issue 4: Thread Deadlock

**Symptoms:** Application hangs, threads blocked

**Diagnosis:**
1. Monitor thread status
2. Check lock acquisition
3. Identify circular dependencies
4. Review lock ordering

**Solution:**
```python
# Use lock timeout
lock = threading.Lock()

def safe_acquire(lock, timeout=30):
    acquired = lock.acquire(timeout=timeout)
    if not acquired:
        raise TimeoutError("Lock acquisition timeout")
    return acquired

# Always acquire locks in same order
def operation_with_locks():
    with lock1:
        with lock2:
            # Critical section
            pass
```

---

### Issue 5: Configuration File Not Found

**Symptoms:** Application cannot find configuration file

**Diagnosis:**
1. Check file path
2. Verify file exists
3. Check file permissions
4. Validate file format

**Solution:**
```python
import os

def get_config_path():
    # Check multiple possible locations
    possible_paths = [
        'config.yaml',
        '/etc/network-tool/config.yaml',
        os.path.expanduser('~/.network-tool/config.yaml')
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    raise FileNotFoundError("Configuration file not found")
```

---

## Troubleshooting Procedures

### Procedure 1: Application Startup Failure

**Steps:**
1. Check Python version compatibility
```bash
python --version
# Should be Python 3.8+
```

2. Verify dependencies installed
```bash
pip list
```

3. Check for missing dependencies
```bash
pip install -r requirements.txt
```

4. Check configuration files
```bash
ls -la config/
cat config.yaml
```

5. Check log files
```bash
tail -f logs/application.log
```

6. Run in debug mode
```bash
python vlan_checker_web.py --debug
```

---

### Procedure 2: Device Operation Failure

**Steps:**
1. Verify device connectivity
```bash
ping <device_ip>
telnet <device_ip> 22
```

2. Test manual connection
```python
from netmiko import ConnectHandler

device = {
    'device_type': 'cisco_ios',
    'host': '10.1.1.1',
    'username': 'admin',
    'password': 'password'
}

conn = ConnectHandler(**device)
output = conn.send_command('show version')
print(output)
conn.disconnect()
```

3. Check device logs
```python
output = conn.send_command('show logging')
print(output)
```

4. Verify device resources
```python
output = conn.send_command('show processes cpu')
print(output)
```

5. Test with different device type
```python
device['device_type'] = 'cisco_nxos'
conn = ConnectHandler(**device)
```

---

### Procedure 3: Plugin Execution Failure

**Steps:**
1. Check plugin metadata
```python
import importlib

plugin = importlib.import_module('modules.plugins.network_discovery')
print(plugin.METADATA)
```

2. Test plugin in isolation
```python
from modules.plugins.network_discovery import run

result = run(device, credentials, params, config, log_func)
print(result)
```

3. Check plugin dependencies
```python
import sys
print(sys.path)
```

4. Validate plugin code
```python
import ast

with open('modules/plugins/network_discovery.py') as f:
    code = f.read()
    ast.parse(code)  # Will raise syntax error if invalid
```

5. Check plugin logs
```bash
tail -f logs/plugins.log
```

---

### Procedure 4: Performance Degradation

**Steps:**
1. Profile operation
```python
import cProfile

cProfile.run('operation()', sort='cumtime')
```

2. Monitor resource usage
```python
import psutil

process = psutil.Process()
print(f"CPU: {process.cpu_percent()}%")
print(f"Memory: {process.memory_info().rss / 1024 / 1024} MB")
```

3. Check thread count
```python
import threading

print(f"Active threads: {threading.active_count()}")
```

4. Monitor network I/O
```python
import psutil

net_io = psutil.net_io_counters()
print(f"Bytes sent: {net_io.bytes_sent}")
print(f"Bytes received: {net_io.bytes_recv}")
```

5. Check for memory leaks
```python
import tracemalloc

tracemalloc.start()
operation()
snapshot = tracemalloc.take_snapshot()
print(snapshot.statistics('lineno'))
```

---

## Debugging Checklist

### Pre-Debugging Checklist

- [ ] Reproduce the issue consistently
- [ ] Identify the exact error message
- [ ] Note the steps to reproduce
- [ ] Check recent changes
- [ ] Review error logs
- [ ] Verify environment configuration

### During Debugging Checklist

- [ ] Enable debug logging
- [ ] Set breakpoints at key points
- [ ] Monitor variable values
- [ ] Check function call stack
- [ ] Verify data structures
- [ ] Test with sample data

### Post-Debugging Checklist

- [ ] Verify fix resolves issue
- [ ] Test edge cases
- [ ] Update documentation
- [ ] Add regression test
- [ ] Review code changes
- [ ] Commit with descriptive message

---

## Debugging Best Practices

### 1. Reproduce Issues

**Best Practice:** Always reproduce issues before fixing

**Implementation:**
```python
def reproduce_issue():
    # Exact steps to reproduce
    device = get_test_device()
    credentials = get_test_credentials()
    operation = get_problematic_operation()
    
    result = execute_operation(device, credentials, operation)
    assert result['status'] == 'error'  # Should fail
    return result
```

---

### 2. Isolate Variables

**Best Practice:** Test with minimal variables

**Implementation:**
```python
def test_with_minimal_data():
    # Test with single device instead of many
    device = get_single_device()
    result = execute_operation(device)
    return result
```

---

### 3. Use Logging

**Best Practice:** Add logging at key points

**Implementation:**
```python
import logging

logger = logging.getLogger(__name__)

def operation_with_logging(data):
    logger.debug(f"Starting operation with {len(data)} items")
    
    for item in data:
        logger.debug(f"Processing item: {item}")
        result = process_item(item)
        logger.debug(f"Result: {result}")
    
    logger.debug("Operation completed")
    return results
```

---

### 4. Test Incrementally

**Best Practice:** Test small changes incrementally

**Implementation:**
```python
def test_incremental_fix():
    # Test fix on small dataset
    small_data = get_small_dataset()
    result = operation(small_data)
    assert result['status'] == 'success'
    
    # Test on medium dataset
    medium_data = get_medium_dataset()
    result = operation(medium_data)
    assert result['status'] == 'success'
    
    # Test on full dataset
    full_data = get_full_dataset()
    result = operation(full_data)
    assert result['status'] == 'success'
```

---

### 5. Document Findings

**Best Practice:** Document debugging findings

**Implementation:**
```python
"""
Debugging Session: Issue #123
Date: 2026-06-02
Issue: Connection timeout on device 10.1.1.1

Findings:
- Device is reachable via ping
- SSH port 22 is open
- Authentication succeeds
- Command execution times out

Root Cause:
- Device has slow command response time
- Default timeout of 30 seconds is insufficient

Solution:
- Increase timeout to 60 seconds for this device
- Implement adaptive timeout based on device response time

Testing:
- Tested with 60 second timeout: Success
- Tested with 30 second timeout: Failure
"""
```

---

## References

- ERROR_HANDLING_DOCUMENTATION.md - Error handling and recovery
- PERFORMANCE_OPTIMIZATION.md - Performance optimization strategies
- CONCURRENCY_DOCUMENTATION.md - Concurrency and race conditions
- PLATFORM_SPECIFIC_OPTIMIZATIONS.md - Platform-specific optimizations

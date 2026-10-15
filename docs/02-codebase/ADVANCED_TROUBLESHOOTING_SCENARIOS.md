# Advanced Troubleshooting Scenarios

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Status** | active |
| **Owner** | System Architect (R-ARCH) + QA Engineer (R-QA) |
| **Last Updated** | 2026-06-02 |
| **Application Version** | 7.0.10 |

---

## Overview

This document provides comprehensive advanced troubleshooting scenarios for Network Swiss Tool Pro, including complex issues, multi-step resolution procedures, and recovery strategies for critical failures.

---

## Scenario 1: Complete Network Outage

### Symptoms
- All devices unreachable
- Connection timeouts for all operations
- Application appears unresponsive
- No logs being generated

### Diagnosis Steps

**Step 1: Verify Application Status**
```python
import psutil

def check_application_status():
    try:
        process = psutil.Process(pid)
        return {
            'status': 'running',
            'cpu_percent': process.cpu_percent(),
            'memory_mb': process.memory_info().rss / 1024 / 1024
        }
    except psutil.NoSuchProcess:
        return {'status': 'not_running'}
```

**Step 2: Check Network Connectivity**
```python
import socket

def check_network_connectivity():
    test_hosts = ['8.8.8.8', '1.1.1.1', 'localhost']
    results = {}
    
    for host in test_hosts:
        try:
            socket.create_connection((host, 53), timeout=5)
            results[host] = 'reachable'
        except:
            results[host] = 'unreachable'
    
    return results
```

**Step 3: Check Firewall Rules**
```bash
# Check Windows Firewall
netsh advfirewall show allprofiles

# Check Linux firewall
sudo iptables -L -n
```

**Step 4: Check DNS Resolution**
```python
import socket

def check_dns_resolution(hostname):
    try:
        ip = socket.gethostbyname(hostname)
        return {'status': 'resolved', 'ip': ip}
    except socket.gaierror:
        return {'status': 'failed', 'error': 'DNS resolution failed'}
```

### Resolution Procedure

**Resolution 1: Restart Application**
```python
def restart_application():
    # Stop application
    stop_application()
    
    # Wait for cleanup
    time.sleep(5)
    
    # Start application
    start_application()
    
    # Verify startup
    return verify_application_health()
```

**Resolution 2: Check Network Configuration**
```bash
# Check IP configuration
ipconfig /all  # Windows
ifconfig      # Linux

# Check routing table
route print    # Windows
route -n       # Linux

# Reset network adapter
netsh interface reset
```

**Resolution 3: Clear DNS Cache**
```bash
# Windows
ipconfig /flushdns

# Linux
sudo systemctl restart systemd-resolved
```

**Resolution 4: Check Proxy Settings**
```python
import os

def check_proxy_settings():
    proxies = {
        'http': os.environ.get('HTTP_PROXY'),
        'https': os.environ.get('HTTPS_PROXY'),
        'no_proxy': os.environ.get('NO_PROXY')
    }
    return proxies
```

### Prevention Measures
- Implement network health monitoring
- Add automatic failover mechanisms
- Configure network redundancy
- Implement circuit breaker pattern

---

## Scenario 2: Database Corruption

### Symptoms
- Application crashes on startup
- Data inconsistencies in reports
- Error messages about database corruption
- Slow query performance

### Diagnosis Steps

**Step 1: Check Database Integrity**
```python
import sqlite3

def check_database_integrity(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('PRAGMA integrity_check')
        result = cursor.fetchone()
        return {'status': 'ok' if result[0] == 'ok' else 'corrupted', 'details': result}
    except sqlite3.DatabaseError as e:
        return {'status': 'error', 'error': str(e)}
    finally:
        conn.close()
```

**Step 2: Check Database Size**
```python
import os

def check_database_size(db_path):
    size_bytes = os.path.getsize(db_path)
    size_mb = size_bytes / 1024 / 1024
    return {'size_bytes': size_bytes, 'size_mb': size_mb}
```

**Step 3: Check Database Lock Status**
```python
def check_database_lock(db_path):
    try:
        conn = sqlite3.connect(db_path, timeout=1)
        conn.close()
        return {'status': 'unlocked'}
    except sqlite3.OperationalError:
        return {'status': 'locked'}
```

### Resolution Procedure

**Resolution 1: Restore from Backup**
```python
def restore_database_from_backup(db_path, backup_path):
    # Stop application
    stop_application()
    
    # Backup current corrupted database
    backup_corrupted(db_path)
    
    # Restore from backup
    import shutil
    shutil.copy(backup_path, db_path)
    
    # Verify integrity
    integrity = check_database_integrity(db_path)
    
    # Start application
    start_application()
    
    return integrity
```

**Resolution 2: Repair Database**
```python
def repair_database(db_path):
    # Create backup
    backup_path = f"{db_path}.backup"
    shutil.copy(db_path, backup_path)
    
    # Attempt repair
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('PRAGMA integrity_check')
        result = cursor.fetchone()
        
        if result[0] != 'ok':
            # Dump and reload
            dump_file = f"{db_path}.dump"
            with open(dump_file, 'w') as f:
                for line in conn.iterdump():
                    f.write(f"{line}\n")
            
            conn.close()
            
            # Create new database
            new_db = sqlite3.connect(db_path)
            with open(dump_file, 'r') as f:
                sql = f.read()
                new_db.executescript(sql)
            new_db.close()
            
            return {'status': 'repaired'}
    except Exception as e:
        return {'status': 'failed', 'error': str(e)}
    finally:
        conn.close()
```

**Resolution 3: Rebuild Database**
```python
def rebuild_database(db_path, schema_file):
    # Stop application
    stop_application()
    
    # Backup current database
    backup_path = f"{db_path}.backup"
    shutil.copy(db_path, backup_path)
    
    # Delete corrupted database
    os.remove(db_path)
    
    # Create new database from schema
    conn = sqlite3.connect(db_path)
    with open(schema_file, 'r') as f:
        schema = f.read()
        conn.executescript(schema)
    conn.close()
    
    # Start application
    start_application()
    
    return {'status': 'rebuilt'}
```

### Prevention Measures
- Implement regular database backups
- Add database integrity checks
- Use transaction isolation
- Implement database monitoring

---

## Scenario 3: Memory Leak

### Symptoms
- Application memory usage increases over time
- Application becomes sluggish
- Eventually crashes with out of memory error
- Performance degrades progressively

### Diagnosis Steps

**Step 1: Monitor Memory Usage**
```python
import psutil
import time

def monitor_memory_usage(duration=60, interval=5):
    process = psutil.Process()
    memory_samples = []
    
    for _ in range(duration // interval):
        memory_mb = process.memory_info().rss / 1024 / 1024
        memory_samples.append(memory_mb)
        time.sleep(interval)
    
    return {
        'samples': memory_samples,
        'min': min(memory_samples),
        'max': max(memory_samples),
        'avg': sum(memory_samples) / len(memory_samples),
        'trend': 'increasing' if memory_samples[-1] > memory_samples[0] * 1.5 else 'stable'
    }
```

**Step 2: Profile Memory Allocation**
```python
import tracemalloc

def profile_memory_allocation():
    tracemalloc.start()
    
    # Run operation
    operation()
    
    # Get snapshot
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')
    
    return top_stats[:10]
```

**Step 3: Check for Circular References**
```python
import gc

def check_circular_references():
    gc.collect()
    referrers = gc.get_referrers()
    circular = gc.collect()
    
    return {
        'referrers_count': len(referrers),
        'circular_references': circular
    }
```

### Resolution Procedure

**Resolution 1: Clear Caches**
```python
def clear_caches():
    # Clear connection pool
    connection_pool.clear()
    
    # Clear data caches
    device_cache.clear()
    plugin_cache.clear()
    
    # Clear result caches
    result_cache.clear()
    
    # Force garbage collection
    gc.collect()
    
    return {'status': 'caches_cleared'}
```

**Resolution 2: Restart Application**
```python
def restart_application():
    # Graceful shutdown
    shutdown_application()
    
    # Wait for cleanup
    time.sleep(10)
    
    # Start application
    start_application()
    
    return {'status': 'restarted'}
```

**Resolution 3: Implement Memory Limits**
```python
import resource

def set_memory_limit(limit_mb):
    limit_bytes = limit_mb * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
```

### Prevention Measures
- Implement memory monitoring
- Use weak references
- Clear caches periodically
- Implement memory limits
- Use generators instead of lists

---

## Scenario 4: Thread Deadlock

### Symptoms
- Application hangs
- No response to user input
- CPU usage near 0%
- Threads blocked indefinitely

### Diagnosis Steps

**Step 1: Check Thread Status**
```python
import threading

def check_thread_status():
    threads = threading.enumerate()
    thread_info = []
    
    for thread in threads:
        thread_info.append({
            'name': thread.name,
            'alive': thread.is_alive(),
            'daemon': thread.daemon
        })
    
    return thread_info
```

**Step 2: Check Lock Status**
```python
def check_lock_status():
    locks = []
    
    for thread in threading.enumerate():
        if hasattr(thread, '_lock'):
            locks.append({
                'thread': thread.name,
                'locked': thread._lock.locked()
            })
    
    return locks
```

**Step 3: Enable Thread Debugging**
```python
import sys
import traceback

def enable_thread_debugging():
    def thread_excepthook(args):
        print(f"Thread {args.thread.name} failed")
        traceback.print_exception(args.exc_type, args.exc_value, args.exc_traceback)
    
    threading.excepthook = thread_excepthook
```

### Resolution Procedure

**Resolution 1: Kill Deadlocked Threads**
```python
def kill_deadlocked_threads():
    for thread in threading.enumerate():
        if thread.name.startswith('worker') and thread.is_alive():
            # Note: Cannot forcibly kill threads in Python
            # Need to implement graceful shutdown
            signal_shutdown(thread)
```

**Resolution 2: Implement Lock Timeouts**
```python
def acquire_with_timeout(lock, timeout=30):
    acquired = lock.acquire(timeout=timeout)
    if not acquired:
        raise TimeoutError("Lock acquisition timeout")
    return acquired
```

**Resolution 3: Restart Application**
```python
def restart_application():
    # Force kill
    os.kill(os.getpid(), signal.SIGTERM)
```

### Prevention Measures
- Use lock timeouts
- Implement lock ordering
- Use reentrant locks
- Monitor lock contention
- Implement deadlock detection

---

## Scenario 5: Plugin System Failure

### Symptoms
- Plugins fail to load
- Plugin execution errors
- Plugin registry corruption
- Plugin metadata validation failures

### Diagnosis Steps

**Step 1: Check Plugin Registry**
```python
from plugin_registry import PluginRegistry

def check_plugin_registry():
    registry = PluginRegistry()
    
    return {
        'plugin_count': len(registry.plugins),
        'errors': registry.get_errors(),
        'loaded_plugins': list(registry.plugins.keys())
    }
```

**Step 2: Validate Plugin Metadata**
```python
def validate_plugin_metadata(plugin_id):
    try:
        plugin_module = importlib.import_module(f'modules.plugins.{plugin_id}')
        metadata = plugin_module.METADATA
        
        required_fields = ['plugin_id', 'display_name', 'version', 'category', 'description']
        missing_fields = [f for f in required_fields if f not in metadata]
        
        return {
            'valid': len(missing_fields) == 0,
            'missing_fields': missing_fields,
            'metadata': metadata
        }
    except Exception as e:
        return {'valid': False, 'error': str(e)}
```

**Step 3: Check Plugin Dependencies**
```python
def check_plugin_dependencies(plugin_id):
    try:
        plugin_module = importlib.import_module(f'modules.plugins.{plugin_id}')
        dependencies = plugin_module.METADATA.get('dependencies', [])
        
        missing_deps = []
        for dep in dependencies:
            try:
                importlib.import_module(dep)
            except ImportError:
                missing_deps.append(dep)
        
        return {
            'dependencies': dependencies,
            'missing': missing_deps,
            'all_available': len(missing_deps) == 0
        }
    except Exception as e:
        return {'error': str(e)}
```

### Resolution Procedure

**Resolution 1: Reload Plugins**
```python
def reload_plugins():
    registry = PluginRegistry()
    registry.discover_plugins()
    
    errors = registry.get_errors()
    if errors:
        return {'status': 'errors', 'errors': errors}
    
    return {'status': 'reloaded', 'plugin_count': len(registry.plugins)}
```

**Resolution 2: Restore Plugin from Backup**
```python
def restore_plugin_from_backup(plugin_id, version):
    registry = PluginRegistry()
    
    try:
        registry.restore_plugin(plugin_id, version)
        return {'status': 'restored', 'plugin_id': plugin_id}
    except Exception as e:
        return {'status': 'failed', 'error': str(e)}
```

**Resolution 3: Reinstall Plugin**
```python
def reinstall_plugin(plugin_id):
    # Remove corrupted plugin
    remove_plugin(plugin_id)
    
    # Reinstall from source
    install_plugin(plugin_id)
    
    # Validate
    validation = validate_plugin_metadata(plugin_id)
    
    return validation
```

### Prevention Measures
- Implement plugin validation
- Use plugin versioning
- Implement plugin backup
- Add plugin health checks
- Monitor plugin performance

---

## Scenario 6: Configuration File Corruption

### Symptoms
- Application fails to start
- Configuration errors
- Invalid settings
- Missing configuration values

### Diagnosis Steps

**Step 1: Validate Configuration File**
```python
import yaml

def validate_config_file(config_path):
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        return {'status': 'valid', 'config': config}
    except yaml.YAMLError as e:
        return {'status': 'invalid', 'error': str(e)}
    except FileNotFoundError:
        return {'status': 'not_found'}
```

**Step 2: Check Configuration Schema**
```python
def check_config_schema(config, schema):
    from jsonschema import validate, ValidationError
    
    try:
        validate(instance=config, schema=schema)
        return {'status': 'valid'}
    except ValidationError as e:
        return {'status': 'invalid', 'error': str(e)}
```

**Step 3: Check Configuration Permissions**
```python
import os

def check_config_permissions(config_path):
    stat = os.stat(config_path)
    
    return {
        'readable': os.access(config_path, os.R_OK),
        'writable': os.access(config_path, os.W_OK),
        'permissions': oct(stat.st_mode)[-3:]
    }
```

### Resolution Procedure

**Resolution 1: Restore from Backup**
```python
def restore_config_from_backup(config_path, backup_path):
    # Backup current corrupted config
    shutil.copy(config_path, f"{config_path}.corrupted")
    
    # Restore from backup
    shutil.copy(backup_path, config_path)
    
    # Validate
    validation = validate_config_file(config_path)
    
    return validation
```

**Resolution 2: Reset to Default**
```python
def reset_config_to_default(config_path, default_config):
    # Backup current config
    shutil.copy(config_path, f"{config_path}.backup")
    
    # Write default config
    with open(config_path, 'w') as f:
        yaml.dump(default_config, f)
    
    return {'status': 'reset'}
```

**Resolution 3: Manual Repair**
```python
def repair_config_file(config_path, repairs):
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Apply repairs
    for key, value in repairs.items():
        config[key] = value
    
    # Write repaired config
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    return {'status': 'repaired'}
```

### Prevention Measures
- Implement configuration validation
- Use configuration versioning
- Implement configuration backups
- Add configuration schema validation
- Monitor configuration changes

---

## Scenario 7: WebSocket Connection Issues

### Symptoms
- CLI terminal not connecting
- WebSocket connection drops
- Session timeout errors
- PTY allocation failures

### Diagnosis Steps

**Step 1: Check WebSocket Server**
```python
from flask_socketio import SocketIO

def check_websocket_server():
    socketio = SocketIO()
    
    return {
        'initialized': socketio is not None,
        'async_mode': socketio.async_mode
    }
```

**Step 2: Check Session Status**
```python
def check_session_status(session_id):
    session = cli_sessions.get(session_id)
    
    if session:
        return {
            'status': session['status'],
            'last_activity': session['last_activity'],
            'timeout': session['timeout']
        }
    else:
        return {'status': 'not_found'}
```

**Step 3: Check PTY Allocation**
```python
def check_pty_allocation(session_id):
    session = cli_sessions.get(session_id)
    
    if session and session.get('pty'):
        return {'status': 'allocated', 'pty': session['pty']}
    else:
        return {'status': 'not_allocated'}
```

### Resolution Procedure

**Resolution 1: Restart WebSocket Server**
```python
def restart_websocket_server():
    # Stop WebSocket server
    stop_websocket_server()
    
    # Wait for cleanup
    time.sleep(5)
    
    # Start WebSocket server
    start_websocket_server()
    
    return {'status': 'restarted'}
```

**Resolution 2: Clear Stale Sessions**
```python
def clear_stale_sessions():
    current_time = time.time()
    stale_sessions = []
    
    for session_id, session in cli_sessions.items():
        if current_time - session['last_activity'] > session['timeout']:
            stale_sessions.append(session_id)
            del cli_sessions[session_id]
    
    return {'status': 'cleared', 'count': len(stale_sessions)}
```

**Resolution 3: Reallocate PTY**
```python
def reallocate_pty(session_id):
    session = cli_sessions.get(session_id)
    
    if session:
        # Close existing PTY
        if session.get('pty'):
            session['pty'].close()
        
        # Allocate new PTY
        session['pty'] = allocate_pty()
        
        return {'status': 'reallocated'}
    
    return {'status': 'not_found'}
```

### Prevention Measures
- Implement session monitoring
- Add keepalive messages
- Implement session timeout
- Monitor PTY allocation
- Add connection health checks

---

## Scenario 8: API Rate Limiting

### Symptoms
- API requests failing
- 429 Too Many Requests errors
- Slow API response times
- Request queue buildup

### Diagnosis Steps

**Step 1: Check API Request Rate**
```python
def check_api_request_rate():
    requests_per_minute = len(api_requests) / 60
    
    return {
        'requests_per_minute': requests_per_minute,
        'limit': API_RATE_LIMIT,
        'exceeded': requests_per_minute > API_RATE_LIMIT
    }
```

**Step 2: Check API Queue**
```python
def check_api_queue():
    return {
        'queue_size': len(api_queue),
        'processing': len(api_processing),
        'completed': len(api_completed)
    }
```

**Step 3: Check API Response Times**
```python
def check_api_response_times():
    if api_response_times:
        avg_time = sum(api_response_times) / len(api_response_times)
        max_time = max(api_response_times)
        
        return {
            'avg_response_time': avg_time,
            'max_response_time': max_time,
            'count': len(api_response_times)
        }
    
    return {'status': 'no_data'}
```

### Resolution Procedure

**Resolution 1: Implement Rate Limiting**
```python
from functools import wraps
import time

def rate_limit(max_calls, period):
    def decorator(func):
        calls = []
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            calls[:] = [c for c in calls if c > now - period]
            
            if len(calls) >= max_calls:
                return {'status': 'error', 'error': 'Rate limit exceeded'}
            
            calls.append(now)
            return func(*args, **kwargs)
        
        return wrapper
    return decorator
```

**Resolution 2: Implement Request Queuing**
```python
from queue import Queue
import threading

request_queue = Queue()

def process_queue():
    while True:
        request = request_queue.get()
        try:
            result = process_request(request)
            request_queue.task_done()
        except Exception as e:
            log_error(e)

# Start queue processor
threading.Thread(target=process_queue, daemon=True).start()
```

**Resolution 3: Implement Caching**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_api_request(endpoint, params):
    return make_api_request(endpoint, params)
```

### Prevention Measures
- Implement rate limiting
- Use request queuing
- Implement caching
- Monitor API usage
- Implement circuit breaker

---

## References

- ADVANCED_DEBUGGING_GUIDE.md - Debugging procedures
- ERROR_HANDLING_DOCUMENTATION.md - Error handling and recovery
- PLATFORM_SPECIFIC_EDGE_CASES.md - Platform-specific issues
- PERFORMANCE_OPTIMIZATION.md - Performance optimization

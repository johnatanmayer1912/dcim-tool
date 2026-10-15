# Concurrency and Race Conditions Documentation

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Status** | active |
| **Owner** | System Architect (R-ARCH) + Lead Developer (R-ENG) |
| **Last Updated** | 2026-06-02 |
| **Application Version** | 7.0.10 |

---

## Overview

This document provides comprehensive concurrency handling and race condition documentation for Network Swiss Tool Pro, including threading models, synchronization mechanisms, race condition prevention, and best practices.

---

## Concurrency Model

### Threading Architecture

**Main Thread:** Flask application server (HTTP/WebSocket handling)

**Worker Threads:** Background job execution (device operations, discovery, analysis)

**Thread Pool:** Concurrent device processing (configurable, default: 10 workers)

**Async Tasks:** I/O-bound operations (HTTP requests, file I/O)

---

### Thread Types

#### 1. Main Application Thread
- **Purpose:** Flask server and request handling
- **Responsibilities:** 
  - HTTP request processing
  - WebSocket connection management
  - API endpoint routing
  - Response generation
- **Concurrency:** Single-threaded (Flask development) or multi-threaded (Flask production with gunicorn)

#### 2. Background Job Threads
- **Purpose:** Execute long-running operations asynchronously
- **Responsibilities:**
  - Network discovery
  - STP analysis
  - Policy validation
  - Configuration backups
- **Concurrency:** Multiple threads (configurable limit)

#### 3. Device Operation Threads
- **Purpose:** Process device operations in parallel
- **Responsibilities:**
  - Device connectivity checks
  - CLI command execution
  - Data collection
  - Result aggregation
- **Concurrency:** Thread pool (configurable, default: 10 workers)

#### 4. CLI Session Threads
- **Purpose:** Manage WebSocket CLI terminal sessions
- **Responsibilities:**
  - PTY allocation
  - Command I/O handling
  - Session timeout management
  - Connection cleanup
- **Concurrency:** One thread per active session

---

## Synchronization Mechanisms

### 1. Locks

**Purpose:** Prevent concurrent access to shared resources

**Implementation:**
```python
import threading

class DeviceLockManager:
    def __init__(self):
        self.locks = {}
        self.global_lock = threading.Lock()
    
    def acquire_lock(self, device_ip):
        with self.global_lock:
            if device_ip not in self.locks:
                self.locks[device_ip] = threading.Lock()
            return self.locks[device_ip].acquire(blocking=False)
        return False
    
    def release_lock(self, device_ip):
        with self.global_lock:
            if device_ip in self.locks:
                self.locks[device_ip].release()
                del self.locks[device_ip]
    
    def is_locked(self, device_ip):
        with self.global_lock:
            return device_ip in self.locks
```

**Usage:**
```python
device_lock_manager = DeviceLockManager()

def execute_operation(device, credentials):
    device_ip = device['host']
    
    if not device_lock_manager.acquire_lock(device_ip):
        return build_json(device, "error", None, "Device is busy")
    
    try:
        # Execute operation
        result = perform_operation(device, credentials)
        return build_json(device, "success", result, None)
    finally:
        device_lock_manager.release_lock(device_ip)
```

**Lock Types:**
- **threading.Lock:** Basic mutual exclusion lock
- **threading.RLock:** Reentrant lock (can be acquired multiple times by same thread)
- **threading.Semaphore:** Limits concurrent access to a resource
- **threading.Event:** Notification mechanism between threads

---

### 2. Thread-Safe Data Structures

**Purpose:** Prevent race conditions when accessing shared data

**Implementation:**
```python
import threading
from collections import defaultdict

class ThreadSafeDict:
    def __init__(self):
        self.data = {}
        self.lock = threading.Lock()
    
    def get(self, key):
        with self.lock:
            return self.data.get(key)
    
    def set(self, key, value):
        with self.lock:
            self.data[key] = value
    
    def delete(self, key):
        with self.lock:
            if key in self.data:
                del self.data[key]
    
    def keys(self):
        with self.lock:
            return list(self.data.keys())

class ThreadSafeList:
    def __init__(self):
        self.items = []
        self.lock = threading.Lock()
    
    def append(self, item):
        with self.lock:
            self.items.append(item)
    
    def pop(self):
        with self.lock:
            if self.items:
                return self.items.pop()
            return None
    
    def get_all(self):
        with self.lock:
            return list(self.items)
```

**Usage:**
```python
job_results = ThreadSafeDict()
device_queue = ThreadSafeList()

# Thread-safe access
job_results.set('job_123', {'status': 'complete'})
device_queue.append({'ip': '10.1.1.1'})
```

---

### 3. Thread Pools

**Purpose:** Manage concurrent execution with controlled concurrency

**Implementation:**
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

class ThreadPoolManager:
    def __init__(self, max_workers=10):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.active_tasks = {}
        self.lock = threading.Lock()
    
    def submit_task(self, func, *args, **kwargs):
        future = self.executor.submit(func, *args, **kwargs)
        
        with self.lock:
            task_id = f"task_{len(self.active_tasks)}"
            self.active_tasks[task_id] = future
        
        return task_id
    
    def get_result(self, task_id):
        with self.lock:
            future = self.active_tasks.get(task_id)
        
        if future:
            return future.result()
        return None
    
    def cancel_task(self, task_id):
        with self.lock:
            future = self.active_tasks.get(task_id)
        
        if future:
            return future.cancel()
        return False
```

**Usage:**
```python
pool_manager = ThreadPoolManager(max_workers=10)

# Submit tasks
task_id = pool_manager.submit_task(process_device, device, credentials)

# Get result
result = pool_manager.get_result(task_id)
```

---

## Race Conditions

### 1. Device Access Race Condition

**Scenario:** Two threads attempt to access the same device simultaneously

**Problem:** 
- Thread A starts operation on device
- Thread B starts operation on same device
- Both operations interfere with each other
- Results in corrupted data or connection errors

**Solution:** Device-level locking

**Implementation:**
```python
device_locks = {}

def execute_with_lock(device_ip, operation):
    lock = device_locks.setdefault(device_ip, threading.Lock())
    
    if not lock.acquire(blocking=False):
        return {"status": "error", "message": "Device is busy"}
    
    try:
        return operation()
    finally:
        lock.release()
```

---

### 2. Shared Resource Race Condition

**Scenario:** Multiple threads modify shared data structure simultaneously

**Problem:**
- Thread A reads shared data
- Thread B modifies shared data
- Thread A writes stale data
- Data corruption occurs

**Solution:** Thread-safe data structures with locks

**Implementation:**
```python
class SharedResourceManager:
    def __init__(self):
        self.data = {}
        self.lock = threading.RLock()  # Reentrant lock
    
    def update_data(self, key, value):
        with self.lock:
            # Critical section
            current = self.data.get(key, {})
            current.update(value)
            self.data[key] = current
```

---

### 3. Job Status Race Condition

**Scenario:** Multiple threads update job status simultaneously

**Problem:**
- Thread A updates job status to "running"
- Thread B updates job status to "complete"
- Thread A updates progress to 50%
- Final status is inconsistent

**Solution:** Atomic operations with locks

**Implementation:**
```python
class JobManager:
    def __init__(self):
        self.jobs = {}
        self.lock = threading.Lock()
    
    def update_job_status(self, job_id, status, progress=None):
        with self.lock:
            if job_id in self.jobs:
                job = self.jobs[job_id]
                job['status'] = status
                if progress is not None:
                    job['progress'] = progress
                job['timestamp'] = time.time()
```

---

### 4. Plugin Loading Race Condition

**Scenario:** Multiple threads attempt to load same plugin simultaneously

**Problem:**
- Thread A starts loading plugin
- Thread B starts loading same plugin
- Plugin loaded twice
- Memory leak or duplicate registration

**Solution:** Plugin loading synchronization

**Implementation:**
```python
class PluginLoader:
    def __init__(self):
        self.loaded_plugins = {}
        self.loading_locks = {}
        self.global_lock = threading.Lock()
    
    def load_plugin(self, plugin_id):
        # Check if already loaded
        with self.global_lock:
            if plugin_id in self.loaded_plugins:
                return self.loaded_plugins[plugin_id]
            
            # Get or create loading lock
            if plugin_id not in self.loading_locks:
                self.loading_locks[plugin_id] = threading.Lock()
        
        # Acquire plugin-specific lock
        with self.loading_locks[plugin_id]:
            # Double-check after acquiring lock
            with self.global_lock:
                if plugin_id in self.loaded_plugins:
                    return self.loaded_plugins[plugin_id]
            
            # Load plugin
            plugin = self._load_plugin_internal(plugin_id)
            
            with self.global_lock:
                self.loaded_plugins[plugin_id] = plugin
            
            return plugin
```

---

### 5. File Write Race Condition

**Scenario:** Multiple threads write to same file simultaneously

**Problem:**
- Thread A opens file for writing
- Thread B opens file for writing
- Both write simultaneously
- File corruption occurs

**Solution:** File locking or sequential writes

**Implementation:**
```python
import fcntl

def write_file_safe(filename, content):
    with open(filename, 'w') as f:
        # Acquire exclusive lock
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.write(content)
        finally:
            # Release lock
            fcntl.flock(f, fcntl.LOCK_UN)
```

---

### 6. Cache Invalidation Race Condition

**Scenario:** Cache is invalidated while being accessed

**Problem:**
- Thread A reads from cache
- Thread B invalidates cache
- Thread A uses stale data
- Inconsistent results

**Solution:** Cache versioning or atomic updates

**Implementation:**
```python
class VersionedCache:
    def __init__(self):
        self.cache = {}
        self.versions = {}
        self.lock = threading.Lock()
    
    def get(self, key):
        with self.lock:
            if key in self.cache:
                return self.cache[key], self.versions[key]
        return None, None
    
    def set(self, key, value):
        with self.lock:
            self.cache[key] = value
            self.versions[key] = time.time()
    
    def invalidate(self, key):
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                del self.versions[key]
```

---

## Deadlock Prevention

### Deadlock Scenarios

**Scenario 1: Circular Lock Acquisition**
- Thread A holds Lock 1, waits for Lock 2
- Thread B holds Lock 2, waits for Lock 1
- Both threads block indefinitely

**Prevention:**
```python
# Bad: Can cause deadlock
def operation1():
    with lock1:
        with lock2:
            # Do something
            pass

def operation2():
    with lock2:
        with lock1:
            # Do something
            pass

# Good: Always acquire locks in same order
def operation1():
    with lock1:
        with lock2:
            # Do something
            pass

def operation2():
    with lock1:
        with lock2:
            # Do something
            pass
```

**Scenario 2: Lock Timeout**
- Thread holds lock indefinitely
- Other threads wait forever

**Prevention:**
```python
def acquire_with_timeout(lock, timeout=30):
    acquired = lock.acquire(timeout=timeout)
    if not acquired:
        raise TimeoutError("Lock acquisition timeout")
    return acquired
```

**Scenario 3: Nested Lock Acquisition**
- Thread acquires same lock multiple times
- Deadlock if lock is not reentrant

**Prevention:**
```python
# Use RLock for reentrant locks
lock = threading.RLock()

def nested_operation():
    with lock:
        # Can acquire same lock again
        with lock:
            # Do something
            pass
```

---

## Thread Safety Guidelines

### 1. Shared Resource Access

**Guideline:** Always protect shared resources with locks

**Implementation:**
```python
# Bad: Unprotected access
shared_data = {'count': 0}

def increment():
    shared_data['count'] += 1  # Race condition

# Good: Protected access
shared_data = {'count': 0}
lock = threading.Lock()

def increment():
    with lock:
        shared_data['count'] += 1  # Thread-safe
```

---

### 2. Lock Ordering

**Guideline:** Always acquire locks in consistent order

**Implementation:**
```python
# Define lock order
LOCK_ORDER = ['global', 'device', 'job']

def acquire_locks_in_order(locks):
    for lock_name in LOCK_ORDER:
        if lock_name in locks:
            locks[lock_name].acquire()
```

---

### 3. Lock Scope

**Guideline:** Minimize lock scope to reduce contention

**Implementation:**
```python
# Bad: Lock held for entire operation
def long_operation():
    with lock:
        # Long operation
        time.sleep(10)

# Good: Lock only for critical section
def long_operation():
    # Prepare data
    data = prepare_data()
    
    # Lock only for update
    with lock:
        shared_data.update(data)
    
    # Continue processing
    process_data()
```

---

### 4. Lock Timeout

**Guideline:** Use lock timeouts to prevent deadlocks

**Implementation:**
```python
def safe_acquire(lock, timeout=30):
    acquired = lock.acquire(timeout=timeout)
    if not acquired:
        raise TimeoutError("Lock acquisition timeout")
    return acquired
```

---

### 5. Exception Handling

**Guideline:** Always release locks in finally block

**Implementation:**
```python
# Bad: Lock not released on exception
def operation():
    lock.acquire()
    if error_condition:
        raise Exception("Error")
    lock.release()

# Good: Lock released in finally
def operation():
    lock.acquire()
    try:
        if error_condition:
            raise Exception("Error")
    finally:
        lock.release()
```

---

## Concurrency Patterns

### 1. Producer-Consumer Pattern

**Purpose:** Separate data production from consumption

**Implementation:**
```python
import queue
import threading

class ProducerConsumer:
    def __init__(self):
        self.queue = queue.Queue(maxsize=100)
        self.producer_thread = threading.Thread(target=self.producer)
        self.consumer_thread = threading.Thread(target=self.consumer)
        self.producer_thread.start()
        self.consumer_thread.start()
    
    def producer(self):
        while True:
            data = produce_data()
            self.queue.put(data)
    
    def consumer(self):
        while True:
            data = self.queue.get()
            process_data(data)
            self.queue.task_done()
```

---

### 2. Thread Pool Pattern

**Purpose:** Reuse threads for multiple tasks

**Implementation:**
```python
from concurrent.futures import ThreadPoolExecutor

def process_tasks(tasks, max_workers=10):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_task, task) for task in tasks]
        results = [future.result() for future in futures]
    return results
```

---

### 3. Future/Promise Pattern

**Purpose:** Handle asynchronous operations

**Implementation:**
```python
from concurrent.futures import Future

class AsyncOperation:
    def __init__(self):
        self.future = Future()
    
    def execute(self):
        try:
            result = self._do_work()
            self.future.set_result(result)
        except Exception as e:
            self.future.set_exception(e)
    
    def get_result(self):
        return self.future.result()
```

---

## Async/Await Pattern

### Async Operations

**Purpose:** Handle I/O-bound operations efficiently

**Implementation:**
```python
import asyncio

async def fetch_device_info(device_ip):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://{device_ip}/api/info") as response:
            return await response.json()

async def fetch_multiple_devices(device_ips):
    tasks = [fetch_device_info(ip) for ip in device_ips]
    results = await asyncio.gather(*tasks)
    return results
```

---

## Concurrency Testing

### 1. Race Condition Testing

**Purpose:** Detect race conditions through testing

**Implementation:**
```python
import threading

def test_concurrent_access():
    shared_counter = 0
    lock = threading.Lock()
    
    def increment():
        nonlocal shared_counter
        for _ in range(1000):
            with lock:
                shared_counter += 1
    
    threads = [threading.Thread(target=increment) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    assert shared_counter == 10000
```

---

### 2. Deadlock Testing

**Purpose:** Detect deadlocks through testing

**Implementation:**
```python
def test_deadlock():
    lock1 = threading.Lock()
    lock2 = threading.Lock()
    
    def thread1():
        with lock1:
            time.sleep(0.1)
            with lock2:
                pass
    
    def thread2():
        with lock2:
            time.sleep(0.1)
            with lock1:
                pass
    
    t1 = threading.Thread(target=thread1)
    t2 = threading.Thread(target=thread2)
    
    t1.start()
    t2.start()
    
    t1.join(timeout=5)
    t2.join(timeout=5)
    
    assert not t1.is_alive() or not t2.is_alive()
```

---

## Monitoring and Debugging

### 1. Thread Monitoring

**Purpose:** Monitor thread activity and detect issues

**Implementation:**
```python
import threading

def monitor_threads():
    for thread in threading.enumerate():
        print(f"Thread: {thread.name}, Alive: {thread.is_alive()}")
```

---

### 2. Lock Monitoring

**Purpose:** Monitor lock contention and detect deadlocks

**Implementation:**
```python
class MonitoredLock:
    def __init__(self):
        self.lock = threading.Lock()
        self.acquired_by = None
        self.acquire_count = 0
    
    def acquire(self):
        self.lock.acquire()
        self.acquired_by = threading.current_thread().name
        self.acquire_count += 1
    
    def release(self):
        self.acquired_by = None
        self.lock.release()
```

---

## Best Practices

### 1. Design Principles

- **Minimize shared state:** Reduce need for synchronization
- **Use immutable data:** Avoid race conditions
- **Prefer message passing:** Over shared memory
- **Design for concurrency:** Consider parallel execution from start
- **Test thoroughly:** Include concurrency tests

### 2. Implementation Guidelines

- **Use context managers:** Ensure locks are released
- **Set lock timeouts:** Prevent deadlocks
- **Minimize lock scope:** Reduce contention
- **Document synchronization:** Explain locking strategy
- **Monitor performance:** Track lock contention

### 3. Debugging Guidelines

- **Use thread-safe logging:** Avoid race conditions in logging
- **Enable thread debugging:** Use thread debugging tools
- **Monitor thread counts:** Detect thread leaks
- **Profile lock contention:** Identify bottlenecks
- **Test with high concurrency:** Stress test concurrency

---

## References

- MODULE_ARCHITECTURE.md - Module architecture and threading
- PERFORMANCE_OPTIMIZATION.md - Performance optimization strategies
- ERROR_HANDLING_DOCUMENTATION.md - Error handling and recovery
- CODE_INVENTORY.md - Data structures and validation

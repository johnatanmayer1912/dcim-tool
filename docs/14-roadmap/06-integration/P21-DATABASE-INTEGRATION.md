# P21: Database Integration

| Field | Value |
|-------|-------|
| **Prompt ID** | P21 |
| **Phase** | 06-integration |
| **Dependency Level** | 1 (Depends on Phase 1) |
| **Estimated Time** | 10 minutes |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-02 |

---

## Purpose

Reconstruct database integration for data persistence. This module provides SQLite database integration for storing device information, job results, and configuration data.

---

## Prerequisites

- Phase 1 (Foundation) completed
- Python environment set up
- SQLite available (standard library)

---

## Instructions

### Step 1: Create database_integration Module

```bash
cd modules
```

---

### Step 2: Create database_integration.py

```python
"""
Database Integration

SQLite database integration for data persistence.
"""

import sqlite3
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from contextlib import contextmanager

class DatabaseManager:
    """Manager for database operations"""
    
    def __init__(self, db_path='app.db'):
        self.db_path = db_path
        self._initialize_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _initialize_database(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            # Devices table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    host TEXT UNIQUE NOT NULL,
                    device_type TEXT NOT NULL,
                    hostname TEXT,
                    serial_number TEXT,
                    last_seen TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Jobs table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT UNIQUE NOT NULL,
                    plugin_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    devices TEXT NOT NULL,
                    results TEXT,
                    errors TEXT,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            ''')
            
            # Configurations table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS configurations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id INTEGER NOT NULL,
                    config_type TEXT NOT NULL,
                    config_data TEXT NOT NULL,
                    version TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (device_id) REFERENCES devices(id)
                )
            ''')
            
            # VLANs table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS vlans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id INTEGER NOT NULL,
                    vlan_id INTEGER NOT NULL,
                    vlan_name TEXT,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (device_id) REFERENCES devices(id)
                )
            ''')
    
    def add_device(self, device: Dict) -> int:
        """Add device to database"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT OR REPLACE INTO devices (host, device_type, hostname, serial_number, last_seen)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                device['host'],
                device['device_type'],
                device.get('hostname'),
                device.get('serial_number'),
                datetime.utcnow()
            ))
            return cursor.lastrowid
    
    def get_device(self, host: str) -> Optional[Dict]:
        """Get device by host"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM devices WHERE host = ?', (host,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def get_all_devices(self) -> List[Dict]:
        """Get all devices"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM devices')
            return [dict(row) for row in cursor.fetchall()]
    
    def create_job(self, job_id: str, plugin_id: str, devices: List[Dict]) -> int:
        """Create job record"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO jobs (job_id, plugin_id, status, devices)
                VALUES (?, ?, ?, ?)
            ''', (
                job_id,
                plugin_id,
                'pending',
                json.dumps(devices)
            ))
            return cursor.lastrowid
    
    def update_job_status(self, job_id: str, status: str, results: List = None, errors: List = None):
        """Update job status"""
        with self.get_connection() as conn:
            conn.execute('''
                UPDATE jobs
                SET status = ?, results = ?, errors = ?, completed_at = ?
                WHERE job_id = ?
            ''', (
                status,
                json.dumps(results) if results else None,
                json.dumps(errors) if errors else None,
                datetime.utcnow() if status == 'complete' else None,
                job_id
            ))
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job by ID"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM jobs WHERE job_id = ?', (job_id,))
            row = cursor.fetchone()
            if row:
                job = dict(row)
                job['devices'] = json.loads(job['devices'])
                if job['results']:
                    job['results'] = json.loads(job['results'])
                if job['errors']:
                    job['errors'] = json.loads(job['errors'])
                return job
            return None
    
    def save_vlan_info(self, device_id: int, vlans: List[Dict]):
        """Save VLAN information"""
        with self.get_connection() as conn:
            # Delete existing VLANs for device
            conn.execute('DELETE FROM vlans WHERE device_id = ?', (device_id,))
            
            # Insert new VLANs
            for vlan in vlans:
                conn.execute('''
                    INSERT INTO vlans (device_id, vlan_id, vlan_name, status)
                    VALUES (?, ?, ?, ?)
                ''', (
                    device_id,
                    vlan['vlan_id'],
                    vlan.get('name'),
                    vlan.get('status')
                ))
    
    def get_device_vlans(self, device_id: int) -> List[Dict]:
        """Get VLANs for device"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM vlans WHERE device_id = ?', (device_id,))
            return [dict(row) for row in cursor.fetchall()]
```

---

### Step 3: Validate Database Integration

```python
# Test database integration
from modules.database_integration import DatabaseManager

# Create database manager
db = DatabaseManager('test_app.db')

# Test device operations
device = {
    'host': '10.1.1.1',
    'device_type': 'cisco_ios',
    'hostname': 'router1',
    'serial_number': 'SN12345'
}
device_id = db.add_device(device)
assert device_id > 0

# Test device retrieval
retrieved_device = db.get_device('10.1.1.1')
assert retrieved_device is not None
assert retrieved_device['host'] == '10.1.1.1'

# Test job operations
job_id = 'test-job-123'
job_id_db = db.create_job(job_id, 'network_discovery', [device])
assert job_id_db > 0

# Test job update
db.update_job_status(job_id, 'complete', results=[{'test': 'data'}])

# Test job retrieval
job = db.get_job(job_id)
assert job is not None
assert job['status'] == 'complete'

print("Database integration validation successful")
```

---

## Validation Checklist

- [ ] database_integration.py created
- [ ] DatabaseManager class implemented
- [ ] Database schema initialized
- [ ] add_device implemented
- [ ] get_device implemented
- [ ] get_all_devices implemented
- [ ] create_job implemented
- [ ] update_job_status implemented
- [ ] get_job implemented
- [ ] save_vlan_info implemented
- [ ] get_device_vlans implemented
- [ ] Database integration validation successful
- [ ] Integration phase complete
- [ ] Ready for testing reconstruction

---

## Troubleshooting

### Issue: Database initialization fails

**Solution:**
- Check write permissions
- Verify disk space
- Test SQLite availability

### Issue: Database operations fail

**Solution:**
- Verify database schema
- Check SQL syntax
- Test with simple queries

---

## Next Steps

After completing this prompt, Phase 6 (Integration) is complete. Proceed to Phase 7: Testing

---

## References

- CODE_INVENTORY.md: ../../02-codebase/CODE_INVENTORY.md
- MODULE_ARCHITECTURE.md: ../../01-architecture/MODULE_ARCHITECTURE.md

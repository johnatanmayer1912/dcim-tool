# API Documentation

## Overview

Network Swiss Tool Pro provides a RESTful API and WebSocket API for network management operations. The API is built on Flask with Flask-SocketIO for real-time CLI terminal functionality.

**Base URL:** `http://127.0.0.1:5051`  
**Application Version:** **7.0.29** (see `/VERSION` and `GET /api/version`)  
**Doc last synced:** 2026-06-10  
**Authentication:** None (local network use only)  
**Content-Type:** `application/json`

> Example responses below may show older version strings; **runtime truth** is always `/VERSION` and live `GET /api/version`.

---

## REST API Endpoints

### Health & Status

#### GET /health
Simple HTTP health check to verify the server is reachable.

**Response:** `200 OK` with body `"OK"`

#### GET /debug_status
Return JSON formatted dependency report for troubleshooting.

**Response:**
```json
{
  "flask": "2.3.3",
  "socketio": "5.3.6",
  "netmiko": "4.2.0",
  "dependencies": [...]
}
```

#### GET /api/version
Return current application version and update date.

**Response:**
```json
{
  "version": "7.0.10",
  "date": "2026-05-31 — v7.0.10 NX-OS LLDP discovery link parsing fixes"
}
```

#### GET /api/release-notes
Return release notes for the current version.

**Response:**
```json
{
  "version": "7.0.10",
  "highlights": [
    "Discovery NX-OS LLDP link parsing fixes",
    "network_discovery plugin v1.4.0"
  ]
}
```

#### GET /api/readme
Return the contents of README.md.

**Response:**
```json
{
  "readme": "# Network Swiss Tool Pro\n..."
}
```

---

### Core Operations

#### POST /api/execute
Execute a network operation on selected devices.

**Request:**
```json
{
  "action": "connectivity",
  "username": "admin",
  "password": "password",
  "enable_pwd": "enable_password",
  "scope": "bulk",
  "devices": ["10.1.1.1", "10.1.1.2"],
  "group_filter": "CoreSwitches"
}
```

**Actions:** `connectivity`, `vlan_check`, `mac_check`, `interface_status`, `interface_description`, `topology_mapper`, `network_audit`, `config_backup`, `vlan_compare`, `vlan_add`, `vlan_rename`, `vlan_delete`, `save_config`

**Success Response (200 OK):**
```json
{
  "status": "started",
  "job_id": "exec_job_123456",
  "action": "connectivity",
  "devices_count": 2,
  "timestamp": "2026-06-02T12:00:00Z"
}
```

**Error Response (400 Bad Request):**
```json
{
  "status": "error",
  "error": "Invalid request parameters",
  "details": {
    "field": "action",
    "message": "Invalid action: invalid_action"
  }
}
```

**Error Response (401 Unauthorized):**
```json
{
  "status": "error",
  "error": "Authentication failed",
  "details": {
    "message": "Invalid credentials"
  }
}
```

**Error Response (500 Internal Server Error):**
```json
{
  "status": "error",
  "error": "Internal server error",
  "details": {
    "message": "Failed to start job"
  }
}
```

**Field Descriptions:**
- `status`: Operation status (`started`, `error`)
- `job_id`: Unique job identifier for status polling
- `action`: Network operation being executed
- `devices_count`: Number of devices in scope
- `timestamp`: ISO 8601 timestamp when job started

**Authentication:** None required (local network use only)  
**Rate Limiting:** None enforced  
**Timeout:** 30 seconds for initial request

#### POST /api/shutdown
Gracefully shutdown the application.

**Success Response (200 OK):**
```json
{
  "status": "shutting_down",
  "timestamp": "2026-06-02T12:00:00Z",
  "message": "Application is shutting down gracefully"
}
```

**Error Response (500 Internal Server Error):**
```json
{
  "status": "error",
  "error": "Shutdown failed",
  "details": {
    "message": "Failed to shutdown application"
  }
}
```

**Field Descriptions:**
- `status`: Operation status (`shutting_down`, `error`)
- `timestamp`: ISO 8601 timestamp when shutdown initiated
- `message`: Human-readable status message

**Authentication:** None required (local network use only)  
**Rate Limiting:** None enforced  
**Timeout:** 10 seconds  
**Note:** This endpoint will terminate the application, so subsequent requests will fail.

---

### Inventory & Logs

#### GET /api/inventory
Return the contents of inventory.txt.

**Success Response (200 OK):**
```json
{
  "inventory": "# Test Inventory for QA Validation\n# Format: IP,device_type,group\n\n[CoreSwitches]\n10.1.1.1,cisco_ios,CoreSwitches\n10.1.1.2,cisco_nxos,CoreSwitches\n\n[AccessLayer]\n10.2.1.1,juniper_junos,AccessLayer\n10.2.1.2,cisco_ios,AccessLayer\n\n[Distribution]\n10.3.1.1,cisco_ios,Distribution",
  "device_count": 5,
  "groups": ["CoreSwitches", "AccessLayer", "Distribution"],
  "last_modified": "2026-06-02T10:00:00Z"
}
```

**Error Response (404 Not Found):**
```json
{
  "status": "error",
  "error": "Inventory file not found",
  "details": {
    "message": "inventory.txt does not exist"
  }
}
```

**Field Descriptions:**
- `inventory`: Raw contents of inventory.txt file
- `device_count`: Total number of devices in inventory
- `groups`: List of device group names
- `last_modified`: ISO 8601 timestamp of last file modification

**Authentication:** None required  
**Rate Limiting:** None enforced  
**Timeout:** 5 seconds

---

#### GET /api/logs
Return recent application logs.

**Query Parameters:**
- `lines` (integer): Number of log lines to return (default: 100, max: 1000)
- `level` (string): Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

**Success Response (200 OK):**
```json
{
  "logs": [
    "[2026-06-02 10:30:00] [INFO] Starting application...",
    "[2026-06-02 10:30:01] [INFO] Loaded 13 plugins...",
    "[2026-06-02 10:30:02] [DEBUG] Initializing plugin registry...",
    "[2026-06-02 10:30:03] [INFO] Application ready on http://127.0.0.1:5051"
  ],
  "line_count": 4,
  "timestamp": "2026-06-02T12:00:00Z"
}
```

**Error Response (400 Bad Request):**
```json
{
  "status": "error",
  "error": "Invalid parameters",
  "details": {
    "field": "lines",
    "message": "lines must be between 1 and 1000"
  }
}
```

**Field Descriptions:**
- `logs`: Array of log line strings
- `line_count`: Number of log lines returned
- `timestamp`: ISO 8601 timestamp when logs were retrieved

**Authentication:** None required  
**Rate Limiting:** None enforced  
**Timeout:** 10 seconds

---

#### POST /api/extract_docs
Extract documentation files for offline use.

**Request:**
```json
{
  "files": ["README.md", "QA_TESTING_CHECKLIST.txt"]
}
```

**Success Response (200 OK):**
```json
{
  "status": "extracted",
  "files": [
    {
      "name": "README.md",
      "size": 12345,
      "content": "# Network Swiss Tool Pro\n..."
    },
    {
      "name": "QA_TESTING_CHECKLIST.txt",
      "size": 6789,
      "content": "QA Testing Checklist\n..."
    }
  ],
  "extracted_count": 2,
  "timestamp": "2026-06-02T12:00:00Z"
}
```

**Error Response (400 Bad Request):**
```json
{
  "status": "error",
  "error": "Invalid request parameters",
  "details": {
    "field": "files",
    "message": "files must be a non-empty array"
  }
}
```

**Error Response (404 Not Found):**
```json
{
  "status": "error",
  "error": "File not found",
  "details": {
    "file": "nonexistent.md",
    "message": "File does not exist"
  }
}
```

**Field Descriptions:**
- `status`: Operation status (`extracted`, `error`)
- `files`: Array of extracted file objects
- `files[].name`: File name
- `files[].size`: File size in bytes
- `files[].content`: File content as string
- `extracted_count`: Number of files extracted
- `timestamp`: ISO 8601 timestamp when extraction completed

**Authentication:** None required  
**Rate Limiting:** None enforced  
**Timeout:** 30 seconds

---

### Plugin Management

#### GET /api/plugins/list
Return list of all registered plugins with metadata.

**Success Response (200 OK):**
```json
{
  "plugins": [
    {
      "plugin_id": "network_discovery",
      "display_name": "Network Discovery & Crawl",
      "version": "1.4.0",
      "category": "Discovery",
      "enabled": true,
      "description": "Automated network discovery and topology mapping"
    },
    {
      "plugin_id": "standards_validator",
      "display_name": "Standards Validator",
      "version": "1.0.0",
      "category": "Validation",
      "enabled": true,
      "description": "Validate device configurations against standards"
    }
  ],
  "count": 13,
  "enabled_count": 13,
  "timestamp": "2026-06-02T12:00:00Z"
}
```

**Error Response (500 Internal Server Error):**
```json
{
  "status": "error",
  "error": "Failed to load plugin registry",
  "details": {
    "message": "Plugin registry not initialized"
  }
}
```

**Field Descriptions:**
- `plugins`: Array of plugin objects
- `plugins[].plugin_id`: Unique plugin identifier
- `plugins[].display_name`: Human-readable plugin name
- `plugins[].version`: Plugin version (semantic versioning)
- `plugins[].category`: Plugin category
- `plugins[].enabled`: Plugin enabled status
- `plugins[].description`: Plugin description
- `count`: Total number of plugins
- `enabled_count`: Number of enabled plugins
- `timestamp`: ISO 8601 timestamp when list was generated

**Authentication:** None required  
**Rate Limiting:** None enforced  
**Timeout:** 5 seconds

---

#### POST /api/plugins/reload
Hot-reload the plugin registry.

**Success Response (200 OK):**
```json
{
  "status": "reloaded",
  "plugins": [
    {
      "plugin_id": "network_discovery",
      "version": "1.4.0",
      "status": "loaded"
    }
  ],
  "errors": [],
  "reloaded_count": 13,
  "timestamp": "2026-06-02T12:00:00Z"
}
```

**Error Response (500 Internal Server Error):**
```json
{
  "status": "error",
  "error": "Reload failed",
  "details": {
    "message": "Failed to reload plugin registry",
    "errors": [
      {
        "plugin_id": "broken_plugin",
        "error": "Import error"
      }
    ]
  }
}
```

**Field Descriptions:**
- `status`: Operation status (`reloaded`, `error`)
- `plugins`: Array of reloaded plugin objects
- `plugins[].plugin_id`: Plugin identifier
- `plugins[].version`: Plugin version
- `plugins[].status`: Plugin load status
- `errors`: Array of error objects (if any)
- `reloaded_count`: Number of plugins successfully reloaded
- `timestamp`: ISO 8601 timestamp when reload completed

**Authentication:** None required  
**Rate Limiting:** None enforced  
**Timeout:** 30 seconds

---

#### GET /api/plugins/history/<plugin_id>
Get backup history for a specific plugin.

**Success Response (200 OK):**
```json
{
  "plugin_id": "network_discovery",
  "history": [
    {
      "version": "1.4.0",
      "date": "2026-05-31",
      "path": "/path/to/backup/network_discovery_1.4.0",
      "size": 12345
    },
    {
      "version": "1.3.0",
      "date": "2026-05-15",
      "path": "/path/to/backup/network_discovery_1.3.0",
      "size": 12000
    }
  ],
  "history_count": 2,
  "timestamp": "2026-06-02T12:00:00Z"
}
```

**Error Response (404 Not Found):**
```json
{
  "status": "error",
  "error": "Plugin not found",
  "details": {
    "plugin_id": "nonexistent_plugin",
    "message": "Plugin does not exist"
  }
}
```

**Field Descriptions:**
- `plugin_id`: Plugin identifier
- `history`: Array of backup history objects
- `history[].version`: Plugin version
- `history[].date`: Backup date (YYYY-MM-DD)
- `history[].path`: Backup file path
- `history[].size`: Backup file size in bytes
- `history_count`: Number of backup versions
- `timestamp`: ISO 8601 timestamp when history was retrieved

**Authentication:** None required  
**Rate Limiting:** None enforced  
**Timeout:** 5 seconds

---

#### GET /api/plugins/debug
Debug endpoint to troubleshoot plugin loading issues.

**Success Response (200 OK):**
```json
{
  "registry_status": "loaded",
  "plugins": [
    {
      "plugin_id": "network_discovery",
      "status": "loaded",
      "load_time": "0.05s"
    }
  ],
  "errors": [],
  "sys_path": [
    "/path/to/plugins",
    "/path/to/python/lib"
  ],
  "python_version": "3.11.0",
  "timestamp": "2026-06-02T12:00:00Z"
}
```

**Field Descriptions:**
- `registry_status`: Registry status (`loaded`, `error`)
- `plugins`: Array of plugin status objects
- `plugins[].plugin_id`: Plugin identifier
- `plugins[].status`: Plugin load status
- `plugins[].load_time`: Time to load plugin
- `errors`: Array of error objects (if any)
- `sys_path`: Python system path
- `python_version`: Python version
- `timestamp`: ISO 8601 timestamp when debug info was generated

**Authentication:** None required  
**Rate Limiting:** None enforced  
**Timeout:** 10 seconds

---

#### POST /api/plugins/upload
Upload and validate a new plugin file.

**Request:** `multipart/form-data` with `plugin_file`

**Success Response (200 OK):**
```json
{
  "status": "uploaded",
  "plugin_id": "new_plugin",
  "validation": "passed",
  "validation_details": {
    "syntax": "valid",
    "structure": "valid",
    "dependencies": "satisfied"
  },
  "file_size": 12345,
  "timestamp": "2026-06-02T12:00:00Z"
}
```

**Error Response (400 Bad Request):**
```json
{
  "status": "error",
  "error": "Validation failed",
  "details": {
    "validation": "failed",
    "validation_details": {
      "syntax": "invalid",
      "error": "Syntax error on line 42"
    }
  }
}
```

**Error Response (413 Payload Too Large):**
```json
{
  "status": "error",
  "error": "File too large",
  "details": {
    "max_size": "10MB",
    "actual_size": "15MB"
  }
}
```

**Field Descriptions:**
- `status`: Operation status (`uploaded`, `error`)
- `plugin_id`: Plugin identifier (extracted from file)
- `validation`: Validation result (`passed`, `failed`)
- `validation_details`: Detailed validation results
- `file_size`: Uploaded file size in bytes
- `timestamp`: ISO 8601 timestamp when upload completed

**Authentication:** None required  
**Rate Limiting:** None enforced  
**Timeout:** 60 seconds  
**Max File Size:** 10MB

---

### Standards Validator

#### POST /api/standards/run
Run the Standards Validator against selected devices.

**Request:**
```json
{
  "username": "admin",
  "password": "password",
  "enable_pwd": "enable_password",
  "scope": "bulk",
  "devices": ["10.1.1.1"],
  "policy_file": "standards.yaml"
}
```

**Success Response (200 OK):**
```json
{
  "status": "started",
  "job_id": "std_job_123456",
  "policy_file": "standards.yaml",
  "devices_count": 1,
  "timestamp": "2026-06-02T12:00:00Z"
}
```

**Error Response (400 Bad Request):**
```json
{
  "status": "error",
  "error": "Invalid request parameters",
  "details": {
    "field": "policy_file",
    "message": "Policy file not found: custom_policy.yaml"
  }
}
```

**Error Response (401 Unauthorized):**
```json
{
  "status": "error",
  "error": "Authentication failed",
  "details": {
    "message": "Invalid credentials"
  }
}
```

**Field Descriptions:**
- `status`: Operation status (`started`, `error`)
- `job_id`: Unique job identifier for status polling
- `policy_file`: Policy file used for validation
- `devices_count`: Number of devices in scope
- `timestamp`: ISO 8601 timestamp when job started

**Authentication:** Device credentials required (username, password, enable_pwd)  
**Rate Limiting:** None enforced  
**Timeout:** 30 seconds for initial request

---

#### GET /api/standards/policies
Return list of available policy files and categories.

**Success Response (200 OK):**
```json
{
  "policies": ["standards.yaml", "security_baseline.yaml", "datacenter.yaml"],
  "categories": {
    "Security": ["telnet_disabled", "ssh_version_2", "enable_secret_set"],
    "NTP": ["ntp_synchronized", "ntp_server_configured"],
    "SNMP": ["snmp_v3_configured", "snmp_community_removed"],
    "Logging": ["syslog_server_configured", "logging_buffered"]
  },
  "policy_count": 3,
  "category_count": 4,
  "timestamp": "2026-06-02T12:00:00Z"
}
```

**Error Response (500 Internal Server Error):**
```json
{
  "status": "error",
  "error": "Failed to load policies",
  "details": {
    "message": "Policy directory not accessible"
  }
}
```

**Field Descriptions:**
- `policies`: Array of available policy file names
- `categories`: Object mapping categories to policy IDs
- `policy_count`: Total number of policy files
- `category_count`: Total number of categories
- `timestamp`: ISO 8601 timestamp when list was generated

**Authentication:** None required  
**Rate Limiting:** None enforced  
**Timeout:** 5 seconds

---

#### POST /api/standards/upload
Upload a custom policy file (YAML or JSON).

**Request:** `multipart/form-data` with `policy_file`

**Success Response (200 OK):**
```json
{
  "status": "uploaded",
  "filename": "custom_policy.yaml",
  "validation": "passed",
  "policy_count": 5,
  "timestamp": "2026-06-02T12:00:00Z"
}
```

**Error Response (400 Bad Request):**
```json
{
  "status": "error",
  "error": "Validation failed",
  "details": {
    "validation": "failed",
    "error": "Invalid YAML syntax on line 15"
  }
}
```

**Error Response (413 Payload Too Large):**
```json
{
  "status": "error",
  "error": "File too large",
  "details": {
    "max_size": "5MB",
    "actual_size": "8MB"
  }
}
```

**Field Descriptions:**
- `status`: Operation status (`uploaded`, `error`)
- `filename`: Uploaded file name
- `validation`: Validation result (`passed`, `failed`)
- `policy_count`: Total number of policies after upload
- `timestamp`: ISO 8601 timestamp when upload completed

**Authentication:** None required  
**Rate Limiting:** None enforced  
**Timeout:** 30 seconds  
**Max File Size:** 5MB

---

### Network Discovery

#### POST /api/discovery/run
Launch a background network discovery crawl.

**Request:**
```json
{
  "username": "admin",
  "password": "password",
  "enable_pwd": "enable_password",
  "seed_hosts": ["10.1.1.1"],
  "crawl_depth": 3,
  "demo_mode": false
}
```

**Success Response (200 OK):**
```json
{
  "job_id": "disc_job_456789",
  "status": "started",
  "seed_hosts": ["10.1.1.1"],
  "crawl_depth": 3,
  "demo_mode": false,
  "timestamp": "2026-06-02T12:00:00Z"
}
```

**Error Response (400 Bad Request):**
```json
{
  "status": "error",
  "error": "Invalid request parameters",
  "details": {
    "field": "seed_hosts",
    "message": "seed_hosts must be a non-empty array"
  }
}
```

**Error Response (401 Unauthorized):**
```json
{
  "status": "error",
  "error": "Authentication failed",
  "details": {
    "message": "Invalid credentials"
  }
}
```

**Field Descriptions:**
- `job_id`: Unique job identifier for status polling
- `status`: Operation status (`started`, `error`)
- `seed_hosts`: Array of seed IP addresses
- `crawl_depth`: Maximum crawl depth (1-10)
- `demo_mode`: Demo mode flag
- `timestamp`: ISO 8601 timestamp when job started

**Authentication:** Device credentials required (username, password, enable_pwd)  
**Rate Limiting:** None enforced  
**Timeout:** 30 seconds for initial request

---

#### GET /api/discovery/status/<job_id>
Poll job status for a discovery job.

**Success Response (200 OK) - Running:**
```json
{
  "status": "running",
  "progress": 45,
  "devices_discovered": 15,
  "devices_total": 33,
  "current_host": "10.2.1.5",
  "timestamp": "2026-06-02T12:05:00Z"
}
```

**Success Response (200 OK) - Complete:**
```json
{
  "status": "complete",
  "progress": 100,
  "devices_discovered": 33,
  "devices_total": 33,
  "result": {
    "devices": [...],
    "links": [...]
  },
  "error": null,
  "timestamp": "2026-06-02T12:10:00Z"
}
```

**Error Response (404 Not Found):**
```json
{
  "status": "error",
  "error": "Job not found",
  "details": {
    "job_id": "disc_job_999999",
    "message": "Job does not exist or has expired"
  }
}
```

**Field Descriptions:**
- `status`: Job status (`running`, `complete`, `error`)
- `progress`: Progress percentage (0-100)
- `devices_discovered`: Number of devices discovered so far
- `devices_total`: Estimated total devices
- `current_host`: Current host being processed (running only)
- `result`: Discovery result (complete only)
- `error`: Error message (if any)
- `timestamp`: ISO 8601 timestamp when status was retrieved

**Authentication:** None required  
**Rate Limiting:** None enforced  
**Timeout:** 5 seconds

---

#### GET /api/discovery/export/<job_id>
Return raw JSON inventory export for a completed job.

**Success Response (200 OK):**
```json
{
  "job_id": "disc_job_456789",
  "devices": [
    {
      "ip": "10.1.1.1",
      "hostname": "core-sw-01",
      "device_type": "cisco_ios",
      "vendor": "Cisco",
      "model": "Catalyst 3850",
      "serial": "FOC1234ABCD",
      "interfaces": [...],
      "neighbors": [...]
    }
  ],
  "device_count": 33,
  "timestamp": "2026-06-02T12:10:00Z"
}
```

**Error Response (404 Not Found):**
```json
{
  "status": "error",
  "error": "Job not found",
  "details": {
    "job_id": "disc_job_999999",
    "message": "Job does not exist or has not completed"
  }
}
```

**Field Descriptions:**
- `job_id`: Job identifier
- `devices`: Array of discovered device objects
- `devices[].ip`: Device IP address
- `devices[].hostname`: Device hostname
- `devices[].device_type`: Device type
- `devices[].vendor`: Device vendor
- `devices[].model`: Device model
- `devices[].serial`: Device serial number
- `devices[].interfaces`: Array of interface objects
- `devices[].neighbors`: Array of neighbor objects
- `device_count`: Total number of devices
- `timestamp`: ISO 8601 timestamp when export was generated

**Authentication:** None required  
**Rate Limiting:** None enforced  
**Timeout:** 10 seconds

---

#### GET /api/discovery/report/<job_id>
Serve Vis.js topology HTML for a completed discovery job.

**Success Response (200 OK):** HTML file (text/html) with interactive topology map

**Error Response (404 Not Found):**
```json
{
  "status": "error",
  "error": "Job not found",
  "details": {
    "job_id": "disc_job_999999",
    "message": "Job does not exist or has not completed"
  }
}
```

**Content-Type:** text/html  
**Authentication:** None required  
**Rate Limiting:** None enforced  
**Timeout:** 10 seconds

---

### Health Check

#### GET /api/health-check/run
Run comprehensive health checks (inventory, port, plugins, demos, CLI smoke).

**Query Parameters:**
- `quick` (boolean): Run quick checks only
- `full` (boolean): Run full checks including CLI smoke
- `include_cli` (boolean): Include CLI smoke test

**Success Response (200 OK):**
```json
{
  "ok": true,
  "checks": [
    {
      "name": "inventory",
      "status": "pass",
      "message": "Inventory file found with 5 devices",
      "duration_ms": 5
    },
    {
      "name": "port",
      "status": "pass",
      "message": "Application port 5051 is reachable",
      "duration_ms": 2
    },
    {
      "name": "plugins",
      "status": "pass",
      "message": "13 plugins loaded successfully",
      "duration_ms": 15
    },
    {
      "name": "demos",
      "status": "pass",
      "message": "Demo maps are available",
      "duration_ms": 8
    },
    {
      "name": "cli_smoke",
      "status": "pass",
      "message": "CLI smoke test passed",
      "duration_ms": 120
    }
  ],
  "summary": {
    "total": 5,
    "passed": 5,
    "failed": 0,
    "skipped": 0
  },
  "ran_at": "2026-06-02T10:30:00Z"
}
```

**Error Response (500 Internal Server Error):**
```json
{
  "ok": false,
  "checks": [
    {
      "name": "inventory",
      "status": "fail",
      "message": "Inventory file not found",
      "duration_ms": 5
    }
  ],
  "summary": {
    "total": 5,
    "passed": 4,
    "failed": 1,
    "skipped": 0
  },
  "ran_at": "2026-06-02T10:30:00Z"
}
```

**Field Descriptions:**
- `ok`: Overall health status (`true`, `false`)
- `checks`: Array of check results
- `checks[].name`: Check name
- `checks[].status`: Check status (`pass`, `fail`, `skip`)
- `checks[].message`: Check result message
- `checks[].duration_ms`: Check duration in milliseconds
- `summary`: Summary of check results
- `summary.total`: Total number of checks
- `summary.passed`: Number of passed checks
- `summary.failed`: Number of failed checks
- `summary.skipped`: Number of skipped checks
- `ran_at`: ISO 8601 timestamp when checks ran

**Authentication:** None required  
**Rate Limiting:** None enforced  
**Timeout:** 120 seconds (full checks), 30 seconds (quick checks)

---

#### GET /api/health-check/status
Return the last health check results.

**Success Response (200 OK):**
```json
{
  "ok": true,
  "checks": [
    {
      "name": "inventory",
      "status": "pass",
      "message": "Inventory file found with 5 devices",
      "duration_ms": 5
    }
  ],
  "summary": {
    "total": 5,
    "passed": 5,
    "failed": 0,
    "skipped": 0
  },
  "ran_at": "2026-06-02T10:30:00Z"
}
```

**Error Response (404 Not Found):**
```json
{
  "status": "error",
  "error": "No health check results available",
  "details": {
    "message": "Run health check first"
  }
}
```

**Field Descriptions:** Same as GET /api/health-check/run

**Authentication:** None required  
**Rate Limiting:** None enforced  
**Timeout:** 5 seconds

---

#### GET /api/health-check/demo-map/<which>
Serve demo topology maps for health check validation.

**Parameters:** `which` can be `discovery` or `vpc`

**Success Response (200 OK):** HTML file (text/html) with demo topology map

**Error Response (404 Not Found):**
```json
{
  "status": "error",
  "error": "Demo map not found",
  "details": {
    "which": "invalid",
    "message": "Valid values: discovery, vpc"
  }
}
```

**Content-Type:** text/html  
**Authentication:** None required  
**Rate Limiting:** None enforced  
**Timeout:** 5 seconds

---

### MAC Trace

**Backend (v7.0.28+):** `modules/mac_trace.py` uses `utils/mac_utils.py` for MAC normalization and vendor-specific search terms (Cisco dotted `aabb.ccdd.eeff`, Junos colon `aa:bb:cc:dd:ee:ff`). Web and GUI paths share the same normalization logic.

#### GET /api/mac-trace/last
Return the last MAC trace results.

**Response:**
```json
{
  "mac_address": "00:11:22:33:44:55",
  "devices": [...],
  "html_path": "/path/to/report.html"
}
```

#### GET /api/mac-trace/report
Serve the MAC trace HTML report.

**Response:** HTML file (text/html)

---

### Description Search

#### GET /api/description-search/last
Return the last description search results.

**Response:**
```json
{
  "search_term": "server",
  "matches": [...],
  "html_path": "/path/to/report.html"
}
```

#### GET /api/description-search/report
Serve the description search HTML report.

**Response:** HTML file (text/html)

---

### Ping Scan

#### GET /api/ping-scan/last
Return the last ping scan results.

**Response:**
```json
{
  "subnet": "10.1.1.0/24",
  "results": [...],
  "html_path": "/path/to/report.html"
}
```

#### GET /api/ping-scan/report
Serve the ping scan HTML report.

**Response:** HTML file (text/html)

---

### Search It Progress

#### GET /api/search-it/progress
Return progress for all search_it operations (MAC trace, description search, ping scan).

**Response:**
```json
{
  "mac_trace": {"status": "complete", "progress": 100},
  "description_search": {"status": "running", "progress": 45},
  "ping_scan": {"status": "idle", "progress": 0}
}
```

---

### STP Swiss Tools

#### POST /api/stp/run
Run STP topology analysis.

**Request:**
```json
{
  "username": "admin",
  "password": "password",
  "enable_pwd": "enable_password",
  "vlan_id": 100,
  "demo_mode": false
}
```

**Response:**
```json
{
  "job_id": "stp_job_789",
  "status": "started"
}
```

#### GET /api/stp/status/<job_id>
Poll STP job status.

**Response:**
```json
{
  "status": "complete",
  "result": {...},
  "error": null
}
```

---

### Config Templates

#### GET /api/templates/list
List available configuration templates.

**Response:**
```json
{
  "templates": [
    {
      "name": "cisco_ios_ntp.j2",
      "description": "NTP configuration template"
    }
  ]
}
```

#### POST /api/templates/save
Save a new configuration template.

**Request:**
```json
{
  "name": "custom_template.j2",
  "content": "{{ ntp_servers }}",
  "description": "Custom NTP template"
}
```

**Response:**
```json
{
  "status": "saved",
  "path": "/path/to/template.j2"
}
```

#### POST /api/templates/render
Render a template with provided variables.

**Request:**
```json
{
  "template_name": "cisco_ios_ntp.j2",
  "variables": {
    "ntp_servers": ["10.1.1.1", "10.1.1.2"]
  }
}
```

**Response:**
```json
{
  "rendered_config": "ntp server 10.1.1.1\nntp server 10.1.1.2"
}
```

#### GET /api/templates/get/<template_name>
Get template content.

**Response:**
```json
{
  "name": "cisco_ios_ntp.j2",
  "content": "{{ ntp_servers }}",
  "variables": ["ntp_servers"]
}
```

#### GET /api/templates/presets
Get available template presets.

**Response:**
```json
{
  "presets": [
    {
      "name": "NX-OS Trunk",
      "template": "nxos_trunk.j2",
      "variables": {...}
    }
  ]
}
```

---

### Topology

#### POST /api/topology/run
Run topology mapper.

**Request:**
```json
{
  "username": "admin",
  "password": "password",
  "enable_pwd": "enable_password",
  "scope": "bulk",
  "devices": ["10.1.1.1"]
}
```

**Response:**
```json
{
  "status": "started"
}
```

#### GET /api/topology/status
Get last topology job status.

**Response:**
```json
{
  "status": "complete",
  "devices_ok": 5,
  "devices_total": 5
}
```

#### GET /api/topology/open
Open the last completed topology map in browser.

**Response:** HTML file (text/html)

#### GET /api/topology/open-diagnostics
Open the topology diagnostics folder.

**Response:** JSON with folder path

---

### Static Assets

#### GET /favicon.ico
Serve favicon from root directory.

**Response:** Image file (image/x-icon)

#### GET /static/favicon_program.png
Serve favicon from static path for HTML reference.

**Response:** Image file (image/png)

#### GET /favicon_program.png
Serve favicon from root path for HTML reference.

**Response:** Image file (image/png)

---

## WebSocket API (Socket.IO)

### CLI Terminal

#### Event: cli_connect
Establish CLI terminal connection to a device.

**Request:**
```json
{
  "session_id": "cli_session_123",
  "host": "10.1.1.1",
  "device_type": "cisco_ios",
  "username": "admin",
  "password": "password"
}
```

**Response Events:**
- `cli_status`: Connection status (`connecting`, `connected`, `error`)
- `cli_output`: Terminal output from device
- `cli_error`: Error messages

#### Event: cli_data
Send input data to CLI terminal.

**Request:**
```json
{
  "session_id": "cli_session_123",
  "data": "show version\n"
}
```

**Response:** `cli_output` event with command output

#### Event: cli_resize
Resize CLI terminal PTY.

**Request:**
```json
{
  "session_id": "cli_session_123",
  "cols": 80,
  "rows": 24
}
```

**Response:** None (acknowledged)

#### Event: cli_disconnect
Disconnect CLI terminal session.

**Request:**
```json
{
  "session_id": "cli_session_123"
}
```

**Response:** `cli_status` event with status `disconnected`

---

## Error Codes

| Code | Description | Common Causes | Resolution |
|------|-------------|---------------|------------|
| 200 | Success | Request completed successfully | N/A |
| 400 | Bad Request | Invalid parameters, missing required fields | Check request parameters and format |
| 401 | Unauthorized | Invalid credentials | Verify username/password |
| 404 | Not Found | Resource or device not found | Check resource path or device IP |
| 413 | Payload Too Large | File upload exceeds size limit | Reduce file size or increase limit |
| 500 | Internal Server Error | Server-side error | Check server logs and retry |

---

## Common Response Format

### Success Response
```json
{
  "status": "success",
  "data": {...}
}
```

### Error Response
```json
{
  "status": "error",
  "error": "Error message",
  "details": {...}
}
```

---

## Error Handling Patterns

### 1. Invalid Parameters (400 Bad Request)

**Scenario:** Missing or invalid request parameters

**Request:**
```json
{
  "action": "invalid_action",
  "username": "admin"
}
```

**Error Response:**
```json
{
  "status": "error",
  "error": "Invalid request parameters",
  "details": {
    "field": "action",
    "message": "Invalid action: invalid_action",
    "valid_actions": ["connectivity", "vlan_check", "mac_check"]
  }
}
```

**Resolution:**
- Check valid parameter values in documentation
- Ensure all required fields are present
- Validate parameter types and formats

---

### 2. Authentication Failure (401 Unauthorized)

**Scenario:** Invalid device credentials

**Request:**
```json
{
  "username": "admin",
  "password": "wrong_password"
}
```

**Error Response:**
```json
{
  "status": "error",
  "error": "Authentication failed",
  "details": {
    "message": "Invalid credentials",
    "device": "10.1.1.1",
    "attempts_remaining": 2
  }
}
```

**Resolution:**
- Verify username and password
- Check enable password if required
- Ensure device is accessible
- Check device authentication configuration

---

### 3. Resource Not Found (404 Not Found)

**Scenario:** Requested resource does not exist

**Request:**
```
GET /api/plugins/history/nonexistent_plugin
```

**Error Response:**
```json
{
  "status": "error",
  "error": "Plugin not found",
  "details": {
    "plugin_id": "nonexistent_plugin",
    "message": "Plugin does not exist",
    "available_plugins": ["network_discovery", "standards_validator"]
  }
}
```

**Resolution:**
- Check resource identifier
- Verify resource exists
- Check spelling and case sensitivity
- Review available resources

---

### 4. File Too Large (413 Payload Too Large)

**Scenario:** Uploaded file exceeds size limit

**Request:**
```
POST /api/plugins/upload
Content-Type: multipart/form-data
```

**Error Response:**
```json
{
  "status": "error",
  "error": "File too large",
  "details": {
    "max_size": "10MB",
    "actual_size": "15MB",
    "message": "File size exceeds maximum allowed size"
  }
}
```

**Resolution:**
- Reduce file size
- Compress file if applicable
- Split large files into smaller chunks
- Increase size limit if necessary

---

### 5. Internal Server Error (500 Internal Server Error)

**Scenario:** Server-side error occurred

**Request:**
```
POST /api/execute
```

**Error Response:**
```json
{
  "status": "error",
  "error": "Internal server error",
  "details": {
    "message": "Failed to start job",
    "error_id": "ERR_12345",
    "timestamp": "2026-06-02T12:00:00Z"
  }
}
```

**Resolution:**
- Check server logs for details
- Verify server resources (CPU, memory, disk)
- Check network connectivity
- Restart application if necessary
- Contact support with error ID

---

## Error Recovery Procedures

### 1. Network Connectivity Errors

**Symptoms:**
- Connection timeout
- Device unreachable
- Authentication failure

**Recovery Steps:**
1. Verify network connectivity to device
2. Check device IP address and hostname
3. Verify device is powered on
4. Check firewall rules
5. Verify device credentials
6. Test with manual SSH/Telnet connection
7. Check device authentication configuration

**Prevention:**
- Use reliable network infrastructure
- Monitor device availability
- Implement redundancy
- Regular credential rotation

---

### 2. Plugin Loading Errors

**Symptoms:**
- Plugin fails to load
- Import errors
- Dependency missing

**Recovery Steps:**
1. Check plugin syntax and structure
2. Verify Python dependencies are installed
3. Check plugin file permissions
4. Review plugin error logs
5. Test plugin in isolation
6. Reinstall plugin if corrupted
7. Use plugin debug endpoint for troubleshooting

**Prevention:**
- Test plugins before deployment
- Use version control for plugins
- Monitor plugin health
- Regular plugin updates

---

### 3. File Upload Errors

**Symptoms:**
- File too large
- Invalid file format
- Validation failure

**Recovery Steps:**
1. Check file size against limits
2. Verify file format is supported
3. Validate file content
4. Check available disk space
5. Verify file permissions
6. Retry upload with smaller file
7. Use alternative upload method

**Prevention:**
- Compress files before upload
- Validate files locally
- Use appropriate file formats
- Monitor disk space

---

### 4. Job Execution Errors

**Symptoms:**
- Job fails to start
- Job hangs
- Job fails during execution

**Recovery Steps:**
1. Check job status endpoint
2. Review job logs
3. Verify device credentials
4. Check device availability
5. Verify job parameters
6. Cancel and retry job
7. Check system resources

**Prevention:**
- Validate parameters before job submission
- Monitor job progress
- Implement job timeouts
- Use job retry logic

---

### 5. Health Check Failures

**Symptoms:**
- Inventory check fails
- Port check fails
- Plugin check fails
- CLI smoke test fails

**Recovery Steps:**
1. Review failed check details
2. Check inventory file exists and is valid
3. Verify application port is not in use
4. Check plugin loading
5. Verify CLI connectivity
6. Restart application if needed
7. Check system resources

**Prevention:**
- Regular health checks
- Monitor system resources
- Implement alerts for failures
- Regular maintenance

---

## Rate Limiting

No rate limiting is enforced (local network use only).

---

## Authentication

No authentication is required (designed for local network use only). Ensure the application is not exposed to untrusted networks.

---

## WebSocket Connection

**URL:** `http://127.0.0.1:5051/socket.io/`  
**Transports:** `websocket`, `polling`  
**Socket.IO Client Version:** 5.x

---

## Notes

- All POST requests require `Content-Type: application/json` header
- File uploads use `multipart/form-data`
- WebSocket events require a valid `session_id` for CLI operations
- Job-based operations (discovery, STP) return a `job_id` for status polling
- HTML report endpoints return HTML files directly (not JSON)

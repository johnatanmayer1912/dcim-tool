# P18: Logging Utilities

| Field | Value |
|-------|-------|
| **Prompt ID** | P18 |
| **Phase** | 05-utilities |
| **Dependency Level** | 1 (Depends on Phase 1) |
| **Estimated Time** | 10 minutes |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-02 |

---

## Purpose

Reconstruct logging utilities for application logging. This module provides logging configuration, log rotation, and structured logging functions.

---

## Prerequisites

- Phase 1 (Foundation) completed
- Python environment set up
- logs directory created

---

## Instructions

### Step 1: Create logging_utilities Module

```bash
cd modules
```

---

### Step 2: Create logging_utilities.py

```python
"""
Logging Utilities

Application logging configuration and utilities.
"""

import logging
import logging.handlers
import os
from datetime import datetime
import json

def setup_logging(log_level='INFO', log_file='logs/application.log', max_bytes=10485760, backup_count=5):
    """
    Setup application logging with rotation
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Log file path
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
    
    Returns:
        logging.Logger: Configured logger
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setLevel(getattr(logging, log_level.upper()))
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    return logger

def get_logger(name):
    """
    Get logger with specified name
    
    Args:
        name: Logger name
    
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)

def log_structured(logger, level, message, **kwargs):
    """
    Log structured data as JSON
    
    Args:
        logger: Logger instance
        level: Log level (debug, info, warning, error, critical)
        message: Log message
        **kwargs: Additional structured data
    """
    log_data = {
        'message': message,
        'timestamp': datetime.utcnow().isoformat(),
        **kwargs
    }
    
    log_method = getattr(logger, level.lower())
    log_method(json.dumps(log_data))

class ContextFilter(logging.Filter):
    """Filter to add context information to log records"""
    
    def __init__(self, context=None):
        super().__init__()
        self.context = context or {}
    
    def filter(self, record):
        """Add context to log record"""
        for key, value in self.context.items():
            setattr(record, key, value)
        return True

def add_context_filter(logger, context):
    """
    Add context filter to logger
    
    Args:
        logger: Logger instance
        context: Context dictionary
    """
    context_filter = ContextFilter(context)
    logger.addFilter(context_filter)

def setup_job_logging(job_id, log_level='INFO'):
    """
    Setup logging for specific job
    
    Args:
        job_id: Job identifier
        log_level: Logging level
    
    Returns:
        logging.Logger: Configured logger for job
    """
    # Create job-specific log file
    log_file = f'logs/jobs/{job_id}.log'
    
    # Setup logging
    logger = setup_logging(log_level=log_level, log_file=log_file)
    
    # Add context
    add_context_filter(logger, {'job_id': job_id})
    
    return logger

def setup_plugin_logging(plugin_id, log_level='INFO'):
    """
    Setup logging for specific plugin
    
    Args:
        plugin_id: Plugin identifier
        log_level: Logging level
    
    Returns:
        logging.Logger: Configured logger for plugin
    """
    # Create plugin-specific log file
    log_file = f'logs/plugins/{plugin_id}.log'
    
    # Setup logging
    logger = setup_logging(log_level=log_level, log_file=log_file)
    
    # Add context
    add_context_filter(logger, {'plugin_id': plugin_id})
    
    return logger
```

---

### Step 3: Create logging Configuration File

```bash
cat > config_logging.yaml << 'EOF'
# Logging Configuration

version: 1
disable_existing_loggers: false

formatters:
  detailed:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
  simple:
    format: '%(asctime)s - %(levelname)s - %(message)s'
  json:
    format: '%(message)s'
    class: pythonjsonlogger.jsonlogger.JsonFormatter

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: simple
    stream: ext://sys.stdout
  
  file:
    class: logging.handlers.RotatingFileHandler
    level: INFO
    formatter: detailed
    filename: logs/application.log
    maxBytes: 10485760
    backupCount: 5
  
  error_file:
    class: logging.handlers.RotatingFileHandler
    level: ERROR
    formatter: detailed
    filename: logs/errors.log
    maxBytes: 10485760
    backupCount: 5

loggers:
  '':
    level: INFO
    handlers: [console, file, error_file]
    propagate: false
  
  modules:
    level: DEBUG
    handlers: [console, file]
    propagate: false
  
  plugins:
    level: INFO
    handlers: [console, file]
    propagate: false
EOF
```

---

### Step 4: Validate Logging Utilities

```python
# Test logging utilities
from modules.logging_utilities import (
    setup_logging,
    get_logger,
    log_structured,
    setup_job_logging,
    setup_plugin_logging
)

# Test basic logging
logger = setup_logging()
assert logger is not None
assert logger.level == 20  # INFO level

# Test get_logger
test_logger = get_logger('test')
assert test_logger is not None

# Test structured logging
log_structured(logger, 'info', 'Test message', key='value')

# Test job logging
job_logger = setup_job_logging('test-job-123')
assert job_logger is not None

# Test plugin logging
plugin_logger = setup_plugin_logging('test-plugin')
assert plugin_logger is not None

print("Logging utilities validation successful")
```

---

## Validation Checklist

- [ ] logging_utilities.py created
- [ ] setup_logging implemented
- [ ] get_logger implemented
- [ ] log_structured implemented
- [ ] ContextFilter implemented
- [ ] add_context_filter implemented
- [ ] setup_job_logging implemented
- [ ] setup_plugin_logging implemented
- [ ] Logging configuration file created
- [ ] Logging utilities validation successful
- [ ] Utilities phase complete
- [ ] Ready for integration reconstruction

---

## Troubleshooting

### Issue: Log file creation fails

**Solution:**
- Verify logs directory exists
- Check write permissions
- Verify disk space

### Issue: Log rotation not working

**Solution:**
- Verify RotatingFileHandler configuration
- Check max_bytes setting
- Test with large log file

---

## Next Steps

After completing this prompt, Phase 5 (Utilities) is complete. Proceed to Phase 6: Integration (can run in parallel with Phase 5)

---

## References

- CODE_INVENTORY.md: ../../02-codebase/CODE_INVENTORY.md
- UTILITIES_DOCUMENTATION.md: ../../02-codebase/UTILITIES_DOCUMENTATION.md

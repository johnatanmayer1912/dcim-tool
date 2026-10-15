"""
utils/structured_logger.py
-------------------------
Production-grade structured logging system for Network Swiss Tool Pro.

Provides JSON-structured logs with log levels, operation tracing, and device context.
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional
from functools import wraps


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class OperationType(Enum):
    CONNECTIVITY_CHECK = "connectivity_check"
    VLAN_AUDIT = "vlan_audit"
    VLAN_ADD = "vlan_add"
    VLAN_RENAME = "vlan_rename"
    VLAN_DELETE = "vlan_delete"
    VLAN_COMPARE = "vlan_compare"
    MAC_TRACE = "mac_trace"
    CONFIG_BACKUP = "config_backup"
    CONFIG_SAVE = "config_save"
    CONFIG_ROLLBACK = "config_rollback"
    INTERFACE_CHECK = "interface_check"
    TOPOLOGY_MAP = "topology_map"
    NETWORK_AUDIT = "network_audit"
    NODE_ANALYZE = "node_analyze"


class ConfigState(Enum):
    PENDING = "pending"
    PUSHED = "pushed"
    VERIFIED = "verified"
    COMMITTED = "committed"
    SAVED = "saved"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class NetworkLogger:
    """
    Production-grade structured logger for network operations.
    
    Features:
    - JSON-structured logs with consistent schema
    - Multiple output handlers (file, console)
    - Operation tracing with device context
    - Config state tracking
    - Audit trail for compliance
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, log_dir: str = None, console_output: bool = True):
        if NetworkLogger._initialized:
            return

        if log_dir is None:
            from utils.output_paths import get_logs_dir
            log_dir = get_logs_dir()

        self.log_dir = log_dir
        self.console_output = console_output
        self._ensure_log_dir()
        
        # Initialize loggers
        self.operation_logger = self._create_logger("operations", "operations.log")
        self.error_logger = self._create_logger("errors", "errors.log", level=logging.WARNING)
        self.audit_logger = self._create_logger("audit", "audit.log")
        
        # Console handler for GUI/Web integration
        if console_output:
            self.console_handler = logging.StreamHandler(sys.stdout)
            self.console_handler.setLevel(logging.INFO)
            console_fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
            self.console_handler.setFormatter(console_fmt)
            self.operation_logger.addHandler(self.console_handler)
        
        # Callback for GUI/Web log integration
        self._gui_callback = None
        
        NetworkLogger._initialized = True
    
    def _ensure_log_dir(self):
        """Ensure log directory exists."""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def _create_logger(self, name: str, filename: str, level: int = logging.INFO) -> logging.Logger:
        """Create a configured logger with JSON formatting."""
        logger = logging.getLogger(f"network_swiss_tool.{name}")
        logger.setLevel(level)
        
        # Remove existing handlers to prevent duplicates
        logger.handlers = []
        
        # File handler with JSON formatting
        log_path = os.path.join(self.log_dir, filename)
        file_handler = logging.FileHandler(log_path, mode='a', encoding='utf-8')
        file_handler.setLevel(level)
        
        # Custom JSON formatter
        formatter = JsonFormatter()
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def set_gui_callback(self, callback):
        """Set callback for GUI/Web log integration."""
        self._gui_callback = callback
    
    def _notify_gui(self, message: str, level: str = "INFO"):
        """Notify GUI/Web of log message."""
        if self._gui_callback:
            try:
                self._gui_callback(message, level)
            except Exception:
                pass
    
    def _create_log_entry(self, 
                          level: LogLevel,
                          message: str,
                          operation: Optional[OperationType] = None,
                          device: Optional[str] = None,
                          context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a structured log entry."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": level.value,
            "message": message,
            "component": "network_swiss_tool"
        }
        
        if operation:
            entry["operation"] = operation.value
        if device:
            entry["device"] = device
        if context:
            entry["context"] = context
            
        return entry
    
    def log(self, 
            level: LogLevel,
            message: str,
            operation: Optional[OperationType] = None,
            device: Optional[str] = None,
            context: Optional[Dict[str, Any]] = None):
        """General structured logging method."""
        entry = self._create_log_entry(level, message, operation, device, context)
        
        # Log to appropriate logger
        log_method = getattr(self.operation_logger, level.value.lower())
        log_method(json.dumps(entry))
        
        # Notify GUI/Web
        self._notify_gui(message, level.value)
    
    def debug(self, message: str, operation: Optional[OperationType] = None, 
              device: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """Log debug message."""
        self.log(LogLevel.DEBUG, message, operation, device, context)
    
    def info(self, message: str, operation: Optional[OperationType] = None,
             device: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """Log info message."""
        self.log(LogLevel.INFO, message, operation, device, context)
    
    def warning(self, message: str, operation: Optional[OperationType] = None,
                device: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        self.log(LogLevel.WARNING, message, operation, device, context)
    
    def error(self, message: str, operation: Optional[OperationType] = None,
              device: Optional[str] = None, context: Optional[Dict[str, Any]] = None,
              exception: Optional[Exception] = None):
        """Log error message."""
        if context is None:
            context = {}
        if exception:
            context["exception"] = str(exception)
            context["exception_type"] = type(exception).__name__
        self.log(LogLevel.ERROR, message, operation, device, context)
        
        # Also log to error logger
        entry = self._create_log_entry(LogLevel.ERROR, message, operation, device, context)
        self.error_logger.error(json.dumps(entry))
    
    def critical(self, message: str, operation: Optional[OperationType] = None,
                 device: Optional[str] = None, context: Optional[Dict[str, Any]] = None,
                 exception: Optional[Exception] = None):
        """Log critical message."""
        if context is None:
            context = {}
        if exception:
            context["exception"] = str(exception)
            context["exception_type"] = type(exception).__name__
        self.log(LogLevel.CRITICAL, message, operation, device, context)
        
        # Also log to error logger
        entry = self._create_log_entry(LogLevel.CRITICAL, message, operation, device, context)
        self.error_logger.critical(json.dumps(entry))
    
    # === Operation-Specific Logging Methods ===
    
    def log_operation_start(self, operation: OperationType, device: str,
                          parameters: Dict[str, Any]):
        """Log operation start with parameters."""
        context = {
            "event": "operation_start",
            "parameters": parameters
        }
        self.info(f"Starting {operation.value} on {device}", operation, device, context)
    
    def log_operation_complete(self, operation: OperationType, device: str,
                             duration_ms: int, result: str, details: Dict[str, Any]):
        """Log operation completion."""
        context = {
            "event": "operation_complete",
            "duration_ms": duration_ms,
            "result": result,
            "details": details
        }
        self.info(f"Completed {operation.value} on {device}: {result}", operation, device, context)
    
    def log_config_state_change(self, operation: OperationType, device: str,
                               vlan_id: str, from_state: ConfigState, to_state: ConfigState,
                               commands: Optional[list] = None):
        """Log configuration state change."""
        context = {
            "event": "config_state_change",
            "vlan_id": vlan_id,
            "from_state": from_state.value,
            "to_state": to_state.value,
            "commands": commands or []
        }
        self.info(f"Config state change: {from_state.value} -> {to_state.value}",
                 operation, device, context)
    
    def log_backup_created(self, device: str, backup_path: str, trigger: str,
                          snapshot_cmd: str):
        """Log backup creation."""
        context = {
            "event": "backup_created",
            "backup_path": backup_path,
            "trigger": trigger,
            "snapshot_command": snapshot_cmd
        }
        self.info(f"Backup created for {device}", OperationType.CONFIG_BACKUP, device, context)
    
    def log_backup_restore(self, device: str, backup_path: str, success: bool,
                          error: Optional[str] = None):
        """Log backup restore operation."""
        context = {
            "event": "backup_restore",
            "backup_path": backup_path,
            "success": success,
            "error": error
        }
        if success:
            self.info(f"Backup restored for {device}", OperationType.CONFIG_ROLLBACK, device, context)
        else:
            self.error(f"Backup restore failed for {device}", OperationType.CONFIG_ROLLBACK,
                      device, context)
    
    def log_verification_result(self, operation: OperationType, device: str,
                              check_type: str, expected: Any, actual: Any,
                              passed: bool):
        """Log verification check result."""
        context = {
            "event": "verification",
            "check_type": check_type,
            "expected": expected,
            "actual": actual,
            "passed": passed
        }
        level = LogLevel.INFO if passed else LogLevel.WARNING
        status = "PASSED" if passed else "FAILED"
        self.log(level, f"Verification {status}: {check_type}", operation, device, context)
    
    def log_dry_run(self, operation: OperationType, device: str, commands: list):
        """Log dry-run command preview."""
        context = {
            "event": "dry_run",
            "commands": commands,
            "would_execute": False
        }
        self.info(f"Dry-run mode - commands preview", operation, device, context)
    
    def log_idempotency_skip(self, operation: OperationType, device: str,
                            vlan_id: str, reason: str):
        """Log idempotency-based operation skip."""
        context = {
            "event": "idempotency_skip",
            "vlan_id": vlan_id,
            "reason": reason
        }
        self.info(f"Skipped {operation.value} - idempotency check: {reason}",
                 operation, device, context)
    
    def log_connection_event(self, device: str, event: str, success: bool,
                           details: Optional[Dict[str, Any]] = None):
        """Log connection-related event."""
        context = {
            "event": f"connection_{event}",
            "success": success,
            "details": details or {}
        }
        level = LogLevel.INFO if success else LogLevel.ERROR
        status = "succeeded" if success else "failed"
        self.log(level, f"Connection {event} {status}", None, device, context)


class JsonFormatter(logging.Formatter):
    """Custom formatter for JSON log output."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # If message is already JSON, use it directly
        try:
            json.loads(record.getMessage())
            return record.getMessage()
        except (json.JSONDecodeError, ValueError):
            # Create structured entry from plain message
            entry = {
                "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
                "level": record.levelname,
                "message": record.getMessage(),
                "logger": record.name,
                "line": record.lineno
            }
            return json.dumps(entry)


def get_logger(log_dir: str = None, console_output: bool = True) -> NetworkLogger:
    """Get or create the singleton logger instance."""
    return NetworkLogger(log_dir, console_output)


def log_operation(operation_type: OperationType):
    """Decorator for automatic operation logging."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger()
            device = kwargs.get('device', {}).get('host', 'unknown') if kwargs.get('device') else 'unknown'
            
            # Extract parameters (excluding credentials)
            safe_params = {k: v for k, v in kwargs.items() 
                           if k not in ('user', 'pwd', 'enb_pwd', 'password')}
            
            logger.log_operation_start(operation_type, device, safe_params)
            
            start_time = datetime.now(timezone.utc)
            try:
                result = func(*args, **kwargs)
                duration = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
                
                status = result.get('status', 'unknown') if isinstance(result, dict) else 'success'
                logger.log_operation_complete(operation_type, device, duration, status, 
                                            {"result": result})
                return result
            except Exception as e:
                duration = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
                logger.error(f"Operation failed: {str(e)}", operation_type, device,
                           {"duration_ms": duration}, exception=e)
                raise
        return wrapper
    return decorator


# Legacy compatibility wrapper
class LegacyLogAdapter:
    """
    Adapter to provide legacy-style logging interface while using structured logger.
    Maintains backward compatibility with existing code.
    """
    
    def __init__(self, logger: NetworkLogger, operation: Optional[OperationType] = None,
                 device: Optional[str] = None):
        self.logger = logger
        self.operation = operation
        self.device = device
    
    def __call__(self, message: str):
        """Allow adapter to be called like a function (legacy interface)."""
        self.info(message)
    
    def debug(self, message: str, context: Optional[Dict[str, Any]] = None):
        self.logger.debug(message, self.operation, self.device, context)
    
    def info(self, message: str, context: Optional[Dict[str, Any]] = None):
        self.logger.info(message, self.operation, self.device, context)
    
    def warning(self, message: str, context: Optional[Dict[str, Any]] = None):
        self.logger.warning(message, self.operation, self.device, context)
    
    def error(self, message: str, exception: Optional[Exception] = None,
              context: Optional[Dict[str, Any]] = None):
        self.logger.error(message, self.operation, self.device, context, exception)
    
    def set_device(self, device: str):
        """Update the device context."""
        self.device = device
    
    def set_operation(self, operation: OperationType):
        """Update the operation context."""
        self.operation = operation


def create_legacy_adapter(operation: Optional[OperationType] = None,
                         device: Optional[str] = None) -> LegacyLogAdapter:
    """Create a legacy-compatible logging adapter."""
    logger = get_logger()
    return LegacyLogAdapter(logger, operation, device)

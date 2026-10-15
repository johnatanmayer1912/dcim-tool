"""
utils/app_logger.py
-------------------
Production-grade application logging for Network Swiss Tool Pro v6.5.3.

DESIGN GOALS:
  - Never crash the application (all logging is fail-safe)
  - Structured JSON output for machine parsing / AI analysis
  - Human-readable console output for operators
  - Full stack traces on exceptions
  - Input context included (device, operation, command)
  - Export capability for AI/post-mortem analysis
  - Thread-safe (multiple concurrent device operations)

LOG FILES:
  logs/app.log          — All events (INFO+), JSON lines
  logs/errors.log       — Errors and criticals only, JSON lines
  logs/audit.log        — Config-change audit trail, JSON lines
  logs/operations.log   — Per-operation structured events

USAGE:
  from utils.app_logger import get_app_logger
  log = get_app_logger()

  log.info("Starting VLAN audit", device="10.1.1.1", operation="vlan_audit")
  log.error("SSH failed", device="10.1.1.1", exc=e, context={"command": "show vlan"})
  log.audit("VLAN 100 added", device="10.1.1.1", before="absent", after="present")
"""

import json
import logging
import logging.handlers
import os
import re
import sys
import traceback
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional


# ── Constants ─────────────────────────────────────────────────────────────────
LOG_DIR = "logs"
APP_LOG_FILE = "app.log"
ERROR_LOG_FILE = "errors.log"
AUDIT_LOG_FILE = "audit.log"
OPS_LOG_FILE = "operations.log"
MAX_BYTES = 10 * 1024 * 1024   # 10 MB per file
BACKUP_COUNT = 5                # Keep 5 rotated files


_SECRET_PATTERNS = [
    re.compile(r'((?:password|secret|enable_pwd|admin_password)[\'"]?\s*[:=]\s*[\'"]?)[^\'"\s,;]+([\'"]?)', re.IGNORECASE),
]

def _scrub_secrets(text: str) -> str:
    """Zero-Trust: scrub any passwords or secrets from logged text."""
    if not text:
        return ""
    scrubbed = str(text)
    for pat in _SECRET_PATTERNS:
        scrubbed = pat.sub(r'\1***REDACTED***\2', scrubbed)
    return scrubbed


# ── JSON Formatter ─────────────────────────────────────────────────────────────
class _JsonLineFormatter(logging.Formatter):
    """Emit one JSON object per log line. Machine-parseable."""

    def format(self, record: logging.LogRecord) -> str:
        # Base fields always present
        entry: Dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
            "msg": _scrub_secrets(record.getMessage()),
        }

        # Extra fields injected via log.info(..., extra={...})
        for key in ("device", "operation", "command", "context", "exc_info_str",
                    "duration_ms", "result", "audit_before", "audit_after"):
            val = getattr(record, key, None)
            if val is not None:
                if isinstance(val, str):
                    entry[key] = _scrub_secrets(val)
                elif isinstance(val, dict):
                    # scrub dict values
                    entry[key] = {
                        k: ('***REDACTED***' if any(s in k.lower() for s in ('pass', 'secret', 'key', 'token')) else (_scrub_secrets(v) if isinstance(v, str) else v))
                        for k, v in val.items()
                    }
                else:
                    entry[key] = val

        # Exception info
        if record.exc_info:
            entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": _scrub_secrets(str(record.exc_info[1])) if record.exc_info[1] else None,
                "traceback": [_scrub_secrets(line) for line in traceback.format_exception(*record.exc_info)],
            }

        try:
            return json.dumps(entry, default=str)
        except Exception:
            # Last-resort: plain string so logging never crashes
            return json.dumps({"ts": entry["ts"], "level": "ERROR",
                               "msg": f"[LOG SERIALIZATION FAILED] {_scrub_secrets(record.getMessage())}"})


# ── Human-readable console formatter ──────────────────────────────────────────
class _ConsoleFormatter(logging.Formatter):
    """Compact, coloured-friendly console output."""

    LEVEL_ICONS = {
        "DEBUG":    "🔍",
        "INFO":     "ℹ️ ",
        "WARNING":  "⚠️ ",
        "ERROR":    "❌",
        "CRITICAL": "🔥",
    }

    def format(self, record: logging.LogRecord) -> str:
        icon = self.LEVEL_ICONS.get(record.levelname, "  ")
        ts = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        device = getattr(record, "device", None)
        op = getattr(record, "operation", None)

        prefix_parts = [f"[{ts}]", f"{icon} {record.levelname:<8}"]
        if op:
            prefix_parts.append(f"[{op}]")
        if device:
            prefix_parts.append(f"[{device}]")

        clean_msg = _scrub_secrets(record.getMessage())
        line = " ".join(prefix_parts) + f" {clean_msg}"

        if record.exc_info:
            line += "\n" + _scrub_secrets(self.formatException(record.exc_info))

        return line


# ── Core AppLogger ─────────────────────────────────────────────────────────────
class AppLogger:
    """
    Thread-safe, fail-safe application logger.

    All public methods are guaranteed not to raise exceptions —
    logging failures are silently swallowed so the application
    never crashes due to a logging error.
    """

    _instance: Optional["AppLogger"] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._ready = False
            return cls._instance

    def __init__(self, log_dir: str = None, console: bool = True,
                 console_level: str = "INFO"):
        if self._ready:
            return
        with self._lock:
            if self._ready:
                return
            if log_dir is None:
                from utils.output_paths import get_logs_dir
                log_dir = get_logs_dir()
            self._log_dir = log_dir
            self._console = console
            self._gui_callbacks = []   # list of callables(msg, level)
            self._setup(console_level)
            self._ready = True

    # ── Setup ──────────────────────────────────────────────────────────────────
    def _setup(self, console_level: str):
        """Create log directory and configure all handlers."""
        try:
            os.makedirs(self._log_dir, exist_ok=True)
        except Exception:
            pass  # Can't create log dir — continue without file logging

        self._app_logger   = self._make_logger("nstp.app",   APP_LOG_FILE,   logging.DEBUG)
        self._error_logger = self._make_logger("nstp.error", ERROR_LOG_FILE, logging.ERROR)
        self._audit_logger = self._make_logger("nstp.audit", AUDIT_LOG_FILE, logging.INFO)
        self._ops_logger   = self._make_logger("nstp.ops",   OPS_LOG_FILE,   logging.INFO)

        if self._console:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(getattr(logging, console_level, logging.INFO))
            handler.setFormatter(_ConsoleFormatter())
            self._app_logger.addHandler(handler)

    def _make_logger(self, name: str, filename: str, level: int) -> logging.Logger:
        """Create a rotating-file logger with JSON formatting."""
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        logger.handlers = []

        try:
            path = os.path.join(self._log_dir, filename)
            handler = logging.handlers.RotatingFileHandler(
                path, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT,
                encoding="utf-8"
            )
            handler.setLevel(level)
            handler.setFormatter(_JsonLineFormatter())
            logger.addHandler(handler)
        except Exception:
            pass  # File handler failed — logger still works (console only)

        return logger

    # ── GUI/Web callback registration ──────────────────────────────────────────
    def add_gui_callback(self, callback):
        """Register a callable(message: str, level: str) for UI log streaming."""
        if callable(callback):
            self._gui_callbacks.append(callback)

    def remove_gui_callback(self, callback):
        """Remove a previously registered GUI callback."""
        try:
            self._gui_callbacks.remove(callback)
        except ValueError:
            pass

    def _notify_gui(self, message: str, level: str):
        """Notify all registered GUI callbacks. Never raises."""
        for cb in list(self._gui_callbacks):
            try:
                cb(message, level)
            except Exception:
                pass

    # ── Internal emit ──────────────────────────────────────────────────────────
    def _emit(self, level: int, msg: str, *,
              device: Optional[str] = None,
              operation: Optional[str] = None,
              command: Optional[str] = None,
              context: Optional[Dict[str, Any]] = None,
              duration_ms: Optional[int] = None,
              result: Optional[str] = None,
              exc: Optional[BaseException] = None,
              exc_info: bool = False):
        """Core emit — all public methods delegate here."""
        try:
            extra: Dict[str, Any] = {}
            if device:      extra["device"]      = device
            if operation:   extra["operation"]   = operation
            if command:     extra["command"]      = command
            if context:     extra["context"]      = context
            if duration_ms is not None: extra["duration_ms"] = duration_ms
            if result:      extra["result"]       = result

            # Resolve exc_info
            _exc_info = None
            if exc is not None:
                _exc_info = (type(exc), exc, exc.__traceback__)
            elif exc_info:
                _exc_info = sys.exc_info()

            self._app_logger.log(level, msg, extra=extra, exc_info=_exc_info)

            # Mirror errors to error log
            if level >= logging.ERROR:
                self._error_logger.log(level, msg, extra=extra, exc_info=_exc_info)

            # Notify GUI
            level_name = logging.getLevelName(level)
            self._notify_gui(msg, level_name)

        except Exception:
            pass  # Logging must never crash the app

    # ── Public API ─────────────────────────────────────────────────────────────
    def debug(self, msg: str, **kwargs):
        self._emit(logging.DEBUG, msg, **kwargs)

    def info(self, msg: str, **kwargs):
        self._emit(logging.INFO, msg, **kwargs)

    def warning(self, msg: str, **kwargs):
        self._emit(logging.WARNING, msg, **kwargs)

    def error(self, msg: str, **kwargs):
        self._emit(logging.ERROR, msg, **kwargs)

    def critical(self, msg: str, **kwargs):
        self._emit(logging.CRITICAL, msg, **kwargs)

    def exception(self, msg: str, exc: BaseException, **kwargs):
        """Log an exception with full traceback."""
        self._emit(logging.ERROR, msg, exc=exc, **kwargs)

    # ── Operation lifecycle helpers ────────────────────────────────────────────
    def op_start(self, operation: str, device: str, params: Optional[Dict] = None):
        """Log the start of a network operation."""
        ctx = {"event": "op_start", "params": params or {}}
        self._emit(logging.INFO, f"[{operation}] Starting on {device}",
                   device=device, operation=operation, context=ctx)

    def op_success(self, operation: str, device: str, duration_ms: int,
                   details: Optional[Dict] = None):
        """Log successful completion of a network operation."""
        ctx = {"event": "op_success", "details": details or {}}
        self._emit(logging.INFO, f"[{operation}] Completed on {device} ({duration_ms}ms)",
                   device=device, operation=operation,
                   duration_ms=duration_ms, result="success", context=ctx)

    def op_fail(self, operation: str, device: str, duration_ms: int,
                error: str, exc: Optional[BaseException] = None):
        """Log failed network operation."""
        ctx = {"event": "op_fail", "error": error}
        self._emit(logging.ERROR, f"[{operation}] FAILED on {device} ({duration_ms}ms): {error}",
                   device=device, operation=operation,
                   duration_ms=duration_ms, result="fail", context=ctx, exc=exc)

    def cmd_sent(self, device: str, command: str, operation: Optional[str] = None):
        """Log a command being sent to a device."""
        self._emit(logging.DEBUG, f"CMD → {command}",
                   device=device, operation=operation, command=command)

    def cmd_result(self, device: str, command: str, lines: int,
                   operation: Optional[str] = None):
        """Log command response received."""
        self._emit(logging.DEBUG, f"CMD ← {lines} lines",
                   device=device, operation=operation, command=command,
                   context={"response_lines": lines})

    # ── Audit trail ────────────────────────────────────────────────────────────
    def audit(self, msg: str, device: str, operation: str,
              before: Optional[str] = None, after: Optional[str] = None,
              user: Optional[str] = None):
        """
        Write an immutable audit trail entry.
        Used for all config-change operations (VLAN add/rename/delete, save config).
        """
        try:
            entry = {
                "ts": datetime.now(tz=timezone.utc).isoformat(),
                "event": "audit",
                "msg": msg,
                "device": device,
                "operation": operation,
                "before": before,
                "after": after,
                "user": user,
            }
            self._audit_logger.info(json.dumps(entry, default=str))
            self._emit(logging.INFO, f"[AUDIT] {msg}",
                       device=device, operation=operation,
                       context={"before": before, "after": after})
        except Exception:
            pass

    # ── Export ─────────────────────────────────────────────────────────────────
    def export_logs(self, output_path: str, level_filter: str = "WARNING",
                    last_n_lines: int = 1000) -> bool:
        """
        Export recent log entries to a file for AI analysis or support.

        Args:
            output_path: Destination file path
            level_filter: Minimum level to include (DEBUG/INFO/WARNING/ERROR/CRITICAL)
            last_n_lines: Maximum number of lines to export per log file

        Returns:
            True if export succeeded, False otherwise
        """
        try:
            min_level = getattr(logging, level_filter.upper(), logging.WARNING)
            exported_lines = []
            exported_lines.append(f"# Log Export — {datetime.now().isoformat()}")
            exported_lines.append(f"# Level filter: {level_filter}+")
            exported_lines.append("")

            log_files = [APP_LOG_FILE, ERROR_LOG_FILE, AUDIT_LOG_FILE]
            for fname in log_files:
                path = os.path.join(self._log_dir, fname)
                if not os.path.exists(path):
                    continue
                exported_lines.append(f"## {fname}")
                try:
                    with open(path, "r", encoding="utf-8", errors="replace") as f:
                        lines = f.readlines()
                    # Take last N lines
                    recent = lines[-last_n_lines:]
                    for line in recent:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            entry = json.loads(line)
                            entry_level = getattr(logging, entry.get("level", "INFO"), logging.INFO)
                            if entry_level >= min_level:
                                exported_lines.append(line)
                        except json.JSONDecodeError:
                            exported_lines.append(line)
                except Exception as e:
                    exported_lines.append(f"# ERROR reading {fname}: {e}")
                exported_lines.append("")

            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(exported_lines))
            return True

        except Exception:
            return False

    # ── Stats ──────────────────────────────────────────────────────────────────
    def get_log_stats(self) -> Dict[str, Any]:
        """Return basic stats about log files (sizes, line counts)."""
        stats = {}
        for fname in [APP_LOG_FILE, ERROR_LOG_FILE, AUDIT_LOG_FILE, OPS_LOG_FILE]:
            path = os.path.join(self._log_dir, fname)
            if os.path.exists(path):
                size = os.path.getsize(path)
                try:
                    with open(path, "r", encoding="utf-8", errors="replace") as f:
                        lines = sum(1 for _ in f)
                except Exception:
                    lines = -1
                stats[fname] = {"size_bytes": size, "lines": lines, "path": path}
            else:
                stats[fname] = {"size_bytes": 0, "lines": 0, "path": path}
        return stats


# ── Module-level singleton accessor ───────────────────────────────────────────
_logger_instance: Optional[AppLogger] = None


def get_app_logger(log_dir: str = None, console: bool = True,
                   console_level: str = "INFO") -> AppLogger:
    """
    Get (or create) the singleton AppLogger.

    Thread-safe. Safe to call from any module.

    Example:
        from utils.app_logger import get_app_logger
        log = get_app_logger()
        log.info("Starting", device="10.1.1.1", operation="vlan_audit")
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = AppLogger(log_dir=log_dir, console=console,
                                     console_level=console_level)
    return _logger_instance


# ── Convenience decorator ──────────────────────────────────────────────────────
def log_operation(operation_name: str):
    """
    Decorator that automatically logs operation start, success, and failure.

    Usage:
        @log_operation("vlan_audit")
        def run(device, user, pwd, enb_pwd, log_func=None):
            ...
    """
    import functools
    import time

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            log = get_app_logger()

            # Extract device host from first positional arg or kwargs
            device_host = "unknown"
            if args and isinstance(args[0], dict):
                device_host = args[0].get("host", "unknown")
            elif "device" in kwargs and isinstance(kwargs["device"], dict):
                device_host = kwargs["device"].get("host", "unknown")

            log.op_start(operation_name, device_host)
            t0 = time.monotonic()

            try:
                result = func(*args, **kwargs)
                duration = int((time.monotonic() - t0) * 1000)

                # Inspect result for status
                if isinstance(result, dict):
                    status = result.get("status", "unknown")
                    if status == "fail":
                        log.op_fail(operation_name, device_host, duration,
                                    result.get("error", "unknown error"))
                    else:
                        log.op_success(operation_name, device_host, duration)
                else:
                    log.op_success(operation_name, device_host, duration)

                return result

            except Exception as exc:
                duration = int((time.monotonic() - t0) * 1000)
                log.op_fail(operation_name, device_host, duration, str(exc), exc=exc)
                raise

        return wrapper
    return decorator

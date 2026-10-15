"""
runtime_hook_stdout_fix.py
-------------------------
Runtime hook for PyInstaller to fix stdout/stderr issues in no-console builds.
This hook MUST be included in EVERY PyInstaller spec for this project.

Fixes multiple issues:
1. AttributeError: 'NoneType' object has no attribute 'isatty' (uvicorn/logging)
2. TypeError: write() argument must be str, not bytes (colorama)
3. ValueError: I/O operation on closed file (click._winconsole)
4. OSError: [Errno 9] Bad file descriptor (click._winconsole._is_console)

MANDATORY: This hook must be listed in runtime_hooks in every spec file.
"""

import sys
import io
import os

class NullWriter:
    """
    A null writer that completely replaces stdout/stderr in no-console builds.
    All methods are safe and return appropriate values to prevent crashes.
    """

    def __init__(self):
        self._closed = False
        self._buffer = []

    def write(self, s):
        """Silently ignore all writes."""
        if self._closed:
            return 0
        if isinstance(s, bytes):
            try:
                s = s.decode('utf-8', errors='replace')
            except (AttributeError, UnicodeDecodeError):
                s = str(s)
        self._buffer.append(s)
        return len(s)

    def writelines(self, lines):
        """Silently ignore all line writes."""
        if self._closed:
            return
        for line in lines:
            self.write(line)

    def flush(self):
        """Do nothing on flush."""
        pass

    def close(self):
        """Mark as closed but don't actually close anything."""
        self._closed = True

    @property
    def closed(self):
        """Always return our safe closed state."""
        return self._closed

    def isatty(self):
        """Always return False - we're not a TTY."""
        return False

    def fileno(self):
        """Return -1 to indicate no valid file descriptor."""
        return -1

    def seek(self, offset, whence=0):
        """Do nothing on seek."""
        return 0

    def tell(self):
        """Always return 0."""
        return 0

    def truncate(self, size=None):
        """Do nothing on truncate."""
        return 0

    def read(self, size=-1):
        """Always return empty string."""
        return ''

    def readline(self, size=-1):
        """Always return empty string."""
        return ''

    def readlines(self, hint=-1):
        """Always return empty list."""
        return []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def __repr__(self):
        return "<NullWriter>"


# CRITICAL FIX: Patch Click's Windows console detection BEFORE it tries to access invalid handles
# This prevents OSError: [Errno 9] Bad file descriptor in click._winconsole._is_console
try:
    import click._winconsole
    # Replace _is_console with a safe version that never accesses file descriptors
    _original_is_console = getattr(click._winconsole, '_is_console', None)
    def _safe_is_console(f):
        """Always return False - we're in a no-console PyInstaller build."""
        return False
    click._winconsole._is_console = _safe_is_console
except (ImportError, AttributeError):
    # Click might not be imported yet, or the module structure changed
    # We'll try again when Click is imported
    pass


# MANDATORY: Replace stdout and stderr immediately with safe null writers
# This MUST happen before any imports that might use stdout/stderr
sys.stdout = NullWriter()
sys.stderr = NullWriter()

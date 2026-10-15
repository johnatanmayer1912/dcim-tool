"""
Network Swiss Tool Pro - Core Application

Main Flask application entry point.
Refactored from vlan_checker_web.py for enterprise architecture.

v7.0.0 - Enterprise Architecture Refactor
"""

import sys
import os

# CRITICAL: Install telnetlib compatibility for Python 3.13+
try:
    import telnetlib
except ImportError:
    import telnetlib_compat  # noqa: F401

import re
import time
import threading
import webbrowser
from datetime import datetime
from flask import Flask, render_template, request, jsonify

# Flask-SocketIO for CLI terminal interface
try:
    from flask_socketio import SocketIO, emit, disconnect, join_room
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False
    print("[WARNING] flask-socketio not available. CLI terminal feature disabled.")


def _get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def _read_version() -> str:
    """Read version from VERSION file (single source of truth)."""
    try:
        path = _get_resource_path("VERSION")
        with open(path, 'r', encoding='utf-8') as f:
            return f.read().strip().lstrip('v')
    except Exception:
        return "0.0.0-DEV"


# Flask app configuration
if getattr(sys, 'frozen', False):
    # When bundled with PyInstaller
    template_folder = os.path.join(sys._MEIPASS, "src", "web", "templates")
    static_folder = os.path.join(sys._MEIPASS, "src", "web", "static")
else:
    # Development mode
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    template_folder = os.path.join(base_dir, "src", "web", "templates")
    static_folder = os.path.join(base_dir, "src", "web", "static")

app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
app.config['VERSION'] = _read_version()

# Initialize SocketIO
socketio = None
if SOCKETIO_AVAILABLE:
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')


# Import core modules (refactored imports)
from src.adapters.vlan_adapter import VlanAdapter
from src.adapters.topology_adapter import TopologyAdapter
from src.adapters.interface_adapter import InterfaceAdapter
from src.adapters.backup_adapter import BackupAdapter
from src.plugins.registry import PluginRegistry


@app.route('/')
def index():
    """Main application page."""
    return render_template('index.html', version=app.config['VERSION'])


@app.route('/api/version')
def api_version():
    """Return application version."""
    return jsonify({
        'version': app.config['VERSION'],
        'socketio_available': SOCKETIO_AVAILABLE
    })


def run_app(debug: bool = False, port: int = 5051) -> None:
    """Run the Flask application."""
    if socketio:
        socketio.run(app, debug=debug, port=port)
    else:
        app.run(debug=debug, port=port)


if __name__ == '__main__':
    run_app()

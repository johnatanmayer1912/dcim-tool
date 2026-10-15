# ============================================================================
# AI_NAVIGATION_BREADCRUMBS - modules/plugin_registry.py
# ============================================================================
# PURPOSE: Plugin discovery, validation, and execution system.
# SINGLETON: Use PluginRegistry() instance for all plugin operations.
#
# PLUGIN_DIRECTORY: modules/plugins/ (or bundled in PyInstaller _MEIPASS)
# SIDECAR_SUPPORT: Loads from plugins/ directory next to executable if writable
#
# KEY_FUNCTIONS:
#   - reload(): Scan plugins/, validate METADATA, load modules
#   - get_all_metadata(): Return list of plugin METADATA dicts
#   - execute(plugin_id, device, credentials, params, config, log_func): Run plugin
#   - _load_plugin(): Load single plugin file with AST validation
#
# PLUGIN_CONTRACT:
#   Each plugin must have METADATA dict at module level with:
#   - plugin_id: Unique identifier
#   - display_name: Human-readable name
#   - version: Semantic version
#   - category: Plugin category (Audit, Discovery, etc.)
#   - required_params: Dict of parameter definitions
#
# EXECUTION_FLOW:
#   1. reload() discovers plugins in modules/plugins/
#   2. _load_plugin() parses AST, validates METADATA, loads module
#   3. execute() calls plugin.run(device, credentials, params, config, log_func)
#   4. Plugin returns JSON result via build_json()
#
# SECURITY:
#   - BANNED_IMPORTS list prevents dangerous imports
#   - AST parsing validates code before execution
#   - No os.system, subprocess, eval, exec allowed
#
# CONNECTIONS:
#   - Called by: vlan_checker_web.py (plugin listing and execution)
#   - Calls: modules/plugins/*.py (individual plugins)
#   - Uses: modules/network_base.py (for build_json helper)
#
# ============================================================================
# v6.0.10: MODULE-LEVEL PATH INJECTION - Must happen BEFORE any imports
import sys
if getattr(sys, 'frozen', False):
    exe_path = getattr(sys, '_MEIPASS', None)
    if exe_path and exe_path not in sys.path:
        sys.path.insert(0, exe_path)
        print(f"[REGISTRY v6.0.10] MODULE-LEVEL: Added EXE path: {exe_path}", file=sys.stderr)

"""
modules/plugin_registry.py
-------------------------
Plugin Discovery and Registry System for Network Swiss Tool Pro v6.0.

The PluginRegistry is a singleton that:
1. Scans modules/plugins/ for .py files
2. Extracts METADATA without executing unsafe code
3. Validates plugin contracts
4. Supports hot-reloading
5. Manages plugin execution

Usage:
    from modules.plugin_registry import PluginRegistry
    registry = PluginRegistry()
    plugins = registry.get_all_metadata()
"""

import os
import sys
import ast
import shutil
import types
import importlib.util
import shutil
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional, Callable, Tuple


class PluginRegistry:
    """Singleton plugin registry for discovering and managing plugins."""
    
    _instance = None
    _initialized = False
    
    BANNED_IMPORTS = [
        'os.system', 'os.popen', 'subprocess.call', 'subprocess.Popen',
        'shutil.rmtree', 'eval', 'exec', 'compile(', '__import__',
        'ctypes', 'pickle.loads', 'socket.socket', 'pty.spawn',
        'urllib.request', 'http.client',
    ]
    
    REQUIRED_META_KEYS = ['plugin_id', 'display_name', 'version', 'category']

    @staticmethod
    def _count_plugin_py(plugins_dir: str) -> int:
        if not os.path.isdir(plugins_dir):
            return 0
        return len([
            f for f in os.listdir(plugins_dir)
            if f.endswith('.py') and not f.startswith('__')
        ])

    @staticmethod
    def _bundled_plugins_dir() -> str:
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            bundled = os.path.join(sys._MEIPASS, 'modules', 'plugins')
            if os.path.isdir(bundled):
                return bundled
        return ''

    def _resolve_frozen_plugins_dir(self, exe_dir: str, requested: Optional[str]) -> str:
        """NEW-C1: load from bundled MEIPASS or seed sidecar plugins/."""
        sidecar = requested or os.path.join(exe_dir, 'plugins')
        bundled = self._bundled_plugins_dir()
        if bundled and self._count_plugin_py(bundled) >= 10:
            if not os.access(exe_dir, os.W_OK):
                return bundled
            # Always ensure any missing bundled plugins are copied into sidecar
            try:
                os.makedirs(sidecar, exist_ok=True)
                for fn in os.listdir(bundled):
                    if not fn.endswith('.py') or fn.startswith('__'):
                        continue
                    dst = os.path.join(sidecar, fn)
                    if not os.path.isfile(dst):
                        shutil.copy2(os.path.join(bundled, fn), dst)
                        print(f"[REGISTRY] Synced missing bundled plugin to sidecar: {fn}")
            except Exception as exc:
                print(f"[REGISTRY] Sidecar sync warning ({exc}); continuing")

        if self._count_plugin_py(sidecar) >= 10:
            return sidecar
        if bundled and self._count_plugin_py(bundled) >= 10:
            return bundled
        return sidecar
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, plugins_dir: str = None):
        if PluginRegistry._initialized:
            return
        
        from utils.output_paths import get_backups_root, get_scratch_dir

        # v7.0.35: Writable plugin scratch/backups under data root (never install dir)
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
            self.plugins_dir = self._resolve_frozen_plugins_dir(exe_dir, plugins_dir)
        else:
            self.plugins_dir = plugins_dir or os.path.join(os.path.dirname(__file__), 'plugins')
        self.backup_dir = os.path.join(get_backups_root(), 'plugins')
        self.scratch_dir = get_scratch_dir()
        
        self._plugins: Dict[str, Dict[str, Any]] = {}
        self._errors: List[Dict[str, Any]] = []
        
        try:
            os.makedirs(self.plugins_dir, exist_ok=True)
            os.makedirs(self.backup_dir, exist_ok=True)
            os.makedirs(self.scratch_dir, exist_ok=True)
        except Exception as e:
            print(f"[REGISTRY v6.9.3] FATAL: Failed to create directories: {e}")
            # Final fallback to absolute temp
            import tempfile
            self.scratch_dir = tempfile.gettempdir()
        
        self.reload()
        PluginRegistry._initialized = True
    
    def reload(self) -> None:
        """Re-scan plugins directory and rebuild registry."""
        self._plugins = {}
        self._errors = []
        
        print(f"[REGISTRY v6.0.10] Reloading plugins from: {self.plugins_dir}")
        print(f"[REGISTRY v6.0.10] Directory exists: {os.path.exists(self.plugins_dir)}")
        
        if not os.path.exists(self.plugins_dir):
            print(f"[REGISTRY v6.0.10] WARNING: plugins_dir does not exist!")
            return
        
        # List all files in plugins directory
        try:
            all_files = os.listdir(self.plugins_dir)
            py_files = [f for f in all_files if f.endswith('.py') and not f.startswith('__')]
            print(f"[REGISTRY v6.0.10] Files in plugins_dir: {all_files}")
            print(f"[REGISTRY v6.0.10] Python files found: {py_files}")
        except Exception as e:
            print(f"[REGISTRY v6.0.10] ERROR listing directory: {e}")
            return
        
        for filename in sorted(os.listdir(self.plugins_dir)):
            if not filename.endswith('.py') or filename.startswith('__'):
                continue
            file_path = os.path.join(self.plugins_dir, filename)
            print(f"[REGISTRY v6.0.10] Loading plugin: {filename}")
            try:
                self._load_plugin(file_path)
                print(f"[REGISTRY v6.0.10] SUCCESS: Loaded {filename}")
            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                print(f"[REGISTRY v6.0.10] ERROR loading {filename}: {error_msg}")
                self._errors.append({'file': filename, 'error': error_msg, 'type': 'load_error'})
        
        print(f"[REGISTRY v6.0.10] Reload complete: {len(self._plugins)} plugins, {len(self._errors)} errors")
        if self._errors:
            for err in self._errors:
                print(f"[REGISTRY v6.0.10]   - {err['file']}: {err['error']}")
    
    def _load_plugin(self, file_path: str) -> None:
        """Load and validate a single plugin file."""
        filename = os.path.basename(file_path)
        print(f"[REGISTRY v6.0.10] _load_plugin: Starting {filename}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"[REGISTRY v6.0.10] _load_plugin: Read {len(content)} bytes")
        except Exception as e:
            print(f"[REGISTRY v6.0.10] _load_plugin: ERROR reading file: {e}")
            raise ValueError(f"Cannot read file: {e}")
        
        try:
            tree = ast.parse(content)
            print(f"[REGISTRY v6.0.10] _load_plugin: Parsed AST successfully")
        except SyntaxError as e:
            print(f"[REGISTRY v6.0.10] _load_plugin: ERROR parsing: {e}")
            raise ValueError(f"Syntax error: {e}")
        
        metadata = self._extract_metadata(tree, filename)
        if not metadata:
            print(f"[REGISTRY v6.0.10] _load_plugin: ERROR - No METADATA found")
            raise ValueError(f"Missing METADATA")
        print(f"[REGISTRY v6.0.10] _load_plugin: Found metadata for plugin_id={metadata.get('plugin_id')}")
        
        self._validate_metadata(metadata, filename)
        plugin_id = metadata['plugin_id']
        print(f"[REGISTRY v6.0.10] _load_plugin: Validated metadata, plugin_id={plugin_id}")

        banned = self.banned_ast_reason(tree)
        if banned:
            print(f"[REGISTRY v6.0.10] _load_plugin: FAIL CLOSED banned pattern: {banned}")
            raise ValueError(f"Untrusted plugin ({banned}). AST denylist is not a sandbox.")

        if plugin_id in self._plugins:
            print(f"[REGISTRY v6.0.10] _load_plugin: ERROR - Duplicate plugin_id '{plugin_id}'")
            self._errors.append({'file': filename, 'error': f"Duplicate plugin_id '{plugin_id}'", 'type': 'duplicate_id'})
            return
        
        print(f"[REGISTRY v6.0.10] _load_plugin: Loading module...")
        module = self._load_module_safely(file_path, plugin_id)
        
        if not hasattr(module, 'run'):
            print(f"[REGISTRY v6.0.10] _load_plugin: ERROR - Module has no 'run' function")
            raise ValueError(f"Missing 'run' function")
        
        print(f"[REGISTRY v6.0.10] _load_plugin: Module loaded successfully with 'run' function")
        
        self._plugins[plugin_id] = {
            'metadata': metadata,
            'module': module,
            'file_path': file_path,
            'filename': filename,
            'last_modified': os.path.getmtime(file_path)
        }
        print(f"[REGISTRY v6.0.10] _load_plugin: Plugin {plugin_id} registered")
    
    def _extract_metadata(self, tree: ast.AST, filename: str) -> Optional[Dict]:
        """Extract METADATA dict from AST."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == 'METADATA':
                        try:
                            return ast.literal_eval(node.value)
                        except:
                            return None
        return None
    
    def _validate_metadata(self, metadata: Dict, filename: str) -> None:
        """Validate metadata has required keys."""
        for key in self.REQUIRED_META_KEYS:
            if key not in metadata:
                raise ValueError(f"Missing METADATA key: {key}")
        
        pid = metadata['plugin_id']
        if not re.match(r'^[a-z][a-z0-9_]*$', pid):
            raise ValueError("plugin_id must be snake_case")

    _BANNED_CALL_NAMES = frozenset({'eval', 'exec', 'compile'})
    _BANNED_ATTR = frozenset({
        ('os', 'system'),
        ('os', 'popen'),
        ('subprocess', 'call'),
        ('subprocess', 'Popen'),
        ('shutil', 'rmtree'),
        ('socket', 'socket'),
        ('pickle', 'loads'),
        ('pty', 'spawn'),
    })
    _BANNED_MODULES = frozenset({'ctypes', 'urllib.request', 'http.client'})

    @classmethod
    def banned_ast_reason(cls, tree: ast.AST) -> Optional[str]:
        """Fail-closed denylist on AST (comments and re.compile are not matches).

        Not a sandbox: uns listed dangerous APIs can still run.
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id in cls._BANNED_CALL_NAMES:
                    return func.id + '('
                if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                    pair = (func.value.id, func.attr)
                    if pair in cls._BANNED_ATTR:
                        return f'{pair[0]}.{pair[1]}'
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name
                    if name in cls._BANNED_MODULES or name == 'ctypes' or name.startswith('ctypes.'):
                        return name
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ''
                if mod in cls._BANNED_MODULES or mod.startswith('urllib.request') or mod.startswith('http.client'):
                    return mod
                if mod == 'ctypes':
                    return 'ctypes'
                if mod == 'os':
                    for alias in node.names:
                        if alias.name in ('system', 'popen'):
                            return f'os.{alias.name}'
                if mod == 'subprocess':
                    for alias in node.names:
                        if alias.name in ('call', 'Popen'):
                            return f'subprocess.{alias.name}'
                if mod == 'shutil':
                    for alias in node.names:
                        if alias.name == 'rmtree':
                            return 'shutil.rmtree'
                if mod == 'socket':
                    for alias in node.names:
                        if alias.name == 'socket':
                            return 'socket.socket'
                if mod == 'pickle':
                    for alias in node.names:
                        if alias.name == 'loads':
                            return 'pickle.loads'
        return None

    @classmethod
    def banned_content_reason(cls, content: str) -> Optional[str]:
        try:
            tree = ast.parse(content or '')
        except SyntaxError:
            return None
        return cls.banned_ast_reason(tree)
    
    def _load_module_safely(self, file_path: str, plugin_id: str) -> Optional[Any]:
        """Load a plugin module using importlib.util for proper import context."""
        module_name = f"plugin_{plugin_id}"
        print(f"[REGISTRY v6.0.10] _load_module_safely: Loading {plugin_id}")
        print(f"[REGISTRY v6.0.10] _load_module_safely: file_path = {file_path}")

        # Ensure sys.path includes the project root so plugins can import
        # modules.network_base, utils.report_formatter, etc.
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
            print(f"[REGISTRY v6.0.10] Added project root to sys.path: {project_root}")

        # EXE mode: also ensure _MEIPASS is on sys.path
        if getattr(sys, 'frozen', False):
            exe_internal = getattr(sys, '_MEIPASS', None)
            if exe_internal and exe_internal not in sys.path:
                sys.path.insert(0, exe_internal)
                print(f"[REGISTRY v6.0.10] Added EXE internal path: {exe_internal}")

        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot create module spec for {file_path}")

            module = importlib.util.module_from_spec(spec)
            module.__package__ = ''   # top-level module, no parent package

            # Register BEFORE exec so circular/self-referential imports resolve
            sys.modules[module_name] = module
            print(f"[REGISTRY v6.0.10] Registered in sys.modules: {module_name}")

            spec.loader.exec_module(module)
            print(f"[REGISTRY v6.0.10] Module executed successfully")
            return module

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print(f"[REGISTRY v6.0.10] ERROR loading {plugin_id}: {type(e).__name__}: {e}")
            print(f"[REGISTRY v6.0.10] Traceback:\n{tb}")
            # Clean up sys.modules on failure to avoid stale entries
            sys.modules.pop(module_name, None)
            # Re-raise so _load_plugin() captures the real error message
            raise
    
    def get_all_metadata(self) -> List[Dict]:
        """Return metadata for all registered plugins."""
        return [p['metadata'] for p in self._plugins.values()]
    
    def get_plugin(self, plugin_id: str) -> Optional[Dict]:
        """Get full plugin record by ID."""
        return self._plugins.get(plugin_id)
    
    def exists(self, plugin_id: str) -> bool:
        """Check if a plugin exists."""
        return plugin_id in self._plugins
    
    def get_errors(self) -> List[Dict]:
        """Get list of loading errors."""
        return self._errors.copy()
    
    # ===================================================================
    # PLUGIN EXECUTION
    # ===================================================================
    
    def execute(self, plugin_id: str, device: Dict, credentials: Dict, 
                params: Dict, config: Dict, log_func: Optional[Callable] = None) -> Dict:
        """Execute a plugin on a single device."""
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            return {'status': 'fail', 'error': f"Plugin '{plugin_id}' not found", 'data': {}}
        
        try:
            result = plugin['module'].run(device, credentials, params, config, log_func)
            if not isinstance(result, dict):
                return {'status': 'fail', 'error': 'Plugin must return dict', 'data': {}}
            return result
        except Exception as e:
            return {'status': 'fail', 'error': str(e), 'data': {}}
    
    def execute_parallel(self, plugin_id: str, devices: List[Dict], 
                         credentials: Dict, params: Dict, config: Dict,
                         log_func: Optional[Callable] = None,
                         max_workers: int = 10) -> List[Dict]:
        """Execute a plugin on multiple devices in parallel."""
        results = []
        
        def run_on_device(device):
            return self.execute(plugin_id, device, credentials, params, config, log_func)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(run_on_device, dev): dev for dev in devices}
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    dev = futures[future]
                    results.append({'status': 'fail', 'device': dev.get('host'), 'error': str(e), 'data': {}})
        
        return results
    
    # ===================================================================
    # UPLOAD & ROLLBACK (Gatekeeper)
    # ===================================================================
    
    def validate_upload(self, file_path: str) -> Tuple[bool, str]:
        """Validate a plugin file before promoting to production."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Syntax check (catches IndentationError as well)
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                # Provide more detailed error message for indentation errors
                if 'indentation' in str(e).lower():
                    return False, f"Indentation error: {e}"
                return False, f"Syntax error: {e}"
            except IndentationError as e:
                return False, f"Indentation error: {e}"
            
            # METADATA check
            metadata = self._extract_metadata(tree, os.path.basename(file_path))
            if not metadata:
                return False, "Missing METADATA dictionary"

            banned = self.banned_ast_reason(tree)
            if banned:
                return False, f"Security violation: {banned} is not allowed"

            return True, "Valid"
        except Exception as e:
            return False, str(e)
    
    def promote_plugin(self, source_path: str) -> Tuple[bool, str]:
        """Runtime HTTP promotion is disabled (RB-ZT-01). Never copy into plugins_dir."""
        return False, (
            'Runtime plugin promotion is disabled. Place trusted .py files in '
            'the plugins directory offline, then reload.'
        )
    
    def get_plugin_history(self, plugin_id: str) -> List[Dict]:
        """Get backup history for a plugin."""
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            return []
        
        filename = plugin['filename']
        backup_subdir = os.path.join(self.backup_dir, filename.replace('.py', ''))
        
        if not os.path.exists(backup_subdir):
            return []
        
        history = []
        for f in sorted(os.listdir(backup_subdir), reverse=True):
            if f.endswith('.py'):
                path = os.path.join(backup_subdir, f)
                history.append({
                    'filename': f,
                    'timestamp': datetime.fromtimestamp(os.path.getmtime(path)).isoformat(),
                    'path': path
                })
        return history
    
    def rollback(self, plugin_id: str, backup_filename: str) -> Tuple[bool, str]:
        """Rollback a plugin to a previous version."""
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            return False, f"Plugin '{plugin_id}' not found"
        
        filename = plugin['filename']
        backup_path = os.path.join(self.backup_dir, filename.replace('.py', ''), backup_filename)
        prod_path = plugin['file_path']
        
        if not os.path.exists(backup_path):
            return False, f"Backup '{backup_filename}' not found"
        
        # Create new backup of current
        backup_subdir = os.path.join(self.backup_dir, filename.replace('.py', ''))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        current_backup = os.path.join(backup_subdir, f"{timestamp}_before_rollback_{filename}")
        shutil.copy2(prod_path, current_backup)
        
        # Restore backup
        shutil.copy2(backup_path, prod_path)
        
        # Reload
        self.reload()
        
        return True, f"Rolled back {filename} to {backup_filename}"


# Singleton accessor
_registry_instance = None

def get_registry() -> PluginRegistry:
    """Get the singleton registry instance."""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = PluginRegistry()
    return _registry_instance


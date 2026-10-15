"""
utils/config_backup_system.py
----------------------------
Comprehensive configuration backup system for Network Swiss Tool Pro.

Features:
- Automatic pre-change backups
- Scheduled backups with 24-hour monitoring
- Manual backup triggers
- Per-device organized storage
- Backup manifest with metadata
- Diff-friendly format
"""

import json
import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import threading
import hashlib

# v7.0.36: Ensure project root is on sys.path for absolute imports.
# utils/ has no __init__.py; relative imports (from ..) are invalid here.
_utils_proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _utils_proj_root not in sys.path:
    sys.path.insert(0, _utils_proj_root)
if getattr(sys, 'frozen', False):
    _utils_mei = getattr(sys, '_MEIPASS', None)
    if _utils_mei and _utils_mei not in sys.path:
        sys.path.insert(0, _utils_mei)

from utils.structured_logger import get_logger, OperationType


@dataclass
class BackupMetadata:
    """Metadata for a configuration backup."""
    device: str
    hostname: str
    timestamp: str
    backup_type: str  # 'pre_change', 'scheduled', 'manual'
    trigger: str  # Description of what triggered the backup
    snapshot_command: str
    file_hash: str
    file_size: int
    previous_backup: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ConfigBackupSystem:
    """
    Production-grade configuration backup system.
    
    Manages per-device configuration backups with automatic organization,
    metadata tracking, and scheduled backup monitoring.
    """
    
    BACKUP_DIR = "backups/devices"
    MANIFEST_FILE = "backup_manifest.json"
    MAX_BACKUPS_PER_DEVICE = 50  # Keep last N backups per device
    
    def __init__(self, backup_dir: str = None):
        self.backup_dir = backup_dir or self.BACKUP_DIR
        self.manifest_path = os.path.join(self.backup_dir, self.MANIFEST_FILE)
        self.logger = get_logger()
        self._lock = threading.Lock()
        
        self._ensure_backup_structure()
    
    def _ensure_backup_structure(self):
        """Ensure backup directory structure exists."""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir, exist_ok=True)
        
        # Initialize manifest if doesn't exist
        if not os.path.exists(self.manifest_path):
            self._save_manifest({"backups": [], "last_scheduled_run": None})
    
    def _sanitize_hostname(self, hostname: str) -> str:
        """Sanitize hostname for filesystem use."""
        # Replace problematic characters
        safe = hostname.replace(".", "_").replace(":", "_").replace("/", "_")
        safe = safe.replace("\\", "_").replace(" ", "_")
        return safe[:50]  # Limit length
    
    def _calculate_hash(self, content: str) -> str:
        """Calculate MD5 hash of content."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _get_device_backup_dir(self, hostname: str) -> str:
        """Get backup directory for a specific device."""
        safe_host = self._sanitize_hostname(hostname)
        device_dir = os.path.join(self.backup_dir, safe_host)
        if not os.path.exists(device_dir):
            os.makedirs(device_dir, exist_ok=True)
        return device_dir
    
    def _load_manifest(self) -> Dict[str, Any]:
        """Load backup manifest."""
        try:
            with open(self.manifest_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"backups": [], "last_scheduled_run": None}
    
    def _save_manifest(self, manifest: Dict[str, Any]):
        """Save backup manifest."""
        with self._lock:
            with open(self.manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2)
    
    def create_backup(self, 
                     device: str,
                     hostname: str,
                     config_content: str,
                     snapshot_command: str,
                     backup_type: str = "manual",
                     trigger: str = "User initiated") -> Dict[str, Any]:
        """
        Create a new configuration backup.
        
        Args:
            device: Device IP address
            hostname: Device hostname
            config_content: The configuration content to backup
            snapshot_command: The command used to retrieve the config
            backup_type: Type of backup ('pre_change', 'scheduled', 'manual')
            trigger: Description of what triggered this backup
            
        Returns:
            Dictionary with backup metadata
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        device_dir = self._get_device_backup_dir(hostname)
        
        # Create filename
        safe_type = backup_type.replace("_", "-")
        filename = f"config_{safe_type}_{timestamp}.txt"
        backup_path = os.path.join(device_dir, filename)
        
        # Calculate hash and size
        file_hash = self._calculate_hash(config_content)
        file_size = len(config_content.encode('utf-8'))
        
        # Get previous backup for this device
        manifest = self._load_manifest()
        device_backups = [b for b in manifest.get("backups", []) 
                         if b.get("hostname") == hostname]
        previous_backup = device_backups[-1].get("backup_path") if device_backups else None
        
        # Write backup file
        try:
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(config_content)
        except Exception as e:
            self.logger.error(f"Failed to write backup file: {str(e)}",
                            OperationType.CONFIG_BACKUP, device, exception=e)
            return {
                "success": False,
                "error": f"Failed to write backup: {str(e)}"
            }
        
        # Create metadata
        metadata = BackupMetadata(
            device=device,
            hostname=hostname,
            timestamp=timestamp,
            backup_type=backup_type,
            trigger=trigger,
            snapshot_command=snapshot_command,
            file_hash=file_hash,
            file_size=file_size,
            previous_backup=previous_backup
        )
        
        # Update manifest
        manifest_entry = metadata.to_dict()
        manifest_entry["backup_path"] = backup_path
        manifest["backups"].append(manifest_entry)
        
        # Cleanup old backups for this device
        self._cleanup_old_backups(hostname, manifest)
        
        self._save_manifest(manifest)
        
        # Log backup creation
        self.logger.log_backup_created(device, backup_path, trigger, snapshot_command)
        
        return {
            "success": True,
            "backup_path": backup_path,
            "metadata": metadata.to_dict()
        }
    
    def _cleanup_old_backups(self, hostname: str, manifest: Dict[str, Any]):
        """Remove old backups keeping only MAX_BACKUPS_PER_DEVICE most recent."""
        device_backups = [b for b in manifest.get("backups", []) 
                         if b.get("hostname") == hostname]
        
        if len(device_backups) > self.MAX_BACKUPS_PER_DEVICE:
            # Sort by timestamp descending
            sorted_backups = sorted(device_backups, 
                                   key=lambda x: x.get("timestamp", ""), 
                                   reverse=True)
            
            # Keep only the most recent
            to_keep = sorted_backups[:self.MAX_BACKUPS_PER_DEVICE]
            to_remove = sorted_backups[self.MAX_BACKUPS_PER_DEVICE:]
            
            # Remove old backup files
            for old_backup in to_remove:
                backup_path = old_backup.get("backup_path")
                if backup_path and os.path.exists(backup_path):
                    try:
                        os.remove(backup_path)
                    except Exception:
                        pass
            
            # Update manifest
            other_backups = [b for b in manifest.get("backups", []) 
                           if b.get("hostname") != hostname]
            manifest["backups"] = other_backups + to_keep
    
    def get_last_backup_time(self, hostname: str) -> Optional[datetime]:
        """Get timestamp of the most recent backup for a device.

        Checks the ConfigBackupSystem manifest first, then Tools run-folder
        backups under outputs/config_backup (same catalog as Compare).
        """
        candidates: List[datetime] = []
        manifest = self._load_manifest()
        device_backups = [b for b in manifest.get("backups", [])
                         if b.get("hostname") == hostname or b.get("device") == hostname]

        for row in device_backups:
            timestamp_str = row.get("timestamp", "")
            parsed = self._parse_backup_timestamp(timestamp_str)
            if parsed:
                candidates.append(parsed)

        # Also honor Tools → Config backup & save outputs (Oxidized-style catalog)
        try:
            from utils.backup_api import list_backup_records
            for row in list_backup_records(hostname=hostname):
                parsed = self._parse_backup_timestamp(row.get("timestamp") or "")
                if parsed:
                    candidates.append(parsed)
                mtime = row.get("mtime") or row.get("modified")
                if isinstance(mtime, (int, float)) and mtime > 0:
                    candidates.append(datetime.utcfromtimestamp(mtime))
        except Exception:
            pass

        if not candidates:
            return None
        return max(candidates)

    @staticmethod
    def _parse_backup_timestamp(timestamp_str: str) -> Optional[datetime]:
        raw = (timestamp_str or "").strip()
        if not raw:
            return None
        # Compact Tools/manifest stamp: 20261006_210000
        if len(raw) >= 15 and raw[8] == '_':
            try:
                return datetime.strptime(raw[:15], "%Y%m%d_%H%M%S")
            except ValueError:
                pass
        for fmt, width in (("%Y-%m-%dT%H:%M:%S", 19), ("%Y-%m-%d %H:%M:%S", 19)):
            try:
                return datetime.strptime(raw.replace("Z", "")[:width], fmt)
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(raw.replace("Z", ""))
        except ValueError:
            return None
    
    def check_backup_age(self, hostname: str, max_age_hours: int = 24) -> Dict[str, Any]:
        """
        Check if device's last backup is within acceptable age.
        
        Returns:
            Dict with status, last_backup_time, age_hours, and warning flag
        """
        last_backup = self.get_last_backup_time(hostname)
        
        if last_backup is None:
            return {
                "has_backup": False,
                "warning": True,
                "message": (
                    f"No backup found for {hostname}. "
                    "Use Tools → Config backup & save (or Fleet Backup)."
                ),
                "age_hours": None
            }
        
        now = datetime.utcnow()
        age = now - last_backup
        age_hours = age.total_seconds() / 3600
        
        warning = age_hours > max_age_hours
        
        return {
            "has_backup": True,
            "warning": warning,
            "message": f"Last backup: {age_hours:.1f} hours ago" if not warning 
                      else (
                          f"WARNING: Backup is {age_hours:.1f} hours old. "
                          "Refresh via Tools → Config backup & save."
                      ),
            "age_hours": age_hours,
            "last_backup": last_backup.isoformat()
        }
    
    def startup_backup_check(self, devices: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Check all devices on startup and return warnings for stale backups.
        
        Args:
            devices: List of device dicts with 'host' and expected 'hostname'
            
        Returns:
            List of warning dictionaries for devices with stale/missing backups
        """
        warnings = []
        
        for device in devices:
            hostname = device.get('hostname', device.get('host', 'unknown'))
            check_result = self.check_backup_age(hostname)
            
            if check_result["warning"]:
                warnings.append({
                    "device": device.get('host'),
                    "hostname": hostname,
                    **check_result
                })
                self.logger.warning(
                    f"Backup check: {check_result['message']}",
                    OperationType.CONFIG_BACKUP,
                    device.get('host')
                )
        
        return warnings
    
    def list_backups(self, hostname: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all backups or backups for a specific device."""
        manifest = self._load_manifest()
        backups = manifest.get("backups", [])
        
        if hostname:
            backups = [b for b in backups if b.get("hostname") == hostname]
        
        # Sort by timestamp descending
        return sorted(backups, key=lambda x: x.get("timestamp", ""), reverse=True)
    
    def get_backup_content(self, backup_path: str) -> Optional[str]:
        """Retrieve the content of a backup file."""
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Failed to read backup: {str(e)}",
                            OperationType.CONFIG_BACKUP)
            return None
    
    def compare_backups(self, backup_path1: str, backup_path2: str) -> Dict[str, Any]:
        """
        Compare two backup files and return differences.
        
        Returns:
            Dict with added_lines, removed_lines, and unified_diff
        """
        content1 = self.get_backup_content(backup_path1) or ""
        content2 = self.get_backup_content(backup_path2) or ""
        
        lines1 = content1.splitlines()
        lines2 = content2.splitlines()
        
        # Simple diff (can be enhanced with difflib)
        import difflib
        
        diff = list(difflib.unified_diff(
            lines1, lines2,
            fromfile=backup_path1,
            tofile=backup_path2,
            lineterm=''
        ))
        
        added = [line[1:] for line in diff if line.startswith('+') and not line.startswith('+++')]
        removed = [line[1:] for line in diff if line.startswith('-') and not line.startswith('---')]
        
        return {
            "added_count": len(added),
            "removed_count": len(removed),
            "added_lines": added,
            "removed_lines": removed,
            "unified_diff": '\n'.join(diff)
        }
    
    def auto_backup_pre_change(self, device: Dict[str, Any], 
                              user: str, pwd: str, enb_pwd: str,
                              change_description: str) -> Dict[str, Any]:
        """
        Automatically create backup before configuration change.
        
        Args:
            device: Device dictionary
            user, pwd, enb_pwd: Credentials
            change_description: Description of the pending change
            
        Returns:
            Dict with backup result
        """
        # v7.0.36 FIX: replaced illegal relative import (from ..modules) with
        # absolute import. utils/ has no __init__.py so '..' is beyond top-level.
        from modules.network_base import connect_device
        
        host = device.get('host', 'unknown')
        dtype = device.get('device_type', '')
        
        try:
            conn = connect_device(device, user, pwd, enb_pwd)
            
            # Get hostname from device
            try:
                prompt = conn.find_prompt()
                hostname = prompt.replace('#', '').replace('>', '').strip()
            except:
                hostname = host
            
            # Get config based on device type
            if "juniper" in dtype.lower():
                snapshot_cmd = "show configuration | display set"
            else:
                snapshot_cmd = "show running-config"
            
            config_content = conn.send_command(snapshot_cmd)
            conn.disconnect()
            
            # Create backup
            result = self.create_backup(
                device=host,
                hostname=hostname,
                config_content=config_content,
                snapshot_command=snapshot_cmd,
                backup_type="pre_change",
                trigger=f"Pre-change: {change_description}"
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Auto-backup failed: {str(e)}"
            self.logger.error(error_msg, OperationType.CONFIG_BACKUP, host, exception=e)
            return {
                "success": False,
                "error": error_msg
            }


# Singleton instance
_backup_system = None

def get_backup_system(backup_dir: str = None) -> ConfigBackupSystem:
    """Get or create the singleton backup system instance."""
    global _backup_system
    if _backup_system is None:
        if backup_dir is None:
            from utils.output_paths import get_backups_root
            backup_dir = os.path.join(get_backups_root(), 'devices')
        _backup_system = ConfigBackupSystem(backup_dir)
    return _backup_system

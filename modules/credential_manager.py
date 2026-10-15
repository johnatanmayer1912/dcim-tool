# ============================================================================
# AI_NAVIGATION_BREADCRUMBS - modules/credential_manager.py
# ============================================================================
# PURPOSE: Secure credential storage with Fernet encryption for offline use.
# STORAGE: .credentials.enc (encrypted), .credentials_meta.json (metadata)
#
# KEY_FUNCTIONS:
#   - add_credential(credential_id, username, password, ...): Store encrypted credential
#   - get_credential(credential_id): Retrieve decrypted credential
#   - list_credentials(): Return all credential IDs with metadata
#   - delete_credential(credential_id): Remove credential
#   - export_credentials(): Export encrypted backup
#   - import_credentials(): Import encrypted backup
#
# ENCRYPTION:
#   - Uses Fernet (AES-128 in CBC mode with HMAC)
#   - Operational key: machine-local .credential_key (always-on for daily use)
#   - Legacy master-password vaults: one-time unlock migrates to machine key
#
# CREDENTIAL_FIELDS:
#   - username: SSH username
#   - password: SSH password (encrypted)
#   - enable_pwd: Enable password (encrypted)
#   - snmp_version: SNMP version (2c, 3, or none)
#   - snmp_community: SNMP community (v2c)
#   - snmp_v3_user: SNMP v3 username
#   - snmp_v3_auth_protocol: SNMP v3 auth protocol
#   - snmp_v3_auth_key: SNMP v3 auth key (encrypted)
#   - snmp_v3_priv_protocol: SNMP v3 priv protocol
#   - snmp_v3_priv_key: SNMP v3 priv key (encrypted)
#
# CONNECTIONS:
#   - Called by: vlan_checker_web.py (credential management routes)
#   - Used by: utils/vault_credentials.py (credential resolution)
#   - Used by: utils/collection_credentials.py (credential bundling)
#
# USAGE_PATTERN:
#   cm = CredentialManager(storage_dir)
#   cm.add_credential('lab', 'admin', 'password')
#   cred = cm.get_credential('lab')
#
# ============================================================================
"""
Credential Manager Module
Secure credential storage and management for offline environments
Uses Fernet encryption for local password storage
"""

import os
import json
import base64
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id


def _credential_has_snmp(cred: dict) -> bool:
    ver = str(cred.get('snmp_version') or '').strip().lower()
    if ver in ('', 'none', 'off'):
        return False
    if ver in ('2c', 'v2c', '2') and cred.get('snmp_community'):
        return True
    if ver in ('3', 'v3') and cred.get('snmp_v3_user'):
        return True
    return False


class CredentialManager:
    """
    Manages secure credential storage with Fernet encryption
    Supports multiple credential sets with deduplication
    Provides export/import functionality for offline environments
    Supports master password for encryption key derivation
    """
    
    def __init__(self, storage_dir: str = None, master_password: str = None):
        """
        Initialize the credential manager
        
        Args:
            storage_dir: Directory to store credential files (defaults to current directory)
            master_password: Master password for encryption (if None, uses auto-generated key)
        """
        if storage_dir is None:
            storage_dir = os.getcwd()
        
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        self.credentials_file = os.path.join(storage_dir, ".credentials.enc")
        self.metadata_file = os.path.join(storage_dir, ".credentials_meta.json")
        self.master_password_file = os.path.join(storage_dir, ".credentials_master_hash")
        self.key_file = os.path.join(storage_dir, ".credential_key")
        
        # Prefer explicit constructor password (tests / one-shot tools).
        if master_password:
            self._key = self._derive_key_from_password(master_password)
            self.fernet = Fernet(self._key)
            self._save_master_password_hash(master_password)
        else:
            self.fernet = None
            self._key = None
            # Prefer machine key when present (daily-use model).
            if os.path.exists(self.key_file):
                try:
                    self._key = self._load_or_generate_key()
                    self.fernet = Fernet(self._key)
                    # Probe decrypt — if vault was master-encrypted this fails.
                    if os.path.exists(self.credentials_file):
                        with open(self.credentials_file, 'rb') as f:
                            self.fernet.decrypt(f.read())
                except Exception:
                    self.fernet = None
                    self._key = None
            if self.fernet is None and not os.path.exists(self.master_password_file):
                # Fresh / machine-key vault
                self._key = self._load_or_generate_key()
                self.fernet = Fernet(self._key)
            elif self.fernet is None and os.path.exists(self.master_password_file):
                # Legacy locked vault — one-time unlock migrates to machine key
                self.fernet = None
                self._key = None
        
        # Load credentials
        if self.fernet:
            self.credentials: Dict[str, dict] = self._load_credentials()
            # If a legacy master-hash remains but machine key works, drop the gate.
            if os.path.exists(self.master_password_file) and os.path.exists(self.key_file):
                try:
                    self.clear_master_password_gate(reencrypt=False)
                except Exception:
                    pass
        else:
            self.credentials: Dict[str, dict] = {}
    
    def _derive_key_from_password(self, password: str) -> bytes:
        """
        Derive encryption key from master password using Argon2id
        
        Args:
            password: Master password
            
        Returns:
            Encryption key as bytes
        """
        # Use a fixed salt for master password derivation (stored in metadata)
        salt_file = os.path.join(self.storage_dir, ".credentials_salt")
        if os.path.exists(salt_file):
            with open(salt_file, 'rb') as f:
                salt = f.read()
        else:
            salt = os.urandom(16)
            with open(salt_file, 'wb') as f:
                f.write(salt)
        
        kdf = Argon2id(
            salt=salt,
            length=32,
            iterations=3,
            lanes=4,
            memory_cost=2**16
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def _save_master_password_hash(self, password: str):
        """
        Save hash of master password for verification
        
        Args:
            password: Master password
        """
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        with open(self.master_password_file, 'w') as f:
            f.write(password_hash)
    
    def verify_master_password(self, password: str) -> bool:
        """
        Verify master password against stored hash
        
        Args:
            password: Password to verify
            
        Returns:
            True if password matches, False otherwise
        """
        if not os.path.exists(self.master_password_file):
            return False
        
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        with open(self.master_password_file, 'r') as f:
            stored_hash = f.read().strip()
        
        return password_hash == stored_hash
    
    def set_master_password(self, password: str) -> Tuple[bool, str]:
        """Legacy: create a master-password-encrypted vault (discouraged).

        Daily operator use should rely on the machine-local key. Prefer
        export-with-password for portable backups. Kept for migration tests /
        recovery tooling.
        """
        if not password:
            return False, "Password cannot be empty"
        if self.is_master_password_required():
            return False, (
                "Vault is locked; unlock with the current master password before changing it"
            )
        if self.fernet is None:
            return False, "Credential vault is not available"
        old_credentials = dict(self.credentials)

        self._key = self._derive_key_from_password(password)
        self.fernet = Fernet(self._key)
        self._save_master_password_hash(password)
        self.credentials = old_credentials
        self._save_credentials()

        if os.path.exists(self.key_file):
            os.remove(self.key_file)
        return True, "Master password set successfully"

    def clear_master_password_gate(self, reencrypt: bool = True) -> Tuple[bool, str]:
        """Remove master-password gate; keep credentials on machine-local key."""
        if self.fernet is None:
            return False, "Vault is locked; unlock once to migrate, then credentials stay available"
        if reencrypt or not os.path.exists(self.key_file):
            old = dict(self.credentials)
            self._key = self._load_or_generate_key()
            self.fernet = Fernet(self._key)
            self.credentials = old
            self._save_credentials()
        if os.path.exists(self.master_password_file):
            try:
                os.remove(self.master_password_file)
            except OSError as exc:
                return False, f"Failed to remove master password gate: {exc}"
        return True, "Master password gate cleared — credentials use the local machine key"
    
    def is_master_password_required(self) -> bool:
        """
        Check if master password is required to access credentials
        
        Returns:
            True if master password is required, False otherwise
        """
        return os.path.exists(self.master_password_file) and self.fernet is None
    
    def unlock_with_master_password(self, password: str) -> bool:
        """Unlock a legacy master-password vault, then migrate to machine key."""
        if not self.verify_master_password(password):
            return False
        
        self._key = self._derive_key_from_password(password)
        self.fernet = Fernet(self._key)
        self.credentials = self._load_credentials()
        # One-time migration: never require unlock again on this machine.
        self.clear_master_password_gate(reencrypt=True)
        return True
        
    def _load_or_generate_key(self) -> bytes:
        """
        Load existing encryption key or generate a new one
        
        Returns:
            Encryption key as bytes
        """
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                return f.read()
        
        # Generate new key
        key = Fernet.generate_key()
        with open(self.key_file, 'wb') as f:
            f.write(key)
        return key
    
    def _load_credentials(self) -> Dict[str, dict]:
        """
        Load credentials from encrypted storage
        
        Returns:
            Dictionary of credentials indexed by username
        """
        if not os.path.exists(self.credentials_file):
            return {}
        
        try:
            with open(self.credentials_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode('utf-8'))
        except Exception as e:
            print(f"Error loading credentials: {e}")
            return {}
    
    def _save_credentials(self):
        """
        Save credentials to encrypted storage. Raises on failure (fail closed).
        """
        data = json.dumps(self.credentials).encode('utf-8')
        encrypted_data = self.fernet.encrypt(data)
        with open(self.credentials_file, 'wb') as f:
            f.write(encrypted_data)
    
    def add_credential(
        self,
        username: str,
        password: str,
        admin_password: Optional[str] = None,
        become_password: Optional[str] = None,
        label: Optional[str] = None,
        force: bool = False,
        snmp_version: Optional[str] = None,
        snmp_community: Optional[str] = None,
        snmp_port: Optional[int] = None,
        snmp_v3_user: Optional[str] = None,
        snmp_v3_auth_protocol: Optional[str] = None,
        snmp_v3_auth_key: Optional[str] = None,
        snmp_v3_priv_protocol: Optional[str] = None,
        snmp_v3_priv_key: Optional[str] = None,
        profile_type: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Add a new credential set
        
        Args:
            username: Username for the credential
            password: Password for the credential
            admin_password: Optional admin/enable password
            become_password: Optional become password
            label: Optional label for the credential
            force: Force overwrite if username exists
            
        Returns:
            Tuple of (success, message)
        """
        if username is None or not isinstance(username, str):
            return False, "Username cannot be empty"
        username = username.strip()
        if not username:
            return False, "Username cannot be empty"
        if len(username) > 128 or any(c in username for c in '/\\:\x00') or '..' in username:
            return False, "Invalid username"

        from utils.credential_profiles import normalize_profile_type, validate_profile_fields
        ptype = normalize_profile_type(profile_type)
        ok, msg = validate_profile_fields(
            ptype, password, snmp_version, snmp_community, snmp_v3_user,
        )
        if not ok:
            return False, msg
        if ptype == 'snmp_only' and not (password or '').strip():
            password = '-'
        
        if not password:
            return False, "Password cannot be empty"
        
        # Check for existing credential
        if username in self.credentials and not force:
            return False, f"Credential for '{username}' already exists. Use force=True to overwrite."
        
        # Store credential
        credential = {
            'username': username,
            'password': password,
            'admin_password': admin_password,
            'become_password': become_password,
            'label': label or username,
            'profile_type': ptype,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
        }
        if snmp_version:
            credential['snmp_version'] = snmp_version
        if snmp_community:
            credential['snmp_community'] = snmp_community
        if snmp_port is not None:
            credential['snmp_port'] = int(snmp_port)
        if snmp_v3_user:
            credential['snmp_v3_user'] = snmp_v3_user
        if snmp_v3_auth_protocol:
            credential['snmp_v3_auth_protocol'] = snmp_v3_auth_protocol
        if snmp_v3_auth_key:
            credential['snmp_v3_auth_key'] = snmp_v3_auth_key
        if snmp_v3_priv_protocol:
            credential['snmp_v3_priv_protocol'] = snmp_v3_priv_protocol
        if snmp_v3_priv_key:
            credential['snmp_v3_priv_key'] = snmp_v3_priv_key
        
        self.credentials[username] = credential
        try:
            self._save_credentials()
        except Exception as e:
            self.credentials.pop(username, None)
            return False, f"Failed to persist credential: {e}"
        
        return True, f"Credential for '{username}' added successfully"
    
    def get_credential(self, username: str) -> Optional[dict]:
        """
        Retrieve a credential by username
        
        Args:
            username: Username to retrieve
            
        Returns:
            Credential dictionary or None if not found
        """
        return self.credentials.get(username)

    def record_use(self, username: str) -> bool:
        """Stamp last_used_at. Username is the vault credential_id."""
        cred = self.credentials.get(username)
        if not cred:
            return False
        cred['last_used_at'] = datetime.now().isoformat()
        self._save_credentials()
        return True
    
    def list_credentials(self) -> List[dict]:
        """
        List all credentials (without passwords)
        
        Returns:
            List of credential summaries
        """
        summaries = []
        for username, cred in self.credentials.items():
            summary = {
                'credential_id': username,
                'username': username,
                'label': cred.get('label', username),
                'has_admin': bool(cred.get('admin_password')),
                'has_become': bool(cred.get('become_password')),
                'has_snmp': _credential_has_snmp(cred),
                'snmp_version': cred.get('snmp_version') or 'none',
                'profile_type': cred.get('profile_type') or 'ssh_and_snmp',
                'has_ssh': bool(cred.get('profile_type') != 'snmp_only' and cred.get('password') and cred.get('password') != '-'),
                'created_at': cred.get('created_at'),
                'updated_at': cred.get('updated_at'),
                'last_used_at': cred.get('last_used_at'),
            }
            summaries.append(summary)
        return summaries
    
    def remove_credential(self, username: str) -> Tuple[bool, str]:
        """
        Remove a credential
        
        Args:
            username: Username to remove
            
        Returns:
            Tuple of (success, message)
        """
        if username not in self.credentials:
            return False, f"Credential for '{username}' not found"
        
        del self.credentials[username]
        self._save_credentials()
        
        return True, f"Credential for '{username}' removed successfully"
    
    def update_credential(
        self,
        username: str,
        password: Optional[str] = None,
        admin_password: Optional[str] = None,
        become_password: Optional[str] = None,
        label: Optional[str] = None,
        snmp_version: Optional[str] = None,
        snmp_community: Optional[str] = None,
        snmp_port: Optional[int] = None,
        snmp_v3_user: Optional[str] = None,
        snmp_v3_auth_protocol: Optional[str] = None,
        snmp_v3_auth_key: Optional[str] = None,
        snmp_v3_priv_protocol: Optional[str] = None,
        snmp_v3_priv_key: Optional[str] = None,
        clear_snmp: bool = False,
        profile_type: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Update an existing credential
        
        Args:
            username: Username to update
            password: New password (optional)
            admin_password: New admin password (optional)
            become_password: New become password (optional)
            label: New label (optional)
            
        Returns:
            Tuple of (success, message)
        """
        if username not in self.credentials:
            return False, f"Credential for '{username}' not found"
        
        cred = self.credentials[username]
        
        if password:
            cred['password'] = password
        if admin_password is not None:
            cred['admin_password'] = admin_password
        if become_password is not None:
            cred['become_password'] = become_password
        if label:
            cred['label'] = label
        if clear_snmp:
            for key in (
                'snmp_version', 'snmp_community', 'snmp_port', 'snmp_v3_user',
                'snmp_v3_auth_protocol', 'snmp_v3_auth_key', 'snmp_v3_priv_protocol',
                'snmp_v3_priv_key',
            ):
                cred.pop(key, None)
        if snmp_version is not None:
            cred['snmp_version'] = snmp_version or 'none'
        if snmp_community:
            cred['snmp_community'] = snmp_community
        if snmp_port is not None:
            cred['snmp_port'] = int(snmp_port)
        if snmp_v3_user is not None:
            cred['snmp_v3_user'] = snmp_v3_user
        if snmp_v3_auth_protocol is not None:
            cred['snmp_v3_auth_protocol'] = snmp_v3_auth_protocol
        if snmp_v3_auth_key:
            cred['snmp_v3_auth_key'] = snmp_v3_auth_key
        if snmp_v3_priv_protocol is not None:
            cred['snmp_v3_priv_protocol'] = snmp_v3_priv_protocol
        if snmp_v3_priv_key:
            cred['snmp_v3_priv_key'] = snmp_v3_priv_key
        if profile_type is not None:
            cred['profile_type'] = profile_type or 'ssh_and_snmp'
        
        cred['updated_at'] = datetime.now().isoformat()
        
        try:
            self._save_credentials()
        except Exception as e:
            return False, f"Failed to persist credential update: {e}"
        
        return True, f"Credential for '{username}' updated successfully"
    
    def export_credentials(self, export_path: str, password: str) -> Tuple[bool, str]:
        """
        Export credentials to an encrypted file for backup/migration
        
        Args:
            export_path: Path to export file
            password: Password to encrypt the export
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Derive key from password using Argon2id
            salt = os.urandom(16)
            kdf = Argon2id(
                salt=salt,
                length=32,
                iterations=3,
                lanes=4,
                memory_cost=2**16
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            export_fernet = Fernet(key)
            
            # Prepare export data
            export_data = {
                'version': '1.0',
                'exported_at': datetime.now().isoformat(),
                'credentials': self.credentials
            }
            
            # Encrypt and save
            data = json.dumps(export_data).encode('utf-8')
            encrypted_data = export_fernet.encrypt(data)
            
            # Prepend salt to encrypted data (16 bytes salt + encrypted data)
            final_data = salt + encrypted_data
            
            with open(export_path, 'wb') as f:
                f.write(final_data)
            
            return True, f"Credentials exported successfully to {export_path}"
            
        except Exception as e:
            return False, f"Error exporting credentials: {e}"
    
    def import_credentials(self, import_path: str, password: str, merge: bool = False) -> Tuple[bool, str]:
        """
        Import credentials from an encrypted file
        
        Args:
            import_path: Path to import file
            password: Password to decrypt the import
            merge: If True, merge with existing credentials; if False, replace
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Read encrypted file
            with open(import_path, 'rb') as f:
                file_data = f.read()
            
            # Extract salt from first 16 bytes
            if len(file_data) < 16:
                return False, "Invalid credential file: too short"
            
            salt = file_data[:16]
            encrypted_data = file_data[16:]
            
            # Derive key from password using the extracted salt
            kdf = Argon2id(
                salt=salt,
                length=32,
                iterations=3,
                lanes=4,
                memory_cost=2**16
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            import_fernet = Fernet(key)
            
            # Decrypt the data
            decrypted_data = import_fernet.decrypt(encrypted_data)
            import_data = json.loads(decrypted_data.decode('utf-8'))
            
            if 'credentials' not in import_data:
                return False, "Invalid credential file format"
            
            imported_creds = import_data['credentials']
            
            if merge:
                # Merge with existing credentials
                for username, cred in imported_creds.items():
                    if username not in self.credentials:
                        self.credentials[username] = cred
                    else:
                        # Keep existing, don't overwrite
                        pass
            else:
                # Replace all credentials
                self.credentials = imported_creds
            
            self._save_credentials()
            
            return True, f"Credentials imported successfully from {import_path}"
            
        except Exception as e:
            return False, f"Error importing credentials: {e}"
    
    def clear_all_credentials(self) -> Tuple[bool, str]:
        """
        Clear all credentials
        
        Returns:
            Tuple of (success, message)
        """
        self.credentials = {}
        self._save_credentials()
        return True, "All credentials cleared"
    
    def get_credential_count(self) -> int:
        """
        Get the number of stored credentials
        
        Returns:
            Number of credentials
        """
        return len(self.credentials)

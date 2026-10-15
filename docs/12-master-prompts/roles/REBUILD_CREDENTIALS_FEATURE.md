# REBUILD_CREDENTIALS_FEATURE

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Status** | active |
| **Registry ID** | W-REBUILD-CRED |
| **Trigger** | `rebuild credentials feature` · paste this file into another AI IDE |
| **Owner** | R-ENG + R-ARCH |
| **Source application** | Network Swiss Tool Pro **v7.0.31** |
| **last_updated** | 2026-06-10 |

**Invoke:** Paste this entire file into a blank AI IDE project to recreate the **Credential Management** feature 1:1 and integrate it into a Flask web app (or adapt layers as noted).

**Canonical source files in reference repo:**

| Layer | Path |
|-------|------|
| Core module | `modules/credential_manager.py` |
| REST API | `vlan_checker_web.py` (lines ~161–168 boot, ~1988–2321 routes) |
| UI + JS | `modules/web/templates/index.html` (sidebar ~879–895, tab ~1927–2030, JS ~4732–5168) |

---

## Mission

Build a **secure, offline-capable credential vault** for network automation tools:

- Store multiple credential sets (username-keyed) with optional admin/enable and become passwords
- Encrypt at rest with **Fernet** (local auto-key OR master-password-derived key via **Argon2id**)
- Export/import encrypted `.enc` bundles for migration between machines/versions
- Web UI tab + sidebar integration: **Use** fills active session fields for all SSH operations
- REST API consumed by vanilla `fetch()` — no framework beyond Flask

---

## Architecture (do not simplify)

```
┌─────────────────────────────────────────────────────────────┐
│  Browser                                                     │
│  Sidebar: #username, #password, #enable_password            │
│  Tab "Credentials": list / add / edit / export / import     │
│  useCredential() → GET /api/credentials/get/<user>          │
│                    → fills sidebar fields                    │
└──────────────────────────┬──────────────────────────────────┘
                           │ JSON / multipart
┌──────────────────────────▼──────────────────────────────────┐
│  Flask app (e.g. vlan_checker_web.py)                        │
│  credential_manager = CredentialManager()  # global singleton  │
│  /api/credentials/* routes                                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  CredentialManager (modules/credential_manager.py)             │
│  Fernet encrypt → .credentials.enc                           │
│  Optional master password → Argon2id key derivation          │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  On-disk files (cwd / storage_dir)                           │
│  .credentials.enc, .credential_key OR .credentials_salt +    │
│  .credentials_master_hash, .credentials_meta.json (unused    │
│  in logic but reserved)                                      │
└─────────────────────────────────────────────────────────────┘

Operations (VLAN, MAC, topology, plugins) read sidebar fields at
runtime — they do NOT call CredentialManager directly.
```

---

## Phase 1 — Core module (`CredentialManager`)

### Dependencies

```text
cryptography>=41.0.0   # Fernet, Argon2id (cryptography.hazmat.primitives.kdf.argon2)
```

### Class: `CredentialManager`

**Constructor**

```python
CredentialManager(storage_dir: str = None, master_password: str = None)
```

- `storage_dir` defaults to `os.getcwd()`
- File paths (all under `storage_dir`):
  - `.credentials.enc` — Fernet-encrypted JSON blob of all credentials
  - `.credential_key` — auto-generated Fernet key (when no master password)
  - `.credentials_salt` — 16-byte salt for Argon2id master-password KDF
  - `.credentials_master_hash` — SHA-256 hex of master password (verification only)
  - `.credentials_meta.json` — reserved (not read/written in v7.0.31 logic)

**Init behavior**

1. If `master_password` passed → derive key, init Fernet, save hash, load creds
2. Else if `.credentials_master_hash` exists → `fernet = None`, `credentials = {}` (locked until unlock)
3. Else → load/generate `.credential_key`, init Fernet, load creds

### Credential record schema (in-memory / JSON)

Dictionary keyed by **username** (unique index):

```json
{
  "admin": {
    "username": "admin",
    "password": "secret123",
    "admin_password": "enableSecret",
    "become_password": "junosRootOptional",
    "label": "Production NX-OS",
    "created_at": "2026-06-10T12:00:00.000000",
    "updated_at": "2026-06-10T12:00:00.000000"
  }
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `username` | yes | Primary key; stripped whitespace |
| `password` | yes | Device login password |
| `admin_password` | no | Maps to Cisco **enable secret** in UI |
| `become_password` | no | Juniper/sudo-style; stored but sidebar only maps `admin_password` → `#enable_password` today |
| `label` | no | Display name; defaults to username |
| `created_at` / `updated_at` | auto | ISO 8601 |

### Encryption details

**At-rest (local vault)**

- `json.dumps(credentials)` → UTF-8 → `Fernet.encrypt()` → write `.credentials.enc`

**Master password key derivation**

```python
Argon2id(salt=salt, length=32, iterations=3, lanes=4, memory_cost=2**16)
key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
fernet = Fernet(key)
```

- Salt persisted in `.credentials_salt` (create once with `os.urandom(16)`)
- Master password verified via SHA-256 hash in `.credentials_master_hash` (not used as encryption key directly)

**Export file format (`.enc`)**

```
[16 bytes salt][Fernet ciphertext of JSON]
```

JSON inside ciphertext:

```json
{
  "version": "1.0",
  "exported_at": "2026-06-10T...",
  "credentials": { ... same schema ... }
}
```

Export uses a **fresh random salt** per file (not the master-password salt). Import reads first 16 bytes as salt, derives key from user-supplied export password, decrypts remainder.

### Public methods (implement exactly)

| Method | Returns | Behavior |
|--------|---------|----------|
| `add_credential(username, password, admin_password=None, become_password=None, label=None, force=False)` | `(bool, str)` | Reject empty user/pass; duplicate username unless `force=True` |
| `get_credential(username)` | `dict \| None` | Full record including passwords |
| `list_credentials()` | `list[dict]` | Summaries only: `username`, `label`, `has_admin`, `has_become`, `created_at`, `updated_at` |
| `remove_credential(username)` | `(bool, str)` | |
| `update_credential(username, password=None, admin_password=None, become_password=None, label=None)` | `(bool, str)` | Only set fields that are passed; always bump `updated_at` |
| `export_credentials(export_path, password)` | `(bool, str)` | Salt-prefixed `.enc` file |
| `import_credentials(import_path, password, merge=False)` | `(bool, str)` | `merge=True` skips existing usernames |
| `clear_all_credentials()` | `(bool, str)` | Empty dict + save |
| `get_credential_count()` | `int` | |
| `is_master_password_required()` | `bool` | `master_hash exists AND fernet is None` |
| `verify_master_password(password)` | `bool` | Compare SHA-256 |
| `set_master_password(password)` | — | Re-encrypt all creds with new KDF key; delete `.credential_key` |
| `unlock_with_master_password(password)` | `bool` | Verify hash → derive key → load creds |

### Error handling

- Load/save failures: log/print, return `{}` or no-op save
- API layer returns HTTP 500 if `credential_manager is None` (import failed at boot)

---

## Phase 2 — Flask integration

### Boot (global singleton)

```python
try:
    from modules.credential_manager import CredentialManager
    credential_manager = CredentialManager()
    startup_log("Credential manager initialized successfully")
except Exception as e:
    credential_manager = None
    startup_log(f"WARNING: Credential manager initialization failed: {e}")
```

Place after app creation, before routes. Never crash the app if cryptography missing — degrade gracefully.

### REST API contract

All routes prefix: `/api/credentials/`

| Method | Path | Body / params | Success response |
|--------|------|---------------|------------------|
| GET | `/list` | — | `{"credentials": [...], "count": N}` |
| POST | `/add` | JSON: `username`, `password`, `admin_password?`, `become_password?`, `label?`, `force?` | `{"success": true, "message": "..."}` |
| GET | `/get/<username>` | — | `{"credential": {...}}` or 404 |
| POST | `/update` | JSON: `username` + optional fields | `{"success": true, "message": "..."}` |
| DELETE | `/remove/<username>` | — | `{"success": true, "message": "..."}` |
| POST | `/clear` | — | `{"success": true, "message": "..."}` |
| POST | `/export-file` | JSON: `password` | **File download** (`send_file`, `application/octet-stream`, name `credentials_export_YYYYMMDD_HHMMSS.enc`) |
| POST | `/import-file` | **multipart**: `file`, `password`, `merge` (`true`/`false`) | `{"success": true, "message": "..."}` |
| POST | `/export` | JSON: `export_path`, `password` | JSON success + path (legacy path-based export) |
| POST | `/import` | JSON: `import_path`, `password`, `merge?` | JSON success |
| GET | `/master-password/status` | — | `{"is_required": bool, "is_set": bool}` |
| POST | `/master-password/set` | JSON: `password` | `{"success": true, "message": "..."}` |
| POST | `/master-password/unlock` | JSON: `password` | `{"success": true}` or 400 incorrect |

**Logging:** On mutating operations call `add_log(f"[Credential Manager] ...")` if your app has a session log.

**Export-file implementation notes:**

- Write temp file → `send_file` → delete temp in `finally`
- UI uses `/export-file` (blob download), not `/export`

---

## Phase 3 — Web UI

### A. Sidebar (always visible)

HTML IDs **must match** (operations read these):

| ID | Type | Purpose |
|----|------|---------|
| `username` | text | SSH username |
| `password` | password | SSH password |
| `enable_password` | password | Cisco enable / privileged secret |
| `credential-label-display` | div | Hidden until credential loaded |
| `credential-label-text` | span | Shows `📋 Using: {label} ({username})` |
| Clear button | — | `clearCredentialLabel()` hides display |

### B. Tab navigation

- Segment button: `onclick="switchTab('credentials', this)"` label **🔐 Credentials**
- Panel: `id="tab-credentials"` class `content-card tab-view` initially `display: none`
- Optional: call `loadCredentials()` when tab opens (reference app loads on `DOMContentLoaded` only)

### C. Credentials tab sections

1. **Header** — Refresh + Add Credential buttons
2. **Stats cards** — `#credential-count`, `#admin-count`, `#become-count`
3. **Table** — `#credential-list-body` columns: Username, Label, Admin ✓, Become ✓, Created, Actions
4. **Export** — `#export-password` + `exportCredentialsFile()`
5. **Import** — `#import-file` (accept `.enc`), `#import-password`, `#import-merge` checkbox, `importCredentialsFile()`
6. **Master password** — `#master-password-status`, `#master-password-input`, `#master-password-btn`, `handleMasterPassword()`
7. **Danger zone** — `clearAllCredentials()`

### D. JavaScript functions (implement all)

| Function | Purpose |
|----------|---------|
| `loadCredentials()` | Check master status → unlock prompt if needed → GET `/list` → render table + stats → `checkMasterPasswordStatus()` |
| `showAddCredentialModal()` | Sequential `prompt()` for user/pass/admin/become/label → `addCredential()` |
| `addCredential(username, password, adminPassword, becomePassword, label, force=false)` | POST `/add`; on duplicate offer overwrite with `force: true` in JSON body |
| `removeCredential(username)` | DELETE `/remove/<username>` |
| `editCredential(username)` | GET `/get/<username>` → prompts → POST `/update` only changed fields |
| `useCredential(username)` | GET `/get/<username>` → fill `#username`, `#password`, `#enable_password` from `admin_password` → show label banner |
| `clearCredentialLabel()` | Hide `#credential-label-display` |
| `checkMasterPasswordStatus()` | GET `/master-password/status` → update status text + button label (Set / Change / Unlock) |
| `handleMasterPassword()` | Unlock OR set/change master password |
| `exportCredentialsFile()` | POST `/export-file` → blob → `<a download>` |
| `importCredentialsFile()` | FormData POST `/import-file` |
| `clearAllCredentials()` | POST `/clear` |

**Startup:** `document.addEventListener('DOMContentLoaded', () => { loadCredentials(); });`

### E. `useCredential` → operations bridge

All network jobs (e.g. `/api/execute`, discovery, STP) read:

```javascript
username: document.getElementById('username').value,
password: document.getElementById('password').value,
enable_pwd: document.getElementById('enable_password').value,
```

Server maps to plugin dict:

```python
credentials = {"username": username, "password": password, "secret": enable_pwd}
```

`become_password` maps to sidebar `#become_password` (Junos root) when user clicks **Use** (v7.0.32+).

---

## Phase 4 — Integration with network operations

CredentialManager is **not** imported by plugins. Integration is:

1. User clicks **Use** on stored credential
2. Sidebar fields populated
3. User runs any feature (VLAN, MAC trace, topology, discovery, interface manager, etc.)
4. Feature sends sidebar values in API payload
5. Backend passes `credentials` dict to `connect_permissive` / Netmiko

**Validation pattern in UI** (copy to each action):

```javascript
if (!user || !pwd) {
    alert('Please enter credentials in the sidebar.');
    return;
}
```

---

## Phase 5 — Security requirements

| Rule | Implementation |
|------|----------------|
| Never log passwords | API logs username only |
| List endpoint omits secrets | `list_credentials()` strips passwords |
| GET single credential returns secrets | Only after unlock; used for Use/Edit |
| Master password lock | On restart, if hash exists, fernet=None until unlock |
| Export password ≠ master password | Separate user-chosen export passphrase |
| Offline / EXE | Files live beside executable (`os.getcwd()`); bundle `cryptography` in PyInstaller `hiddenimports` |
| No cloud | All storage local |

**PyInstaller hiddenimports (minimum):**

```python
'modules.credential_manager',
'cryptography', 'cryptography.fernet',
'cryptography.hazmat.primitives.kdf.argon2',
```

---

## Phase 6 — Tests (minimum)

Create `tests/test_credential_manager.py`:

1. Add credential → list shows `has_admin` → get returns password
2. Duplicate add without force → fails; with force → overwrites
3. Export → import merge / replace round-trip
4. set_master_password → restart manager without password → `is_master_password_required()` True → unlock loads creds
5. remove + clear_all

Optional: Flask test client for `/api/credentials/list` and `/add`.

---

## Phase 7 — Acceptance checklist

- [ ] `.credentials.enc` created after first add
- [ ] Credentials tab lists entries without showing passwords in table
- [ ] **Use** fills sidebar; VLAN/MAC/SSH operation succeeds with filled creds
- [ ] Export downloads `.enc`; import on second machine restores sets
- [ ] Master password: set → restart app → unlock prompt → list works
- [ ] Clear all removes entries
- [ ] App starts if `cryptography` import fails (manager None, API 500 with message)

---

## Known reference quirks (v7.0.32 status)

1. **Overwrite on duplicate** — fixed: `addCredential(..., force=false)` passes `force` in JSON body.
2. **`become_password`** — fixed: `#become_password` sidebar field + `useCredential()` mapping.
3. **Tab refresh** — fixed: `switchTab('credentials')` calls `loadCredentials()`.
4. **Tests** — `tests/test_credential_manager.py` (8 cases) ships with v7.0.32.

---

## Copy-paste mega-command (for blank AI IDE project)

```text
Implement the Credential Management feature exactly as specified in
REBUILD_CREDENTIALS_FEATURE.md:

1. Create modules/credential_manager.py — full CredentialManager class
   (Fernet + Argon2id master password + export/import salt-prefixed .enc)
2. Wire Flask routes /api/credentials/* per API table
3. Add sidebar credential fields + Credentials tab UI + all JS functions
4. Global CredentialManager() at app boot with graceful fallback
5. useCredential() fills sidebar; all SSH features read sidebar fields
6. Add tests/test_credential_manager.py per Phase 6
7. Verify acceptance checklist Phase 7

Match field names, file names, endpoint paths, and encryption parameters
exactly. Do not substitute with a generic secrets manager or external vault.
```

---

## Related docs

- `docs/07-security/credential-management.md` — stub pointer
- `docs/08-operations/exe-smoke-checklist.md` — field validation
- Source: `modules/credential_manager.py` (505 lines, v7.0.18+)

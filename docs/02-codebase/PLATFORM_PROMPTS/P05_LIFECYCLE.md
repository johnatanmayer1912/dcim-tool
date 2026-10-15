# 🧩 Puzzle Piece 5: The Gatekeeper & Rollback Manager

> **[OBJECTIVE]**
> Build the "Safety System" that ensures no broken or malicious code can crash the platform. This includes a sandbox uploader, a pre-flight validator, and an emergency rollback mechanism.

---

## 🛠️ Task 1: The "Sandbox" Uploader
Implement an upload endpoint in `vlan_checker_web.py` that handles `.py` files.

### The Pipeline:
1.  **Stage**: Save the file to `scratch/uploads/`.
2.  **Validate**: Run a "Pre-Flight" check:
    - **Syntax Check**: `compile(code, filename, 'exec')` to catch syntax errors without running.
    - **Contract Check**: Verify `METADATA` exists and `run()` function has the correct signature.
    - **Security Check**: Check for banned imports (`os.system`, `shutil.rmtree`, etc.).
3.  **Promote**: Only if valid, move the file to `modules/plugins/`.

---

## 🛠️ Task 2: The Rollback Engine
In the `PluginRegistry`, implement a "Version Vault".

### Logic:
1.  **Pre-Update Backup**: Before overwriting `my_tool.py`, move the existing version to `backups/plugins/my_tool/YYYYMMDD_HHMMSS_vX.py`.
2.  **History API**: Provide an endpoint `/api/plugins/history/<id>` that returns the list of backups.
3.  **One-Click Restore**: Provide a `/api/plugins/rollback` endpoint that swaps the current production file with a selected backup.

---

## 🛠️ Task 3: UI Feedback
Update the "Plugin Manager" UI to show the "Health" of each plugin.
- **Green**: Living in `modules/plugins` and valid.
- **Red**: Failed validation (show error message in UI).
- **History Link**: Open a dropdown showing the rollback options.

---

## ✅ QA Validation for the Agent
1.  **Broken Upload Test**: Upload a file with a `SyntaxError`. Verify that the system rejects it and the "Plugin Tools" tab remains stable.
2.  **Clean Overwrite Test**: Upload `v2.0` of a plugin. Verify that `v1.0` is safely stored in the `backups/` directory.
3.  **Rollback Verifier**: Trigger a rollback. Verify the "Hot Reload" logic instantly returns the UI to the previous version's metadata.

---

**Final Action**: Once all pieces are complete, perform a system-wide "Architecture Verification" according to [00_INDEX.md](./00_INDEX.md).

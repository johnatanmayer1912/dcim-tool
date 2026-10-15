# Credential Management

> **Implementation:** `modules/credential_manager.py` · [authentication.md](authentication.md)

Fernet-encrypted credential sets for offline EXE deployments.

## CLI terminal (Socket.IO) — credential_id only

Interactive CLI (`/cli_terminal`) **requires a vault `credential_id`**. Plaintext username/password over Socket.IO is **not supported**. The former `NST_CLI_PLAINTEXT_COMPAT` opt-in has been **removed**.

### Operator workflow

1. Create or verify a vault credential in the main console (Settings → Credentials).
2. Unlock the vault with the master password if the vault is locked.
3. Open **CLI Terminal** and select the stored credential (metadata-only list; passwords stay on the server).
4. Connect — the client sends `credential_id` only; the server resolves secrets immediately before SSH.
5. Do **not** type or transmit a device password through Socket.IO.

If connect fails with `credential_id_required` or “Credential is unavailable”, fix the vault selection (missing, deleted, locked, or mismatched username) rather than pasting a password into the CLI page.

# Job index (Evidence catalog)

Metadata catalog for execute jobs. **Artifacts stay in run folders.** This file is not a CMDB and not a log of CLI output.

## Location

`{get_data_root()}/index/jobs.sqlite`

Same `utils/output_paths.get_data_root()` as reports (override with `NST_DATA_DIR`). Works in the frozen EXE as long as the data root is writable.

## Schema (version 1)

Table `jobs`:

| Column | Meaning |
|---|---|
| `task_id` | Control-plane id (PK) |
| `created_at` / `updated_at` | ISO timestamps |
| `completed_at` | Set when status is terminal |
| `action` | `/api/execute` action name |
| `status` | See below |
| `inventory_source` | Target source label: `committed` / `unsaved` / `legacy_body` / `discovery_seeds` / `committed_inventory` / `unsaved_inventory` / `single_host` / `cidr_scan` / `demo` / `explicit_host_list` — **never** inventory text or passwords |
| `device_count` | Filtered host count (CIDR host count for ping scan) |
| `run_dir` | Path relative to data root, must be under `outputs/` |
| `error_summary` | Sanitized, truncated; secrets redacted |
| `partial` | `1` when status is `partial` |

## Status

| Status | Meaning |
|---|---|
| `running` | Registered, not finished |
| `complete` | Finished without cancel |
| `failed` | Exception (`complete_task(..., 'error')` maps here) |
| `cancelled` | Operator cancelled; no contained run folder |
| `partial` | Cancelled (or cancel-then-finish) **with** a contained `run_dir` |

Never collapsed: cancelled/failed/partial → complete.

In-memory control plane still uses `error` and `cancelling`. The index is the durable vocabulary.

## Path safety

- Only `outputs/` under the data root is stored.
- Traversal (`..`, `/etc/passwd`) is rejected.
- GET `/api/jobs` never opens files and never accepts a path parameter as a reader.

## Concurrency

Write lock + SQLite WAL + `busy_timeout`. One connection per operation.

## Failure policy

**Fail-open.** Index errors are logged as exception type only. They must not change the job result or crash the worker.

Corrupt sqlite: rotate to `jobs.sqlite.corrupt` and recreate.

## API

- `GET /api/jobs?limit=50` — newest first, limit clamped 1–200
- `GET /api/jobs/<task_id>` — one row or 404
- Each row includes `artifacts_available` (true only if `run_dir` is a contained `outputs/` directory that exists). Complete + `artifacts_available=false` means no evidence pack, not a missing UI.

Localhost + trusted origin (`before_request` and `@localhost_required`).

## Lifecycle hooks

`utils/task_control_plane.py`: `register_task` → start; `complete_task` / `request_cancel` → status.  
`prepare_run_output` attaches `run_dir` when a task is bound.

Discovery (`action=discovery`), Interface Manager (`interface_discover|validate|deploy`), Ping Scan (`ping_scan`), STP (`stp`), and Standards (`standards`) register the same way. Standards remains a **synchronous** HTTP POST: the index row is written around the blocking run. `cancel_scope=none` — do not treat a Standards task as cancellable mid-SSH.

Seed hosts and single-host targets are **not** bulk execute inventory.

In-memory eviction never drops `running` or `cancelling` tasks. `complete_task` still updates SQLite if the memory row is already gone.

See `utils/job_source.py` for Discovery/IM `target_source` semantics.

## Not stored

Passwords, Fernet keys, enable secrets, inventory bodies, CLI dumps, caller-supplied paths.

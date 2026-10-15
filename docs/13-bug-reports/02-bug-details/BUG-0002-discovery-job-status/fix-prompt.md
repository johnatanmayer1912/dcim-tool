# Fix prompt — BUG-0002 (copy into AI IDE)

In `vlan_checker_web.py`, inside `api_discovery_run` → `_run()` after `result = plugin.execute(...)`:

1. If `result.get("status") == "error"` or `result.get("error")`:
   - Set `_discovery_jobs[job_id]["status"] = "error"`
   - Set `_discovery_jobs[job_id]["error"]` from `result.get("error")` or a default message
   - Log `[Discovery] Job {job_id} failed: ...`
   - **Do not** set status to `complete`
2. Else set `complete` and store `result` as today.
3. In `modules/web/templates/index.html` `discUpdateStatus`, if `data.status === 'complete'` but `data.result?.status === 'error'`, treat as error (defensive).

Add a unit test: mock `NetworkDiscoveryPlugin.execute` returning `build_json(..., 'error', ...)` and assert job status is `error`.

Minimal diff only; no unrelated refactors.

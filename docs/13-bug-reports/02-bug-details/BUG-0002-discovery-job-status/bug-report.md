# Bug report — BUG-0002

| Field | Value |
|-------|-------|
| **ID** | BUG-0002 |
| **Title** | Discovery API marks job complete when plugin returns error |
| **Severity** | Medium |
| **Priority** | P1 |
| **Owner** | Lead Developer |
| **Status** | **closed** (v6.9.26) |
| **Found** | 2026-05-31 |
| **Closed** | 2026-05-31 |

## Description

`/api/discovery/run` background thread always sets `_discovery_jobs[job_id]["status"] = "complete"` after `plugin.execute()`, even when the plugin returns `{"status": "error", ...}` (e.g. no valid seeds). The UI polls job status only and shows a green “Complete” line while `result.status` is `error`.

## Root cause

`vlan_checker_web.py` `_run()` does not inspect `result.get("status")` before assigning job status.

## Impact

Operators believe discovery succeeded; table may be empty; topology button may 404.

## Reproduction

1. Start app v6.9.25.
2. Discovery tab → invalid/empty seed handling path, or trigger plugin error return without exception.
3. Observe job status `complete` in `/api/discovery/status/<id>` while `result.status` is `error`.

## Role findings

| Role | Finding |
|------|---------|
| QA Engineer | UI tests should assert job `status` matches plugin outcome |
| Observability Engineer | Log says “Job complete” even on logical failure |
| Product Strategist | False success undermines Discovery trust |

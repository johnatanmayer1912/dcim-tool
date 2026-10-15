# QA — Live-lab evidence failure closeout

## Scope

Closeout of failed PASS-eligible evidence collection. Attempt-only JSON retained. No product/UI changes.

## Confirm

- `evidence_paths.live_evidence_artifact` is `null`
- Probe/prereq modes are `live_ssh_prereq_skip` / `live_ssh_not_executed`
- Checker/consumer remain BLOCKED + hard_stop
- Honesty suite: `python3 -m pytest tests/test_live_lab_evidence_attempt_honesty.py -q`

## Do not report as

- Attempt-only JSON = live vendor validated
- BLOCKED softened / almost ready
- Enterprise clearance

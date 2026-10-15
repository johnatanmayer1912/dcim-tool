# Live SSH QA Warranty

Network Swiss Tool Pro **offline pytest** validates vendor command matrices, parsers, formatters, and API contracts without contacting real devices.

## Default CI / release gate

| Layer | Coverage |
|-------|----------|
| `tests/` | 280+ unit/integration tests (offline) |
| `tests/qa/test_00_implemented_mandatory.py` | Council questionnaire rows with code evidence |
| `_prebuild.py` | Syntax, plugins, CLI smoke |
| `scripts/mandatory_release_qa.py` | Manifest-driven orchestrator |

**Warranty:** Cisco IOS/XE, NX-OS, Juniper Junos, and IOS-XR **plumbing** is tested offline. Field CLI variants on specific hardware may still differ.

## Optional live SSH probe

```powershell
$env:NST_LIVE_SSH = "1"
$env:NST_LIVE_HOST = "10.0.0.1"
$env:NST_LIVE_USER = "admin"
$env:NST_LIVE_PASS = "secret"
$env:NST_LIVE_DEVICE_TYPE = "cisco_ios"   # optional
python -m pytest tests/test_live_ssh_matrix.py::TestLiveSshProbe -q
```

Use containerlab or lab switches before declaring support on new platform images.

## Not in default gate

- Live Netmiko sessions
- Full 150+ device topology soak
- Bulk Interface Manager deploy (single-host by design)

Document lab results in CHANGELOG when live matrix is exercised for a release.

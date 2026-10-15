# Honesty — live-lab vs fixture

| Claim | Status |
|---|---|
| Live SSH two-sample collection against a signed named lab | **Not executed** |
| TCP/22 open on candidate inventory IPs | **False** (timeout / refused / unreachable) |
| Operator console live execute | **Not running** (`127.0.0.1:5051` closed) |
| Fixture live overlay document + mocked collector tests | **Real rehearsal** — not retained live |
| Replay fallback | **Real** in fixture tests |
| Discovery does not start live SSH | **Real** in fixture HTML (`live_controls=false`) |
| SNMP used | **No** |
| `utils.telemetry` thawed | **No** |
| `release_gate` cleared | **No** |
| Secrets in this evidence folder | **None written** (env values not captured; credential key not read) |

Calling the 70+8 pytest passes a “live-lab Pass” would be false.

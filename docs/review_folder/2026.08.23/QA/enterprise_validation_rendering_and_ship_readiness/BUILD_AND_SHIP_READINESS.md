# Build and ship readiness

**VERSION:** 7.2.2 · **Date:** 2026-08-23  
**Platform of this pass:** Darwin (macOS)

## Prebuild

| Check | Result | Log |
|---|---|---|
| `python3 _prebuild.py` | **ALL CHECKS PASSED — READY TO BUILD** | `prebuild/prebuild.txt` |
| Mandatory manifest integrity | PASS | `qa/every_code_change.txt` |

## Packaging artifacts

| Artifact | Status |
|---|---|
| `NetworkSwissToolPro_v7.2.2.spec` | Copied to `packaging/` |
| Windows PE EXE via PyInstaller | **NOT BUILT** on Darwin (`exe/README.md`) |
| Offline ship path (documented) | Windows host: `_prebuild.py` → `pyinstaller NetworkSwissToolPro_v7.2.2.spec` |

## Security / trust model (ship constraints)

- Default bind: localhost — **deployment choice, not authn**  
- No SSO/RBAC — local operator console  
- Credential APIs / vault: localhost + unlock guards (tested in core battery)  
- Plugin upload remains high blast radius — sandbox not a security boundary  

## Program Status contract

Playwright confirms:

- `release_gate` = **BLOCKED**  
- `hard_stop` = true  
- `may_claim_enterprise_ready` = false  

## Ship-readiness result

| Claim | Allowed? |
|---|---|
| Offline localhost operator console (CI-proven behavior) | **Yes — conditional** |
| Windows offline EXE artifact from this host | **No** (build on Windows) |
| Enterprise operational ready / live vendor validated | **No** |
| Multi-user IdP enterprise infrastructure | **No** |

**Verdict:** **CONDITIONALLY READY TO BUILD** on a Windows packaging host; **NOT** ready to declare enterprise operational ship without live evidence and EXE validation.

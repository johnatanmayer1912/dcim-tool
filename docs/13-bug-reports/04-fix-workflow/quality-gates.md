# Quality gates — post-fix (G-07)

| Gate | Requirement |
|------|-------------|
| Pre-build | `python _prebuild.py` — all PASS |
| Unit tests | `python -m unittest discover -s tests -p "test_*.py"` |
| vPC validation | `python tests/validate_vpc_member_interfaces.py` |
| Web smoke | `GET /` 200, `/health` 200, `/api/version` matches VERSION |
| Jinja | No raw `{{` in JS inside `index.html` without escape |
| Discovery | Demo + live seed (or mocked) job status matches outcome |
| Docs | Version Awareness fields match VERSION after release |
| EXE | `pyinstaller NetworkSwissToolPro_vX.spec` when code changed |

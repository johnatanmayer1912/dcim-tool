# System Dependencies & Offline Installation

The Network Swiss Tool Pro is designed for air-gapped environment deployment.

## Mandatory Libraries
| Library | Minimum Version | Purpose |
|---------|-----------------|---------|
| `python` | 3.10+ | Runtime environment |
| `netmiko` | 4.1.2 | Multi-vendor SSH orchestration |
| `flask` | 2.0+ | Web Dashboard backend |
| `pyinstaller`| 5.0+ | Standalone executable bundling |

## Transitive Dependencies
- `paramiko` (Handle SSH key exchange and transport)
- `scp` (Secure copy protocol support)
- `pyserial` (Serial console support)
- `textfsm` (Template-based CLI parsing - optional/future)
- `jinja2` (HTML template rendering)
- `werkzeug` (WSGI web server for Flask)

## Offline Installation Method
1. **Prepare**: On a machine with internet access, run:
   ```bash
   pip download -r requirements.txt -d ./paramiko_deps
   ```
2. **Transfer**: Move the `paramiko_deps` folder to the target air-gapped machine.
3. **Execute**:
   ```bash
   pip install -r requirements.txt --no-index --find-links ./paramiko_deps
   ```

## Virtual Environment Policy
It is strongly recommended to use a virtual environment (`.venv`) to isolate dependencies. Avoid installing libraries globally to prevent collisions with other system automation scripts.

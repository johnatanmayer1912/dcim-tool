# System Rebuild Instructions (Clean Room Recovery)

Follow these steps to reconstruct the Network Swiss Tool Pro from scratch using the documentation provided in this blueprint.

## Phase 1: Environment Setup
1. **Python**: Install Python 3.10 or higher.
2. **Structure**: Recreate the directory hierarchy:
   ```
   /project
   ├── core/
   ├── modules/
   ├── utils/
   ├── config/
   ├── inventory/
   ├── logs/
   └── reports/
   ```
3. **Dependencies**: Install via `pip install netmiko flask pyinstaller`.

## Phase 2: Core Network Layer
1. **Base Functions**: Implement `modules/network_base.py`. Use the `build_json` contract and the `connect_permissive` logic using `Netmiko's ConnectHandler`.
2. **Adapter Layer**: Implement `modules/adapters.py`. This must contain the top-level loops that iterate over device lists and call sub-modules. It must accept a `log` callback for UI updates.

## Phase 3: Feature Implementation
1. **Modules**: Rebuild each script in `modules/` (e.g., `vlan_audit.py`) using the CLI commands documented in `cli_commands.md` and the regex patterns in `parsing_logic.md`.
2. **Report Formatter**: Implement `utils/report_formatter.py` to handle CSV (`csv.DictWriter`) and Text file output.

## Phase 4: User Interface
1. **GUI**: Use `tkinter`. Implement a `VlanCheckerApp` class. Spawning network tasks in `threading.Thread` is critical to prevent UI freezing. Use a `queue.Queue` to share logs between threads.
2. **Web**: Use `Flask`. Implement a REST API (`/api/execute`) that starts worker threads. Serve a frontend (HTML/JS) that polls `/api/logs` for real-time updates.

## Phase 5: Routing & Entry Point
1. **Router**: Implement `main.py` using `argparse`. Route commands to either the Tkinter loop or the Flask server.
2. **Validation**: Add pre-boot checks to ensure `inventory.txt` is present and accessible.

## Phase 6: Prompt & Intelligence Injection
1. **Refining**: Use the prompts in `master_prompts/` with an AI assistant to verify the code against the documented architecture and fix any edge cases discovered in the original system.

## Phase 7: Validation
1. **QA**: Execute all scenarios in `QA_TESTING_CHECKLIST.txt`.
2. **Build**: Use `pyinstaller` with the provided `.spec` files (or create new ones) to bundle the app into a standalone `.exe`.

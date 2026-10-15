# Deployment Flow Document: Visual Interface Management System

## Sequential Deployment Process
1. **Trigger**: User inputs a configuration change and initiates deployment.
2. **Pre-Check**: Validation pipeline checks dry-run results, syntax errors, and platform conflicts.
3. **Approval Prompt**: Confirms execution with a safety verification modal:
   - Visual configuration diff (colored line removals/additions).
   - Impact summary (detection of interface shutdowns, VLAN pruning).
   - Double-check consent forms.
4. **Pre-Change Backup**: The plugin connects to the device, retrieves the running configuration, and saves it into `backups/{hostname}/config_timestamp.txt`.
5. **Execution**: Safe deployment of config sets line-by-line via Netmiko configuration sessions.
6. **Post-Change Verification**: Executes verification commands (e.g. `show run interface {name}`) and validates config state consistency.

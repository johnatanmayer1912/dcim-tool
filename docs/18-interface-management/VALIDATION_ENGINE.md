# Validation Engine Document: Visual Interface Management System

## Validation Pipeline Checks
- **Step 1: Dry-Run Check**: Runs mock command execution to trace parsing logic errors.
- **Step 2: Vendor Syntax Check**: Matches configuration commands against vendor regex libraries:
  - Cisco NX-OS: Checks for unsupported legacy commands (e.g. `switchport trunk encapsulation dot1q`).
  - Cisco IOS & IOS-XE: Checks VLAN ID bounds (1-4094), valid IP formats, and trunk configuration structure.
  - Juniper JUNOS: Checks hierarchy configuration layout rules.
- **Step 3: Platform Check**: Connects to the device, retrieves firmware version, and verifies command availability.
- **Step 4: Conflict Check**: Compares proposed state with running configurations:
  - Warns on VLAN removals.
  - Warns on port mode changes (access to trunk or vice versa).
- **Step 5: User Approval**: Prompt modal checking double-consent boxes.

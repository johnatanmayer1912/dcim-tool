# Build Guide for Network Swiss Tool Pro

## Creating New Builds

### Step 1: Update Version
1. Update `VERSION` file with new version number (e.g., 7.0.28)
2. Update `README.md` version history with new version details
3. Update plugin metadata in relevant plugin files

### Step 2: Create Spec File from Template
**CRITICAL**: Always use the template spec file to ensure all dependencies are included for offline compatibility.

1. Copy `NetworkSwissToolPro_TEMPLATE.spec` to `NetworkSwissToolPro_vX.X.X.spec`
2. Update the name in the spec file:
   - Line 3: Update description with new version
   - Line 136: Update `name='NetworkSwissToolPro_vX.X.X_OFFLINE'` with new version
3. If you added new plugins, add them to the hiddenimports list under "# All plugins - explicit list"

### Step 3: Build EXE
```bash
pyinstaller NetworkSwissToolPro_vX.X.X.spec
```

### Step 4: Verify Build
1. Check that the EXE file size is similar to previous builds (should be 80-100MB range)
2. Test the EXE in offline mode to ensure all dependencies are included
3. Verify all plugins load correctly
4. Test demo mode functionality

## Dependency Management

### Why Dependencies Are Hardcoded
The spec file uses hardcoded dependencies to ensure offline compatibility. This prevents:
- Missing dependencies in the EXE
- Runtime errors when running without internet
- Inconsistent builds between versions

### Adding New Dependencies
If you add a new library to the project:
1. Add it to the hiddenimports list in the spec file
2. Add specific submodules if needed (e.g., `library.submodule`)
3. If the library has data files, add them to the datas list
4. If the library has binary files, use `collect_all('library')` and add to binaries

### Template Structure
The spec file is organized into sections:
- **Core utilities**: Internal utility modules
- **Core modules**: Main application modules
- **All plugins**: All plugin modules (add new plugins here)
- **Network libraries**: SSH and network communication
- **Security libraries**: Encryption and security
- **Template libraries**: Parsing and templating
- **Web libraries**: Flask and web framework
- **Network utilities**: IP and network utilities

## Common Issues

### EXE Size Too Small
If the EXE is significantly smaller than expected (less than 80MB):
- Check that you used the template spec file
- Verify all collect_all() calls are present
- Ensure datas list includes all directories

### Missing Dependencies at Runtime
If you get import errors:
- Add the missing module to hiddenimports
- Rebuild the EXE
- Test again

### Plugin Not Loading
If a plugin doesn't load:
- Check that the plugin is in the hiddenimports list
- Verify the plugin file is in the datas list under modules/plugins
- Check plugin metadata for errors

## Version History Reference

### v7.0.38 (2026-06-18)
- VLAN management UI enhancement: Added confirmation modal with "are you sure?" mechanism
- Added save configuration checkbox to VLAN operations (add/rename/delete)
- Confirmation modal mirrors interface manager behavior with validation checkboxes
- User must confirm backup creation and live configuration modification before execution
- Save configuration option allows user to choose whether to persist changes to startup-config
- Enhanced logging to show save configuration status in UI

### v7.0.37 (2026-06-18)
- VLAN management enhancement: Added automatic configuration save after VLAN add/delete/rename operations
- Save logic mimics interface management behavior with platform-specific commands (write memory, copy running-config startup-config, commit)
- Added save_config parameter to VLAN operations (default: True) for optional save control
- Enhanced logging to reflect save operation status and method used
- Maintains existing backup functionality and idempotency checks

### v7.0.31 (2026-06-10)
- Lab smoke offline tests (IOS-XE MAC, QFX5100 LLDP); enterprise QA gate; 0 broken doc links
- Topology parallel-link dedup key; offline EXE build

### v7.0.30 (2026-06-10)
- Bug sweep auto-fix: NEW-M1–M9 + hygiene

### v7.0.29 (2026-06-10)
- BUG-0009/0010 closed; pytest 146/146; NEW-C1 read-only EXE; NEW-H5 Junos LLDP; NEW-M2 serial merge

### v7.0.28 (2026-06-10)
- MAC trace: Cisco dotted-format normalization for IOS-XE L3; Juniper multi-command MAC search
- Juniper interface map: ae/LACP bundle correlation (physical xe/ge ↔ logical ae)
- New utils: `mac_utils.py`, `juniper_iface.py`

### v7.0.27 (2026-06-07)
- Critical JUNOS LLDP Discovery Fix
- Changed command order for Juniper devices to try brief first
- Added comprehensive hardcoded dependencies for offline compatibility
- Created template spec file for future builds

### v7.0.26 (2026-06-07)
- JUNOS LLDP and Interface Fixes
- xe- interface support
- 4-tier fallback chain for LLDP parsing

## Build Checklist
- [ ] Update VERSION file
- [ ] Update README.md version history
- [ ] Update plugin metadata
- [ ] Copy template spec file to new version
- [ ] Update spec file name and description
- [ ] Add new plugins to hiddenimports if needed
- [ ] Run pyinstaller with new spec file
- [ ] Verify EXE size (80-100MB range)
- [ ] Test offline functionality
- [ ] Test all plugins load correctly
- [ ] Test demo mode

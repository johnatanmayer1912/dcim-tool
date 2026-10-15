# User Error Prevention Guide

## Important Instructions for Safe Operation

### Discovery Tab
- **Demo Mode**: Use Demo Mode checkbox to test without real devices. This prevents accidental scans on production networks.
- **Seed Hosts**: Always verify seed host IPs before starting discovery. Incorrect IPs can cause unnecessary SSH attempts.
- **Crawl Depth**: Default depth of 2 is recommended for most networks. Higher depths (5+) can cause long scan times.
- **Protocol Selection**: Use "Both" for maximum compatibility. "CDP Only" or "LLDP Only" may miss neighbors.
- **Credentials**: Ensure credentials are correct before starting. Failed authentication attempts will be logged but consume time.

### Interface Manager
- **Configuration Changes**: Always use "Preview" before "Deploy" to review changes.
- **Backup**: Pre-change backup is automatic. Keep these backups for rollback.
- **Scope Selection**: Verify Single/Bulk/Group scope before deploying to prevent unintended changes.
- **VLAN Operations**: Deleting VLANs is destructive. Always verify VLAN ID before deletion.
- **Credential Storage**: Use master password protection for credential security in offline environments.

### vPC Domain Analysis
- **NX-OS Only**: This plugin only works on Cisco NX-OS devices. Running on IOS/JUNOS will return "Not applicable".
- **Verification Checks**: All 10 verification checks require specific command support. Older NX-OS versions may not support all commands.
- **Domain Correlation**: The plugin caches domain information across devices. Clear cache if switching between different vPC domains.
- **Peer Detection**: Duplicate devices are automatically merged based on domain ID, role, and peer status.

### STP Topology
- **VLAN ID**: Specify VLAN ID for STP topology. Use 0 for all VLANs (may be slow on large networks).
- **Demo Mode**: Use Demo Mode to test STP visualization without real devices.
- **Map Rendering**: STP maps require JavaScript. Ensure browser supports modern JavaScript.

### General Best Practices
- **Inventory Format**: Use correct inventory format: `IP,device_type,group`. Invalid lines will be skipped.
- **Device Types**: Supported types: `cisco_ios`, `cisco_nxos`, `cisco_xe`, `juniper_junos`. Incorrect types will cause connection failures.
- **Port Configuration**: Default SSH port is 22. Non-standard ports must be specified in inventory.
- **Timeout Settings**: Default timeout is 30 seconds. Increase for slow networks or high-latency devices.
- **Log Files**: All operations create log files. Review logs for troubleshooting failed operations.

### Offline Environment
- **Demo Mode**: All plugins support Demo Mode for offline validation without network access.
- **Credential Encryption**: Credentials are encrypted with Fernet for offline storage. Master password is required for decryption.
- **Documentation**: All documentation is included in the offline build. No internet connection required.
- **Health Check**: Run full health check to validate offline environment before deployment.

### Error Prevention Checklist
Before running any operation:
1. Verify inventory file format and device IPs
2. Test credentials on a single device first
3. Use Demo Mode to test workflow
4. Verify scope (Single/Bulk/Group) is correct
5. Review logs for any warnings
6. Keep backups of configurations before changes
7. Use Preview/Review features when available
8. Monitor operation progress in real-time
9. Review results before proceeding to next step
10. Document any issues for future reference

### Common User Errors and Prevention

**Error**: "No devices found in inventory"
- **Prevention**: Verify inventory.txt exists in correct location and has valid device lines

**Error**: "Authentication failed"
- **Prevention**: Test credentials manually via SSH before using in tool

**Error**: "Device type not supported"
- **Prevention**: Use only supported device types: cisco_ios, cisco_nxos, cisco_xe, juniper_junos

**Error**: "Command not supported on device"
- **Prevention**: Check device OS version compatibility. Some features require newer versions.

**Error**: "Timeout waiting for response"
- **Prevention**: Increase timeout setting for slow networks or high-latency devices

**Error**: "Demo mode not available"
- **Prevention**: Ensure plugin supports demo mode. Check plugin documentation.

**Error**: "Duplicate device detected"
- **Prevention**: This is normal behavior. Devices with same IP/hostname/serial are automatically merged.

**Error**: "VLAN already exists"
- **Prevention**: Check existing VLANs before creating new ones to avoid duplicates.

**Error**: "Interface not found"
- **Prevention**: Verify interface name format matches device naming convention (e.g., Ethernet1/1 vs Eth1/1).

### Limitations and Known Issues

- **CDP/LLDP**: Some devices may not advertise CDP/LLDP or may have non-standard output formats
- **Interface Parsing**: Older device OS versions may have different output formats requiring fallback parsing
- **vPC Analysis**: Only supported on NX-OS with vPC configured
- **STP Topology**: Large networks with many VLANs may be slow to render
- **Demo Mode**: Demo data is synthetic and may not match real-world complexity
- **Offline Mode**: Some features require network access for full functionality
- **Browser Compatibility**: Requires modern browser with JavaScript enabled
- **Memory Usage**: Large inventories (100+ devices) may require more memory

### Support and Troubleshooting

If you encounter issues:
1. Check the log files in the `logs/` directory
2. Run health check to validate environment
3. Review plugin documentation for specific requirements
4. Test with Demo Mode to isolate network issues
5. Check device compatibility with plugin requirements
6. Verify credentials and network connectivity
7. Review error messages in logs for specific failure reasons

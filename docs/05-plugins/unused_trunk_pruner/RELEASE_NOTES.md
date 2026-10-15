# Release Notes: unused_trunk_pruner

## Version 1.0.1 (2026-04-23)

### Improvements
- Enhanced cross-platform support for Cisco IOS, Cisco NX-OS, and Juniper JunOS
- Improved hostname detection using connection prompt for more accurate device identification
- Refined regex for trunk parsing to handle complex output formats

### Platform Support
- Cisco IOS: Full support with standard trunk configurations
- Cisco NX-OS: Full support with NX-OS trunk configurations
- Juniper JunOS: Limited support - simplified parsing, focus on Cisco Ghost VLANs

### Testing
- Cisco IOS and NX-OS compatibility tests passing
- VLAN range parsing tests passing
- Ghost VLAN detection tests passing
- Report generation tests passing

## Version 1.0.0 (2026-04-23)

### Initial Release
- First public release of unused_trunk_pruner plugin
- Ghost VLAN detection and analysis functionality
- Multi-platform support for major network operating systems
- VLAN range parsing for complex formats (e.g., "1,10-12,20")
- Human-readable report generation with pruning recommendations
- Platform-specific command selection for accurate trunk analysis

### Features
- Identifies VLANs allowed on trunk ports but missing from switch database
- Compares trunk configurations against active VLAN database
- Handles complex VLAN range formats
- Generates formatted reports saved to reports/unused_trunk_pruner/ directory
- Returns JSON with comprehensive trunk and VLAN analysis
- Provides pruning command recommendations in report

### Use Cases
- Network cleanup by identifying and removing unnecessary VLANs from trunks
- Security hardening by reducing attack surface through VLAN limitation
- Broadcast domain optimization by minimizing unnecessary broadcast traffic
- Configuration audit to verify trunk configurations match actual VLAN requirements
- Compliance verification for VLAN configuration best practices

### Safety
- Read-only operation - does not modify device configuration
- Analysis only - provides recommendations for manual implementation

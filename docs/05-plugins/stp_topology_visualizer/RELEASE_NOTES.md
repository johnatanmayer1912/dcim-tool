# Release Notes: stp_topology_visualizer

## Version 1.0.1 (2026-04-23)

### Improvements
- Enhanced cross-platform support for Cisco IOS, Cisco NX-OS, and Juniper JunOS
- Improved hostname detection using connection prompt for more accurate device identification
- Refined platform-specific command mapping for better STP command selection

### Platform Support
- Cisco IOS: Full support with PVST+, RSTP, MST modes
- Cisco NX-OS: Full support with RSTP, MST modes
- Juniper JunOS: Full support with RSTP, MSTP, VSTP modes

### Testing
- All platform compatibility tests passing
- Parsing tests for Root ID extraction and blocked port detection passing
- Report generation tests passing

## Version 1.0.0 (2026-04-23)

### Initial Release
- First public release of stp_topology_visualizer plugin
- Root Bridge detection and VLAN mapping functionality
- Blocked port analysis for loop prevention verification
- Multi-platform support for major network operating systems
- Human-readable report generation with clear status indicators
- Platform-specific command selection for accurate STP analysis

### Features
- Identifies whether a device is the Root Bridge for any VLAN
- Maps VLANs to their respective Root Bridge IDs
- Detects and reports blocked ports that prevent loops
- Supports optional vlan_id parameter (0 = all VLANs, 1-4094 = specific VLAN)
- Generates formatted reports saved to reports/stp_topology_visualizer/ directory
- Returns JSON with comprehensive STP status information

### Use Cases
- STP topology verification and Root Bridge placement analysis
- Loop detection through blocked port identification
- STP-related connectivity troubleshooting
- Network audit documentation for STP configuration

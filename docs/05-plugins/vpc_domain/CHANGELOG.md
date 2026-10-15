# Changelog: vpc_domain

All notable changes to this plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.3.1] - 2026-05-26

### Fixed
- Defensive programming fixes to prevent AttributeError and crashes
- Added None checks and type validation to all verification functions
- Added isinstance() checks before string operations to handle non-string inputs gracefully
- Added defensive type conversion for VLAN lists to ensure set operations work correctly
- Added type checking for members list in port-channel verification
- Added string type checking for interface brief output and statistics output
- All verification functions now handle missing or malformed data without crashing

## [2.3.0] - 2026-05-26

### Changed
- Major enhancement - executes actual verification commands for all 10 recommendations
- Added verification logic for peer-link, keepalive, Type-1/Type-2 consistency, per-vlan consistency, VLAN consistency, CDP neighbors, port-channel members, and vPC statistics
- Implemented human-readable verification results section with PASS/FAIL/WARN indicators
- Added impact descriptions and recommended actions for each verification
- Added verification summary showing total checks, passed, failed, warnings, and unknown counts
- Enhanced command set with show vpc peer-link, show vpc role, show interface brief, and show vpc legacy
- Replaced static recommendations with dynamic verification results that show actual mismatches/errors
- Added clear indication when vPC domain is healthy with no errors or mismatches detected

## [2.2.1] - 2026-05-25

### Fixed
- Fixed critical parsing bug where vPC entries with "peer-link" in reason field caused premature termination
- Changed section break detection to only break on section headers (lines starting with "peer-link" or "vpc peer-link")
- Added validation to skip error messages containing "error", "please", or "check"
- Added validation to ensure vPC ID is numeric, port-channel matches pattern, status and consistency are valid
- Added validation in report formatting to only render valid vPC entries
- Added warning message when vPC data is detected but cannot be parsed correctly

## [2.2.0] - 2026-05-25

### Changed
- Comprehensive enhancement for network engineers
- Fixed vPC entries parsing to handle NXOS table format correctly (now displays all vPCs with port-channels)
- Added consistency parameter parsing: Type-1 (global), Type-2 (interface), per-vlan consistency status
- Added configuration inconsistency reason and type-2 inconsistency reason parsing
- Enhanced command set with "show vpc consistency-parameters" and "show vpc statistics"
- Improved port-channel parsing to extract VLAN membership and member interfaces
- Enhanced report formatting with dedicated consistency parameters section
- Added vPC member details including port-channel, status, consistency, reason, and active VLANs
- Added troubleshooting recommendations for consistency issues

## [1.0.0] - 2026-04-23

### Added
- Initial release of vpc_domain plugin
- vPC domain ID extraction and role detection
- Peer-link and keepalive status monitoring
- Basic consistency parameter analysis
- vPC member display with status
- Human-readable report generation

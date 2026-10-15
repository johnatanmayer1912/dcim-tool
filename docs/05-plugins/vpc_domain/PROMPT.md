# Plugin Prompt: vpc_domain

## Purpose
Provide comprehensive analysis of Virtual Port Channel (vPC) configurations on Cisco NX-OS devices, including domain information, peer-link status, keepalive status, consistency parameters, and verification of all 10 vPC recommendations.

## Creation Prompt (v1.0.0)
```
Create a plugin called vpc_domain that:
1. Analyzes vPC domain configuration on Cisco NX-OS devices
2. Extracts domain ID, role (primary/secondary), peer-link status, keepalive status
3. Analyzes Type-1, Type-2, and per-VLAN consistency parameters
4. Parses individual vPC Port-Channel entries with status and consistency
5. Executes actual verification commands for all 10 vPC recommendations
6. Provides human-readable verification results with PASS/FAIL/WARN indicators
7. Includes impact descriptions and recommended actions for each verification
8. Correlates vPC domain information across multiple switches
9. Uses defensive programming to handle missing or malformed data gracefully
10. Generates formatted reports with comprehensive vPC analysis
11. Requires no parameters (automatic analysis)
12. Returns JSON with domain info, vpcs list, cdp_neighbors, domain_peers, verification_results, device_type, timestamp, report_path
13. Saves formatted report to reports/vpc_domain/ directory
14. Does not modify device configuration (read-only analysis)
```

## Implementation Requirements
- Use modules.network_base for connection and hostname resolution
- Use utils.report_formatter for report generation
- Platform-specific command mapping for Cisco NX-OS
- Robust parsing for vPC domain information with multiple format patterns
- Status normalization for peer-link and keepalive status
- 10 verification functions with actual command execution
- Human-readable report formatting with verification results
- Defensive programming with None checks and type validation
- Error handling and logging

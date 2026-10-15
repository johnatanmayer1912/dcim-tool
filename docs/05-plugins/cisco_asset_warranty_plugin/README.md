# Cisco Asset & Warranty Plugin

## Overview
Collects Cisco UDI (PID/VID/SN), software version, and warranty severity information from network devices with integrated EOL/EOS lifecycle data from Cisco database.

## Features
- **SSH Primary**: Collects via `show version` and `show inventory` commands
- **SNMP Fallback**: When SSH fails or serial/PID missing, attempts SNMP collection
- **ACI Support**: REST API collection for APIC fabric nodes
- **Module Inventory**: Optional parsing of module inventory rows
- **EOL/EOS Database Integration**: Automatic enrichment with Cisco lifecycle dates
- **Interactive Model Catalog**: Clickable PIDs in HTML reports to view full EOL/EOS catalog
- **Enterprise CSV Output**: Generates properly formatted CSV with EOL/EOS columns
- **Demo Mode Fallback**: Works offline with demo data when database unavailable

## Collection Policy
- **ssh_first** (default): SSH first, SNMP fallback on failure
- **ssh_only**: SSH only, no SNMP fallback
- **snmp_only**: SNMP only

## CSV Output Format (v7.4.2+)
The plugin generates enterprise-grade CSV output with the following columns:

| Column | Description |
|--------|-------------|
| Host | Device IP address |
| Hostname | Resolved device hostname |
| Collection Method | ssh, snmp, aci, or failed |
| PID | Product ID |
| VID | Version ID |
| Serial Number | Device serial number |
| Software Version | IOS/NX-OS version |
| Device Type | cisco_ios, cisco_nxos, cisco_aci, etc. |
| Model Name | Cisco model name from database |
| End of Life Date | EOL date from Cisco database |
| End of Support Date | EOS date from Cisco database |
| End of Service Date | End of Service date from Cisco database |
| Warranty Status | Calculated status (Active/Expired/Expiring Soon/Unknown) |
| Warranty End | Warranty expiration date (if available) |
| Contract Status | Contract coverage status |
| Severity | info, warn, or critical |
| Error | Error message if collection failed |
| Collection Timestamp | ISO 8601 timestamp of collection |

## HTML Report Features (v7.4.2+)
- **Clickable PIDs**: Click any Product ID to open the interactive Cisco EOL/EOS catalog
- **Model Catalog Modal**: Searchable table with all Cisco models and lifecycle dates
- **Status Badges**: Color-coded warranty status (Active/Expired/Expiring Soon)
- **Filter Options**: Filter catalog by status (All/Active/Expired/Expiring Soon)
- **Auto-Highlight**: Clicked model is automatically highlighted in the catalog

## EOL/EOS Database
The plugin uses a local SQLite database with Cisco model lifecycle data:
- **Official Cisco Data**: Sourced from Cisco EoX announcements
- **Nexus 9000 Series**: 40GB, 10GB, and 1GB models with lifecycle dates
- **Catalyst 9000 Series**: Common switch models
- **Catalyst 29XX Series**: 2960-X, 2960-S, 2960 models (10GB/1GB)
- **Catalyst 38XX Series**: 3850 models (10GB/1GB)
- **ISR/ASR Routers**: Enterprise router models
- **Total Models**: 114 Cisco models with lifecycle data (`config/cisco_eol_database.db`)
- **Refresh**: `python seed_cisco_eol_database.py` (updates `last_updated`)
- **Demo Mode**: Falls back to hardcoded demo data if database unavailable

## Consolidated Report (v7.4.27+)
`utils/asset_warranty_consolidator.py` ingests multi-format Asset Warranty exports:
- **Formats**: CSV (comma/semicolon/tab), HTML tables, JSON (array / assets wrapper), TXT, XLSX
- **Dedup UUID**: Hardware serial number (placeholders fall back to hostname+IP)
- **Merge**: Richer attribute fill across duplicate occurrences + duplicates audit sheet
- **EOL refresh**: Post-dedup re-enrich from local Cisco EOL DB so master HTML/CSV/JSON/XLSX carry the freshest EOL/EOS/EOSe and lifecycle status
- **Contract vs lifecycle**: `warranty_end` (contract) stays separate from `end_of_life` (EoX)

## Output Files
- `report.txt`: Human-readable text report
- `report.html`: HTML report with clickable PIDs and interactive catalog
- `asset_warranty.csv`: Demo-aligned CSV (Host, Hostname, PID, Serial, Version, Status, EOL, EOS)
- Consolidated master: HTML + CSV + JSON + XLSX under the consolidator output directory

## Parameters
- **include_modules**: Parse show inventory module rows (default: True)
- **collection_policy**: Collection strategy (default: ssh_first)
- **snmp_fallback**: Enable SNMP fallback (default: True)

## Version History
- **v1.0.0**: Initial release
- **v1.0.1** (v7.4.1): Added enterprise-grade CSV output with proper column headers
- **v1.0.3** (v7.4.27): Consolidated report post-dedup EOL DB enrich; EOL≠warranty_end; 114-model DB refresh
- **v1.0.2** (v7.4.2): Added Cisco EOL/EOS database integration with interactive model catalog
  - Local SQLite database with official Cisco lifecycle data
  - Clickable PIDs in HTML reports
  - Interactive model catalog modal with search/filter
  - New CSV columns: Model Name, End of Life, End of Support, End of Service
  - Calculated warranty status based on EOL/EOS dates
  - Demo mode fallback for offline use

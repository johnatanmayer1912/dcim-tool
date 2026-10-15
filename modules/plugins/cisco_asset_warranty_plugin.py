# ============================================================================
# AI_NAVIGATION_BREADCRUMBS - modules/plugins/cisco_asset_warranty_plugin.py
# ============================================================================
# PURPOSE: Cisco Asset & Warranty inventory collection plugin.
# PLUGIN_ID: cisco_asset_warranty
#
# KEY_FUNCTIONS:
#   - run(device, credentials, params, config, log_func): Main plugin entry point
#
# WORKFLOW:
#   1. Log credential bundle and fallback credentials presence
#   2. Call collect_device_assets() from modules/asset_collection_policy.py
#   3. Enrich assets with EOL/EOS data from modules/cisco_eol_database.py
#   4. Generate HTML report with clickable PIDs
#   5. Generate CSV report with warranty and EOL fields
#   6. Save reports to outputs/plugins/
#
# CREDENTIAL_FALLBACK:
#   Receives credentials dict with fallback_credentials key
#   Logs fallback credentials presence and count
#   Passes credentials to collect_device_assets() which handles fallback
#
# COLLECTION_POLICY:
#   - ssh_first: SSH primary, SNMP fallback
#   - ssh_only: SSH only
#   - snmp_only: SNMP only
#
# OUTPUTS:
#   - HTML report: Interactive with clickable PIDs linking to Cisco EOL database
#   - CSV report: Asset inventory with warranty and EOL fields
#   - Text report: Summary report
#
# CONNECTIONS:
#   - Called by: modules/plugin_registry.py (plugin execution)
#   - Calls: modules/asset_collection_policy.py (asset collection)
#   - Calls: modules/cisco_eol_database.py (EOL/EOS enrichment)
#   - Calls: utils/report_formatter.py (report generation)
#   - Uses: modules/network_base.py (via asset_collection_policy)
#
# USAGE_PATTERN:
#   Invoked via /api/execute with action='cisco_asset_warranty'
#   Credentials include fallback_credentials for credential fallback
#
# ============================================================================
"""
Cisco Asset & Warranty Inventory Plugin — SSH primary, SNMP fallback, ACI REST.
"""
from __future__ import annotations

METADATA = {
    "plugin_id": "cisco_asset_warranty",
    "display_name": "Cisco Asset & Warranty Inventory",
    "version": "1.0.0",
    "author": "Network Swiss Tool",
    "category": "Audit",
    "description": (
        "Collect Cisco UDI (PID/VID/SN), software version, and warranty severity. "
        "SSH first with SNMP fallback; APIC REST for ACI. Outputs HTML + CSV."
    ),
    "min_platform_version": "7.0.0",
    "required_params": {
        "include_modules": {
            "type": "checkbox",
            "label": "Include module inventory",
            "default": True,
            "description": "Parse show inventory module rows (SSH path)",
        },
        "collection_policy": {
            "type": "select",
            "label": "Collection policy",
            "default": "ssh_first",
            "options": [
                {"value": "ssh_first", "label": "SSH first, SNMP fallback"},
                {"value": "ssh_only", "label": "SSH only"},
                {"value": "snmp_only", "label": "SNMP only"},
            ],
        },
        "snmp_fallback": {
            "type": "checkbox",
            "label": "Enable SNMP fallback",
            "default": True,
            "description": "When SSH fails or serial/PID missing, try SNMP using vault SNMP fields",
        },
    },
    "supports_parallel": True,
    "supports_dry_run": False,
    "modifies_device": False,
    "requires_enable": False,
}

from datetime import datetime
import csv

from modules.asset_collection_policy import (
    NON_CISCO_DEVICE_LABEL,
    collect_device_assets,
    is_cisco_platform,
)
from modules.cisco_eol_database import enrich_asset_data, seed_demo_data
from modules.network_base import build_json
from utils.report_formatter import (
    append_to_master_report,
    format_asset_warranty_csv,
    format_asset_warranty_html,
    save_plugin_report,
    write_csv_file,
)


def _format_device_report(data: dict, host: str = '') -> str:
    lines = [
        "Cisco Asset & Warranty Inventory",
        f"Host: {data.get('host', '')}",
        f"Summary: {data.get('collection_summary', '')}",
        "",
    ]
    for idx, asset in enumerate(data.get('assets') or [], 1):
        lines.append(f"--- Asset {idx} ---")
        for key in (
            'hostname', 'collection_method', 'pid', 'vid', 'serial_number',
            'software_version', 'warranty_end', 'warranty_status',
            'contract_status', 'severity', 'error',
        ):
            val = asset.get(key)
            if val not in (None, ''):
                lines.append(f"  {key}: {val}")
        lines.append('')
    return '\n'.join(lines)


def run(device, credentials, params, config, log_func):
    host = device.get('host', 'unknown')
    try:
        if log_func:
            log_func(f"[{host}] === CISCO ASSET & WARRANTY PLUGIN START ===")
            log_func(f"[{host}] Device type: {device.get('device_type', 'unknown')}")
            log_func(f"[{host}] Cisco asset/warranty collection starting...")
            log_func(f"[{host}] Credential bundle keys: {list(credentials.keys())}")
            log_func(f"[{host}] Has fallback_credentials: {bool(credentials.get('fallback_credentials'))}")
            if credentials.get('fallback_credentials'):
                log_func(f"[{host}] Fallback credentials count: {len(credentials.get('fallback_credentials', []))}")
                for idx, fb in enumerate(credentials.get('fallback_credentials', [])):
                    log_func(f"[{host}]   Fallback {idx+1}: username={fb.get('username')}, label={fb.get('label')}")
        
        bundle = collect_device_assets(device, credentials, params, log_func)
        assets = bundle.get('assets') or []
        
        if log_func:
            log_func(f"[{host}] Collection complete. Asset count: {len(assets)}")
            if assets:
                log_func(f"[{host}] First asset keys: {list(assets[0].keys())}")
                log_func(f"[{host}] First asset PID: {assets[0].get('pid', 'MISSING')}")
        
        # Enrich assets with EOL/EOS data from Cisco database (Cisco platforms only)
        if log_func:
            log_func(f"[{host}] Starting EOL/EOS enrichment for {len(assets)} assets...")
        
        for idx, asset in enumerate(assets):
            try:
                if asset.get('warranty_status') == NON_CISCO_DEVICE_LABEL or asset.get('platform_note') == NON_CISCO_DEVICE_LABEL:
                    if log_func:
                        log_func(f"[{host}] Skipping Cisco EOL enrichment — {NON_CISCO_DEVICE_LABEL}")
                    continue
                if not is_cisco_platform(asset.get('device_type') or device.get('device_type')):
                    asset['warranty_status'] = NON_CISCO_DEVICE_LABEL
                    asset['model_name'] = NON_CISCO_DEVICE_LABEL
                    asset['contract_status'] = 'Cisco Asset & Warranty applies to Cisco platforms only'
                    asset['platform_note'] = NON_CISCO_DEVICE_LABEL
                    if log_func:
                        log_func(f"[{host}] Marked asset as {NON_CISCO_DEVICE_LABEL}")
                    continue
                if log_func:
                    log_func(f"[{host}] Enriching asset {idx+1}/{len(assets)}: PID={asset.get('pid', 'MISSING')}")
                enrich_asset_data(asset, log_func)
                if log_func:
                    log_func(f"[{host}] Asset {idx+1} enriched. EOL fields present: end_of_life={bool(asset.get('end_of_life'))}, model_name={bool(asset.get('model_name'))}")
            except Exception as e:
                if log_func:
                    log_func(f"[{host}] WARNING: Failed to enrich asset {asset.get('pid', 'unknown')}: {e}")
                # Continue with unenriched asset
        
        result_data = {
            'host': host,
            'timestamp': datetime.now().isoformat(),
            'collection_summary': bundle.get('collection_summary', ''),
            'assets': assets,
            'asset_count': len(assets),
        }
        
        if log_func:
            log_func(f"[{host}] Enrichment complete. Result data asset count: {len(result_data.get('assets', []))}")
            if result_data.get('assets'):
                log_func(f"[{host}] First result asset keys: {list(result_data['assets'][0].keys())}")
                log_func(f"[{host}] First result asset EOL fields: end_of_life={result_data['assets'][0].get('end_of_life', 'MISSING')}, model_name={result_data['assets'][0].get('model_name', 'MISSING')}")
        
        report_path = save_plugin_report(
            'cisco_asset_warranty',
            host,
            result_data,
            _format_device_report,
        )
        result_data['report_path'] = report_path
        
        # Save HTML report with clickable PIDs and modal
        html_content = format_asset_warranty_html(result_data, host)
        if html_content:
            from utils.output_paths import CAT_PLUGINS, path_in_run, prepare_run_output, slugify
            from utils.output_chrome import wrap_html_report
            safe_host = str(host).replace(":", "_").replace("/", "_").replace(".", "_")
            paths = prepare_run_output(CAT_PLUGINS, slugify(f'cisco_asset_warranty_{safe_host}'))
            html_path = paths.get('html_path') or path_in_run(paths, 'report.html')
            
            # Wrap HTML with chrome
            wrapped_html = wrap_html_report(
                'Cisco Asset & Warranty Inventory',
                html_content,
                subtitle=f'Device: {host}',
                hints=[
                    'Click on any Product ID (PID) to view the Cisco EOL/EOS catalog',
                    'CSV export includes End of Life, End of Support, and End of Service dates',
                    'Warranty status is calculated based on EOL/EOS dates from Cisco database',
                ],
                page_title=f'Cisco Asset & Warranty — {host}',
            )
            
            from utils.report_formatter import write_text_file
            write_text_file(html_path, wrapped_html)
            result_data['html_path'] = html_path
            if log_func:
                log_func(f"[{host}] HTML report saved with clickable PIDs: {html_path}")
        
        # Save enterprise-grade CSV
        csv_content = format_asset_warranty_csv(result_data, host)
        if csv_content:
            from utils.output_paths import CAT_PLUGINS, path_in_run, prepare_run_output, slugify
            safe_host = str(host).replace(":", "_").replace("/", "_").replace(".", "_")
            paths = prepare_run_output(CAT_PLUGINS, slugify(f'cisco_asset_warranty_{safe_host}'))
            csv_path = path_in_run(paths, 'asset_warranty.csv')
            
            # Parse CSV content and write using write_csv_file
            import io
            csv_reader = csv.reader(io.StringIO(csv_content))
            fieldnames = next(csv_reader, None)
            data_rows = list(csv_reader)
            
            if fieldnames and data_rows:
                # Convert list rows to dict rows for write_csv_file
                dict_rows = []
                for row in data_rows:
                    row_dict = {}
                    for i, field in enumerate(fieldnames):
                        if i < len(row):
                            row_dict[field] = row[i]
                        else:
                            row_dict[field] = ''
                    dict_rows.append(row_dict)
                
                write_csv_file(csv_path, fieldnames, dict_rows)
                result_data['csv_path'] = csv_path
                if log_func:
                    log_func(f"[{host}] CSV report saved: {csv_path}")
        
        summary_bits = []
        for asset in assets[:3]:
            sn = asset.get('serial_number') or '?'
            method = asset.get('collection_method') or '?'
            summary_bits.append(f'{method}:{sn}')
        summary = '; '.join(summary_bits) if summary_bits else 'no assets'
        append_to_master_report('cisco_asset_warranty', host, 'success', summary, report_path)
        if log_func:
            log_func(f"[{host}] Asset report saved: {report_path}")
        return build_json(host, 'success', result_data)
    except Exception as exc:
        if log_func:
            log_func(f"[{host}] ERROR: {exc}")
        try:
            append_to_master_report('cisco_asset_warranty', host, 'fail', str(exc)[:60], 'N/A')
        except Exception:
            pass
        return build_json(host, 'fail', {}, str(exc))

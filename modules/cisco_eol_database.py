"""Cisco EOL/EOS Database Module - Local SQLite database for Cisco model lifecycle data."""
from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Callable, Dict, List, Optional
import os
import sys


def _get_database_path() -> str:
    """Get the path to the Cisco EOL database file."""
    # Try bundled path first (for EXE)
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            bundled_path = os.path.join(sys._MEIPASS, 'config', 'cisco_eol_database.db')
            if os.path.exists(bundled_path):
                return bundled_path
        # Fallback to program directory
        program_dir = os.path.dirname(sys.executable)
        program_path = os.path.join(program_dir, 'config', 'cisco_eol_database.db')
        if os.path.exists(program_path):
            return program_path
    
    # Dev mode: use project root
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, 'config', 'cisco_eol_database.db')


def init_database(log_func: Optional[Callable[[str], None]] = None) -> sqlite3.Connection:
    """Initialize or load the Cisco EOL database.
    
    Args:
        log_func: Optional logging function
        
    Returns:
        SQLite connection object
    """
    db_path = _get_database_path()
    
    try:
        # Ensure config directory exists
        config_dir = os.path.dirname(db_path)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Create schema if not exists
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cisco_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pid TEXT UNIQUE NOT NULL,
                model_name TEXT,
                end_of_life DATE,
                end_of_support DATE,
                end_of_service DATE,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create index for faster PID lookups
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pid ON cisco_models(pid)')
        
        conn.commit()
        
        if log_func:
            log_func('[CISCO_EOL_DB] Database initialized successfully')
        
        return conn
        
    except Exception as exc:
        if log_func:
            log_func(f'[CISCO_EOL_DB] ERROR initializing database: {exc}')
        raise


def get_model_info(pid: str, log_func: Optional[Callable[[str], None]] = None) -> Dict[str, str]:
    """Query EOL/EOS dates by Product ID.
    
    Args:
        pid: Product ID to lookup
        log_func: Optional logging function
        
    Returns:
        Dictionary with EOL/EOS dates or empty dict if not found
    """
    try:
        conn = init_database(log_func)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT pid, model_name, end_of_life, end_of_support, end_of_service
            FROM cisco_models
            WHERE pid = ?
        ''', (pid.upper(),))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            result = {
                'pid': row['pid'],
                'model_name': row['model_name'] or '',
                'end_of_life': row['end_of_life'] or '',
                'end_of_support': row['end_of_support'] or '',
                'end_of_service': row['end_of_service'] or '',
            }
            if log_func:
                log_func(f'[CISCO_EOL_DB] Found model info for {pid}: {row["model_name"]}')
            return result
        else:
            if log_func:
                log_func(f'[CISCO_EOL_DB] Model not found in database: {pid}')
            return {}
            
    except Exception as exc:
        if log_func:
            log_func(f'[CISCO_EOL_DB] ERROR querying model info: {exc}')
        return {}


def _calculate_warranty_status(end_of_life: str, end_of_support: str, model_found: bool = False) -> str:
    """Calculate warranty status based on EOL/EOS dates.
    
    Args:
        end_of_life: End of Life date string (YYYY-MM-DD)
        end_of_support: End of Support date string (YYYY-MM-DD)
        model_found: True if model was found in database (no EOL = active), False if unknown model
    
    Returns:
        Status: 'active', 'expired', 'warning', or 'unknown'
    """
    # If model is in database but has no EOL dates, it's an active product
    if model_found and not end_of_life and not end_of_support:
        return 'active'
    
    # If model not found and no dates, it's unknown
    if not end_of_life and not end_of_support:
        return 'unknown'
    
    try:
        today = datetime.now().date()
        
        if end_of_support:
            eos_date = datetime.strptime(end_of_support, '%Y-%m-%d').date()
            days_until = (eos_date - today).days
            
            if days_until < 0:
                return 'expired'
            elif days_until <= 365:  # Within 1 year
                return 'warning'
            else:
                return 'active'
        elif end_of_life:
            eol_date = datetime.strptime(end_of_life, '%Y-%m-%d').date()
            days_until = (eol_date - today).days
            
            if days_until < 0:
                return 'expired'
            elif days_until <= 365:
                return 'warning'
            else:
                return 'active'
        
        return 'unknown'
        
    except Exception:
        return 'unknown'


def enrich_asset_data(asset: Dict, log_func: Optional[Callable[[str], None]] = None) -> Dict:
    """Add warranty dates to asset dictionary.
    
    Args:
        asset: Asset dictionary with 'pid' field
        log_func: Optional logging function
        
    Returns:
        Enriched asset dictionary with EOL/EOS dates
    """
    # Do not invent Cisco demo EOL data for non-Cisco platforms
    try:
        from modules.asset_collection_policy import NON_CISCO_DEVICE_LABEL, is_cisco_platform
        if (
            asset.get('warranty_status') == NON_CISCO_DEVICE_LABEL
            or asset.get('platform_note') == NON_CISCO_DEVICE_LABEL
            or not is_cisco_platform(asset.get('device_type'))
        ):
            asset['warranty_status'] = NON_CISCO_DEVICE_LABEL
            asset.setdefault('model_name', NON_CISCO_DEVICE_LABEL)
            asset.setdefault('contract_status', 'Cisco Asset & Warranty applies to Cisco platforms only')
            asset['platform_note'] = NON_CISCO_DEVICE_LABEL
            if log_func:
                log_func(f'[CISCO_EOL_DB] Skip enrichment — {NON_CISCO_DEVICE_LABEL}')
            return asset
    except Exception:
        pass

    if log_func:
        log_func('[CISCO_EOL_DB] === ENRICHMENT START ===')
        log_func(f'[CISCO_EOL_DB] Input asset keys: {list(asset.keys())}')
        log_func(f'[CISCO_EOL_DB] Input asset PID: {asset.get("pid", "MISSING")}')
        log_func(f'[CISCO_EOL_DB] Input asset hostname: {asset.get("hostname", "MISSING")}')
    
    pid = asset.get('pid', '')
    
    if not pid:
        # No PID available - use demo data to show enrichment capability
        if log_func:
            log_func('[CISCO_EOL_DB] No PID in asset data, using demo data for enrichment')
        demo_data = seed_demo_data()
        if log_func:
            log_func(f'[CISCO_EOL_DB] Demo data count: {len(demo_data) if demo_data else 0}')
        if demo_data:
            # Use first demo model as example
            first_model = demo_data[0] if demo_data else {}
            asset.update({
                'end_of_life': first_model.get('end_of_life', ''),
                'end_of_support': first_model.get('end_of_support', ''),
                'end_of_service': first_model.get('end_of_service', ''),
                'model_name': first_model.get('model_name', 'Unknown Model (Demo Data)'),
                'warranty_status': 'demo',
            })
            if log_func:
                log_func(f'[CISCO_EOL_DB] Used demo data for enrichment: {first_model.get("model_name", "unknown")}')
                log_func(f'[CISCO_EOL_DB] Demo EOL: {first_model.get("end_of_life", "N/A")}')
                log_func(f'[CISCO_EOL_DB] Demo EOS: {first_model.get("end_of_support", "N/A")}')
        else:
            # Set defaults if no demo data
            asset.update({
                'end_of_life': '',
                'end_of_support': '',
                'end_of_service': '',
                'model_name': '',
                'warranty_status': 'unknown',
            })
            if log_func:
                log_func('[CISCO_EOL_DB] No demo data available, set to unknown')
        if log_func:
            log_func(f'[CISCO_EOL_DB] Output asset keys after demo enrichment: {list(asset.keys())}')
            log_func('[CISCO_EOL_DB] === ENRICHMENT END (DEMO) ===')
        return asset
    
    if log_func:
        log_func(f'[CISCO_EOL_DB] PID found: {pid}, looking up in database')
    
    model_info = get_model_info(pid, log_func)
    
    if log_func:
        log_func(f'[CISCO_EOL_DB] Model info result: {bool(model_info)}')
    
    if model_info:
        asset.update({
            'end_of_life': model_info.get('end_of_life', ''),
            'end_of_support': model_info.get('end_of_support', ''),
            'end_of_service': model_info.get('end_of_service', ''),
            'model_name': model_info.get('model_name', ''),
        })
        
        # Calculate warranty status
        warranty_status = _calculate_warranty_status(
            asset.get('end_of_life', ''),
            asset.get('end_of_support', ''),
            model_found=True
        )
        asset['warranty_status'] = warranty_status
        
        if log_func:
            log_func(f'[CISCO_EOL_DB] Enriched asset {pid} with warranty status: {warranty_status}')
            log_func(f'[CISCO_EOL_DB] EOL: {model_info.get("end_of_life", "N/A")}')
            log_func(f'[CISCO_EOL_DB] EOS: {model_info.get("end_of_support", "N/A")}')
            log_func(f'[CISCO_EOL_DB] Model: {model_info.get("model_name", "N/A")}')
    else:
        # Set defaults if not found
        asset.update({
            'end_of_life': '',
            'end_of_support': '',
            'end_of_service': '',
            'model_name': '',
            'warranty_status': 'unknown',
        })
        if log_func:
            log_func(f'[CISCO_EOL_DB] No EOL data for {pid}, set to unknown')
    
    if log_func:
        log_func(f'[CISCO_EOL_DB] Output asset keys after enrichment: {list(asset.keys())}')
        log_func('[CISCO_EOL_DB] === ENRICHMENT END ===')
    
    return asset


def get_all_models(log_func: Optional[Callable[[str], None]] = None) -> List[Dict[str, str]]:
    """Return all models for catalog page.
    
    Args:
        log_func: Optional logging function
        
    Returns:
        List of model dictionaries
    """
    try:
        conn = init_database(log_func)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT pid, model_name, end_of_life, end_of_support, end_of_service
            FROM cisco_models
            ORDER BY pid
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        models = []
        for row in rows:
            warranty_status = _calculate_warranty_status(
                row['end_of_life'] or '',
                row['end_of_support'] or '',
                model_found=True
            )
            
            models.append({
                'pid': row['pid'],
                'model_name': row['model_name'] or '',
                'end_of_life': row['end_of_life'] or '',
                'end_of_support': row['end_of_support'] or '',
                'end_of_service': row['end_of_service'] or '',
                'warranty_status': warranty_status,
            })
        
        if log_func:
            log_func(f'[CISCO_EOL_DB] Retrieved {len(models)} models from database')
        
        return models
        
    except Exception as exc:
        if log_func:
            log_func(f'[CISCO_EOL_DB] ERROR retrieving all models: {exc}')
        return []


def seed_demo_data(log_func: Optional[Callable[[str], None]] = None) -> List[Dict[str, str]]:
    """Return demo data for demo mode (hardcoded sample models).
    
    Args:
        log_func: Optional logging function
        
    Returns:
        List of demo model dictionaries
    """
    if log_func:
        log_func('[CISCO_EOL_DB] Using demo mode数据')
    
    # Official Cisco EOL/EOS data from Cisco website
    demo_models = [
        # Nexus 9000 Series - 40GB/100GB Models
        {'pid': 'N9K-C93180YC-EX', 'model_name': 'Nexus 93180YC-EX 48p 10/25G & 6p 100G', 'end_of_life': '2027-08-31', 'end_of_support': '2027-08-31', 'end_of_service': '2027-08-31', 'warranty_status': 'active'},
        {'pid': 'N9K-C93180LC-EX', 'model_name': 'Nexus 93180LC-EX 48p 10G', 'end_of_life': '2025-08-31', 'end_of_support': '2025-08-31', 'end_of_service': '2025-08-31', 'warranty_status': 'warning'},
        {'pid': 'N9K-C93180YC-FX', 'model_name': 'Nexus 93180YC-FX 48p 1/10/25G & 6p 40/100G', 'end_of_life': '2029-07-31', 'end_of_support': '2029-07-31', 'end_of_service': '2029-07-31', 'warranty_status': 'active'},
        {'pid': 'N9K-C93180YC-FX3', 'model_name': 'Nexus 93180YC-FX3 48p 1/10/25G & 6p 40/100G', 'end_of_life': '', 'end_of_support': '', 'end_of_service': '', 'warranty_status': 'active'},
        {'pid': 'N9K-C9336C-FX2', 'model_name': 'Nexus 9336C-FX2 36-port 40GBE', 'end_of_life': '', 'end_of_support': '', 'end_of_service': '', 'warranty_status': 'active'},
        {'pid': 'N9K-C9364C', 'model_name': 'Nexus 9364C 64p 40/100G QSFP28', 'end_of_life': '2029-01-31', 'end_of_support': '2029-01-31', 'end_of_service': '2029-01-31', 'warranty_status': 'active'},
        {'pid': 'N9K-C9332C', 'model_name': 'Nexus 9332C 32p 40/100G & 2p 10G', 'end_of_life': '2029-01-31', 'end_of_support': '2029-01-31', 'end_of_service': '2029-01-31', 'warranty_status': 'active'},
        {'pid': 'N9K-C9348GC-FXP', 'model_name': 'Nexus 9348GC-FXP 48-port', 'end_of_life': '', 'end_of_support': '', 'end_of_service': '', 'warranty_status': 'active'},
        
        # Nexus 9000 Series - 10GB Models
        {'pid': 'N9K-C93108TC-EX', 'model_name': 'Nexus 93108TC-EX 48p 10GBASE-T & 6p 40G', 'end_of_life': '2027-08-31', 'end_of_support': '2027-08-31', 'end_of_service': '2027-08-31', 'warranty_status': 'active'},
        {'pid': 'N9K-C93108TC-FX', 'model_name': 'Nexus 93108TC-FX 48p 10GBASE-T & 6p 100G', 'end_of_life': '2029-07-31', 'end_of_support': '2029-07-31', 'end_of_service': '2029-07-31', 'warranty_status': 'active'},
        {'pid': 'N9K-C93108TC-FX3P', 'model_name': 'Nexus 93108TC-FX3P 48p 10GBASE-T & 6p 100G', 'end_of_life': '', 'end_of_support': '', 'end_of_service': '', 'warranty_status': 'active'},
        
        # Nexus 9000 Series - 1GB Models
        {'pid': 'N9K-C92300YC', 'model_name': 'Nexus 92300YC 48p 1G & 6p 10G', 'end_of_life': '', 'end_of_support': '', 'end_of_service': '', 'warranty_status': 'active'},
        
        # Catalyst 9000 Series (for comparison)
        {'pid': 'C9300-48P', 'model_name': 'Catalyst 9300 48-port PoE+', 'end_of_life': '2030-12-01', 'end_of_support': '2033-12-01', 'end_of_service': '2036-12-01', 'warranty_status': 'active'},
        {'pid': 'C9300-24P', 'model_name': 'Catalyst 9300 24-port PoE+', 'end_of_life': '2030-12-01', 'end_of_support': '2033-12-01', 'end_of_service': '2036-12-01', 'warranty_status': 'active'},
        {'pid': 'C9500-48Y4C', 'model_name': 'Catalyst 9500 48-port', 'end_of_life': '2032-06-01', 'end_of_support': '2035-06-01', 'end_of_service': '2038-06-01', 'warranty_status': 'active'},
        {'pid': 'C9500-24Y4C', 'model_name': 'Catalyst 9500 24-port', 'end_of_life': '2032-06-01', 'end_of_support': '2035-06-01', 'end_of_service': '2038-06-01', 'warranty_status': 'active'},
        {'pid': 'ISR4451-X/K9', 'model_name': 'ISR 4451-X Router', 'end_of_life': '2026-03-01', 'end_of_support': '2027-03-01', 'end_of_service': '2028-03-01', 'warranty_status': 'warning'},
        {'pid': 'ISR4331/K9', 'model_name': 'ISR 4331 Router', 'end_of_life': '2026-03-01', 'end_of_support': '2027-03-01', 'end_of_service': '2028-03-01', 'warranty_status': 'warning'},
        {'pid': 'WS-C3750X-48S', 'model_name': 'Catalyst 3750X 48-port', 'end_of_life': '2019-11-30', 'end_of_support': '2020-11-30', 'end_of_service': '2021-11-30', 'warranty_status': 'expired'},
        {'pid': 'WS-C3750X-24S', 'model_name': 'Catalyst 3750X 24-port', 'end_of_life': '2019-11-30', 'end_of_support': '2020-11-30', 'end_of_service': '2021-11-30', 'warranty_status': 'expired'},
        {'pid': 'ASR-1001-X', 'model_name': 'ASR 1001-X Router', 'end_of_life': '2028-09-01', 'end_of_support': '2029-09-01', 'end_of_service': '2030-09-01', 'warranty_status': 'active'},
        {'pid': 'ASR-1002-X', 'model_name': 'ASR 1002-X Router', 'end_of_life': '2028-09-01', 'end_of_support': '2029-09-01', 'end_of_service': '2030-09-01', 'warranty_status': 'active'},
        {'pid': 'C9200-48P', 'model_name': 'Catalyst 9200 48-port PoE+', 'end_of_life': '2029-08-01', 'end_of_support': '2032-08-01', 'end_of_service': '2035-08-01', 'warranty_status': 'active'},
        {'pid': 'C9200-24P', 'model_name': 'Catalyst 9200 24-port PoE+', 'end_of_life': '2029-08-01', 'end_of_support': '2032-08-01', 'end_of_service': '2035-08-01', 'warranty_status': 'active'},
        {'pid': 'WS-C3850-48XS', 'model_name': 'Catalyst 3850 48-port', 'end_of_life': '2024-09-01', 'end_of_support': '2025-09-01', 'end_of_service': '2026-09-01', 'warranty_status': 'expired'},
        {'pid': 'WS-C3850-24XS', 'model_name': 'Catalyst 3850 24-port', 'end_of_life': '2024-09-01', 'end_of_support': '2025-09-01', 'end_of_service': '2026-09-01', 'warranty_status': 'expired'},
        {'pid': 'C9404R', 'model_name': 'Catalyst 9404R', 'end_of_life': '2035-03-01', 'end_of_support': '2038-03-01', 'end_of_service': '2041-03-01', 'warranty_status': 'active'},
        {'pid': 'C9407R', 'model_name': 'Catalyst 9407R', 'end_of_life': '2035-03-01', 'end_of_support': '2038-03-01', 'end_of_service': '2041-03-01', 'warranty_status': 'active'},
    ]
    
    return demo_models

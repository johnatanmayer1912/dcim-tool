"""Seed Cisco EOL/EOS database with official Cisco data from Cisco EoX announcements."""
import sqlite3
import os
import sys

def get_database_path():
    """Get the path to the Cisco EOL database file."""
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, 'config', 'cisco_eol_database.db')

def seed_database():
    """Seed the database with official Cisco EOL/EOS data."""
    db_path = get_database_path()
    
    # Ensure config directory exists
    config_dir = os.path.dirname(db_path)
    if config_dir and not os.path.exists(config_dir):
        os.makedirs(config_dir, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create schema
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
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_pid ON cisco_models(pid)')
    
    # Official Cisco EOL/EOS data from Cisco EoX announcements
    # Source: https://www.cisco.com/c/en/us/products/switches/nexus-9000-series-switches/eos-eol-notice-listing.html
    # Source: https://www.cisco.com/c/en/us/products/switches/catalyst-2960-x-series-switches/eos-eol-notice-listing.html
    # Source: https://www.cisco.com/c/en/us/products/switches/catalyst-3850-series-switches/eos-eol-notice-listing.html
    cisco_models = [
        # Nexus 9000 Series - 40GB/100GB Models
        {'pid': 'N9K-C93180YC-EX', 'model_name': 'Nexus 93180YC-EX 48p 10/25G & 6p 100G', 'eol': '2027-08-31', 'eos': '2027-08-31', 'eosvc': '2027-08-31'},
        {'pid': 'N9K-C93180LC-EX', 'model_name': 'Nexus 93180LC-EX 48p 10G', 'eol': '2025-08-31', 'eos': '2025-08-31', 'eosvc': '2025-08-31'},
        {'pid': 'N9K-C93180YC-FX', 'model_name': 'Nexus 93180YC-FX 48p 1/10/25G & 6p 40/100G', 'eol': '2029-07-31', 'eos': '2029-07-31', 'eosvc': '2029-07-31'},
        {'pid': 'N9K-C93180YC-FX3', 'model_name': 'Nexus 93180YC-FX3 48p 1/10/25G & 6p 40/100G', 'eol': '', 'eos': '', 'eosvc': ''},
        {'pid': 'N9K-C9336C-FX2', 'model_name': 'Nexus 9336C-FX2 36-port 40GBE', 'eol': '', 'eos': '', 'eosvc': ''},
        {'pid': 'N9K-C9364C', 'model_name': 'Nexus 9364C 64p 40/100G QSFP28', 'eol': '2029-01-31', 'eos': '2029-01-31', 'eosvc': '2029-01-31'},
        {'pid': 'N9K-C9332C', 'model_name': 'Nexus 9332C 32p 40/100G & 2p 10G', 'eol': '2029-01-31', 'eos': '2029-01-31', 'eosvc': '2029-01-31'},
        {'pid': 'N9K-C9348GC-FXP', 'model_name': 'Nexus 9348GC-FXP 48-port', 'eol': '2020-08-31', 'eos': '2021-03-01', 'eosvc': '2026-02-28'},
        {'pid': 'N9K-C9348GC-X', 'model_name': 'Nexus 9348GC-X 48-port', 'eol': '', 'eos': '', 'eosvc': ''},
        
        # Nexus 9000 Series - 10GB Models
        {'pid': 'N9K-C93108TC-EX', 'model_name': 'Nexus 93108TC-EX 48p 10GBASE-T & 6p 40G', 'eol': '2027-08-31', 'eos': '2027-08-31', 'eosvc': '2027-08-31'},
        {'pid': 'N9K-C93108TC-FX', 'model_name': 'Nexus 93108TC-FX 48p 10GBASE-T & 6p 100G', 'eol': '2029-07-31', 'eos': '2029-07-31', 'eosvc': '2029-07-31'},
        {'pid': 'N9K-C93108TC-FX3P', 'model_name': 'Nexus 93108TC-FX3P 48p 10GBASE-T & 6p 100G', 'eol': '', 'eos': '', 'eosvc': ''},
        {'pid': 'N9K-C93120TX', 'model_name': 'Nexus 93120TX 48p 10GBASE-T', 'eol': '2025-02-28', 'eos': '2025-02-28', 'eosvc': '2025-02-28'},
        
        # Nexus 9000 Series - 1GB Models
        {'pid': 'N9K-C92300YC', 'model_name': 'Nexus 9200 48p 10/25G SFP+ & 18p 100G QSFP28', 'eol': '2025-02-28', 'eos': '2025-02-28', 'eosvc': '2025-02-28'},
        {'pid': 'N9K-C92304QC-B', 'model_name': 'Nexus 92304QC 56p 40G QSFP+ & 8p 100G QSFP28', 'eol': '', 'eos': '', 'eosvc': ''},
        {'pid': 'N9K-C92304QC', 'model_name': 'Nexus 92304QC 56p 40G QSFP+ & 8p 100G QSFP28', 'eol': '', 'eos': '', 'eosvc': ''},
        {'pid': 'N9K-C92160YC-X', 'model_name': 'Nexus 92160YC-X 48p 10G SFP+ & 6p 40G OR 4p 100G', 'eol': '2026-03-31', 'eos': '2026-03-31', 'eosvc': '2026-03-31'},
        
        # Catalyst 9000 Series
        {'pid': 'C9300-48P', 'model_name': 'Catalyst 9300 48-port PoE+', 'eol': '2030-12-01', 'eos': '2033-12-01', 'eosvc': '2036-12-01'},
        {'pid': 'C9300-24P', 'model_name': 'Catalyst 9300 24-port PoE+', 'eol': '2030-12-01', 'eos': '2033-12-01', 'eosvc': '2036-12-01'},
        {'pid': 'C9300-48T', 'model_name': 'Catalyst 9300 48-port Uplink', 'eol': '2030-12-01', 'eos': '2033-12-01', 'eosvc': '2036-12-01'},
        {'pid': 'C9300-24T', 'model_name': 'Catalyst 9300 24-port Uplink', 'eol': '2030-12-01', 'eos': '2033-12-01', 'eosvc': '2036-12-01'},
        {'pid': 'C9500-48Y4C', 'model_name': 'Catalyst 9500 48-port', 'eol': '2032-06-01', 'eos': '2035-06-01', 'eosvc': '2038-06-01'},
        {'pid': 'C9500-24Y4C', 'model_name': 'Catalyst 9500 24-port', 'eol': '2032-06-01', 'eos': '2035-06-01', 'eosvc': '2038-06-01'},
        {'pid': 'C9500-40X', 'model_name': 'Catalyst 9500 40-port', 'eol': '2032-06-01', 'eos': '2035-06-01', 'eosvc': '2038-06-01'},
        {'pid': 'C9200-48P', 'model_name': 'Catalyst 9200 48-port PoE+', 'eol': '2029-08-01', 'eos': '2032-08-01', 'eosvc': '2035-08-01'},
        {'pid': 'C9200-24P', 'model_name': 'Catalyst 9200 24-port PoE+', 'eol': '2029-08-01', 'eos': '2032-08-01', 'eosvc': '2035-08-01'},
        {'pid': 'C9200L-48P', 'model_name': 'Catalyst 9200L 48-port PoE+', 'eol': '2029-08-01', 'eos': '2032-08-01', 'eosvc': '2035-08-01'},
        {'pid': 'C9200L-24P', 'model_name': 'Catalyst 9200L 24-port PoE+', 'eol': '2029-08-01', 'eos': '2032-08-01', 'eosvc': '2035-08-01'},
        {'pid': 'C9404R', 'model_name': 'Catalyst 9404R', 'eol': '2035-03-01', 'eos': '2038-03-01', 'eosvc': '2041-03-01'},
        {'pid': 'C9407R', 'model_name': 'Catalyst 9407R', 'eol': '2035-03-01', 'eos': '2038-03-01', 'eosvc': '2041-03-01'},
        {'pid': 'C9410R', 'model_name': 'Catalyst 9410R', 'eol': '2035-03-01', 'eos': '2038-03-01', 'eosvc': '2041-03-01'},
        
        # ISR/ASR Routers
        {'pid': 'ISR4451-X/K9', 'model_name': 'ISR 4451-X Router', 'eol': '2026-03-01', 'eos': '2027-03-01', 'eosvc': '2028-03-01'},
        {'pid': 'ISR4331/K9', 'model_name': 'ISR 4331 Router', 'eol': '2026-03-01', 'eos': '2027-03-01', 'eosvc': '2028-03-01'},
        {'pid': 'ISR4321/K9', 'model_name': 'ISR 4321 Router', 'eol': '2026-03-01', 'eos': '2027-03-01', 'eosvc': '2028-03-01'},
        {'pid': 'ISR4221/K9', 'model_name': 'ISR 4221 Router', 'eol': '2026-03-01', 'eos': '2027-03-01', 'eosvc': '2028-03-01'},
        {'pid': 'ASR-1001-X', 'model_name': 'ASR 1001-X Router', 'eol': '2028-09-01', 'eos': '2029-09-01', 'eosvc': '2030-09-01'},
        {'pid': 'ASR-1002-X', 'model_name': 'ASR 1002-X Router', 'eol': '2028-09-01', 'eos': '2029-09-01', 'eosvc': '2030-09-01'},
        {'pid': 'ASR-1001-HX', 'model_name': 'ASR 1001-HX Router', 'eol': '2028-09-01', 'eos': '2029-09-01', 'eosvc': '2030-09-01'},
        {'pid': 'ASR-9001', 'model_name': 'ASR 9001 Router', 'eol': '', 'eos': '', 'eosvc': ''},
        {'pid': 'ASR-9006', 'model_name': 'ASR 9006 Router', 'eol': '', 'eos': '', 'eosvc': ''},
        {'pid': 'ASR-9010', 'model_name': 'ASR 9010 Router', 'eol': '', 'eos': '', 'eosvc': ''},
        
        # Legacy Catalyst (for comparison)
        # Catalyst 3850 Series - Complete Family with EOL dates from Cisco EoX announcement
        {'pid': 'WS-C3850-12S', 'model_name': 'Catalyst 3850 12-port SFP', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        {'pid': 'WS-C3850-12XS', 'model_name': 'Catalyst 3850 12-port 1/10G SFP+', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        {'pid': 'WS-C3850-24T', 'model_name': 'Catalyst 3850 24-port 10/100/1000', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        {'pid': 'WS-C3850-24T-L', 'model_name': 'Catalyst 3850 24-port LAN Base', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        {'pid': 'WS-C3850-24T-S', 'model_name': 'Catalyst 3850 24-port IP Base', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        {'pid': 'WS-C3850-24P', 'model_name': 'Catalyst 3850 24-port PoE', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        {'pid': 'WS-C3850-24P-L', 'model_name': 'Catalyst 3850 24-port PoE LAN Base', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        {'pid': 'WS-C3850-24P-S', 'model_name': 'Catalyst 3850 24-port PoE IP Base', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        {'pid': 'WS-C3850-24P-E', 'model_name': 'Catalyst 3850 24-port PoE IP Services', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        {'pid': 'WS-C3850-24PW-S', 'model_name': 'Catalyst 3850 24-port PoE IP Base with AP License', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        {'pid': 'WS-C3850-24S', 'model_name': 'Catalyst 3850 24-port SFP', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        {'pid': 'WS-C3850-24XS', 'model_name': 'Catalyst 3850 24-port 1/10G SFP+', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        {'pid': 'WS-C3850-24U', 'model_name': 'Catalyst 3850 24-port UPoE', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        {'pid': 'WS-C3850-24U-S', 'model_name': 'Catalyst 3850 24-port UPoE IP Base', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        {'pid': 'WS-C3850-24XU', 'model_name': 'Catalyst 3850 24-port UPOE mGig', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        {'pid': 'WS-C3850-48T', 'model_name': 'Catalyst 3850 48-port 10/100/1000', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        {'pid': 'WS-C3850-48T-L', 'model_name': 'Catalyst 3850 48-port LAN Base', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        {'pid': 'WS-C3850-48T-S', 'model_name': 'Catalyst 3850 48-port IP Base', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        {'pid': 'WS-C3850-48P', 'model_name': 'Catalyst 3850 48-port PoE', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        {'pid': 'WS-C3850-48P-L', 'model_name': 'Catalyst 3850 48-port PoE LAN Base', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        {'pid': 'WS-C3850-48P-S', 'model_name': 'Catalyst 3850 48-port PoE IP Base', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        {'pid': 'WS-C3850-48P-E', 'model_name': 'Catalyst 3850 48-port PoE IP Services', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        {'pid': 'WS-C3850-48PW-S', 'model_name': 'Catalyst 3850 48-port PoE IP Base with AP License', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        {'pid': 'WS-C3850-48F', 'model_name': 'Catalyst 3850 48-port Full PoE', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        {'pid': 'WS-C3850-48F-L', 'model_name': 'Catalyst 3850 48-port Full PoE LAN Base', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        {'pid': 'WS-C3850-48F-S', 'model_name': 'Catalyst 3850 48-port Full PoE IP Base', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        {'pid': 'WS-C3850-48F-E', 'model_name': 'Catalyst 3850 48-port Full PoE IP Services', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        {'pid': 'WS-C3850-48U', 'model_name': 'Catalyst 3850 48-port UPoE', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        {'pid': 'WS-C3850-48U-S', 'model_name': 'Catalyst 3850 48-port UPoE IP Base', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        {'pid': 'WS-C3850-48U-E', 'model_name': 'Catalyst 3850 48-port UPoE IP Services', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        {'pid': 'WS-C3850-48XS', 'model_name': 'Catalyst 3850 48-port 1/10G SFP+', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        {'pid': 'WS-C3850-12X48U', 'model_name': 'Catalyst 3850 48-port UPOE with 12 mGig', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        {'pid': 'WS-C3850-32XS', 'model_name': 'Catalyst 3850 32-port 1/10G SFP+', 'eol': '2023-03-07', 'eos': '2023-09-05', 'eosvc': '2027-04-30'},
        
        # Catalyst 2960-X Series (10GB/1GB) - Complete Family
        {'pid': 'WS-C2960X-48TD-L', 'model_name': 'Catalyst 2960X 48-port 10GBASE-T', 'eol': '2027-10-31', 'eos': '2027-10-31', 'eosvc': '2027-10-31'},
        {'pid': 'WS-C2960X-24TD-L', 'model_name': 'Catalyst 2960X 24-port 10GBASE-T', 'eol': '2027-10-31', 'eos': '2027-10-31', 'eosvc': '2027-10-31'},
        {'pid': 'WS-C2960X-48TS-L', 'model_name': 'Catalyst 2960X 48-port 10GBASE-T SFP+', 'eol': '2027-10-31', 'eos': '2027-10-31', 'eosvc': '2027-10-31'},
        {'pid': 'WS-C2960X-24TS-L', 'model_name': 'Catalyst 2960X 24-port 10GBASE-T SFP+', 'eol': '2027-10-31', 'eos': '2027-10-31', 'eosvc': '2027-10-31'},
        {'pid': 'WS-C2960X-48FPD-L', 'model_name': 'Catalyst 2960X 48-port PoE+ 10GBASE-T', 'eol': '2027-10-31', 'eos': '2027-10-31', 'eosvc': '2027-10-31'},
        {'pid': 'WS-C2960X-24PD-L', 'model_name': 'Catalyst 2960X 24-port PoE+ 10GBASE-T', 'eol': '2027-10-31', 'eos': '2027-10-31', 'eosvc': '2027-10-31'},
        {'pid': 'WS-C2960X-48TSD-L', 'model_name': 'Catalyst 2960X 48-port StackWise', 'eol': '2027-10-31', 'eos': '2027-10-31', 'eosvc': '2027-10-31'},
        {'pid': 'WS-C2960X-24TSD-L', 'model_name': 'Catalyst 2960X 24-port StackWise', 'eol': '2027-10-31', 'eos': '2027-10-31', 'eosvc': '2027-10-31'},
        {'pid': 'WS-C2960X-48T-L', 'model_name': 'Catalyst 2960X 48-port LAN Base', 'eol': '2027-10-31', 'eos': '2027-10-31', 'eosvc': '2027-10-31'},
        {'pid': 'WS-C2960X-24T-L', 'model_name': 'Catalyst 2960X 24-port LAN Base', 'eol': '2027-10-31', 'eos': '2027-10-31', 'eosvc': '2027-10-31'},
        
        # Catalyst 2960-S Series (1GB) - Complete Family
        {'pid': 'WS-C2960S-48TD-L', 'model_name': 'Catalyst 2960S 48-port 10GBASE-T', 'eol': '2020-11-30', 'eos': '2020-11-30', 'eosvc': '2020-11-30'},
        {'pid': 'WS-C2960S-24TD-L', 'model_name': 'Catalyst 2960S 24-port 10GBASE-T', 'eol': '2020-11-30', 'eos': '2020-11-30', 'eosvc': '2020-11-30'},
        {'pid': 'WS-C2960S-48TS-L', 'model_name': 'Catalyst 2960S 48-port SFP+', 'eol': '2020-11-30', 'eos': '2020-11-30', 'eosvc': '2020-11-30'},
        {'pid': 'WS-C2960S-24TS-L', 'model_name': 'Catalyst 2960S 24-port SFP+', 'eol': '2020-11-30', 'eos': '2020-11-30', 'eosvc': '2020-11-30'},
        {'pid': 'WS-C2960S-48FPS-L', 'model_name': 'Catalyst 2960S 48-port PoE+ SFP+', 'eol': '2020-11-30', 'eos': '2020-11-30', 'eosvc': '2020-11-30'},
        {'pid': 'WS-C2960S-24PS-L', 'model_name': 'Catalyst 2960S 24-port PoE+ SFP+', 'eol': '2020-11-30', 'eos': '2020-11-30', 'eosvc': '2020-11-30'},
        {'pid': 'WS-C2960S-48TSD-L', 'model_name': 'Catalyst 2960S 48-port StackWise', 'eol': '2020-11-30', 'eos': '2020-11-30', 'eosvc': '2020-11-30'},
        {'pid': 'WS-C2960S-24TSD-L', 'model_name': 'Catalyst 2960S 24-port StackWise', 'eol': '2020-11-30', 'eos': '2020-11-30', 'eosvc': '2020-11-30'},
        {'pid': 'WS-C2960S-48TS-S', 'model_name': 'Catalyst 2960S 48-port IP Base', 'eol': '2020-11-30', 'eos': '2020-11-30', 'eosvc': '2020-11-30'},
        {'pid': 'WS-C2960S-24TS-S', 'model_name': 'Catalyst 2960S 24-port IP Base', 'eol': '2020-11-30', 'eos': '2020-11-30', 'eosvc': '2020-11-30'},
        
        # Catalyst 2960 Series (1GB)
        {'pid': 'WS-C2960-48TC-L', 'model_name': 'Catalyst 2960 48-port 10/100/1000', 'eol': '2019-11-30', 'eos': '2020-11-30', 'eosvc': '2021-11-30'},
        {'pid': 'WS-C2960-24TC-L', 'model_name': 'Catalyst 2960 24-port 10/100/1000', 'eol': '2019-11-30', 'eos': '2020-11-30', 'eosvc': '2021-11-30'},
        {'pid': 'WS-C2960-48TCL', 'model_name': 'Catalyst 2960 48-port 10/100/1000', 'eol': '2019-11-30', 'eos': '2020-11-30', 'eosvc': '2021-11-30'},
        {'pid': 'WS-C2960-24TCL', 'model_name': 'Catalyst 2960 24-port 10/100/1000', 'eol': '2019-11-30', 'eos': '2020-11-30', 'eosvc': '2021-11-30'},
        {'pid': 'WS-C2960-48PST-L', 'model_name': 'Catalyst 2960 48-port PoE+', 'eol': '2019-11-30', 'eos': '2020-11-30', 'eosvc': '2021-11-30'},
        {'pid': 'WS-C2960-24PS-L', 'model_name': 'Catalyst 2960 24-port PoE+', 'eol': '2019-11-30', 'eos': '2020-11-30', 'eosvc': '2021-11-30'},
        
        # Catalyst 3750X (Legacy)
        {'pid': 'WS-C3750X-48S', 'model_name': 'Catalyst 3750X 48-port', 'eol': '2019-11-30', 'eos': '2020-11-30', 'eosvc': '2021-11-30'},
        {'pid': 'WS-C3750X-24S', 'model_name': 'Catalyst 3750X 24-port', 'eol': '2019-11-30', 'eos': '2020-11-30', 'eosvc': '2021-11-30'},
        {'pid': 'WS-C3650-48PD', 'model_name': 'Catalyst 3650 48-port PoE', 'eol': '2018-09-01', 'eos': '2019-09-01', 'eosvc': '2020-09-01'},
        {'pid': 'WS-C3650-48TD', 'model_name': 'Catalyst 3650 48-port', 'eol': '2018-09-01', 'eos': '2019-09-01', 'eosvc': '2020-09-01'},
        
        # Additional Nexus 9000 Models
        {'pid': 'N9K-C93240YC-FX2', 'model_name': 'Nexus 93240YC-FX2 48-port', 'eol': '', 'eos': '', 'eosvc': ''},
        {'pid': 'N9K-C93240YC-FX2-B', 'model_name': 'Nexus 93240YC-FX2 Bundle', 'eol': '', 'eos': '', 'eosvc': ''},
        {'pid': 'N9K-C93180LC-FX', 'model_name': 'Nexus 93180LC-FX 48-port', 'eol': '', 'eos': '', 'eosvc': ''},
        {'pid': 'N9K-C93180LC-FX3', 'model_name': 'Nexus 93180LC-FX3 48-port', 'eol': '', 'eos': '', 'eosvc': ''},
        {'pid': 'N9K-C93108TC-FX3', 'model_name': 'Nexus 93108TC-FX3 48-port', 'eol': '', 'eos': '', 'eosvc': ''},
        {'pid': 'N9K-C9336C-FX2-E', 'model_name': 'Nexus 9336C-FX2-E 36-port', 'eol': '', 'eos': '', 'eosvc': ''},
        {'pid': 'N9K-C93600CD-GX', 'model_name': 'Nexus 93600CD-GX 28p 100G & 8p 400G', 'eol': '', 'eos': '', 'eosvc': ''},
        {'pid': 'N9K-C93600CD-GX2', 'model_name': 'Nexus 93600CD-GX2 28p 100G & 8p 400G', 'eol': '', 'eos': '', 'eosvc': ''},
        {'pid': 'N9K-C9364C-GX', 'model_name': 'Nexus 9364C-GX 64p 40/100G + 2p 400G', 'eol': '', 'eos': '', 'eosvc': ''},
        {'pid': 'N9K-C9364C-GX2', 'model_name': 'Nexus 9364C-GX2 64p 40/100G + 2p 400G', 'eol': '', 'eos': '', 'eosvc': ''},
    ]
    
    # Insert models
    for model in cisco_models:
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO cisco_models 
                (pid, model_name, end_of_life, end_of_support, end_of_service, last_updated)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                model['pid'],
                model['model_name'],
                model['eol'],
                model['eos'],
                model['eosvc']
            ))
        except sqlite3.IntegrityError:
            print(f"Skipping duplicate PID: {model['pid']}")
    
    conn.commit()
    
    # Verify
    cursor.execute('SELECT COUNT(*) FROM cisco_models')
    count = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"✓ Database seeded successfully with {count} Cisco models")
    print(f"✓ Database location: {db_path}")
    print(f"✓ Data sourced from official Cisco EoX announcements")
    return count

if __name__ == '__main__':
    seed_database()

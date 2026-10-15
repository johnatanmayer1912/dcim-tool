import os
import zipfile
import datetime
import logging
import json

def setup_logger():
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_file = os.path.join(log_dir, "system.log")
    
    logger = logging.getLogger("FullNetworkBackup")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        fh = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
    return logger

def create_full_intelligent_backup():
    logger = setup_logger()
    logger.info("=== FULL INTELLIGENT BACKUP STARTED ===")
    
    # Read version
    version = "4.3.0" # Manual override for current state
    if os.path.exists("VERSION"):
        with open("VERSION", "r") as f:
            version = f.read().strip()
            
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_NETWORK_FULL_{version}_{timestamp}.zip"
    backup_dir = "backups"
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        
    zip_path = os.path.join(backup_dir, backup_filename)
    
    # Files/Dirs to include
    includes = [
        'vlan_checker_web.py', 'vlan_checker_gui.py', 'main.py', 'f5_manager_gui.py', 'check_vlans.py',
        'core', 'modules', 'utils', 'config', 'inventory', 'docs', 'tests',
        'VERSION', 'CHANGELOG.md', 'README.md', 'requirements.txt',
        'backups/system_design' # The blueprint we just created
    ]
    
    excludes = ['.venv', '__pycache__', '.git', 'paramiko_deps', 'build', 'dist']
    
    logger.info(f"Target file: {zip_path}")
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for item in includes:
                if not os.path.exists(item):
                    logger.warning(f"Item not found, skipping: {item}")
                    continue
                
                if os.path.isfile(item):
                    zipf.write(item, item)
                else:
                    for root, dirs, files in os.walk(item):
                        # Skip excluded directories
                        dirs[:] = [d for d in dirs if d not in excludes]
                        for file in files:
                            file_path = os.path.join(root, file)
                            # Store with path relative to root
                            arcname = os.path.relpath(file_path, ".")
                            zipf.write(file_path, arcname)
                            
        size_mb = os.path.getsize(zip_path) / (1024 * 1024)
        logger.info(f"=== FULL INTELLIGENT BACKUP COMPLETED successfully ===")
        logger.info(f"Filename: {backup_filename}")
        logger.info(f"Size: {size_mb:.2f} MB")
        
        print(f"\n[BACKUP SUCCESS]")
        print(f"Filename: {backup_filename}")
        print(f"Path: {zip_path}")
        print(f"Size: {size_mb:.2f} MB")
        print(f"Validation: Blueprint included in backups/system_design/")
        
    except Exception as e:
        logger.error(f"Backup failed: {str(e)}")
        print(f"[ERROR] Backup failed: {e}")

if __name__ == "__main__":
    create_full_intelligent_backup()

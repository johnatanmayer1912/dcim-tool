import os
import shutil
import datetime
import logging

def setup_logger():
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_file = os.path.join(log_dir, "system.log")
    
    logger = logging.getLogger("SystemBackup")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        fh = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
        # Also log to console
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
    return logger

def create_backup():
    logger = setup_logger()
    
    # Read current version
    version = "unknown"
    if os.path.exists("VERSION"):
        with open("VERSION", "r") as f:
            version = f.read().strip()
            
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    backup_filename = f"backup_{version}_{timestamp}"
    backup_dir = "backups"
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        
    backup_path = os.path.join(backup_dir, backup_filename)
    
    logger.info(f"Starting backup: {backup_filename}.zip")
    
    # We want to backup the whole directory but exclude the 'backups' directory, '__pycache__', '.venv', etc.
    # To use shutil.make_archive easily without recursive custom filters, we can just let it zip everything
    # and maybe filter out large folders later, but for a solid baseline, let's just zip the root, 
    # but excluding .venv is good to save space. We'll use a temporary folder or just zip the current dir
    # knowing that backups will contain backups if we aren't careful.
    # Actually, shutil.make_archive running from root zipping root will try to zip its own output.
    
    # Custom zip creation
    import zipfile
    
    zip_path = backup_path + ".zip"
    
    excludes = ['.venv', 'backups', '__pycache__', '.git', 'paramiko_deps']
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("."):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in excludes]
            
            for file in files:
                if file.endswith(".zip") and root == ".":
                    # Skip existing zip files in root folder to avoid duplicating previous manual backups
                    continue
                
                file_path = os.path.join(root, file)
                # Store relative to root
                arcname = os.path.relpath(file_path, ".")
                zipf.write(file_path, arcname)
                
    logger.info(f"Backup completed successfully: {zip_path}")
    print(f"Backup created: {zip_path}")

if __name__ == "__main__":
    create_backup()

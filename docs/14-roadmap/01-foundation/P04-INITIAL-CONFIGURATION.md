# P04: Initial Configuration

| Field | Value |
|-------|-------|
| **Prompt ID** | P04 |
| **Phase** | 01-foundation |
| **Dependency Level** | 3 (Depends on P01, P02, P03) |
| **Estimated Time** | 5 minutes |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-02 |

---

## Purpose

Create initial configuration files for Network Swiss Tool Pro. This includes requirements.txt, .gitignore, and basic configuration files.

---

## Prerequisites

- P01: Environment Setup completed
- P02: Dependency Installation completed
- P03: Project Structure completed
- Virtual environment activated

---

## Instructions

### Step 1: Create requirements.txt

```bash
cat > requirements.txt << 'EOF'
Flask==3.0.0
Flask-SocketIO==5.3.6
netmiko==4.3.0
paramiko==3.4.0
Jinja2==3.1.2
PyYAML==6.0.1
textfsm==1.1.3
requests==2.31.0
python-dotenv==1.0.0
gunicorn==21.2.0
eventlet==0.33.3
pyserial==3.5
ipaddress==1.0.23
pytest==7.4.3
pytest-cov==4.1.0
pytest-mock==3.12.0
pytest-asyncio==0.21.1
black==23.12.1
flake8==7.0.0
mypy==1.7.1
pyinstaller==6.3.0
pywin32==306
EOF
```

---

### Step 2: Create .gitignore

```bash
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
logs/
*.log

# Configuration
.env
.env.local
*.secret

# OS
.DS_Store
Thumbs.db

# Build
build/
dist/
*.exe
*.spec

# Temporary
*.tmp
*.bak
*.backup
EOF
```

---

### Step 3: Create .env.example

```bash
cat > .env.example << 'EOF'
# Application Configuration
FLASK_APP=vlan_checker_web.py
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here

# Server Configuration
HOST=0.0.0.0
PORT=5000

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/application.log

# Database
DATABASE_URL=sqlite:///app.db
EOF
```

---

### Step 4: Create README.md

```bash
cat > README.md << 'EOF'
# Network Swiss Tool Pro

Version: 7.0.10

## Overview

Network Swiss Tool Pro is a comprehensive network management application for device discovery, configuration management, and network analysis.

## Installation

### Prerequisites
- Python 3.11+
- pip

### Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run application:
```bash
python vlan_checker_web.py
```

## Documentation

See docs/ directory for comprehensive documentation.

## License

Proprietary
EOF
```

---

### Step 5: Create config.yaml

```bash
cat > config.yaml << 'EOF'
# Application Configuration
app:
  name: Network Swiss Tool Pro
  version: 7.0.10
  debug: false

# Server Configuration
server:
  host: 0.0.0.0
  port: 5000
  workers: 4

# Logging Configuration
logging:
  level: INFO
  file: logs/application.log
  max_bytes: 10485760
  backup_count: 5

# Plugin Configuration
plugins:
  directory: modules/plugins
  enabled:
    - network_discovery
    - standards_validator
    - stp_topology_visualizer
    - vpc_domain
    - vlan_audit_plugin
    - unused_trunk_pruner
    - critical_logs_plugin
    - device_time_plugin
    - environment_status_plugin
    - interface_errors_plugin
    - serial_number_plugin
    - config_templates
EOF
```

---

### Step 6: Verify Configuration

```bash
# Verify files created
ls -la
cat requirements.txt
cat .gitignore
cat .env.example
cat README.md
cat config.yaml
```

---

## Validation Checklist

- [ ] requirements.txt created
- [ ] .gitignore created
- [ ] .env.example created
- [ ] README.md created
- [ ] config.yaml created
- [ ] All files validated
- [ ] Environment ready for development

---

## Troubleshooting

### Issue: File creation fails

**Solution:**
- Check write permissions
- Check disk space
- Verify directory exists

### Issue: Configuration syntax errors

**Solution:**
- Validate YAML syntax
- Check for proper indentation
- Use YAML validator

---

## Next Steps

After completing this prompt, Phase 1 (Foundation) is complete. Proceed to Phase 2: Core Modules

---

## References

- CONFIGURATION_DOCUMENTATION.md: ../../02-codebase/CONFIGURATION_DOCUMENTATION.md
- BUILD_PROCESS.md: ../../10-rebuild/BUILD_PROCESS.md

# Onboarding Guide - Network Swiss Tool Pro

> **ARCHIVE / LEGACY** — References v5/v6 folder layout (`01_ARCHITECTURE/`, etc.).  
> **Canonical onboarding (2026+):** [project-overview.md](../00-overview/project-overview.md) · [walkthrough.md](../00-overview/walkthrough.md) · [docs/README.md](../README.md)

# Onboarding Guide - Network Swiss Tool Pro (legacy)

**Welcome to the team!** This guide will get you productive within 2 hours.

---

## 🎯 Day 1: First 2 Hours

### Hour 1: Understanding the System (30 min)

1. **Read the system overview**
   - File: `../01_ARCHITECTURE/SYSTEM_OVERVIEW.md`
   - Key concepts: Modular architecture, adapter pattern, Flask web interface

2. **Understand the codebase structure**
   ```
   modules/
   ├── network_base.py      # Base connectivity (SSH/Telnet)
   ├── vlan_audit.py        # VLAN analysis
   ├── vlan_mgmt.py         # VLAN provisioning
   ├── mac_trace.py         # MAC address tracing
   ├── topology_mapper.py   # Network topology
   ├── adapters.py          # Platform adapters
   ├── interfaces.py        # Interface management
   ├── config_backup.py    # Configuration backup
   └── cli_manager.py      # CLI terminal (v5.0)
   
   modules/web/
   └── templates/           # Flask HTML templates
   
   utils/
   └── report_formatter.py  # Output formatting
   ```

3. **Review the tech stack**
   - Python 3.x with backward compatibility (3.14 ready)
   - Netmiko for SSH/Telnet connections
   - Flask + Flask-SocketIO for web interface
   - xterm.js for CLI terminal
   - PyInstaller for executable builds

### Hour 2: Hands-On (30 min)

1. **Run the application locally**
   ```bash
   # Setup
   pip install -r requirements.txt
   
   # Run web interface
   python vlan_checker_web.py
   
   # Or run CLI version
   python main.py
   ```

2. **Explore the UI**
   - Open http://localhost:5000
   - Try: VLAN Audit, MAC Trace, Topology Map
   - Use "Extract Documentation" button

### Remaining Time: Deep Dive (60 min)

Choose your focus area:
- **Network Engineer** → Focus on `02_FEATURES/VLAN_*/`
- **Frontend Developer** → Focus on `modules/web/templates/`
- **Backend Developer** → Focus on `01_ARCHITECTURE/CORE_MODULES.md`
- **QA Engineer** → Focus on `03_QA_TESTING/`

---

## 📚 Essential Reading List

### Must Read (Day 1)
1. [System Overview](../00-overview/project-overview.md)
2. [Architecture Diagram](../01-architecture/system-architecture.md)
3. [Walkthrough](../00-overview/walkthrough.md)

### Should Read (Week 1)
1. [VLAN Audit Plugin](../05-plugins/vlan_audit_plugin/README.md)
2. [MAC Trace How-To](mac-trace-howto.md)
3. [Troubleshooting Index](TS_ERROR_INDEX.md)
4. [QA Testing Overview](../09-qa/ST_MASTER_QA_SUITE.md)

### Reference (As Needed)
1. [API Documentation](../02-codebase/API_DOCUMENTATION.md)
2. [Module Architecture](../01-architecture/MODULE_ARCHITECTURE.md)
3. [Recovery Procedures](recovery/BUILD_PROCEDURES.md)
4. [Release History](../11-release-management/release-history.md)

---

## 🏗️ Understanding the Architecture

### Core Principle: Modular Design

Each feature is a **self-contained module** that:
- Inherits from `NetworkDevice` base class
- Implements platform-specific adapters
- Returns standardized output
- Has independent test coverage

### Data Flow

```
User Input → Web Interface → Backend Module → Device Connection → Output
                 ↓                    ↓               ↓
            Templates          Business Logic    Netmiko/SSH
            (Flask)            (Python)          (Network)
```

### Key Design Patterns

1. **Adapter Pattern** - Platform-specific command generation
2. **Strategy Pattern** - Different connection methods (SSH/Telnet)
3. **Factory Pattern** - Device type instantiation
4. **Observer Pattern** - WebSocket for CLI terminal

---

## 🔧 Development Environment Setup

### Prerequisites
- Python 3.9+ (3.14 compatible)
- Git
- Text editor/IDE (VS Code, PyCharm, etc.)

### Step-by-Step Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd NetworkSwissToolPro

# 2. Create virtual environment
python -m venv venv

# 3. Activate environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Verify installation
python -c "import netmiko; import flask; print('✓ Dependencies OK')"

# 6. Run tests
python -m py_compile modules/*.py

# 7. Start application
python vlan_checker_web.py
```

---

## 🧪 Your First Contribution

### Good First Issues

1. **Documentation fixes** - Typos, clarifications
2. **Device support** - Add new platform variant
3. **UI improvements** - Template enhancements
4. **Test coverage** - Add QA prompts for existing features

### Contribution Workflow

1. **Read** the documentation sync checklist
2. **Create** feature branch: `git checkout -b feature/your-feature`
3. **Code** your changes
4. **Update** relevant docs in `02_FEATURES/`
5. **Write** QA prompts in `03_QA_TESTING/`
6. **Test** using QA prompts
7. **Commit** with message: `docs: + feature: + tests:`
8. **Push** and create PR

---

## 🎓 Learning Paths

### Path 1: Network Automation Specialist
Focus: Understanding network device interaction

1. Study `modules/network_base.py` - Connection handling
2. Study `modules/adapters.py` - Platform-specific logic
3. Study `modules/vlan_audit.py` - Data collection
4. Practice: Add support for new device type

### Path 2: Full-Stack Developer
Focus: Web interface and integration

1. Study `vlan_checker_web.py` - Flask application
2. Study `modules/web/templates/*.html` - Frontend
3. Study `modules/cli_manager.py` - WebSocket handling
4. Practice: Add new UI feature

### Path 3: QA Engineer
Focus: Testing and quality assurance

1. Study `03_QA_TESTING/MASTER_QA_SUITE.md`
2. Study existing test prompts
3. Practice: Write comprehensive test for existing feature
4. Practice: Find and document bugs

### Path 4: DevOps/Release Engineer
Focus: Build and deployment

1. Study `05_RECOVERY/BUILD_PROCEDURES.md`
2. Study PyInstaller spec files
3. Study release process
4. Practice: Create build from scratch

---

## 🆘 Getting Help

### Internal Resources
1. **Documentation** → Check `04_TROUBLESHOOTING/`
2. **Code comments** → All modules have docstrings
3. **Examples** → `examples/` folder
4. **Tests** → `03_QA_TESTING/` for usage examples

### External Resources
- **Netmiko Docs** → https://github.com/ktbyers/netmiko
- **Flask Docs** → https://flask.palletsprojects.com/
- **Network Device CLI** → Vendor documentation

### Emergency Contacts
- **Technical Lead** → Architecture questions
- **QA Lead** → Testing questions
- **DevOps Lead** → Build/deployment issues

---

## ✅ Onboarding Checklist

### Day 1
- [ ] Read system overview
- [ ] Set up development environment
- [ ] Run application locally
- [ ] Explore all UI features
- [ ] Read one complete feature documentation

### Week 1
- [ ] Complete assigned learning path
- [ ] Make first documentation contribution
- [ ] Run full QA suite
- [ ] Attend team architecture review
- [ ] Shadow experienced developer

### Month 1
- [ ] Lead one feature development
- [ ] Write comprehensive QA prompts
- [ ] Contribute to troubleshooting docs
- [ ] Mentor next new team member

---

## 🎉 Welcome Aboard!

You're now part of maintaining one of the most comprehensive network automation tools. Remember:

- **Documentation is code** - Keep it updated
- **Test everything** - QA prompts are your safety net
- **Ask questions** - Better to ask than assume
- **Leave it better** - Always improve what you touch

**Next Steps:**
1. Complete the checklist above
2. Pick your learning path
3. Make your first contribution

**Questions?** Check the troubleshooting section or ask the team.

---

*Last updated: 2026-04-19*  
*Next review: 2026-05-19*

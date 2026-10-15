# P01: Environment Setup

| Field | Value |
|-------|-------|
| **Prompt ID** | P01 |
| **Phase** | 01-foundation |
| **Dependency Level** | 0 (No Dependencies) |
| **Estimated Time** | 5 minutes |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-02 |

---

## Purpose

Set up the Python development environment for Network Swiss Tool Pro. This includes installing Python 3.11+, creating a virtual environment, and verifying the environment is ready for development.

---

## Prerequisites

- Operating System: Windows 10/11, Linux, or macOS
- Administrative privileges (for system-wide Python installation)
- Internet connection (for downloading Python and packages)
- 10 GB free disk space

---

## Instructions

### Step 1: Install Python 3.11+

**Windows:**
1. Download Python 3.11 from https://www.python.org/downloads/
2. Run the installer
3. Check "Add Python to PATH"
4. Click "Install Now"
5. Verify installation: `python --version`

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

**macOS:**
```bash
brew install python@3.11
```

**Validation:**
```bash
python --version
# Expected output: Python 3.11.x
```

---

### Step 2: Create Project Directory

```bash
mkdir Net_mngmnt_tool
cd Net_mngmnt_tool
```

---

### Step 3: Create Virtual Environment

```bash
python -m venv venv
```

**Windows Activation:**
```bash
venv\Scripts\activate
```

**Linux/macOS Activation:**
```bash
source venv/bin/activate
```

**Validation:**
```bash
which python
# Expected output: Path to venv python
```

---

### Step 4: Upgrade pip

```bash
pip install --upgrade pip
```

**Validation:**
```bash
pip --version
# Expected output: pip 24.x.x
```

---

### Step 5: Verify Environment

```bash
python --version
pip --version
which python
```

**Expected Output:**
- Python 3.11.x
- pip 24.x.x
- Path points to virtual environment

---

## Validation Checklist

- [ ] Python 3.11+ installed
- [ ] Virtual environment created
- [ ] Virtual environment activated
- [ ] pip upgraded
- [ ] Environment verified
- [ ] Ready for dependency installation

---

## Troubleshooting

### Issue: Python not found in PATH

**Solution:**
- Windows: Re-run Python installer with "Add Python to PATH" checked
- Linux/macOS: Add Python to PATH in shell configuration

### Issue: Virtual environment creation fails

**Solution:**
- Ensure python-venv is installed
- Try: `sudo apt install python3.11-venv` (Linux)
- Try: `brew install python@3.11` (macOS)

### Issue: pip upgrade fails

**Solution:**
- Use: `python -m pip install --upgrade pip`
- Check internet connection
- Check firewall settings

---

## Next Steps

After completing this prompt, proceed to P02: Dependency Installation

---

## References

- Python Documentation: https://docs.python.org/3.11/
- Virtual Environment: https://docs.python.org/3.11/library/venv.html
- pip Documentation: https://pip.pypa.io/

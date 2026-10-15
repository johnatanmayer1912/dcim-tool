# P02: Dependency Installation

| Field | Value |
|-------|-------|
| **Prompt ID** | P02 |
| **Phase** | 01-foundation |
| **Dependency Level** | 1 (Depends on P01) |
| **Estimated Time** | 10 minutes |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-02 |

---

## Purpose

Install all required Python dependencies for Network Swiss Tool Pro. This includes Flask, Netmiko, Paramiko, and all other required packages.

---

## Prerequisites

- P01: Environment Setup completed
- Virtual environment activated
- pip upgraded to latest version

---

## Instructions

### Step 1: Install Core Dependencies

```bash
pip install Flask==3.0.0
pip install Flask-SocketIO==5.3.6
pip install netmiko==4.3.0
pip install paramiko==3.4.0
pip install Jinja2==3.1.2
pip install PyYAML==6.0.1
pip install textfsm==1.1.3
```

---

### Step 2: Install Additional Dependencies

```bash
pip install requests==2.31.0
pip install python-dotenv==1.0.0
pip install gunicorn==21.2.0
pip install eventlet==0.33.3
pip install pyserial==3.5
pip install ipaddress==1.0.23
```

---

### Step 3: Install Development Dependencies

```bash
pip install pytest==7.4.3
pip install pytest-cov==4.1.0
pip install pytest-mock==3.12.0
pip install pytest-asyncio==0.21.1
pip install black==23.12.1
pip install flake8==7.0.0
pip install mypy==1.7.1
```

---

### Step 4: Install Build Dependencies

```bash
pip install pyinstaller==6.3.0
pip install pywin32==306
```

---

### Step 5: Verify Installation

```bash
pip list
```

**Expected Output:**
- Flask 3.0.0
- Flask-SocketIO 5.3.6
- netmiko 4.3.0
- paramiko 3.4.0
- Jinja2 3.1.2
- PyYAML 6.0.1
- textfsm 1.1.3
- requests 2.31.0
- python-dotenv 1.0.0
- gunicorn 21.2.0
- eventlet 0.33.3
- pyserial 3.5
- ipaddress 1.0.23
- pytest 7.4.3
- pytest-cov 4.1.0
- pytest-mock 3.12.0
- pytest-asyncio 0.21.1
- black 23.12.1
- flake8 7.0.0
- mypy 1.7.1
- pyinstaller 6.3.0
- pywin32 306

---

## Validation Checklist

- [ ] All core dependencies installed
- [ ] All additional dependencies installed
- [ ] All development dependencies installed
- [ ] All build dependencies installed
- [ ] Package versions verified
- [ ] No dependency conflicts
- [ ] Ready for project structure creation

---

## Troubleshooting

### Issue: Package installation fails

**Solution:**
- Check internet connection
- Try: `pip install --upgrade pip`
- Try: `pip install --no-cache-dir <package>`
- Check for conflicting packages

### Issue: Version conflicts

**Solution:**
- Use: `pip install <package>==<version>` to force specific version
- Use: `pip install --upgrade <package>` to upgrade to latest
- Check for conflicting packages with: `pip check`

### Issue: Windows-specific packages fail

**Solution:**
- Ensure Visual C++ Build Tools installed
- Try: `pip install <package> --prefer-binary`
- Check system requirements

---

## Next Steps

After completing this prompt, proceed to P03: Project Structure

---

## References

- Flask Documentation: https://flask.palletsprojects.com/
- Netmiko Documentation: https://netmiko.readthedocs.io/
- Paramiko Documentation: https://www.paramiko.org/
- PyInstaller Documentation: https://pyinstaller.org/

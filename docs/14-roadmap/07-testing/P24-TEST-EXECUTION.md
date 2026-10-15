# P24: Test Execution

| Field | Value |
|-------|-------|
| **Prompt ID** | P24 |
| **Phase** | 07-testing |
| **Dependency Level** | 7 (Depends on P22-P23) |
| **Estimated Time** | 10 minutes |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-02 |

---

## Purpose

Reconstruct test execution procedures and CI/CD integration. This provides automated test execution, reporting, and CI/CD pipeline integration.

---

## Prerequisites

- Phase 7 (Unit Tests) completed
- Phase 7 (Integration Tests) completed
- pytest installed
- Python environment set up

---

## Instructions

### Step 1: Create run_tests.py

```python
"""
Test Execution Script

Run all tests and generate reports.
"""

import subprocess
import sys
import os
from datetime import datetime

def run_tests(test_type='all'):
    """
    Run tests
    
    Args:
        test_type: Type of tests to run (unit, integration, all)
    
    Returns:
        int: Exit code
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if test_type == 'unit':
        test_path = 'tests/modules/'
        coverage_path = f'coverage_unit_{timestamp}.html'
    elif test_type == 'integration':
        test_path = 'tests/integration/'
        coverage_path = f'coverage_integration_{timestamp}.html'
    else:
        test_path = 'tests/'
        coverage_path = f'coverage_all_{timestamp}.html'
    
    # Run pytest with coverage
    cmd = [
        'pytest',
        test_path,
        '--verbose',
        '--tb=short',
        f'--cov=modules',
        f'--cov-report=html:{coverage_path}',
        '--cov-report=term-missing',
        '--junitxml=test_results.xml'
    ]
    
    print(f"Running tests: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    return result.returncode

if __name__ == '__main__':
    test_type = sys.argv[1] if len(sys.argv) > 1 else 'all'
    exit_code = run_tests(test_type)
    sys.exit(exit_code)
```

---

### Step 2: Create .github/workflows/test.yml

```bash
mkdir -p .github/workflows
```

```yaml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-mock
    
    - name: Run unit tests
      run: |
        python run_tests.py unit
    
    - name: Run integration tests
      run: |
        python run_tests.py integration
    
    - name: Upload coverage reports
      uses: actions/upload-artifact@v3
      with:
        name: coverage-reports
        path: coverage_*.html
```

---

### Step 3: Create test_report_generator.py

```python
"""
Test Report Generator

Generate test reports from test results.
"""

import xml.etree.ElementTree as ET
from datetime import datetime
import json

def generate_test_report(junit_xml_path='test_results.xml'):
    """
    Generate test report from JUnit XML
    
    Args:
        junit_xml_path: Path to JUnit XML file
    
    Returns:
        dict: Test report
    """
    tree = ET.parse(junit_xml_path)
    root = tree.getroot()
    
    total_tests = 0
    failures = 0
    errors = 0
    skipped = 0
    duration = 0
    
    test_cases = []
    
    for test_suite in root.findall('testsuite'):
        total_tests += int(test_suite.get('tests', 0))
        failures += int(test_suite.get('failures', 0))
        errors += int(test_suite.get('errors', 0))
        skipped += int(test_suite.get('skipped', 0))
        duration += float(test_suite.get('time', 0))
        
        for test_case in test_suite.findall('testcase'):
            case_info = {
                'name': test_case.get('name'),
                'classname': test_case.get('classname'),
                'time': test_case.get('time'),
                'status': 'passed'
            }
            
            if test_case.find('failure') is not None:
                case_info['status'] = 'failed'
                case_info['failure'] = test_case.find('failure').text
            
            if test_case.find('error') is not None:
                case_info['status'] = 'error'
                case_info['error'] = test_case.find('error').text
            
            test_cases.append(case_info)
    
    report = {
        'timestamp': datetime.utcnow().isoformat(),
        'summary': {
            'total': total_tests,
            'passed': total_tests - failures - errors - skipped,
            'failed': failures,
            'errors': errors,
            'skipped': skipped,
            'duration': duration
        },
        'test_cases': test_cases
    }
    
    return report

def save_report(report, output_path='test_report.json'):
    """Save test report to JSON file"""
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

if __name__ == '__main__':
    report = generate_test_report()
    save_report(report)
    print(f"Test report generated: test_report.json")
    print(f"Total tests: {report['summary']['total']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
```

---

### Step 4: Validate Test Execution

```bash
# Run all tests
python run_tests.py

# Run unit tests only
python run_tests.py unit

# Run integration tests only
python run_tests.py integration

# Generate test report
python test_report_generator.py
```

---

## Validation Checklist

- [ ] run_tests.py created
- [ ] Test execution functional
- [ ] Coverage reporting functional
- [ ] .github/workflows/test.yml created
- [ ] CI/CD integration functional
- [ ] test_report_generator.py created
- [ ] Test report generation functional
- [ ] All tests passing
- [ ] Coverage >= 80%
- [ ] Testing phase complete
- [ ] Ready for deployment reconstruction

---

## Troubleshooting

### Issue: Tests fail to run

**Solution:**
- Verify pytest installation
- Check test file paths
- Validate test structure

### Issue: CI/CD workflow fails

**Solution:**
- Verify GitHub Actions configuration
- Check Python version
- Validate dependencies

---

## Next Steps

After completing this prompt, Phase 7 (Testing) is complete. Proceed to Phase 8: Deployment

---

## References

- CODE_INVENTORY.md: ../../02-codebase/CODE_INVENTORY.md
- AUTOMATED_TESTING_DOCUMENTATION.md: ../../02-codebase/AUTOMATED_TESTING_DOCUMENTATION.md
- COMPREHENSIVE_TESTING_COVERAGE.md: ../../02-codebase/COMPREHENSIVE_TESTING_COVERAGE.md

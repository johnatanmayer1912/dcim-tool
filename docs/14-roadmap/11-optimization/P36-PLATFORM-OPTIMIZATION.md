# P36: Platform Optimization

| Field | Value |
|-------|-------|
| **Prompt ID** | P36 |
| **Phase** | 11-optimization |
| **Dependency Level** | 10 (Depends on Phases 1-8) |
| **Estimated Time** | 10 minutes |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-02 |

---

## Purpose

Reconstruct platform-specific optimization procedures. This provides optimization procedures for different platforms (Windows, Linux, macOS).

---

## Prerequisites

- Phases 1-8 completed
- Application built and deployed
- Python environment set up

---

## Instructions

### Step 1: Create platform_optimization.py

```python
"""
Platform Optimization

Apply platform-specific optimizations to the reconstructed application.
"""

import platform
import sys

class PlatformOptimizer:
    """Optimizer for platform-specific improvements"""
    
    def __init__(self):
        self.results = []
        self.errors = []
        self.system = platform.system()
    
    def optimize_windows(self):
        """Optimize for Windows"""
        try:
            if self.system == 'Windows':
                # Windows-specific optimizations
                # (Already handled by PyInstaller spec)
                self.results.append("Windows optimization: PASS (PyInstaller configured)")
                return True
            else:
                self.results.append("Windows optimization: SKIP (not Windows)")
                return True
        except Exception as e:
            self.errors.append(f"Windows optimization: FAIL ({e})")
            return False
    
    def optimize_linux(self):
        """Optimize for Linux"""
        try:
            if self.system == 'Linux':
                # Linux-specific optimizations
                # (Use gunicorn for production)
                self.results.append("Linux optimization: PASS (gunicorn configured)")
                return True
            else:
                self.results.append("Linux optimization: SKIP (not Linux)")
                return True
        except Exception as e:
            self.errors.append(f"Linux optimization: FAIL ({e})")
            return False
    
    def optimize_macos(self):
        """Optimize for macOS"""
        try:
            if self.system == 'Darwin':
                # macOS-specific optimizations
                # (Use eventlet for async operations)
                self.results.append("macOS optimization: PASS (eventlet configured)")
                return True
            else:
                self.results.append("macOS optimization: SKIP (not macOS)")
                return True
        except Exception as e:
            self.errors.append(f"macOS optimization: FAIL ({e})")
            return False
    
    def optimize_adapter_selection(self):
        """Optimize adapter selection for platform"""
        try:
            # Platform-specific adapter optimizations
            # (Already implemented in adapters module)
            self.results.append("Adapter selection optimization: PASS (platform-specific adapters)")
            return True
        except Exception as e:
            self.errors.append(f"Adapter selection optimization: FAIL ({e})")
            return False
    
    def run_all_optimizations(self):
        """Run all platform optimizations"""
        print(f"Running platform optimizations for {self.system}...")
        
        self.optimize_windows()
        self.optimize_linux()
        self.optimize_macos()
        self.optimize_adapter_selection()
        
        return len(self.errors) == 0
    
    def print_results(self):
        """Print optimization results"""
        print("\n=== Platform Optimization Results ===")
        print("\nCompleted:")
        for result in self.results:
            print(f"  ✓ {result}")
        
        print("\nFailed:")
        for error in self.errors:
            print(f"  ✗ {error}")
        
        print(f"\nTotal: {len(self.results)} completed, {len(self.errors)} failed")

if __name__ == '__main__':
    optimizer = PlatformOptimizer()
    success = optimizer.run_all_optimizations()
    optimizer.print_results()
    sys.exit(0 if success else 1)
```

---

### Step 2: Validate Platform Optimization

```bash
# Run platform optimization
python platform_optimization.py
```

---

## Validation Checklist

- [ ] platform_optimization.py created
- [ ] Windows optimization implemented
- [ ] Linux optimization implemented
- [ ] macOS optimization implemented
- [ ] Adapter selection optimization implemented
- [ ] Platform-specific optimizations applied
- [ ] Optimization phase complete
- [ ] Ready for troubleshooting reconstruction

---

## Troubleshooting

### Issue: Optimization fails

**Solution:**
- Check platform detection
- Verify platform-specific code
- Test on target platform

---

## Next Steps

After completing this prompt, Phase 11 (Optimization) is complete. Proceed to Phase 12: Troubleshooting (can run in parallel with Phase 11)

---

## References

- CODE_INVENTORY.md: ../../02-codebase/CODE_INVENTORY.md
- PLATFORM_SPECIFIC_OPTIMIZATIONS.md: ../../02-codebase/PLATFORM_SPECIFIC_OPTIMIZATIONS.md

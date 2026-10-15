"""Runs scripts/offline_verification.py — checkout ingredients only."""
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestOfflineVerificationScript(unittest.TestCase):
    def test_script_exits_zero(self):
        script = os.path.join(ROOT, 'scripts', 'offline_verification.py')
        r = subprocess.run(
            [sys.executable, script],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)
        self.assertIn('OFFLINE INGREDIENTS OK', r.stdout)
        self.assertIn('not a signed EXE', r.stdout)


if __name__ == '__main__':
    unittest.main()

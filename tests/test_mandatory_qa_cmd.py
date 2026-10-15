"""mandatory_release_qa uses the current interpreter when the manifest says python."""
import importlib.util
import sys
from pathlib import Path


def _mod():
    path = Path(__file__).resolve().parents[1] / 'scripts' / 'mandatory_release_qa.py'
    spec = importlib.util.spec_from_file_location('mandatory_release_qa', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_normalize_command_rewrites_python_token():
    normalize_command = _mod().normalize_command
    assert normalize_command(['python', '_prebuild.py'])[0] == sys.executable
    assert normalize_command(['python3', '-m', 'pytest'])[0] == sys.executable
    assert normalize_command(['pytest', '-q'])[0] == 'pytest'

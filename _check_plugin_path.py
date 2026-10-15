"""Test the exact path resolution that standards_validator.py uses."""
import sys, os
sys.path.insert(0, '.')

# Simulate what the plugin does
policy_file = 'policies/standards.yaml'

plugin_dir = os.path.dirname(os.path.abspath('modules/plugins/standards_validator.py'))
modules_dir = os.path.dirname(plugin_dir)
base = os.path.dirname(modules_dir)

print(f"plugin_dir: {plugin_dir}")
print(f"modules_dir: {modules_dir}")
print(f"base: {base}")
print(f"CWD: {os.getcwd()}")

possible_paths = [
    os.path.join(base, policy_file),
    os.path.join(os.getcwd(), policy_file),
    policy_file,
]

for i, path in enumerate(possible_paths):
    exists = os.path.exists(path)
    print(f"Try {i+1}: {path} -> {'EXISTS' if exists else 'NOT FOUND'}")

# Now test via the actual plugin
from modules.plugins.standards_validator import _load_policies
policies = _load_policies('policies/standards.yaml', 'all', '')
print(f"\nPolicies loaded via plugin: {len(policies)}")
if len(policies) <= 5:
    print("WARNING: Only built-in policies loaded!")
    print("IDs:", [p.get('id') for p in policies])
else:
    print(f"OK: {len(policies)} policies from YAML")
    cats = sorted(set(p.get('category','?') for p in policies))
    print(f"Categories: {cats}")

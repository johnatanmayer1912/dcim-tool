#!/usr/bin/env python
"""Test script to verify plugin discovery and functionality."""

from modules.plugin_registry import get_registry

print('='*60)
print('TESTING PLUGIN DISCOVERY - v6.0.0-BETA')
print('='*60)

registry = get_registry()
registry.reload()

plugins = registry.get_all_metadata()
errors = registry.get_errors()

print(f'\nDiscovered {len(plugins)} plugins:\n')

for i, p in enumerate(plugins, 1):
    cat = p.get('category', 'Unknown')
    icons = {
        'Template': '[T]',
        'Audit': '[A]', 
        'Discovery': '[D]',
        'Management': '[M]'
    }
    icon = icons.get(cat, '[P]')
    
    print(f"{i}. {icon} [{cat:12}] {p['display_name']:<30} (v{p['version']})")
    print(f"   ID: {p['plugin_id']}")
    params = list(p.get('required_params', {}).keys())
    if params:
        print(f"   Parameters: {params}")
    print()

if errors:
    print('[WARNING] ERRORS:')
    for e in errors:
        print(f"  - {e['file']}: {e['error']}")
else:
    print('[SUCCESS] All plugins loaded successfully!')

print('='*60)
print('SUGGESTED TESTING WORKFLOW:')
print('='*60)
print('1. Start web server: python vlan_checker_web.py')
print('2. Open browser to http://127.0.0.1:5000')
print('3. Click "Plugin Tools" tab')
print('4. Click "Reload Registry" to see all 7 plugins')
print('5. Test each plugin:')
print('   - Click plugin name')
print('   - Fill required parameters')
print('   - Click "Execute Plugin"')
print('6. Test upload: Copy one plugin to scratch/, upload via UI')
print('7. Test rollback: Check backups/plugins/ for versions')
print('='*60)

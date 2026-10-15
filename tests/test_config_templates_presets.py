"""Config template presets — v6.9.28."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.plugins.config_templates import (
    get_template_presets,
    render_template_string,
    extract_template_variables,
)


class TestTemplatePresets(unittest.TestCase):
    def test_presets_catalog(self):
        presets = get_template_presets()
        ids = {p['id'] for p in presets}
        self.assertIn('nxos_trunk_vpc', ids)
        self.assertGreaterEqual(len(presets), 5)

    def test_nxos_trunk_renders(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(root, 'templates', 'cisco_nxos_trunk.j2')
        with open(path, encoding='utf-8') as f:
            content = f.read()
        out = render_template_string(content, {
            'hostname': 'sw1',
            'interface': 'Eth1/10',
            'description': 'TRUNK',
            'allowed_vlans': '10,20',
            'native_vlan': '1',
        })
        self.assertIn('switchport mode trunk', out)
        self.assertIn('Eth1/10', out)


if __name__ == '__main__':
    unittest.main()

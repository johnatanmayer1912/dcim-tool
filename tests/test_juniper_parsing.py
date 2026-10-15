
import re
import unittest

class TestJuniperParsing(unittest.TestCase):
    def test_vlan_parsing_legacy(self):
        output = """
VLAN Name       Tag  Interfaces
default         1    ge-0/0/0.0*
sales           10   ge-0/0/1.0
voice           20   ge-0/0/2.0
"""
        results = []
        lines = output.splitlines()
        # Original Logic Logic (mocked)
        junos_pattern = re.compile(r'^([\w-]+)\s+(\d+)\s+')
        for line in lines:
            match = junos_pattern.search(line.strip())
            if match:
                v_name, v_id = match.groups()
                results.append((v_id, v_name))
        
        # Expectation: Finds default(1), sales(10), voice(20)
        self.assertIn(('1', 'default'), results)
        self.assertIn(('10', 'sales'), results)

    def test_vlan_parsing_els(self):
        output = """
Routing instance        VLAN name             Tag          Interfaces
default-switch          default               1            ae0.0*
default-switch          management            100          ae0.0*
"""
        results = []
        lines = output.splitlines()
        # Original Logic
        junos_pattern = re.compile(r'^([\w-]+)\s+(\d+)\s+')
        for line in lines:
            match = junos_pattern.search(line.strip())
            if match:
                v_name, v_id = match.groups()
                results.append((v_id, v_name))
        
        # Expectation: Fails because "default-switch" matches name, but "default" (next word) is not digits
        # This confirms current logic is broken for ELS
        # results will likely be empty or garbage
        print(f"ELS Original Results: {results}")
        self.assertEqual(len(results), 0) 

    def test_proposed_vlan_regex(self):
        output_els = """
Routing instance        VLAN name             Tag          Interfaces
default-switch          default               1            ae0.0*
default-switch          mgmt                  99           ge-0/0/0.0
"""
        output_legacy = """
VLAN Name       Tag  Interfaces
default         1    ge-0/0/0.0*
data            10   ge-0/0/1.0
"""
        
        # Proposed Logic
        parsed_els = self.parse_juniper_output(output_els)
        parsed_legacy = self.parse_juniper_output(output_legacy)

        print(f"Proposed ELS: {parsed_els}")
        print(f"Proposed Legacy: {parsed_legacy}")

        self.assertTrue(any(v[0] == '1' and v[1] == 'default' for v in parsed_els))
        self.assertTrue(any(v[0] == '99' and v[1] == 'mgmt' for v in parsed_els))
        
        self.assertTrue(any(v[0] == '1' and v[1] == 'default' for v in parsed_legacy))
        self.assertTrue(any(v[0] == '10' and v[1] == 'data' for v in parsed_legacy))

    def parse_juniper_output(self, output):
        results = []
        lines = output.splitlines()
        
        # Pattern A: Name Tag ... (Legacy)
        # Pattern B: ... Name Tag ... (ELS) or just flexible
        
        # Try finding Tag column
        # Better approach: Regex that handles an optional prefix column
        # ELS: \S+ \s+ (name) \s+ (id) \s+
        # Legacy: (name) \s+ (id) \s+
        
        # Combined Regex:
        # Check for ELS first? 
        # Or use a generic pattern?
        
        # Regex for 'Tag' usually being digits.
        # Line usually has "Name" and "Tag"
        
        els_pattern = re.compile(r'^\S+\s+([\w-]+)\s+(\d+)\s+') # RoutingInstance Name Tag
        legacy_pattern = re.compile(r'^([\w-]+)\s+(\d+)\s+')    # Name Tag
        
        for line in lines:
            line = line.strip()
            if not line or "VLAN name" in line or "Name" in line:
                continue
            
            # Try ELS first (3 columns start)
            match = els_pattern.search(line)
            if match:
                results.append((match.group(2), match.group(1))) # ID, Name
                continue
                
            # Try Legacy
            match = legacy_pattern.search(line)
            if match:
                results.append((match.group(2), match.group(1))) # ID, Name
                
        return results

if __name__ == '__main__':
    unittest.main()

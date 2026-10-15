"""
tests/routing_analyzer/demo_data_generator.py
-----------------------------------------
Generate demo data for HTML map visualization.
Creates realistic multi-vendor network topology data.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from modules.routing_analyzer.normalizer import RoutingNormalizer
from modules.routing_analyzer.graph_builder import L3TopologyGraphBuilder, SubnetAnalyzer, GatewayDetector
import json
from datetime import datetime


class DemoDataGenerator:
    """Generate realistic demo data for network topology visualization"""
    
    def __init__(self):
        self.normalizer = RoutingNormalizer()
        self.graph_builder = L3TopologyGraphBuilder()
        self.subnet_analyzer = SubnetAnalyzer()
        self.gateway_detector = GatewayDetector()
    
    def generate_enterprise_network(self) -> dict:
        """Generate a realistic enterprise network topology"""
        all_routes = []
        
        # Core routers
        core_routes = self._generate_core_router('core-router-01', 'cisco_ios')
        all_routes.extend(core_routes)
        
        core_routes = self._generate_core_router('core-router-02', 'cisco_ios')
        all_routes.extend(core_routes)
        
        # Distribution switches
        dist_routes = self._generate_distribution_switch('dist-switch-01', 'cisco_nxos')
        all_routes.extend(dist_routes)
        
        dist_routes = self._generate_distribution_switch('dist-switch-02', 'cisco_nxos')
        all_routes.extend(dist_routes)
        
        # Access switches
        access_routes = self._generate_access_switch('access-switch-01', 'arista_eos')
        all_routes.extend(access_routes)
        
        access_routes = self._generate_access_switch('access-switch-02', 'arista_eos')
        all_routes.extend(access_routes)
        
        # Edge router
        edge_routes = self._generate_edge_router('edge-router-01', 'juniper_junos')
        all_routes.extend(edge_routes)
        
        # Data center switches
        dc_routes = self._generate_datacenter_switch('dc-switch-01', 'cisco_nxos')
        all_routes.extend(dc_routes)
        
        # Normalize and build topology
        normalized = self.normalizer.normalize_routing_table(all_routes, 'demo-network')
        topology = self.graph_builder.build_topology(normalized)
        subnet_analysis = self.subnet_analyzer.analyze_subnets(normalized)
        gateway_analysis = self.gateway_detector.detect_gateways(normalized)
        
        return {
            'network_name': 'Enterprise Demo Network',
            'generated_at': datetime.now().isoformat(),
            'topology': {
                'nodes': topology['nodes'],
                'edges': topology['edges'],
                'subnets': topology['subnets'],
                'gateways': topology['gateways'],
                'protocols': topology['protocols'],
                'analysis': topology['analysis']
            },
            'subnet_analysis': subnet_analysis,
            'gateway_analysis': gateway_analysis,
            'devices': self._get_device_info(all_routes)
        }
    
    def _generate_core_router(self, device_id: str, vendor: str) -> list:
        """Generate core router routing table"""
        routes = []
        
        # Connected networks
        for i in range(3):
            routes.append({
                'network': f'10.0.{i}.0/24',
                'protocol': 'C',
                'metric': '0',
                'interface': f'GigabitEthernet1/0/{i+1}',
                'next_hop': '0.0.0.0',
                'device_id': device_id
            })
        
        # OSPF routes
        for i in range(10, 20):
            routes.append({
                'network': f'192.168.{i}.0/24',
                'protocol': 'O',
                'metric': '[110/2]',
                'next_hop': f'10.0.0.{i-9}',
                'interface': 'GigabitEthernet1/0/1',
                'device_id': device_id
            })
        
        # BGP routes
        for i in range(20, 25):
            routes.append({
                'network': f'203.0.113.{i}.0/24',
                'protocol': 'B',
                'metric': '[20/0]',
                'next_hop': '198.51.100.1',
                'interface': 'GigabitEthernet1/0/10',
                'device_id': device_id
            })
        
        # Default route
        routes.append({
            'network': '0.0.0.0/0',
            'protocol': 'S',
            'metric': '[1/0]',
            'next_hop': '10.0.0.254',
            'interface': 'GigabitEthernet1/0/10',
            'device_id': device_id
        })
        
        return routes
    
    def _generate_distribution_switch(self, device_id: str, vendor: str) -> list:
        """Generate distribution switch routing table"""
        routes = []
        
        # Connected VLANs
        for i in range(10, 20):
            routes.append({
                'network': f'10.10.{i}.0/24',
                'protocol': 'C',
                'metric': '0',
                'interface': f'Vlan{i}',
                'next_hop': '0.0.0.0',
                'device_id': device_id
            })
        
        # Static routes to access switches
        for i in range(5):
            routes.append({
                'network': f'10.20.{i}.0/24',
                'protocol': 'S',
                'metric': '[1/0]',
                'next_hop': f'10.10.{i+10}.1',
                'interface': 'Port-channel1',
                'device_id': device_id
            })
        
        return routes
    
    def _generate_access_switch(self, device_id: str, vendor: str) -> list:
        """Generate access switch routing table"""
        routes = []
        
        # Connected user VLANs
        for i in range(5):
            routes.append({
                'network': f'10.20.{i}.0/24',
                'protocol': 'C',
                'metric': '0',
                'interface': f'Vlan{100+i}',
                'next_hop': '0.0.0.0',
                'device_id': device_id
            })
        
        # Default route to distribution
        routes.append({
            'network': '0.0.0.0/0',
            'protocol': 'S',
            'metric': '[1/0]',
            'next_hop': '10.20.0.1',
            'interface': 'Port-channel1',
            'device_id': device_id
        })
        
        return routes
    
    def _generate_edge_router(self, device_id: str, vendor: str) -> list:
        """Generate edge router routing table"""
        routes = []
        
        # Connected networks
        routes.append({
            'network': '10.255.0.0/24',
            'protocol': 'Direct',
            'metric': '0',
            'interface': 'ge-0/0/0',
            'next_hop': '0.0.0.0',
            'device_id': device_id
        })
        
        # BGP routes to internet
        for i in range(10):
            routes.append({
                'network': f'198.51.100.{i}.0/24',
                'protocol': 'BGP',
                'metric': '170',
                'next_hop': f'203.0.113.{i+1}',
                'interface': 'ge-0/0/1',
                'device_id': device_id
            })
        
        # Static routes to internal network
        routes.append({
            'network': '10.0.0.0/8',
            'protocol': 'Static',
            'metric': '5',
            'next_hop': '10.255.0.1',
            'interface': 'ge-0/0/0',
            'device_id': device_id
        })
        
        return routes
    
    def _generate_datacenter_switch(self, device_id: str, vendor: str) -> list:
        """Generate data center switch routing table"""
        routes = []
        
        # Connected server VLANs
        for i in range(100, 110):
            routes.append({
                'network': f'10.100.{i}.0/24',
                'protocol': 'C',
                'metric': '0',
                'interface': f'Vlan{i}',
                'next_hop': '0.0.0.0',
                'device_id': device_id
            })
        
        # OSPF routes to other DC switches
        for i in range(5):
            routes.append({
                'network': f'10.110.{i}.0/24',
                'protocol': 'OSPF',
                'metric': '[110/2]',
                'next_hop': f'10.100.254.{i+1}',
                'interface': 'Port-channel10',
                'device_id': device_id
            })
        
        return routes
    
    def _get_device_info(self, routes: list) -> dict:
        """Extract device information from routes"""
        devices = {}
        for route in routes:
            device_id = route.get('device_id', 'unknown')
            if device_id not in devices:
                devices[device_id] = {
                    'name': device_id,
                    'route_count': 0,
                    'protocols': set(),
                    'interfaces': set()
                }
            devices[device_id]['route_count'] += 1
            devices[device_id]['protocols'].add(route.get('protocol', 'Unknown'))
            devices[device_id]['interfaces'].add(route.get('interface', 'Unknown'))
        
        # Convert sets to lists for JSON serialization
        for device_id, info in devices.items():
            info['protocols'] = list(info['protocols'])
            info['interfaces'] = list(info['interfaces'])
        
        return devices
    
    def generate_small_network(self) -> dict:
        """Generate a small office network topology"""
        all_routes = []
        
        # Single router
        router_routes = [
            {
                'network': '192.168.1.0/24',
                'protocol': 'C',
                'metric': '0',
                'interface': 'GigabitEthernet0/0',
                'next_hop': '0.0.0.0',
                'device_id': 'office-router'
            },
            {
                'network': '0.0.0.0/0',
                'protocol': 'S',
                'metric': '[1/0]',
                'next_hop': '192.168.1.1',
                'interface': 'GigabitEthernet0/1',
                'device_id': 'office-router'
            }
        ]
        all_routes.extend(router_routes)
        
        # Switch
        switch_routes = [
            {
                'network': '192.168.1.0/24',
                'protocol': 'C',
                'metric': '0',
                'interface': 'Vlan1',
                'next_hop': '0.0.0.0',
                'device_id': 'office-switch'
            }
        ]
        all_routes.extend(switch_routes)
        
        normalized = self.normalizer.normalize_routing_table(all_routes, 'small-office')
        topology = self.graph_builder.build_topology(normalized)
        
        return {
            'network_name': 'Small Office Network',
            'generated_at': datetime.now().isoformat(),
            'topology': {
                'nodes': topology['nodes'],
                'edges': topology['edges'],
                'subnets': topology['subnets'],
                'gateways': topology['gateways'],
                'protocols': topology['protocols'],
                'analysis': topology['analysis']
            },
            'devices': self._get_device_info(all_routes)
        }
    
    def generate_datacenter_network(self) -> dict:
        """Generate a data center network topology"""
        all_routes = []
        
        # Spine switches
        for i in range(2):
            spine_routes = [
                {
                    'network': f'10.0.{i}.0/24',
                    'protocol': 'C',
                    'metric': '0',
                    'interface': f'Ethernet1/1',
                    'next_hop': '0.0.0.0',
                    'device_id': f'spine-{i+1}'
                }
            ]
            all_routes.extend(spine_routes)
        
        # Leaf switches
        for i in range(4):
            leaf_routes = []
            for j in range(10):
                leaf_routes.append({
                    'network': f'10.{i+10}.{j}.0/24',
                    'protocol': 'C',
                    'metric': '0',
                    'interface': f'Vlan{j+1}',
                    'next_hop': '0.0.0.0',
                    'device_id': f'leaf-{i+1}'
                })
            
            # Routes to spine
            leaf_routes.append({
                'network': '0.0.0.0/0',
                'protocol': 'OSPF',
                'metric': '[110/2]',
                'next_hop': f'10.0.{i%2}.1',
                'interface': 'Ethernet1/1',
                'device_id': f'leaf-{i+1}'
            })
            
            all_routes.extend(leaf_routes)
        
        normalized = self.normalizer.normalize_routing_table(all_routes, 'datacenter')
        topology = self.graph_builder.build_topology(normalized)
        
        return {
            'network_name': 'Data Center Fabric',
            'generated_at': datetime.now().isoformat(),
            'topology': {
                'nodes': topology['nodes'],
                'edges': topology['edges'],
                'subnets': topology['subnets'],
                'gateways': topology['gateways'],
                'protocols': topology['protocols'],
                'analysis': topology['analysis']
            },
            'devices': self._get_device_info(all_routes)
        }


def generate_demo_data():
    """Generate all demo data and save to files"""
    generator = DemoDataGenerator()
    
    # Generate different network topologies
    enterprise_data = generator.generate_enterprise_network()
    small_office_data = generator.generate_small_network()
    datacenter_data = generator.generate_datacenter_network()
    
    # Save to JSON files
    demo_dir = 'tests/routing_analyzer/demo_data'
    import os
    os.makedirs(demo_dir, exist_ok=True)
    
    with open(f'{demo_dir}/enterprise_network.json', 'w') as f:
        json.dump(enterprise_data, f, indent=2)
    
    with open(f'{demo_dir}/small_office.json', 'w') as f:
        json.dump(small_office_data, f, indent=2)
    
    with open(f'{demo_dir}/datacenter_network.json', 'w') as f:
        json.dump(datacenter_data, f, indent=2)
    
    print(f"Demo data generated in {demo_dir}/")
    print(f"- enterprise_network.json")
    print(f"- small_office.json")
    print(f"- datacenter_network.json")
    
    return enterprise_data, small_office_data, datacenter_data


if __name__ == '__main__':
    generate_demo_data()

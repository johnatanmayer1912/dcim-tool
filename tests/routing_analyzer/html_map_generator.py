"""
tests/routing_analyzer/html_map_generator.py
------------------------------------------
Generate HTML topology maps from demo data.
Creates interactive network topology visualizations.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import json
from pathlib import Path
from datetime import datetime


class HTMLMapGenerator:
    """Generate HTML topology maps from routing analysis data"""
    
    def __init__(self):
        self.template_dir = Path(__file__).parent / 'demo_data'
        self.output_dir = Path(__file__).parent / 'html_maps'
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_html_map(self, data: dict, output_filename: str):
        """Generate HTML map from routing analysis data"""
        html_content = self._build_html_template(data)
        
        output_path = self.output_dir / output_filename
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        print(f"Generated HTML map: {output_path}")
        return output_path
    
    def _build_html_template(self, data: dict) -> str:
        """Build HTML template with embedded data and visualization"""
        network_name = data.get('network_name', 'Network Topology')
        generated_at = data.get('generated_at', datetime.now().isoformat())
        topology = data.get('topology', {})
        subnet_analysis = data.get('subnet_analysis', {})
        gateway_analysis = data.get('gateway_analysis', {})
        devices = data.get('devices', {})
        
        nodes = topology.get('nodes', [])
        edges = topology.get('edges', [])
        analysis = topology.get('analysis', {})
        
        # Build node data for Cytoscape
        nodes_json = json.dumps(nodes)
        edges_json = json.dumps(edges)
        subnet_analysis_json = json.dumps(subnet_analysis)
        gateway_analysis_json = json.dumps(gateway_analysis)
        devices_json = json.dumps(devices)
        analysis_json = json.dumps(analysis)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{network_name} - Network Topology Map</title>
    <script src="https://cdn.jsdelivr.net/npm/cytoscape@3.26.0/dist/cytoscape.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #007bff;
            padding-bottom: 20px;
        }}
        .header h1 {{
            color: #333;
            margin: 0;
        }}
        .header p {{
            color: #666;
            margin: 5px 0 0 0;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-card h3 {{
            margin: 0 0 10px 0;
            font-size: 14px;
            opacity: 0.9;
        }}
        .stat-card .value {{
            font-size: 32px;
            font-weight: bold;
        }}
        #cy {{
            width: 100%;
            height: 600px;
            border: 2px solid #ddd;
            border-radius: 8px;
            margin-bottom: 30px;
            background-color: #fafafa;
        }}
        .info-panel {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }}
        .info-card {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }}
        .info-card h3 {{
            margin-top: 0;
            color: #333;
        }}
        .info-card ul {{
            list-style: none;
            padding: 0;
        }}
        .info-card li {{
            padding: 8px 0;
            border-bottom: 1px solid #dee2e6;
        }}
        .info-card li:last-child {{
            border-bottom: none;
        }}
        .legend {{
            margin-top: 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 8px;
        }}
        .legend h3 {{
            margin-top: 0;
        }}
        .legend-item {{
            display: inline-block;
            margin-right: 20px;
            margin-bottom: 10px;
        }}
        .legend-color {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-right: 5px;
            vertical-align: middle;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{network_name}</h1>
            <p>Generated: {generated_at}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Devices</h3>
                <div class="value">{analysis.get('total_devices', 0)}</div>
            </div>
            <div class="stat-card">
                <h3>Total Subnets</h3>
                <div class="value">{analysis.get('total_subnets', 0)}</div>
            </div>
            <div class="stat-card">
                <h3>Total Gateways</h3>
                <div class="value">{analysis.get('total_gateways', 0)}</div>
            </div>
            <div class="stat-card">
                <h3>Total Routes</h3>
                <div class="value">{analysis.get('total_routes', 0)}</div>
            </div>
        </div>
        
        <div id="cy"></div>
        
        <div class="legend">
            <h3>Legend</h3>
            <div class="legend-item">
                <span class="legend-color" style="background-color: #4CAF50;"></span>
                <span>Device</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background-color: #2196F3;"></span>
                <span>Gateway</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background-color: #FF9800;"></span>
                <span>Subnet</span>
            </div>
        </div>
        
        <div class="info-panel">
            <div class="info-card">
                <h3>Device Information</h3>
                <ul id="device-list"></ul>
            </div>
            <div class="info-card">
                <h3>Gateway Analysis</h3>
                <ul id="gateway-list"></ul>
            </div>
        </div>
        
        <div class="info-card">
            <h3>Subnet Analysis</h3>
            <ul id="subnet-list"></ul>
        </div>
        
        <div class="footer">
            <p>Network Swiss Tool Pro - L3 Routing Analysis Demo</p>
            <p>Interactive topology map with real routing data</p>
        </div>
    </div>
    
    <script>
        // Network topology data
        const nodes = {nodes_json};
        const edges = {edges_json};
        const subnetAnalysis = {subnet_analysis_json};
        const gatewayAnalysis = {gateway_analysis_json};
        const devices = {devices_json};
        const analysis = {analysis_json};
        
        // Build Cytoscape elements
        const elements = {{
            nodes: nodes.map(node => ({{
                data: {{
                    id: node.id,
                    label: node.id,
                    type: node.type
                }}
            }})),
            edges: edges.map(edge => ({{
                data: {{
                    source: edge.source,
                    target: edge.target,
                    type: edge.type
                }}
            }}))
        }};
        
        // Initialize Cytoscape
        const cy = cytoscape({{
            container: document.getElementById('cy'),
            elements: elements,
            style: [
                {{
                    selector: 'node',
                    style: {{
                        'background-color': function(ele) {{
                            const type = ele.data('type');
                            if (type === 'device') return '#4CAF50';
                            if (type === 'gateway') return '#2196F3';
                            if (type === 'subnet') return '#FF9800';
                            return '#999';
                        }},
                        'label': 'data(label)',
                        'font-size': '12px',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'width': '60px',
                        'height': '60px',
                        'border-width': 2,
                        'border-color': '#333'
                    }}
                }},
                {{
                    selector: 'edge',
                    style: {{
                        'width': 2,
                        'line-color': '#666',
                        'target-arrow-color': '#666',
                        'target-arrow-shape': 'triangle',
                        'curve-style': 'bezier'
                    }}
                }}
            ],
            layout: {{
                name: 'cose',
                animate: false,
                nodeRepulsion: 1000,
                idealEdgeLength: 100,
                nodeOverlap: 20
            }}
        }});
        
        // Populate device list
        const deviceList = document.getElementById('device-list');
        Object.entries(devices).forEach(([deviceId, info]) => {{
            const li = document.createElement('li');
            li.innerHTML = `<strong>${{deviceId}}</strong>: ${{info.route_count}} routes, protocols: ${{info.protocols.join(', ')}}`;
            deviceList.appendChild(li);
        }});
        
        // Populate gateway list
        const gatewayList = document.getElementById('gateway-list');
        Object.entries(gatewayAnalysis).forEach(([gateway, info]) => {{
            const li = document.createElement('li');
            li.innerHTML = `<strong>${{gateway}}</strong>: ${{info.subnet_count}} subnets, is_default: ${{info.is_default_gateway}}`;
            gatewayList.appendChild(li);
        }});
        
        // Populate subnet list
        const subnetList = document.getElementById('subnet-list');
        Object.entries(subnetAnalysis).forEach(([subnet, info]) => {{
            const li = document.createElement('li');
            li.innerHTML = `<strong>${{subnet}}</strong>: gateways: ${{info.gateway_ips.join(', ')}}, devices: ${{info.advertising_devices.join(', ')}}`;
            subnetList.appendChild(li);
        }});
    </script>
</body>
</html>"""
        
        return html


def generate_all_html_maps():
    """Generate HTML maps for all demo data files"""
    generator = HTMLMapGenerator()
    
    demo_dir = Path(__file__).parent / 'demo_data'
    
    # Generate HTML maps for each demo data file
    demo_files = [
        'enterprise_network.json',
        'small_office.json',
        'datacenter_network.json'
    ]
    
    for demo_file in demo_files:
        demo_path = demo_dir / demo_file
        if demo_path.exists():
            with open(demo_path) as f:
                data = json.load(f)
            
            output_filename = demo_file.replace('.json', '.html')
            generator.generate_html_map(data, output_filename)
    
    print(f"\\nHTML maps generated in {generator.output_dir}/")
    print(f"- enterprise_network.html")
    print(f"- small_office.html")
    print(f"- datacenter_network.html")


if __name__ == '__main__':
    generate_all_html_maps()

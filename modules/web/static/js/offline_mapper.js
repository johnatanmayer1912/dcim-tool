// offline_mapper.js
// Handles the visualization of L2, L3 and Flow maps using local offline libraries.

class OfflineMapper {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.network = null;
    }

    async loadL2Map() {
        try {
            const response = await fetch('/api/discovery/advanced_map/l2');
            const data = await response.json();
            this.renderMap(data);
        } catch (error) {
            console.error("Error loading L2 map:", error);
            this.container.innerHTML = "<p>Error loading map</p>";
        }
    }

    async loadL3Map() {
        try {
            const response = await fetch('/api/discovery/advanced_map/l3');
            const data = await response.json();
            this.renderMap(data);
        } catch (error) {
            console.error("Error loading L3 map:", error);
            this.container.innerHTML = "<p>Error loading map</p>";
        }
    }

    renderMap(data) {
        if (!this.container) return;
        
        // Ensure vis-network is loaded
        if (typeof vis === 'undefined') {
            this.container.innerHTML = "<p>Vis.js library is not loaded. Ensure it is bundled for offline use.</p>";
            return;
        }

        const nodes = new vis.DataSet(data.nodes);
        const edges = new vis.DataSet(data.edges);

        const options = {
            nodes: {
                shape: 'dot',
                size: 20,
                font: {
                    size: 14,
                    color: '#ffffff'
                },
                borderWidth: 2
            },
            edges: {
                width: 2,
                font: {
                    align: 'middle'
                },
                color: { inherit: 'from' }
            },
            physics: {
                forceAtlas2Based: {
                    gravitationalConstant: -26,
                    centralGravity: 0.005,
                    springLength: 230,
                    springConstant: 0.18
                },
                maxVelocity: 146,
                solver: 'forceAtlas2Based',
                timestep: 0.35,
                stabilization: { iterations: 150 }
            }
        };

        const graphData = { nodes, edges };
        this.network = new vis.Network(this.container, graphData, options);
    }
}

// Export to global scope
window.OfflineMapper = OfflineMapper;

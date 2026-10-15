"""
Node Adapter

Orchestrates per-node analysis operations.

v7.0.0 - Enterprise Architecture Refactor
"""

from typing import List, Dict, Any, Optional

from src.network.node_analyze import NodeAnalyzer


class NodeAdapter:
    """Adapter for node analysis operations."""
    
    def __init__(self):
        self.analyzer = NodeAnalyzer()
    
    def analyze_node(self, device: Dict, username: str, password: str) -> Dict:
        """Analyze a single network node."""
        return self.analyzer.analyze(device, username, password)

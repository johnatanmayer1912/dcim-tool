"""
modules/routing_analyzer/__init__.py
------------------------------------
L3 Routing Analysis Module for Network Swiss Tool Pro.

This module provides SSH-based routing table collection, parsing, and analysis
for Cisco IOS/IOS-XE, NX-OS, and Juniper Junos platforms.
"""

from .collector import RoutingCollector, collect_routing_table
from .parser import RoutingParser
from .normalizer import RoutingNormalizer
from .path_tracer import L3PathTracer

__all__ = [
    'RoutingCollector',
    'collect_routing_table',
    'RoutingParser',
    'RoutingNormalizer',
    'L3PathTracer',
]

__version__ = '1.0.0'

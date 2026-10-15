# BUG-0007: Discovery platform misclassification and duplicate map nodes

**Status:** Fixed in app **v7.0.1** (plugin **network_discovery 1.3.0**)  
**Severity:** High (operator trust / wrong topology counts)

## Symptoms

- NX-OS devices (correct hostname) labeled **JunOS** on Discovery map and inventory.
- Same physical switch appears as **multiple nodes** when reached via IP, hostname alias, or multiple links (e.g. 4+ nodes for a 3-device triangle).

## Root cause

1. `_platform_from_neighbor_string()` used `'ex' in platform`, which is true for **`'ex' in 'nexus'`**, classifying Cisco Nexus CDP platforms as Juniper.
2. Crawl deduplication only collapsed duplicate dict values by `id` string, without merging IP/hostname aliases before HTML export.

## Fix

- [`utils/discovery_graph.py`](../../../../utils/discovery_graph.py): `classify_os_family()`, `merge_nodes()`, `rewire_edges()`, `canonicalize_discovery_graph()`.
- Discovery crawl calls canonicalize before JSON/HTML export.
- Map labels show `OS family · model` via `node_map_label()`.

## Verification

- `tests/test_discovery_platform_classifier.py`
- `tests/test_discovery_graph_dedup.py`
- Manual: Discovery demo mode + live crawl; compare node count to unique devices.

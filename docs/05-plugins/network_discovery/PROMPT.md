# Prompt Instructions — Network Discovery & Crawl Plugin

# Purpose
Guides AI agents and developers on maintaining, debugging, or extending the Network Discovery & Crawl plugin.

# Scope
Crawl engines, parsing regexes, Vis.js generation logic.

---

## Guidelines for Modification
1. **Adding Platform Support**:
   - Add new command formats inside the `run()` crawl block.
   - Implement custom parsers (similar to `_parse_cisco_cdp_detail`) mapping local and remote port variables.
2. **Path Resolution Safety**:
   - Always use `_get_resource_path()` for loading local assets like `vis-network.min.js`.
3. **Vis.js Rendering**:
   - When modifying colors or shapes, respect the **NOC-grade Apple Glassmorphism** guidelines: deep slate backdrops, soft neon active borders, dynamic layout configurations.

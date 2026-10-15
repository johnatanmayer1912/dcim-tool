# Architecture Document: Visual Interface Management System

## Integration Layout
The Interface Manager is implemented as a hot-reloadable modular plugin extending the v6.0 plugin registry structure.

```
┌────────────────────────────────────────────────────────┐
│                      index.html                        │
│    (Vis.js map, interface grid, deploy safety modal)   │
└──────────────────────────┬─────────────────────────────┘
                           │ HTTP REST APIs
                           ▼
┌────────────────────────────────────────────────────────┐
│                 vlan_checker_web.py                    │
│   (Flask endpoints /api/interface/*)                   │
└──────────────────────────┬─────────────────────────────┘
                           │ Import & Execution
                           ▼
┌────────────────────────────────────────────────────────┐
│             modules/plugins/interface_manager.py       │
│  (run() contract, parsing engines, validation steps)   │
└────────────────────────────────────────────────────────┘
```

## Platform Modules
- **modules/network_base.py**: Abstraction of Netmiko/Paramiko SSH connectivity.
- **modules/plugin_registry.py**: Registration, metadata collection, dynamic execution routing.
- **utils/report_formatter.py**: Persistent report saving and historical tracking.

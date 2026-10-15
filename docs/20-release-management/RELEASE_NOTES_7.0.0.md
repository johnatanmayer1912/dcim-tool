# Network Swiss Tool Pro v7.0.0 — NOC Efficiency Bundle

**Release date:** 2026-05-24  
**Artifact:** `dist/NetworkSwissToolPro_v7.0.0_OFFLINE.exe`

## Highlights

- Single hostname identity contract across maps, reports, and plugins (no NX-OS banner labels).
- First-run health wizard: inventory, plugins, port, offline discovery + vPC demos, CLI smoke.
- Unified offline map UX: Link Inventory → Topology Map → search + adjacency (Discovery, standard, vPC simplified, STP).
- In-app “What’s new” on the About tab from `CHANGELOG.md`.
- MAC trace produces an ordered hop table and openable HTML path report.
- STP topology scan under Swiss Tools with demo mode for field validation.

## Upgrade notes

- Clear browser `localStorage` key `nst_health_v7_ok` to re-run the health wizard.
- Regenerate `DEMO_VPC_TOPOLOGY_v7.0.html` with `python create_demo_map_v7.py` if the vPC demo check fails.

## QA gate

Run the full matrix in the v7.0.0 plan (hostname, topo shell, MAC path, STP, VPC board, `_prebuild.py`, `_master_qa_test.py`) before deploying the EXE.

# BUG-0005 — Unbounded discovery job store

**Severity:** Low | **Owner:** Lead Developer

`_discovery_jobs` in `vlan_checker_web.py` grows for every crawl with no TTL or max entries. Long NOC sessions may retain large result payloads. Fix: cap to N jobs or expire after 24h; optional prune on new job.

"""Contract for static operator-console UX demos (docs/11-ux/demos)."""
from __future__ import annotations

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO = os.path.join(ROOT, "docs", "11-ux", "demos")

FILES = [
    "index.html",
    "00-app-shell.html",
    "01-inventory.html",
    "02-maps-hub.html",
    "03-find.html",
    "04-change.html",
    "05-evidence.html",
    "06-settings-vault.html",
    "07-maps-utilization.html",
    "08-e2e-incident.html",
    "nst-demo.css",
    "nst-demo.js",
]

CDN_HINTS = ("cdn.jsdelivr", "unpkg.com", "googleapis.com", "cdnjs.", "ajax.googleapis")

WORKSPACE_ARIA = {
    "01-inventory.html": "Inventory",
    "02-maps-hub.html": "Maps",
    "03-find.html": "Find",
    "04-change.html": "Change",
    "05-evidence.html": "Evidence",
    "06-settings-vault.html": "Settings",
    "07-maps-utilization.html": "Maps",
}


def _read(name: str) -> str:
    return open(os.path.join(DEMO, name), encoding="utf-8").read()


def test_demo_files_exist():
    missing = [n for n in FILES if not os.path.isfile(os.path.join(DEMO, n))]
    assert missing == [], missing


def test_html_demos_are_offline_local_assets():
    for name in FILES:
        if not name.endswith(".html"):
            continue
        html = _read(name)
        lower = html.lower()
        for hint in CDN_HINTS:
            assert hint not in lower, f"{name} pulls {hint}"
        if name != "index.html":
            assert 'href="nst-demo.css"' in html
            assert "skip-link" in html
            assert 'href="#main"' in html


def test_workspace_nav_aria_current():
    for name, label in WORKSPACE_ARIA.items():
        html = _read(name)
        assert 'aria-current="page"' in html, name
        assert label in html


def test_inlined_sample_json_parses():
    for name in FILES:
        if not name.endswith(".html") or name == "index.html":
            continue
        html = _read(name)
        m = re.search(
            r'<script type="application/json" id="sample-data">\s*(.*?)\s*</script>',
            html,
            re.S,
        )
        assert m, f"{name} missing sample-data"
        json.loads(m.group(1))


def test_inventory_commit_names_rejects():
    html = _read("01-inventory.html")
    assert "rejected will be omitted" in html.lower() or "2 rejected" in html
    assert "duplicate" in html.lower()
    assert "commit-modal" in html


def test_find_path_note_and_unlinked_hit():
    html = _read("03-find.html")
    assert "path_note" in html
    assert "unlinked" in html.lower()
    assert "disabled" in html


def test_change_golden_and_vlan_1002_no_ssh():
    html = _read("04-change.html")
    assert "Golden-config" in html or "golden" in html.lower()
    assert "1002" in html
    assert "No SSH" in html or "no SSH" in html


def test_utilization_does_not_mint_edges():
    html = _read("07-maps-utilization.html")
    assert "never creates edges" in html.lower() or "must not appear as a new link" in html.lower()
    assert "no SNMP sample" in html or "no sample" in html.lower()
    assert "Eth1/99" in html
    assert "94%" in html or ">90%" in html or "&gt;90%" in html


def test_e2e_has_six_steps():
    html = _read("08-e2e-incident.html")
    for label in ("Import", "Unlock", "Map", "MAC", "Issue", "VLAN"):
        assert label.lower() in html.lower(), label

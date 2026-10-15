"""Resolve a skill id to on-disk SKILL.md paths (search SKILL_CATALOG.json)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / '.cursor' / 'SKILL_CATALOG.json'


def main() -> int:
    if len(sys.argv) < 2:
        print('Usage: python scripts/resolve_skill.py <id-or-keyword>')
        return 1
    q = sys.argv[1].lower()
    data = json.loads(CATALOG.read_text(encoding='utf-8'))
    hits = [s for s in data['skills'] if q in s['id'].lower() or q in s.get('description', '').lower()]
    # prefer exact id
    exact = [s for s in hits if s['id'].lower() == q]
    ordered = exact + [s for s in hits if s not in exact]
    for s in ordered[:15]:
        print(f"{s['library']:14} {s['id']:40} {s['path']}")
    if not hits:
        print('No matches. Run scripts/build_skill_catalog.py')
        return 2
    print(f'\n{len(hits)} match(es), showing up to 15')
    return 0


if __name__ == '__main__':
    sys.exit(main())

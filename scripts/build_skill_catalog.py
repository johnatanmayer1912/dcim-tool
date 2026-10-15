"""Index skillss/ and .devin/skills/ into .cursor/SKILL_CATALOG.json (read-only sources)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.cursor' / 'SKILL_CATALOG.json'

FRONTMATTER_RE = re.compile(r'^---\s*\n(.*?)\n---', re.DOTALL)
NAME_RE = re.compile(r'^name:\s*["\']?([^"\'\n]+)', re.M)
DESC_RE = re.compile(r'^description:\s*["\']?(.+?)["\']?\s*$', re.M)


def parse_skill_md(path: Path) -> dict | None:
    try:
        text = path.read_text(encoding='utf-8', errors='replace')[:8000]
    except OSError:
        return None
    m = FRONTMATTER_RE.match(text)
    block = m.group(1) if m else text[:2000]
    name_m = NAME_RE.search(block)
    desc_m = DESC_RE.search(block)
    name = name_m.group(1).strip() if name_m else path.parent.name
    desc = desc_m.group(1).strip() if desc_m else ''
    if desc.startswith('"') or desc.startswith("'"):
        desc = desc.strip('"\'')
    return {
        'id': name,
        'name': name,
        'description': desc[:500],
        'path': str(path.relative_to(ROOT)).replace('\\', '/'),
        'library': 'skillss' if 'skillss' in str(path) else 'devin',
    }


def walk_skills(base: Path, library: str) -> list[dict]:
    entries = []
    if not base.is_dir():
        return entries
    for skill_md in base.rglob('SKILL.md'):
        # skip node_modules-ish noise
        if any(p in skill_md.parts for p in ('node_modules', '.git', '__pycache__')):
            continue
        row = parse_skill_md(skill_md)
        if row:
            row['library'] = library
            entries.append(row)
    return entries


def main() -> int:
    sources = [
        (ROOT / 'skillss', 'skillss'),
        (ROOT / '.devin' / 'skills', 'devin'),
        (ROOT / '.cursor' / 'skills', 'cursor-native'),
    ]
    all_entries: list[dict] = []
    seen: set[str] = set()
    for base, lib in sources:
        for e in walk_skills(base, lib):
            key = f"{e['id']}:{e['path']}"
            if key in seen:
                continue
            seen.add(key)
            all_entries.append(e)

    all_entries.sort(key=lambda x: (x['id'], x['library']))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    catalog = {
        'generated_by': 'scripts/build_skill_catalog.py',
        'total': len(all_entries),
        'libraries': {
            'skillss': sum(1 for e in all_entries if e['library'] == 'skillss'),
            'devin': sum(1 for e in all_entries if e['library'] == 'devin'),
            'cursor-native': sum(1 for e in all_entries if e['library'] == 'cursor-native'),
        },
        'skills': all_entries,
    }
    OUT.write_text(json.dumps(catalog, indent=2), encoding='utf-8')
    print(f'Wrote {OUT} ({catalog["total"]} skills)')
    return 0


if __name__ == '__main__':
    sys.exit(main())

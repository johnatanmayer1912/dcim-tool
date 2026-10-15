#!/usr/bin/env python3
"""Validate internal markdown links under docs/. Exit 1 if broken links found."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "docs"
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")

# Legacy folder renames (old docs layout → current layout)
LEGACY_SEGMENT_MAP = {
    "05-ui-ux": "06-ui-ux",
    "08-operations": "07-operations",
    "11-release-management": "20-release-management",
    "14-bug-reports": "13-bug-reports",
    "13-master-prompts": "12-master-prompts",
    "17-roles-by-command": "16-roles-by-command",
    "15-rebuild-roadmap": "14-roadmap",
}


def _strip_fenced_blocks(text: str) -> str:
    """Remove fenced code blocks so inline regex is not parsed as markdown links."""
    out = []
    in_fence = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(line)
    return "\n".join(out)


def _apply_legacy_map(path: Path) -> Path:
    s = str(path).replace("\\", "/")
    for old, new in LEGACY_SEGMENT_MAP.items():
        s = s.replace(f"/{old}/", f"/{new}/").replace(f"\\{old}\\", f"/{new}/")
        if s.endswith(f"/{old}"):
            s = s[: -len(old)] + new
    return Path(s)


def _resolve_target(source_md: Path, target: str) -> bool:
    target = target.split("#")[0].split("?")[0].strip()
    if not target:
        return True
    if target.startswith(("http://", "https://", "mailto:", "file:")):
        return True

    candidates = []
    if target.startswith("/"):
        candidates.append(Path(target))
    else:
        candidates.append((source_md.parent / target).resolve())

    for base in list(candidates):
        candidates.append(_apply_legacy_map(base))
        # Directory link (trailing slash)
        if str(target).endswith("/"):
            candidates.append(base)
            candidates.append(_apply_legacy_map(base))

    basename = Path(target.rstrip("/")).name
    if basename:
        for hit in ROOT.rglob(basename):
            candidates.append(hit.resolve())

    for p in candidates:
        try:
            if p.exists():
                return True
        except OSError:
            continue
    return False


def main():
    broken = []
    for md in sorted(ROOT.rglob("*.md")):
        text = _strip_fenced_blocks(md.read_text(encoding="utf-8", errors="replace"))
        for m in LINK_RE.finditer(text):
            target = m.group(2).strip()
            if target.startswith("#"):
                continue
            if not _resolve_target(md, target):
                broken.append((str(md.relative_to(ROOT)), target))
    print(f"Scanned: {ROOT}")
    print(f"Broken links: {len(broken)}")
    for f, t in broken[:80]:
        print(f"  {f} -> {t}")
    if len(broken) > 80:
        print(f"  ... and {len(broken) - 80} more")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())

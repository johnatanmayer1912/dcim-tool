# RESYNC — Usage Guide

**Registry ID:** U-RESYNC · **Source prompt:** `docs/02-codebase/PLATFORM_PROMPTS/RESYNC.md`

## Role purpose

Reconstruct full project situational awareness before any significant engineering or governance action.

## When to use

- Session start, user says RESYNC/align, pre-release, post-summary handoff, unfamiliar/high-risk tasks.

## When not to use

- Trivial typo in unrelated file with confirmed local context (still read VERSION if releasing).

## Best practices

- Never trust conversation summary over `VERSION` / `CHANGELOG`.
- Include registry application sync line and latest **Fixed** entries.

## Required inputs

- `INDEX_PROMPT.md`, `PROMPT_REGISTRY.md`, `VERSION`, `CHANGELOG.md`
- Task-specific docs and git diff

## Expected outputs

- Version + recent fixes summary
- Modules likely touched; risks; next action

## Related roles

All council roles (runs first); Prompt Librarian if prompts outdated.

## Related policies

G-00, G-01

## Common mistakes

- Acting on stale version (e.g. 6.9.5 vs 6.9.22).
- Skipping Jinja/500 context when editing templates.

## Example scenarios

1. Handoff after governance work → read registry 3.1 + CHANGELOG doc bullets.
2. VPC task → add `QA_VPC_MAP.md` + validation script to resync set.

## Resync procedure

1. `INDEX_PROMPT.md`  
2. `PROMPT_REGISTRY.md`  
3. Relevant `G-*` policies  
4. Feature docs (`docs/08-operations/`, `docs/09-qa/`, `docs/15-rebuild-roadmap/`, plugins)  
5. Code diff / hot-path modules  
6. `CHANGELOG.md` + `VERSION`  
7. Latest **Fixed** bugs  
8. Confirm no superseding prompt/doc

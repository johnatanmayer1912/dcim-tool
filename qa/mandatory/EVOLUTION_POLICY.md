# Mandatory QA Evolution Policy

This policy governs how automated tests **grow with the program**. It is mandatory for every feature, bug fix, and release.

## Principles

1. **No silent drift** — code changes without test updates are incomplete.
2. **Code-backed** — mandatory tests assert routes, symbols, files, or behavior exist in source.
3. **Persona-aligned** — every test maps to a council lens (architect, network, field, etc.).
4. **Manifest is law** — `MANIFEST.yaml` must list every file in `tests/mandatory/`.
5. **Gaps become tests** — council GAP findings → new `MQA-*` test in same PR.

## When to extend (required)

| Event | Action |
|-------|--------|
| New feature | Add questionnaire rows + mandatory tests + manifest entries |
| Bug fixed | Add regression test referencing bug ID / version |
| Vendor added | Extend vendor parity tests + questionnaire section C |
| New API route | Architect + software engineer contract tests |
| UI control added | Field operator + UI/UX tests |
| Security change | Security lens tests + questionnaire section A |
| Release prep | Run full gate (when executing): `run_mandatory_qa.py` |

## Test ID convention

```
MQA-<lens>-<topic>-<nnn>
```

Example: `MQA-network-counter-gi-alias-001`

## File layout

```
tests/mandatory/
  test_lens_architect.py
  test_lens_software_engineer.py
  ...
qa/mandatory/
  MANIFEST.yaml
  EVOLUTION_POLICY.md   (this file)
```

## Manifest update checklist

- [ ] New test file listed under correct lens
- [ ] `questionnaire_ids` link to QUESTIONNAIRE.md rows
- [ ] `introduced_version` set
- [ ] `scenario` documents operator context

## Review cadence

- **Every code change** — Cursor hook reminds to sync manifest
- **Every PR / push** — CI `mandatory-qa.yml` (when enabled)
- **Every release** — `_prebuild.py` manifest integrity + full mandatory run

## Do not

- Delete mandatory tests without replacing coverage
- Skip manifest update when adding tests
- Mark GAP as fixed without a regression test

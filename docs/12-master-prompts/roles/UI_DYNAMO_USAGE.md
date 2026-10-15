# UI DYNAMO — Usage Guide

**Registry ID:** U-UI · **Source:** `docs/02-codebase/PLATFORM_PROMPTS/P04_UI_DYNAMO.md`

## Role purpose

Flask/Jinja/Bootstrap UI: templates, tabs, client JS embedded in server templates, and safe rendering.

## When to use

- `modules/web/templates/index.html` or static UI assets.
- New tabs (e.g. search_it, Config Templates).
- TemplateSyntaxError / 500 on `/`.

## When not to use

- Backend-only parser changes with no template touch.

## Best practices

- Never use raw `{{` in JS inside Jinja without `{% raw %}` or escaped braces.
- Smoke `/` after template edits (v6.9.22: `tmplBuildVarForm`).
- Prefer `{% raw %}` blocks for template-editor demo strings.

## Required inputs

- `P04_UI_DYNAMO.md`, `G-07`
- Flask test client or browser check

## Expected outputs

- 200 on `/` and affected routes
- QA notes for template safety

## Related roles

Lead Developer; QA Engineer; Documentation Steward.

## Related policies

G-07

## Common mistakes

- `{{ ${v} }}` inside Jinja (breaks server render).
- CDN assumptions for offline EXE without documenting.

## Example scenarios

1. Config Templates variable form → Jinja escape pattern from CHANGELOG v6.9.22.
2. Rename tab to search_it → index segment + JS handlers.

## Resync procedure

INDEX, registry, G-07, CHANGELOG **Fixed** for template lines, read `index.html` diff only.

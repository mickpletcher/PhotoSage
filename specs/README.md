# Specs

Use this folder for larger PhotoSage changes.

A spec is needed when a change:

- Adds a provider.
- Changes CLI or GUI behavior.
- Touches rename safety.
- Changes manifests or undo.
- Adds a new workflow.
- Affects more than one module.

Small bug fixes do not need a spec.

## Folder Format

Use the next number:

```text
specs/
  001-feature-name/
    spec.md
    plan.md
    tasks.md
```

## What Each File Is For

- `spec.md`: What the feature must do.
- `plan.md`: How to build it.
- `tasks.md`: The implementation checklist.

## Required Safety Rules

Every spec must preserve these rules:

- Metadata first.
- AI only when needed or forced.
- Preview before apply.
- No rename without `--apply`.
- No overwrites.
- Manifest before file changes.
- Undo must keep working.
- Local-only mode must block cloud calls.
- Providers classify only. They do not rename files.

## Active Specs

- [001-lm-studio-provider](001-lm-studio-provider/spec.md)

# PhotoSage Specs

This folder is the planning source for larger PhotoSage changes.

Use specs when a change affects more than one subsystem, changes user-facing behavior, adds a provider, touches rename safety, changes manifests, or adds a new workflow.

Small bug fixes can skip specs if the fix is obvious and contained.

## Workflow

Each feature gets its own numbered folder:

```text
specs/
  001-feature-name/
    spec.md
    plan.md
    tasks.md
```

Use the next available number. Keep names short and lowercase.

## File Roles

`spec.md`

Defines the user problem, requirements, non-goals, safety constraints, and acceptance criteria.

`plan.md`

Defines the implementation approach, files to change, data flow, risks, and verification strategy.

`tasks.md`

Defines the actual checklist used during implementation.

## Required Sections

Every spec should answer:

- What user workflow changes?
- What modules are in scope?
- What modules are out of scope?
- What safety rules must remain true?
- What tests prove the change works?
- What docs need updates?

## Safety Requirements

PhotoSage specs must preserve these project rules:

- Metadata first.
- AI fallback only when needed or explicitly forced.
- Providers classify images only.
- Providers never rename or move files.
- Preview before apply.
- No rename without explicit `--apply`.
- No overwrites.
- Manifest before mutation.
- Undo must remain possible.
- Local-only mode must block cloud calls.

## Current Specs

- `001-lm-studio-provider`: Add LM Studio as a local OpenAI-compatible vision provider.

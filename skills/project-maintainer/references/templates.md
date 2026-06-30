# Project Maintainer Templates

Use these templates as compact starting points. Remove empty sections instead of filling space.

## Root README

```markdown
# Project Maintainer Docs

Status: initialized | partial | current
Last updated: YYYY-MM-DD
Sync status: current | partial | stale | unknown

## Project Brief

- Name:
- Purpose:
- Primary users:
- Main runtime:
- Tech stack:

## How To Read

Start with `INDEX.md`, then `manifest.yaml`, then the module or directory relevant to the task.

## Maintenance Rules

- Keep files within the size budgets in `references/artifact-structure.md`.
- Update module docs, directory docs, changes, and decisions after behavior or structure changes.
- Check existing artifact sync status before relying on it.
- Mark uncertain claims with `confidence: inferred` or `confidence: unknown`.
```

## Manifest

```yaml
version: "0.0.1"
artifact_root: ".doc_project_maintainer"
last_updated: "YYYY-MM-DD"

sync:
  status: "unknown"
  last_scanned_commit: null
  last_synced_commit: null
  pending:
    - id: "SYNC-YYYYMMDD-001"
      reason: "Docs may not reflect recent gateway changes."
      paths:
        - "src/gateway"
      modules:
        - "gateway"
      created: "YYYY-MM-DD"

project:
  name: ""
  summary: ""
  docs:
    overview: "project/overview.md"
    architecture: "project/architecture.md"
    glossary: "project/glossary.md"
    build_plan: "project/build-plan.md"
    open_questions: "project/open-questions.md"

modules:
  - id: "gateway"
    name: "Gateway"
    summary: "Handles external entrypoints and message routing."
    confidence: "confirmed"
    docs:
      readme: "modules/gateway/README.md"
      design: "modules/gateway/design.md"
      directories: "modules/gateway/directories.md"
      changes: "modules/gateway/changes.md"
      git_history: "modules/gateway/git-history.md"
    directories:
      - "src/gateway"
      - "tests/gateway"
    related_decisions: []
    recent_changes: []
    coverage:
      status: "partial"
      last_scanned: "YYYY-MM-DD"
      notes: "Entrypoints scanned; git history still pending."

directories:
  - path: "src/gateway"
    encoded: "src__gateway"
    summary: "Gateway implementation."
    modules:
      - "gateway"
    doc: "directories/src__gateway/README.md"
    related_changes: []
    related_decisions: []
    coverage:
      status: "partial"
      last_scanned: "YYYY-MM-DD"
```

## Build Plan

```markdown
---
last_updated: YYYY-MM-DD
sync_status: current | partial | stale | unknown
coverage_status: planned | partial | current
---

# Build Plan

## Current State

- Artifact status:
- Trusted coverage:
- Known stale areas:

## Completed Slices

- YYYY-MM-DD: `module-or-path` - what was built and confidence

## Pending Slices

- `module-or-path`: why it remains and suggested next step

## Multi-Agent Notes

- Slice boundaries:
- Integration owner:
- Files that require central merge:

## Open Questions

- Question:
```

## Module README

```markdown
---
id: module-id
name: Module Name
confidence: confirmed | inferred | unknown
last_updated: YYYY-MM-DD
read_when: "Working on this module or one of its mapped directories."
---

# Module Name

## Responsibility

One short paragraph.

## Boundaries

- Owns:
- Does not own:

## Entry Points

- `path/to/file`: why it matters

## Directory Map

See `directories.md`.

## Related Changes

See `changes.md`.

## Related Decisions

- ADR-NNNN: title
```

## Directory README

```markdown
---
path: src/gateway
encoded: src__gateway
modules:
  - gateway
confidence: confirmed | inferred | unknown
last_updated: YYYY-MM-DD
read_when: "Editing files under this directory or tracing its ownership."
---

# `src/gateway`

## Purpose

One short paragraph.

## Important Files

- `file.py`: role

## Module Links

See `module-links.md`.

## Related Changes

See `changes.md`.
```

## Change Record

```markdown
---
id: CHG-YYYYMMDD-NNN
title: Short semantic title
type: feature | fix | refactor | docs | test | chore
date: YYYY-MM-DD
modules:
  - module-id
directories:
  - path/to/directory
decisions:
  - ADR-NNNN
commits:
  - abc1234
confidence: confirmed | inferred | unknown
---

# Short Semantic Title

## What Changed

Brief behavior or structure change.

## Why

Use evidence. Mark uncertainty explicitly.

## Impact

- User-visible:
- Internal:
- Tests:
```

## Decision Record

```markdown
---
id: ADR-NNNN
title: Short decision title
status: proposed | accepted | superseded | deprecated
date: YYYY-MM-DD
modules:
  - module-id
directories:
  - path/to/directory
related_changes:
  - CHG-YYYYMMDD-NNN
confidence: confirmed | inferred | unknown
---

# ADR-NNNN: Short Decision Title

## Context

What forced this decision.

## Decision

What was chosen.

## Consequences

- Positive:
- Negative:
- Follow-up:
```

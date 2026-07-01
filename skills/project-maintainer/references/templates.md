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

Start with `INDEX.md`, then `manifest.yaml`, then the module, directory, or flow relevant to the task.

## Maintenance Rules

- Keep files within the size budgets in `references/artifact-structure.md`.
- Update module docs, directory docs, flow docs, changes, and decisions after behavior or structure changes.
- Check existing artifact sync status before relying on it.
- Do not mark the artifact `current` without a recorded coverage closure audit or skip reason.
- Do not mark cross-boundary behavior `current` unless required flows are documented, pending, or out of scope.
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
  coverage_closure:
    status: "not_run" # not_run | partial | passed | skipped
    source: null # git ls-files | filesystem listing | skipped
    last_audited: null
    tracked_paths: "not_audited" # not_audited | mapped_or_dispositioned
    untracked_paths: "not_audited" # not_audited | classified | not_applicable
    flow_traces: "not_audited" # not_audited | documented_or_dispositioned
    notes: "Do not mark current until stable tracked paths and required flows are mapped, pending, or out of scope."
  pending:
    - id: "SYNC-YYYYMMDD-001"
      reason: "Docs may not reflect recent changes."
      paths:
        - "path/to/directory"
      modules:
        - "module-id"
      flows: []
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
    flows_dir: "project/flows"

modules:
  - id: "module-id"
    name: "Module Name"
    summary: "Module responsibility."
    confidence: "confirmed"
    docs:
      readme: "modules/module-id/README.md"
      design: "modules/module-id/design.md"
      directories: "modules/module-id/directories.md"
      changes: "modules/module-id/changes.md"
      git_history: "modules/module-id/git-history.md"
    directories:
      - "path/to/directory"
      - "tests/module-id"
    related_decisions: []
    related_flows: []
    recent_changes: []
    coverage:
      status: "partial"
      last_scanned: "YYYY-MM-DD"
      notes: "Entrypoints scanned; related flows still pending."

directories:
  - path: "path/to/directory"
    encoded: "path__to__directory"
    summary: "Directory responsibility."
    modules:
      - "module-id"
    doc: "directories/path__to__directory/README.md"
    related_changes: []
    related_decisions: []
    related_flows: []
    coverage:
      status: "partial"
      last_scanned: "YYYY-MM-DD"

flows:
  - id: "flow-id"
    name: "Flow Name"
    summary: "Cross-boundary behavior that produces or restores relied-on state or output."
    confidence: "inferred"
    doc: "project/flows/flow-id.md"
    modules: []
    directories: []
    entrypoints: []
    source_of_truth: []
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
flow_coverage_status: planned | partial | current
---

# Build Plan

## Current State

- Artifact status:
- Trusted coverage:
- Known stale areas:
- Known incomplete areas:
- Known incomplete flow slices:

## Completed Slices

- YYYY-MM-DD: `slice-id` - module, directory, or flow slice built and confidence

## Pending Slices

- `module-or-path`: why it remains and suggested next step

## Pending Flow Slices

- `flow-id`: required outcome or state, missing trace link, and suggested next step

## Coverage Closure Audit

- Audit source:
- Tracked path audit:
- Unmapped stable tracked paths:
- Pending tracked paths:
- Out-of-scope tracked paths:
- Untracked path disposition:
- Generated/local/runtime exclusions:
- Flow trace disposition:
- Criteria to mark `current`:

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

## Related Flows

- `flow-id`: why it matters
```

## Directory README

```markdown
---
path: path/to/directory
encoded: path__to__directory
modules:
  - module-id
confidence: confirmed | inferred | unknown
last_updated: YYYY-MM-DD
read_when: "Editing files under this directory or tracing its ownership."
---

# `path/to/directory`

## Purpose

One short paragraph.

## Important Files

- `file.py`: role

## Module Links

See `module-links.md`.

## Related Changes

See `changes.md`.

## Related Flows

- `flow-id`: why it matters.
```

## Flow Doc

```markdown
---
id: flow-id
name: Flow Name
status: partial
confidence: inferred
last_updated: YYYY-MM-DD
user_visible_surface:
source_of_truth: []
modules: []
directories: []
entrypoints: []
---

# Flow Name

## Outcome

What users, operators, integrations, or future agents rely on.

## Causal Path

Producer -> boundary crossings -> transport or contract -> consumer state -> output surface.

## State Classification

Files, databases, caches, generated artifacts, telemetry, debug traces, fixtures, transient runtime state, or disposable local state touched by the flow. State which item is source of truth when one exists.

## Replay, Restore, Or Reconstruction

How state or output is reconstructed after reload, restart, pagination, retry, rebuild, or recovery.

## Contract

Stable methods, message types, file formats, schemas, payload fields, or compatibility layers.

## Consumer State And Output

State mutations, derived state, renderers, exporters, operator surfaces, or integration outputs.

## Failure, Ordering, And Identity

Errors, retries, cancellation, ordering guarantees, deduplication keys, idempotency, and finalization rules when they affect visible or durable behavior.

## Verification

Relevant tests, scripts, manual checks, or missing coverage.

## Known Gaps

Open questions and uncertain links.
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
flows:
  - flow-id
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
flows:
  - flow-id
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

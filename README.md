# Project Maintainer Skill

Project Maintainer is a Codex skill for creating and maintaining compact, structured project documentation inside a target repository.

The skill is designed for long-lived codebases where agents need to understand project structure without loading a large documentation corpus into context. It creates a `.doc_project_maintainer/` artifact in the maintained project and keeps that artifact organized by modules, directories, cross-boundary flows, code symbols, changes, decisions, and build progress.

## Contents

```text
skills/
  project-maintainer/
    SKILL.md
    VERSION
    metadata.yaml
    LICENSE
    agents/openai.yaml
    references/
      artifact-structure.md
      code-symbol-docs.md
      templates.md
    scripts/
      check_doc_sizes.py
      audit_integrity.py
      render_audit_report.py
      inventory_symbols.py
  project-maintainer.zip
```

## Version

Current version: `0.0.11`

## What The Skill Does

- Initializes `.doc_project_maintainer/` in a target repository.
- Documents project overview, architecture, module boundaries, and directory responsibilities.
- Documents cross-boundary causal flows for user-visible, stateful, generated, integration, background, or operator-facing behavior.
- Documents every stable source file, top-level class, top-level function, and class method using a source-mirrored `code/` tree with class, function, and method health assessment.
- Routes work into Knowledge Base Delivery Mode when the `.doc_project_maintainer/` artifact is the requested deliverable, and Maintenance-Aware Fix Mode when Project Maintainer is requested during a bug fix, feature change, or refactor.
- Generates source symbol inventories, git-linked coverage maps, and symbol audit maps through a dependency-light script that automatically uses stronger extractors when available and falls back without blocking.
- Promotes and verifies audit status transitions through `scripts/audit_integrity.py`, including HMAC-SHA256 integrity metadata, source and entry-doc hash checks, and trusted/provisional/suspicious/invalid agent audit reporting.
- Generates a self-contained HTML audit visualization report through `scripts/render_audit_report.py`, combining `coverage-map.json`, `symbol-audit-map.json`, and a freshly refreshed `audit_integrity.py report` result for human review.
- Requires single-symbol health audits to be performed by the current agent after reading implementation evidence, and multiple-symbol health audits to use one audit agent per required symbol instead of bulk script-generated health.
- Classifies inventoried files with `source_role` and `audit_scope` so full repository coverage stays separate from default runtime/library health audit.
- Records a directory disposition summary showing recorded source directories, excluded directories with reasons, and skipped non-source directories.
- Summarizes git history by module, directory, flow, and code symbol when applicable.
- Records meaningful project and code changes, including features, fixes, refactors, behavior or structure changes, test strategy changes, and design decisions, while excluding routine artifact synchronization from change records.
- Tracks partial coverage with `project/coverage-map.json` and `project/build-plan.md` for large projects.
- Tracks class, top-level function, and class method audit state with `project/symbol-audit-map.json`, including symbol-level expiration that avoids invalidating unchanged sibling methods, agent/human audit state, health snapshots, issue records, and default health audit summaries.
- Recommends repository coverage slices and default runtime/library audit slices for first scans or stale coverage when the repository exceeds file, symbol, or module-size thresholds.
- Requires a coverage closure audit before marking project-wide coverage or sync status as current.
- Requires full repository analysis goals to continue through actionable pending slices instead of ending after a partial map.
- Requires every top-level class, top-level function, and class method to have `Actual Role` plus health before code symbol coverage can be current; pending symbol slices keep coverage partial.
- Requires agents to synchronize affected artifact slices after verified code changes when Project Maintainer is used during repair or development.
- Enforces small file budgets so future agents can read only the relevant slices.

## Validation

Validate the skill metadata:

```bash
python C:/Users/Administrator/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/project-maintainer
```

Check generated project-maintainer artifacts for oversized files:

```bash
python skills/project-maintainer/scripts/check_doc_sizes.py <repo-root>/.doc_project_maintainer
```

Generate an audit visualization report for a maintained project:

```bash
python skills/project-maintainer/scripts/render_audit_report.py <repo-root>
```

The output defaults to `<repo-root>/.doc_project_maintainer/project/audit-report.html`. If inventory, coverage maps, symbol audit maps, or integrity reports are refreshed afterward, regenerate the HTML because the report reflects older data.

The packaged skill archive is available at `skills/project-maintainer.zip`.

## License

This project is licensed under the Apache License, Version 2.0. See `LICENSE`.

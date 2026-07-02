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
      inventory_symbols.py
  project-maintainer.zip
```

## Version

Current version: `0.0.3`

## What The Skill Does

- Initializes `.doc_project_maintainer/` in a target repository.
- Documents project overview, architecture, module boundaries, and directory responsibilities.
- Documents cross-boundary causal flows for user-visible, stateful, generated, integration, background, or operator-facing behavior.
- Documents every stable source file, top-level function, and class method using a source-mirrored `code/` tree with function and method health assessment.
- Generates source symbol inventories and git-linked coverage maps through a dependency-light script that automatically uses stronger extractors when available and falls back without blocking.
- Summarizes git history by module, directory, flow, and code symbol when applicable.
- Records feature, fix, refactor, and design-decision changes.
- Tracks partial coverage with `project/coverage-map.json` and `project/build-plan.md` for large projects.
- Recommends subagent slices for first scans or stale coverage when the repository exceeds file, symbol, or module-size thresholds.
- Requires a coverage closure audit before marking project-wide coverage or sync status as current.
- Requires full repository analysis goals to continue through actionable pending slices instead of ending after a partial map.
- Requires every top-level function and class method to have `Actual Role` plus health before code symbol coverage can be current; pending symbol slices keep coverage partial.
- Requires agents to update the maintenance artifact after code development when behavior or structure changes.
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

The packaged skill archive is available at `skills/project-maintainer.zip`.

## License

This project is licensed under the Apache License, Version 2.0. See `LICENSE`.

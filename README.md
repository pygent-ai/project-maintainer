# Project Maintainer Skill

Project Maintainer is a Codex skill for creating and maintaining compact, structured project documentation inside a target repository.

The skill is designed for long-lived codebases where agents need to understand project structure without loading a large documentation corpus into context. It creates a `.doc_project_maintainer/` artifact in the maintained project and keeps that artifact organized by modules, directories, changes, decisions, and build progress.

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
      templates.md
    scripts/
      check_doc_sizes.py
  project-maintainer.zip
```

## Version

Current version: `0.0.1`

## What The Skill Does

- Initializes `.doc_project_maintainer/` in a target repository.
- Documents project overview, architecture, module boundaries, and directory responsibilities.
- Summarizes git history by module and directory.
- Records feature, fix, refactor, and design-decision changes.
- Tracks partial coverage with `project/build-plan.md` for large projects.
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

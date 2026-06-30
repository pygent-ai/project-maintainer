---
name: project-maintainer
description: Create and maintain compact in-repository project-maintenance documentation. Use when initializing a project knowledge base, documenting a new project design, exploring an existing project, summarizing git history by module or directory, or updating project docs after a feature, refactor, or bug fix.
---

# Project Maintainer

## Purpose

Maintain a structured project knowledge base inside the target repository at `.doc_project_maintainer/`. Treat the artifact as an agent-readable project map, not a long-form documentation dump.

Use a dual-axis model:

- Modules are the primary understanding axis: product capability, service boundary, package, subsystem, or feature area.
- Directories are the evidence axis: real paths, file ownership, tests, runtime entrypoints, and git changes.

Keep files small enough for selective reading. Prefer indexes, summaries, and links over repeated narrative.

## Preflight

1. Identify the target repository root.
2. Check whether `.doc_project_maintainer/` already exists.
3. If the artifact exists, read `.doc_project_maintainer/INDEX.md`, `.doc_project_maintainer/manifest.yaml`, and `.doc_project_maintainer/project/build-plan.md` when present.
4. Assess whether the existing artifact is stale before editing code or docs:
   - Compare the current task, touched paths, git status, recent commits, and manifest mappings.
   - If the task depends on stale docs, sync the relevant artifact files before relying on them.
   - If stale docs are unrelated to the current task, record or preserve the pending sync state and remind the user at the end.
5. If starting fresh, create the artifact structure described in `references/artifact-structure.md`.
6. Load `references/templates.md` before creating or heavily revising artifact files.

## Core Workflows

### Initialize New Project Docs

Use this when the project is new or still being designed.

1. Capture project goal, audience, runtime shape, technical stack, and important constraints.
2. Propose initial modules before detailed files exist.
3. Map planned directories to modules.
4. Record early architecture decisions as decision records.
5. Create `.doc_project_maintainer/README.md`, `INDEX.md`, `manifest.yaml`, project overview, initial module docs, and initial directory docs.

### Explore Existing Project

Use this when the repository already has code.

1. Inspect root files, package manifests, build config, test config, and existing docs.
2. List top-level directories and likely entrypoints.
3. Infer modules from package boundaries, command entrypoints, tests, routes, services, and recurring directory names.
4. Create directory docs as evidence, then module docs as interpretation.
5. Mark uncertain module boundaries with `confidence: inferred` and add questions to `project/open-questions.md`.
6. For large projects, create or update `project/build-plan.md` before attempting full coverage. Document what has been scanned, what is trusted, what remains, and the next suggested module or directory slices.

### Build Large Artifacts In Slices

Use this when the project is too large to map accurately in one pass.

1. Create `project/build-plan.md` with phases, scope, completed slices, pending slices, blocked questions, and integration notes.
2. Prefer module slices when the module boundaries are clear. Prefer directory slices when module boundaries are unknown.
3. When multi-agent tools are available, assign independent slices to agents by module or directory. Give each agent only the root index, manifest, build plan, assigned paths, and required templates.
4. Require each agent to write or propose updates only for its assigned slice and to report affected modules, directories, changes, decisions, confidence, and open questions.
5. Integrate slice outputs centrally by updating `manifest.yaml`, `INDEX.md`, cross-links, and `project/build-plan.md`.
6. Keep incomplete coverage explicit. A partial but honest artifact is better than a broad artifact with invented certainty.

### Summarize Git History

Use this when a git repository exists and history should be documented.

1. Read recent commits and relevant path history with `git log --stat`, `git log -- <path>`, and `git show --name-status`.
2. Assign commits to directories by touched paths.
3. Assign commits to modules through `manifest.yaml` directory mappings.
4. Create one change record per meaningful feature, fix, refactor, or behavior change.
5. Do not invent intent. Use `confidence: confirmed` only when commit messages, issues, PRs, docs, or code context clearly support the reason. Otherwise use `confidence: inferred` or `confidence: unknown`.

### Update After Feature Or Fix

Use this whenever code changes alter behavior, structure, boundaries, dependencies, or known defects.

1. Update affected module docs.
2. Update affected directory docs.
3. Add or update change records.
4. Add or update decision records when design rationale changed.
5. Update `manifest.yaml`, `INDEX.md`, and any `changes/by-*` index that points to the new records.
6. Update `project/build-plan.md` when the task changes coverage, known gaps, or next steps.
7. Run the size-check script when available.

### Develop Code With This Skill

When this skill is used during feature development, refactoring, or defect repair, treat artifact sync as part of the completion criteria.

1. Before coding, read the relevant module and directory docs if they exist.
2. During coding, note affected modules, directories, decisions, and changes.
3. After coding and verification, update the corresponding artifact files before the final response when feasible.
4. If artifact sync is needed but cannot be completed safely in the current turn, state the pending sync clearly in the final response and include the affected modules or directories.

## Final Response Checklist

Before finishing a task that used this skill:

- State whether `.doc_project_maintainer/` exists.
- State whether the artifact was updated, was already current for the task, or still needs sync.
- If sync is pending, name the affected module or directory docs and the reason.
- If the project is only partially mapped, point to `project/build-plan.md` and summarize the next slice.

## Reading Strategy

Never read the whole artifact by default. Start with:

1. `.doc_project_maintainer/INDEX.md`
2. `.doc_project_maintainer/manifest.yaml`
3. The target module `README.md`
4. The target directory `README.md`
5. Only the linked change or decision records that matter for the current task

If a file exceeds its size budget, split it before adding more content.

## Required References

- Read `references/artifact-structure.md` when creating the artifact, checking size budgets, choosing filenames, or wiring links.
- Read `references/templates.md` when writing `manifest.yaml`, module docs, directory docs, change records, or decision records.

## Validation

If `.doc_project_maintainer/` exists and `scripts/check_doc_sizes.py` is available, run:

```bash
python <skill-dir>/scripts/check_doc_sizes.py <repo-root>/.doc_project_maintainer
```

Fix any reported oversized file by splitting it and updating parent indexes.

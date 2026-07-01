---
name: project-maintainer
description: Create and maintain compact in-repository project-maintenance documentation. Use when initializing a project knowledge base, documenting design, exploring existing code, tracing cross-boundary runtime flows, summarizing git history, or updating project docs after a feature, refactor, or bug fix.
---

# Project Maintainer

## Purpose

Maintain a structured project knowledge base inside the target repository at `.doc_project_maintainer/`. Treat the artifact as an agent-readable project map, not a long-form documentation dump.

Use three complementary views:

- Modules are the primary understanding axis: product capability, service boundary, package, subsystem, or feature area.
- Directories are the evidence axis: real paths, file ownership, tests, runtime entrypoints, and git changes.
- Cross-boundary flows are the causal axis: how user-visible output, durable state, external integration state, generated artifacts, background status, or operator/admin decisions come into existence.

Flow docs are required when behavior crosses module, process, service, runtime, storage, protocol, or UI boundaries and affects state or output that users, operators, integrations, or future agents rely on.

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
4. Identify candidate cross-boundary flows from entrypoints, boundary handlers, event or message types, persistence readers and writers, protocol adapters, queues, workers, schedulers, caches, stores, reducers, replay or hydration logic, renderers, importers, exporters, integrations, and tests.
5. Create directory docs as evidence, module docs as interpretation, and flow docs for causal behavior that crosses boundaries.
6. Mark uncertain module boundaries or flow links with `confidence: inferred` and add questions to `project/open-questions.md`.
7. For large projects, create or update `project/build-plan.md` before attempting full coverage. Document what has been scanned, what is trusted, what remains, and the next suggested module, directory, or flow slices.

### Build Large Artifacts In Slices

Use this when the project is too large to map accurately in one pass.

1. Create `project/build-plan.md` with phases, scope, completed slices, pending slices, blocked questions, and integration notes.
2. Prefer module slices when the module boundaries are clear. Prefer directory slices when module boundaries are unknown. Prefer flow slices when the risk is causal behavior across boundaries.
3. When multi-agent tools are available, assign independent slices to agents by module, directory, or flow. Give each agent only the root index, manifest, build plan, assigned paths or flow scope, and required templates.
4. Require each agent to write or propose updates only for its assigned slice and to report affected modules, directories, flows, changes, decisions, confidence, and open questions.
5. Integrate slice outputs centrally by updating `manifest.yaml`, `INDEX.md`, cross-links, and `project/build-plan.md`.
6. Keep incomplete coverage explicit. A partial but honest artifact is better than a broad artifact with invented certainty.
7. Before marking coverage or sync status as `current`, run the coverage closure audit below and record the result in `project/build-plan.md`.

### Trace Cross-Boundary Causal Flows

Use this when behavior crosses module, process, service, runtime, storage, protocol, or UI boundaries and affects user-visible output, durable state, external integration state, generated artifacts, background status, or operator/admin decisions.

1. Identify candidate flows from producers, boundary crossings, data contracts, persistence points, state mutation points, output surfaces, recovery paths, and verification coverage.
2. For each candidate, choose one disposition:
   - create or update a concise flow doc under `project/flows/`,
   - record it as a pending flow slice in `project/build-plan.md`,
   - mark it out of scope with a reason.
3. For each documented flow, record:
   - the user-visible or externally relied-on outcome,
   - the producer that creates the data, event, state, artifact, or decision input,
   - each meaningful boundary crossing,
   - the transport, protocol, data contract, or file format that carries it,
   - durable or derived state and whether it is source of truth, cache, generated output, telemetry, debug trace, transient runtime state, fixture, or disposable local state,
   - replay, restore, hydration, pagination, or reconstruction behavior when applicable,
   - consumer state and the final output, renderer, exporter, or operator surface,
   - failure, ordering, identity, deduplication, idempotency, and finalization rules when they affect visible or durable behavior,
   - tests, scripts, manual checks, or missing verification,
   - known gaps and confidence.
4. Keep flow docs focused on stable causal chains and contracts. Do not document every helper, local branch, or UI component unless it changes the causal behavior.
5. If the flow cannot be traced from producer through boundary crossings to state and output, keep the flow `partial` and add the missing link to `project/build-plan.md`.

### Coverage Closure Audit

Use this before marking an artifact `current` or treating `project/build-plan.md` as complete.

1. List stable project paths:
   - Use `git ls-files` when the target repository uses git.
   - If git is unavailable, use the best stable source listing available and record that git was unavailable.
2. Group tracked files by stable directory boundary. Do not require file-by-file documentation.
3. Compare those directories against `manifest.yaml` directory mappings and documented pending slices.
4. For each unmapped stable tracked path, choose exactly one disposition:
   - add or update a module and directory doc,
   - add it as a pending slice in `project/build-plan.md`,
   - mark it out of scope with a reason.
5. Review untracked paths from `git status --short` when git exists.
6. Classify untracked paths as artifact output, local runtime state, generated output, or candidate project files.
7. Treat candidate project files as pending until they are mapped, ignored, or explicitly out of scope.
8. Check whether documented user-visible, stateful, generated, integration, background, or event-driven behavior has a traceable flow from producer to boundary crossing, optional durable state, consumer state, and output surface.
9. Do not set sync or coverage status to `current` until stable tracked paths are mapped, pending, or out of scope; untracked paths have been dispositioned; and required flow docs are completed, pending, or out of scope.
10. Record the audit source, unmapped paths, pending paths, out-of-scope paths, untracked disposition, flow trace disposition, and criteria to mark `current` in `project/build-plan.md`.

Wide parent directory mappings are useful for navigation but do not by themselves prove closure over important stable subdirectories. If a broad mapping hides a meaningful subsystem, either add a narrower directory entry, add a pending slice, or record why the parent mapping is sufficient.

### Summarize Git History

Use this when a git repository exists and history should be documented.

1. Read recent commits and relevant path history with `git log --stat`, `git log -- <path>`, and `git show --name-status`.
2. Assign commits to directories by touched paths.
3. Assign commits to modules through `manifest.yaml` directory mappings.
4. Assign commits to flows when they alter cross-boundary behavior, persistence, replay, generated output, background status, integrations, or operator/admin surfaces.
5. Create one change record per meaningful feature, fix, refactor, or behavior change.
6. Do not invent intent. Use `confidence: confirmed` only when commit messages, issues, PRs, docs, or code context clearly support the reason. Otherwise use `confidence: inferred` or `confidence: unknown`.

### Update After Feature Or Fix

Use this whenever code changes alter behavior, structure, boundaries, dependencies, or known defects.

1. Update affected module docs.
2. Update affected directory docs.
3. Update affected flow docs when the change affects cross-boundary behavior, data contracts, persistence, replay or hydration, generated output, background status, integrations, consumer state, or output surfaces.
4. Add or update change records.
5. Add or update decision records when design rationale changed.
6. Update `manifest.yaml`, `INDEX.md`, and any `changes/by-*` index that points to the new records.
7. Update `project/build-plan.md` when the task changes coverage, known gaps, pending flow slices, or next steps.
8. Run the size-check script when available.

### Develop Code With This Skill

When this skill is used during feature development, refactoring, or defect repair, treat artifact sync as part of the completion criteria.

1. Before coding, read the relevant module and directory docs if they exist.
2. Read relevant flow docs when the task affects cross-boundary behavior, durable state, generated output, replay, integration, background status, or user/operator-visible output.
3. During coding, note affected modules, directories, flows, decisions, and changes.
4. After coding and verification, update the corresponding artifact files before the final response when feasible.
5. If artifact sync is needed but cannot be completed safely in the current turn, state the pending sync clearly in the final response and include the affected modules, directories, or flows.

## Final Response Checklist

Before finishing a task that used this skill:

- State whether `.doc_project_maintainer/` exists.
- State whether the artifact was updated, was already current for the task, or still needs sync.
- If claiming the artifact is `current`, state the coverage closure audit source or why the audit was skipped.
- State whether affected cross-boundary flow docs were updated, not applicable, or still pending.
- If sync is pending, name the affected module, directory, or flow docs and the reason.
- If the project is only partially mapped, point to `project/build-plan.md` and summarize the next slice.

## Reading Strategy

Never read the whole artifact by default. Start with:

1. `.doc_project_maintainer/INDEX.md`
2. `.doc_project_maintainer/manifest.yaml`
3. The target module `README.md`
4. The target directory `README.md`
5. The relevant flow doc under `project/flows/` when tracing behavior across boundaries
6. Only the linked change or decision records that matter for the current task

If a file exceeds its size budget, split it before adding more content.

## Required References

- Read `references/artifact-structure.md` when creating the artifact, checking size budgets, choosing filenames, or wiring links.
- Read `references/templates.md` when writing `manifest.yaml`, module docs, directory docs, flow docs, change records, or decision records.

## Validation

If `.doc_project_maintainer/` exists and `scripts/check_doc_sizes.py` is available, run:

```bash
python <skill-dir>/scripts/check_doc_sizes.py <repo-root>/.doc_project_maintainer
```

Fix any reported oversized file by splitting it and updating parent indexes.

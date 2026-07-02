---
name: project-maintainer
description: Use when initializing or updating structured in-repository project-maintenance docs; exploring existing code; analyzing a full project or repository; documenting complete source symbol coverage, coverage maps, symbol audit maps, or health for every top-level function and class method; summarizing git history; or syncing docs after a feature, refactor, or bug fix.
---

# Project Maintainer

## Purpose

Maintain a structured project knowledge base inside the target repository at `.doc_project_maintainer/`. Treat the artifact as an agent-readable project map, not a long-form documentation dump.

Use four complementary views:

- Modules are the primary understanding axis: product capability, service boundary, package, subsystem, or feature area.
- Directories are the evidence axis: real paths, file ownership, tests, runtime entrypoints, and git changes.
- Cross-boundary flows are the causal axis: how user-visible output, durable state, external integration state, generated artifacts, background status, or operator/admin decisions come into existence.
- Code symbols are the executable-detail axis: every stable source file, top-level function, and method on every top-level class, each with actual behavior, detail indexes, and health assessment.

Flow docs are required when behavior crosses module, process, service, runtime, storage, protocol, or UI boundaries and affects state or output that users, operators, integrations, or future agents rely on.

Keep files small enough for selective reading. Prefer indexes, summaries, and links over repeated narrative.

## Preflight

1. Identify the target repository root.
2. Check whether `.doc_project_maintainer/` already exists.
3. If the artifact exists, read `.doc_project_maintainer/INDEX.md`, `.doc_project_maintainer/manifest.yaml`, `.doc_project_maintainer/project/build-plan.md`, `.doc_project_maintainer/project/coverage-map.json`, and `.doc_project_maintainer/project/symbol-audit-map.json` when present.
4. Assess whether the existing artifact is stale before editing code or docs:
   - Compare the current task, touched paths, git status, recent commits, and manifest mappings.
   - If the task depends on stale docs, sync the relevant artifact files before relying on them.
   - If stale docs are unrelated to the current task, record or preserve the pending sync state and remind the user at the end.
5. If starting fresh, create the artifact structure described in `references/artifact-structure.md`.
6. Load `references/templates.md` before creating or heavily revising artifact files.
7. Load `references/code-symbol-docs.md` before creating or heavily revising code symbol docs.

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
5. Inventory stable source files, top-level functions, top-level classes, and methods on top-level classes. Record any unsupported language or parser uncertainty in `project/build-plan.md`.
6. Create directory docs as evidence, module docs as interpretation, flow docs for causal behavior that crosses boundaries, and code symbol docs for every inventoried top-level function and class method when the goal is complete coverage.
7. Mark uncertain module boundaries, flow links, or symbol behavior with `confidence: inferred` and add questions to `project/open-questions.md`.
8. For large projects, create or update `project/build-plan.md` before attempting full coverage. Document what has been scanned, what is trusted, what remains, and the next suggested module, directory, flow, or code symbol slices.

### Build Large Artifacts In Slices

Use this when the project is too large to map accurately in one pass.

1. Create `project/build-plan.md` and refresh `project/coverage-map.json` plus `project/symbol-audit-map.json` with phases, scope, completed slices, pending slices, stale files, changed hashes, audit status, blocked questions, and integration notes.
2. Prefer module slices when the module boundaries are clear. Prefer directory slices when module boundaries are unknown. Prefer flow slices when the risk is causal behavior across boundaries. Prefer code symbol slices when the task requires function or method behavior and health.
3. When multi-agent tools are available, assign independent slices to agents by module, directory, flow, or code symbol scope. Give each agent only the root index, manifest, build plan, assigned paths or flow scope, and required templates.
4. Require each agent to write or propose updates only for its assigned slice and to report affected modules, directories, flows, code symbols, changes, decisions, confidence, and open questions.
5. Integrate slice outputs centrally by updating `manifest.yaml`, `INDEX.md`, cross-links, `project/coverage-map.json`, `project/symbol-audit-map.json`, and `project/build-plan.md`.
6. Keep incomplete coverage explicit. A partial but honest artifact is better than a broad artifact with invented certainty, but partial coverage is not complete for a full-repository analysis goal.
7. Before marking coverage or sync status as `current`, or before completing a full-repository analysis goal, run the coverage closure audit below and record the result in `project/build-plan.md`.

### Full Repository Analysis Goals

Use this when a user request, Codex goal, or automation asks to analyze, map, document, or cover the whole project or repository, all areas, every module or directory, complete coverage, or project-wide current state.

1. Treat full project coverage as the completion condition, not merely a planning condition.
2. Start with Explore Existing Project, then Build Large Artifacts In Slices, then continue selecting the next actionable pending slice from `project/coverage-map.json`, `project/symbol-audit-map.json`, and `project/build-plan.md` until the coverage closure audit has no actionable pending module, directory, flow, code symbol, or symbol audit slices.
3. An actionable pending slice is any stable tracked path, candidate project file, required flow, stable source file, required top-level class, required top-level function, or required class method that is not documented, not audited, audit-expired, and not explicitly out of scope with a reason.
4. Do not mark a Codex goal complete while actionable pending slices remain. If context, time, token budget, missing tools, or external blockers prevent continued work, leave the artifact `partial`, update `project/build-plan.md` with the exact next slice, and report the goal as incomplete or blocked rather than complete.
5. Use `current` only when no actionable pending slices remain. Use `partial` when known pending slices, stale areas, unclassified paths, incomplete flow traces, or incomplete code symbol slices remain. Do not use `current` just because every gap has been listed.
6. For large repositories, use multi-agent slicing when available. The coordinator still owns closure: integrate slices, re-run the audit, and continue until no actionable pending slices remain or the goal is explicitly blocked.

### Exhaustive Code Symbol Coverage

Use this for complete deliverables, full-repository analysis, project-wide `current` status, or any request where future developers should be able to query arbitrary implementation detail.

1. Every stable source file must have a file-level code doc and symbol inventory. Stable source files are tracked executable project source files, including tests, scripts, CLIs, workers, app code, library code, and tooling source, unless explicitly generated, vendored, build output, disposable local state, or out of scope with a reason.
2. Every top-level function must have a function entry doc with a functionality description in `Actual Role`, key signals, health summary fields, confidence, source path, and manifest entry.
3. Every method on every top-level class must have a method entry doc with a functionality description in `Actual Role`, key signals, health summary fields, confidence, source path, class owner, and manifest entry. Include constructors, lifecycle methods, magic or dunder methods, static methods, class methods, and private methods when they are methods of a top-level class.
4. Top-level means declared at file or module scope. Nested functions, local classes, anonymous callbacks, generated declarations, overload-only signatures, and type-only declarations do not need separate entry docs unless they are independently callable, exported, risky, or needed to explain a documented flow. Record any exclusion rule in the file-level doc or build plan.
5. Detail docs such as `actual-behavior.md`, `contracts.md`, `side-effects.md`, `health.md`, `risks.md`, and `tests.md` may still be created in slices. However, complete code symbol coverage requires at least the entry doc and health summary for every required function and method.
6. Do not mark code symbol coverage, project-wide coverage, sync status, or a full-repository goal `current` while any required source file lacks an inventory, any required top-level class, top-level function, or class method lacks an audit map record, any required top-level function or class method lacks an entry doc, or any entry doc lacks `Actual Role` and health fields.
7. If language tooling cannot reliably enumerate symbols, inspect the file manually or record the file as an actionable pending slice. Parser uncertainty never counts as `current`.

### Source Symbol Inventory

Use `scripts/inventory_symbols.py` as the single entry point for complete code symbol inventory. The script must run without external dependencies and use automatic extractor selection to choose the best available extractor.

1. Before claiming complete code symbol coverage, run:
   ```bash
   python <skill-dir>/scripts/inventory_symbols.py <repo-root> --output <repo-root>/.doc_project_maintainer/project/source-symbol-inventory.json --coverage-map-output <repo-root>/.doc_project_maintainer/project/coverage-map.json --audit-map-output <repo-root>/.doc_project_maintainer/project/symbol-audit-map.json --verify-docs
   ```
2. Treat extractor choice as automatic, not user-facing setup. The built-in priority is `python_ast`, then optional `ctags` when present, then dependency-free `heuristic` fallback.
3. Do not ask users to install optional extractors as a prerequisite. If an enhanced extractor is unavailable, continue with the fallback, record the extractor and confidence in `source-symbol-inventory.json`, and keep low-confidence files actionable.
4. A file inventoried with `heuristic`, `unknown`, parser warnings, or `requires_review: true` can be used to scaffold docs, but it cannot support `current` until manually reviewed, re-run with a stronger extractor, or marked out of scope with a reason.
5. Use file hashes from the inventory to focus later runs on changed files and symbols. Do not rescan or rewrite stable symbol docs just because the full inventory command was re-run.
6. When `--verify-docs` reports missing entry docs, missing `Actual Role`, missing health fields, `unaudited`, or `audit_expired` symbol audit records, record those items as actionable pending code symbol slices.

### Coverage Map And Subagent Coordination

Use `project/coverage-map.json` as the machine-readable progress ledger for full-project analysis and complete code symbol coverage.

1. Generate or refresh `project/coverage-map.json` in the same command that generates `project/source-symbol-inventory.json`.
2. Treat file statuses as operational state:
   - `documented`: current source hash, sufficient extractor confidence, file doc present, and required function or method docs include `Actual Role` plus health.
   - `pending`: required file, function, method, `Actual Role`, or health docs are missing.
   - `stale`: the source hash changed since the previous coverage map.
   - `pending_review`: extractor confidence, parser warnings, or unsupported language handling needs manual review.
   - `not_checked`: docs were not verified in this run.
3. Use git data from the coverage map to decide work:
   - `git.head` records the scanned commit.
   - `git.status_short` records dirty worktree state.
   - `git.untracked_candidate_source_files` must be classified as project source, generated/local state, ignored, or out of scope.
4. Use multi-agent slicing when more than 20 stable source files, more than 80 required symbols, or any module slice with more than 40 symbols is pending or stale. If multi-agent tools are unavailable, continue serially by `suggested_slices` and keep coverage `partial`.
5. Coordinator owns closure. The Coordinator assigns `suggested_slices`, gives each subagent only its assigned source paths and required templates, prevents overlapping edits, integrates outputs into `manifest.yaml`, `INDEX.md`, code docs, flow docs, `project/coverage-map.json`, and `project/build-plan.md`, then reruns the inventory command.
6. Subagents must report affected files, functions, class methods, modules, directories, flows, health status, tests, confidence, blockers, and any out-of-scope proposal for their assigned slice only.
7. Do not mark a full-repository goal complete while `coverage-map.json` contains pending, stale, pending_review, not_checked, removed, or candidate project file work that has not been documented, reviewed, removed from the artifact, or explicitly dispositioned.

### Symbol Audit Map

Use `project/symbol-audit-map.json` as the machine-readable audit ledger for every discovered top-level class, top-level function, and method on a top-level class.

1. Generate or refresh `project/symbol-audit-map.json` in the same command that generates the inventory and coverage map.
2. Treat `audit.status` as the audit state:
   - `unaudited`: no agent or human has reviewed the symbol behavior, health, and issues.
   - `agent_audited`: an agent reviewed the symbol and recorded health plus issues with evidence.
   - `human_audited`: a human reviewed or confirmed the symbol and recorded health plus issues with evidence.
   - `audit_expired`: the symbol was audited, but current source hash differs from the audited source hash.
   - `out_of_scope`: the symbol is intentionally excluded with a reason.
3. Record health as a fixed-dimension snapshot: `overall`, `name_behavior_match`, `responsibility_focus`, `length`, `complexity`, `implementation_soundness`, `input_contract`, `output_contract`, `boundary_safety`, `side_effects`, `state_mutation`, `error_handling`, `dependency_coupling`, `test_coverage`, `observability`, and `performance_risk`.
4. Record concrete findings in `issues[]`; each issue needs `dimension`, `severity`, `status`, `summary`, `evidence`, and `suggested_action`. Health dimensions classify the risk; issues explain the evidence.
5. Preserve previous `agent_audited` or `human_audited` records when the current source hash still matches `audited_source_hash`.
6. Automatically treat a previously audited symbol as `audit_expired` when the source hash changes. Do not silently keep old health or issues as current.
7. Do not mark complete symbol coverage or a full-repository goal `current` while required symbols remain `unaudited` or `audit_expired`, unless they are explicitly `out_of_scope` with a reason.

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
3. Compare those directories against `manifest.yaml` directory mappings, completed slices, out-of-scope dispositions, and documented pending slices.
4. For each unmapped stable tracked path, choose exactly one disposition:
   - add or update a module and directory doc,
   - add it as an actionable pending slice in `project/build-plan.md` and keep coverage `partial`,
   - mark it out of scope with a reason.
5. Review untracked paths from `git status --short` when git exists.
6. Classify untracked paths as artifact output, local runtime state, generated output, or candidate project files.
7. Treat candidate project files as pending until they are mapped, ignored, or explicitly out of scope.
8. Check whether documented user-visible, stateful, generated, integration, background, or event-driven behavior has a traceable flow from producer to boundary crossing, optional durable state, consumer state, and output surface.
9. Run `scripts/inventory_symbols.py` with `--verify-docs`, `--coverage-map-output`, and `--audit-map-output`. Check whether every stable source file has a file-level code doc and symbol inventory, every top-level class, top-level function, and method on every top-level class has a symbol audit map record, every top-level function has an entry doc with `Actual Role` and health fields, every method on every top-level class has an entry doc with `Actual Role` and health fields, `project/coverage-map.json` has no actionable pending, stale, pending_review, not_checked, removed, or candidate project file work, and `project/symbol-audit-map.json` has no required `unaudited` or `audit_expired` symbols.
10. Do not set sync or coverage status to `current` while any actionable pending slice remains. Stable tracked paths must be mapped or out of scope; untracked paths must be dispositioned; required flow docs must be completed or out of scope; and every required code symbol doc must be completed or out of scope.
11. Record the audit source, unmapped paths, actionable pending slices, out-of-scope paths, untracked disposition, flow trace disposition, code symbol disposition, symbol audit disposition, undocumented source files, unaudited or audit-expired top-level classes, undocumented or unaudited top-level functions, undocumented or unaudited class methods, and criteria to mark `current` in `project/build-plan.md`.

Wide parent directory mappings are useful for navigation but do not by themselves prove closure over important stable subdirectories. If a broad mapping hides a meaningful subsystem, either add a narrower directory entry, add a pending slice, or record why the parent mapping is sufficient.

### Summarize Git History

Use this when a git repository exists and history should be documented.

1. Read recent commits and relevant path history with `git log --stat`, `git log -- <path>`, and `git show --name-status`.
2. Assign commits to directories by touched paths.
3. Assign commits to modules through `manifest.yaml` directory mappings.
4. Assign commits to flows when they alter cross-boundary behavior, persistence, replay, generated output, background status, integrations, or operator/admin surfaces.
5. Assign commits to code symbols when they alter source files, classes, functions, methods, behavior, contracts, health, or tests.
6. Create one change record per meaningful feature, fix, refactor, or behavior change.
7. Do not invent intent. Use `confidence: confirmed` only when commit messages, issues, PRs, docs, or code context clearly support the reason. Otherwise use `confidence: inferred` or `confidence: unknown`.

### Update After Feature Or Fix

Use this whenever code changes alter behavior, structure, boundaries, dependencies, or known defects.

1. Update affected module docs.
2. Update affected directory docs.
3. Update affected flow docs when the change affects cross-boundary behavior, data contracts, persistence, replay or hydration, generated output, background status, integrations, consumer state, or output surfaces.
4. Update affected code symbol docs and function or method health when the change touches source files, classes, functions, methods, contracts, side effects, risks, or tests.
5. Add or update change records.
6. Add or update decision records when design rationale changed.
7. Update `manifest.yaml`, `INDEX.md`, and any `changes/by-*` index that points to the new records.
8. Update `project/build-plan.md` when the task changes coverage, known gaps, pending flow slices, pending code symbol slices, or next steps.
9. Run the size-check script when available.

### Develop Code With This Skill

When this skill is used during feature development, refactoring, or defect repair, treat artifact sync as part of the completion criteria.

1. Before coding, read the relevant module and directory docs if they exist.
2. Read relevant flow docs when the task affects cross-boundary behavior, durable state, generated output, replay, integration, background status, or user/operator-visible output.
3. Read relevant code symbol docs when editing or calling documented source files, classes, functions, or methods.
4. During coding, note affected modules, directories, flows, code symbols, decisions, and changes.
5. After coding and verification, update the corresponding artifact files before the final response when feasible.
6. If artifact sync is needed but cannot be completed safely in the current turn, state the pending sync clearly in the final response and include the affected modules, directories, flows, or code symbols.

## Final Response Checklist

Before finishing a task that used this skill:

- State whether `.doc_project_maintainer/` exists.
- State whether the artifact was updated, was already current for the task, or still needs sync.
- If claiming the artifact is `current`, state the coverage closure audit source or why the audit was skipped.
- State whether affected cross-boundary flow docs were updated, not applicable, or still pending.
- State whether affected code symbol docs and function or method health were updated, not applicable, or still pending.
- For complete or full-repository deliverables, state whether every stable source file has a symbol inventory and whether every top-level function and class method has an entry doc with `Actual Role` and health.
- For complete or full-repository deliverables, state the `coverage-map.json` summary, recommended mode, and whether any suggested slices remain.
- For complete or full-repository deliverables, state the `symbol-audit-map.json` summary, including unaudited, agent_audited, human_audited, audit_expired, out_of_scope, and open issue counts.
- If sync is pending, name the affected module, directory, flow, or code symbol docs and the reason.
- If the project is only partially mapped, point to `project/build-plan.md` and summarize the next slice.
- If the task was a full-repository analysis goal, state whether actionable pending slices remain. Do not describe the goal as complete unless none remain.

## Reading Strategy

For scoped maintenance tasks, never read the whole artifact by default. Full-repository analysis goals are the exception: use indexes, the manifest, and the build plan to drive slice-by-slice coverage, then read each required slice as needed. Start with:

1. `.doc_project_maintainer/INDEX.md`
2. `.doc_project_maintainer/manifest.yaml`
3. The target module `README.md`
4. The target directory `README.md`
5. The target code symbol entry doc under `code/` when working on a source file, class, function, or method
6. The relevant linked code symbol detail docs only when the summary is insufficient
7. The relevant flow doc under `project/flows/` when tracing behavior across boundaries
8. Only the linked change or decision records that matter for the current task

If a file exceeds its size budget, split it before adding more content.

## Required References

- Read `references/artifact-structure.md` when creating the artifact, checking size budgets, choosing filenames, or wiring links.
- Read `references/templates.md` when writing `manifest.yaml`, module docs, directory docs, flow docs, change records, or decision records.
- Read `references/code-symbol-docs.md` when creating or updating code symbol docs, function or method entry docs, detail docs, health assessment, or code symbol coverage state.

## Validation

If `.doc_project_maintainer/` exists and `scripts/check_doc_sizes.py` is available, run:

```bash
python <skill-dir>/scripts/check_doc_sizes.py <repo-root>/.doc_project_maintainer
```

Fix any reported oversized file by splitting it and updating parent indexes.

For complete or full-repository deliverables, also run `scripts/inventory_symbols.py` with `--verify-docs`, `--coverage-map-output`, and `--audit-map-output`. Treat any missing docs, missing health, missing `Actual Role`, `requires_review` files, `unaudited` symbols, or `audit_expired` symbols as pending work, not success.

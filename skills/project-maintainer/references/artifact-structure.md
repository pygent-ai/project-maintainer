# Project Maintainer Artifact Structure

Create the delivery artifact at the target repository root:

```text
.doc_project_maintainer/
  README.md
  INDEX.md
  manifest.yaml
  project/
    overview.md
    architecture.md
    glossary.md
    build-plan.md
    open-questions.md
    flows/
      <flow-id>.md
  modules/
    <module-id>/
      README.md
      design.md
      directories.md
      dependencies.md
      changes.md
      git-history.md
  directories/
    <encoded-path>/
      README.md
      files.md
      module-links.md
      changes.md
  decisions/
    ADR-0001-short-slug.md
  changes/
    records/
      CHG-YYYYMMDD-NNN-short-slug.md
    by-module/
      <module-id>.md
    by-directory/
      <encoded-path>.md
```

## Required Root Files

- `README.md`: Project brief, current documentation status, technical stack, startup/test hints, and maintenance rules.
- `INDEX.md`: Human and agent navigation for modules, directories, flows, changes, and decisions. Keep this as links and one-line summaries only.
- `manifest.yaml`: Machine-readable relationship graph for modules, directories, flows, changes, and decisions.
- `project/build-plan.md`: Coverage plan for large or partially mapped projects. Track completed slices, pending slices, stale areas, pending flow slices, coverage closure audit results, and suggested next work.

## Size Budgets

Use byte size as the enforceable limit. Token count varies by language and content type.

- `INDEX.md`: 5 KB
- root `README.md`: 8 KB
- `manifest.yaml`: 20 KB
- `project/*.md`: 8 KB each
- `project/flows/*.md`: 8 KB each
- `modules/*/README.md`: 8 KB
- `modules/*/*.md`: 8 KB each
- `directories/*/README.md`: 6 KB
- `directories/*/*.md`: 6 KB each
- `changes/records/*.md`: 6 KB each
- `changes/by-*/*.md`: 10 KB each
- `decisions/*.md`: 6 KB each

When a file exceeds budget, split by topic, time period, or submodule. Leave a short summary and links in the parent file.

## Naming

Use stable IDs for records:

- Changes: `CHG-YYYYMMDD-NNN-short-slug.md`
- Decisions: `ADR-NNNN-short-slug.md`
- Modules: lowercase kebab-case IDs
- Flows: lowercase kebab-case IDs that name the causal behavior, stored as `project/flows/<flow-id>.md`
- Encoded paths: replace path separators with double underscores

Use semantic filenames for change records. Do not use date-only filenames because agents cannot infer relevance from them.

## Linking Model

Use three link layers:

1. Markdown links for humans.
2. YAML frontmatter in each record for stable IDs and relationships.
3. `manifest.yaml` as the central relationship graph.

Modules link to:

- owning directories
- related flows
- related changes
- related decisions
- tests and verification commands

Directories link to:

- mapped modules
- related flows
- notable files
- related changes
- related decisions

Flows link to:

- affected modules
- affected directories
- source-of-truth, cache, generated, telemetry, debug, fixture, transient, or local-state paths when applicable
- entrypoints, producers, consumers, output surfaces, and verification commands
- related changes and decisions

Changes link to:

- affected modules
- affected directories
- affected flows
- decisions that explain the change
- commits when git data exists

Decisions link to:

- affected modules
- affected directories
- affected flows
- changes that implemented or revised the decision

## Sync And Coverage State

Every existing artifact needs a preflight sync assessment before use. Store durable state in `manifest.yaml` and human-readable status in `project/build-plan.md`.

Track at least:

- artifact version
- last artifact update date
- last scanned commit when git exists
- last synced commit when git exists
- sync status: `current`, `partial`, `stale`, or `unknown`
- coverage status by module, directory, and flow
- coverage closure audit status, source, and last audit date
- pending sync items with affected paths, modules, directories, flows, and reason

Use `project/build-plan.md` for large projects, partial migrations, and multi-agent work. Keep it short and operational: what is done, what is trusted, what remains, what is blocked, and what module, directory, or flow slice should be built next.

Only use `current` for project-wide sync or coverage status after a coverage closure audit has run or an explicit skip reason has been recorded. For git repositories, the audit source should be `git ls-files` plus `git status --short`. For non-git repositories, record the substitute listing source. The audit proves directory/module coverage, not exhaustive file-level documentation.

Before marking project-wide coverage `current`, every stable tracked path must be one of:

- mapped to a module or directory entry,
- recorded as a pending slice,
- marked out of scope with a reason.

Untracked paths must be classified as artifact output, local runtime state, generated output, or candidate project files. Candidate project files keep coverage partial until they are mapped, ignored, or marked out of scope. Generated, cache, runtime, session, coverage-report, virtual-environment, and local-state paths should be excluded intentionally rather than silently omitted.

Before marking flow coverage `current`, every documented user-visible, stateful, generated, integration, background, or event-driven behavior must have a completed flow doc, a pending flow slice, or an explicit out-of-scope reason. Flow coverage proves causal traceability, not exhaustive line-level behavior.

Status meanings:

- `planned`: Documentation structure or coverage is intended but not yet created.
- `partial`: Some stable areas are mapped, but known gaps, pending slices, stale areas, or unclassified paths remain.
- `scanned`: A directory or slice has been inspected and has evidence, but project-wide closure is not implied.
- `current`: The artifact is synced to the recorded source and stable tracked paths are mapped, pending, or out of scope.
- `stale`: The artifact is known to lag behind code, docs, git history, or project structure.
- `unknown`: The artifact has not been assessed.

When multiple agents work on the artifact, split work by module or directory. Do not let agents edit the same module or directory doc concurrently unless a coordinator merges the outputs.

## Confidence Rules

Use one of:

- `confirmed`: Supported by code, tests, docs, commit messages, PRs, or issues.
- `inferred`: Reasonable interpretation from structure or code behavior.
- `unknown`: Evidence is insufficient.

Never present inferred rationale as fact.

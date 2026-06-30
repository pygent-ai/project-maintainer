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
- `INDEX.md`: Human and agent navigation. Keep this as links and one-line summaries only.
- `manifest.yaml`: Machine-readable relationship graph for modules, directories, changes, and decisions.
- `project/build-plan.md`: Coverage plan for large or partially mapped projects. Track completed slices, pending slices, stale areas, and suggested next work.

## Size Budgets

Use byte size as the enforceable limit. Token count varies by language and content type.

- `INDEX.md`: 5 KB
- root `README.md`: 8 KB
- `manifest.yaml`: 20 KB
- `project/*.md`: 8 KB each
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
- Modules: lowercase kebab-case IDs such as `gateway`, `skill-retrieval`, `web-channel`
- Encoded paths: replace path separators with double underscores, for example `jiuwenswarm__gateway`

Use semantic filenames for change records. Do not use date-only filenames because agents cannot infer relevance from them.

## Linking Model

Use three link layers:

1. Markdown links for humans.
2. YAML frontmatter in each record for stable IDs and relationships.
3. `manifest.yaml` as the central relationship graph.

Modules link to:

- owning directories
- related changes
- related decisions
- tests and verification commands

Directories link to:

- mapped modules
- notable files
- related changes
- related decisions

Changes link to:

- affected modules
- affected directories
- decisions that explain the change
- commits when git data exists

Decisions link to:

- affected modules
- affected directories
- changes that implemented or revised the decision

## Sync And Coverage State

Every existing artifact needs a preflight sync assessment before use. Store durable state in `manifest.yaml` and human-readable status in `project/build-plan.md`.

Track at least:

- artifact version
- last artifact update date
- last scanned commit when git exists
- last synced commit when git exists
- sync status: `current`, `partial`, `stale`, or `unknown`
- coverage status by module and directory
- pending sync items with affected paths and reason

Use `project/build-plan.md` for large projects, partial migrations, and multi-agent work. Keep it short and operational: what is done, what is trusted, what remains, what is blocked, and what slice should be built next.

When multiple agents work on the artifact, split work by module or directory. Do not let agents edit the same module or directory doc concurrently unless a coordinator merges the outputs.

## Confidence Rules

Use one of:

- `confirmed`: Supported by code, tests, docs, commit messages, PRs, or issues.
- `inferred`: Reasonable interpretation from structure or code behavior.
- `unknown`: Evidence is insufficient.

Never present inferred rationale as fact.

# Code Symbol Documentation

Use code symbol docs when a task requires source-level understanding, function or method health review, or post-change artifact sync for touched code.

Code symbol docs are the executable-detail view of the project. They mirror source paths and symbol ownership so the artifact tree itself explains where a file, class, function, or method lives. File and directory names are documentation signals. Do not hide primary symbol identity behind generic `README.md` files.

## Complete Deliverable Requirements

A complete project-maintainer deliverable must let a future developer query any stable source-level detail without first rediscovering the codebase.

For complete coverage or project-wide `current` status:

- Every stable source file must have a file-level doc and symbol inventory.
- Every top-level function must have an entry doc.
- Every method on every top-level class must have an entry doc.
- Each function or method entry doc must include `Actual Role`, `Key Signals`, a complete health summary, source metadata, confidence, and manifest linkage.
- Do not mark code symbol coverage `current` while any stable source file lacks an inventory, any top-level function lacks an entry doc, any class method lacks an entry doc, or any required entry doc lacks `Actual Role` or health fields.

Stable source files include tracked executable project source such as app code, library code, tests, scripts, CLIs, workers, and tooling source. Exclude generated files, vendored files, build output, disposable local state, and unsupported files only with explicit out-of-scope reasons.

Top-level means declared at file or module scope. Document methods on top-level classes, including constructors, lifecycle methods, magic or dunder methods, static methods, class methods, and private methods. Nested functions, local classes, anonymous callbacks, generated declarations, overload-only signatures, and type-only declarations do not need separate entry docs unless they are independently callable, exported, risky, or needed for a documented flow.

## Inventory Script

Use `scripts/inventory_symbols.py` as the single entry point for source symbol discovery. It must run on a plain Python environment with no external dependency. Optional extractors are enhancements, not prerequisites.

Run it before claiming complete code symbol coverage:

```bash
python <skill-dir>/scripts/inventory_symbols.py <repo-root> --output <repo-root>/.doc_project_maintainer/project/source-symbol-inventory.json --coverage-map-output <repo-root>/.doc_project_maintainer/project/coverage-map.json --verify-docs
```

Extractor behavior:

- `python_ast`: built-in Python AST extractor for `.py` files; confirmed confidence when parsing succeeds.
- `ctags`: optional enhanced extractor when `ctags` is available on `PATH`; used automatically for non-Python files.
- `heuristic`: dependency-free fallback for common source languages; useful for scaffolding but requires manual review before `current`.

The inventory records each file's extractor, confidence, hash, symbols, warnings, and doc verification status. The coverage map records git head, dirty worktree state, untracked candidate source files, stale hashes, per-file status, per-symbol doc status, removed files, and suggested slices. Treat `heuristic`, `unknown`, parser warnings, `requires_review: true`, missing file docs, missing entry docs, missing `Actual Role`, missing health, stale files, removed files, and untracked candidate project files as actionable pending code symbol slices. These states can move work forward but keep coverage `partial`.

Use the recorded file hashes in `coverage-map.json` to focus future passes on changed files and newly discovered symbols. For large first scans, assign work from `suggested_slices`; the coordinator must merge outputs, rerun the inventory command, and keep coverage `partial` until no pending, stale, pending_review, or not_checked files remain.

## Structure

Create code symbol docs under `.doc_project_maintainer/code/` by mirroring the source-relative path:

```text
.doc_project_maintainer/code/
  src/
    foo/
      a.py/
        a.py.md
        Class A/
          Class A.md
          A.a.md
          A.a/
            actual-behavior.md
            contracts.md
            side-effects.md
            health.md
            risks.md
            tests.md
        B.md
        B/
          actual-behavior.md
          contracts.md
          side-effects.md
          health.md
          risks.md
          tests.md
```

For source:

```python
class A:
    def a(self):
        ...

def B():
    ...
```

Create:

- `a.py/a.py.md` for file-level role and symbol index.
- `a.py/Class A/Class A.md` for class-level role, state, lifecycle, and method index.
- `a.py/Class A/A.a.md` for method entry documentation.
- `a.py/Class A/A.a/` for method detail documents.
- `a.py/B.md` for module-level function entry documentation.
- `a.py/B/` for module-level function detail documents.

## Naming Rules

- Preserve the source-relative directory path below `code/`.
- Represent each source file as a directory named exactly like the source file, such as `a.py/`, `UserService.ts/`, or `main.go/`.
- Name the file-level document `<file-name>.md`, such as `a.py.md`.
- Represent classes, structs, traits, interfaces, and comparable type containers as directories using `<Kind> <Name>/`, such as `Class A/`, `Struct User/`, or `Interface Store/`.
- Name the class-level document `<Kind> <Name>.md`, such as `Class A.md`.
- Name methods `<Owner>.<method>.md`, such as `A.a.md`.
- Name module-level functions `<function>.md`, such as `B.md`.
- Give every function or method with expanded detail docs a sibling directory with the same symbol name, such as `A.a/` or `B/`.
- If a language allows overloads or duplicate local symbols, keep the symbolic prefix and append the smallest stable disambiguator, such as `Parser.parse__arity2.md` or `parse__line42.md`.
- If a source symbol contains characters that cannot be used in a file name, use the closest readable safe name and store the exact symbol in YAML frontmatter.

Do not use `README.md` inside `code/`. Do not create generic `functions.md` inventories as the main deliverable.

## Function Or Method Entry Docs

The entry document is a compact symbol card. It must help an agent decide whether to read details or inspect source. Keep it focused on evidence and navigation.

Include only:

- YAML frontmatter with stable symbol metadata, summarized health, confidence, and links to detail docs.
- `Actual Role`: one to three sentences describing what the function actually does based on the body.
- `Key Signals`: compact bullets for input, output, side effects, primary risk, and related tests.
- `Detail Index`: links to detail docs that exist or are intentionally pending.

Do not include:

- `Read When` sections.
- Generic `Overview` sections.
- Purpose text that only rephrases the function name.
- Empty headings.
- Notes without evidence.
- Field explanations duplicated from frontmatter.

Never write `Actual Role` from the function name alone. Read the implementation first. Use `confidence: confirmed` only when the behavior is supported by code, tests, docs, or commit evidence. Use `confidence: inferred` or `unknown` when the body or call paths are not fully traced.

## Detail Docs

Create detail docs only when the information is needed for the current slice, touched code, risky behavior, or requested coverage. If detail is not yet documented, leave the target out of `Detail Index` or add a short `pending_details` list in frontmatter. Detail docs can be pending while entry-doc coverage is complete; entry docs with `Actual Role` and health cannot be pending for `current`.

Use these detail docs:

- `actual-behavior.md`: real execution path, important branches, and behavior not obvious from the name.
- `contracts.md`: parameters, accepted ranges, return values, exceptions, preconditions, postconditions, and compatibility promises.
- `side-effects.md`: file, database, network, cache, event, global state, mutable argument, process, or UI state mutations.
- `health.md`: full health assessment, score rationale, and evidence.
- `risks.md`: boundary, permission, race, nullability, overflow, resource, ordering, identity, retry, idempotency, and finalization risks.
- `tests.md`: direct tests, indirect tests, missing tests, boundary cases, failure cases, and suggested verification commands.

Each detail doc should be narrow. Split again only if it exceeds the size budget.

## Health Summary Fields

Every function or method entry doc must include a compact health summary:

```yaml
health:
  overall: healthy | watch | risky | critical | unknown
  name_behavior_match: good | partial | mismatch | unknown
  responsibility_focus: single | mixed | overloaded | unknown
  length: short | medium | long | excessive | unknown
  complexity: low | medium | high | excessive | unknown
  boundary_safety: safe | partial | risky | unknown
  input_contract: clear | implicit | weak | unknown
  output_contract: clear | implicit | weak | unknown
  side_effects: none | explicit | implicit | hidden | unknown
  error_handling: clear | partial | missing | unknown
  state_mutation: none | isolated | shared | global | unknown
  dependency_coupling: low | medium | high | unknown
  test_coverage: covered | partial | missing | unknown
  observability: clear | partial | missing | not_applicable | unknown
  performance_risk: low | medium | high | unknown
```

Use `overall` as the decision summary:

- `healthy`: clear role, low risk, adequate tests or simple pure behavior.
- `watch`: usable but has gaps such as implicit contracts, partial tests, or moderate complexity.
- `risky`: likely maintenance or runtime risk due to unclear behavior, weak boundaries, missing tests, hidden side effects, or high coupling.
- `critical`: evidence of likely defects, unsafe boundary behavior, dangerous side effects, or severe mismatch between name and behavior.
- `unknown`: insufficient evidence.

## Health Assessment Guidance

Evaluate at least these dimensions:

- Actual behavior: what the function really does after reading its body and key callees.
- Name and behavior match: whether the name accurately describes the observed behavior.
- Responsibility focus: whether it does one coherent job or mixes parsing, validation, persistence, IO, rendering, orchestration, and policy.
- Length: short enough to understand locally, or long enough to hide branches and state.
- Complexity: branching, nesting, loops, recursion, early returns, exception paths, async paths, or state machines.
- Boundary safety: null/none checks, indexes, pagination, path traversal, permissions, numeric ranges, date ranges, concurrency, retry, idempotency, timeouts, resource cleanup, and external contracts.
- Input and output contracts: whether callers can know valid inputs, outputs, and failure behavior.
- Side effects: whether mutations and external effects are explicit and isolated.
- Error handling: whether errors are swallowed, normalized, propagated, retried, or leave partial state.
- State mutation: whether state changes are local, shared, global, durable, cached, or derived.
- Dependency coupling: whether the symbol depends on hidden context, global state, concrete services, or broad modules.
- Test coverage: direct tests, boundary tests, failure tests, and indirect flow coverage.
- Observability: whether important failures, background work, generated outputs, or operator-visible behavior have logs or status.
- Performance and resource risk: loops over large data, recursion, repeated IO, unbounded memory, missing pagination, leaked handles, and avoidable recomputation.

## Coverage Modes

Use scope-aware coverage:

- During project initialization or exploration, document code symbols by slices. Record every uncovered stable source file, top-level function, and class method in `project/build-plan.md`.
- During feature, refactor, or bug-fix work, update only touched symbols and directly affected high-risk callers or callees unless the user asks for broader coverage.
- Run `scripts/inventory_symbols.py` to generate or refresh `project/source-symbol-inventory.json` and `project/coverage-map.json` before claiming complete source symbol coverage.
- For large projects, keep code symbol coverage `partial` until every stable source file has an inventory and every top-level function and class method has an entry doc with health, or is explicitly out of scope.
- Do not mark code symbol coverage `current` unless every stable source file, every top-level function, and every class method is documented or explicitly out of scope through a coverage closure audit. Pending symbol slices keep coverage `partial`.

Prioritize:

- exported or public APIs,
- command, route, handler, worker, scheduler, and UI entrypoints,
- persistence, permissions, file, network, generated artifact, background status, and integration code,
- changed functions and methods,
- high-complexity or low-test symbols,
- symbols participating in documented cross-boundary flows.

## Template

Use this entry doc template for functions and methods:

```markdown
---
symbol: A.a
kind: method
source: src/foo/a.py
class: A
signature: "a(x, y)"
health:
  overall: watch
  name_behavior_match: partial
  responsibility_focus: mixed
  length: medium
  complexity: medium
  boundary_safety: partial
  input_contract: implicit
  output_contract: clear
  side_effects: explicit
  error_handling: partial
  state_mutation: shared
  dependency_coupling: medium
  test_coverage: partial
  observability: not_applicable
  performance_risk: low
confidence: inferred
details:
  actual_behavior: A.a/actual-behavior.md
  contracts: A.a/contracts.md
  side_effects: A.a/side-effects.md
  health: A.a/health.md
  risks: A.a/risks.md
  tests: A.a/tests.md
---

# A.a

## Actual Role

One to three sentences describing what the method actually does, based on the implementation.

## Key Signals

- Input:
- Output:
- Main side effects:
- Main risk:
- Related tests:

## Detail Index

- [Actual Behavior](A.a/actual-behavior.md)
- [Contracts](A.a/contracts.md)
- [Side Effects](A.a/side-effects.md)
- [Health](A.a/health.md)
- [Risks](A.a/risks.md)
- [Tests](A.a/tests.md)
```

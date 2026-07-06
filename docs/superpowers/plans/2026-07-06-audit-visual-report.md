# Audit Visual Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a static, self-contained HTML audit report generator for Project Maintainer.

**Architecture:** Add one dependency-free Python script, `skills/project-maintainer/scripts/render_audit_report.py`, that reads existing Project Maintainer JSON ledgers, refreshes audit integrity trust data through `audit_integrity.py report`, normalizes records into a report model, and writes one HTML file with embedded data, CSS, and JavaScript. Keep audit logic unchanged; the new script is a read-only renderer plus integrity-report caller.

**Tech Stack:** Python standard library (`argparse`, `json`, `html`, `subprocess`, `datetime`, `pathlib`, `typing`, `shutil`, `zipfile`), existing `pytest`/`unittest` tests, static HTML/CSS/JavaScript.

---

## File Structure

- Create `skills/project-maintainer/scripts/render_audit_report.py`
  - CLI entrypoint.
  - Loads coverage and audit maps.
  - Runs `audit_integrity.py report` unless `--skip-integrity-refresh` is set.
  - Builds overview, priority, scope tree, and table data.
  - Renders self-contained HTML.

- Create `tests/test_render_audit_report.py`
  - Temporary-project tests for missing input, static HTML generation, integrity refresh success/failure, priority ordering, embedded filters, and escaping.

- Modify `tests/test_skill_contract.py`
  - Add contract tests requiring `SKILL.md`, README, and agent prompt coverage for the report workflow and stale-report warning.

- Modify `README.md`
  - Add `render_audit_report.py` to contents.
  - Add report capability and usage examples.

- Modify `skills/project-maintainer/SKILL.md`
  - Add audit visualization report workflow.
  - Add final-response/staleness guidance: when data refreshes after report generation, tell the user to regenerate or refresh the HTML.

- Modify `skills/project-maintainer/agents/openai.yaml`
  - Mention report generation and stale-report warning in the default prompt.

- Modify `skills/project-maintainer/VERSION` and `skills/project-maintainer/metadata.yaml`
  - Bump version from `0.0.7` to `0.0.8`.

- Modify `skills/project-maintainer.zip`
  - Rebuild archive so the packaged skill contains the new script and docs.

---

### Task 1: CLI Skeleton And Required Map Failures

**Files:**
- Create: `tests/test_render_audit_report.py`
- Create: `skills/project-maintainer/scripts/render_audit_report.py`

- [ ] **Step 1: Write the failing missing-map test**

Add this initial test file:

```python
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_SCRIPT = REPO_ROOT / "skills" / "project-maintainer" / "scripts" / "render_audit_report.py"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_report(project: Path, *args: str, key: str | None = "test-secret") -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if key is None:
        env.pop("PROJECT_MAINTAINER_AUDIT_SIGNING_KEY", None)
    else:
        env["PROJECT_MAINTAINER_AUDIT_SIGNING_KEY"] = key
    return subprocess.run(
        [sys.executable, str(REPORT_SCRIPT), str(project), *args],
        cwd=project,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


class AuditReportRenderingTests(unittest.TestCase):
    def test_missing_project_maps_fail_without_writing_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            output = project / ".doc_project_maintainer" / "project" / "audit-report.html"

            result = run_report(project, "--output", str(output), "--skip-integrity-refresh")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("coverage-map.json not found", result.stderr)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python -m pytest tests/test_render_audit_report.py::AuditReportRenderingTests::test_missing_project_maps_fail_without_writing_report -q
```

Expected: FAIL because `render_audit_report.py` does not exist or does not emit the required message.

- [ ] **Step 3: Add the minimal CLI implementation**

Create `skills/project-maintainer/scripts/render_audit_report.py`:

```python
#!/usr/bin/env python3
"""Render a self-contained Project Maintainer audit visualization report."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any


DEFAULT_ARTIFACT_ROOT = ".doc_project_maintainer"
DEFAULT_SCOPE = "default_health_audit"
ALL_SCOPE = "all"


class AuditReportError(Exception):
    """Expected user-facing report generation error."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise AuditReportError(f"{label} not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise AuditReportError(f"Invalid JSON in {label}: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise AuditReportError(f"Expected JSON object in {label}: {path}")
    return data


def resolve_paths(args: argparse.Namespace) -> dict[str, Path]:
    repo_root = args.repo_root.resolve()
    artifact_root = (args.artifact_root or (repo_root / DEFAULT_ARTIFACT_ROOT)).resolve()
    project_root = artifact_root / "project"
    return {
        "repo_root": repo_root,
        "artifact_root": artifact_root,
        "coverage_map": (args.coverage_map or (project_root / "coverage-map.json")).resolve(),
        "audit_map": (args.audit_map or (project_root / "symbol-audit-map.json")).resolve(),
        "integrity_report": (args.integrity_report_output or (project_root / "audit-integrity-report.json")).resolve(),
        "output": (args.output or (project_root / "audit-report.html")).resolve(),
    }


def render_minimal_html(*, generated_at: str) -> str:
    return (
        "<!doctype html>\n"
        "<html><head><meta charset=\"utf-8\"><title>Project Maintainer Audit Report</title></head>"
        "<body><h1>Project Maintainer Audit Report</h1>"
        f"<p>Generated at {generated_at}</p>"
        "</body></html>\n"
    )


def generate_report(args: argparse.Namespace) -> Path:
    paths = resolve_paths(args)
    read_json(paths["coverage_map"], "coverage-map.json")
    read_json(paths["audit_map"], "symbol-audit-map.json")
    html = render_minimal_html(generated_at=utc_now())
    paths["output"].parent.mkdir(parents=True, exist_ok=True)
    paths["output"].write_text(html, encoding="utf-8")
    return paths["output"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_root", type=Path)
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--coverage-map", type=Path)
    parser.add_argument("--audit-map", type=Path)
    parser.add_argument("--integrity-report-output", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--scope", choices=(DEFAULT_SCOPE, ALL_SCOPE), default=DEFAULT_SCOPE)
    parser.add_argument("--skip-integrity-refresh", action="store_true")
    parser.add_argument("--signing-key-env", default="PROJECT_MAINTAINER_AUDIT_SIGNING_KEY")
    parser.add_argument("--batch-reuse-threshold", type=int, default=1)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        output = generate_report(args)
    except AuditReportError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps({"output": str(output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
python -m pytest tests/test_render_audit_report.py::AuditReportRenderingTests::test_missing_project_maps_fail_without_writing_report -q
```

Expected: PASS.

- [ ] **Step 5: Commit Task 1**

Run:

```bash
git add tests/test_render_audit_report.py skills/project-maintainer/scripts/render_audit_report.py
git commit -m "feat: add audit report generator skeleton"
```

---

### Task 2: Self-Contained HTML From Coverage And Audit Maps

**Files:**
- Modify: `tests/test_render_audit_report.py`
- Modify: `skills/project-maintainer/scripts/render_audit_report.py`

- [ ] **Step 1: Add fixture builders and the static HTML test**

Append these helpers near the top of `tests/test_render_audit_report.py`:

```python
def minimal_coverage_map(project: Path) -> dict:
    return {
        "schema": "project-maintainer.coverage-map.v1",
        "generated_at": "2026-07-06T00:00:00+00:00",
        "repo_root": str(project),
        "git": {"head": "abc123", "status_short": []},
        "summary": {
            "source_files": 2,
            "required_symbols": 2,
            "documented_required_symbols": 1,
            "pending_required_symbols": 1,
            "default_health_audit_required_symbols": 1,
            "documented_default_health_audit_required_symbols": 1,
            "pending_default_health_audit_required_symbols": 0,
            "repository_coverage_only_required_symbols": 1,
            "documented_repository_coverage_only_required_symbols": 0,
            "pending_repository_coverage_only_required_symbols": 1,
        },
        "files": [
            {
                "path": "app/server.py",
                "source_role": "runtime_source",
                "audit_scope": "default_health_audit",
                "status": "documented",
                "symbols": [
                    {
                        "id": "app/server.py::function::handle_request",
                        "symbol": "handle_request",
                        "name": "handle_request",
                        "kind": "function",
                        "audit_scope": "default_health_audit",
                        "doc_status": "present",
                        "actual_role_status": "present",
                        "health_status": "present",
                    }
                ],
            },
            {
                "path": "tests/test_server.py",
                "source_role": "test_source",
                "audit_scope": "repository_coverage_only",
                "status": "pending",
                "symbols": [
                    {
                        "id": "tests/test_server.py::function::test_handle_request",
                        "symbol": "test_handle_request",
                        "name": "test_handle_request",
                        "kind": "function",
                        "audit_scope": "repository_coverage_only",
                        "doc_status": "missing",
                        "actual_role_status": "missing",
                        "health_status": "missing",
                    }
                ],
            },
        ],
    }


def minimal_audit_map(project: Path) -> dict:
    return {
        "schema": "project-maintainer.symbol-audit-map.v1",
        "generated_at": "2026-07-06T00:00:01+00:00",
        "repo_root": str(project),
        "git": {"head": "abc123", "status_short": []},
        "summary": {
            "symbols": 2,
            "unaudited": 1,
            "script_assessed": 0,
            "agent_audited": 1,
            "human_audited": 0,
            "audit_expired": 0,
            "out_of_scope": 0,
            "open_issues": 1,
        },
        "health_audit_summary": {
            "symbols": 1,
            "unaudited": 0,
            "script_assessed": 0,
            "agent_audited": 1,
            "human_audited": 0,
            "audit_expired": 0,
            "out_of_scope": 0,
            "open_issues": 1,
        },
        "symbols": [
            {
                "id": "app/server.py::function::handle_request",
                "symbol": "handle_request",
                "name": "handle_request",
                "kind": "function",
                "source": "app/server.py",
                "source_role": "runtime_source",
                "audit_scope": "default_health_audit",
                "location": {"line": 10, "end_line": 12},
                "audit": {"status": "agent_audited", "confidence": "confirmed"},
                "health": {"overall": "watch", "error_handling": "weak"},
                "issues": [
                    {
                        "dimension": "error_handling",
                        "severity": "high",
                        "status": "open",
                        "summary": "Missing failure-path coverage",
                        "evidence": "No test covers exception handling",
                        "suggested_action": "Add a failure-path test and guard the exception boundary",
                    }
                ],
                "docs": {"entry_doc": "code/app/server.py/handle_request.md"},
            },
            {
                "id": "tests/test_server.py::function::test_handle_request",
                "symbol": "test_handle_request",
                "name": "test_handle_request",
                "kind": "function",
                "source": "tests/test_server.py",
                "source_role": "test_source",
                "audit_scope": "repository_coverage_only",
                "location": {"line": 5, "end_line": 6},
                "audit": {"status": "unaudited", "confidence": "unknown"},
                "health": {"overall": "unknown"},
                "issues": [],
                "docs": {"entry_doc": None},
            },
        ],
        "health_audit_symbols": [],
    }


def write_project_maps(project: Path) -> None:
    project_root = project / ".doc_project_maintainer" / "project"
    write_json(project_root / "coverage-map.json", minimal_coverage_map(project))
    write_json(project_root / "symbol-audit-map.json", minimal_audit_map(project))
```

Add this test:

```python
    def test_generates_self_contained_html_with_default_and_all_scope_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            write_project_maps(project)
            output = project / ".doc_project_maintainer" / "project" / "audit-report.html"

            result = run_report(project, "--output", str(output), "--skip-integrity-refresh")

            self.assertEqual(result.returncode, 0, result.stderr)
            html = output.read_text(encoding="utf-8")
            self.assertIn("Project Maintainer Audit Report", html)
            self.assertIn('"defaultScope": "default_health_audit"', html)
            self.assertIn('"scope": "all"', html)
            self.assertIn("handle_request", html)
            self.assertIn("test_handle_request", html)
            self.assertNotIn("https://", html)
            self.assertNotIn("<script src=", html)
            self.assertNotIn("<link rel=", html)
```

- [ ] **Step 2: Run the new test to verify it fails**

Run:

```bash
python -m pytest tests/test_render_audit_report.py::AuditReportRenderingTests::test_generates_self_contained_html_with_default_and_all_scope_data -q
```

Expected: FAIL because the minimal HTML does not embed report data.

- [ ] **Step 3: Implement report model and static HTML embedding**

Replace `render_minimal_html` with these functions and update `generate_report` to call them:

```python
def symbol_scope(symbol: dict[str, Any]) -> str:
    return str(symbol.get("audit_scope") or "repository_coverage_only")


def audit_status(symbol: dict[str, Any]) -> str:
    audit = symbol.get("audit") if isinstance(symbol.get("audit"), dict) else {}
    return str(audit.get("status") or "unaudited")


def open_issues(symbol: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        issue
        for issue in symbol.get("issues", [])
        if isinstance(issue, dict) and str(issue.get("status") or "open") != "closed"
    ]


def normalize_symbol(symbol: dict[str, Any], integrity_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    symbol_id = str(symbol.get("id") or "")
    location = symbol.get("location") if isinstance(symbol.get("location"), dict) else {}
    docs = symbol.get("docs") if isinstance(symbol.get("docs"), dict) else {}
    trust = integrity_by_id.get(symbol_id, {})
    return {
        "id": symbol_id,
        "name": str(symbol.get("name") or symbol.get("symbol") or symbol_id),
        "symbol": str(symbol.get("symbol") or symbol.get("name") or symbol_id),
        "kind": str(symbol.get("kind") or "unknown"),
        "className": symbol.get("class"),
        "source": str(symbol.get("source") or "unknown"),
        "line": location.get("line"),
        "endLine": location.get("end_line"),
        "sourceRole": str(symbol.get("source_role") or "unknown"),
        "auditScope": symbol_scope(symbol),
        "auditStatus": audit_status(symbol),
        "health": symbol.get("health") if isinstance(symbol.get("health"), dict) else {"overall": "unknown"},
        "issues": open_issues(symbol),
        "entryDoc": docs.get("entry_doc"),
        "trustResult": trust.get("trust_result") or "unverified",
        "closureEligible": bool(trust.get("closure_eligible")) if trust else False,
        "resultCodes": trust.get("result_codes") if isinstance(trust.get("result_codes"), list) else [],
    }


def build_integrity_lookup(integrity_report: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not integrity_report:
        return {}
    records = integrity_report.get("records_detail")
    if not isinstance(records, list):
        return {}
    return {str(item.get("id")): item for item in records if isinstance(item, dict) and item.get("id")}


def build_report_model(
    *,
    coverage_map: dict[str, Any],
    audit_map: dict[str, Any],
    integrity_report: dict[str, Any] | None,
    integrity_state: dict[str, Any],
    default_scope: str,
    generated_at: str,
) -> dict[str, Any]:
    integrity_by_id = build_integrity_lookup(integrity_report)
    symbols = [
        normalize_symbol(symbol, integrity_by_id)
        for symbol in audit_map.get("symbols", [])
        if isinstance(symbol, dict)
    ]
    return {
        "schema": "project-maintainer.audit-visual-report.v1",
        "generatedAt": generated_at,
        "defaultScope": default_scope,
        "scopes": ["default_health_audit", "all"],
        "status": {
            "coverageGeneratedAt": coverage_map.get("generated_at"),
            "auditGeneratedAt": audit_map.get("generated_at"),
            "coverageGit": coverage_map.get("git") if isinstance(coverage_map.get("git"), dict) else {},
            "auditGit": audit_map.get("git") if isinstance(audit_map.get("git"), dict) else {},
            "integrity": integrity_state,
        },
        "coverageSummary": coverage_map.get("summary") if isinstance(coverage_map.get("summary"), dict) else {},
        "auditSummary": audit_map.get("summary") if isinstance(audit_map.get("summary"), dict) else {},
        "healthAuditSummary": audit_map.get("health_audit_summary")
        if isinstance(audit_map.get("health_audit_summary"), dict)
        else {},
        "symbols": symbols,
    }


def render_html(model: dict[str, Any]) -> str:
    data = json.dumps(model, ensure_ascii=False, sort_keys=True)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Project Maintainer Audit Report</title>
  <style>
    body {{ margin: 0; font-family: Arial, sans-serif; background: #f8fafc; color: #111827; }}
    main {{ max-width: 1200px; margin: 0 auto; padding: 24px; }}
    .status {{ padding: 12px; border: 1px solid #d1d5db; background: #fff; border-radius: 8px; }}
    .warning {{ background: #fef2f2; border-color: #fecaca; color: #7f1d1d; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin: 16px 0; }}
    .metric {{ background: #fff; border: 1px solid #d1d5db; border-radius: 8px; padding: 12px; }}
    .metric strong {{ display: block; font-size: 24px; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; }}
    th, td {{ border-bottom: 1px solid #e5e7eb; padding: 8px; text-align: left; vertical-align: top; }}
    input, select {{ padding: 8px; margin: 4px 4px 12px 0; }}
    .risk-high {{ color: #991b1b; font-weight: 700; }}
    .risk-medium {{ color: #92400e; font-weight: 700; }}
    .risk-low {{ color: #166534; font-weight: 700; }}
  </style>
</head>
<body>
<main>
  <h1>Project Maintainer Audit Report</h1>
  <section id="status" class="status"></section>
  <section id="dashboard" class="grid"></section>
  <section>
    <h2>Priority View</h2>
    <div id="priority"></div>
  </section>
  <section>
    <h2>Scope And Details</h2>
    <label>Scope <select id="scopeSelect"><option value="default_health_audit">Default health audit</option><option value="all">All</option></select></label>
    <label>Risk <select id="riskFilter"><option value="">All risks</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select></label>
    <label>Status <select id="statusFilter"><option value="">All statuses</option></select></label>
    <label>Search <input id="searchInput" type="search" placeholder="Search symbol, file, class, method"></label>
    <table id="detailsTable"></table>
  </section>
</main>
<script id="report-data" type="application/json">{data}</script>
<script>
const report = JSON.parse(document.getElementById('report-data').textContent);
document.getElementById('status').textContent = 'Generated at ' + report.generatedAt;
document.getElementById('dashboard').innerHTML = '<div class="metric"><span>Symbols</span><strong>' + report.symbols.length + '</strong></div>';
document.getElementById('priority').textContent = 'Priority data will render in the completed report.';
document.getElementById('detailsTable').innerHTML = '<tr><th>Name</th><th>Source</th><th>Status</th></tr>' +
  report.symbols.map(item => '<tr><td>' + item.name + '</td><td>' + item.source + '</td><td>' + item.auditStatus + '</td></tr>').join('');
</script>
</body>
</html>
"""
```

Update `generate_report`:

```python
def generate_report(args: argparse.Namespace) -> Path:
    paths = resolve_paths(args)
    coverage_map = read_json(paths["coverage_map"], "coverage-map.json")
    audit_map = read_json(paths["audit_map"], "symbol-audit-map.json")
    integrity_report = None
    integrity_state = {
        "fresh": False,
        "status": "skipped" if args.skip_integrity_refresh else "unverified",
        "generatedAt": None,
        "message": "Integrity refresh skipped" if args.skip_integrity_refresh else "Integrity refresh not yet implemented",
    }
    model = build_report_model(
        coverage_map=coverage_map,
        audit_map=audit_map,
        integrity_report=integrity_report,
        integrity_state=integrity_state,
        default_scope=args.scope,
        generated_at=utc_now(),
    )
    html = render_html(model)
    paths["output"].parent.mkdir(parents=True, exist_ok=True)
    paths["output"].write_text(html, encoding="utf-8")
    return paths["output"]
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
python -m pytest tests/test_render_audit_report.py::AuditReportRenderingTests::test_generates_self_contained_html_with_default_and_all_scope_data -q
```

Expected: PASS.

- [ ] **Step 5: Commit Task 2**

Run:

```bash
git add tests/test_render_audit_report.py skills/project-maintainer/scripts/render_audit_report.py
git commit -m "feat: render static audit report data"
```

---

### Task 3: Integrity Refresh Success And Failure

**Files:**
- Modify: `tests/test_render_audit_report.py`
- Modify: `skills/project-maintainer/scripts/render_audit_report.py`

- [ ] **Step 1: Add integrity refresh tests**

Add these tests:

```python
    def test_refreshes_integrity_report_and_merges_trust_details(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            write_project_maps(project)
            output = project / ".doc_project_maintainer" / "project" / "audit-report.html"
            integrity_output = project / ".doc_project_maintainer" / "project" / "audit-integrity-report.json"

            result = run_report(project, "--output", str(output), "--integrity-report-output", str(integrity_output))

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(integrity_output.exists())
            report = json.loads(integrity_output.read_text(encoding="utf-8"))
            self.assertEqual(report["records"], 2)
            html = output.read_text(encoding="utf-8")
            self.assertIn('"fresh": true', html)
            self.assertIn("unsigned_agent_audit", html)

    def test_integrity_refresh_failure_marks_report_unverified(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            write_project_maps(project)
            output = project / ".doc_project_maintainer" / "project" / "audit-report.html"

            result = run_report(project, "--output", str(output), key=None)

            self.assertEqual(result.returncode, 0, result.stderr)
            html = output.read_text(encoding="utf-8")
            self.assertIn("Integrity refresh failed", html)
            self.assertIn('"trustResult": "unverified"', html)
            self.assertIn('"fresh": false', html)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/test_render_audit_report.py::AuditReportRenderingTests::test_refreshes_integrity_report_and_merges_trust_details tests/test_render_audit_report.py::AuditReportRenderingTests::test_integrity_refresh_failure_marks_report_unverified -q
```

Expected: FAIL because integrity refresh is not implemented.

- [ ] **Step 3: Implement integrity refresh**

Add imports:

```python
import subprocess
```

Add this function:

```python
def run_integrity_report(args: argparse.Namespace, paths: dict[str, Path]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    if args.skip_integrity_refresh:
        return None, {
            "fresh": False,
            "status": "skipped",
            "generatedAt": None,
            "message": "Integrity refresh skipped",
            "command": None,
        }

    script = Path(__file__).resolve().with_name("audit_integrity.py")
    command = [
        sys.executable,
        str(script),
        "report",
        "--repo-root",
        str(paths["repo_root"]),
        "--audit-map",
        str(paths["audit_map"]),
        "--scope",
        ALL_SCOPE,
        "--report-output",
        str(paths["integrity_report"]),
        "--signing-key-env",
        args.signing_key_env,
        "--batch-reuse-threshold",
        str(args.batch_reuse_threshold),
    ]
    result = subprocess.run(
        command,
        cwd=paths["repo_root"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        return None, {
            "fresh": False,
            "status": "failed",
            "generatedAt": utc_now(),
            "message": "Integrity refresh failed",
            "command": command,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    report = json.loads(result.stdout)
    return report, {
        "fresh": True,
        "status": "fresh",
        "generatedAt": utc_now(),
        "message": "Integrity refresh succeeded",
        "command": command,
        "summary": {
            "records": report.get("records"),
            "closure": report.get("closure"),
            "agentAuditTrustCounts": report.get("agent_audit_trust_counts"),
            "resultCounts": report.get("result_counts"),
        },
    }
```

Update `generate_report`:

```python
    integrity_report, integrity_state = run_integrity_report(args, paths)
```

Use that line instead of the temporary unverified `integrity_state`.

- [ ] **Step 4: Improve status banner rendering**

In `render_html`, replace the status JavaScript assignment:

```javascript
const statusEl = document.getElementById('status');
statusEl.className = 'status' + (report.status.integrity.status === 'failed' ? ' warning' : '');
statusEl.textContent = 'Generated at ' + report.generatedAt + ' | Integrity: ' + report.status.integrity.message;
```

- [ ] **Step 5: Run tests to verify they pass**

Run:

```bash
python -m pytest tests/test_render_audit_report.py::AuditReportRenderingTests::test_refreshes_integrity_report_and_merges_trust_details tests/test_render_audit_report.py::AuditReportRenderingTests::test_integrity_refresh_failure_marks_report_unverified -q
```

Expected: PASS.

- [ ] **Step 6: Commit Task 3**

Run:

```bash
git add tests/test_render_audit_report.py skills/project-maintainer/scripts/render_audit_report.py
git commit -m "feat: refresh audit integrity before rendering"
```

---

### Task 4: Overview Metrics, Risk Scoring, And Priority View

**Files:**
- Modify: `tests/test_render_audit_report.py`
- Modify: `skills/project-maintainer/scripts/render_audit_report.py`

- [ ] **Step 1: Add priority and overview tests**

Add this test:

```python
    def test_priority_view_and_overview_metrics_include_risk_and_pending_states(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            write_project_maps(project)
            audit_path = project / ".doc_project_maintainer" / "project" / "symbol-audit-map.json"
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            audit["symbols"].append(
                {
                    "id": "app/server.py::function::stale_handler",
                    "symbol": "stale_handler",
                    "name": "stale_handler",
                    "kind": "function",
                    "source": "app/server.py",
                    "source_role": "runtime_source",
                    "audit_scope": "default_health_audit",
                    "location": {"line": 30, "end_line": 32},
                    "audit": {"status": "audit_expired", "confidence": "confirmed"},
                    "health": {"overall": "risky"},
                    "issues": [],
                    "docs": {"entry_doc": "code/app/server.py/stale_handler.md"},
                }
            )
            write_json(audit_path, audit)
            output = project / ".doc_project_maintainer" / "project" / "audit-report.html"

            result = run_report(project, "--output", str(output))

            self.assertEqual(result.returncode, 0, result.stderr)
            html = output.read_text(encoding="utf-8")
            self.assertIn('"highRisk"', html)
            self.assertIn('"pending"', html)
            self.assertIn('"priorityItems"', html)
            self.assertLess(html.index("handle_request"), html.index("stale_handler"))
            self.assertIn("Missing failure-path coverage", html)
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python -m pytest tests/test_render_audit_report.py::AuditReportRenderingTests::test_priority_view_and_overview_metrics_include_risk_and_pending_states -q
```

Expected: FAIL because metrics and priority data are not computed.

- [ ] **Step 3: Implement risk helpers**

Add these functions:

```python
SEVERITY_SCORE = {"critical": 900, "high": 800, "medium": 500, "low": 200}
HEALTH_RISK_VALUES = {"risky", "weak", "high", "poor", "unsafe", "missing"}


def issue_severity(issue: dict[str, Any]) -> str:
    return str(issue.get("severity") or "unknown").lower()


def health_overall(item: dict[str, Any]) -> str:
    health = item.get("health") if isinstance(item.get("health"), dict) else {}
    return str(health.get("overall") or "unknown").lower()


def priority_score(item: dict[str, Any]) -> int:
    codes = {str(code) for code in item.get("resultCodes", [])}
    trust = str(item.get("trustResult") or "")
    status = str(item.get("auditStatus") or "")
    score = 0
    if "integrity_mismatch" in codes or "unsigned_agent_audit" in codes or trust == "invalid_agent_audit":
        score = max(score, 1000)
    if "suspicious_batch_signature_reuse" in codes or trust == "suspicious_agent_audit":
        score = max(score, 900)
    for issue in item.get("issues", []):
        if isinstance(issue, dict):
            score = max(score, SEVERITY_SCORE.get(issue_severity(issue), 0))
    if status == "audit_expired":
        score = max(score, 700)
    if status == "unaudited":
        score = max(score, 650)
    if status == "script_assessed" or trust == "provisional_agent_audit":
        score = max(score, 600)
    if health_overall(item) in HEALTH_RISK_VALUES:
        score = max(score, 450)
    return score


def risk_level(score: int) -> str:
    if score >= 700:
        return "high"
    if score >= 450:
        return "medium"
    if score > 0:
        return "low"
    return "none"
```

Replace `normalize_symbol` with this version so the returned item includes report-only priority fields:

```python
def normalize_symbol(symbol: dict[str, Any], integrity_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    symbol_id = str(symbol.get("id") or "")
    location = symbol.get("location") if isinstance(symbol.get("location"), dict) else {}
    docs = symbol.get("docs") if isinstance(symbol.get("docs"), dict) else {}
    trust = integrity_by_id.get(symbol_id, {})
    item = {
        "id": symbol_id,
        "name": str(symbol.get("name") or symbol.get("symbol") or symbol_id),
        "symbol": str(symbol.get("symbol") or symbol.get("name") or symbol_id),
        "kind": str(symbol.get("kind") or "unknown"),
        "className": symbol.get("class"),
        "source": str(symbol.get("source") or "unknown"),
        "line": location.get("line"),
        "endLine": location.get("end_line"),
        "sourceRole": str(symbol.get("source_role") or "unknown"),
        "auditScope": symbol_scope(symbol),
        "auditStatus": audit_status(symbol),
        "health": symbol.get("health") if isinstance(symbol.get("health"), dict) else {"overall": "unknown"},
        "issues": open_issues(symbol),
        "entryDoc": docs.get("entry_doc"),
        "trustResult": trust.get("trust_result") or "unverified",
        "closureEligible": bool(trust.get("closure_eligible")) if trust else False,
        "resultCodes": trust.get("result_codes") if isinstance(trust.get("result_codes"), list) else [],
    }
    score = priority_score(item)
    item["priorityScore"] = score
    item["riskLevel"] = risk_level(score)
    item["dangerReason"] = danger_reason(item)
    item["suggestedAction"] = suggested_action(item)
    return item
```

Add `danger_reason` and `suggested_action`:

```python
def danger_reason(item: dict[str, Any]) -> str:
    if item.get("resultCodes"):
        return "Trust verification reported: " + ", ".join(str(code) for code in item["resultCodes"])
    if item.get("issues"):
        first = item["issues"][0]
        return str(first.get("evidence") or first.get("summary") or "Open issue recorded")
    if item.get("auditStatus") == "audit_expired":
        return "Audit source hash changed after review"
    if item.get("auditStatus") == "unaudited":
        return "Symbol has not been audited"
    if item.get("auditStatus") == "script_assessed":
        return "Only script processing exists; no trusted agent or human audit"
    return "No open risk reason recorded"


def suggested_action(item: dict[str, Any]) -> str:
    if item.get("issues"):
        first = item["issues"][0]
        action = first.get("suggested_action")
        if action:
            return str(action)
    if item.get("trustResult") in {"invalid_agent_audit", "suspicious_agent_audit"}:
        return "Rerun or review the affected audit through the controlled integrity workflow"
    if item.get("auditStatus") == "audit_expired":
        return "Refresh symbol docs and rerun the audit for the changed source"
    if item.get("auditStatus") == "unaudited":
        return "Assign a symbol audit or mark the symbol out of scope with a reason"
    if item.get("auditStatus") == "script_assessed":
        return "Perform a real agent or human audit before treating this as closure"
    return "No immediate action recorded"
```

- [ ] **Step 4: Implement overview data**

Add:

```python
def in_scope(symbol: dict[str, Any], scope: str) -> bool:
    return scope == ALL_SCOPE or symbol.get("auditScope") == scope


def overview_for_scope(symbols: list[dict[str, Any]], scope: str) -> dict[str, Any]:
    scoped = [item for item in symbols if in_scope(item, scope)]
    audited = [
        item
        for item in scoped
        if item.get("auditStatus") in {"agent_audited", "human_audited", "out_of_scope"}
    ]
    pending = [item for item in scoped if not item.get("closureEligible")]
    risk_counts = {"high": 0, "medium": 0, "low": 0, "none": 0}
    health_counts: dict[str, int] = {}
    issue_dimensions: dict[str, int] = {}
    for item in scoped:
        risk_counts[str(item.get("riskLevel") or "none")] += 1
        overall = health_overall(item)
        health_counts[overall] = health_counts.get(overall, 0) + 1
        for issue in item.get("issues", []):
            dimension = str(issue.get("dimension") or "unknown")
            issue_dimensions[dimension] = issue_dimensions.get(dimension, 0) + 1
    coverage = round((len(audited) / len(scoped)) * 100, 1) if scoped else 0.0
    return {
        "scope": scope,
        "symbols": len(scoped),
        "audited": len(audited),
        "unaudited": sum(1 for item in scoped if item.get("auditStatus") == "unaudited"),
        "scriptAssessed": sum(1 for item in scoped if item.get("auditStatus") == "script_assessed"),
        "auditExpired": sum(1 for item in scoped if item.get("auditStatus") == "audit_expired"),
        "closureEligible": sum(1 for item in scoped if item.get("closureEligible")),
        "pending": len(pending),
        "highRisk": risk_counts["high"],
        "mediumRisk": risk_counts["medium"],
        "lowRisk": risk_counts["low"],
        "riskCounts": risk_counts,
        "healthCounts": health_counts,
        "topIssueDimensions": sorted(issue_dimensions.items(), key=lambda pair: (-pair[1], pair[0]))[:5],
        "coveragePercent": coverage,
    }
```

Update `build_report_model`:

```python
    priority_items = sorted(
        [item for item in symbols if item["priorityScore"] > 0],
        key=lambda item: (-item["priorityScore"], item["source"], item["name"]),
    )
```

Add to the returned model:

```python
        "overview": {
            "default_health_audit": overview_for_scope(symbols, "default_health_audit"),
            "all": overview_for_scope(symbols, "all"),
        },
        "priorityItems": priority_items[:50],
```

- [ ] **Step 5: Render priority and dashboard data**

Replace the dashboard and priority JavaScript snippets:

```javascript
function activeSymbols() {
  const scope = document.getElementById('scopeSelect').value;
  return report.symbols.filter(item => scope === 'all' || item.auditScope === scope);
}
function renderDashboard() {
  const scope = document.getElementById('scopeSelect').value;
  const overview = report.overview[scope];
  document.getElementById('dashboard').innerHTML = [
    ['Audited', overview.audited],
    ['Unaudited', overview.unaudited],
    ['Pending', overview.pending],
    ['Closure eligible', overview.closureEligible],
    ['High risk', overview.highRisk],
    ['Coverage', overview.coveragePercent + '%']
  ].map(([label, value]) => '<div class="metric"><span>' + label + '</span><strong>' + value + '</strong></div>').join('');
}
function renderPriority() {
  const scope = document.getElementById('scopeSelect').value;
  const items = report.priorityItems.filter(item => scope === 'all' || item.auditScope === scope).slice(0, 10);
  document.getElementById('priority').innerHTML = items.map(item =>
    '<article><strong class="risk-' + item.riskLevel + '">' + item.riskLevel.toUpperCase() + '</strong> ' +
    item.name + ' <code>' + item.source + ':' + (item.line || '') + '</code><br>' +
    '<span>' + item.dangerReason + '</span><br><em>' + item.suggestedAction + '</em></article>'
  ).join('') || '<p>No prioritized risks recorded for this scope.</p>';
}
```

Call `renderDashboard()` and `renderPriority()` after parsing data.

- [ ] **Step 6: Run the test to verify it passes**

Run:

```bash
python -m pytest tests/test_render_audit_report.py::AuditReportRenderingTests::test_priority_view_and_overview_metrics_include_risk_and_pending_states -q
```

Expected: PASS.

- [ ] **Step 7: Commit Task 4**

Run:

```bash
git add tests/test_render_audit_report.py skills/project-maintainer/scripts/render_audit_report.py
git commit -m "feat: compute audit report risk priorities"
```

---

### Task 5: Search, Filters, Sorting, Scope Tree, And Escaping

**Files:**
- Modify: `tests/test_render_audit_report.py`
- Modify: `skills/project-maintainer/scripts/render_audit_report.py`

- [ ] **Step 1: Add UI behavior and escaping tests**

Add:

```python
    def test_report_embeds_filter_controls_scope_tree_and_escaped_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            write_project_maps(project)
            audit_path = project / ".doc_project_maintainer" / "project" / "symbol-audit-map.json"
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            audit["symbols"][0]["name"] = "<script>alert('x')</script>"
            audit["symbols"][0]["issues"][0]["summary"] = "<b>unsafe</b>"
            write_json(audit_path, audit)
            output = project / ".doc_project_maintainer" / "project" / "audit-report.html"

            result = run_report(project, "--output", str(output), "--skip-integrity-refresh")

            self.assertEqual(result.returncode, 0, result.stderr)
            html = output.read_text(encoding="utf-8")
            self.assertIn("id=\"searchInput\"", html)
            self.assertIn("id=\"riskFilter\"", html)
            self.assertIn("id=\"statusFilter\"", html)
            self.assertIn("id=\"scopeTree\"", html)
            self.assertIn("function applyFilters()", html)
            self.assertIn("function sortBy(field)", html)
            self.assertIn("\\u003cscript\\u003ealert", html)
            self.assertNotIn("<script>alert('x')</script>", html)
            self.assertNotIn("<b>unsafe</b>", html)
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python -m pytest tests/test_render_audit_report.py::AuditReportRenderingTests::test_report_embeds_filter_controls_scope_tree_and_escaped_data -q
```

Expected: FAIL because scope tree, sorting, and safe JSON escaping are incomplete.

- [ ] **Step 3: Add safe JSON embedding**

Add:

```python
def safe_json_for_script(value: Any) -> str:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )
```

Use it in `render_html`:

```python
    data = safe_json_for_script(model)
```

- [ ] **Step 4: Build the scope tree data**

Add:

```python
def build_scope_tree(symbols: list[dict[str, Any]]) -> dict[str, Any]:
    root: dict[str, Any] = {"name": ".", "kind": "root", "children": {}, "symbols": []}
    for item in symbols:
        path_parts = str(item.get("source") or "unknown").split("/")
        node = root
        for part in path_parts:
            children = node.setdefault("children", {})
            node = children.setdefault(part, {"name": part, "kind": "path", "children": {}, "symbols": []})
        node.setdefault("symbols", []).append(item["id"])
    return root
```

Add to the returned model:

```python
        "scopeTree": build_scope_tree(symbols),
```

- [ ] **Step 5: Replace detail-table JavaScript with filters and sorting**

Use this JavaScript in `render_html`:

```javascript
let currentSort = 'priorityScore';
let sortDescending = true;
function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
}
function activeScope() {
  return document.getElementById('scopeSelect').value;
}
function activeSymbols() {
  const scope = activeScope();
  return report.symbols.filter(item => scope === 'all' || item.auditScope === scope);
}
function populateStatusFilter() {
  const statuses = Array.from(new Set(report.symbols.map(item => item.auditStatus))).sort();
  document.getElementById('statusFilter').innerHTML =
    '<option value="">All statuses</option>' + statuses.map(status => '<option value="' + escapeHtml(status) + '">' + escapeHtml(status) + '</option>').join('');
}
function applyFilters() {
  const query = document.getElementById('searchInput').value.toLowerCase();
  const risk = document.getElementById('riskFilter').value;
  const status = document.getElementById('statusFilter').value;
  let rows = activeSymbols().filter(item => {
    const haystack = [item.name, item.symbol, item.className, item.source, item.kind].join(' ').toLowerCase();
    return (!query || haystack.includes(query)) &&
      (!risk || item.riskLevel === risk) &&
      (!status || item.auditStatus === status);
  });
  rows.sort((a, b) => {
    const left = a[currentSort] ?? '';
    const right = b[currentSort] ?? '';
    if (left < right) return sortDescending ? 1 : -1;
    if (left > right) return sortDescending ? -1 : 1;
    return a.name.localeCompare(b.name);
  });
  renderTable(rows);
  renderDashboard();
  renderPriority();
}
function sortBy(field) {
  if (currentSort === field) sortDescending = !sortDescending;
  else { currentSort = field; sortDescending = field === 'priorityScore'; }
  applyFilters();
}
function renderTable(rows) {
  document.getElementById('detailsTable').innerHTML =
    '<tr><th onclick="sortBy(\\'name\\')">Name</th><th onclick="sortBy(\\'source\\')">Source</th><th onclick="sortBy(\\'auditStatus\\')">Status</th><th onclick="sortBy(\\'riskLevel\\')">Risk</th><th>Action</th></tr>' +
    rows.map(item => '<tr><td>' + escapeHtml(item.name) + '<br><small>' + escapeHtml(item.kind) + '</small></td><td><code>' + escapeHtml(item.source) + ':' + escapeHtml(item.line || '') + '</code></td><td>' + escapeHtml(item.auditStatus) + '<br><small>' + escapeHtml(item.trustResult) + '</small></td><td class="risk-' + escapeHtml(item.riskLevel) + '">' + escapeHtml(item.riskLevel) + '</td><td>' + escapeHtml(item.suggestedAction) + '</td></tr>').join('');
}
function renderScopeTreeNode(node) {
  const children = Object.values(node.children || {});
  const symbolCount = (node.symbols || []).length;
  return '<li>' + escapeHtml(node.name) + (symbolCount ? ' <small>(' + symbolCount + ' symbols)</small>' : '') +
    (children.length ? '<ul>' + children.map(renderScopeTreeNode).join('') + '</ul>' : '') + '</li>';
}
function renderScopeTree() {
  document.getElementById('scopeTree').innerHTML = '<ul>' + renderScopeTreeNode(report.scopeTree) + '</ul>';
}
```

Add a scope tree container before the table:

```html
<div id="scopeTree"></div>
```

Initialize:

```javascript
populateStatusFilter();
renderScopeTree();
document.getElementById('scopeSelect').value = report.defaultScope;
['scopeSelect','riskFilter','statusFilter','searchInput'].forEach(id => document.getElementById(id).addEventListener('input', applyFilters));
applyFilters();
```

- [ ] **Step 6: Run the UI test to verify it passes**

Run:

```bash
python -m pytest tests/test_render_audit_report.py::AuditReportRenderingTests::test_report_embeds_filter_controls_scope_tree_and_escaped_data -q
```

Expected: PASS.

- [ ] **Step 7: Run all report tests**

Run:

```bash
python -m pytest tests/test_render_audit_report.py -q
```

Expected: all report tests PASS.

- [ ] **Step 8: Commit Task 5**

Run:

```bash
git add tests/test_render_audit_report.py skills/project-maintainer/scripts/render_audit_report.py
git commit -m "feat: add audit report filtering UI"
```

---

### Task 6: Skill Documentation And Contract Tests

**Files:**
- Modify: `tests/test_skill_contract.py`
- Modify: `README.md`
- Modify: `skills/project-maintainer/SKILL.md`
- Modify: `skills/project-maintainer/agents/openai.yaml`

- [ ] **Step 1: Add contract tests**

Append to `tests/test_skill_contract.py`:

```python
def test_audit_visual_report_workflow_is_documented() -> None:
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    openai_yaml = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
    combined = "\n".join([skill, readme, openai_yaml])

    assert "render_audit_report.py" in combined
    assert "audit-report.html" in combined
    assert "self-contained HTML" in combined
    assert "audit visualization report" in combined
    assert "audit_integrity.py report" in combined
    assert "regenerate" in combined
    assert "older data" in combined
```

- [ ] **Step 2: Run the contract test to verify it fails**

Run:

```bash
python -m pytest tests/test_skill_contract.py::test_audit_visual_report_workflow_is_documented -q
```

Expected: FAIL because docs do not mention the new report workflow.

- [ ] **Step 3: Update README**

Modify README contents listing to include:

```text
      render_audit_report.py
```

Add to "What The Skill Does":

```markdown
- Generates a self-contained HTML audit visualization report through `scripts/render_audit_report.py`, combining `coverage-map.json`, `symbol-audit-map.json`, and a freshly refreshed `audit_integrity.py report` result for human review.
```

Add to Validation:

````markdown
Generate an audit visualization report for a maintained project:

```bash
python skills/project-maintainer/scripts/render_audit_report.py <repo-root>
```

The output defaults to `<repo-root>/.doc_project_maintainer/project/audit-report.html`.
````

- [ ] **Step 4: Update SKILL.md**

Add a workflow section after "Symbol Audit Map":

````markdown
### Generate Audit Visualization Report

Use this when the user asks for a human-readable audit summary, visual audit report, dashboard, HTML report, team review artifact, or security-review artifact.

1. Confirm `.doc_project_maintainer/project/coverage-map.json` and `.doc_project_maintainer/project/symbol-audit-map.json` exist. If they are missing or stale for the requested scope, explain that inventory should be refreshed before the report can be trusted.
2. Run:
   ```bash
   python <skill-dir>/scripts/render_audit_report.py <repo-root>
   ```
3. The report generator refreshes trust classification with `audit_integrity.py report` unless `--skip-integrity-refresh` is explicitly used.
4. Treat the generated `project/audit-report.html` as a presentation artifact only. The JSON maps and symbol docs remain the source of truth.
5. If inventory, coverage maps, symbol audit maps, or audit integrity reports are refreshed after the HTML report is generated, tell the user the report reflects older data and should be regenerated or refreshed in the browser.
````

Add to the Final Response Checklist:

```markdown
- If an audit visualization report was generated, state the HTML path, whether integrity refresh succeeded, and whether any later artifact refresh made the report reflect older data.
```

- [ ] **Step 5: Update agents/openai.yaml**

Extend `default_prompt` with this sentence:

```text
When a human-readable audit dashboard is requested, use scripts/render_audit_report.py to generate project/audit-report.html; if you refresh inventory, coverage maps, symbol audit maps, or audit integrity reports after report generation, tell the user the HTML reflects older data and should be regenerated.
```

- [ ] **Step 6: Run the contract test to verify it passes**

Run:

```bash
python -m pytest tests/test_skill_contract.py::test_audit_visual_report_workflow_is_documented -q
```

Expected: PASS.

- [ ] **Step 7: Commit Task 6**

Run:

```bash
git add tests/test_skill_contract.py README.md skills/project-maintainer/SKILL.md skills/project-maintainer/agents/openai.yaml
git commit -m "docs: document audit visual reports"
```

---

### Task 7: Version, Package Archive, And Full Verification

**Files:**
- Modify: `skills/project-maintainer/VERSION`
- Modify: `skills/project-maintainer/metadata.yaml`
- Modify: `skills/project-maintainer.zip`

- [ ] **Step 1: Bump version files**

Change `skills/project-maintainer/VERSION` to:

```text
0.0.8
```

Change `skills/project-maintainer/metadata.yaml` to:

```yaml
version: "0.0.8"
license: "Apache-2.0"
artifact_root: ".doc_project_maintainer"
```

- [ ] **Step 2: Rebuild the packaged skill archive**

Run this PowerShell command:

```powershell
Compress-Archive -Path skills/project-maintainer/* -DestinationPath skills/project-maintainer.zip -Force
```

Expected: `skills/project-maintainer.zip` is updated.

- [ ] **Step 3: Run all tests**

Run:

```bash
python -m pytest
```

Expected: all tests PASS.

- [ ] **Step 4: Run skill validation**

Run:

```bash
python C:/Users/Administrator/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/project-maintainer
```

Expected: validation exits 0 and reports no blocking manifest or skill errors.

- [ ] **Step 5: Check changed files**

Run:

```bash
git status --short
```

Expected changed files:

```text
M README.md
M skills/project-maintainer.zip
M skills/project-maintainer/SKILL.md
M skills/project-maintainer/VERSION
M skills/project-maintainer/agents/openai.yaml
M skills/project-maintainer/metadata.yaml
A skills/project-maintainer/scripts/render_audit_report.py
A tests/test_render_audit_report.py
```

The exact order may differ. Earlier task commits may leave fewer files changed at this point.

- [ ] **Step 6: Commit release update**

Run:

```bash
git add README.md skills/project-maintainer.zip skills/project-maintainer/SKILL.md skills/project-maintainer/VERSION skills/project-maintainer/agents/openai.yaml skills/project-maintainer/metadata.yaml skills/project-maintainer/scripts/render_audit_report.py tests/test_render_audit_report.py tests/test_skill_contract.py
git commit -m "feat: add audit visual report"
```

If previous tasks already committed some files, stage only the remaining version and zip files:

```bash
git add skills/project-maintainer.zip skills/project-maintainer/VERSION skills/project-maintainer/metadata.yaml
git commit -m "chore: release project maintainer 0.0.8"
```

---

## Final Verification Checklist

- [ ] `python -m pytest` passes.
- [ ] `python C:/Users/Administrator/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/project-maintainer` passes.
- [ ] `render_audit_report.py` can generate `.doc_project_maintainer/project/audit-report.html` from test fixture maps.
- [ ] Generated HTML is self-contained and includes no external `http://`, `https://`, `<script src=`, or `<link rel=`.
- [ ] Generated HTML shows integrity refresh failure as unverified when signing key is missing.
- [ ] `SKILL.md` tells agents to warn users when data refresh happens after report generation.
- [ ] `README.md` documents the report command.
- [ ] `skills/project-maintainer.zip` includes `scripts/render_audit_report.py`.

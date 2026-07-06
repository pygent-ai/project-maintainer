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


class AuditReportRenderingTests(unittest.TestCase):
    def test_missing_project_maps_fail_without_writing_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            output = project / ".doc_project_maintainer" / "project" / "audit-report.html"

            result = run_report(project, "--output", str(output), "--skip-integrity-refresh")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("coverage-map.json not found", result.stderr)
            self.assertFalse(output.exists())

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


if __name__ == "__main__":
    unittest.main()

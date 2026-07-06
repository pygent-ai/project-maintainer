import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INVENTORY_SCRIPT = REPO_ROOT / "skills" / "project-maintainer" / "scripts" / "inventory_symbols.py"
AUDIT_INTEGRITY_SCRIPT = REPO_ROOT / "skills" / "project-maintainer" / "scripts" / "audit_integrity.py"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")


def run_git(project: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=project, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def init_project_with_docs(function_names: list[str]) -> tuple[tempfile.TemporaryDirectory[str], Path, Path]:
    temp_dir = tempfile.TemporaryDirectory()
    project = Path(temp_dir.name)
    source = "\n\n".join(f"def {name}(value):\n    return value.strip()" for name in function_names)
    write(project / "app" / "server.py", source)
    for name in function_names:
        write(
            project / ".doc_project_maintainer" / "code" / "app" / "server.py" / f"{name}.md",
            f"""
            ---
            health:
              overall: healthy
            audit:
              status: unaudited
              auditor: null
              audited_at: null
              audited_commit: null
              audited_source_hash: null
              confidence: unknown
              expired_reason: null
            ---

            # {name}

            ## Actual Role

            Strips whitespace from the provided value.
            """,
        )
    run_git(project, "init")
    run_git(project, "add", ".")
    audit_map = project / ".doc_project_maintainer" / "project" / "symbol-audit-map.json"
    subprocess.run(
        [
            sys.executable,
            str(INVENTORY_SCRIPT),
            str(project),
            "--audit-map-output",
            str(audit_map),
            "--verify-docs",
            "--pretty",
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return temp_dir, project, audit_map


def run_audit_integrity(project: Path, *args: str, key: str = "test-secret") -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PROJECT_MAINTAINER_AUDIT_SIGNING_KEY"] = key
    return subprocess.run(
        [sys.executable, str(AUDIT_INTEGRITY_SCRIPT), *args],
        cwd=project,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def signature_file(project: Path) -> Path:
    path = project / "signature-batch.json"
    write(
        path,
        """
        {
          "calls": [
            {
              "tool_name": "functions.shell_command",
              "raw_input": {
                "command": "Get-Content -Raw app/server.py",
                "workdir": "repo"
              }
            }
          ]
        }
        """,
    )
    return path


def bom_signature_file(project: Path) -> Path:
    path = project / "signature-batch-bom.json"
    payload = {
        "calls": [
            {
                "tool_name": "functions.shell_command",
                "raw_input": {
                    "command": "Get-Content -Raw app/server.py",
                    "workdir": "repo",
                },
            }
        ]
    }
    path.write_bytes(b"\xef\xbb\xbf" + json.dumps(payload).encode("utf-8"))
    return path


class AuditIntegrityEntrypointTests(unittest.TestCase):
    def test_promote_without_agent_signature_downgrades_to_script_assessed(self) -> None:
        temp_dir, project, audit_map = init_project_with_docs(["handle_request"])
        self.addCleanup(temp_dir.cleanup)

        result = run_audit_integrity(
            project,
            "promote",
            "--repo-root",
            str(project),
            "--audit-map",
            str(audit_map),
            "--entry-doc",
            str(project / ".doc_project_maintainer" / "code" / "app" / "server.py" / "handle_request.md"),
            "--symbol-id",
            "app/server.py::function::handle_request",
            "--source-file",
            "app/server.py",
            "--scope",
            "default_health_audit",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("missing_agent_call_signature", result.stdout)
        audit = json.loads(audit_map.read_text(encoding="utf-8"))
        symbol = audit["symbols"][0]
        self.assertEqual(symbol["audit"]["status"], "script_assessed")
        self.assertEqual(symbol["audit"]["downgrade_reason"], "missing_agent_call_signature")
        self.assertEqual(symbol["integrity"]["signature_algorithm"], "hmac-sha256")
        self.assertNotIn("machine_assessment", symbol)

        closure_result = run_audit_integrity(
            project,
            "verify",
            "--repo-root",
            str(project),
            "--audit-map",
            str(audit_map),
            "--scope",
            "default_health_audit",
            "--require-closure",
        )
        self.assertEqual(closure_result.returncode, 4, closure_result.stdout)
        report = json.loads(closure_result.stdout)
        self.assertEqual(report["result_counts"]["script_assessed_only"], 1)
        self.assertEqual(report["closure"]["pending"], 1)

    def test_promote_with_unique_signature_verifies_as_trusted_agent_audit(self) -> None:
        temp_dir, project, audit_map = init_project_with_docs(["handle_request"])
        self.addCleanup(temp_dir.cleanup)
        signature = signature_file(project)

        promote = run_audit_integrity(
            project,
            "promote",
            "--repo-root",
            str(project),
            "--audit-map",
            str(audit_map),
            "--entry-doc",
            str(project / ".doc_project_maintainer" / "code" / "app" / "server.py" / "handle_request.md"),
            "--symbol-id",
            "app/server.py::function::handle_request",
            "--source-file",
            "app/server.py",
            "--scope",
            "default_health_audit",
            "--agent-call-signature-json",
            str(signature),
        )
        self.assertEqual(promote.returncode, 0, promote.stderr)

        verify = run_audit_integrity(
            project,
            "verify",
            "--repo-root",
            str(project),
            "--audit-map",
            str(audit_map),
            "--scope",
            "default_health_audit",
            "--require-closure",
        )

        self.assertEqual(verify.returncode, 0, verify.stdout)
        report = json.loads(verify.stdout)
        self.assertEqual(report["agent_audit_trust_counts"]["trusted_agent_audit"], 1)
        self.assertEqual(report["closure"]["eligible"], 1)
        self.assertTrue(report["closure"]["require_closure_passed"])

    def test_wrong_hmac_key_invalidates_agent_audit(self) -> None:
        temp_dir, project, audit_map = init_project_with_docs(["handle_request"])
        self.addCleanup(temp_dir.cleanup)
        signature = signature_file(project)

        promote = run_audit_integrity(
            project,
            "promote",
            "--repo-root",
            str(project),
            "--audit-map",
            str(audit_map),
            "--entry-doc",
            str(project / ".doc_project_maintainer" / "code" / "app" / "server.py" / "handle_request.md"),
            "--symbol-id",
            "app/server.py::function::handle_request",
            "--source-file",
            "app/server.py",
            "--scope",
            "default_health_audit",
            "--agent-call-signature-json",
            str(signature),
        )
        self.assertEqual(promote.returncode, 0, promote.stderr)

        verify = run_audit_integrity(
            project,
            "verify",
            "--repo-root",
            str(project),
            "--audit-map",
            str(audit_map),
            "--scope",
            "default_health_audit",
            key="wrong-secret",
        )

        self.assertEqual(verify.returncode, 1, verify.stdout)
        report = json.loads(verify.stdout)
        self.assertEqual(report["result_counts"]["integrity_mismatch"], 1)
        self.assertEqual(report["agent_audit_trust_counts"]["invalid_agent_audit"], 1)

    def test_reused_batch_hash_keeps_agent_audits_out_of_closure(self) -> None:
        temp_dir, project, audit_map = init_project_with_docs(["handle_request", "normalize_request"])
        self.addCleanup(temp_dir.cleanup)
        signature = signature_file(project)

        for symbol_name in ["handle_request", "normalize_request"]:
            promote = run_audit_integrity(
                project,
                "promote",
                "--repo-root",
                str(project),
                "--audit-map",
                str(audit_map),
                "--entry-doc",
                str(project / ".doc_project_maintainer" / "code" / "app" / "server.py" / f"{symbol_name}.md"),
                "--symbol-id",
                f"app/server.py::function::{symbol_name}",
                "--source-file",
                "app/server.py",
                "--scope",
                "default_health_audit",
                "--agent-call-signature-json",
                str(signature),
            )
            self.assertEqual(promote.returncode, 0, promote.stderr)

        report_result = run_audit_integrity(
            project,
            "report",
            "--repo-root",
            str(project),
            "--audit-map",
            str(audit_map),
            "--scope",
            "default_health_audit",
        )

        self.assertEqual(report_result.returncode, 0, report_result.stderr)
        report = json.loads(report_result.stdout)
        self.assertEqual(report["result_counts"]["suspicious_batch_signature_reuse"], 2)
        self.assertEqual(report["agent_audit_trust_counts"]["suspicious_agent_audit"], 2)
        self.assertEqual(report["closure"]["eligible"], 0)
        self.assertEqual(report["closure"]["pending"], 2)

    def test_bom_encoded_json_inputs_are_accepted(self) -> None:
        temp_dir, project, audit_map = init_project_with_docs(["handle_request"])
        self.addCleanup(temp_dir.cleanup)
        signature = bom_signature_file(project)

        promote = run_audit_integrity(
            project,
            "promote",
            "--repo-root",
            str(project),
            "--audit-map",
            str(audit_map),
            "--entry-doc",
            str(project / ".doc_project_maintainer" / "code" / "app" / "server.py" / "handle_request.md"),
            "--symbol-id",
            "app/server.py::function::handle_request",
            "--source-file",
            "app/server.py",
            "--scope",
            "default_health_audit",
            "--agent-call-signature-json",
            str(signature),
        )
        self.assertEqual(promote.returncode, 0, promote.stderr)

        audit_bytes = audit_map.read_bytes()
        audit_map.write_bytes(b"\xef\xbb\xbf" + audit_bytes)

        verify = run_audit_integrity(
            project,
            "verify",
            "--repo-root",
            str(project),
            "--audit-map",
            str(audit_map),
            "--scope",
            "default_health_audit",
            "--require-closure",
        )

        self.assertEqual(verify.returncode, 0, verify.stdout)
        report = json.loads(verify.stdout)
        self.assertEqual(report["agent_audit_trust_counts"]["trusted_agent_audit"], 1)


if __name__ == "__main__":
    unittest.main()

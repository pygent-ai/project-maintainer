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


def run_audit_integrity_without_env(project: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("PROJECT_MAINTAINER_AUDIT_SIGNING_KEY", None)
    return subprocess.run(
        [sys.executable, str(AUDIT_INTEGRITY_SCRIPT), *args],
        cwd=project,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def artifact_signing_key_path(project: Path) -> Path:
    return project / ".doc_project_maintainer" / "project" / "audit-signing-key.json"


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
    def test_verify_keeps_audit_trusted_when_only_sibling_function_changes(self) -> None:
        temp_dir, project, audit_map = init_project_with_docs(["handle_request", "normalize_request"])
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
            ".doc_project_maintainer/code/app/server.py/handle_request.md",
            "--symbol-id",
            "app/server.py::function::handle_request",
            "--source-file",
            "app/server.py",
            "--agent-call-signature-json",
            str(signature),
        )
        self.assertEqual(promote.returncode, 0, promote.stderr)

        write(
            project / "app" / "server.py",
            """
            def handle_request(value):
                return value.strip()

            def normalize_request(value):
                return value.casefold()
            """,
        )
        verify = run_audit_integrity(
            project,
            "verify",
            "--repo-root",
            str(project),
            "--audit-map",
            str(audit_map),
        )

        self.assertEqual(verify.returncode, 0, verify.stdout)
        report = json.loads(verify.stdout)
        audited = next(item for item in report["records_detail"] if item["id"].endswith("handle_request"))
        self.assertEqual(audited["trust_result"], "trusted_agent_audit")
        self.assertNotIn("source_hash_changed", audited["result_codes"])
        self.assertNotIn("symbol_hash_changed", audited["result_codes"])

    def test_verify_reports_symbol_hash_change_for_changed_audited_function(self) -> None:
        temp_dir, project, audit_map = init_project_with_docs(["handle_request", "normalize_request"])
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
            ".doc_project_maintainer/code/app/server.py/handle_request.md",
            "--symbol-id",
            "app/server.py::function::handle_request",
            "--source-file",
            "app/server.py",
            "--agent-call-signature-json",
            str(signature),
        )
        self.assertEqual(promote.returncode, 0, promote.stderr)

        write(
            project / "app" / "server.py",
            """
            def handle_request(value):
                return value.strip().casefold()

            def normalize_request(value):
                return value.strip()
            """,
        )
        verify = run_audit_integrity(
            project,
            "verify",
            "--repo-root",
            str(project),
            "--audit-map",
            str(audit_map),
        )

        self.assertEqual(verify.returncode, 2, verify.stdout)
        report = json.loads(verify.stdout)
        audited = next(item for item in report["records_detail"] if item["id"].endswith("handle_request"))
        self.assertEqual(audited["trust_result"], "invalid_agent_audit")
        self.assertIn("symbol_hash_changed", audited["result_codes"])
        self.assertNotIn("source_hash_changed", audited["result_codes"])

    def test_ensure_key_creates_artifact_local_key_without_audit_map(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            key_path = artifact_signing_key_path(project)

            result = run_audit_integrity_without_env(
                project,
                "ensure-key",
                "--repo-root",
                str(project),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(key_path.exists())
            output = json.loads(result.stdout)
            self.assertTrue(output["created"])
            self.assertEqual(output["key_path"], str(key_path))
            self.assertNotIn("secret", output)

            second_result = run_audit_integrity_without_env(
                project,
                "ensure-key",
                "--repo-root",
                str(project),
            )

            self.assertEqual(second_result.returncode, 0, second_result.stderr)
            second_output = json.loads(second_result.stdout)
            self.assertFalse(second_output["created"])

    def test_promote_without_env_creates_artifact_local_signing_key(self) -> None:
        temp_dir, project, audit_map = init_project_with_docs(["handle_request"])
        self.addCleanup(temp_dir.cleanup)
        key_path = artifact_signing_key_path(project)
        self.assertFalse(key_path.exists())

        result = run_audit_integrity_without_env(
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
        self.assertTrue(key_path.exists())
        key_record = json.loads(key_path.read_text(encoding="utf-8"))
        self.assertEqual(key_record["schema"], "project-maintainer.audit-signing-key.v1")
        self.assertEqual(key_record["environment_variable"], "PROJECT_MAINTAINER_AUDIT_SIGNING_KEY")
        self.assertEqual(key_record["purpose"], "artifact-local agent workflow integrity")
        self.assertIsInstance(key_record["secret"], str)
        self.assertGreaterEqual(len(key_record["secret"]), 32)

        verify = run_audit_integrity_without_env(
            project,
            "verify",
            "--repo-root",
            str(project),
            "--audit-map",
            str(audit_map),
            "--scope",
            "default_health_audit",
        )

        self.assertEqual(verify.returncode, 0, verify.stdout)

    def test_existing_artifact_local_signing_key_is_reused_when_env_is_missing(self) -> None:
        temp_dir, project, audit_map = init_project_with_docs(["handle_request"])
        self.addCleanup(temp_dir.cleanup)
        key_path = artifact_signing_key_path(project)
        write(
            key_path,
            """
            {
              "schema": "project-maintainer.audit-signing-key.v1",
              "algorithm": "hmac-sha256",
              "environment_variable": "PROJECT_MAINTAINER_AUDIT_SIGNING_KEY",
              "key_id": "project-maintainer-local-v1",
              "purpose": "artifact-local agent workflow integrity",
              "secret": "persisted-test-secret",
              "generated_by": "test"
            }
            """,
        )
        signature = signature_file(project)

        promote = run_audit_integrity_without_env(
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

        verify_with_env_key = run_audit_integrity(
            project,
            "verify",
            "--repo-root",
            str(project),
            "--audit-map",
            str(audit_map),
            "--scope",
            "default_health_audit",
            "--require-closure",
            key="persisted-test-secret",
        )

        self.assertEqual(verify_with_env_key.returncode, 0, verify_with_env_key.stdout)

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

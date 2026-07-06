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

import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INVENTORY_SCRIPT = REPO_ROOT / "skills" / "project-maintainer" / "scripts" / "inventory_symbols.py"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")


class InventorySymbolScopeTests(unittest.TestCase):
    def test_class_entry_doc_is_required_for_verified_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            write(
                project / "app" / "model.py",
                """
                class Widget:
                    def render(self):
                        return "widget"

                def helper():
                    return Widget().render()
                """,
            )
            write(
                project / ".doc_project_maintainer" / "code" / "app" / "model.py" / "model.py.md",
                """
                # model.py

                Symbol inventory for app/model.py.
                """,
            )
            write(
                project / ".doc_project_maintainer" / "code" / "app" / "model.py" / "Class Widget" / "Widget.render.md",
                """
                ---
                health:
                  overall: healthy
                ---

                # Widget.render

                ## Actual Role

                Returns the display value for a widget.
                """,
            )
            write(
                project / ".doc_project_maintainer" / "code" / "app" / "model.py" / "helper.md",
                """
                ---
                health:
                  overall: healthy
                ---

                # helper

                ## Actual Role

                Instantiates a widget and returns its rendered value.
                """,
            )

            subprocess.run(["git", "init"], cwd=project, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "add", "."], cwd=project, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            inventory_path = project / ".doc_project_maintainer" / "project" / "source-symbol-inventory.json"
            coverage_path = project / ".doc_project_maintainer" / "project" / "coverage-map.json"

            subprocess.run(
                [
                    sys.executable,
                    str(INVENTORY_SCRIPT),
                    str(project),
                    "--output",
                    str(inventory_path),
                    "--coverage-map-output",
                    str(coverage_path),
                    "--verify-docs",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
            coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
            self.assertEqual(inventory["summary"]["missing_entry_docs"], 1)
            self.assertEqual(coverage["summary"]["required_symbols"], 3)
            self.assertEqual(coverage["summary"]["pending_required_symbols"], 1)
            self.assertEqual(coverage["files"][0]["status"], "pending")
            self.assertEqual(coverage["files"][0]["symbols"][0]["doc_status"], "missing")

            write(
                project / ".doc_project_maintainer" / "code" / "app" / "model.py" / "Class Widget" / "Class Widget.md",
                """
                ---
                health:
                  overall: healthy
                ---

                # Widget

                ## Actual Role

                Provides widget rendering behavior through its methods.
                """,
            )

            subprocess.run(
                [
                    sys.executable,
                    str(INVENTORY_SCRIPT),
                    str(project),
                    "--output",
                    str(inventory_path),
                    "--coverage-map-output",
                    str(coverage_path),
                    "--verify-docs",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
            coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
            self.assertEqual(inventory["summary"]["missing_entry_docs"], 0)
            self.assertEqual(coverage["summary"]["pending_required_symbols"], 0)
            self.assertEqual(coverage["files"][0]["status"], "documented")

    def test_default_health_audit_scope_excludes_tests_scripts_and_package_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            write(
                project / "app" / "server.py",
                """
                def handle_request():
                    return "ok"
                """,
            )
            write(
                project / "tests" / "test_server.py",
                """
                def test_handle_request():
                    assert True
                """,
            )
            write(
                project / "src" / "server.test.js",
                """
                function exercisesClient() {
                  return true;
                }
                """,
            )
            write(
                project / "scripts" / "maintenance.py",
                """
                def rebuild_index():
                    return None
                """,
            )
            write(
                project / "setup.py",
                """
                def build_package_metadata():
                    return {}
                """,
            )
            write(
                project / "node_modules" / "leftpad" / "index.js",
                """
                function leftpad() {
                  return "";
                }
                """,
            )
            write(
                project / "docs" / "overview.md",
                """
                # Overview
                """,
            )

            subprocess.run(["git", "init"], cwd=project, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "add", "."], cwd=project, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            inventory_path = project / ".doc_project_maintainer" / "project" / "source-symbol-inventory.json"
            coverage_path = project / ".doc_project_maintainer" / "project" / "coverage-map.json"
            audit_path = project / ".doc_project_maintainer" / "project" / "symbol-audit-map.json"

            subprocess.run(
                [
                    sys.executable,
                    str(INVENTORY_SCRIPT),
                    str(project),
                    "--output",
                    str(inventory_path),
                    "--coverage-map-output",
                    str(coverage_path),
                    "--audit-map-output",
                    str(audit_path),
                    "--pretty",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
            coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
            audit = json.loads(audit_path.read_text(encoding="utf-8"))

            roles_by_path = {item["path"]: item["source_role"] for item in inventory["files"]}
            self.assertEqual(roles_by_path["app/server.py"], "runtime_source")
            self.assertEqual(roles_by_path["tests/test_server.py"], "test_source")
            self.assertEqual(roles_by_path["src/server.test.js"], "test_source")
            self.assertEqual(roles_by_path["scripts/maintenance.py"], "script")
            self.assertEqual(roles_by_path["setup.py"], "package_metadata")

            audit_scope_by_path = {item["path"]: item["audit_scope"] for item in coverage["files"]}
            self.assertEqual(audit_scope_by_path["app/server.py"], "default_health_audit")
            self.assertEqual(audit_scope_by_path["tests/test_server.py"], "repository_coverage_only")
            self.assertEqual(audit_scope_by_path["src/server.test.js"], "repository_coverage_only")
            self.assertEqual(audit_scope_by_path["scripts/maintenance.py"], "repository_coverage_only")
            self.assertEqual(audit_scope_by_path["setup.py"], "repository_coverage_only")

            repository_slice_paths = {
                path
                for suggested_slice in coverage["suggested_slices"]
                for path in suggested_slice["files"]
            }
            self.assertEqual(
                repository_slice_paths,
                {
                    "app/server.py",
                    "tests/test_server.py",
                    "src/server.test.js",
                    "scripts/maintenance.py",
                    "setup.py",
                },
            )

            default_audit_slice_paths = {
                path
                for suggested_slice in coverage["suggested_audit_slices"]
                for path in suggested_slice["files"]
            }
            self.assertEqual(default_audit_slice_paths, {"app/server.py"})

            self.assertEqual(coverage["summary"]["default_health_audit_required_symbols"], 1)
            self.assertEqual(coverage["summary"]["repository_coverage_only_required_symbols"], 4)
            self.assertEqual(audit["health_audit_summary"]["symbols"], 1)
            self.assertTrue(
                all(item["audit_scope"] == "default_health_audit" for item in audit["health_audit_symbols"])
            )

            directory_summary = inventory["directory_summary"]
            recorded_by_directory = {item["directory"]: item for item in directory_summary["recorded_directories"]}
            excluded_by_directory = {item["directory"]: item for item in directory_summary["excluded_directories"]}
            skipped_by_directory = {
                item["directory"]: item for item in directory_summary["skipped_non_source_directories"]
            }

            self.assertEqual(recorded_by_directory["app"]["source_files"], 1)
            self.assertEqual(recorded_by_directory["app"]["source_roles"], {"runtime_source": 1})
            self.assertEqual(recorded_by_directory["app"]["audit_scopes"], {"default_health_audit": 1})
            self.assertEqual(recorded_by_directory["tests"]["source_roles"], {"test_source": 1})

            self.assertEqual(excluded_by_directory["node_modules/leftpad"]["files"], 1)
            self.assertEqual(
                excluded_by_directory["node_modules/leftpad"]["reasons"],
                {"excluded path component: node_modules": 1},
            )
            self.assertEqual(skipped_by_directory["docs"]["files"], 1)
            self.assertEqual(skipped_by_directory["docs"]["reasons"], {"unsupported source extension": 1})
            self.assertEqual(coverage["directory_summary"], directory_summary)


if __name__ == "__main__":
    unittest.main()

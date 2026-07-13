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


def run_audit_inventory(project: Path, audit_path: Path) -> dict:
    subprocess.run(
        [
            sys.executable,
            str(INVENTORY_SCRIPT),
            str(project),
            "--audit-map-output",
            str(audit_path),
            "--pretty",
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return json.loads(audit_path.read_text(encoding="utf-8"))


def mark_all_human_audited(audit_path: Path, *, legacy_file_hash_only: bool = False) -> dict:
    audit_map = json.loads(audit_path.read_text(encoding="utf-8"))
    for item in audit_map["symbols"]:
        fingerprint = item["source_fingerprint"]
        item["audit"].update(
            {
                "status": "human_audited",
                "auditor": "unit-test",
                "audited_source_hash": fingerprint["source_hash"],
                "audited_symbol_hash": None if legacy_file_hash_only else fingerprint["symbol_hash"],
                "expired_reason": None,
            }
        )
    audit_path.write_text(json.dumps(audit_map, indent=2) + "\n", encoding="utf-8")
    return audit_map


def audit_statuses(audit_map: dict) -> dict[str, tuple[str, str | None]]:
    return {
        item["symbol"]: (item["audit"]["status"], item["audit"].get("expired_reason"))
        for item in audit_map["symbols"]
    }


class InventorySymbolScopeTests(unittest.TestCase):
    def test_changing_one_method_expires_only_that_method_and_its_class(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            source_path = project / "app" / "service.py"
            write(
                source_path,
                """
                class Service:
                    def start(self):
                        return "started"

                    def stop(self):
                        return "stopped"

                def helper():
                    return "helper"
                """,
            )
            subprocess.run(["git", "init"], cwd=project, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "add", "."], cwd=project, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            audit_path = project / ".doc_project_maintainer" / "project" / "symbol-audit-map.json"
            run_audit_inventory(project, audit_path)
            mark_all_human_audited(audit_path)

            write(
                source_path,
                """
                class Service:
                    def start(self):
                        return "started-v2"

                    def stop(self):
                        return "stopped"

                def helper():
                    return "helper"
                """,
            )
            statuses = audit_statuses(run_audit_inventory(project, audit_path))

            self.assertEqual(statuses["Service"], ("audit_expired", "symbol_hash_changed"))
            self.assertEqual(statuses["Service.start"], ("audit_expired", "symbol_hash_changed"))
            self.assertEqual(statuses["Service.stop"], ("human_audited", None))
            self.assertEqual(statuses["helper"], ("human_audited", None))

    def test_one_change_in_large_class_does_not_mass_expire_sibling_methods(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            source_path = project / "app" / "large_service.py"

            def class_source(changed_method: int | None = None) -> str:
                methods = []
                for index in range(40):
                    value = 999 if index == changed_method else index
                    methods.append(f"    def method_{index}(self):\n        return {value}")
                return "class LargeService:\n" + "\n\n".join(methods)

            write(source_path, class_source())
            subprocess.run(["git", "init"], cwd=project, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "add", "."], cwd=project, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            audit_path = project / ".doc_project_maintainer" / "project" / "symbol-audit-map.json"
            run_audit_inventory(project, audit_path)
            mark_all_human_audited(audit_path)

            write(source_path, class_source(changed_method=17))
            updated = run_audit_inventory(project, audit_path)
            expired = [item["symbol"] for item in updated["symbols"] if item["audit"]["status"] == "audit_expired"]
            current_methods = [
                item["symbol"]
                for item in updated["symbols"]
                if item["kind"] == "method" and item["audit"]["status"] == "human_audited"
            ]

            self.assertEqual(expired, ["LargeService", "LargeService.method_17"])
            self.assertEqual(len(current_methods), 39)

    def test_comments_formatting_and_line_moves_do_not_expire_python_symbols(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            source_path = project / "app" / "service.py"
            write(
                source_path,
                """
                class Service:
                    def start(self):
                        return "started"

                    def stop(self):
                        return "stopped"
                """,
            )
            subprocess.run(["git", "init"], cwd=project, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "add", "."], cwd=project, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            audit_path = project / ".doc_project_maintainer" / "project" / "symbol-audit-map.json"
            first = run_audit_inventory(project, audit_path)
            original_signatures = {
                item["symbol"]: item["source_fingerprint"]["signature_hash"] for item in first["symbols"]
            }
            mark_all_human_audited(audit_path)

            write(
                source_path,
                """
                # Module comment inserted before every symbol.


                class Service:
                    # Method comment and spacing changes are non-semantic.
                    def start(self):
                        return "started"


                    def stop(self):
                        return "stopped"
                """,
            )
            updated = run_audit_inventory(project, audit_path)

            self.assertTrue(all(item["audit"]["status"] == "human_audited" for item in updated["symbols"]))
            self.assertEqual(
                {item["symbol"]: item["source_fingerprint"]["signature_hash"] for item in updated["symbols"]},
                original_signatures,
            )

    def test_changing_top_level_function_does_not_expire_unrelated_methods(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            source_path = project / "app" / "service.py"
            write(
                source_path,
                """
                class Service:
                    def run(self):
                        return "running"

                def helper():
                    return "helper"
                """,
            )
            subprocess.run(["git", "init"], cwd=project, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "add", "."], cwd=project, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            audit_path = project / ".doc_project_maintainer" / "project" / "symbol-audit-map.json"
            run_audit_inventory(project, audit_path)
            mark_all_human_audited(audit_path)

            write(
                source_path,
                """
                class Service:
                    def run(self):
                        return "running"

                def helper():
                    return "helper-v2"
                """,
            )
            statuses = audit_statuses(run_audit_inventory(project, audit_path))

            self.assertEqual(statuses["helper"], ("audit_expired", "symbol_hash_changed"))
            self.assertEqual(statuses["Service"], ("human_audited", None))
            self.assertEqual(statuses["Service.run"], ("human_audited", None))

    def test_legacy_file_hash_audits_migrate_before_selective_expiration(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            source_path = project / "app" / "service.py"
            write(
                source_path,
                """
                class Service:
                    def first(self):
                        return 1

                    def second(self):
                        return 2
                """,
            )
            subprocess.run(["git", "init"], cwd=project, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "add", "."], cwd=project, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            audit_path = project / ".doc_project_maintainer" / "project" / "symbol-audit-map.json"
            run_audit_inventory(project, audit_path)
            mark_all_human_audited(audit_path, legacy_file_hash_only=True)

            migrated = run_audit_inventory(project, audit_path)
            self.assertTrue(all(item["audit"]["audited_symbol_hash"] for item in migrated["symbols"]))
            self.assertTrue(all(item["audit"]["status"] == "human_audited" for item in migrated["symbols"]))

            write(
                source_path,
                """
                class Service:
                    def first(self):
                        return 10

                    def second(self):
                        return 2
                """,
            )
            statuses = audit_statuses(run_audit_inventory(project, audit_path))
            self.assertEqual(statuses["Service"], ("audit_expired", "symbol_hash_changed"))
            self.assertEqual(statuses["Service.first"], ("audit_expired", "symbol_hash_changed"))
            self.assertEqual(statuses["Service.second"], ("human_audited", None))

    def test_unmigrated_legacy_audits_expire_conservatively_after_file_change(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            source_path = project / "app" / "service.py"
            write(
                source_path,
                """
                class Service:
                    def first(self):
                        return 1

                    def second(self):
                        return 2
                """,
            )
            subprocess.run(["git", "init"], cwd=project, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "add", "."], cwd=project, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            audit_path = project / ".doc_project_maintainer" / "project" / "symbol-audit-map.json"
            run_audit_inventory(project, audit_path)
            mark_all_human_audited(audit_path, legacy_file_hash_only=True)

            write(
                source_path,
                """
                class Service:
                    def first(self):
                        return 10

                    def second(self):
                        return 2
                """,
            )
            statuses = audit_statuses(run_audit_inventory(project, audit_path))
            self.assertTrue(all(status == "audit_expired" for status, _ in statuses.values()))
            self.assertTrue(all(reason == "source_hash_changed" for _, reason in statuses.values()))

    def test_script_assessed_status_does_not_count_as_agent_audit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            write(
                project / "app" / "server.py",
                """
                def handle_request(value):
                    return value.strip()
                """,
            )
            write(
                project
                / ".doc_project_maintainer"
                / "code"
                / "app"
                / "server.py"
                / "handle_request.md",
                """
                ---
                health:
                  overall: watch
                audit:
                  status: script_assessed
                  auditor: null
                  audited_at: null
                  audited_commit: null
                  audited_source_hash: null
                  confidence: unknown
                  expired_reason: null
                ---

                # handle_request

                ## Actual Role

                Strips whitespace from the provided value.
                """,
            )

            subprocess.run(["git", "init"], cwd=project, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "add", "."], cwd=project, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            audit_path = project / ".doc_project_maintainer" / "project" / "symbol-audit-map.json"

            subprocess.run(
                [
                    sys.executable,
                    str(INVENTORY_SCRIPT),
                    str(project),
                    "--audit-map-output",
                    str(audit_path),
                    "--verify-docs",
                    "--pretty",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            symbol = audit["symbols"][0]

            self.assertEqual(symbol["audit"]["status"], "script_assessed")
            self.assertNotIn("machine_assessment", symbol)
            self.assertIn("script_assessed", audit["audit_statuses"])
            self.assertEqual(audit["summary"]["script_assessed"], 1)
            self.assertEqual(audit["summary"]["agent_audited"], 0)
            self.assertNotIn("machine_assessment_summary", audit)

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

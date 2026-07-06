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
        '<html><head><meta charset="utf-8"><title>Project Maintainer Audit Report</title></head>'
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

#!/usr/bin/env python3
"""Render a self-contained Project Maintainer audit visualization report."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
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


def run_integrity_report(args: argparse.Namespace, paths: dict[str, Path]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    if args.skip_integrity_refresh:
        return None, {
            "fresh": False,
            "status": "skipped",
            "generatedAt": None,
            "message": "Integrity refresh skipped",
            "command": None,
            "reportPath": str(paths["integrity_report"]),
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
            "reportPath": str(paths["integrity_report"]),
        }
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return None, {
            "fresh": False,
            "status": "failed",
            "generatedAt": utc_now(),
            "message": f"Integrity refresh failed: invalid JSON output: {exc}",
            "command": command,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "reportPath": str(paths["integrity_report"]),
        }
    return report, {
        "fresh": True,
        "status": "fresh",
        "generatedAt": utc_now(),
        "message": "Integrity refresh succeeded",
        "command": command,
        "reportPath": str(paths["integrity_report"]),
        "summary": {
            "records": report.get("records"),
            "closure": report.get("closure"),
            "agentAuditTrustCounts": report.get("agent_audit_trust_counts"),
            "resultCounts": report.get("result_counts"),
        },
    }


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
        "scopes": [{"scope": DEFAULT_SCOPE}, {"scope": ALL_SCOPE}],
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
        "coverageFiles": coverage_map.get("files") if isinstance(coverage_map.get("files"), list) else [],
        "symbols": symbols,
    }


def render_html(model: dict[str, Any]) -> str:
    data = json.dumps(model, indent=2, sort_keys=True, ensure_ascii=False)
    return (
        "<!doctype html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "  <meta charset=\"utf-8\">\n"
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        "  <title>Project Maintainer Audit Report</title>\n"
        "  <style>\n"
        "    :root { color-scheme: light; --ink: #172026; --muted: #65717a; --line: #d9e0e6; --bg: #f7f9fb; --panel: #ffffff; --accent: #0f766e; }\n"
        "    * { box-sizing: border-box; }\n"
        "    body { margin: 0; font-family: Georgia, 'Times New Roman', serif; color: var(--ink); background: var(--bg); }\n"
        "    header { padding: 32px clamp(20px, 5vw, 56px) 24px; border-bottom: 1px solid var(--line); background: var(--panel); }\n"
        "    h1 { margin: 0 0 8px; font-size: clamp(30px, 5vw, 54px); line-height: 1; letter-spacing: 0; }\n"
        "    main { width: min(1200px, calc(100% - 32px)); margin: 24px auto 48px; }\n"
        "    .toolbar { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; margin-bottom: 18px; }\n"
        "    select { min-height: 40px; border: 1px solid var(--line); background: white; padding: 0 12px; }\n"
        "    .dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; }\n"
        "    .metric, section { border: 1px solid var(--line); background: var(--panel); padding: 16px; }\n"
        "    .metric span { display: block; color: var(--muted); font-size: 13px; }\n"
        "    .metric strong { display: block; margin-top: 6px; font-size: 28px; }\n"
        "    table { width: 100%; border-collapse: collapse; background: var(--panel); }\n"
        "    th, td { border-bottom: 1px solid var(--line); padding: 10px; text-align: left; vertical-align: top; }\n"
        "    code { font-family: Consolas, 'Courier New', monospace; font-size: 13px; }\n"
        "    .status.warning { color: #991b1b; font-weight: 700; }\n"
        "  </style>\n"
        "</head>\n"
        "<body>\n"
        "  <header>\n"
        "    <h1>Project Maintainer Audit Report</h1>\n"
        "    <p id=\"statusLine\" class=\"status\"></p>\n"
        "  </header>\n"
        "  <main>\n"
        "    <div class=\"toolbar\"><label>Scope <select id=\"scopeSelect\"><option value=\"default_health_audit\">Default health audit</option><option value=\"all\">All symbols</option></select></label></div>\n"
        "    <section><h2>Overview</h2><div id=\"dashboard\" class=\"dashboard\"></div></section>\n"
        "    <section><h2>Audit Items</h2><table id=\"detailsTable\"></table></section>\n"
        "  </main>\n"
        "  <script>\n"
        f"    const report = {data};\n"
        "    function activeSymbols() {\n"
        "      const scope = document.getElementById('scopeSelect').value;\n"
        "      return report.symbols.filter(item => scope === 'all' || item.auditScope === scope);\n"
        "    }\n"
        "    function renderDashboard() {\n"
        "      const rows = activeSymbols();\n"
        "      const audited = rows.filter(item => ['agent_audited','human_audited','out_of_scope'].includes(item.auditStatus)).length;\n"
        "      const unaudited = rows.filter(item => item.auditStatus === 'unaudited').length;\n"
        "      document.getElementById('dashboard').innerHTML = [['Symbols', rows.length], ['Audited', audited], ['Unaudited', unaudited], ['Open issues', rows.reduce((sum, item) => sum + item.issues.length, 0)]].map(([label, value]) => '<div class=\"metric\"><span>' + label + '</span><strong>' + value + '</strong></div>').join('');\n"
        "    }\n"
        "    function renderTable() {\n"
        "      document.getElementById('detailsTable').innerHTML = '<tr><th>Name</th><th>Source</th><th>Status</th><th>Health</th></tr>' + activeSymbols().map(item => '<tr><td>' + item.name + '<br><small>' + item.kind + '</small></td><td><code>' + item.source + ':' + (item.line || '') + '</code></td><td>' + item.auditStatus + '<br><small>' + item.trustResult + '</small></td><td>' + (item.health.overall || 'unknown') + '</td></tr>').join('');\n"
        "    }\n"
        "    function render() { renderDashboard(); renderTable(); }\n"
        "    document.getElementById('scopeSelect').value = report.defaultScope;\n"
        "    document.getElementById('scopeSelect').addEventListener('input', render);\n"
        "    const statusEl = document.getElementById('statusLine');\n"
        "    statusEl.className = 'status' + (report.status.integrity.status === 'failed' ? ' warning' : '');\n"
        "    statusEl.textContent = 'Generated ' + report.generatedAt + ' | Integrity: ' + report.status.integrity.message;\n"
        "    render();\n"
        "  </script>\n"
        "</body>\n"
        "</html>\n"
    )


def generate_report(args: argparse.Namespace) -> Path:
    paths = resolve_paths(args)
    coverage_map = read_json(paths["coverage_map"], "coverage-map.json")
    audit_map = read_json(paths["audit_map"], "symbol-audit-map.json")
    integrity_report, integrity_state = run_integrity_report(args, paths)
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

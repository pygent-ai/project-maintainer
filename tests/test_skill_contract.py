from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "project-maintainer"


def test_agent_audited_requires_real_agent_review_contract() -> None:
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    code_symbol_docs = (SKILL_ROOT / "references" / "code-symbol-docs.md").read_text(encoding="utf-8")
    templates = (SKILL_ROOT / "references" / "templates.md").read_text(encoding="utf-8")
    openai_yaml = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")

    combined = "\n".join([skill, code_symbol_docs, templates, openai_yaml])

    assert "Agent Symbol Audit Contract" in skill
    assert "must not mark a symbol `agent_audited`" in skill
    assert "`scripts/inventory_symbols.py` is not an auditor" in combined
    assert "real audit agent" in combined
    assert "read the symbol implementation" in combined
    assert "must remain `unaudited`" in combined


def test_script_assessment_is_separate_from_audit_completion() -> None:
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    code_symbol_docs = (SKILL_ROOT / "references" / "code-symbol-docs.md").read_text(encoding="utf-8")
    templates = (SKILL_ROOT / "references" / "templates.md").read_text(encoding="utf-8")
    openai_yaml = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")

    combined = "\n".join([skill, code_symbol_docs, templates, openai_yaml])

    assert "machine_assessment" not in combined
    assert "audit_integrity.py" in combined
    assert "script_assessed" in combined
    assert "trusted_agent_audit" in combined
    assert "provisional_agent_audit" in combined
    assert "closure_eligible" in combined
    assert "does not satisfy" in combined
    assert "must remain pending" in combined
    assert "status: script_assessed" in combined
    assert "audit:\n  status: unaudited" in code_symbol_docs


def test_entry_doc_template_defaults_to_unaudited() -> None:
    code_symbol_docs = (SKILL_ROOT / "references" / "code-symbol-docs.md").read_text(encoding="utf-8")
    template = code_symbol_docs.split("## Template", 1)[1]

    assert "status: unaudited" in template
    assert "status: agent_audited" not in template


def test_symbol_health_audit_workflow_blocks_batch_script_audits() -> None:
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    code_symbol_docs = (SKILL_ROOT / "references" / "code-symbol-docs.md").read_text(encoding="utf-8")
    templates = (SKILL_ROOT / "references" / "templates.md").read_text(encoding="utf-8")
    openai_yaml = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")

    combined = "\n".join([skill, code_symbol_docs, templates, openai_yaml])

    assert "Symbol Health Audit Workflow" in skill
    assert "single symbol audit" in combined
    assert "multiple symbol audit" in combined
    assert "one audit agent per required symbol" in combined
    assert "must not bulk-generate health" in combined
    assert "scripts may only inventory, queue, validate, or record" in combined
    assert "If independent audit agents are unavailable" in combined


def test_task_intent_router_separates_delivery_from_maintenance_aware_fix() -> None:
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    templates = (SKILL_ROOT / "references" / "templates.md").read_text(encoding="utf-8")
    openai_yaml = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")

    combined = "\n".join([skill, templates, openai_yaml])

    assert "Task Intent Router" in skill
    assert "Knowledge Base Delivery Mode" in combined
    assert "Maintenance-Aware Fix Mode" in combined
    assert "Project Maintainer must not be the primary debugging workflow" in combined
    assert "check whether `.doc_project_maintainer/` exists" in combined
    assert "ask the user whether to analyze first" in combined
    assert "artifact maintenance becomes part of the task completion criteria" in combined
    assert "synchronize affected artifact slices after verification" in combined


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

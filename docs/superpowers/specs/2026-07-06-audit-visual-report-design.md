# Audit Visual Report Design

## Goal

Add a one-command audit visualization report for Project Maintainer. The report should turn existing coverage and symbol audit JSON into a self-contained HTML file that can be opened directly in a browser for team review, risk triage, and security or maintenance reporting.

## Context

Project Maintainer currently stores audit results in machine-friendly files under `.doc_project_maintainer/project/`, especially `coverage-map.json`, `symbol-audit-map.json`, and `audit-integrity-report.json` when integrity reporting has been run. These files preserve maintenance state well, but they are hard for people to scan during a review.

The new capability must not change audit logic or promote audit states. It should be a read-only presentation layer over the existing data sources. It may invoke the existing integrity report command to refresh trust classification before rendering.

## Chosen Approach

Implement a static report generator script named:

```text
skills/project-maintainer/scripts/render_audit_report.py
```

The script will:

- Read `.doc_project_maintainer/project/coverage-map.json`.
- Read `.doc_project_maintainer/project/symbol-audit-map.json`.
- Run `audit_integrity.py report --scope all` before rendering.
- Write or refresh `.doc_project_maintainer/project/audit-integrity-report.json`.
- Generate a self-contained HTML report, defaulting to `.doc_project_maintainer/project/audit-report.html`.

The report is static and does not run a local server. If an agent later refreshes inventory, coverage, audit maps, or integrity reports after generating the HTML, the Project Maintainer skill instructions will require the agent to tell the user that the HTML report is based on older data and should be regenerated or refreshed in the browser.

## Non-Goals

- Do not alter audit promotion, verification, or health assessment logic.
- Do not bulk-generate health, issues, audit rationale, or `agent_audited` status.
- Do not add a long-running report server.
- Do not depend on external web services, CDNs, fonts, or packages.
- Do not make the report the source of truth. The JSON and symbol docs remain authoritative.

## Command Interface

Primary command:

```bash
python skills/project-maintainer/scripts/render_audit_report.py <repo-root>
```

Default behavior:

- Input artifact root: `<repo-root>/.doc_project_maintainer`.
- Coverage map: `.doc_project_maintainer/project/coverage-map.json`.
- Audit map: `.doc_project_maintainer/project/symbol-audit-map.json`.
- Integrity output: `.doc_project_maintainer/project/audit-integrity-report.json`.
- HTML output: `.doc_project_maintainer/project/audit-report.html`.
- Default visible scope in the page: `default_health_audit`.
- Embedded switchable scope: `all`.

Useful options:

```bash
--artifact-root <path>
--coverage-map <path>
--audit-map <path>
--integrity-report-output <path>
--output <path>
--scope default_health_audit|all
--skip-integrity-refresh
--signing-key-env PROJECT_MAINTAINER_AUDIT_SIGNING_KEY
--batch-reuse-threshold <n>
```

`--skip-integrity-refresh` exists for constrained environments, but the generated report must show that trust was not freshly verified.

## Data Flow

1. Load coverage map and symbol audit map.
2. Refresh trust data by invoking `audit_integrity.py report --scope all --report-output <audit-integrity-report.json>`.
3. Merge symbol records with integrity `records_detail` by symbol id.
4. Build a normalized report model:
   - symbol id, name, kind, class owner, source path, line range,
   - source role and audit scope,
   - coverage documentation state,
   - audit status,
   - health dimensions,
   - open issues,
   - trust result,
   - closure eligibility,
   - result codes,
   - derived risk level,
   - derived priority score.
5. Build grouped views:
   - overview metrics,
   - issue dimension counts,
   - health buckets,
   - risk buckets,
   - priority items,
   - directory/file/class/function scope tree,
   - filter facets.
6. Render one HTML document with embedded CSS, JavaScript, and JSON data.

## Risk And Priority Model

The report should not pretend that all non-healthy states are equal. Priority should be derived for display only, not written back to audit maps.

Suggested ordering:

1. `invalid_agent_audit`, integrity mismatch, unsigned agent audit, or untrusted script hash.
2. `suspicious_agent_audit` or suspicious batch signature reuse.
3. Open issue with severity `critical` or `high`.
4. `audit_expired`.
5. `unaudited` in the active audit scope.
6. `script_assessed` or `provisional_agent_audit`.
7. Open issue with severity `medium`.
8. Health dimension values indicating risk, such as `risky`, `weak`, `high`, or `poor`.
9. Open issue with severity `low`.
10. Trusted, human-audited, or out-of-scope records with no open issues.

The page should label derived risk as a report-level triage aid. It must still display the raw audit status, trust result, and result codes.

## Page Structure

The HTML report starts with a dashboard view.

### 1. Status Bar

Show:

- active scope,
- report generation time,
- coverage map generation time,
- symbol audit map generation time,
- integrity report refresh time or failure state,
- git head,
- dirty status,
- whether trust data was freshly refreshed.

### 2. Overview Dashboard

Show metrics for the active scope:

- audited count,
- unaudited count,
- script-assessed count,
- audit-expired count,
- closure-eligible count,
- pending count,
- trusted, suspicious, invalid, provisional agent-audit counts,
- high, medium, and low risk counts,
- healthy, watch, risky, and unknown health counts,
- current audit coverage percentage,
- top issue dimensions.

### 3. Priority View

Show the highest-priority records first. Each item should display:

- symbol name and kind,
- source file and line,
- risk label,
- audit status,
- trust result,
- main issue summary,
- why it is dangerous or pending,
- suggested action.

### 4. Scope View

Show a directory/file/class/function tree that makes it clear which areas are audited, unaudited, pending, or risky. The tree should support default `default_health_audit` scope and a switch to `all` scope.

### 5. Searchable Detail Table

The table should support:

- search by symbol, file, class, or method name,
- risk filter,
- audit status filter,
- trust result filter,
- health filter,
- directory or file filter,
- scope filter,
- sort by risk,
- sort by health,
- sort by source path,
- sort by audit state.

### 6. Item Detail

Selecting or expanding an item should show:

- name,
- kind,
- class owner when present,
- source file and line range,
- audit scope,
- source role,
- audit status,
- trust result,
- closure eligibility,
- health dimensions,
- open issues,
- danger reason,
- suggested action,
- linked entry doc path if available.

## Error Handling

Missing required maps:

- If `coverage-map.json` or `symbol-audit-map.json` is missing, fail the command and do not generate a misleading report.

Integrity refresh failure:

- Still generate HTML when possible.
- Mark trust state as `unverified`.
- Show a prominent warning at the top.
- Include a concise command failure summary and the attempted command.
- Do not count `agent_audited` records as trusted closure without a fresh trusted integrity result.

Missing or unreadable signing key:

- Do not fail merely because `PROJECT_MAINTAINER_AUDIT_SIGNING_KEY` is absent; preflight may run `audit_integrity.py ensure-key`, and the report refresh should load or create `.doc_project_maintainer/project/audit-signing-key.json`.
- Treat an unsupported, unreadable, or malformed artifact-local key as integrity refresh failure.
- Explain that agent audit trust could not be verified because the configured signing key source was unavailable or invalid.

Unknown schema or missing optional fields:

- Render unknown values as `unknown`.
- Add a data quality section listing missing fields or unrecognized schema values.

No open issues:

- Show that no open issues are recorded.
- Continue to show unaudited, script-assessed, audit-expired, provisional, suspicious, or invalid records.

Post-report data refresh:

- Update `SKILL.md` and README guidance so agents know that if they refresh inventory, coverage maps, symbol audit maps, or integrity reports after generating an HTML report, they must tell the user that the report reflects older data and should be regenerated or refreshed.

## Test Strategy

Use TDD for implementation.

Create `tests/test_render_audit_report.py` with temporary-project fixtures similar to the existing inventory and audit integrity tests.

Test cases:

- The generator produces a self-contained HTML file from real coverage and audit maps.
- The report contains overview metrics for audited, unaudited, pending, closure-eligible, and risk counts.
- The default displayed scope is `default_health_audit`.
- The embedded data includes `all` scope records for page-level switching.
- The priority model ranks invalid or suspicious trust results before lower-risk issues.
- High-severity issues appear in the priority view.
- `audit_expired` and `unaudited` records are visible as pending work.
- Search and filter data are embedded in the page.
- Successful `audit_integrity.py report` output is merged into symbol records.
- Failed integrity refresh still produces HTML with an explicit unverified warning.
- Missing coverage or audit map fails without producing a misleading report.
- HTML escaping prevents symbol names, issue text, and file paths from injecting markup.

Update `tests/test_skill_contract.py` to require:

- `SKILL.md` describes the audit visualization report command.
- `README.md` mentions the report capability.
- Skill guidance requires agents to warn users when report data becomes stale after later refreshes.

Run:

```bash
python -m pytest
python C:/Users/Administrator/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/project-maintainer
```

## Documentation Updates

Update:

- `README.md`: add report generation to the feature list and validation/usage section.
- `skills/project-maintainer/SKILL.md`: add report generation workflow and final-response guidance.
- `skills/project-maintainer/agents/openai.yaml`: mention report generation in the default prompt.
- `skills/project-maintainer/VERSION` and `metadata.yaml`: bump version during release work.

## Acceptance Criteria

- A user can run one command and open a self-contained HTML report in a browser.
- The report starts with a dashboard, not a raw table.
- The report answers what is audited, unaudited, risky, healthy, pending, and trusted.
- The report contains a priority view for team discussion.
- The report supports search, filters, and sort in the browser without external services.
- The report distinguishes trusted closure from provisional, suspicious, invalid, script-assessed, unaudited, and expired states.
- The report clearly states when integrity refresh failed or trust state is unverified.
- Existing audit logic remains unchanged.

# Audit Integrity Entrypoint Design

## Background

Project Maintainer health audits need to distinguish real agent or human review from automated or bulk script output. The current inventory script is useful for symbol discovery, coverage ledgers, and documentation verification, but it must not be treated as a reviewer.

The core problem is not that agents run scripts. Scripts are allowed and useful. The problem is when a script-generated or bulk-generated result is promoted to `agent_audited` and then treated as trusted closure without full verification.

## Goals

- Make audit file writes pass through a controlled script entrypoint.
- Use one `audit.status` progress state machine and remove the separate `machine_assessment` status model.
- Keep script-produced checks visible in `audit.status` without letting them satisfy audit closure.
- Make health-audit closure a derived decision from `audit.status`, current verification results, source hashes, and integrity checks, not from `audit.status` alone.
- Detect direct or out-of-band edits to audit output files.
- Distinguish likely bulk-generated audit output from per-action agent audit promotion.
- Give agents a non-error prompt when required audit-promotion metadata is missing, so they can rerun the script correctly.
- Preserve partial progress: missing agent metadata should downgrade to script assessment instead of failing the whole workflow.
- Use a dependency-light HMAC-SHA256 signing scheme for v1, while leaving the metadata schema open to a future public-key signature implementation.

## Non-Goals

- Do not try to prove cryptographically that an agent read the source code.
- Do not rely on file modification time as the main integrity signal.
- Do not prevent a fully malicious actor with repository write access from fabricating data.
- Do not bind the agent tool-call signature to the audited file, symbol, source path, or tests. It is a behavior signature, not source evidence.
- Do not make `audit.status` by itself answer whether the health audit is complete.

## Current State

The audit model should use one state machine for audit progress. There should be no separate `machine_assessment` status field. `script_assessed` belongs in `audit.status`, and `audit.status` answers "where is this symbol in the audit workflow?" rather than "has this symbol passed closure?"

This avoids semantic drift where one script treats machine assessment as separate while another script treats it as part of audit progress. It also prevents automated script checks from living in a second progress model that agents forget to inspect.

Closure is a separate derived predicate. Every report, CI check, final-response summary, and coordinator decision must compute closure from `audit.status` plus the latest integrity verification result. `audit.status` provides progress; the closure predicate decides whether that progress is trusted enough to satisfy the requested health-audit scope.

`audit.status` should allow:

- `unaudited`: no script, agent, or human has produced a current audit result.
- `script_assessed`: the controlled script processed the symbol or audit record, but no agent or human audit has been accepted.
- `agent_audited`: an agent audit claim was accepted through the controlled entrypoint with an agent call signature. This is provisional until full verification classifies it as trusted.
- `human_audited`: a human audit was accepted or confirmed.
- `audit_expired`: the audited source hash no longer matches current source.
- `out_of_scope`: the symbol is intentionally excluded with a reason.

Only `human_audited`, `out_of_scope`, and verified-trusted `agent_audited` records satisfy health-audit closure. Plain `agent_audited` means "accepted for review tracking," not "trusted for closure." `unaudited`, `script_assessed`, `audit_expired`, and unverified or suspicious `agent_audited` records are pending for closure.

Implementations should expose a single helper or report field equivalent to:

```text
closure_eligible =
  audit.status == "human_audited"
  OR audit.status == "out_of_scope"
  OR (
    audit.status == "agent_audited"
    AND latest_verification.trust_result == "trusted_agent_audit"
  )
```

Callers must not infer closure directly from raw status counts.

`script_assessed` must stay strictly limited to script processing, inventory checks, documentation-field checks, parser signals, metrics, or other automated evidence. It must not imply that an agent read the implementation, checked callers or callees, reviewed tests, or made a health judgment.

## Agent Audit Trust Model

`audit.status` is the progress state. Agent trust is a verification qualifier produced by `verify` or `report`, not a second progress state machine.

When `promote` receives a valid agent call signature batch, it may write `audit.status: agent_audited` immediately. That status is provisional by default. It records that an agent audit claim passed through the controlled entrypoint, not that the claim is trusted.

Full `verify` or `report` runs should classify each `agent_audited` record with one of these trust results:

- `provisional_agent_audit`: accepted through the controlled entrypoint, but no current full verification has established trust.
- `trusted_agent_audit`: integrity metadata is valid, source and entry-doc hashes are current, the script hash is trusted, the signature verifies, and the agent call fingerprint is unique within the configured comparison window.
- `suspicious_agent_audit`: the agent call fingerprint is missing, reused above the configured threshold, produced by an untrusted script, or otherwise suspicious.
- `invalid_agent_audit`: integrity, signature, status, source hash, or entry-doc hash verification failed.

Health-audit closure must use the trust result from the latest full verification. `audit.status: agent_audited` alone is not closure-eligible. `trusted_agent_audit` is closure-eligible; `provisional_agent_audit`, `suspicious_agent_audit`, and `invalid_agent_audit` are not.

The trust result is script output. `verify` and `report` should not mutate audit records, but they should optionally write a JSON verification report, for example with `--report-output <path>`, so the coordinator can show the result to an agent or human. If a user or coordinator decides to downgrade, expire, or mark a claim as suspicious after reviewing that output, the follow-up write must still go through the controlled entrypoint.

## Proposed Entrypoint

Add a dedicated script for audit promotion and integrity signing, for example:

```bash
python skills/project-maintainer/scripts/audit_integrity.py promote ^
  --repo-root <repo-root> ^
  --audit-map <repo-root>/.doc_project_maintainer/project/symbol-audit-map.json ^
  --entry-doc <repo-root>/.doc_project_maintainer/code/.../Symbol.md ^
  --symbol-id "<stable-symbol-id>" ^
  --source-file <repo-relative-source-path> ^
  --scope default_health_audit ^
  --signing-key-env PROJECT_MAINTAINER_AUDIT_SIGNING_KEY ^
  --agent-call-signature-json <path-to-signature-batch.json>
```

The script should support at least:

- `promote`: validate inputs, write or update audit fields, and attach integrity metadata.
- `verify`: recompute hashes and report whether the audit output was produced by the controlled entrypoint.
- `report`: print audit integrity status without modifying audit records.
- `mark`: apply a user-approved disposition such as downgrade to `script_assessed`, expire stale audits, or record that a suspicious result was reviewed. This mode is optional for v1 but any such write must use the same validation and signing rules.

This script should be the only writer for `audit.status`. Inventory or coverage scripts may produce candidate information, but they should not directly transition a symbol to `script_assessed`, `agent_audited`, or `human_audited` unless they call this same validation entrypoint.

## Required Input Parameters

These parameters identify what the script should operate on:

- `--repo-root`: target repository root.
- `--audit-map`: audit ledger path, usually `.doc_project_maintainer/project/symbol-audit-map.json`.
- `--entry-doc`: symbol entry doc path.
- `--symbol-id`: stable audit symbol identifier.
- `--source-file`: source file associated with the symbol.
- `--scope`: audit scope such as `default_health_audit` or `repository_coverage_only`.
- `--agent-call-signature-json`: optional recent tool-call batch signature.

These identify signer or verification behavior:

- `--signing-key-env`: environment variable name containing the HMAC signing secret. Default: `PROJECT_MAINTAINER_AUDIT_SIGNING_KEY`. Preflight can run `audit_integrity.py ensure-key --repo-root <repo-root>` to create `.doc_project_maintainer/project/audit-signing-key.json`; if the environment variable is absent, promote, verify, and report commands load that artifact-local key.
- `--key-id`: stable label for the signing secret, used for rotation and reporting.
- `--public-key`: reserved for a future Ed25519 verification mode; not required for v1 HMAC verification.
- `--strict`: optional mode that turns warnings into non-zero exits for CI.
- `--report-output`: optional JSON output path for `verify` or `report`.
- `--require-closure`: optional mode for `verify` that fails when the requested audit scope still has non-closure-eligible records.

## Script-Computed Fields

The script must compute these itself and must not trust caller-provided values:

- `payload_hash`: hash of canonicalized audit payload.
- `source_hash`: hash of the current source file.
- `entry_doc_hash`: hash of the current symbol entry doc.
- `audit_map_hash_before`: hash of the audit map before mutation.
- `audit_map_hash_after`: hash of the audit map after mutation, recorded as an observation field and excluded from the signed payload to avoid self-referential hashing.
- `script_hash`: hash of the entrypoint script.
- `git_head`: current repository commit.
- `git_status_short`: dirty worktree state.
- `signed_at`: script-generated UTC timestamp.
- `canonicalization`: canonicalization scheme name.

## Integrity Metadata

The script should attach integrity metadata to the generated or promoted audit record:

```yaml
integrity:
  schema: project-maintainer.audit-integrity.v1
  generated_by: audit_integrity.py
  script_hash: sha256...
  canonicalization: sorted-json-excluding-signature-payload-hash-and-observation-fields
  payload_hash: sha256...
  source_hash: sha256...
  entry_doc_hash: sha256...
  audit_map_hash_before: sha256...
  git_head: abc1234
  git_status_short: ""
  signed_at: "YYYY-MM-DDTHH:MM:SSZ"
  signature_algorithm: hmac-sha256
  key_id: project-maintainer-local-v1
  signer: project-maintainer-local-hmac
  signature: "..."
  observation:
    audit_map_hash_after: sha256...
```

The verifier should recompute these values and report mismatches as suspected out-of-band modification.

The signed payload must exclude fields whose values depend on the final signed record itself, including `integrity.signature`, `integrity.payload_hash`, and `integrity.observation.audit_map_hash_after`. Other computed fields, including `signed_at`, `source_hash`, `entry_doc_hash`, `audit_map_hash_before`, `script_hash`, `git_head`, and the normalized agent call fingerprint, should be included in the signed payload. This avoids hash cycles while still signing the meaningful claim.

## Verify Health Report Integrity

The integrity checker is the read-only counterpart to `promote`. Its job is to answer: "Was this health audit report produced by the controlled entrypoint, and is it still current?"

Use the same script in `verify` mode:

```bash
python skills/project-maintainer/scripts/audit_integrity.py verify ^
  --repo-root <repo-root> ^
  --audit-map <repo-root>/.doc_project_maintainer/project/symbol-audit-map.json ^
  --signing-key-env PROJECT_MAINTAINER_AUDIT_SIGNING_KEY ^
  --report-output <repo-root>/.doc_project_maintainer/project/audit-integrity-report.json ^
  --strict
```

Use `report` mode when a human-readable summary is needed without failing the command:

```bash
python skills/project-maintainer/scripts/audit_integrity.py report ^
  --repo-root <repo-root> ^
  --audit-map <repo-root>/.doc_project_maintainer/project/symbol-audit-map.json
```

### What Verify Must Check

`verify` should inspect every audit record in the health report and classify it. It should not modify audit records.

Required checks:

- `audit.status` is one of the allowed states.
- Closure candidate states (`agent_audited`, `human_audited`, `out_of_scope`) have the required fields for that state.
- `agent_audited` records have `integrity` metadata generated by the controlled entrypoint.
- `agent_audited` records have `agent_call_signature_batch`.
- `agent_audited` records are classified as provisional, trusted, suspicious, or invalid.
- `script_assessed` records do not count as closed.
- `audit_expired` records do not count as closed.
- `integrity.generated_by` is the expected script name.
- `integrity.script_hash` matches an allowed script hash or trusted script manifest.
- Recomputed canonical payload hash matches `integrity.payload_hash`.
- Recomputed source hash matches `integrity.source_hash`.
- Recomputed entry doc hash matches `integrity.entry_doc_hash`.
- Recomputed HMAC signature verifies against the configured verification secret.
- The record's `git_head` and dirty status are reported so reviewers know what source state was signed.
- Records that claim closure-candidate audit status but lack integrity metadata are reported as unsigned.
- Records whose integrity hash changed after signing are reported as suspected out-of-band edits.
- Repeated `agent_call_signature_batch.batch_hash` values across many records are reported as suspicious batch reuse.
- `agent_audited` records are closure-eligible only when classified as `trusted_agent_audit`.
- `--require-closure` fails if any requested-scope record is not closure-eligible, even when integrity verification itself passed.

`verify` should not require the tool-call batch to mention the source file or audited symbol. The batch is a behavior signature, not source evidence.

### Suggested Result Codes

Each audit record should receive one or more result codes:

- `valid_controlled_entrypoint`: signature, hashes, status, and required metadata are valid.
- `provisional_agent_audit`: record is `agent_audited`, but the current run has not established trusted closure.
- `trusted_agent_audit`: record is `agent_audited` and passed full trust verification, including fingerprint uniqueness.
- `script_assessed_only`: record was processed by the script but is not closure-eligible.
- `missing_agent_call_signature`: record requests or claims agent audit without a call signature batch.
- `unsigned_agent_audit`: record claims `agent_audited` but has no integrity signature.
- `integrity_mismatch`: payload or signature verification failed.
- `source_hash_changed`: source file no longer matches the signed source hash.
- `entry_doc_hash_changed`: symbol entry doc no longer matches the signed entry doc hash.
- `untrusted_script_hash`: signature was produced by a script hash that is not trusted.
- `invalid_audit_status`: status is missing or not in the allowed state machine.
- `suspicious_batch_signature_reuse`: the same batch hash was reused above the configured threshold.
- `invalid_agent_audit`: record claims `agent_audited`, but integrity, source, entry-doc, signature, or trusted-script verification failed.

### Suggested Exit Codes

Use predictable exit codes so CI and agents can react consistently:

- `0`: integrity verification completed without invalid signatures, invalid statuses, stale source hashes, stale entry-doc hashes, or suspicious fingerprint reuse. Pending audit states may still exist unless `--require-closure` is set.
- `1`: integrity mismatch, unsigned closure-candidate audit, invalid status, or untrusted script hash.
- `2`: source or entry docs changed, so one or more audits should be expired or rerun.
- `3`: suspicious batch signature reuse exceeded the configured threshold.
- `4`: `--require-closure` was set and one or more requested-scope records are not closure-eligible.

In non-strict mode, `report` can return `0` while printing all findings.

### Suggested Report Summary

`report` should print and optionally write JSON with:

- Total audit records.
- Counts by `audit.status`.
- Counts by agent audit trust result.
- Counts by result code.
- Closure-eligible audit count.
- Trusted agent audit count.
- Provisional or suspicious agent audit count.
- Pending audit count.
- Unsigned closure-candidate audit count.
- Integrity mismatch count.
- Source or entry-doc changed count.
- Unique `agent_call_signature_batch.batch_hash` count.
- Reused batch hashes with affected symbol ids.
- Whether `--require-closure` would pass for the requested scope.
- Recommended next action for each non-valid record.

Example summary:

```json
{
  "records": 120,
  "status_counts": {
    "unaudited": 20,
    "script_assessed": 40,
    "agent_audited": 55,
    "human_audited": 2,
    "audit_expired": 3,
    "out_of_scope": 0
  },
  "agent_audit_trust_counts": {
    "provisional_agent_audit": 0,
    "trusted_agent_audit": 55,
    "suspicious_agent_audit": 1,
    "invalid_agent_audit": 2
  },
  "result_counts": {
    "trusted_agent_audit": 55,
    "script_assessed_only": 40,
    "source_hash_changed": 3,
    "unsigned_agent_audit": 2,
    "suspicious_batch_signature_reuse": 1
  },
  "closure": {
    "scope": "default_health_audit",
    "eligible": 57,
    "pending": 63,
    "require_closure_passed": false
  },
  "recommended_action": "Expire stale audits, rerun unsigned agent audits through promote, and review reused batch signatures before treating agent audits as trusted."
}
```

### Handling Failed Verification

When `verify` finds invalid closure-candidate audit records, the coordinator should not treat the health report as current. The safest handling is:

- Keep invalid records visible in the report.
- Keep `agent_audited` records visible as audit claims, but treat provisional, suspicious, or invalid agent audits as pending for closure.
- Mark records with source hash changes as `audit_expired` only through the controlled script.
- Ask an agent or human to rerun `promote` for records that need fresh review.
- When a verification report finds unsigned, suspicious, or invalid records, the coordinator should present the report to the agent or human and ask whether to downgrade, mark suspicious, expire, or rerun review. The chosen disposition must be written through the controlled entrypoint.
- Record suspicious batch reuse in `project/build-plan.md` or the report output so it is not hidden by later inventory runs.

## Agent Call Fingerprint Batch

The agent call fingerprint is a behavior fingerprint. It records a comparable hash for the recent tool-call batch supplied by the agent when requesting promotion, but the tool execution details are not interpreted as file-level audit evidence.

Use a batch shape because the last tool action may be a parallel tool call with multiple tool uses:

```json
{
  "calls": [
    {
      "tool_name": "functions.shell_command",
      "raw_input": {
        "command": "Get-Content ...",
        "workdir": "E:\\Projects\\project-maintainer"
      }
    },
    {
      "tool_name": "functions.shell_command",
      "raw_input": {
        "command": "rg \"pattern\" ...",
        "workdir": "E:\\Projects\\project-maintainer"
      }
    }
  ]
}
```

The script should compute stable hashes from the submitted batch and preserve enough metadata to compare fingerprints across audit records:

```yaml
agent_call_signature_batch:
  status: provided
  submitted_at: "YYYY-MM-DDTHH:MM:SSZ"
  batch_hash: sha256...
  call_count: 2
  calls:
    - tool_name: functions.shell_command
      input_hash: sha256...
    - tool_name: functions.shell_command
      input_hash: sha256...
```

Rules:

- The normalized batch hash must be stored in the signed payload.
- The raw tool-call input is optional. If preserved, prefer a sidecar file referenced by hash or a redacted/truncated copy.
- The script may normalize call ordering for `batch_hash`, but it must keep the original call list.
- The script must not require the tool calls to mention the audited file, symbol, caller, or tests.
- The batch fingerprint is only a behavioral marker used for repeat detection and audit-entrypoint discipline.

## Supporting Audit Evidence

The agent call fingerprint batch is required for provisional promotion, but it is not audit evidence by itself. It makes the promotion traceable and comparable during full verification.

The artifact-local signing key exists to keep controlled agent workflow integrity stable across Project Maintainer tasks. It is stored with the artifact and is not a tamper-proof security boundary; a user or process with artifact write access can read the key and re-sign records.

Audit evidence fields may still be recorded to make the health judgment easier to review:

- `source_reviewed`: source paths or symbol ids the agent actually inspected.
- `caller_callee_reviewed`: relevant callers, callees, or a stated reason why none were needed.
- `tests_reviewed`: direct tests, indirect tests, verification commands, or explicit missing-test evidence.
- `health_rationale`: evidence-backed rationale for the health dimensions that changed or matter most.
- `issue_rationale`: concrete issue evidence, or a stated reason no issues were recorded.

Missing audit evidence should be reported as weaker review context, but it should not prevent `promote` from writing provisional `audit.status: agent_audited` when the required tool-call fingerprint and integrity metadata are present. Full trust is determined by the latest full verification report, especially fingerprint uniqueness, integrity validity, current hashes, and trusted script provenance.

## Downgrade Behavior

If `--agent-call-signature-json` is missing:

- Do not fail the script by default.
- Do not write `audit.status: agent_audited`.
- Write `audit.status: script_assessed`.
- Record a `downgrade_reason` explaining that the agent call signature was missing.
- Include a `missing_agent_call_signature` result code in the command output.
- Return a warning message, not an error.

Suggested warning:

```text
No agent call signature batch provided.
Recorded as audit.status=script_assessed only.
To promote to agent_audited, rerun with --agent-call-signature-json containing the recent tool-call batch.
```

If `--strict` is set, the same condition may return non-zero for CI or release enforcement.

## Batch Detection

The verifier or report mode should detect repeated fingerprints across audit records:

- Same `batch_hash` reused across many symbols.
- Same `input_hash` repeated across many records.
- Missing fingerprint on records claiming `agent_audited`.
- `agent_audited` records lacking integrity metadata.
- Fingerprint created by an unexpected script hash.

Suggested statuses:

- `valid_controlled_entrypoint`
- `provisional_agent_audit`
- `trusted_agent_audit`
- `missing_agent_call_signature`
- `script_assessed_only`
- `suspicious_batch_signature_reuse`
- `suspicious_agent_audit`
- `invalid_agent_audit`
- `integrity_mismatch`
- `unsigned_agent_audit`

Repeated fingerprints should not automatically prove misconduct. They should make bulk generation visible to the coordinator and prevent affected `agent_audited` records from being classified as trusted until reviewed or rerun.

## Promotion And Trust Rules

To write provisional `agent_audited`, the script should require:

- Existing symbol entry doc with `Actual Role`.
- Existing health fields.
- Current `source_hash`.
- Agent call fingerprint batch present.
- HMAC-SHA256 integrity metadata generated by the script.
- Current status is `unaudited`, `script_assessed`, or `audit_expired`, and the script performs an explicit transition to `agent_audited`.

The agent call fingerprint batch is sufficient to allow provisional promotion when the other required fields are valid. It is not sufficient for trusted closure. A periodic full verification pass must compare fingerprints across the audit map and classify each `agent_audited` record. Only `trusted_agent_audit` records count toward health-audit closure.

All status transitions should be owned by the unified validation script. Agents should not hand-edit `audit.status` in entry docs or audit maps.

## Implementation Plan

1. Add tests for downgrade behavior when no agent call signature is provided.
2. Add tests for computing stable per-call and batch fingerprint hashes, with optional redacted or sidecar raw-input preservation.
3. Add tests for repeated `batch_hash` reporting.
4. Add tests for HMAC-SHA256 signing, verification, wrong-key failure, and stable `key_id` reporting.
5. Add tests that canonicalization excludes `signature`, `payload_hash`, and observation-only `audit_map_hash_after` so verification does not self-reference.
6. Add tests that valid tool-call fingerprints allow provisional `agent_audited` promotion.
7. Add tests that provisional `agent_audited` records do not satisfy closure until full verification classifies them as `trusted_agent_audit`.
8. Add tests that duplicate or suspicious fingerprints keep affected `agent_audited` records out of trusted closure.
9. Add tests for `--require-closure` so integrity success and audit closure are not confused.
10. Implement `scripts/audit_integrity.py` with `promote`, `verify`, `report`, and optional `mark`.
11. Update `symbol-audit-map.json` generation to use only `audit.status` and remove `machine_assessment`.
12. Update skill docs and templates to describe the controlled entrypoint, unified status model, agent audit trust model, and closure predicate.
13. Add final-response checklist language requiring agents to report provisional, trusted, suspicious, invalid, closure-eligible, and pending audit counts during full health audits.

## Open Decisions

- Decide key rotation and `key_id` conventions for the v1 HMAC signing secret.
- Decide whether `--strict` is enabled by default in CI.
- Decide whether raw tool-call input should be embedded directly in audit records or stored in sidecar files referenced by hash.
- Decide reuse threshold for `suspicious_batch_signature_reuse`.
- Decide whether and when to add a future Ed25519 mode for public-key verification.

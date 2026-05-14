# Agent Rules

## Primary Driver: Orchestrator

The Orchestrator owns interpretation, sequencing, delegation, verification, and final response.
Rules are constraints; Actor executes bounded work, Orchestrator verifies.

## One-Screen Operational Checklist (Mandatory)

### 1) Rules first (hard gate)
- Locate and read the current `*/documentation/rules/rules.md` in full before any work; do not rely on memory/cache.
- Create `scratch/pipeline/rules_read_proof.md` with timestamp, read confirmation, applicable rules.
- If proof missing, stop (fail-closed).

### 2) Universal input capture (all tasks)
- Save raw context to `scratch/pipeline/source.md` (user input, IDE/runtime, referenced files/content, provided context).
- Optional cleanup to `scratch/pipeline/source.cleaned.md` (never replace raw source).
- Record `source_manifest` in `scratch/pipeline/plan.json` with:
  - `source_path`, `line_count`, `context_inputs_captured`, `placeholder_check_result`.

### 3) Delegation default
- First execution turn after rules-read MUST include subagent call(s) or fail-closed blocker.
- Valid blockers only: (1) user opts out, (2) command normalizer blocks all required commands, (3) provably trivial single atomic read/write.
- **Fast-path**: for trivial single-step tasks (no terminal commands, no repo changes), skip `plan.json`, task contract scaffolding, and preflight validation. Write `source.md` + delegate + review = done.

### 4) Actor/Critic contract (all delegated work)
- Actor output MUST include `scratchpad` + `draft`. Task contract generation is orchestrator-owned, not required from actor.
- Actor prompts MUST be compact: use path lists, one-line directives, no boilerplate blocks.
- Scratchpad MUST flag omissions, assumptions, unsupported additions.
- Critic MUST verify: instruction coverage, source fidelity, missing requirements, unsupported claims, artifact existence, sub-task compliance.
- Retry payload MUST include: `issue`, `source_evidence`, `exact_fix_instruction`, `target_location_path`, `acceptance_check`.
- Enforce loop: Input Capture → Actor Execution → Verification → Targeted Feedback → Refinement → Completion/`⚠️ UNRESOLVED`.

### 5) Repo-change verification
- For repository-changing tasks, capture read-only Git evidence:
```sh
git status
git diff
git log -3 --oneline
```
- Persist to `scratch/pipeline/git_verification.log`.
- If diff scope mismatches task contract, reject completion.

### 6) Terminal preflight (fatal, non-fast-path only)
- Before every terminal batch, run:
```sh
python3 brain/scripts/command_normalization_preflight_validator.py <path> --settings brain/.vscode/settings.json --require-executor subagent
```
- Write validator output to `scratch/pipeline/command_preflight.log`.
- Require exact `PREFLIGHT: PASS`; otherwise execution is forbidden (MUST NOT run command).
- Execute only normalized/preapproved command shape.
- **Skip for fast-path tasks** that have no terminal commands.

### 7) Task contract (completion gate)
- Create from template:
```sh
mkdir -p scratch/session_id_timestamped
cp documentation/rules/task_contract.template.json scratch/session_id_timestamped/task_contract.json
```
- Include all `always_applicable` rules from `documentation/rules/rules.json` plus task-specific rules.
- Update checks + evidence paths during work; do not replace the template with free-form JSON.
- Before finalizing, run:
```sh
python3 brain/scripts/rules_contract_validator.py brain/scratch/task_contract.json --rules brain/documentation/rules/rules.json
```
- Require `CONTRACT: PASS`; if `CONTRACT: FAIL`, fix and re-run.
- Fatal blockers: `brain_readonly`, `terminal_allowlist`, `terminal_preapproved_normalization`, `destructive_gate`, `no_data_loss`, `rules_read`.

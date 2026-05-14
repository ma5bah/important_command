#!/usr/bin/env python3
"""DEPRECATED: OpenCode actor/critic orchestration pipeline. 
The Orchestrator is now the primary OpenCode agent and calls the Actor subagent directly via tools."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))
from task_workspace import TaskWorkspace  # noqa: E402


ROOT = Path(__file__).resolve().parent
RULES_JSON = ROOT / "documentation" / "rules" / "rules.json"
VALIDATOR = ROOT / "scripts" / "rules_contract_validator.py"


def call_agent(agent: str, prompt: str) -> str:
    """Execute one OpenCode agent turn."""
    print(f"--- Calling {agent} ---")
    result = subprocess.run(
        ["opencode", "run", "--agent", agent, prompt],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"OpenCode agent '{agent}' failed with exit code {result.returncode}:\n{result.stderr.strip()}"
        )
    return result.stdout.strip()


def parse_json_response(raw: str) -> dict:
    """Parse a direct JSON response or a fenced JSON block."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(raw[start : end + 1])


def validate_contract(contract_path: Path) -> tuple[bool, str]:
    """Node C: deterministic Rules Contract Validator."""
    if not contract_path.exists():
        return False, f"task_contract.json does not exist at {contract_path}"
    result = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            str(contract_path),
            "--rules",
            str(RULES_JSON),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    output = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
    return result.returncode == 0 and "CONTRACT: PASS" in result.stdout, output or "Valid"


def run_pipeline(user_input: str, max_cycles: int) -> None:
    # --- Workspace init ---
    workspace = TaskWorkspace(task_slug="pipeline-run")
    workspace.write_master_context(prompt=user_input, source="", contract={})
    contract_path = workspace.workspace_path / "context" / "task_contract.json"
    print(f"[Workspace] {workspace.workspace_path}")

    print("[Node A5] Checking for ambiguity...")
    gate_prompt = (
        "Analyze the following task for high-impact ambiguity. "
        "Return JSON only: {\"ambiguous\": boolean, \"query\": \"string\"}.\n\n"
        f"TASK:\n{user_input}"
    )
    gate_resp = parse_json_response(call_agent("actor", gate_prompt))
    if gate_resp.get("ambiguous"):
        print(f"[Node AQ] Clarification needed: {gate_resp.get('query', 'Clarify the task.')}")
        return

    feedback = ""
    final_draft = ""
    for cycle in range(1, max_cycles + 1):
        workspace.start_cycle(cycle)
        workspace.update_pipeline_state(cycle, "actor", "running")
        print(f"[Node B] Actor drafting content, cycle {cycle}/{max_cycles}...")

        # Build context: filesystem workspace path + inline feedback for first read
        ws_context = workspace.get_context_for_agent("actor", cycle)
        actor_prompt = (
            ws_context + "\n\n"
            "Draft or repair the requested output and write task_contract.json to the workspace. "
            "Use @documentation/rules/task_contract.template.json as the contract shape. "
            "Use @documentation/rules/rules.json for rule IDs and tiers. "
            "Write context/task_contract.json inside the workspace path shown above. "
            "Return a brief status only after writing the file.\n\n"
            f"TASK:\n{user_input}"
        )
        if feedback:
            actor_prompt += f"\n\nFEEDBACK TO APPLY:\n{feedback}"
        actor_output = call_agent("actor", actor_prompt)
        workspace.commit_actor(
            cycle,
            scratchpad=actor_output,
            draft=actor_output,
            contract={},  # contract is written directly by actor to workspace
        )

        is_valid, validation_output = validate_contract(contract_path)
        workspace.commit_validation(cycle, is_valid, validation_output)
        if not is_valid:
            print(f"[Node C] Validation failed:\n{validation_output}")
            feedback = f"Fix task_contract.json so the validator passes. Validator output:\n{validation_output}"
            continue

        print("[Node C] CONTRACT: PASS")
        print("[Node H] Low-cost completeness recheck...")
        ws_context = workspace.get_context_for_agent("actor", cycle)
        recheck_prompt = (
            ws_context + "\n\n"
            "Review the task_contract.json in the workspace context dir and the task below "
            "for missed explicit requirements. "
            "Use only low-cost completeness checking: source/task coverage, required sections, constraints, and formatting. "
            "Return JSON only: {\"complete\": boolean, \"needs_high_cost_critic\": boolean, \"feedback\": \"string\"}. "
            "Set needs_high_cost_critic=true only for ambiguity, implicit context, contradiction, or edge-case reasoning.\n\n"
            f"TASK:\n{user_input}"
        )
        recheck = parse_json_response(call_agent("actor", recheck_prompt))
        workspace.commit_recheck(cycle, recheck)
        if not recheck.get("complete"):
            feedback = recheck.get("feedback", "Fix missed explicit requirements from the low-cost recheck.")
            print(f"[Node H] Missing explicit work found. Looping to Actor:\n{feedback}")
            continue
        if not recheck.get("needs_high_cost_critic"):
            workspace.commit_final(draft=final_draft)
            print(f"[Node Z] Pipeline success after low-cost recheck. Workspace: {workspace.workspace_path}")
            print(f"[Audit]   {workspace.git_log()}")
            return

        print("[Node E] High-cost Critic auditing...")
        ws_context = workspace.get_context_for_agent("critic", cycle)
        critic_prompt = (
            ws_context + "\n\n"
            "Review the task_contract.json and actor draft in the workspace against "
            "@documentation/rules/rules.json and the task below. "
            "Only handle advanced reasoning: ambiguity, implicit context reconstruction, contradictions, edge cases, or systemic errors. "
            "Return JSON only: {\"feedback_contract\": [{\"category\": \"string\", \"issue\": \"string\", \"resolved_context\": \"string\", \"action_required\": \"string\"}], \"needs_fix\": boolean}. "
            "Use an empty feedback_contract and needs_fix=false only if all criteria are met.\n\n"
            f"TASK:\n{user_input}"
        )
        critic_resp = parse_json_response(call_agent("critic", critic_prompt))
        feedback_items = critic_resp.get("feedback_contract", [])
        workspace.commit_critic(cycle, feedback_items)
        if not critic_resp.get("needs_fix") and not feedback_items:
            workspace.commit_final(draft=final_draft)
            print(f"[Node Z] Pipeline success after high-cost review. Workspace: {workspace.workspace_path}")
            print(f"[Audit]   {workspace.git_log()}")
            return

        feedback = json.dumps(feedback_items, indent=2)
        print(f"[Node F] Critic feedback received. Looping to Actor:\n{feedback}")

    raise RuntimeError(f"UNRESOLVED: pipeline did not pass within {max_cycles} cycles")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the OpenCode actor/critic pipeline.")
    parser.add_argument("task", help="Task instructions to process.")
    parser.add_argument("--max-cycles", type=int, default=3)
    args = parser.parse_args()
    run_pipeline(args.task, args.max_cycles)


if __name__ == "__main__":
    main()

---
description: Launch the Orchestrator Agent to plan and execute a task end-to-end
---
### Orchestrator — Task Runner

Read `documentation/prompt/orchestrator-agent.md` for your full operating instructions.

**Workflow:**
1. Disambiguate the task (halt if unresolvable ambiguity found)
2. Decompose into N steps → write `scratch/pipeline/plan.json`
3. For each step:
   - `intelligence_required: false` → delegate to actor (`opencode run --agent actor`), then review output yourself
   - `intelligence_required: true` → do it directly with your own reasoning
4. Aggregate all step outputs → `scratch/pipeline/final_output.md`
5. Write `scratch/pipeline/status.json` and report summary to user

**You are both the planner and the critic. The actor (MiniMax) handles mechanical work only.**

Begin with task: $ARGUMENTS

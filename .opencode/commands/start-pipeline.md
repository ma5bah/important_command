---
description: Initiates the Actor-Critic Orchestration Pipeline
---
### Pipeline Initiation
The system is now analyzing your requirements and running the MiniMax/Gemini loop.

**Logic Path:**
1. **Disambiguation Gate** (MiniMax)
2. **Drafting Phase** (MiniMax)
3. **Contract Validation** (Python deterministic validator)
4. **Low-Cost Completeness Recheck** (MiniMax)
5. **Deep Audit when needed** (Gemini 3.1 Pro)

**Action:**
!`opencode run --agent orchestrator "$ARGUMENTS"`

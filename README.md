# brain

A shared AI agent ruleset and knowledge base, used across all projects without being committed to them.

## What it is

- The **master brain** lives at `~/project/brain/`
- Each project (e.g. `~/project/XYZ/`) gets a **satellite clone** of brain inside it: `~/project/XYZ/brain/`
- The satellite is a plain `git clone` — not a submodule, not committed to the project repo

## Why

- Projects reference brain's rules, prompts, and agent configs locally
- Brain stays independent — updated centrally, pulled into each project on demand
- No brain files pollute the project's git history

## Script

`scripts/update.sh` — detects where it's run from and does the right thing:

| Run from | What it does |
|---|---|
| Master brain (`~/project/brain/`) | Pushes master brain → copies brain files into each project root → pulls latest in each satellite |
| A project (`~/project/XYZ/`) | Copies brain files into the project root |

## Typical workflow

```
# 1. Set up a new project
cd ~/project/XYZ
git clone <brain-repo> brain
bash brain/scripts/update.sh    # copies AGENTS.md etc. into XYZ root

# 2. Update brain and propagate to all projects
cd ~/project/brain
bash scripts/update.sh          # push + copy + pull all satellites
```

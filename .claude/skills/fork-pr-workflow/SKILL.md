---
name: fork-pr-workflow
description: Forks the original repository to `denizin42` and sets up branch rules and a template for creating pull requests
allowed-tools: Bash, Read, Grep, Glob
---

# Safe Fork & Pull Request Workflow Skill

## When to Use

Invoke before forking upstream, creating a feature branch, pushing to `denizin42`, or opening a fork-only PR.

## Fork & PR Commands

1. Call `verify_contribution_target` MCP tool to confirm `fork_owner` is `denizin42` and branch is not `main`/`master`.
2. Fork upstream if needed (`gh repo fork TheAlgorithms/Python --clone=false`).
3. Render PR body / submit to personal fork only:

```bash
DRY_RUN=false bash scripts/fork-and-submit-pr.sh
```

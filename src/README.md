# Target Output Directory for the AI Agent (`src/`)

This directory intentionally starts **without any pre-written Python code** (per `AGENTS.md` Phase 1 Context Engineering rules).

## Two-Phase Workflow (Same Pattern as Lab 5)

1. **Phase 1 — Human Setup (Context Engineering `TODO`s):**
   Complete the `TODO` sections in the repository's Context Engineering markdown, hook, skill, sub-agent, and MCP files:
   - `CLAUDE.md` (selected issue metadata table, `CONTRIBUTING.md` project memory rules, `Task()` sub-agent delegation, and `@./context/*.md` imports)
   - `.claude/settings.json` & `scripts/context-switcher.sh` (`UserPromptSubmit` hook and idempotent `add_context()` guard)
   - `context/contributing-rules.md` & `context/fork-pr-workflow.md` (and `.claude/context/`)
   - `.claude/skills/thealgorithms-contributing/SKILL.md` & `.claude/skills/fork-pr-workflow/SKILL.md`
   - `.claude/agents/contributing-reviewer.md` & `.claude/agents/issue-researcher.md`
   - `mcp_server.py` (`@mcp.tool`, `@mcp.resource`, and `@mcp.prompt`)

2. **Verify Phase 1 Context Engineering Setup:**
   Run `pytest -v` (`tests/test_lab6_progress.py`) until all Context Engineering tests are green.

3. **Phase 2 — Run the Coding Agent (`agy` / `claude`) Through Its Paces:**
   Launch your coding agent and instruct it to read `CLAUDE.md`. Using the harness you engineered, **the agent** will:
   - Delegate to `issue-researcher` to diagnose the root cause of the selected `TheAlgorithms/Python` issue in `maths/` or `data_structures/`.
   - Fix the upstream algorithm bug and add doctests in compliance with `CONTRIBUTING.md` (guided by your `thealgorithms-contributing` skill).
   - Generate the Python `CONTRIBUTING.md` auditor and safe fork/PR workflow modules inside `src/` (and unit tests in `tests/`).
   - Call the MCP tools in `mcp_server.py` and delegate to `contributing-reviewer` to audit the diff against `CONTRIBUTING.md`.
   - Create a feature branch, update `CHANGELOG.md`, and submit/prepare the fork-only Pull Request (`CONTRIBUTION_REPORT.md`) without touching upstream `TheAlgorithms/Python`.

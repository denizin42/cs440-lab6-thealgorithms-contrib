# Project Context: CS 440 Lab 6 — Contributing to `TheAlgorithms/Python`

## 1. Architecture & Two-Phase Workflow

This repository follows the same two-phase **Context Engineering** pattern as Lab 5:

- **Phase 1 (What You Do — Context Engineering Setup)**: You complete the `TODO`s in `CLAUDE.md`, `.claude/`, `context/`, `scripts/context-switcher.sh`, and `mcp_server.py` until `pytest -v` (`tests/test_lab6_progress.py`) is 100% green.
- **Phase 2 (What Your Coding Agent Figures Out)**: You launch your coding agent (`agy` / `claude`). Using the harness you built, **the agent** researches the open issue via `issue-researcher`, fixes the upstream bug in `maths/` or `data_structures/` following `CONTRIBUTING.md`, generates the Python fork/PR & compliance tooling in `src/`, audits its changes via `mcp_server.py` and `contributing-reviewer`, and submits/prepares the fork-only Pull Request.

### Selected Contribution Target (Agent Must Use These Values in Phase 2)

| Setting | Key | Selected Value |
| :--- | :--- | :--- |
| Upstream Issue Number | `issue_number` | `15656` |
| Target Algorithm File | `target_file` | `maths/binomial_distribution.py` |
| Personal Fork Owner | `fork_owner` | `denizin42` |
| Feature Branch Name | `branch_name` | `feature/fix_binomial_distribution` |

---

## 2. Project Memory & Context Routing (No Duplication)

To avoid **Context Bloat** (Context Engineering Lecture Slide 15), `CLAUDE.md` stores only the high-level **orchestration protocol and Phase 2 deliverables**, while detailed rules live in `@./context/*.md` and `.claude/skills/*/SKILL.md`:

- **Single-Source Context Routing**:
  - Detailed coding style, `PEP 484` type hints, `doctest` requirements, and `ruff`/`mypy` checks $\rightarrow$ defined once in `@./context/contributing-rules.md` (and audited via `.claude/skills/thealgorithms-contributing/SKILL.md`).
  - Personal fork safety (`denizin42`, never `TheAlgorithms/*`) and `.github/pull_request_template.md` formatting $\rightarrow$ defined once in `@./context/fork-pr-workflow.md` (and executed via `.claude/skills/fork-pr-workflow/SKILL.md`).

### Phase 2 Agent Deliverables (`src/` & Target Issue Fix)

1. Fix Issue `#15656` in `maths/binomial_distribution.py` so large `trials` (e.g., `n >= 171`) do not overflow `float(factorial(trials))`, and add `doctest` regression tests.
2. Generate the Python workflow package in `src/` providing:
   - An AST-based `CONTRIBUTING.md` compliance checker (verifying `snake_case`, PEP 484 type hints, docstrings, `>>>` doctests, and no `input()`).
   - A fork/PR safety validator that blocks `TheAlgorithms/*` and renders the `.github/pull_request_template.md` checklist.
3. Verify via MCP (`verify_contribution_target`) and sub-agents (`issue-researcher`, `contributing-reviewer`), and document results in `CONTRIBUTION_REPORT.md`.
4. Fork `TheAlgorithms/Python` to `denizin42/Python` and open the fork-only PR inside `denizin42/Python` by running `DRY_RUN=false bash scripts/fork-and-submit-pr.sh` (never target upstream `TheAlgorithms/*`).

---

## 3. Sub-Agent Delegation Rules (Subagents Lecture Slides 4–18)

You are the **Main Coding Agent (Orchestrator)**. Delegate isolated research and `CONTRIBUTING.md` code reviews to the bounded sub-agents in `.claude/agents/`:

```javascript
Task(
  description: "Review algorithm contribution against CONTRIBUTING.md",
  prompt: "Audit maths/binomial_distribution.py and src/ against CONTRIBUTING.md (snake_case, PEP 484 type hints, docstrings, doctests, and fork-only safety) and return a PASS/FAIL checklist.",
  subagent_type: "contributing-reviewer"
)

Task(
  description: "Research TheAlgorithms/Python open issue root cause",
  prompt: "Analyze Issue #15656 in maths/binomial_distribution.py, identify why float(factorial(trials)) overflows at trials >= 171, and return a root-cause summary and fix plan.",
  subagent_type: "issue-researcher"
)
```

---

## 4. Dynamic Context Imports (Context Engineering Lecture Slide 25)

@./context/contributing-rules.md
@./context/issue-brief.md
@./context/fork-pr-workflow.md

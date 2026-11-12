# Project Context: CS 440 Lab 6 — Contributing to `TheAlgorithms/Python`

## 1. Architecture & Two-Phase Workflow
This repository follows the same two-phase **Context Engineering** pattern as Lab 5:
- **Phase 1 (What You Do — Context Engineering Setup)**: You complete the `TODO`s in `CLAUDE.md`, `.claude/`, `context/`, `scripts/context-switcher.sh`, and `mcp_server.py` until `pytest -v` (`tests/test_lab6_progress.py`) is 100% green.
- **Phase 2 (What Your Coding Agent Figures Out)**: You launch your coding agent (`agy` / `claude`). Using the harness you built, **the agent** researches the open issue via `issue-researcher`, fixes the upstream bug in `maths/` or `data_structures/` following `CONTRIBUTING.md`, generates the Python fork/PR & compliance tooling in `src/`, audits its changes via `mcp_server.py` and `contributing-reviewer`, and submits/prepares the fork-only Pull Request.

### Selected Contribution Target (Agent Must Use These Values in Phase 2)
<!--
==============================================================================
TODO (Part 1 - Document Your Selected Issue & Personal Fork Target):
Replace the four `TODO_SET_VALUE` placeholders in the table below with your
chosen issue from `context/issue-brief.md` and your personal GitHub fork info:
  - `issue_number`: `15656`, `15655`, or `15576`
  - `target_file`: relative path to the algorithm file in this repo
  - `fork_owner`: your personal GitHub username (NEVER `TheAlgorithms`!)
  - `branch_name`: feature branch name (not `main` or `master`)
==============================================================================
-->
| Setting | Key | Selected Value |
| :--- | :--- | :--- |
| Upstream Issue Number | `issue_number` | `TODO_SET_VALUE` |
| Target Algorithm File | `target_file` | `TODO_SET_VALUE` |
| Personal Fork Owner | `fork_owner` | `TODO_SET_VALUE` |
| Feature Branch Name | `branch_name` | `TODO_SET_VALUE` |

---

## 2. How the Agent Must Follow `CONTRIBUTING.md` & Build `src/` (Project Memory)
<!--
==============================================================================
TODO (Part 2D - Project Memory & Agent Protocol in `CLAUDE.md`):
Read `CONTRIBUTING.md` and `.github/pull_request_template.md`, then replace
`TODO_PART_2D_WRITE_CONTRIBUTING_RULES` below with:
  1. The always-on `CONTRIBUTING.md` coding, docstring, doctest, and type-hint
     rules your agent must follow in every conversation.
  2. Instructions telling the agent what code features to generate inside `src/`
     (e.g., programmatic `CONTRIBUTING.md` compliance checker, safe fork/branch
     verifier that blocks upstream `TheAlgorithms/*`, and PR description builder)
     and how to fix the target issue and publish `CONTRIBUTION_REPORT.md`.
==============================================================================
-->
TODO_PART_2D_WRITE_CONTRIBUTING_RULES

---

## 3. Sub-Agent Delegation Rules (Subagents Lecture Slides 4–18)
You are the **Main Coding Agent (Orchestrator)**. Delegate isolated research and `CONTRIBUTING.md` code reviews to the bounded sub-agents in `.claude/agents/`:

```javascript
// ============================================================================
// TODO (Part 4B - Orchestrator Task Delegation, Subagents Lecture Slides 12 & 18):
// Wire the `Task()` calls below to your custom reviewer and researcher sub-agents
// in `.claude/agents/`, and write clear input prompts specifying the files/issues.
// ============================================================================

Task(
  description: "Review algorithm contribution against CONTRIBUTING.md",
  prompt: "TODO_SET_REVIEWER_PROMPT",
  subagent_type: "TODO_SET_REVIEWER_SUBAGENT"
)

Task(
  description: "Research TheAlgorithms/Python open issue root cause",
  prompt: "TODO_SET_RESEARCHER_PROMPT",
  subagent_type: "TODO_SET_RESEARCHER_SUBAGENT"
)
```

---

## 4. Dynamic Context Imports (Context Engineering Lecture Slide 25)
<!--
TODO (Part 2C - Dynamic Context Imports):
Add the `@./context/*.md` import directives at column 0 (outside this comment)
for the three context files in `context/` so Claude Code loads them dynamically.
-->

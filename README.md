# CS 440 Lab 6: Contributing to `TheAlgorithms/Python` with a Coding Agent Harness, Skills, Sub-Agents & MCP

**Course:** CS 440 — Introduction to Artificial Intelligence (Fall 2026)  
**Target Upstream Organization:** [`TheAlgorithms/Python`](https://github.com/TheAlgorithms/Python) *(Fork-Only — Never Contribute to Upstream!)*

---

## 1. Two-Phase Workflow: What **You** Do vs. What **Your Agent** Figures Out

Just like Lab 5, this repository splits the work into two distinct phases:

| Phase | Who Does It | What Happens |
| :--- | :--- | :--- |
| **Phase 1: Build the Coding Harness (`TODO`s)** | **You (The Student)** | You read [`CONTRIBUTING.md`](./CONTRIBUTING.md) and the three lecture decks (*Components of a Coding Agent*, *Agent Skills*, *Introduction to Subagents*), then complete the **12 Context Engineering `TODO`s** in `CLAUDE.md`, `.claude/`, `context/`, `scripts/context-switcher.sh`, and `mcp_server.py` until `pytest -v` (`tests/test_lab6_progress.py`) is **12/12 green**. |
| **Phase 2: Run the Agent Through Its Paces** | **Your Coding Agent (`agy` / `claude`)** | Once your harness tests are green, you launch your coding agent and tell it to resolve the selected `TheAlgorithms/Python` issue following `CLAUDE.md`. **The agent** uses your skills, sub-agents, hooks, and MCP server to diagnose the bug in `maths/` or `data_structures/`, fix the algorithm per `CONTRIBUTING.md`, generate the fork/PR automation inside `src/`, audit its diff via `contributing-reviewer`, and submit/prepare the fork-only Pull Request. |

---

## 2. Repository Structure

```text
cs440-lab6-thealgorithms-contrib/
├── README.md                                  # Two-phase workflow, TODO roadmap, and verification commands
├── CLAUDE.md                                  # [TODO Part 1, 2C, 2D, 4B] Target table, CONTRIBUTING.md memory, Task() rules
├── AGENTS.md -> CLAUDE.md                     # Symlink for multi-harness compatibility
├── CONTRIBUTING.md                            # Official unmodified TheAlgorithms/Python Contributing Guidelines
├── CHANGELOG.md                               # Keep a Changelog history (enforced by .githooks/pre-commit)
├── .mcp.json                                  # [Feature 2: MCP] Registers local FastMCP stdio server
├── mcp_server.py                              # [TODO Part 5A–5C] @mcp.tool, @mcp.resource, and @mcp.prompt
├── .claude/
│   ├── settings.json                          # [TODO Part 2A] UserPromptSubmit & PreToolUse safety hooks
│   ├── context/                               # [TODO Part 2E–2F] Modular context echoed by context-switcher.sh
│   │   ├── contributing-rules.md
│   │   ├── issue-brief.md
│   │   └── fork-pr-workflow.md
│   ├── skills/                                # [TODO Part 3A–3B] On-demand SKILL.md folders (Agent Skills Lecture)
│   │   ├── thealgorithms-contributing/
│   │   │   └── SKILL.md
│   │   └── fork-pr-workflow/
│   │       └── SKILL.md
│   └── agents/                                # [TODO Part 4A] Isolated sub-agents (Subagents Lecture)
│       ├── contributing-reviewer.md
│       └── issue-researcher.md
├── context/                                   # [TODO Part 2E–2F] Dynamic @./context/*.md files imported by CLAUDE.md
├── maths/                                     # Unmodified upstream TheAlgorithms/Python `maths` files (for Agent to fix!)
│   ├── binomial_distribution.py               # [Option A: Issue #15656] Overflow at 171 trials
│   └── continued_fraction.py                  # [Option B: Issue #15655] Float division precision/OverflowError
├── data_structures/
│   └── linked_list/
│       └── has_loop.py                        # [Option C: Issue #15576] O(n) visited set -> O(1) auxiliary space
├── scripts/
│   ├── context-switcher.sh                    # [TODO Part 2B] Dynamic context injection + idempotency guard
│   ├── prevent-main-commit.sh                 # PreToolUse guard blocking upstream PRs & direct main commits
│   ├── fork-and-submit-pr.sh                  # [TODO] Safe fork-only PR automation script
│   ├── demo-reset.sh                          # Resets Phase 2 agent output back to clean Phase 1 state
│   └── changelog-add.sh                       # Helper to add entries under ## [Unreleased] in CHANGELOG.md
├── src/
│   └── README.md                              # Empty target directory where the AI Agent generates its code in Phase 2
└── tests/
    └── test_lab6_progress.py                  # Phase 1 pytest suite verifying your 12 Context Engineering TODOs
```

---

## 3. Your Phase 1 `TODO` Roadmap (What the Professor Is Teaching)

Run `pytest -v` to track your progress across all 12 checks:

1. **Part 1 — Select Target Issue & Personal Fork (`CLAUDE.md`)**:
   - Fill in `issue_number`, `target_file`, `fork_owner`, and `branch_name` in the `CLAUDE.md` table (`TestPart1IssueTargetInMarkdown`).
2. **Part 2 — Hooks, Project Memory & Dynamic Context (*Components of a Coding Agent* & *Context Engineering*)**:
   - **Part 2A (`.claude/settings.json`)**: Wire `UserPromptSubmit` to `scripts/context-switcher.sh`.
   - **Part 2B (`scripts/context-switcher.sh`)**: Implement the idempotent check-then-append guard in `add_context()`.
   - **Part 2C (`CLAUDE.md`)**: Add the `@./context/*.md` dynamic context imports at column 0.
   - **Part 2D–2F (`CLAUDE.md`, `context/contributing-rules.md`, `context/fork-pr-workflow.md`)**: Read `CONTRIBUTING.md` and author the project memory and modular context files teaching the agent how to follow `CONTRIBUTING.md`, what to generate in `src/`, and how to handle the fork/PR workflow without touching upstream.
3. **Part 3 — On-Demand Agent Skills (*Agent Skills* Lecture)**:
   - **Part 3A (`.claude/skills/thealgorithms-contributing/SKILL.md`)**: Author the YAML frontmatter (`name`, `description` answering *what* and *when*, `allowed-tools`) and procedural checklist for `CONTRIBUTING.md`.
   - **Part 3B (`.claude/skills/fork-pr-workflow/SKILL.md` & `scripts/fork-and-submit-pr.sh`)**: Author the YAML frontmatter and procedural workflow for inspecting branch diffs (`git diff main...HEAD`), formatting the PR body, and submitting a PR strictly to your personal fork.
4. **Part 4 — Bounded Sub-Agents (*Introduction to Subagents* Lecture)**:
   - **Part 4A (`.claude/agents/contributing-reviewer.md` & `.claude/agents/issue-researcher.md`)**: Author the YAML frontmatter (scoping read-only vs. execution tools and preloading skills) and system prompts (defining structured output templates and `Obstacles Encountered` sections).
   - **Part 4B (`CLAUDE.md`)**: Wire orchestrator `Task()` delegation to `contributing-reviewer` and `issue-researcher`.
5. **Part 5 — Model Context Protocol Server (`mcp_server.py`)**:
   - **Part 5A**: Implement `@mcp.tool` `verify_contribution_target` (blocking upstream `TheAlgorithms` and `main`/`master` branch commits).
   - **Part 5B**: Implement `@mcp.resource("thealgorithms://issue-brief")` `get_issue_brief_resource`.
   - **Part 5C**: Implement `@mcp.prompt("audit_contribution")` `audit_contribution_prompt`.

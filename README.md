# CS 440 Lab 6: Contributing to `TheAlgorithms/Python` with a Coding Agent Harness, Skills, Sub-Agents & MCP

**Course:** CS 440 — Introduction to Artificial Intelligence (Fall 2026)  
**Target Upstream Organization:** [`TheAlgorithms/Python`](https://github.com/TheAlgorithms/Python) *(Fork-Only — Never Contribute to Upstream!)*

---

## 1. Quick Start for Professor & TA (`Makefile`)

Everything in this repository can be verified or executed directly via the root [`Makefile`](./Makefile):

```bash
# 1. Install Python dependencies (fastmcp, pydantic, pytest, pylint, mypy, ruff)
make install

# 2. Run all 35+ pytest harness, workflow, and telemetry tests
make test

# 3. Run pylint (10.00/10), ruff, and mypy static checks
make lint

# 4. Audit the fixed algorithm against CONTRIBUTING.md & run doctests
make compliance

# 5. Verify the local FastMCP server (resource + fork-safety validator)
make mcp-check

# 6. Dry-run the fork-only PR workflow (no remote push or PR created)
make demo-dry-run
```

### Running a Live Agent Benchmark & Fork Cleanup

`make benchmark` is **agent-agnostic** (`AGENT=auto` detects `claude` or `agy`, or pass `AGENT=claude`, `AGENT=agy`, or a custom `AGENT_CMD="..."`). It records wall-clock speed, token usage, sub-agent invocation (`issue-researcher`, `contributing-reviewer`), and changelog notes in [`PERFORMANCE_REPORT.md`](./PERFORMANCE_REPORT.md) + `logs/harness_performance.db`, and automatically cleans up `denizin42/Python` afterward:

```bash
# Auto-detect Claude Code or Antigravity (agy)
make benchmark VERSION=v6 LABEL="Benchmark Run" CHANGE="Describe harness/prompt change"

# Explicitly target Claude Code, Antigravity, or a custom agent CLI
make benchmark AGENT=claude VERSION=v6 LABEL="Claude Code Run"
make benchmark AGENT=agy VERSION=v6 LABEL="AGY Run"
make benchmark AGENT_CMD="my-agent -p 'Follow CLAUDE.md'" VERSION=v6
```

To manually close test PRs and prune feature branches on `denizin42/Python` at any time:

```bash
make cleanup-fork
```

---

## 2. Two-Phase Workflow: What **You** Do vs. What **Your Agent** Figures Out

| Phase | Who Does It | What Happens |
| :--- | :--- | :--- |
| **Phase 1: Context Engineering Harness** | **Student (Completed)** | Configured `CLAUDE.md`, symlinked `.claude/context/*.md`, `UserPromptSubmit` + `PreToolUse` hooks, on-demand skills (`denizin42-contributing`, `fork-pr-workflow`), bounded sub-agents (`issue-researcher`, `contributing-reviewer`), and `mcp_server.py`. |
| **Phase 2: Autonomous Agent Execution** | **Coding Agent (`agy`)** | Forks `TheAlgorithms/Python` → `denizin42/Python` first, diagnoses Issue `#15656` (`maths/binomial_distribution.py` overflow at `trials >= 171`), applies the log-space fix, generates `src/` workflow tooling, audits via `contributing-reviewer`, and opens a fork-only PR. |

---

## 3. Performance, Token & Sub-Agent Tracking (`PERFORMANCE_REPORT.md`)

Every benchmark run executed via [`scripts/track_performance.py`](./scripts/track_performance.py) logs to SQLite (`logs/harness_performance.db`) and regenerates [`PERFORMANCE_REPORT.md`](./PERFORMANCE_REPORT.md):

- **Wall-Clock Fix Duration & Delta vs. `v1` Baseline**
- **Token Usage** (`input_tokens`, `output_tokens`, `total_tokens` via `agy --output-format json`)
- **Sub-Agent Verification** (checks transcript/output for `issue-researcher` and `contributing-reviewer`)
- **Change / Changelog Attribution** (links each run to its `--change` or `CHANGELOG.md` entry)

---

## 4. Repository Structure

```text
cs440-lab6-thealgorithms-contrib/
├── Makefile                                   # One-command install, test, lint, compliance, benchmark, cleanup-fork
├── README.md                                  # Professor/TA quickstart, architecture, and verification guide
├── CLAUDE.md                                  # Single-source target config, context router, and Phase 2 deliverables
├── AGENTS.md -> CLAUDE.md                     # Symlink for multi-harness compatibility
├── CONTRIBUTING.md                            # Official unmodified TheAlgorithms/Python Contributing Guidelines
├── CHANGELOG.md                               # Keep a Changelog history
├── PERFORMANCE_REPORT.md                      # SQLite-backed agent speed, token usage, and sub-agent report
├── mcp_server.py                              # FastMCP server (@mcp.tool, @mcp.resource, @mcp.prompt)
├── .claude/
│   ├── settings.json                          # UserPromptSubmit & PreToolUse safety hooks
│   ├── context/                               # Symlinks to ../../context/*.md (zero duplication)
│   ├── skills/
│   │   ├── denizin42-contributing/            # SKILL.md + AST check_compliance.py
│   │   └── fork-pr-workflow/                  # SKILL.md + build_pr_body.py
│   └── agents/
│       ├── contributing-reviewer.md           # Preloads denizin42-contributing skill
│       └── issue-researcher.md                # Read-only issue root-cause researcher
├── context/                                   # Modular context rules imported by CLAUDE.md
├── maths/binomial_distribution.py             # Fixed Issue #15656 (math.comb + log-space fallback)
├── src/                                       # Generated compliance & fork-PR validator package
├── scripts/
│   ├── track_performance.py                   # SQLite + Markdown telemetry & Mermaid trend generator
│   ├── fork-and-submit-pr.sh                  # Fork-only PR submission script (blocks TheAlgorithms/*)
│   ├── cleanup-fork.sh                        # Closes test PRs & prunes feature branches on denizin42/Python
│   ├── context-switcher.sh                    # Dynamic context injection hook
│   └── prevent-main-commit.sh                 # PreToolUse guard blocking main commits & upstream PRs
└── tests/
    ├── test_lab6_progress.py                  # Phase 1 & harness verification suite
    └── test_src_workflow.py                   # Phase 2 src/ workflow unit tests
```

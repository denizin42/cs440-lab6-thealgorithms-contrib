# Phase 2 Fast-Path Playbook (Token & Latency Optimization)

Use this pre-digested map instead of running exploratory `ls`, `grep`, or redundant file reads:

1. **Repo Inventory (Already Ready)**:
   - `src/` (`__init__.py`, `compliance_checker.py`, `fork_pr_validator.py`) and `tests/test_src_workflow.py` are **already implemented** — only inspect/modify them if `pytest tests/test_src_workflow.py` fails.
   - Only `maths/binomial_distribution.py` needs the Issue `#15656` fix.
2. **One-Call Pre-Flight**:
   - Call MCP `get_phase2_fastpath_bundle()` once (returns `target_validation`, `issue_context`, `target_file_source`, `contributing_rules`, and `src_ready` in a single call).
   - Do **not** waste turns running `ls -la .claude/agents/`, reading `mcp_server.py`, reading `context/issue-brief.md`, or reading `maths/binomial_distribution.py` separately—you already have `target_file_source` and `contributing_rules` from the bundle.
3. **Diagnose & Fix Issue `#15656` (`maths/binomial_distribution.py`)**:
   - Have `issue-researcher` (`flash_lite`/`haiku`) diagnose the root cause of Issue `#15656` from `maths/binomial_distribution.py` and `context/issue-brief.md`, then implement a numerically stable fix with PEP 484 annotations, `<= 100`-char lines, and `doctest` regression cases.
4. **Single-Pass Sub-Agent Pattern (Do NOT Audit Twice)**:
   - Run `issue-researcher` (`flash_lite`/`haiku`) to diagnose the bug **before** reviewing.
   - Edit `maths/binomial_distribution.py`, then invoke `contributing-reviewer` (`flash_lite`/`haiku`) **once post-edit** to run `fast_audit.py maths/binomial_distribution.py` (which auto-fixes minor `ruff` formatting and returns exact lint/compliance errors).
   - Submit fork-only PR via `DRY_RUN=false bash scripts/fork-and-submit-pr.sh`, then run `pytest tests/test_src_workflow.py -q --tb=short` once.
5. **Never Stop Early on Sub-Agent Wakeup**:
   - Do **not** output a final summary or end your turn without tool calls until `maths/binomial_distribution.py` is edited, `contributing-reviewer` has audited it, `DRY_RUN=false bash scripts/fork-and-submit-pr.sh` has succeeded, and `pytest tests/test_src_workflow.py -q --tb=short` has passed.

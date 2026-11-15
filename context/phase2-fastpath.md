# Phase 2 Fast-Path Playbook (Token & Latency Optimization)

Use this pre-digested map instead of running exploratory `ls`, `grep`, or redundant file reads:

1. **Repo Inventory (Already Ready)**:
   - `src/` (`__init__.py`, `compliance_checker.py`, `fork_pr_validator.py`) and `tests/test_src_workflow.py` are **already implemented** — only inspect/modify them if `pytest tests/test_src_workflow.py` fails.
   - Only `maths/binomial_distribution.py` needs the Issue `#15656` fix.
2. **One-Call Pre-Flight**:
   - Call MCP `get_phase2_fastpath_bundle()` once (returns `target_validation`, `issue_context`, and `src_ready` in a single call).
3. **Exact Issue `#15656` Fix Pattern (`maths/binomial_distribution.py`)**:
   - Replace `float(factorial(trials))` with `math.comb(trials, successes)` when `probability > 0.0` (wrapped in `try ... except OverflowError`), falling back to log-space:
     `exp(lgamma(trials + 1) - lgamma(successes + 1) - lgamma(trials - successes + 1) + successes * log(prob) + (trials - successes) * log1p(-prob))`.
   - Keep `TypeError` (`not isinstance(..., int)`), `ValueError` checks, PEP 484 annotations, `<= 100`-char lines, and `doctest` cases (including `binomial_distribution(85, 171, 0.5)` and `binomial_distribution(20, 1000, 0.02)`).
4. **Single-Pass Sub-Agent Pattern (Do NOT Audit Twice)**:
   - Run `issue-researcher` (`flash_lite`/`haiku`) while checking MCP preflight (or skip redundant `ls`/`grep`).
   - Edit `maths/binomial_distribution.py` **first**, then invoke `contributing-reviewer` (`flash_lite`/`haiku`) **once post-edit** to run `fast_audit.py maths/binomial_distribution.py`.
   - Submit fork-only PR via `DRY_RUN=false bash scripts/fork-and-submit-pr.sh`.

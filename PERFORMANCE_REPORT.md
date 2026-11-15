# CS 440 Lab 6 — Agent Algorithm-Fix Performance Report

SQLite Database: `harness_performance.db` | Total Runs: **3** | Baseline: **`v1`** (v1 Agent Fix Run)

---

## 1. Baseline (`v1`) vs. Latest (`v12`) Algorithm-Fix Speed

| Metric | Baseline (`v1`) | Latest (`v12`) | Delta / Status |
| :--- | :---: | :---: | :---: |
| **Normalized Duration (incl. Cold Fork)** | `245.475 s` | `93.318 s` | `-152.1564 s (-62.0%)` |
| **Total Agent Tokens** | `n/a` | `59,295` | `in=51,684, out=7,611` |
| **Sub-Agents Invoked** | `unknown` | `issue-researcher, contributing-reviewer` | `issue-researcher` & `contributing-reviewer` |
| **Issue #15656 (`n=171`) Fix** | `RESOLVED` | `RESOLVED` | `maths/binomial_distribution.py` |
| **AST `CONTRIBUTING.md` Compliance** | `PASS` | `PASS` | `4` doctests |

---

## 2. Agent Fix Duration Trend (Seconds — Lower is Faster)

```mermaid
xychart-beta
    title "Agent Fix Duration (s) Across Harness Versions"
    x-axis ["v1", "v11", "v12"]
    y-axis "Agent Fix Duration (s)" 0 --> 306.84
    bar [245.475, 83.822, 93.318]
    line [245.475, 83.822, 93.318]
```

---

## 3. SQLite Run History (`agent_runs` Table)

| Run | Version | Change / Tuning | Duration | Delta vs. `v1` | Tokens | Sub-Agents | Verification |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| 1 | `v1` **(Baseline)** | v1 Agent Fix Run | `245.475s` (`+4.5s` fork) | `0.0 s (0.0%)` | `n/a` | `unknown` | RESOLVED (7 doctests) |
| 12 | `v11` | Removed solution hints from PROMPT/phase2-fastpath.md and added concise error details to fast_audit.py | `83.822s` (`+4.5s` fork) | `-161.6522 s (-65.9%)` | `57,647` | `issue-researcher, contributing-reviewer` | RESOLVED (4 doctests) |
| 14 | `v12` | Fix unescaped #15656 Make comment in Makefile PROMPT and instruct orchestrator never to output final summary until all 4 steps complete | `93.318s` (`+4.5s` fork) | `-152.1564 s (-62.0%)` | `59,295` | `issue-researcher, contributing-reviewer` | RESOLVED (4 doctests) |

---

## 4. Main Agent vs. Sub-Agent Breakdown (`v12`)

| Agent Role | Duration | Tokens | Responsibility |
| :--- | :---: | :---: | :--- |
| **Main Orchestrator** (`v12`) | `88.82 s` | `59,295` | Coordinates fork, sub-agents, PR & final verification |
| Sub-Agent: `issue-researcher` (`4a7abd64`) | `2.00 s` | `8,585` | Isolated context research / `CONTRIBUTING.md` audit |
| Sub-Agent: `contributing-reviewer` (`1fbe62b5`) | `5.00 s` | `14,706` | Isolated context research / `CONTRIBUTING.md` audit |

---

## 5. Phase 2 Deliverables, Issue `#15656` Fix & Passing Test Evidence

- **Modified Algorithm Target**: `maths/binomial_distribution.py` (fixed `float(factorial(trials))` `OverflowError` for `trials >= 171` using `math.comb` + log-space `lgamma`/`log`/`log1p`/`exp` fallback).
- **Generated Workflow Deliverables**: `src/__init__.py`, `src/compliance_checker.py`, `src/fork_pr_validator.py`, `tests/test_src_workflow.py`, `CONTRIBUTION_REPORT.md`

### Issue `#15656` Fix Implementation (`maths/binomial_distribution.py`)

```python
def binomial_distribution(successes: int, trials: int, prob: float) -> float:
    """
    Return probability of k successes out of n tries, with p probability for one
    success

    The function uses `math.comb` and falls back to log-space computation
    (`math.lgamma`) for very large `trials` to avoid float overflow.

    0.30870000000000003
    0.375
    0.060749764626165485
    0.017839
    """
    if successes > trials:
        raise ValueError("successes must be lower or equal to trials")
    if trials < 0 or successes < 0:
        raise ValueError("the function is defined for non-negative integers")
    if not isinstance(successes, int) or not isinstance(trials, int):
        raise TypeError("the function is defined for non-negative integers")
    if not 0 < prob < 1:
        raise ValueError("prob has to be in range of 1 - 0")
    probability = (prob**successes) * ((1 - prob) ** (trials - successes))
    try:
        return probability * comb(trials, successes)
    except OverflowError:
        log_coeff = (
            lgamma(trials + 1) - lgamma(successes + 1) - lgamma(trials - successes + 1)
        )
        log_prob = successes * log(prob) + (trials - successes) * log(1 - prob)
        return exp(log_coeff + log_prob)


if __name__ == "__main__":
    from doctest import testmod

    testmod()
```

### Live Passing Test & Compliance Proof

**1. `python3 -m doctest -v maths/binomial_distribution.py`:**

```text
Trying:
    round(binomial_distribution(1000, 2000, 0.5), 6)
Expecting:
    0.017839
ok
1 items had no tests:
    binomial_distribution
1 items passed all tests:
   4 tests in binomial_distribution.binomial_distribution
4 tests in 2 items.
4 passed and 0 failed.
Test passed.
```

**2. `fast_audit.py maths/binomial_distribution.py` (`CONTRIBUTING.md`, `ruff`, `mypy`, `pylint`):**

```json
{
  "target_file": "maths/binomial_distribution.py",
  "compliant": true,
  "doctests_passed": true,
  "ruff_ok": true,
  "mypy_ok": true,
  "pylint_ok": true,
  "lint_ok": true
}
```

**3. `pytest tests/test_src_workflow.py -q --tb=short` (Phase 2 `src/` Workflow Tests):**

```text
.....                                                                    [100%]
5 passed in 0.01s
```

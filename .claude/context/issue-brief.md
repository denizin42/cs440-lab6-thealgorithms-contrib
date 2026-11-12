# Open Issues Brief — `TheAlgorithms/Python` (`@./context/issue-brief.md`)

Below are three real open issues from [`TheAlgorithms/Python`](https://github.com/TheAlgorithms/Python/issues). Pick **one** in `CLAUDE.md` and `mcp_server.py` for your agent to investigate and resolve:

## Option A: Issue #15656 — `maths/binomial_distribution.py`
- **Issue Title**: `binomial_distribution` overflows at 171 trials even when the result is representable
- **Reproduction**:
  ```python
  from maths.binomial_distribution import binomial_distribution
  binomial_distribution(85, 171, 0.5)
  ```
- **Expected Behavior**: Should return approximately `0.060749764626165485` without raising `OverflowError`.

## Option B: Issue #15655 — `maths/continued_fraction.py`
- **Issue Title**: `continued_fraction` uses float division, producing invalid terms for large integers and raising `OverflowError`
- **Reproduction**:
  ```python
  from fractions import Fraction
  from maths.continued_fraction import continued_fraction
  continued_fraction(Fraction(10**400 + 1, 10**400))
  ```
- **Expected Behavior**: Should return `[1, 10**400]` using exact integer arithmetic without raising `OverflowError`.

## Option C: Issue #15576 — `data_structures/linked_list/has_loop.py`
- **Issue Title**: Optimize `Node.has_loop` to use constant auxiliary space instead of $O(n)$ space
- **Problem Statement**: `Node.has_loop` currently traverses the linked list via `list(self)` which allocates a `visited = set()` of every visited node ($O(n)$ memory).
- **Expected Behavior**: Detect cycles in $O(n)$ time and $O(1)$ auxiliary space while comparing node references (`is`) rather than node data values.

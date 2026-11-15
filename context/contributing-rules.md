# `TheAlgorithms/Python` Contributing Rules Context (`@./context/contributing-rules.md`)

## 1. Algorithm Scope & Repository Structure

- **Unique Algorithmic Value**: Submissions must perform internal calculations or data manipulations rather than acting as thin how-to wrappers around existing Python packages.
- **Fit Existing Directories**: Place files inside existing category directories (`maths/`, `data_structures/`, etc.); avoid creating new directories.
- **Protected Auto-Generated Files**: Never modify `README.md` or `DIRECTORY.md` (they are updated automatically by repo automation).
- **One File Per PR**: Each Pull Request must modify only the single selected `<target_file>` from `CLAUDE.md`.

## 2. Python Naming & Coding Style (`PEP 8` & `PEP 484`)

- **Target Runtime**: Write modern Python 3 (`3.15t+` compatible) using `f-strings` where they improve readability.
- **Naming Conventions**:
  - Filenames, function names, and variable names: descriptive `snake_case` (`lower_case_with_underscores`), no spaces or hyphens.
  - Class names: `CamelCase`.
  - Module constants: `UPPER_CASE`.
  - Avoid cryptic single-letter variable names and expand acronyms (e.g., `greatest_common_divisor` instead of `gcd`).
- **Explicit Type Hints (`PEP 484`)**: Every function parameter and return value must have explicit Python type annotations.
- **Pure Calculation Functions & Exceptions**:
  - Return calculation results directly instead of `print()` or plotting.
  - Never call interactive `input()`.
  - Raise explicit Python exceptions (`ValueError`, `TypeError`) on invalid or out-of-domain inputs.

## 3. Docstrings, Doctests & Local Verification Commands

- **Docstrings**: Every function requires a clear docstring explaining the algorithm and linking reference URLs (such as Wikipedia) when applicable. Comments should explain *why*, not repeat *what* the code does.
- **Doctests (`doctest`)**: Every function docstring must contain `>>>` doctest examples testing both valid inputs and erroneous inputs (`Traceback (most recent call last): ...`).
- **Required Pre-Submission Checks**:
  - Run doctests: `python3 -m doctest -v <target_file>`
  - Run formatter & linter: `ruff format` and `ruff check` (or `pre-commit run --all-files --show-diff-on-failure`)
  - Run static type & lint checks: `mypy <target_file>` and `python3 -m pylint <target_file>`

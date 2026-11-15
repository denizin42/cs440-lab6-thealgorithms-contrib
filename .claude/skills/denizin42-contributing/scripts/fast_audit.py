"""Single-command fast audit script for `denizin42-contributing` skill.

Runs AST compliance, doctest, ruff, mypy, and pylint on a target Python file
and prints a compact JSON summary (Agent Skills Slide 14: "Run scripts, don't read them").
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parents[4]
CHECK_SCRIPT = Path(__file__).resolve().parent / "check_compliance.py"


def _run_ok(cmd: list[str]) -> bool:
    """Execute a subprocess command quietly and return True when exit code is 0."""
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, check=False)
    return proc.returncode == 0


def run_fast_audit(target_rel: str) -> Dict[str, Any]:
    """Auto-format minor ruff issues, then run compliance, doctest, ruff, mypy, and pylint."""
    _run_ok([sys.executable, "-m", "ruff", "check", "--fix", "--quiet", target_rel])
    _run_ok([sys.executable, "-m", "ruff", "format", "--quiet", target_rel])
    comp_proc = subprocess.run(
        [sys.executable, str(CHECK_SCRIPT), target_rel],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    compliant = False
    if comp_proc.returncode == 0:
        compliant = bool(json.loads(comp_proc.stdout).get("compliant", False))

    doctests_ok = _run_ok([sys.executable, "-m", "doctest", target_rel])
    ruff_ok = _run_ok([sys.executable, "-m", "ruff", "check", "--quiet", target_rel])
    mypy_ok = _run_ok(
        [sys.executable, "-m", "mypy", "--no-error-summary", "--hide-error-context", target_rel]
    )
    pylint_ok = _run_ok([sys.executable, "-m", "pylint", "--reports=n", "--score=n", target_rel])
    return {
        "target_file": target_rel,
        "compliant": compliant,
        "doctests_passed": doctests_ok,
        "ruff_ok": ruff_ok,
        "mypy_ok": mypy_ok,
        "pylint_ok": pylint_ok,
        "lint_ok": ruff_ok and mypy_ok and pylint_ok,
    }


def main() -> int:
    """CLI entrypoint printing compact JSON audit results."""
    target = sys.argv[1] if len(sys.argv) > 1 else "maths/binomial_distribution.py"
    result = run_fast_audit(target)
    print(json.dumps(result, indent=2))
    return 0 if (result["compliant"] and result["doctests_passed"] and result["lint_ok"]) else 1


if __name__ == "__main__":
    sys.exit(main())

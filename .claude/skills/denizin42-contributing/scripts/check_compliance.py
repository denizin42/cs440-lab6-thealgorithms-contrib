"""Bundled AST Compliance Checker for `.claude/skills/denizin42-contributing`.

Demonstrates Agent Skills Lecture Slides 13–14 ("Bundled Resources" &
"Run scripts, don't read them"): the agent executes this script via Bash to
deterministically verify a Python algorithm file against `CONTRIBUTING.md`.

CLI usage:
    python3 .claude/skills/denizin42-contributing/scripts/check_compliance.py \\
        maths/binomial_distribution.py
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
import re
import sys
from typing import Any, List

SNAKE_CASE_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*$")


def check_contributing_compliance(file_path: str | Path) -> dict[str, Any]:
    """Audit a Python file against `TheAlgorithms/Python` `CONTRIBUTING.md`."""
    audit_file = ast.parse(Path(file_path).read_bytes(), filename=str(file_path))

    details: dict[str, dict[str, Any]] = {}
    missing_type_hints: List[str] = []
    missing_doctests: List[str] = []
    bad_names: List[str] = []
    uses_input = False

    for node in ast.walk(audit_file):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "input":
                uses_input = True

        if isinstance(node, ast.ClassDef):
            if ast.get_docstring(node) is None:
                details[f"class:{node.name} (line {node.lineno})"] = {
                    "type": "class",
                    "line": node.lineno,
                    "missing_docstring": True,
                }
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not SNAKE_CASE_PATTERN.match(node.name):
                bad_names.append(node.name)

            missing_args = [
                arg.arg
                for arg in node.args.args
                if arg.arg not in ("self", "cls", "class") and arg.annotation is None
            ]
            missing_return = node.returns is None
            if missing_args or missing_return:
                missing_type_hints.append(node.name)

            docstring = ast.get_docstring(node)
            missing_docstring = docstring is None
            if docstring is None or ">>>" not in docstring:
                missing_doctests.append(node.name)

            key = f"{node.name} (line {node.lineno})"
            if missing_args or missing_return or missing_docstring:
                details[key] = {
                    "type": "function",
                    "line": node.lineno,
                    "missing_args": missing_args,
                    "missing_return": missing_return,
                    "missing_docstring": missing_docstring,
                }
            else:
                details[key] = {
                    "compliant": node.lineno,
                }

    compliant = (
        not missing_type_hints
        and not missing_doctests
        and not bad_names
        and not uses_input
    )
    return {
        "compliant": compliant,
        "missing_type_hints": missing_type_hints,
        "missing_doctests": missing_doctests,
        "bad_names": bad_names,
        "uses_input": uses_input,
        "details": details,
    }


def main() -> int:
    """CLI entrypoint printing the JSON compliance report to stdout."""
    target = sys.argv[1] if len(sys.argv) > 1 else "maths/binomial_distribution.py"
    report = check_contributing_compliance(target)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

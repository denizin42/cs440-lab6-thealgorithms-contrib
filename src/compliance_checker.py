"""AST-based `CONTRIBUTING.md` compliance checker for Python algorithm files."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

SNAKE_CASE_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*$")
CAMEL_CASE_PATTERN = re.compile(r"^[A-Z][a-zA-Z0-9]*$")


@dataclass(frozen=True)
class ComplianceReport:
    """Structured result of an AST compliance audit."""

    file_path: str
    compliant: bool
    missing_type_hints: list[str] = field(default_factory=list)
    missing_docstrings: list[str] = field(default_factory=list)
    missing_doctests: list[str] = field(default_factory=list)
    bad_names: list[str] = field(default_factory=list)
    uses_input: bool = False


def _check_function_node(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    missing_type_hints: list[str],
    missing_docstrings: list[str],
    missing_doctests: list[str],
    bad_names: list[str],
) -> None:
    """Validate naming, PEP 484 annotations, docstrings, and doctests on a function."""
    if not SNAKE_CASE_PATTERN.match(node.name):
        bad_names.append(node.name)

    positional_and_kw = (
        list(node.args.posonlyargs) + list(node.args.args) + list(node.args.kwonlyargs)
    )
    missing_args = [
        arg.arg
        for arg in positional_and_kw
        if arg.arg not in ("self", "cls") and arg.annotation is None
    ]
    if node.args.vararg and node.args.vararg.annotation is None:
        missing_args.append(node.args.vararg.arg)
    if node.args.kwarg and node.args.kwarg.annotation is None:
        missing_args.append(node.args.kwarg.arg)

    if missing_args or node.returns is None:
        missing_type_hints.append(node.name)

    docstring = ast.get_docstring(node)
    if docstring is None:
        missing_docstrings.append(node.name)
        missing_doctests.append(node.name)
    elif ">>>" not in docstring:
        missing_doctests.append(node.name)


def check_file_compliance(file_path: str | Path) -> ComplianceReport:
    """Audit a Python file against `TheAlgorithms/Python` `CONTRIBUTING.md`.

    Verifies:
      - `snake_case` function names and `CamelCase` class names
      - PEP 484 parameter and return type annotations
      - Function and class docstrings
      - `>>>` doctest examples inside every function docstring
      - No interactive `input()` calls
    """
    path = Path(file_path)
    tree = ast.parse(path.read_bytes(), filename=str(path))

    missing_type_hints: list[str] = []
    missing_docstrings: list[str] = []
    missing_doctests: list[str] = []
    bad_names: list[str] = []
    uses_input = False

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "input"
        ):
            uses_input = True
        elif isinstance(node, ast.ClassDef):
            if not CAMEL_CASE_PATTERN.match(node.name):
                bad_names.append(node.name)
            if ast.get_docstring(node) is None:
                missing_docstrings.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _check_function_node(
                node,
                missing_type_hints,
                missing_docstrings,
                missing_doctests,
                bad_names,
            )

    compliant = not (
        missing_type_hints
        or missing_docstrings
        or missing_doctests
        or bad_names
        or uses_input
    )
    return ComplianceReport(
        file_path=str(path),
        compliant=compliant,
        missing_type_hints=missing_type_hints,
        missing_docstrings=missing_docstrings,
        missing_doctests=missing_doctests,
        bad_names=bad_names,
        uses_input=uses_input,
    )

"""Unit tests for the `src/` compliance checker and fork/PR safety validator."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.compliance_checker import check_file_compliance
from src.fork_pr_validator import (
    UpstreamTargetError,
    render_pr_checklist,
    validate_fork_pr_target,
)


def test_compliance_checker_passes_valid_module(tmp_path: Path) -> None:
    """Verify compliant functions pass all AST checks."""
    sample = tmp_path / "valid_algo.py"
    sample.write_text(
        '"""Sample module."""\n\n'
        "def add_numbers(first: int, second: int) -> int:\n"
        '    """Add two integers.\n\n'
        "    >>> add_numbers(1, 2)\n"
        "    3\n"
        '    """\n'
        "    return first + second\n",
        encoding="utf-8",
    )
    report = check_file_compliance(sample)
    assert report.compliant is True
    assert not report.missing_type_hints
    assert not report.missing_docstrings
    assert not report.missing_doctests
    assert not report.bad_names
    assert report.uses_input is False


def test_compliance_checker_flags_violations(tmp_path: Path) -> None:
    """Verify non-snake_case, missing hints/doctests, and input() are flagged."""
    sample = tmp_path / "bad_algo.py"
    sample.write_text(
        "def badName(x):\n    val = input('enter: ')\n    return val\n",
        encoding="utf-8",
    )
    report = check_file_compliance(sample)
    assert report.compliant is False
    assert "badName" in report.bad_names
    assert "badName" in report.missing_type_hints
    assert "badName" in report.missing_docstrings
    assert "badName" in report.missing_doctests
    assert report.uses_input is True


def test_validate_fork_pr_target_blocks_upstream_and_main() -> None:
    """Verify TheAlgorithms/* and main/master branches are rejected."""
    with pytest.raises(UpstreamTargetError):
        validate_fork_pr_target(
            "TheAlgorithms",
            "feature/fix_binomial_distribution",
            "maths/binomial_distribution.py",
        )
    with pytest.raises(UpstreamTargetError):
        validate_fork_pr_target(
            "denizin42",
            "main",
            "maths/binomial_distribution.py",
        )
    with pytest.raises(UpstreamTargetError):
        validate_fork_pr_target(
            "denizin42",
            "feature/fix_binomial_distribution",
            "maths/does_not_exist.py",
        )


def test_validate_fork_pr_target_accepts_personal_fork() -> None:
    """Verify valid personal fork and feature branch pass."""
    result = validate_fork_pr_target(
        "denizin42",
        "feature/fix_binomial_distribution",
        "maths/binomial_distribution.py",
    )
    assert "fork=denizin42" in result
    assert "branch=feature/fix_binomial_distribution" in result


def test_render_pr_checklist_includes_fixes_keyword() -> None:
    """Verify rendered PR body checks boxes and includes Fixes #15656."""
    body = render_pr_checklist(
        15656,
        "maths/binomial_distribution.py",
        "Avoid float overflow for large trials",
    )
    assert "Fixes #15656 in `maths/binomial_distribution.py`" in body
    assert "* [x] Fix a bug or typo in an existing algorithm?" in body
    assert "* [x] I have read [CONTRIBUTING.md]" in body

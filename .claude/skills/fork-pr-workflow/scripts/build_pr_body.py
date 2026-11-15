"""Bundled Pull Request Body Builder for `.claude/skills/fork-pr-workflow`.

Demonstrates Agent Skills Lecture Slide 8 ("Build a PR-description skill") and
Slide 14 ("Run scripts, don't read them"): generates a formatted Pull Request
description from `.github/pull_request_template.md` with checked `[x]` items
and the required `Fixes #<issue_number>` closing keyword.

CLI usage:
    python3 .claude/skills/fork-pr-workflow/scripts/build_pr_body.py \\
        15656 maths/binomial_distribution.py "Fix float overflow for trials >= 171"
"""
# pylint: disable=fixme

from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[4]
TEMPLATE_PATH = REPO_ROOT / ".github" / "pull_request_template.md"


def build_pr_body(issue_number: int, target_file: str, summary: str) -> str:
    """Render `.github/pull_request_template.md` for a single-file bugfix PR.

    ===========================================================================
    TODO (Part 6B - PR Description Builder Script, Agent Skills Lecture Slide 8):
    Read `TEMPLATE_PATH` (`.github/pull_request_template.md`) and return a
    completed Markdown PR description that:
      1. Includes `Fixes #<issue_number>` (per `CONTRIBUTING.md` "Issues" section
         and `.github/pull_request_template.md` line 20).
      2. Mentions `target_file` and `summary` under `### Describe your change`.
      3. Marks the relevant checklist boxes as `[x]` (e.g., `Fix a bug or typo
         in an existing algorithm?` and the `### Checklist` compliance items).

    HINTS:
    - Inspect `.github/pull_request_template.md` to see the exact `* [ ]` lines.
    - Test locally with:
        pytest -k test_part_6b -v
    ===========================================================================
    """
    _ = (issue_number, target_file, summary, TEMPLATE_PATH)
    # TODO (Part 6B): Implement PR template rendering and return the Markdown string
    raise NotImplementedError(
        "TODO (Part 6B): Implement `build_pr_body` in "
        "`.claude/skills/fork-pr-workflow/scripts/build_pr_body.py`."
    )


def main() -> int:
    """CLI entrypoint printing the rendered PR markdown body to stdout."""
    issue_num = int(sys.argv[1]) if len(sys.argv) > 1 else 15656
    target = sys.argv[2] if len(sys.argv) > 2 else "maths/binomial_distribution.py"
    summary_text = (
        sys.argv[3]
        if len(sys.argv) > 3
        else "Fix float overflow in binomial_distribution for large trials"
    )
    print(build_pr_body(issue_num, target, summary_text))
    return 0


if __name__ == "__main__":
    sys.exit(main())

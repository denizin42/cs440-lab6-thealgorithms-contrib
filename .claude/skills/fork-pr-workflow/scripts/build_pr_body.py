"""Bundled Pull Request Body Builder for `.claude/skills/fork-pr-workflow`.

Demonstrates Agent Skills Lecture Slide 8 ("Build a PR-description skill") and
Slide 14 ("Run scripts, don't read them"): generates a formatted Pull Request
description from `.github/pull_request_template.md` with checked `[x]` items
and the required `Fixes #<issue_number>` closing keyword.

CLI usage:
    python3 .claude/skills/fork-pr-workflow/scripts/build_pr_body.py \\
        15656 maths/binomial_distribution.py "Fix float overflow for trials >= 171"
"""

from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[4]
TEMPLATE_PATH = REPO_ROOT / ".github" / "pull_request_template.md"


def build_pr_body(issue_number: int, target_file: str, summary: str) -> str:
    """Render `.github/pull_request_template.md` for a single-file bugfix PR."""
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    sections = template.split("### Checklist", maxsplit=1)
    header_part = sections[0].replace(
        "### Describe your change",
        f"### Describe your change\n\nFixes #{issue_number} in `{target_file}`: {summary}.",
        1,
    ).replace(
        "* [ ] Fix a bug or typo",
        "* [x] Fix a bug or typo",
        1,
    )
    checklist_part = (
        sections[1].replace("* [ ] ", "* [x] ") if len(sections) > 1 else ""
    )
    return f"{header_part}### Checklist{checklist_part}\n"


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

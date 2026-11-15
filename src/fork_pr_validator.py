"""Fork-only safety validator and `.github/pull_request_template.md` renderer."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE_PATH = REPO_ROOT / ".github" / "pull_request_template.md"
FORBIDDEN_OWNERS = frozenset({"thealgorithms"})
FORBIDDEN_BRANCHES = frozenset({"main", "master"})


class UpstreamTargetError(ValueError):
    """Raised when a PR or push targets upstream `TheAlgorithms/*` or a protected branch."""


def validate_fork_pr_target(
    fork_owner: str,
    branch_name: str,
    target_file: str,
    repo_root: Path = REPO_ROOT,
) -> str:
    """Validate fork isolation, branch safety, and single-file `.py` scope.

    Raises:
        UpstreamTargetError: If `fork_owner` targets `TheAlgorithms`, `branch_name`
            is `main`/`master`, or `target_file` is invalid.
    """
    owner = fork_owner.strip()
    if (
        not owner
        or owner.lower() in FORBIDDEN_OWNERS
        or "thealgorithms" in owner.lower()
    ):
        raise UpstreamTargetError(
            f"Refusing to target upstream owner '{fork_owner}'. Use a personal fork."
        )

    branch = branch_name.strip()
    if not branch or branch.lower() in FORBIDDEN_BRANCHES:
        raise UpstreamTargetError(
            f"Refusing to target protected branch '{branch_name}'. Use a feature branch."
        )

    target_path = repo_root / target_file
    if not target_file.endswith(".py") or not target_path.is_file():
        raise UpstreamTargetError(
            f"Target file '{target_file}' must be an existing Python (.py) file."
        )

    return f"Validated fork={owner}, branch={branch}, file={target_file}"


def render_pr_checklist(
    issue_number: int,
    target_file: str,
    summary: str,
    template_path: Path = DEFAULT_TEMPLATE_PATH,
) -> str:
    """Render `.github/pull_request_template.md` with checked items and `Fixes #<issue>`."""
    if issue_number <= 0:
        raise ValueError("issue_number must be a positive integer.")

    template = template_path.read_text(encoding="utf-8")
    rendered_lines: list[str] = []
    in_checklist = False

    for line in template.splitlines():
        if line.startswith("### Checklist"):
            in_checklist = True
            rendered_lines.append(line)
            continue

        if line == "### Describe your change":
            rendered_lines.append(line)
            rendered_lines.append("")
            rendered_lines.append(
                f"Fixes #{issue_number} in `{target_file}`: {summary}."
            )
            continue

        if line.startswith("* [ ] Fix a bug or typo") or (
            in_checklist and line.startswith("* [ ] ")
        ):
            rendered_lines.append(line.replace("* [ ]", "* [x]", 1))
        else:
            rendered_lines.append(line)

    return "\n".join(rendered_lines) + "\n"

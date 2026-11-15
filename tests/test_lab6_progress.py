"""CS 440 Lab 6 Context Engineering & Coding Harness Verification Test Suite.

Verifies the human-configured Coding Agent Harness (CLAUDE.md, Hooks, Skills,
Sub-Agents, and MCP Server) BEFORE the AI agent solves the open issue from
`TheAlgorithms/Python` and generates the fork/PR solution in `src/`.

Run all checks:
    pytest -v
"""
# pylint: disable=too-few-public-methods,import-error,wrong-import-position
# pylint: disable=unsupported-membership-test,unsubscriptable-object

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mcp_server import (  # noqa: E402
    audit_contribution_prompt,
    get_issue_brief_resource,
    verify_contribution_target,
)


class TestPart1IssueTargetInMarkdown:
    """Verifies Part 1: Selected Issue & Personal Fork Target documented in `CLAUDE.md`."""

    def test_part_1_contribution_target_documented_in_claude_md(self) -> None:
        """Verify `CLAUDE.md` specifies issue_number, target_file, fork_owner, and branch_name."""
        claude_md = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        assert "TODO_SET_VALUE" not in claude_md, (
            "TODO Part 1: Replace all 4 TODO_SET_VALUE placeholders in the CLAUDE.md table"
        )
        for key in ("issue_number", "target_file", "fork_owner", "branch_name"):
            assert key in claude_md


class TestPart2HooksAndMemory:
    """Verifies Feature 1: Hooks, `CLAUDE.md` Project Memory, and `@./context/` files."""

    def test_part_2a_settings_json_hook_command(self) -> None:
        """Verify `.claude/settings.json` wires `UserPromptSubmit` to `context-switcher.sh`."""
        settings_path = REPO_ROOT / ".claude" / "settings.json"
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        hooks = settings["hooks"]["UserPromptSubmit"][0]["hooks"]
        command = hooks[0]["command"]
        assert "TODO_PART_2A" not in command, (
            "TODO Part 2A: Configure UserPromptSubmit hook command in .claude/settings.json"
        )
        assert "scripts/context-switcher.sh" in command

    def test_part_2b_context_switcher_idempotency_guard(self) -> None:
        """Verify `scripts/context-switcher.sh` uses `grep -qxF` to prevent duplicate imports."""
        script_path = REPO_ROOT / "scripts" / "context-switcher.sh"
        script_text = script_path.read_text(encoding="utf-8")
        assert "grep -qxF" in script_text, "TODO Part 2B: Use grep -qxF inside add_context()"
        assert "return 1" not in script_text, (
            "TODO Part 2B: Remove placeholder `return 1` in add_context()"
        )

    def test_part_2c_claude_md_dynamic_context_imports(self) -> None:
        """Verify `CLAUDE.md` contains uncommented `@./context/*.md` imports at column 0."""
        claude_md = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        active_lines = [
            line for line in claude_md.splitlines() if line.startswith("@./context/")
        ]
        assert "@./context/contributing-rules.md" in active_lines, (
            "TODO Part 2C: Add @./context/contributing-rules.md at column 0 in CLAUDE.md"
        )
        assert "@./context/issue-brief.md" in active_lines, (
            "TODO Part 2C: Add @./context/issue-brief.md at column 0 in CLAUDE.md"
        )
        assert "@./context/fork-pr-workflow.md" in active_lines, (
            "TODO Part 2C: Add @./context/fork-pr-workflow.md at column 0 in CLAUDE.md"
        )

    def test_part_2d_claude_md_project_memory_router(self) -> None:
        """Verify `CLAUDE.md` Section 2 defines non-duplicative routing and `src/` deliverables."""
        claude_md = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        assert "TODO_PART_2D_WRITE_CONTRIBUTING_RULES" not in claude_md.split("-->")[-1], (
            "TODO Part 2D: Write Project Memory & Context Routing in Section 2 of CLAUDE.md"
        )
        assert "src/" in claude_md

    def test_part_2e_contributing_rules_context_file(self) -> None:
        """Verify `context/contributing-rules.md` is authored and symlinked into `.claude/`."""
        contrib_path = REPO_ROOT / "context" / "contributing-rules.md"
        claude_ctx_path = REPO_ROOT / ".claude" / "context" / "contributing-rules.md"
        contrib_ctx = contrib_path.read_text(encoding="utf-8")
        body = contrib_ctx.split("-->")[-1]
        assert "TODO_PART_2E_WRITE_CONTRIBUTING_CONTEXT" not in body, (
            "TODO Part 2E: Author context/contributing-rules.md from CONTRIBUTING.md"
        )
        lowered = body.lower()
        for keyword in ("snake_case", "type", "doctest", "ruff", "directory.md"):
            assert keyword in lowered, (
                f"TODO Part 2E: Include '{keyword}' rule from CONTRIBUTING.md"
            )
        lines = contrib_ctx.splitlines()
        for idx, line in enumerate(lines[:-1]):
            if line.startswith("#"):
                assert lines[idx + 1] == "", (
                    f"MD022: Add a blank line after heading '{line}'"
                )
        assert claude_ctx_path.is_symlink()
        assert claude_ctx_path.read_text(encoding="utf-8") == contrib_ctx

    def test_part_2f_fork_pr_workflow_context_file(self) -> None:
        """Verify `context/fork-pr-workflow.md` is authored and symlinked into `.claude/`."""
        fork_path = REPO_ROOT / "context" / "fork-pr-workflow.md"
        claude_fork_path = REPO_ROOT / ".claude" / "context" / "fork-pr-workflow.md"
        fork_ctx = fork_path.read_text(encoding="utf-8")
        body = fork_ctx.split("-->")[-1]
        assert "TODO_PART_2F_WRITE_FORK_PR_CONTEXT" not in body, (
            "TODO Part 2F: Author context/fork-pr-workflow.md for safe fork & PR handling"
        )
        assert "TheAlgorithms" in body, (
            "TODO Part 2F: Explicitly state that PRs must never target upstream TheAlgorithms/*"
        )
        lines = fork_ctx.splitlines()
        for idx, line in enumerate(lines[:-1]):
            if line.startswith("#"):
                assert lines[idx + 1] == "", (
                    f"MD022: Add a blank line after heading '{line}'"
                )
        assert claude_fork_path.is_symlink()
        assert claude_fork_path.read_text(encoding="utf-8") == fork_ctx


class TestPart3Skills:
    """Verifies Feature 3: On-Demand Claude Code Skills & Bundled Scripts."""

    def test_part_3a_contributing_skill_authored(self) -> None:
        """Verify `.claude/skills/denizin42-contributing/SKILL.md` frontmatter and body."""
        skill_path = REPO_ROOT / ".claude" / "skills" / "denizin42-contributing" / "SKILL.md"
        if not skill_path.exists():
            skill_path = (
                REPO_ROOT / ".claude" / "skills" / "thealgorithms-contributing" / "SKILL.md"
            )
        skill_text = skill_path.read_text(encoding="utf-8")
        non_comment = "\n".join(
            line for line in skill_text.splitlines() if not line.lstrip().startswith("# ")
        )
        assert "TODO_PART_3A" not in non_comment, (
            f"TODO Part 3A: Complete YAML frontmatter in {skill_path.parent.name}/SKILL.md"
        )
        assert f"name: {skill_path.parent.name}" in non_comment
        assert "allowed-tools:" in non_comment

    def test_part_3b_fork_pr_workflow_skill_authored(self) -> None:
        """Verify `.claude/skills/fork-pr-workflow/SKILL.md` frontmatter and body."""
        skill_text = (
            REPO_ROOT / ".claude" / "skills" / "fork-pr-workflow" / "SKILL.md"
        ).read_text(encoding="utf-8")
        non_comment = "\n".join(
            line for line in skill_text.splitlines() if not line.lstrip().startswith("# ")
        )
        assert "TODO_PART_3B" not in non_comment, (
            "TODO Part 3B: Complete YAML frontmatter in fork-pr-workflow/SKILL.md"
        )
        assert "name: fork-pr-workflow" in non_comment
        assert "allowed-tools:" in non_comment

    def test_part_3c_skill_bundled_compliance_script(self) -> None:
        """Verify bundled AST compliance checker script in `.claude/skills/*/scripts/`."""
        script_path = (
            REPO_ROOT
            / ".claude"
            / "skills"
            / "denizin42-contributing"
            / "scripts"
            / "check_compliance.py"
        )
        assert script_path.exists(), (
            "check_compliance.py"
        )
        proc = subprocess.run(
            [sys.executable, str(script_path), "maths/binomial_distribution.py"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, f"check_compliance.py failed: {proc.stderr or proc.stdout}"
        report: Dict[str, Any] = json.loads(proc.stdout)
        for key in (
            "compliant",
            "missing_type_hints",
            "missing_doctests",
            "bad_names",
            "uses_input",
            "details",
        ):
            assert key in report, f"TODO Part 3C: Include '{key}' in JSON compliance output"


class TestPart4SubAgents:
    """Verifies Feature 4: Isolated Sub-Agents (`.claude/agents/*.md` and `CLAUDE.md`)."""

    def test_part_4a_contributing_reviewer_subagent(self) -> None:
        """Verify `.claude/agents/contributing-reviewer.md` frontmatter and system prompt."""
        reviewer_text = (
            REPO_ROOT / ".claude" / "agents" / "contributing-reviewer.md"
        ).read_text(encoding="utf-8")
        assert "TODO_PART_4A" not in reviewer_text, (
            "TODO Part 4A: Complete frontmatter and system prompt in contributing-reviewer.md"
        )
        assert "name: contributing-reviewer" in reviewer_text
        assert "Read" in reviewer_text and "Grep" in reviewer_text and "Bash" in reviewer_text

    def test_part_4a_issue_researcher_subagent(self) -> None:
        """Verify `.claude/agents/issue-researcher.md` frontmatter and system prompt."""
        researcher_text = (
            REPO_ROOT / ".claude" / "agents" / "issue-researcher.md"
        ).read_text(encoding="utf-8")
        assert "TODO_PART_4A" not in researcher_text, (
            "TODO Part 4A: Complete frontmatter and system prompt in issue-researcher.md"
        )
        assert "name: issue-researcher" in researcher_text
        assert "Read" in researcher_text and "Grep" in researcher_text

    def test_part_4b_claude_md_task_delegation(self) -> None:
        """Verify `CLAUDE.md` delegates to `contributing-reviewer` and `issue-researcher`."""
        claude_md = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        assert "TODO_SET_REVIEWER_SUBAGENT" not in claude_md, (
            "TODO Part 4B: Set contributing-reviewer in CLAUDE.md"
        )
        assert "TODO_SET_RESEARCHER_SUBAGENT" not in claude_md, (
            "TODO Part 4B: Set issue-researcher in CLAUDE.md"
        )
        assert 'subagent_type: "contributing-reviewer"' in claude_md
        assert 'subagent_type: "issue-researcher"' in claude_md


class TestPart5MCP:
    """Verifies Feature 2: MCP Server (`mcp_server.py` and `.mcp.json`)."""

    def test_part_5a_mcp_tool_verify_contribution_target(self) -> None:
        """Verify `@mcp.tool` `verify_contribution_target` validates fork and branch safety."""
        output: str = verify_contribution_target(
            issue_number=15656,
            target_file="maths/binomial_distribution.py",
            fork_owner="denizin42",
            branch_name="fix/issue-15656-binomial-overflow",
        )
        assert isinstance(output, str) and len(output.strip()) > 0

        # Must reject targeting upstream TheAlgorithms or committing to main
        with pytest.raises(ValueError):
            verify_contribution_target(
                issue_number=15656,
                target_file="maths/binomial_distribution.py",
                fork_owner="TheAlgorithms",
                branch_name="fix/issue-15656-binomial-overflow",
            )
        with pytest.raises(ValueError):
            verify_contribution_target(
                issue_number=15656,
                target_file="maths/binomial_distribution.py",
                fork_owner="denizin42",
                branch_name="main",
            )

    def test_part_5b_mcp_resource_issue_brief(self) -> None:
        """Verify `@mcp.resource` `thealgorithms://issue-brief` returns target dict."""
        data: Dict[str, Any] = get_issue_brief_resource()
        assert isinstance(data, dict)
        for key in ("issue_number", "target_file", "fork_owner", "branch_name"):
            assert key in data
            assert data[key] is not None

    def test_part_5c_mcp_prompt_audit_contribution(self) -> None:
        """Verify `@mcp.prompt` `audit_contribution` returns a non-empty instruction string."""
        prompt_text: str = audit_contribution_prompt(
            target_file="maths/binomial_distribution.py"
        )
        assert isinstance(prompt_text, str) and len(prompt_text.strip()) > 20
        assert "verify_contribution_target" in prompt_text


class TestPart6UpstreamGuardAndPRBuilder:
    """Verifies Part 6: PreToolUse Upstream PR Guard Hook & PR Template Builder Script."""

    def test_part_6a_prevent_upstream_pr_hook_script(self) -> None:
        """Verify `scripts/prevent-upstream-pr.sh` blocks upstream `TheAlgorithms` PRs (exit 2)."""
        script_path = REPO_ROOT / "scripts" / "prevent-upstream-pr.sh"
        assert script_path.exists(), "TODO Part 6A: Create scripts/prevent-upstream-pr.sh"

        # 1. Must block `gh pr create --repo TheAlgorithms/Python` with exit code 2
        blocked = subprocess.run(
            ["bash", str(script_path)],
            input=json.dumps(
                {"tool_input": {"command": "gh pr create --repo TheAlgorithms/Python --fill"}}
            ),
            capture_output=True,
            text=True,
            check=False,
        )
        assert blocked.returncode == 2, (
            "TODO Part 6A: scripts/prevent-upstream-pr.sh must exit with code 2 when "
            "a command targets TheAlgorithms/*"
        )

        # 2. Must allow `gh pr create --repo denizin42/Python` with exit code 0
        allowed = subprocess.run(
            ["bash", str(script_path)],
            input=json.dumps(
                {"tool_input": {"command": "gh pr create --repo denizin42/Python --fill"}}
            ),
            capture_output=True,
            text=True,
            check=False,
        )
        assert allowed.returncode == 0, (
            "TODO Part 6A: scripts/prevent-upstream-pr.sh must exit 0 for personal fork PRs"
        )

    def test_part_6b_pr_template_builder_script(self) -> None:
        """Verify `.claude/skills/fork-pr-workflow/scripts/build_pr_body.py` renders PR body."""
        script_path = (
            REPO_ROOT / ".claude" / "skills" / "fork-pr-workflow" / "scripts" / "build_pr_body.py"
        )
        assert script_path.exists(), (
            "TODO Part 6B: Implement .claude/skills/fork-pr-workflow/scripts/build_pr_body.py"
        )
        proc = subprocess.run(
            [
                sys.executable,
                str(script_path),
                "15656",
                "maths/binomial_distribution.py",
                "Avoid float overflow in binomial_distribution for trials >= 171",
            ],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, f"build_pr_body.py failed: {proc.stderr or proc.stdout}"
        body = proc.stdout
        assert "Fixes #15656" in body
        assert "[x]" in body.lower()
        assert "CONTRIBUTING.md" in body

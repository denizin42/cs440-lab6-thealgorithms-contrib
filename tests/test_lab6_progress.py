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
import sqlite3
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
    get_issue_root_cause_context,
    run_fast_compliance_audit,
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
        assert "fork-and-submit-pr.sh" in claude_md

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
        with pytest.raises(ValueError):
            verify_contribution_target(
                issue_number=15656,
                target_file="maths/binomial_distribution.py",
                fork_owner="denizin42",
                branch_name="master",
            )
        with pytest.raises(ValueError):
            verify_contribution_target(
                issue_number=0,
                target_file="maths/binomial_distribution.py",
                fork_owner="denizin42",
                branch_name="fix/issue-15656-binomial-overflow",
            )
        with pytest.raises(ValueError):
            verify_contribution_target(
                issue_number=15656,
                target_file="maths/does_not_exist.py",
                fork_owner="denizin42",
                branch_name="fix/issue-15656-binomial-overflow",
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
        """Verify `scripts/prevent-main-commit.sh` blocks upstream `TheAlgorithms` PRs (exit 2)."""
        script_path = REPO_ROOT / "scripts" / "prevent-main-commit.sh"
        assert script_path.exists(), "Missing scripts/prevent-main-commit.sh"

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
            "scripts/prevent-main-commit.sh must exit with code 2 when "
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
            "scripts/prevent-main-commit.sh must exit 0 for personal fork PRs"
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

    def test_part_6c_fork_and_submit_pr_script(self) -> None:
        """Verify `scripts/fork-and-submit-pr.sh` dry-run passes and blocks upstream."""
        script_path = REPO_ROOT / "scripts" / "fork-and-submit-pr.sh"
        script_text = script_path.read_text(encoding="utf-8")
        assert "TODO" not in script_text

        blocked = subprocess.run(
            ["bash", str(script_path)],
            cwd=str(REPO_ROOT),
            env={
                "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
                "FORK_OWNER": "TheAlgorithms",
            },
            capture_output=True,
            text=True,
            check=False,
        )
        assert blocked.returncode != 0

        dry_run = subprocess.run(
            ["bash", str(script_path)],
            cwd=str(REPO_ROOT),
            env={
                "PATH": (
                    f"{Path(sys.executable).parent}:"
                    "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"
                ),
                "DRY_RUN": "true",
            },
            capture_output=True,
            text=True,
            check=False,
        )
        assert dry_run.returncode == 0, (
            f"fork-and-submit-pr.sh failed: {dry_run.stderr or dry_run.stdout}"
        )
        assert "denizin42/Python" in dry_run.stdout


class TestPart7PerformanceTracker:
    """Verifies Part 7: Agent & Harness Performance Tracker (`scripts/track_performance.py`)."""

    def test_part_7_agent_harness_performance_tracker(self, tmp_path: Path) -> None:
        """Verify `scripts/track_performance.py` measures harness, context, and algo metrics."""
        script_path = REPO_ROOT / "scripts" / "track_performance.py"
        assert script_path.exists(), "Missing scripts/track_performance.py"

        db_file = tmp_path / "perf.db"
        report_file = tmp_path / "PERFORMANCE_REPORT.md"

        # 1. Record v1 baseline run timing a simulated agent command
        v1_proc = subprocess.run(
            [
                sys.executable,
                str(script_path),
                "--version",
                "v1",
                "--baseline",
                "--label",
                "v1 Baseline Harness",
                "--agent-cmd",
                f"{sys.executable} -c \"import time; time.sleep(0.05)\"",
                "--db-file",
                str(db_file),
                "--report-file",
                str(report_file),
                "--json",
            ],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        assert v1_proc.returncode == 0, f"track_performance.py failed: {v1_proc.stderr}"
        v1_metrics: Dict[str, Any] = json.loads(v1_proc.stdout)
        for key in (
            "version_tag",
            "is_baseline",
            "label",
            "agent_duration_sec",
            "harness_eval_ms",
            "harness_score_pct",
            "context_efficiency",
            "algorithm_benchmark",
            "feature_breakdown",
        ):
            assert key in v1_metrics, f"Missing '{key}' in performance metrics JSON"

        assert v1_metrics["version_tag"] == "v1"
        assert v1_metrics["is_baseline"] is True
        assert v1_metrics["agent_duration_sec"] >= 0.04
        assert db_file.exists() and report_file.exists()

        # 2. Record v2 tuned run and verify SQLite baseline comparison
        v2_proc = subprocess.run(
            [
                sys.executable,
                str(script_path),
                "--version",
                "v2",
                "--label",
                "v2 Tuned Prompts",
                "--agent-duration-sec",
                "0.02",
                "--db-file",
                str(db_file),
                "--report-file",
                str(report_file),
                "--json",
            ],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        assert v2_proc.returncode == 0, f"v2 run failed: {v2_proc.stderr}"
        v2_metrics: Dict[str, Any] = json.loads(v2_proc.stdout)
        assert "delta_vs_baseline_sec" in v2_metrics
        assert v2_metrics["delta_vs_baseline_sec"] < 0.0

        with sqlite3.connect(db_file) as conn:
            rows = conn.execute(
                "SELECT version_tag, is_baseline, agent_duration_sec FROM agent_runs ORDER BY id"
            ).fetchall()
        assert len(rows) == 2
        assert rows[0][0] == "v1" and rows[0][1] == 1
        assert rows[1][0] == "v2" and rows[1][1] == 0

        report_text = report_file.read_text(encoding="utf-8")
        assert "xychart-beta" in report_text
        assert "Agent Fix Duration" in report_text
        assert "v1" in report_text and "v2" in report_text

        # 3. Verify non-JSON run prints live progress & summary to console
        v2_proc = subprocess.run(
            [
                sys.executable,
                str(script_path),
                "--version",
                "v3",
                "--label",
                "v3 Console Output Check",
                "--agent-duration-sec",
                "0.01",
                "--db-file",
                str(db_file),
                "--report-file",
                str(report_file),
            ],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        assert v2_proc.returncode == 0
        assert "[1/4]" in v2_proc.stdout
        assert "Baseline" in v2_proc.stdout

        for idx, line in enumerate(report_text.splitlines()[:-1]):
            if line.startswith("#"):
                assert report_text.splitlines()[idx + 1] == "", (
                    f"MD022: Add a blank line after heading '{line}'"
                )

    def test_part_7b_requirements_txt_present_and_complete(self) -> None:
        """Verify `requirements.txt` exists and declares all harness and lint dependencies."""
        req_path = REPO_ROOT / "requirements.txt"
        assert req_path.exists(), "Missing requirements.txt in repository root"
        req_text = req_path.read_text(encoding="utf-8").lower()
        for pkg in ("fastmcp", "pydantic", "pytest", "pylint", "mypy", "ruff"):
            assert pkg in req_text, f"Missing '{pkg}' in requirements.txt"

    def test_part_7c_ci_workflow_and_semver_changelog(self) -> None:
        """Verify GitHub Actions CI installs requirements.txt & runs pytest, and SemVer 1.0.0."""
        ci_text = (REPO_ROOT / ".github" / "workflows" / "pylint.yml").read_text(
            encoding="utf-8"
        )
        assert "requirements.txt" in ci_text, "CI must install requirements.txt"
        assert "pytest" in ci_text, "CI must execute pytest"

        changelog_text = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "## [Unreleased]" in changelog_text
        assert "## [1.0.0]" in changelog_text, (
            "CHANGELOG.md must document Semantic Version [1.0.0] release"
        )


class TestPart8HarnessDeduplicationAndConsistency:
    """Verifies single-source config, skill-name consistency, and valid tool frontmatter."""

    def test_part_8a_single_source_branch_name_consistency(self) -> None:
        """Verify CLAUDE.md and mcp_server.py agree on the selected branch_name."""
        claude_md = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        mcp_text = (REPO_ROOT / "mcp_server.py").read_text(encoding="utf-8")
        assert "feature/fix_binomial_distribution" in claude_md
        assert get_issue_brief_resource()["branch_name"] == "feature/fix_binomial_distribution"
        assert "fix/issue-15656-binomial-overflow" not in mcp_text

    def test_part_8b_consistent_contributing_skill_name(self) -> None:
        """Verify CLAUDE.md and contributing-reviewer.md reference denizin42-contributing."""
        claude_md = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        reviewer_md = (
            REPO_ROOT / ".claude" / "agents" / "contributing-reviewer.md"
        ).read_text(encoding="utf-8")
        assert "thealgorithms-contributing" not in claude_md
        assert "thealgorithms-contributing" not in reviewer_md
        assert "denizin42-contributing" in claude_md
        assert "skills: denizin42-contributing" in reviewer_md

    def test_part_8c_valid_claude_frontmatter_tools(self) -> None:
        """Verify agents and skills use valid comma-separated Claude tool names."""
        files = [
            REPO_ROOT / ".claude" / "agents" / "contributing-reviewer.md",
            REPO_ROOT / ".claude" / "agents" / "issue-researcher.md",
            REPO_ROOT / ".claude" / "skills" / "denizin42-contributing" / "SKILL.md",
            REPO_ROOT / ".claude" / "skills" / "fork-pr-workflow" / "SKILL.md",
        ]
        for path in files:
            lines = path.read_text(encoding="utf-8").splitlines()
            tool_lines = [
                line
                for line in lines
                if line.startswith("tools:") or line.startswith("allowed-tools:")
            ]
            assert tool_lines, f"Missing tools/allowed-tools in {path.name}"
            for line in tool_lines:
                value = line.split(":", 1)[1].strip()
                assert "," in value, f"Use comma-separated tool names in {path.name}: {line}"
                for bad in ("python", "python3", "gh", "git"):
                    assert bad not in value.split(), (
                        f"Use 'Bash' instead of CLI binary '{bad}' in {path.name}: {line}"
                    )

    def test_part_8d_context_and_skills_stay_generic(self) -> None:
        """Verify context rules and contributing skill avoid hardcoding the target file."""
        for rel in (
            "context/contributing-rules.md",
            "context/fork-pr-workflow.md",
            ".claude/skills/denizin42-contributing/SKILL.md",
        ):
            text = (REPO_ROOT / rel).read_text(encoding="utf-8")
            assert "maths/binomial_distribution.py" not in text, (
                f"Keep target_file centralized in CLAUDE.md/mcp_server.py, not {rel}"
            )


class TestPart9MakefileCleanupAndTelemetry:
    """Verifies Makefile, fork cleanup script, README quickstart, and token/subagent telemetry."""

    def test_part_9a_makefile_targets(self) -> None:
        """Verify Makefile exists with install, test, lint, compliance, benchmark, cleanup-fork."""
        makefile = REPO_ROOT / "Makefile"
        assert makefile.exists(), "Missing Makefile in repository root"
        text = makefile.read_text(encoding="utf-8")
        for target in (
            "install:",
            "test:",
            "lint:",
            "compliance:",
            "demo-dry-run:",
            "benchmark:",
            "cleanup-fork:",
        ):
            assert target in text, f"Missing '{target}' in Makefile"

    def test_part_9b_cleanup_fork_script_safety(self) -> None:
        """Verify scripts/cleanup-fork.sh exists and blocks upstream TheAlgorithms/*."""
        script_path = REPO_ROOT / "scripts" / "cleanup-fork.sh"
        assert script_path.exists(), "Missing scripts/cleanup-fork.sh"
        blocked = subprocess.run(
            ["bash", str(script_path)],
            cwd=str(REPO_ROOT),
            env={
                "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
                "FORK_OWNER": "TheAlgorithms",
            },
            capture_output=True,
            text=True,
            check=False,
        )
        assert blocked.returncode != 0, "cleanup-fork.sh must refuse FORK_OWNER=TheAlgorithms"

    def test_part_9c_perf_tracker_tokens_subagents_and_changelog(self, tmp_path: Path) -> None:
        """Verify track_performance.py records tokens, subagents_used, and changelog_entry."""
        tracker = REPO_ROOT / "scripts" / "track_performance.py"
        db_file = tmp_path / "perf.db"
        report_file = tmp_path / "REPORT.md"
        fake_json_cmd = (
            "python3 -c 'import json; print(json.dumps({"
            "\"response\": \"Invoked issue-researcher and contributing-reviewer\", "
            "\"usage\": {\"input_tokens\": 1200, \"output_tokens\": 300, \"total_tokens\": 1500}"
            "}))'"
        )
        proc = subprocess.run(
            [
                sys.executable,
                str(tracker),
                "--version",
                "v_test",
                "--baseline",
                "--label",
                "Telemetry Test",
                "--change",
                "Added token and subagent tracking",
                "--agent-cmd",
                fake_json_cmd,
                "--db-file",
                str(db_file),
                "--report-file",
                str(report_file),
            ],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, f"track_performance.py failed: {proc.stderr or proc.stdout}"
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        row = dict(conn.execute("SELECT * FROM agent_runs WHERE version_tag='v_test'").fetchone())
        conn.close()
        assert row["total_tokens"] == 1500
        assert "issue-researcher" in row["subagents_used"]
        assert "contributing-reviewer" in row["subagents_used"]
        assert "Added token and subagent tracking" in row["changelog_entry"]
        report_text = report_file.read_text(encoding="utf-8")
        assert "1,500" in report_text or "1500" in report_text
        assert "issue-researcher" in report_text

    def test_part_9d_readme_professor_ta_quickstart(self) -> None:
        """Verify README.md documents Professor/TA quickstart and Makefile targets."""
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        assert "make test" in readme
        assert "make benchmark" in readme
        assert "make cleanup-fork" in readme
        assert "PERFORMANCE_REPORT.md" in readme

    def test_part_9e_fork_overhead_normalization(self, tmp_path: Path) -> None:
        """Verify --fork-overhead-sec is stored and added to normalized duration."""
        tracker = REPO_ROOT / "scripts" / "track_performance.py"
        db_file = tmp_path / "fork_perf.db"
        report_file = tmp_path / "FORK_REPORT.md"
        proc = subprocess.run(
            [
                sys.executable,
                str(tracker),
                "--version",
                "v_warm",
                "--baseline",
                "--label",
                "Warm Fork Run",
                "--agent-duration-sec",
                "10.0",
                "--fork-overhead-sec",
                "4.5",
                "--db-file",
                str(db_file),
                "--report-file",
                str(report_file),
            ],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, f"track_performance.py failed: {proc.stderr or proc.stdout}"
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        row = dict(conn.execute("SELECT * FROM agent_runs WHERE version_tag='v_warm'").fetchone())
        conn.close()
        assert row["fork_overhead_sec"] == 4.5
        report_text = report_file.read_text(encoding="utf-8")
        assert "14.500" in report_text

    def test_part_9f_rich_emoji_console_formatting(self) -> None:
        """Verify track_performance.py formats stream events with emojis and step detail."""
        tracker_text = (REPO_ROOT / "scripts" / "track_performance.py").read_text(
            encoding="utf-8"
        )
        for marker in ("🚀", "🧪", "📊", "📝", "🤖", "📖", "💻"):
            assert marker in tracker_text, f"Missing '{marker}' emoji in track_performance.py"


class TestPart10AgentAgnosticSupport:
    """Verifies Claude Code, Antigravity (agy), and generic CLI agent compatibility."""

    def test_part_10a_tracker_parses_claude_code_stream_json(self, tmp_path: Path) -> None:
        """Verify track_performance.py parses Claude Code stream-json events and tokens."""
        tracker = REPO_ROOT / "scripts" / "track_performance.py"
        db_file = tmp_path / "claude.db"
        report_file = tmp_path / "CLAUDE_REPORT.md"
        events = [
            json.dumps(
                {
                    "type": "assistant",
                    "message": {
                        "content": [
                            {
                                "type": "tool_use",
                                "name": "Task",
                                "input": {"subagent_type": "issue-researcher"},
                            },
                            {
                                "type": "tool_use",
                                "name": "Task",
                                "input": {"subagent_type": "contributing-reviewer"},
                            },
                        ]
                    },
                }
            ),
            json.dumps(
                {
                    "type": "result",
                    "subtype": "success",
                    "result": "Done",
                    "usage": {"input_tokens": 900, "output_tokens": 150},
                }
            ),
        ]
        cmd = "python3 -c 'import sys; print(\"\\n\".join(sys.argv[1:]))' " + " ".join(
            f"'{e}'" for e in events
        )
        proc = subprocess.run(
            [
                sys.executable,
                str(tracker),
                "--version",
                "v_claude",
                "--baseline",
                "--label",
                "Claude Code Run",
                "--agent-cmd",
                cmd,
                "--db-file",
                str(db_file),
                "--report-file",
                str(report_file),
            ],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, f"track_performance.py failed: {proc.stderr or proc.stdout}"
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        row = dict(conn.execute("SELECT * FROM agent_runs WHERE version_tag='v_claude'").fetchone())
        conn.close()
        assert row["total_tokens"] == 1050
        assert "issue-researcher" in row["subagents_used"]
        assert "contributing-reviewer" in row["subagents_used"]

    def test_part_10b_makefile_and_readme_agent_agnostic(self) -> None:
        """Verify Makefile and README support AGENT=claude, AGENT=agy, or custom AGENT_CMD."""
        makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        assert "AGENT ?=" in makefile
        assert "claude" in makefile and "agy" in makefile
        assert "AGENT=claude" in readme or "claude" in readme.lower()


class TestPart11McpFastAuditAndScopedSubagents:
    """Verifies bundled fast_audit.py, new MCP tools, and scoped sub-agent prompts."""

    def test_part_11a_fast_audit_skill_script(self) -> None:
        """Verify fast_audit.py runs compliance, doctest, and lint in one compact JSON call."""
        script_path = REPO_ROOT.joinpath(
            ".claude", "skills", "denizin42-contributing", "scripts", "fast_audit.py"
        )
        assert script_path.exists(), "Missing fast_audit.py in denizin42-contributing/scripts/"
        proc = subprocess.run(
            [sys.executable, str(script_path), "maths/binomial_distribution.py"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, f"fast_audit.py failed: {proc.stderr or proc.stdout}"
        data: Dict[str, Any] = json.loads(proc.stdout)
        assert data["compliant"] is True
        assert data["doctests_passed"] is True
        assert data["lint_ok"] is True

    def test_part_11b_mcp_get_issue_root_cause_context(self) -> None:
        """Verify MCP tool get_issue_root_cause_context returns compact AST & check info."""
        res = get_issue_root_cause_context("maths/binomial_distribution.py", 15656)
        assert res["target_file"] == "maths/binomial_distribution.py"
        assert res["issue_number"] == 15656
        assert res["overflow_171_resolved"] is True
        assert len(res["ast_functions"]) >= 1

    def test_part_11c_mcp_run_fast_compliance_audit(self) -> None:
        """Verify MCP tool run_fast_compliance_audit delegates to fast_audit.py."""
        res = run_fast_compliance_audit("maths/binomial_distribution.py")
        assert res["compliant"] is True
        assert res["doctests_passed"] is True

    def test_part_11d_subagents_scoped_to_local_repo(self) -> None:
        """Verify sub-agents stay in current repo and use fast MCP/skill tools."""
        researcher = (REPO_ROOT / ".claude" / "agents" / "issue-researcher.md").read_text(
            encoding="utf-8"
        )
        reviewer = (REPO_ROOT / ".claude" / "agents" / "contributing-reviewer.md").read_text(
            encoding="utf-8"
        )
        assert "get_issue_root_cause_context" in researcher
        assert "fast_audit.py" in reviewer or "run_fast_compliance_audit" in reviewer

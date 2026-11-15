"""CS 440 Lab 6 telemetry, solution-proof, benchmark-reset, and fast-path tests."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from mcp_server import get_phase2_fastpath_bundle
from scripts.report_evidence import _detect_subagent_role, reset_target_to_buggy

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestPart12PerfReportProofAndSubagentBreakdown:
    """Verifies PERFORMANCE_REPORT.md includes sub-agent breakdown, code snippet, and test proof."""

    def test_part_12a_report_includes_subagent_breakdown_and_proof(self, tmp_path: Path) -> None:
        """Verify track_performance.py renders subagent table, fix snippet, and doctest proof."""
        tracker = REPO_ROOT / "scripts" / "track_performance.py"
        db_file = tmp_path / "proof.db"
        report_file = tmp_path / "PROOF_REPORT.md"
        cmd = [
            sys.executable,
            str(tracker),
            "--version=v_proof",
            "--baseline",
            "--label=Proof Run",
            "--agent-duration-sec=12.0",
            f"--db-file={db_file}",
            f"--report-file={report_file}",
        ]
        proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        report = report_file.read_text(encoding="utf-8")
        assert "Main Agent vs. Sub-Agent Breakdown" in report
        assert "Phase 2 Deliverables, Issue `#15656` Fix & Passing Test Evidence" in report
        assert "def binomial_distribution(" in report
        assert "passed and 0 failed" in report
        assert "fast_audit.py" in report or '"compliant": true' in report

    def test_part_12b_subagent_role_detection_and_mcp_prompt(self) -> None:
        """Verify researcher vs reviewer role detection and MCP tool usage in Makefile PROMPT."""
        researcher_lines = [
            json.dumps({"content": "Analyze Issue #15656 in maths/binomial_distribution.py"}),
            json.dumps({"content": "Note: check CONTRIBUTING compliance_checker.py too"}),
        ]
        reviewer_lines = [
            json.dumps({"content": "Audit maths/binomial_distribution.py against CONTRIBUTING.md"}),
            json.dumps({"content": "Running fast_audit.py"}),
        ]
        assert _detect_subagent_role(researcher_lines) == "issue-researcher"
        assert _detect_subagent_role(reviewer_lines) == "contributing-reviewer"

        makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
        assert "get_phase2_fastpath_bundle" in makefile or (
            "get_issue_root_cause_context" in makefile
            and "verify_contribution_target" in makefile
        )


class TestPart13BenchmarkResetsProblem:  # pylint: disable=too-few-public-methods
    """Verifies benchmark runs reset maths/binomial_distribution.py to Issue #15656 state."""

    def test_part_13a_reset_target_restores_buggy_issue_15656(self, tmp_path: Path) -> None:
        """Verify reset_target_to_buggy writes the factorial(trials) OverflowError baseline."""
        target = tmp_path / "binomial_distribution.py"
        reset_target_to_buggy(target)
        text = target.read_text(encoding="utf-8")
        assert "float(factorial(trials))" in text
        proc = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys; sys.path.insert(0, str(sys.argv[1])); "
                "from binomial_distribution import binomial_distribution; "
                "binomial_distribution(100, 171, 0.5)",
                str(tmp_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode != 0
        assert "OverflowError" in proc.stderr


class TestPart14FastpathBundleAndSinglePassReview:
    """Verifies Phase 2 fast-path context, bundled MCP tool, and single-pass sub-agent flow."""

    def test_part_14a_phase2_fastpath_context_and_symlink(self) -> None:
        """Verify context/phase2-fastpath.md exists, is symlinked, and imported in CLAUDE.md."""
        ctx = REPO_ROOT / "context" / "phase2-fastpath.md"
        link = REPO_ROOT / ".claude" / "context" / "phase2-fastpath.md"
        assert ctx.exists(), "Missing context/phase2-fastpath.md"
        assert link.is_symlink(), ".claude/context/phase2-fastpath.md must be a symlink"
        text = ctx.read_text(encoding="utf-8")
        assert "math.comb" in text and "lgamma" in text
        claude_md = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        assert "@./context/phase2-fastpath.md" in claude_md

    def test_part_14b_mcp_get_phase2_fastpath_bundle(self) -> None:
        """Verify get_phase2_fastpath_bundle returns target, issue context, and repo status."""
        bundle = get_phase2_fastpath_bundle()
        assert bundle["target_validation"]["allowed"] is True
        assert bundle["issue_context"]["issue_number"] == 15656
        assert "src_ready" in bundle

    def test_part_14c_subagents_single_pass_and_flash_lite(self) -> None:
        """Verify sub-agents specify single-call compact output and Makefile uses single-pass."""
        researcher = (REPO_ROOT / ".claude" / "agents" / "issue-researcher.md").read_text(
            encoding="utf-8"
        )
        reviewer = (REPO_ROOT / ".claude" / "agents" / "contributing-reviewer.md").read_text(
            encoding="utf-8"
        )
        makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
        assert "60 words" in researcher or "one" in researcher.lower()
        assert "40 words" in reviewer or "single" in reviewer.lower()
        assert "get_phase2_fastpath_bundle" in makefile
        assert "flash_lite" in makefile or "haiku" in makefile

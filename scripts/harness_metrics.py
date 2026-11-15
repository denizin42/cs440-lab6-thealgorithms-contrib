"""Harness feature, context-efficiency, and algorithm benchmark measurements."""

from __future__ import annotations

import doctest
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent


def _estimate_tokens(text: str) -> int:
    """Return standard 4-chars-per-token estimate for English/Markdown text."""
    return max(1, len(text) // 4)


def measure_context_efficiency() -> Dict[str, Any]:
    """Measure Strategy 2 (Select) and Strategy 3 (Compress) token savings."""
    raw_contrib = (REPO_ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    curated_contrib = (REPO_ROOT / "context" / "contributing-rules.md").read_text(
        encoding="utf-8"
    )
    raw_tokens = _estimate_tokens(raw_contrib)
    curated_tokens = _estimate_tokens(curated_contrib)
    compression_pct = round((1.0 - (curated_tokens / max(1, raw_tokens))) * 100.0, 1)

    skill_files = list((REPO_ROOT / ".claude" / "skills").glob("*/SKILL.md"))
    full_skill_tokens = 0
    frontmatter_tokens = 0
    for skill_path in skill_files:
        text = skill_path.read_text(encoding="utf-8")
        full_skill_tokens += _estimate_tokens(text)
        parts = text.split("---", 2)
        frontmatter_tokens += _estimate_tokens(parts[1] if len(parts) >= 3 else text)

    progressive_savings_pct = round(
        (1.0 - (frontmatter_tokens / max(1, full_skill_tokens))) * 100.0, 1
    )
    return {
        "raw_contributing_tokens": raw_tokens,
        "curated_context_tokens": curated_tokens,
        "compression_ratio_pct": compression_pct,
        "full_skill_tokens": full_skill_tokens,
        "skill_frontmatter_tokens": frontmatter_tokens,
        "progressive_skill_savings_pct": progressive_savings_pct,
    }


def _map_class_to_bucket(cls_name: str) -> str:
    """Map a pytest class name to its feature bucket key."""
    mapping = {
        "TestPart1IssueTargetInMarkdown": "Part1_Target",
        "TestPart2HooksAndMemory": "Part2_Hooks_Memory",
        "TestPart3Skills": "Part3_Skills",
        "TestPart4SubAgents": "Part4_SubAgents",
        "TestPart5MCP": "Part5_MCP",
        "TestPart6UpstreamGuardAndPRBuilder": "Part6_Safety_PR",
    }
    return mapping.get(cls_name, "Part1_Target")


def measure_harness_features() -> Dict[str, Any]:
    """Run non-Part-7 pytest checks and measure evaluation wall-clock time."""
    start_ns = time.perf_counter_ns()
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_lab6_progress.py",
            "-k",
            (
                "not TestPart7PerformanceTracker and "
                "not TestPart9MakefileCleanupAndTelemetry and "
                "not TestPart10AgentAgnosticSupport and "
                "not TestPart11McpFastAuditAndScopedSubagents"
            ),
            "-v",
            "--tb=no",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    harness_eval_ms = round((time.perf_counter_ns() - start_ns) / 1_000_000.0, 2)

    passed = 0
    total = 0
    feature_counts: Dict[str, List[int]] = {
        "Part1_Target": [0, 0],
        "Part2_Hooks_Memory": [0, 0],
        "Part3_Skills": [0, 0],
        "Part4_SubAgents": [0, 0],
        "Part5_MCP": [0, 0],
        "Part6_Safety_PR": [0, 0],
    }
    pattern = re.compile(r"test_lab6_progress\.py::(\w+)::(\w+)\s+(PASSED|FAILED)")
    for line in proc.stdout.splitlines():
        match = pattern.search(line)
        if not match:
            continue
        cls_name, _, status = match.groups()
        total += 1
        is_pass = 1 if status == "PASSED" else 0
        passed += is_pass
        bucket = _map_class_to_bucket(cls_name)
        feature_counts[bucket][0] += is_pass
        feature_counts[bucket][1] += 1

    return {
        "passed_tests": passed,
        "total_tests": total,
        "harness_score_pct": round((passed / max(1, total)) * 100.0, 1),
        "harness_eval_ms": harness_eval_ms,
        "feature_breakdown": {k: f"{v[0]}/{v[1]}" for k, v in feature_counts.items()},
    }


def measure_algorithm_benchmark() -> Dict[str, Any]:
    """Benchmark `maths/binomial_distribution.py` for compliance, doctests, and #15656."""
    target_rel = "maths/binomial_distribution.py"
    target_path = REPO_ROOT / target_rel
    checker_path = REPO_ROOT.joinpath(
        ".claude", "skills", "denizin42-contributing", "scripts", "check_compliance.py"
    )
    ast_compliant = False
    if checker_path.exists():
        proc = subprocess.run(
            [sys.executable, str(checker_path), target_rel],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            ast_compliant = bool(json.loads(proc.stdout).get("compliant", False))

    start_ns = time.perf_counter_ns()
    spec = importlib.util.spec_from_file_location("binomial_distribution", target_path)
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    failures, attempted = doctest.testmod(module, verbose=False)
    exec_ms = round((time.perf_counter_ns() - start_ns) / 1_000_000.0, 2)

    overflow_resolved = False
    try:
        result = module.binomial_distribution(85, 171, 0.5)
        overflow_resolved = isinstance(result, float) and 0.0 < result < 1.0
    except (OverflowError, ValueError):
        overflow_resolved = False

    return {
        "target_file": target_rel,
        "ast_compliant": ast_compliant,
        "doctests_passed": failures == 0 and attempted > 0,
        "doctests_attempted": attempted,
        "overflow_171_resolved": overflow_resolved,
        "exec_ms": exec_ms,
    }


def latest_changelog_entry() -> str:
    """Return the most recent bullet under `## [Unreleased]` in `CHANGELOG.md`."""
    changelog_path = REPO_ROOT / "CHANGELOG.md"
    if not changelog_path.exists():
        return ""
    in_unreleased = False
    for line in changelog_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## [Unreleased]"):
            in_unreleased = True
            continue
        if in_unreleased and line.startswith("## ["):
            break
        if in_unreleased and line.lstrip().startswith("- "):
            return line.lstrip()[2:].strip()
    return ""

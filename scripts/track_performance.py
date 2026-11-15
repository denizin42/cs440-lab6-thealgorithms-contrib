"""CS 440 Lab 6 — SQLite-Backed Agent & Context Harness Performance Tracker.

Measures how tuning prompts, hooks, skills, sub-agents, and MCP scripts
affects:
  1. Agent Wall-Clock Run Time (`agent_duration_sec`) via `--agent-cmd` or
     `--agent-duration-sec`
  2. Harness Verification Speed (`harness_eval_ms`) & Readiness Score (`%`)
  3. Context Token Efficiency (Strategy 3 Compression % & Strategy 2 Skill
     Progressive Disclosure Savings %)
  4. Target Algorithm Quality & Issue #15656 Benchmark (`exec_ms`)

Persists every run in SQLite (`logs/harness_performance.db`) with `v1`
flagged as the baseline, and generates `PERFORMANCE_REPORT.md` with Mermaid
`xychart-beta` trending graphs.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import doctest
import importlib.util
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_FILE = REPO_ROOT / "logs" / "harness_performance.db"
DEFAULT_REPORT_FILE = REPO_ROOT / "PERFORMANCE_REPORT.md"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS agent_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_tag TEXT NOT NULL,
    is_baseline INTEGER NOT NULL DEFAULT 0,
    label TEXT NOT NULL,
    timestamp_utc TEXT NOT NULL,
    agent_command TEXT NOT NULL DEFAULT '',
    agent_exit_code INTEGER NOT NULL DEFAULT 0,
    agent_duration_sec REAL NOT NULL,
    harness_eval_ms REAL NOT NULL,
    passed_tests INTEGER NOT NULL,
    total_tests INTEGER NOT NULL,
    harness_score_pct REAL NOT NULL,
    compression_ratio_pct REAL NOT NULL,
    progressive_skill_savings_pct REAL NOT NULL,
    raw_contributing_tokens INTEGER NOT NULL,
    curated_context_tokens INTEGER NOT NULL,
    ast_compliant INTEGER NOT NULL,
    doctests_attempted INTEGER NOT NULL,
    overflow_171_resolved INTEGER NOT NULL,
    algo_exec_ms REAL NOT NULL,
    feature_breakdown_json TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT ''
);
"""


def _estimate_tokens(text: str) -> int:
    """Return standard 4-chars-per-token estimate for English/Markdown text."""
    return max(1, len(text) // 4)


def init_db(db_path: Path) -> sqlite3.Connection:
    """Initialize SQLite database and return an open connection."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA_SQL)
    conn.commit()
    return conn


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
        if len(parts) >= 3:
            frontmatter_tokens += _estimate_tokens(parts[1])
        else:
            frontmatter_tokens += _estimate_tokens(text)

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
            "not TestPart7PerformanceTracker",
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

    score_pct = round((passed / max(1, total)) * 100.0, 1)
    breakdown = {key: f"{vals[0]}/{vals[1]}" for key, vals in feature_counts.items()}
    return {
        "passed_tests": passed,
        "total_tests": total,
        "harness_score_pct": score_pct,
        "harness_eval_ms": harness_eval_ms,
        "feature_breakdown": breakdown,
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


def run_timed_agent_command(agent_cmd: str) -> tuple[float, int]:
    """Execute and time an agent command in seconds, returning (duration_sec, exit_code)."""
    start_ns = time.perf_counter_ns()
    proc = subprocess.run(agent_cmd, shell=True, cwd=str(REPO_ROOT), check=False)
    duration_sec = round((time.perf_counter_ns() - start_ns) / 1_000_000_000.0, 4)
    return duration_sec, proc.returncode


def record_run(
    conn: sqlite3.Connection,
    snapshot: Dict[str, Any],
) -> None:
    """Insert a performance snapshot row into SQLite `agent_runs`."""
    if snapshot["is_baseline"]:
        conn.execute("UPDATE agent_runs SET is_baseline = 0")

    ctx = snapshot["context_efficiency"]
    algo = snapshot["algorithm_benchmark"]
    conn.execute(
        """
        INSERT INTO agent_runs (
            version_tag, is_baseline, label, timestamp_utc, agent_command,
            agent_exit_code, agent_duration_sec, harness_eval_ms, passed_tests,
            total_tests, harness_score_pct, compression_ratio_pct,
            progressive_skill_savings_pct, raw_contributing_tokens,
            curated_context_tokens, ast_compliant, doctests_attempted,
            overflow_171_resolved, algo_exec_ms, feature_breakdown_json, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            snapshot["version_tag"],
            1 if snapshot["is_baseline"] else 0,
            snapshot["label"],
            snapshot["timestamp"],
            snapshot["agent_command"],
            snapshot["agent_exit_code"],
            snapshot["agent_duration_sec"],
            snapshot["harness_eval_ms"],
            snapshot["passed_tests"],
            snapshot["total_tests"],
            snapshot["harness_score_pct"],
            ctx["compression_ratio_pct"],
            ctx["progressive_skill_savings_pct"],
            ctx["raw_contributing_tokens"],
            ctx["curated_context_tokens"],
            1 if algo["ast_compliant"] else 0,
            algo["doctests_attempted"],
            1 if algo["overflow_171_resolved"] else 0,
            algo["exec_ms"],
            json.dumps(snapshot["feature_breakdown"]),
            snapshot["notes"],
        ),
    )
    conn.commit()


def fetch_runs(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Fetch all recorded runs from SQLite ordered chronologically."""
    rows = conn.execute("SELECT * FROM agent_runs ORDER BY id ASC").fetchall()
    return [dict(row) for row in rows]


def _format_delta(current: float, baseline: float, unit: str) -> str:
    """Format delta and percent change relative to baseline."""
    diff = round(current - baseline, 4)
    sign = "+" if diff > 0 else ""
    if baseline > 0:
        pct = round(((current - baseline) / baseline) * 100.0, 1)
        pct_sign = "+" if pct > 0 else ""
        return f"{sign}{diff} {unit} ({pct_sign}{pct}%)"
    return f"{sign}{diff} {unit}"


def _build_chart_series(runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute x/y series strings and axis bounds for Mermaid xychart-beta graphs."""
    recent = runs[-10:]
    max_sec = max([r["agent_duration_sec"] for r in recent] + [1.0])
    max_ms = max([r["harness_eval_ms"] for r in recent] + [100.0])
    return {
        "x_versions": ", ".join(f'"{r["version_tag"]}"' for r in recent),
        "y_agent_secs": ", ".join(str(round(r["agent_duration_sec"], 3)) for r in recent),
        "y_eval_ms": ", ".join(str(round(r["harness_eval_ms"], 1)) for r in recent),
        "y_scores": ", ".join(str(round(r["harness_score_pct"], 1)) for r in recent),
        "y_sec_max": round(max_sec * 1.25, 2),
        "y_ms_max": round(max_ms * 1.25, 0),
    }


def render_markdown_report(runs: List[Dict[str, Any]], db_path: Path) -> str:
    """Render `PERFORMANCE_REPORT.md` with baseline comparisons and Mermaid charts."""
    latest = runs[-1]
    baseline = next((r for r in runs if r["is_baseline"] == 1), runs[0])
    chart = _build_chart_series(runs)

    history_rows = []
    for r in runs:
        tag = f"`{r['version_tag']}`" + (" **(Baseline)**" if r["is_baseline"] else "")
        delta_s = _format_delta(r["agent_duration_sec"], baseline["agent_duration_sec"], "s")
        issue_status = "RESOLVED" if r["overflow_171_resolved"] else "Phase 2 Pending"
        history_rows.append(
            f"| {r['id']} | {tag} | {r['label']} | `{r['agent_duration_sec']:.3f}s` | "
            f"`{delta_s}` | `{r['harness_eval_ms']:.1f} ms` | "
            f"**{r['harness_score_pct']}%** ({r['passed_tests']}/{r['total_tests']}) | "
            f"{r['compression_ratio_pct']}% | {issue_status} |"
        )
    history_table = "\n".join(history_rows)

    return f"""# CS 440 Lab 6 — Agent & Harness Performance Report

SQLite Database: `{db_path.name}` | Total Runs Recorded: **{len(runs)}** | Baseline Version: **`{baseline["version_tag"]}`** ({baseline["label"]})

---

## 1. Baseline (`{baseline["version_tag"]}`) vs. Latest (`{latest["version_tag"]}`) Comparison

| Metric | Baseline (`{baseline["version_tag"]}`) | Latest (`{latest["version_tag"]}`) | Delta vs. Baseline |
| :--- | :---: | :---: | :---: |
| **Agent Run Duration** | `{baseline["agent_duration_sec"]:.3f} s` | `{latest["agent_duration_sec"]:.3f} s` | `{_format_delta(latest["agent_duration_sec"], baseline["agent_duration_sec"], "s")}` |
| **Harness Test Eval Speed** | `{baseline["harness_eval_ms"]:.1f} ms` | `{latest["harness_eval_ms"]:.1f} ms` | `{_format_delta(latest["harness_eval_ms"], baseline["harness_eval_ms"], "ms")}` |
| **Harness Readiness Score** | `{baseline["harness_score_pct"]}%` | `{latest["harness_score_pct"]}%` | `{_format_delta(latest["harness_score_pct"], baseline["harness_score_pct"], "%")}` |
| **Context Compression (Strategy 3)** | `{baseline["compression_ratio_pct"]}%` | `{latest["compression_ratio_pct"]}%` | `{latest["curated_context_tokens"]} / {latest["raw_contributing_tokens"]} tokens` |
| **Skill Startup Savings (Strategy 2)** | `{baseline["progressive_skill_savings_pct"]}%` | `{latest["progressive_skill_savings_pct"]}%` | Frontmatter-only load |
| **Issue #15656 (`n=171`) Benchmark** | `{"RESOLVED" if baseline["overflow_171_resolved"] else "UNRESOLVED"}` | `{"RESOLVED" if latest["overflow_171_resolved"] else "UNRESOLVED"}` | `{latest["algo_exec_ms"]} ms` (`{latest["doctests_attempted"]}` doctests) |

---

## 2. Agent Run Duration Trend (Seconds — Lower is Faster)

```mermaid
xychart-beta
    title "Agent Run Duration (s) Across Harness Versions"
    x-axis [{chart["x_versions"]}]
    y-axis "Agent Run Duration (s)" 0 --> {chart["y_sec_max"]}
    bar [{chart["y_agent_secs"]}]
    line [{chart["y_agent_secs"]}]
```

---

## 3. Harness Test Evaluation Speed (ms) & Readiness (%)

```mermaid
xychart-beta
    title "Harness Eval Time (ms) Across Versions"
    x-axis [{chart["x_versions"]}]
    y-axis "Eval Time (ms)" 0 --> {chart["y_ms_max"]}
    bar [{chart["y_eval_ms"]}]
    line [{chart["y_eval_ms"]}]
```

```mermaid
xychart-beta
    title "Harness Readiness Score (%) Across Versions"
    x-axis [{chart["x_versions"]}]
    y-axis "Readiness (%)" 0 --> 100
    line [{chart["y_scores"]}]
```

---

## 4. SQLite Run History (`agent_runs` Table)

| Run | Version | Tuning Milestone | Agent Time | Delta vs. `{baseline["version_tag"]}` | Harness Eval | Readiness | Token Compression | Issue #15656 |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
{history_table}
"""


def _build_snapshot(
    args: argparse.Namespace,
    conn: sqlite3.Connection,
    agent_duration_sec: float,
    agent_exit_code: int,
) -> Dict[str, Any]:
    """Assemble a complete performance snapshot dictionary."""
    existing = fetch_runs(conn)
    version_tag = args.version or f"v{len(existing) + 1}"
    is_baseline = bool(args.baseline or len(existing) == 0)

    harness = measure_harness_features()
    ctx = measure_context_efficiency()
    algo = measure_algorithm_benchmark()

    baseline_row: Optional[Dict[str, Any]] = next(
        (r for r in existing if r["is_baseline"] == 1),
        existing[0] if existing else None,
    )
    baseline_sec = (
        agent_duration_sec
        if is_baseline or baseline_row is None
        else float(baseline_row["agent_duration_sec"])
    )

    return {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "version_tag": version_tag,
        "is_baseline": is_baseline,
        "label": args.label,
        "agent_command": args.agent_cmd or "",
        "agent_exit_code": agent_exit_code,
        "agent_duration_sec": round(agent_duration_sec, 4),
        "delta_vs_baseline_sec": round(agent_duration_sec - baseline_sec, 4),
        "harness_eval_ms": harness["harness_eval_ms"],
        "passed_tests": harness["passed_tests"],
        "total_tests": harness["total_tests"],
        "harness_score_pct": harness["harness_score_pct"],
        "feature_breakdown": harness["feature_breakdown"],
        "context_efficiency": ctx,
        "algorithm_benchmark": algo,
        "notes": args.notes,
    }


def main() -> int:
    """CLI entrypoint for recording and reporting SQLite harness & agent metrics."""
    parser = argparse.ArgumentParser(
        description="SQLite-backed Lab 6 agent & harness performance tracker."
    )
    parser.add_argument("--version", default="", help="Version tag (e.g., v1, v2)")
    parser.add_argument(
        "--baseline",
        action="store_true",
        help="Mark this run as the baseline version in SQLite",
    )
    parser.add_argument(
        "--label",
        default="Harness Tuning Snapshot",
        help="Milestone description for this run",
    )
    parser.add_argument(
        "--agent-cmd",
        default="",
        help="Optional shell command to execute and time (e.g. 'agy ...' or 'pytest -q')",
    )
    parser.add_argument(
        "--agent-duration-sec",
        type=float,
        default=None,
        help="Manual agent run duration in seconds (when not using --agent-cmd)",
    )
    parser.add_argument("--notes", default="", help="Optional tuning notes")
    parser.add_argument("--db-file", default=str(DEFAULT_DB_FILE), help="SQLite DB path")
    parser.add_argument(
        "--report-file", default=str(DEFAULT_REPORT_FILE), help="Markdown report path"
    )
    parser.add_argument("--json", action="store_true", help="Print JSON snapshot to stdout")
    args = parser.parse_args()

    if args.agent_cmd:
        duration_sec, exit_code = run_timed_agent_command(args.agent_cmd)
    elif args.agent_duration_sec is not None:
        duration_sec, exit_code = float(args.agent_duration_sec), 0
    else:
        t0 = time.perf_counter_ns()
        measure_harness_features()
        duration_sec = round((time.perf_counter_ns() - t0) / 1_000_000_000.0, 4)
        exit_code = 0

    db_path = Path(args.db_file)
    report_path = Path(args.report_file)
    with init_db(db_path) as conn:
        snapshot = _build_snapshot(args, conn, duration_sec, exit_code)
        record_run(conn, snapshot)
        runs = fetch_runs(conn)

    report_path.write_text(render_markdown_report(runs, db_path), encoding="utf-8")

    if args.json:
        print(json.dumps(snapshot, indent=2))
    else:
        print(
            f"[SQLite Perf Recorded] {snapshot['version_tag']} ({snapshot['label']}): "
            f"Agent={snapshot['agent_duration_sec']:.3f}s "
            f"(Delta={snapshot['delta_vs_baseline_sec']:+.3f}s), "
            f"Harness={snapshot['harness_score_pct']}% in {snapshot['harness_eval_ms']}ms, "
            f"DB={db_path}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())

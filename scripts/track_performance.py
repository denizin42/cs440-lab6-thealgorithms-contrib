"""CS 440 Lab 6 — SQLite-Backed Agent & Context Harness Performance Tracker.

Measures how tuning prompts, hooks, skills, sub-agents, and MCP scripts
affects:
  1. Agent Wall-Clock Run Time (`agent_duration_sec`) via `--agent-cmd` or
     `--agent-duration-sec`
  2. Harness Verification Speed (`harness_eval_ms`) & Readiness Score (`%`)
  3. Context Token Efficiency (Strategy 3 Compression % & Strategy 2 Skill
     Progressive Disclosure Savings %)
  4. Target Algorithm Quality & Issue #15656 Benchmark (`exec_ms`)
  5. Live Emoji Step Streaming (🚀 🧪 📊 📝 🤖 📖 💻)

Persists every run in SQLite (`logs/harness_performance.db`) with `v1`
flagged as the baseline, and generates `PERFORMANCE_REPORT.md` with Mermaid
`xychart-beta` trending graphs.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys
import time
from typing import Any, Dict, Optional

try:
    from scripts import harness_metrics, report_evidence, report_renderer, stream_telemetry
except ImportError:
    import harness_metrics  # type: ignore[import-not-found,no-redef]
    import report_evidence  # type: ignore[import-not-found,no-redef]
    import report_renderer  # type: ignore[import-not-found,no-redef]
    import stream_telemetry  # type: ignore[import-not-found,no-redef]

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_FILE = REPO_ROOT / "logs" / "harness_performance.db"
DEFAULT_REPORT_FILE = REPO_ROOT / "PERFORMANCE_REPORT.md"

init_db = report_renderer.init_db
record_run = report_renderer.record_run
fetch_runs = report_renderer.fetch_runs
render_markdown_report = report_renderer.render_markdown_report
measure_context_efficiency = harness_metrics.measure_context_efficiency
measure_harness_features = harness_metrics.measure_harness_features
measure_algorithm_benchmark = harness_metrics.measure_algorithm_benchmark
run_timed_agent_command = stream_telemetry.run_timed_agent_command


def _build_snapshot(
    args: argparse.Namespace,
    conn: sqlite3.Connection,
    telemetry: Dict[str, Any],
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
    agent_duration_sec = float(telemetry["duration_sec"])
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
        "agent_exit_code": int(telemetry["exit_code"]),
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
        "input_tokens": int(telemetry.get("input_tokens", 0)),
        "output_tokens": int(telemetry.get("output_tokens", 0)),
        "total_tokens": int(telemetry.get("total_tokens", 0)),
        "subagents_used": str(telemetry.get("subagents_used", "unknown")),
        "changelog_entry": (
            args.change or harness_metrics.latest_changelog_entry() or args.label
        ),
        "fork_overhead_sec": round(float(args.fork_overhead_sec), 4),
        "subagent_breakdown": telemetry.get("subagent_breakdown", {}),
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
    parser.add_argument("--change", default="", help="Changelog / change description for this run")
    parser.add_argument(
        "--fork-overhead-sec",
        type=float,
        default=0.0,
        help="Initial fork time (s) added to normalize runs that skipped cold-forking",
    )
    parser.add_argument("--notes", default="", help="Optional tuning notes")
    parser.add_argument("--db-file", default=str(DEFAULT_DB_FILE), help="SQLite DB path")
    parser.add_argument(
        "--report-file", default=str(DEFAULT_REPORT_FILE), help="Markdown report path"
    )
    parser.add_argument(
        "--no-reset-target",
        action="store_true",
        help="Skip resetting maths/binomial_distribution.py to buggy state before --agent-cmd",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON snapshot to stdout")
    args = parser.parse_args()

    def _log(msg: str) -> None:
        if not args.json:
            print(msg, flush=True)

    _log(f"\n🚀 [1/4] Starting '{args.label}' (version={args.version or 'auto'})...")
    telemetry = stream_telemetry.default_telemetry("unknown")
    if args.agent_cmd:
        if not args.no_reset_target:
            report_evidence.reset_target_to_buggy()
            _log(
                "      🔄 Reset maths/binomial_distribution.py to buggy Issue #15656 baseline "
                "(OverflowError at trials >= 171)."
            )
        _log("      🤖 Running agent & streaming live main + sub-agent steps:")
        telemetry = run_timed_agent_command(args.agent_cmd)
        _log(
            f"      ✅ Agent finished in {telemetry['duration_sec']:.3f}s "
            f"(exit={telemetry['exit_code']}, tokens={telemetry['total_tokens']:,}, "
            f"subagents={telemetry['subagents_used']})."
        )
    elif args.agent_duration_sec is not None:
        telemetry["duration_sec"] = float(args.agent_duration_sec)
        _log(f"      ⏱️  Using recorded agent duration: {telemetry['duration_sec']:.3f}s.")
    else:
        t0 = time.perf_counter_ns()
        measure_harness_features()
        telemetry["duration_sec"] = round((time.perf_counter_ns() - t0) / 1_000_000_000.0, 4)

    _log("\n🧪 [2/4] Measuring harness checks & context efficiency...")
    db_path = Path(args.db_file)
    report_path = Path(args.report_file)
    with init_db(db_path) as conn:
        _log("📊 [3/4] Benchmarking target algorithm & saving run to SQLite...")
        snapshot = _build_snapshot(args, conn, telemetry)
        record_run(conn, snapshot)
        runs = fetch_runs(conn)

    _log(f"📝 [4/4] Rendering {report_path.name}...")
    report_md = render_markdown_report(runs, db_path)
    report_path.write_text(report_md, encoding="utf-8")

    if args.json:
        print(json.dumps(snapshot, indent=2))
    else:
        print(
            f"\n[SQLite Perf Recorded] {snapshot['version_tag']} ({snapshot['label']}): "
            f"Agent={snapshot['agent_duration_sec']:.3f}s "
            f"(Delta={snapshot['delta_vs_baseline_sec']:+.3f}s), "
            f"Harness={snapshot['harness_score_pct']}% in {snapshot['harness_eval_ms']}ms, "
            f"DB={db_path}\n",
            flush=True,
        )
        print(report_md, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

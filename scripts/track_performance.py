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
    notes TEXT NOT NULL DEFAULT '',
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    subagents_used TEXT NOT NULL DEFAULT 'unknown',
    changelog_entry TEXT NOT NULL DEFAULT ''
);
"""

MIGRATION_COLUMNS = (
    ("input_tokens", "INTEGER NOT NULL DEFAULT 0"),
    ("output_tokens", "INTEGER NOT NULL DEFAULT 0"),
    ("total_tokens", "INTEGER NOT NULL DEFAULT 0"),
    ("subagents_used", "TEXT NOT NULL DEFAULT 'unknown'"),
    ("changelog_entry", "TEXT NOT NULL DEFAULT ''"),
)


def _estimate_tokens(text: str) -> int:
    """Return standard 4-chars-per-token estimate for English/Markdown text."""
    return max(1, len(text) // 4)


def init_db(db_path: Path) -> sqlite3.Connection:
    """Initialize SQLite database, run schema migrations, and return connection."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA_SQL)
    existing_cols = {
        row["name"] for row in conn.execute("PRAGMA table_info(agent_runs)").fetchall()
    }
    for col_name, col_def in MIGRATION_COLUMNS:
        if col_name not in existing_cols:
            conn.execute(f"ALTER TABLE agent_runs ADD COLUMN {col_name} {col_def}")
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
            "not TestPart7PerformanceTracker and not TestPart9MakefileCleanupAndTelemetry",
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


def _latest_changelog_entry() -> str:
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


def _detect_subagents(response_text: str, conversation_id: str) -> str:
    """Detect whether `issue-researcher` and `contributing-reviewer` were invoked."""
    corpus = response_text
    if conversation_id:
        for base in (
            Path.home() / ".gemini-personal" / ".gemini" / "antigravity-cli" / "brain",
            Path.home() / ".gemini" / "antigravity-cli" / "brain",
        ):
            transcript = base / conversation_id / ".system_generated" / "logs" / "transcript.jsonl"
            if transcript.exists():
                corpus += "\n" + transcript.read_text(encoding="utf-8", errors="ignore")
                break
    found = [
        name
        for name in ("issue-researcher", "contributing-reviewer")
        if name in corpus
    ]
    return ", ".join(found) if found else "none detected"


def _summarize_tool_params(params: Dict[str, Any]) -> str:
    """Return a concise one-line summary of tool/subagent parameters."""
    for key in ("CommandLine", "Path", "TypeName", "Role", "ToolName", "Query", "Pattern"):
        if params.get(key):
            val = str(params[key]).replace("\n", " ").strip()
            return val[:90] + ("..." if len(val) > 90 else "")
    return ""


def _format_step_update(upd: Dict[str, Any], elapsed: float) -> Optional[str]:
    """Format a stream-json `step_update` into a detailed live console line."""
    state = upd.get("state", "")
    stype = upd.get("step_type", "step")
    idx = upd.get("step_index", "?")
    if stype == "user_input":
        return None
    info = upd.get("tool_info") or {}
    tname = upd.get("tool_name") or info.get("name") or stype
    if state == "ACTIVE" and stype in ("tool", "subagent"):
        detail = _summarize_tool_params(info.get("parameters") or {})
        suffix = f": {detail}" if detail else ""
        return f"      [+{elapsed:5.1f}s] [agy] -> #{idx} {tname}{suffix}"
    if state in ("DONE", "ERROR"):
        dur = upd.get("duration_seconds")
        dur_str = f" ({dur:.2f}s)" if isinstance(dur, (int, float)) else ""
        err = (info.get("error") or {}).get("message", "")
        err_str = f" ERROR: {err[:70]}" if err else ""
        if stype == "agent_response":
            tok = (upd.get("usage") or {}).get("total_tokens", 0)
            tok_str = f" [tokens={tok:,}]" if tok else ""
            return f"      [+{elapsed:5.1f}s] [agy] <- #{idx} response {state}{dur_str}{tok_str}"
        return f"      [+{elapsed:5.1f}s] [agy] <- #{idx} {tname} {state}{dur_str}{err_str}"
    return None


def _process_stream_line(
    raw_line: str,
    start_ns: int,
    telemetry: Dict[str, Any],
    chunks: List[str],
) -> None:
    """Parse one stdout line (stream-json, json, or text) and print live progress."""
    line = raw_line.strip()
    if not line:
        return
    elapsed = (time.perf_counter_ns() - start_ns) / 1_000_000_000.0
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        chunks.append(line)
        print(f"      [+{elapsed:5.1f}s] {line}", flush=True)
        return

    if not isinstance(obj, dict):
        return
    ev = obj.get("event")
    if ev == "init":
        telemetry["conversation_id"] = str(obj.get("conversation_id", ""))
        print(f"      [+{elapsed:5.1f}s] [agy] Session started", flush=True)
    elif ev == "step_update":
        upd = obj.get("step_update") or {}
        if upd.get("text_delta"):
            chunks.append(str(upd["text_delta"]))
        msg = _format_step_update(upd, elapsed)
        if msg:
            print(msg, flush=True)
    elif ev == "result":
        res = obj.get("result") or {}
        usage = res.get("usage") or {}
        telemetry["input_tokens"] = int(usage.get("input_tokens", 0))
        telemetry["output_tokens"] = int(usage.get("output_tokens", 0))
        telemetry["total_tokens"] = int(usage.get("total_tokens", 0))
        telemetry["conversation_id"] = str(
            res.get("conversation_id", telemetry.get("conversation_id", ""))
        )
        if res.get("response"):
            chunks.append(str(res["response"]))
        print(
            f"      [+{elapsed:5.1f}s] [agy] Result: {res.get('status', 'DONE')} "
            f"(tokens={telemetry['total_tokens']:,})",
            flush=True,
        )
    elif "usage" in obj:
        usage = obj.get("usage") or {}
        telemetry["input_tokens"] = int(usage.get("input_tokens", 0))
        telemetry["output_tokens"] = int(usage.get("output_tokens", 0))
        telemetry["total_tokens"] = int(usage.get("total_tokens", 0))
        telemetry["conversation_id"] = str(obj.get("conversation_id", ""))
        if obj.get("response"):
            chunks.append(str(obj["response"]))


def run_timed_agent_command(agent_cmd: str) -> Dict[str, Any]:
    """Execute and time an agent command, streaming live progress and parsing telemetry."""
    start_ns = time.perf_counter_ns()
    telemetry: Dict[str, Any] = {
        "duration_sec": 0.0,
        "exit_code": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "subagents_used": "none detected",
        "conversation_id": "",
    }
    chunks: List[str] = []
    with subprocess.Popen(
        agent_cmd,
        shell=True,
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    ) as proc:
        if proc.stdout is not None:
            for raw_line in proc.stdout:
                _process_stream_line(raw_line, start_ns, telemetry, chunks)
        stderr_text = proc.stderr.read().strip() if proc.stderr is not None else ""
        proc.wait()
        telemetry["exit_code"] = proc.returncode

    telemetry["duration_sec"] = round((time.perf_counter_ns() - start_ns) / 1_000_000_000.0, 4)
    if stderr_text:
        print(stderr_text, file=sys.stderr, flush=True)
    telemetry["subagents_used"] = _detect_subagents(
        "\n".join(chunks), str(telemetry.get("conversation_id", ""))
    )
    return telemetry


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
            overflow_171_resolved, algo_exec_ms, feature_breakdown_json, notes,
            input_tokens, output_tokens, total_tokens, subagents_used, changelog_entry
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            snapshot["input_tokens"],
            snapshot["output_tokens"],
            snapshot["total_tokens"],
            snapshot["subagents_used"],
            snapshot["changelog_entry"],
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


def _format_tokens(val: Any) -> str:
    """Format an integer token count for Markdown tables."""
    count = int(val or 0)
    return f"`{count:,}`" if count > 0 else "`n/a`"


def render_markdown_report(runs: List[Dict[str, Any]], db_path: Path) -> str:
    """Render `PERFORMANCE_REPORT.md` focused on agent algorithm-fix speed."""
    latest = runs[-1]
    baseline = next((r for r in runs if r["is_baseline"] == 1), runs[0])
    chart = _build_chart_series(runs)

    history_rows = []
    for r in runs:
        tag = f"`{r['version_tag']}`" + (" **(Baseline)**" if r["is_baseline"] else "")
        delta_s = _format_delta(r["agent_duration_sec"], baseline["agent_duration_sec"], "s")
        issue_status = "RESOLVED" if r["overflow_171_resolved"] else "UNRESOLVED"
        sub_str = r.get("subagents_used", "unknown") or "unknown"
        chg_str = r.get("changelog_entry", "") or r["label"]
        history_rows.append(
            f"| {r['id']} | {tag} | {chg_str} | `{r['agent_duration_sec']:.3f}s` | "
            f"`{delta_s}` | {_format_tokens(r.get('total_tokens'))} | `{sub_str}` | {issue_status} "
            f"({r['doctests_attempted']} doctests) |"
        )
    history_table = "\n".join(history_rows)

    return f"""# CS 440 Lab 6 — Agent Algorithm-Fix Performance Report

SQLite Database: `{db_path.name}` | Total Runs: **{len(runs)}** | Baseline: **`{baseline["version_tag"]}`** ({baseline["label"]})

---

## 1. Baseline (`{baseline["version_tag"]}`) vs. Latest (`{latest["version_tag"]}`) Algorithm-Fix Speed

| Metric | Baseline (`{baseline["version_tag"]}`) | Latest (`{latest["version_tag"]}`) | Delta / Status |
| :--- | :---: | :---: | :---: |
| **Agent Fix Duration** | `{baseline["agent_duration_sec"]:.3f} s` | `{latest["agent_duration_sec"]:.3f} s` | `{_format_delta(latest["agent_duration_sec"], baseline["agent_duration_sec"], "s")}` |
| **Total Agent Tokens** | {_format_tokens(baseline.get("total_tokens"))} | {_format_tokens(latest.get("total_tokens"))} | `in={latest.get("input_tokens", 0):,}, out={latest.get("output_tokens", 0):,}` |
| **Sub-Agents Invoked** | `{baseline.get("subagents_used", "unknown")}` | `{latest.get("subagents_used", "unknown")}` | `issue-researcher` & `contributing-reviewer` |
| **Issue #15656 (`n=171`) Fix** | `{"RESOLVED" if baseline["overflow_171_resolved"] else "UNRESOLVED"}` | `{"RESOLVED" if latest["overflow_171_resolved"] else "UNRESOLVED"}` | `maths/binomial_distribution.py` |
| **AST `CONTRIBUTING.md` Compliance** | `{"PASS" if baseline["ast_compliant"] else "FAIL"}` | `{"PASS" if latest["ast_compliant"] else "FAIL"}` | `{latest["doctests_attempted"]}` doctests |

---

## 2. Agent Fix Duration Trend (Seconds — Lower is Faster)

```mermaid
xychart-beta
    title "Agent Fix Duration (s) Across Harness Versions"
    x-axis [{chart["x_versions"]}]
    y-axis "Agent Fix Duration (s)" 0 --> {chart["y_sec_max"]}
    bar [{chart["y_agent_secs"]}]
    line [{chart["y_agent_secs"]}]
```

---

## 3. SQLite Run History (`agent_runs` Table)

| Run | Version | Change / Tuning | Duration | Delta vs. `{baseline["version_tag"]}` | Tokens | Sub-Agents | Verification |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- | :--- |
{history_table}
"""


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
        "changelog_entry": args.change or _latest_changelog_entry() or args.label,
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
    parser.add_argument("--notes", default="", help="Optional tuning notes")
    parser.add_argument("--db-file", default=str(DEFAULT_DB_FILE), help="SQLite DB path")
    parser.add_argument(
        "--report-file", default=str(DEFAULT_REPORT_FILE), help="Markdown report path"
    )
    parser.add_argument("--json", action="store_true", help="Print JSON snapshot to stdout")
    args = parser.parse_args()

    def _log(msg: str) -> None:
        if not args.json:
            print(msg, flush=True)

    _log(f"[1/4] Starting '{args.label}' (version={args.version or 'auto'})...")
    telemetry: Dict[str, Any] = {
        "duration_sec": 0.0,
        "exit_code": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "subagents_used": "unknown",
    }
    if args.agent_cmd:
        _log(f"      Executing agent command: {args.agent_cmd}")
        telemetry = run_timed_agent_command(args.agent_cmd)
        _log(
            f"      Agent finished in {telemetry['duration_sec']:.3f}s "
            f"(exit_code={telemetry['exit_code']}, tokens={telemetry['total_tokens']:,}, "
            f"subagents={telemetry['subagents_used']})."
        )
    elif args.agent_duration_sec is not None:
        telemetry["duration_sec"] = float(args.agent_duration_sec)
        _log(f"      Using recorded agent duration: {telemetry['duration_sec']:.3f}s.")
    else:
        t0 = time.perf_counter_ns()
        measure_harness_features()
        telemetry["duration_sec"] = round((time.perf_counter_ns() - t0) / 1_000_000_000.0, 4)

    _log("[2/4] Measuring harness checks & context efficiency...")
    db_path = Path(args.db_file)
    report_path = Path(args.report_file)
    with init_db(db_path) as conn:
        _log("[3/4] Benchmarking target algorithm & saving run to SQLite...")
        snapshot = _build_snapshot(args, conn, telemetry)
        record_run(conn, snapshot)
        runs = fetch_runs(conn)

    _log(f"[4/4] Rendering {report_path.name}...")
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

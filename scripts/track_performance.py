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
import selectors
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
    changelog_entry TEXT NOT NULL DEFAULT '',
    fork_overhead_sec REAL NOT NULL DEFAULT 0.0
);
"""

MIGRATION_COLUMNS = (
    ("input_tokens", "INTEGER NOT NULL DEFAULT 0"),
    ("output_tokens", "INTEGER NOT NULL DEFAULT 0"),
    ("total_tokens", "INTEGER NOT NULL DEFAULT 0"),
    ("subagents_used", "TEXT NOT NULL DEFAULT 'unknown'"),
    ("changelog_entry", "TEXT NOT NULL DEFAULT ''"),
    ("fork_overhead_sec", "REAL NOT NULL DEFAULT 0.0"),
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
            (
                "not TestPart7PerformanceTracker and "
                "not TestPart9MakefileCleanupAndTelemetry and "
                "not TestPart10AgentAgnosticSupport"
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


_TOOL_ICONS = {
    "read_file": "📖",
    "view_file": "📖",
    "edit_file": "✏️",
    "replace_file_content": "✏️",
    "write_file": "📝",
    "write_to_file": "📝",
    "run_command": "💻",
    "grep_search": "🔍",
    "find_by_name": "🔍",
    "list_dir": "📂",
    "define_subagent": "🛠️",
    "invoke_subagent": "🤖",
    "call_mcp_tool": "🔌",
    "read_resource": "🔌",
}


def _summarize_tool_params(params: Dict[str, Any]) -> str:
    """Return a concise one-line summary of tool/subagent parameters."""
    if params.get("TypeName") or params.get("Role"):
        tname = params.get("TypeName", "subagent")
        role = params.get("Role", "")
        return f"{tname}" + (f" ({role})" if role else "")
    for key in ("CommandLine", "Path", "ToolName", "Query", "Pattern"):
        if params.get(key):
            val = str(params[key]).replace("\n", " ").strip()
            if key == "Path":
                val = Path(val).name if len(val) > 65 else val
            return val[:90] + ("..." if len(val) > 90 else "")
    return ""


def _format_step_update(upd: Dict[str, Any], elapsed: float) -> Optional[str]:
    """Format a stream-json `step_update` into an emoji-rich live console line."""
    state = upd.get("state", "")
    stype = upd.get("step_type", "step")
    idx = upd.get("step_index", "?")
    if stype == "user_input":
        return None
    info = upd.get("tool_info") or {}
    tname = upd.get("tool_name") or info.get("name") or stype
    if state == "ACTIVE" and stype in ("tool", "subagent"):
        detail = _summarize_tool_params(info.get("parameters") or {})
        suffix = f" -> {detail}" if detail else ""
        return f"      [+{elapsed:5.1f}s] {_TOOL_ICONS.get(tname, '⚙️')} #{idx} {tname}{suffix}"
    if state in ("DONE", "ERROR"):
        dur = upd.get("duration_seconds")
        dur_str = f" ({dur:.2f}s)" if isinstance(dur, (int, float)) else ""
        if stype == "agent_response":
            tok = (upd.get("usage") or {}).get("total_tokens", 0)
            tok_str = f", {tok:,} tokens" if tok else ""
            return f"      [+{elapsed:5.1f}s] 🧠 #{idx} Agent planned/responded{dur_str}{tok_str}"
        if stype == "system_message":
            return f"      [+{elapsed:5.1f}s] 📬 #{idx} Sub-agent finished & woke orchestrator"
        err = (info.get("error") or {}).get("message", "")
        badge = "❌" if state == "ERROR" else "✅"
        return (
            f"      [+{elapsed:5.1f}s] {badge} #{idx} {tname} {state.lower()}{dur_str}"
            + (f" | {err[:70]}" if err else "")
        )
    return None


def _poll_subagent_transcripts(
    start_epoch: float,
    start_ns: int,
    main_conv_id: str,
    seen_lines: Dict[str, int],
) -> None:
    """Stream new tool calls from active sub-agent transcripts in real time."""
    elapsed = (time.perf_counter_ns() - start_ns) / 1_000_000_000.0
    for base in (
        Path.home() / ".gemini-personal" / ".gemini" / "antigravity-cli" / "brain",
        Path.home() / ".gemini" / "antigravity-cli" / "brain",
    ):
        if not base.exists():
            continue
        for tpath in base.glob("*/.system_generated/logs/transcript.jsonl"):
            conv_id = tpath.parent.parent.parent.name
            if conv_id == main_conv_id or tpath.stat().st_mtime < start_epoch:
                continue
            lines = tpath.read_text(encoding="utf-8", errors="ignore").splitlines()
            prev = seen_lines.get(conv_id, 0)
            for raw in lines[prev:]:
                _print_subagent_step(raw, conv_id[:8], elapsed)
            seen_lines[conv_id] = len(lines)


def _print_subagent_step(raw_json: str, short_id: str, elapsed: float) -> None:
    """Print one sub-agent tool call from a transcript JSONL line."""
    try:
        step = json.loads(raw_json)
    except json.JSONDecodeError:
        return
    for tc in step.get("tool_calls") or []:
        name = tc.get("name", "tool")
        icon = _TOOL_ICONS.get(name, "⚙️")
        detail = _summarize_tool_params(tc.get("arguments") or tc.get("args") or {})
        suffix = f" -> {detail}" if detail else ""
        print(
            f"      [+{elapsed:5.1f}s]    🤖↳ [subagent:{short_id}] {icon} {name}{suffix}",
            flush=True,
        )


def _handle_claude_event(
    obj: Dict[str, Any],
    elapsed: float,
    telemetry: Dict[str, Any],
    chunks: List[str],
) -> None:
    """Handle Claude Code `--output-format stream-json` NDJSON events."""
    ctype = obj.get("type")
    if ctype == "system" and obj.get("subtype") == "init":
        sid = str(obj.get("session_id", ""))
        telemetry["conversation_id"] = sid
        print(f"      [+{elapsed:5.1f}s] 🔌 Claude session started ({sid[:8]})", flush=True)
    elif ctype == "assistant":
        for block in (obj.get("message") or {}).get("content") or []:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use":
                name = str(block.get("name", "tool"))
                inp = block.get("input") or {}
                chunks.append(json.dumps(inp))
                icon = _TOOL_ICONS.get(name, "🤖" if name == "Task" else "⚙️")
                detail = _summarize_tool_params(inp) or str(inp.get("subagent_type", ""))
                suffix = f" -> {detail}" if detail else ""
                print(f"      [+{elapsed:5.1f}s] {icon} {name}{suffix}", flush=True)
            elif block.get("type") == "text" and block.get("text"):
                chunks.append(str(block["text"]))
    elif ctype == "result":
        usage = obj.get("usage") or {}
        in_tok = int(usage.get("input_tokens", 0))
        out_tok = int(usage.get("output_tokens", 0))
        telemetry["input_tokens"] = in_tok
        telemetry["output_tokens"] = out_tok
        telemetry["total_tokens"] = int(usage.get("total_tokens", in_tok + out_tok))
        if obj.get("result"):
            chunks.append(str(obj["result"]))
        print(
            f"      [+{elapsed:5.1f}s] 🏁 Result: {obj.get('subtype', 'DONE')} "
            f"(total tokens={telemetry['total_tokens']:,})",
            flush=True,
        )


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
        print(f"      [+{elapsed:5.1f}s] 💬 {line}", flush=True)
        return

    if not isinstance(obj, dict):
        return
    if "type" in obj and "event" not in obj:
        _handle_claude_event(obj, elapsed, telemetry, chunks)
        return
    ev = obj.get("event")
    if ev == "init":
        conv_id = str(obj.get("conversation_id", ""))
        telemetry["conversation_id"] = conv_id
        print(f"      [+{elapsed:5.1f}s] 🔌 Session started ({conv_id[:8]})", flush=True)
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
            f"      [+{elapsed:5.1f}s] 🏁 Result: {res.get('status', 'DONE')} "
            f"(total tokens={telemetry['total_tokens']:,})",
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
    """Execute and time an agent command, streaming main and sub-agent progress."""
    start_ns = time.perf_counter_ns()
    start_epoch = time.time()
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
    seen_lines: Dict[str, int] = {}
    with subprocess.Popen(
        agent_cmd,
        shell=True,
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    ) as proc:
        sel = selectors.DefaultSelector()
        if proc.stdout is not None:
            sel.register(proc.stdout, selectors.EVENT_READ)
        while sel.get_map():
            events = sel.select(timeout=1.5)
            if not events:
                _poll_subagent_transcripts(
                    start_epoch, start_ns, str(telemetry["conversation_id"]), seen_lines
                )
                continue
            for key, _ in events:
                raw_line = key.fileobj.readline()  # type: ignore[union-attr]
                if raw_line:
                    _process_stream_line(raw_line, start_ns, telemetry, chunks)
                else:
                    sel.unregister(key.fileobj)
        sel.close()
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
            input_tokens, output_tokens, total_tokens, subagents_used, changelog_entry,
            fork_overhead_sec
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            snapshot["fork_overhead_sec"],
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


def _effective_duration(row: Dict[str, Any]) -> float:
    """Return agent duration normalized with initial fork overhead."""
    return round(
        float(row["agent_duration_sec"]) + float(row.get("fork_overhead_sec", 0.0) or 0.0),
        4,
    )


def _build_chart_series(runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute x/y series strings and axis bounds for Mermaid xychart-beta graphs."""
    recent = runs[-10:]
    max_sec = max([_effective_duration(r) for r in recent] + [1.0])
    max_ms = max([r["harness_eval_ms"] for r in recent] + [100.0])
    return {
        "x_versions": ", ".join(f'"{r["version_tag"]}"' for r in recent),
        "y_agent_secs": ", ".join(str(round(_effective_duration(r), 3)) for r in recent),
        "y_eval_ms": ", ".join(str(round(r["harness_eval_ms"], 1)) for r in recent),
        "y_scores": ", ".join(str(round(r["harness_score_pct"], 1)) for r in recent),
        "y_sec_max": round(max_sec * 1.25, 2),
        "y_ms_max": round(max_ms * 1.25, 0),
    }


def _format_tokens(val: Any) -> str:
    """Format an integer token count for Markdown tables."""
    count = int(val or 0)
    return f"`{count:,}`" if count > 0 else "`n/a`"


def _format_history_row(row: Dict[str, Any], base_eff: float) -> str:
    """Format a single run row for the Markdown history table."""
    tag = f"`{row['version_tag']}`" + (" **(Baseline)**" if row["is_baseline"] else "")
    eff_s = _effective_duration(row)
    fork_s = float(row.get("fork_overhead_sec", 0.0) or 0.0)
    dur_cell = (
        f"`{eff_s:.3f}s` (`+{fork_s:.1f}s` fork)"
        if fork_s > 0
        else f"`{eff_s:.3f}s` (cold fork)"
    )
    delta_s = _format_delta(eff_s, base_eff, "s")
    issue_status = "RESOLVED" if row["overflow_171_resolved"] else "UNRESOLVED"
    sub_str = row.get("subagents_used", "unknown") or "unknown"
    chg_str = row.get("changelog_entry", "") or row["label"]
    return (
        f"| {row['id']} | {tag} | {chg_str} | {dur_cell} | "
        f"`{delta_s}` | {_format_tokens(row.get('total_tokens'))} | `{sub_str}` | {issue_status} "
        f"({row['doctests_attempted']} doctests) |"
    )


def render_markdown_report(runs: List[Dict[str, Any]], db_path: Path) -> str:
    """Render `PERFORMANCE_REPORT.md` focused on agent algorithm-fix speed."""
    latest = runs[-1]
    baseline = next((r for r in runs if r["is_baseline"] == 1), runs[0])
    chart = _build_chart_series(runs)
    base_eff = _effective_duration(baseline)
    lat_eff = _effective_duration(latest)
    history_table = "\n".join(_format_history_row(r, base_eff) for r in runs)

    return f"""# CS 440 Lab 6 — Agent Algorithm-Fix Performance Report

SQLite Database: `{db_path.name}` | Total Runs: **{len(runs)}** | Baseline: **`{baseline["version_tag"]}`** ({baseline["label"]})

---

## 1. Baseline (`{baseline["version_tag"]}`) vs. Latest (`{latest["version_tag"]}`) Algorithm-Fix Speed

| Metric | Baseline (`{baseline["version_tag"]}`) | Latest (`{latest["version_tag"]}`) | Delta / Status |
| :--- | :---: | :---: | :---: |
| **Normalized Duration (incl. Cold Fork)** | `{base_eff:.3f} s` | `{lat_eff:.3f} s` | `{_format_delta(lat_eff, base_eff, "s")}` |
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
        "fork_overhead_sec": round(float(args.fork_overhead_sec), 4),
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
    parser.add_argument("--json", action="store_true", help="Print JSON snapshot to stdout")
    args = parser.parse_args()

    def _log(msg: str) -> None:
        if not args.json:
            print(msg, flush=True)

    _log(f"\n🚀 [1/4] Starting '{args.label}' (version={args.version or 'auto'})...")
    telemetry: Dict[str, Any] = {
        "duration_sec": 0.0,
        "exit_code": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "subagents_used": "unknown",
    }
    if args.agent_cmd:
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

"""SQLite persistence and Markdown report rendering for Lab 6 performance runs."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List

try:
    from scripts import report_evidence
except ImportError:
    import report_evidence  # type: ignore[import-not-found,no-redef]

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
    fork_overhead_sec REAL NOT NULL DEFAULT 0.0,
    subagent_breakdown_json TEXT NOT NULL DEFAULT '{}'
);
"""

MIGRATION_COLUMNS = (
    ("input_tokens", "INTEGER NOT NULL DEFAULT 0"),
    ("output_tokens", "INTEGER NOT NULL DEFAULT 0"),
    ("total_tokens", "INTEGER NOT NULL DEFAULT 0"),
    ("subagents_used", "TEXT NOT NULL DEFAULT 'unknown'"),
    ("changelog_entry", "TEXT NOT NULL DEFAULT ''"),
    ("fork_overhead_sec", "REAL NOT NULL DEFAULT 0.0"),
    ("subagent_breakdown_json", "TEXT NOT NULL DEFAULT '{}'"),
)


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


def record_run(conn: sqlite3.Connection, snapshot: Dict[str, Any]) -> None:
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
            fork_overhead_sec, subagent_breakdown_json
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
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
            json.dumps(snapshot.get("subagent_breakdown", {})),
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
    ev = report_evidence.collect_solution_evidence()

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
{chr(10).join(_format_history_row(r, base_eff) for r in runs)}

---

## 4. Main Agent vs. Sub-Agent Breakdown (`{latest["version_tag"]}`)

| Agent Role | Duration | Tokens | Responsibility |
| :--- | :---: | :---: | :--- |
{report_evidence.render_subagent_section(latest)}

---

## 5. Phase 2 Deliverables, Issue `#15656` Fix & Passing Test Evidence

- **Modified Algorithm Target**: `maths/binomial_distribution.py` (fixed `float(factorial(trials))` `OverflowError` for `trials >= 171` using `math.comb` + log-space `lgamma`/`log`/`log1p`/`exp` fallback).
- **Generated Workflow Deliverables**: {ev["created_files"]}

### Issue `#15656` Fix Implementation (`maths/binomial_distribution.py`)

```python
{ev["snippet"]}
```

### Live Passing Test & Compliance Proof

**1. `python3 -m doctest -v maths/binomial_distribution.py`:**

```text
{ev["doctest_out"]}
```

**2. `fast_audit.py maths/binomial_distribution.py` (`CONTRIBUTING.md`, `ruff`, `mypy`, `pylint`):**

```json
{ev["audit_out"]}
```

**3. `pytest tests/test_src_workflow.py -q --tb=short` (Phase 2 `src/` Workflow Tests):**

```text
{ev["src_test_out"]}
```
"""

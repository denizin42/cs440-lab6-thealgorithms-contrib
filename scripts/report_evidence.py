"""Sub-agent transcript metrics and live Issue #15656 solution evidence helpers."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent

BUGGY_BINOMIAL_DISTRIBUTION = '''"""For more information about the Binomial Distribution:
https://en.wikipedia.org/wiki/Binomial_distribution
"""

from __future__ import annotations

from math import factorial


def binomial_distribution(successes: int, trials: int, prob: float) -> float:
    """
    Return probability of k successes out of n tries, with p probability for one
    success

    The function uses the factorial function in order to calculate the binomial
    coefficient

    >>> binomial_distribution(3, 5, 0.7)
    0.30870000000000003
    >>> binomial_distribution(2, 4, 0.5)
    0.375
    """
    if successes > trials:
        raise ValueError("successes must be lower or equal to trials")
    if trials < 0 or successes < 0:
        raise ValueError("the function is defined for non-negative integers")
    if not isinstance(successes, int) or not isinstance(trials, int):
        raise ValueError("the function is defined for non-negative integers")
    if not 0 < prob < 1:
        raise ValueError("prob has to be in range of 1 - 0")
    probability = (prob**successes) * ((1 - prob) ** (trials - successes))
    # Calculate the binomial coefficient: n! / k!(n-k)!
    coefficient = float(factorial(trials))
    coefficient /= factorial(successes) * factorial(trials - successes)
    return probability * coefficient


if __name__ == "__main__":
    from doctest import testmod

    testmod()
'''


def reset_target_to_buggy(target_path: Optional[Path] = None) -> Path:
    """Reset `maths/binomial_distribution.py` to the original buggy Issue #15656 state."""
    dest = target_path or (REPO_ROOT / "maths" / "binomial_distribution.py")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(BUGGY_BINOMIAL_DISTRIBUTION, encoding="utf-8")
    return dest


def _parse_step_ts(raw_json: str) -> float:
    """Extract ISO-8601 `created_at` epoch seconds from a transcript line."""
    try:
        ts = json.loads(raw_json).get("created_at", "")
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp() if ts else 0.0
    except (json.JSONDecodeError, ValueError):
        return 0.0


def _parse_step_tokens(raw_json: str) -> int:
    """Extract token total if present on a transcript step."""
    try:
        data = json.loads(raw_json)
        usage = data.get("usage") or {}
        if usage.get("total_tokens"):
            return int(usage["total_tokens"])
        return int(data.get("input_tokens") or 0) + int(data.get("output_tokens") or 0)
    except (json.JSONDecodeError, TypeError, ValueError):
        return 0


def _detect_subagent_role(lines: List[str]) -> str:
    """Infer subagent role name from initial transcript lines."""
    prompt_line = lines[0] if lines else ""
    head = "\n".join(lines[:5])
    for name in ("issue-researcher", "contributing-reviewer"):
        if name in prompt_line or name in head:
            return name
    if "fast_audit" in prompt_line or "Audit " in prompt_line:
        return "contributing-reviewer"
    if "15656" in prompt_line or "Analyze Issue" in prompt_line or "overflow" in prompt_line:
        return "issue-researcher"
    if "fast_audit" in head or "CONTRIBUTING" in head:
        return "contributing-reviewer"
    if "15656" in head or "binomial_distribution" in head:
        return "issue-researcher"
    return "subagent"


def iter_recent_subagent_transcripts(
    start_epoch: float, main_conv_id: str
) -> List[Tuple[str, List[str]]]:
    """Return `(conv_id, lines)` for sub-agent transcripts modified since `start_epoch`."""
    results: List[Tuple[str, List[str]]] = []
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
            if not lines:
                continue
            first_ts = _parse_step_ts(lines[0])
            if not first_ts or first_ts < start_epoch - 5.0:
                continue
            results.append((conv_id, lines))
    return results


def collect_subagent_metrics(start_epoch: float, telemetry: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize main orchestrator and per-subagent duration & tokens from transcripts."""
    main_conv_id = str(telemetry.get("conversation_id", ""))
    total_dur = float(telemetry.get("duration_sec", 0.0))
    sub_list: List[Dict[str, Any]] = []
    for conv_id, lines in iter_recent_subagent_transcripts(start_epoch, main_conv_id):
        first_ts, last_ts = _parse_step_ts(lines[0]), _parse_step_ts(lines[-1])
        if not first_ts or first_ts < start_epoch - 5.0:
            continue
        dur = round(max(0.0, last_ts - first_ts), 2) if last_ts else 0.0
        tok = sum(_parse_step_tokens(raw) for raw in lines)
        sub_list.append(
            {
                "name": _detect_subagent_role(lines),
                "id": conv_id[:8],
                "duration_sec": dur,
                "tokens": tok,
            }
        )

    subagents_str = str(telemetry.get("subagents_used", ""))
    if not sub_list and subagents_str not in ("none detected", "unknown", ""):
        for name in [s.strip() for s in subagents_str.split(",") if s.strip()]:
            sub_list.append({"name": name, "id": "inline", "duration_sec": 0.0, "tokens": 0})
    return {
        "main_agent": {
            "duration_sec": round(total_dur, 2),
            "total_duration_sec": round(total_dur, 2),
            "tokens": int(telemetry.get("total_tokens", 0)),
        },
        "subagents": sub_list,
    }


def collect_solution_evidence() -> Dict[str, str]:
    """Collect Issue #15656 code snippet, generated files, and live passing test proof."""
    algo_path = REPO_ROOT / "maths" / "binomial_distribution.py"
    lines = algo_path.read_text(encoding="utf-8").splitlines()
    start_idx = next(
        (i for i, ln in enumerate(lines) if ln.startswith("def binomial_distribution(")), 0
    )
    impl_lines = [ln for ln in lines[start_idx:] if not ln.strip().startswith(">>>")]
    snippet = "\n".join(impl_lines[:45]).strip()

    doctest_proc = subprocess.run(
        [sys.executable, "-m", "doctest", "-v", "maths/binomial_distribution.py"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    audit_script = REPO_ROOT.joinpath(
        ".claude", "skills", "denizin42-contributing", "scripts", "fast_audit.py"
    )
    audit_proc = subprocess.run(
        [sys.executable, str(audit_script), "maths/binomial_distribution.py"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    src_test_proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_src_workflow.py", "-q", "--tb=short"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    created = [
        p.relative_to(REPO_ROOT).as_posix()
        for p in sorted((REPO_ROOT / "src").glob("*.py"))
        if p.name != "__pycache__"
    ]
    for extra in ("tests/test_src_workflow.py", "CONTRIBUTION_REPORT.md"):
        if (REPO_ROOT / extra).exists():
            created.append(extra)
    return {
        "snippet": snippet,
        "doctest_out": "\n".join(doctest_proc.stdout.strip().splitlines()[-12:]),
        "audit_out": audit_proc.stdout.strip(),
        "src_test_out": src_test_proc.stdout.strip(),
        "created_files": ", ".join(f"`{f}`" for f in created),
    }


def render_subagent_section(latest: Dict[str, Any]) -> str:
    """Render Section 4: Main Agent vs. Sub-Agent Breakdown."""
    raw = latest.get("subagent_breakdown_json") or "{}"
    try:
        bd = json.loads(raw) if isinstance(raw, str) else dict(raw)
    except (json.JSONDecodeError, TypeError):
        bd = {}
    main_info = bd.get("main_agent") or {
        "duration_sec": latest["agent_duration_sec"],
        "tokens": latest.get("total_tokens", 0),
    }
    tok_m = int(main_info.get("tokens", latest.get("total_tokens", 0)) or 0)
    tok_m_str = f"`{tok_m:,}`" if tok_m > 0 else "`n/a`"
    rows = [
        f"| **Main Orchestrator** (`{latest['version_tag']}`) | "
        f"`{float(main_info.get('duration_sec', 0.0)):.2f} s` | {tok_m_str} | "
        "Coordinates fork, sub-agents, PR & final verification |"
    ]
    for sub in bd.get("subagents") or []:
        dur_val = sub.get("duration_sec")
        dur_s = f"`{float(dur_val):.2f} s`" if dur_val else "`n/a`"
        tok_s = int(sub.get("tokens", 0) or 0)
        tok_s_str = f"`{tok_s:,}`" if tok_s > 0 else "`n/a`"
        rows.append(
            f"| Sub-Agent: `{sub.get('name', 'subagent')}` (`{sub.get('id', 'n/a')}`) | "
            f"{dur_s} | {tok_s_str} | Isolated context research / `CONTRIBUTING.md` audit |"
        )
    return "\n".join(rows)

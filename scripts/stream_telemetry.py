"""Live stream-json telemetry and sub-agent transcript streaming helpers."""

from __future__ import annotations

import json
from pathlib import Path
import selectors
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional

try:
    from scripts import report_evidence
except ImportError:
    import report_evidence  # type: ignore[import-not-found,no-redef]

REPO_ROOT = Path(__file__).resolve().parent.parent

_TOOL_ICONS = {
    "read_file": "📖", "view_file": "📖", "edit_file": "✏️", "replace_file_content": "✏️",
    "write_file": "📝", "write_to_file": "📝", "run_command": "💻", "grep_search": "🔍",
    "find_by_name": "🔍", "list_dir": "📂", "define_subagent": "🛠️", "invoke_subagent": "🤖",
    "call_mcp_tool": "🔌", "read_resource": "🔌",
}


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
    found = [n for n in ("issue-researcher", "contributing-reviewer") if n in corpus]
    return ", ".join(found) if found else "none detected"


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
    start_epoch: float, start_ns: int, main_conv_id: str, seen_lines: Dict[str, int]
) -> None:
    """Stream new tool calls from active sub-agent transcripts in real time."""
    elapsed = (time.perf_counter_ns() - start_ns) / 1_000_000_000.0
    for conv_id, lines in report_evidence.iter_recent_subagent_transcripts(
        start_epoch, main_conv_id
    ):
        role_name = report_evidence._detect_subagent_role(lines)  # pylint: disable=protected-access
        prev = seen_lines.get(conv_id, 0)
        for raw in lines[prev:]:
            _print_subagent_step(raw, role_name, elapsed)
        seen_lines[conv_id] = len(lines)


def _print_subagent_step(raw_json: str, role_name: str, elapsed: float) -> None:
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
            f"      [+{elapsed:5.1f}s]    🤖↳ [{role_name}] {icon} {name}{suffix}",
            flush=True,
        )


def _handle_claude_event(
    obj: Dict[str, Any], elapsed: float, telemetry: Dict[str, Any], chunks: List[str]
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
    raw_line: str, start_ns: int, telemetry: Dict[str, Any], chunks: List[str]
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
    elif ev == "result" or "usage" in obj:
        res = obj.get("result") or obj if ev == "result" else obj
        usage = res.get("usage") or {}
        telemetry["input_tokens"] = int(usage.get("input_tokens", 0))
        telemetry["output_tokens"] = int(usage.get("output_tokens", 0))
        telemetry["total_tokens"] = int(usage.get("total_tokens", 0))
        telemetry["conversation_id"] = str(
            res.get("conversation_id", telemetry.get("conversation_id", ""))
        )
        txt = res.get("response")
        if txt:
            chunks.append(str(txt))
        if ev == "result":
            print(
                f"      [+{elapsed:5.1f}s] 🏁 Result: {res.get('status', 'DONE')} "
                f"(total tokens={telemetry['total_tokens']:,})",
                flush=True,
            )


def default_telemetry(subagents_used: str = "none detected") -> Dict[str, Any]:
    """Return a zero-initialized telemetry dictionary."""
    return {
        "duration_sec": 0.0,
        "exit_code": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "subagents_used": subagents_used,
        "conversation_id": "",
    }


def run_timed_agent_command(agent_cmd: str) -> Dict[str, Any]:
    """Execute and time an agent command, streaming main and sub-agent progress."""
    start_ns = time.perf_counter_ns()
    start_epoch = time.time()
    telemetry = default_telemetry()
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
    telemetry["subagent_breakdown"] = report_evidence.collect_subagent_metrics(
        start_epoch, telemetry
    )
    return telemetry

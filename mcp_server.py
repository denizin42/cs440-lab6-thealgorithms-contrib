"""CS 440 Lab 6 — Feature 2: Model Context Protocol (MCP) Server.

Reference:
  - MCP with Claude Lecture (Tools, Resources, and Prompts)
  - Components of a Coding Agent Lecture (Component 03: Structured, Validated Tool Use)

Exposes the three MCP building blocks to guide the AI agent on `TheAlgorithms/Python`:
  1. Tools     (`@mcp.tool`)     — `read_context_doc`, `verify_contribution_target`
  2. Resources (`@mcp.resource`) — `thealgorithms://context`, `thealgorithms://issue-brief`
  3. Prompts   (`@mcp.prompt`)   — `/audit_contribution`
"""
# pylint: disable=fixme

from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict
from mcp.server.mcpserver import MCPServer
from pydantic import Field


# try:
#     from pydantic import Field
# except ImportError:
#     def Field(  # pylint: disable=invalid-name,unused-argument
#         default: Any = ..., **kwargs: Any
#     ) -> Any:  # type: ignore[misc]
#         """Fallback Field helper matching pydantic.Field signature."""
#         return default if default is not ... else None

    # class FastMCP:  # type: ignore[no-redef]
    #     """Minimal decorator-compatible FastMCP fallback for local unit testing."""

    #     def __init__(self, name: str, log_level: str = "ERROR") -> None:
    #         self.name = name
    #         self.log_level = log_level
    #         self.tools: Dict[str, Callable[..., Any]] = {}
    #         self.resources: Dict[str, Callable[..., Any]] = {}
    #         self.prompts: Dict[str, Callable[..., Any]] = {}

    #     def tool(
    #         self,
    #         name: str | None = None,
    #         description: str = "",  # pylint: disable=unused-argument
    #     ) -> Callable[..., Any]:
    #         """Register an MCP tool function."""
    #         def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
    #             tool_name = name or func.__name__
    #             self.tools[tool_name] = func
    #             return func

    #         return decorator

    #     def resource(
    #         self,
    #         uri: str,
    #         mime_type: str = "text/plain",  # pylint: disable=unused-argument
    #     ) -> Callable[..., Any]:
    #         """Register an MCP resource handler."""
    #         def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
    #             self.resources[uri] = func
    #             return func

    #         return decorator

    #     def prompt(
    #         self,
    #         name: str | None = None,
    #         description: str = "",  # pylint: disable=unused-argument
    #     ) -> Callable[..., Any]:
    #         """Register an MCP prompt template."""
    #         def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
    #             prompt_name = name or func.__name__
    #             self.prompts[prompt_name] = func
    #             return func

    #         return decorator

    #     def run(self) -> None:
    #         """Start the MCP server."""
    #         print(
    #             f"[{self.name}] MCP server initialized with {len(self.tools)} tools, "
    #             f"{len(self.resources)} resources, and {len(self.prompts)} prompts."
    #         )

# mcp = FastMCP("TheAlgorithmsContribMCP", log_level="ERROR")
mcp = MCPServer("TheAlgorithmsContribMCP", log_level="ERROR")

PROJECT_ROOT = Path(__file__).resolve().parent
CONTEXT_DOCS: Dict[str, Path] = {
    "contributing-rules.md": PROJECT_ROOT / "context" / "contributing-rules.md",
    "issue-brief.md": PROJECT_ROOT / "context" / "issue-brief.md",
    "fork-pr-workflow.md": PROJECT_ROOT / "context" / "fork-pr-workflow.md",
}


# ==============================================================================
# 1. MCP TOOLS (`@mcp.tool`)
# ==============================================================================


@mcp.tool(
    name="read_context_doc",
    description="Read a CS 440 TheAlgorithms context document and return its contents.",
)
def read_context_doc(
    doc_id: str = Field(
        description="Context doc ID (contributing-rules.md, issue-brief.md, fork-pr-workflow.md)"
    ),
) -> str:
    """Complete working reference example of `@mcp.tool`."""
    if doc_id not in CONTEXT_DOCS:
        raise ValueError(f"Doc '{doc_id}' not found. Valid IDs: {list(CONTEXT_DOCS)}")
    return CONTEXT_DOCS[doc_id].read_text(encoding="utf-8")


@mcp.tool(
    name="verify_contribution_target",
    description="Validate the issue number, target algorithm file, fork owner, and feature branch.",
)
def verify_contribution_target(
    issue_number: int = Field(
        default=15656, description="Open issue number from TheAlgorithms/Python"
    ),
    target_file: str = Field(
        default="maths/binomial_distribution.py",
        description="Relative path to the target Python algorithm file",
    ),
    fork_owner: str = Field(
        default="denizin42",
        description="Personal GitHub fork owner (never TheAlgorithms)",
    ),
    branch_name: str = Field(
        default="feature/fix_binomial_distribution",
        description="Feature branch name (never main or master)",
    ),
) -> str:
    """Validate that the contribution target obeys upstream isolation and `CONTRIBUTING.md`."""
    if issue_number <= 0:
        raise ValueError("issue_number must be a positive integer.")
    if not fork_owner.strip() or "thealgorithms" in fork_owner.strip().lower():
        raise ValueError("fork_owner cannot be empty or target TheAlgorithms.")
    if not branch_name.strip() or branch_name.strip().lower() in ("main", "master"):
        raise ValueError("branch_name cannot be empty, 'main', or 'master'.")
    target_path = PROJECT_ROOT / target_file
    if not target_file.endswith(".py") or not target_path.is_file():
        raise ValueError(f"target_file '{target_file}' must be an existing .py file.")
    return (
        f"Verified target: issue=#{issue_number}, file={target_file}, "
        f"fork={fork_owner}, branch={branch_name}"
    )


@mcp.tool(
    name="get_issue_root_cause_context",
    description="Return compact AST outline and live Issue #15656 overflow check for target_file.",
)
def get_issue_root_cause_context(
    target_file: str = Field(
        default="maths/binomial_distribution.py",
        description="Relative path to target Python algorithm file",
    ),
    issue_number: int = Field(default=15656, description="Upstream issue number"),
) -> Dict[str, Any]:
    """Inspect target_file locally in 1 call without scanning parent directories or GitHub."""
    target_path = PROJECT_ROOT / target_file
    if not target_path.is_file():
        raise ValueError(f"target_file '{target_file}' does not exist.")
    tree = ast.parse(target_path.read_text(encoding="utf-8"))
    funcs = [
        {
            "name": node.name,
            "line": node.lineno,
            "args": [arg.arg for arg in node.args.args],
        }
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
    ]
    overflow_resolved = False
    if target_file == "maths/binomial_distribution.py":
        spec = importlib.util.spec_from_file_location("binomial_distribution", target_path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            try:
                val = mod.binomial_distribution(85, 171, 0.5)
                overflow_resolved = isinstance(val, float) and 0.0 < val < 1.0
            except (OverflowError, ValueError):
                overflow_resolved = False
    return {
        "issue_number": issue_number,
        "target_file": target_file,
        "ast_functions": funcs,
        "overflow_171_resolved": overflow_resolved,
    }


@mcp.tool(
    name="run_fast_compliance_audit",
    description="Run compliance, doctest, ruff, mypy, and pylint on target_file in one call.",
)
def run_fast_compliance_audit(
    target_file: str = Field(
        default="maths/binomial_distribution.py",
        description="Relative path to target Python algorithm file",
    ),
) -> Dict[str, Any]:
    """Execute bundled fast_audit.py and return its compact JSON summary."""
    script = (
        PROJECT_ROOT
        / ".claude"
        / "skills"
        / "denizin42-contributing"
        / "scripts"
        / "fast_audit.py"
    )
    proc = subprocess.run(
        [sys.executable, str(script), target_file],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if not proc.stdout.strip():
        raise RuntimeError(f"fast_audit.py produced no output: {proc.stderr}")
    return dict(json.loads(proc.stdout))


# ==============================================================================
# 2. MCP RESOURCES (`@mcp.resource`)
# ==============================================================================


@mcp.resource("thealgorithms://context", mime_type="application/json")
def list_context_docs() -> list[str]:
    """Direct resource returning the list of available context document IDs."""
    return list(CONTEXT_DOCS.keys())


@mcp.resource("thealgorithms://issue-brief", mime_type="application/json")
def get_issue_brief_resource() -> dict[str, Any]:
    """Direct resource exposing your selected issue and fork target as a dictionary."""
    issue_brief = {
        "issue_number": "15656",
        "target_file": "maths/binomial_distribution.py",
        "fork_owner": "denizin42",
        "branch_name": "feature/fix_binomial_distribution",
    }
    return issue_brief


# ==============================================================================
# 3. MCP PROMPTS (`@mcp.prompt`)
# ==============================================================================


@mcp.prompt(
    name="audit_contribution",
    description=(
        "Ready-made prompt instructing the agent to solve the issue and audit CONTRIBUTING.md."
    ),
)
def audit_contribution_prompt(
    target_file: str = Field(
        default="maths/binomial_distribution.py",
        description="Relative path to the target algorithm file",
    ),
) -> str:
    """Reusable prompt template triggered via `/audit_contribution`."""
    return (
        f"Call `verify_contribution_target` on {target_file} to confirm upstream "
        f"isolation. Fix the issue in {target_file} following `CONTRIBUTING.md`. "
        "Generate the fork/PR and compliance workflow in `src/`."
    )

if __name__ == "__main__":
    mcp.run()

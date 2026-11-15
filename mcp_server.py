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

from pathlib import Path
from typing import Any, Callable, Dict

try:
    from mcp.server.fastmcp import FastMCP
    from pydantic import Field
except ImportError:
    def Field(  # pylint: disable=invalid-name,unused-argument
        default: Any = ..., **kwargs: Any
    ) -> Any:  # type: ignore[misc]
        """Fallback Field helper matching pydantic.Field signature."""
        return default if default is not ... else None

    class FastMCP:  # type: ignore[no-redef]
        """Minimal decorator-compatible FastMCP fallback for local unit testing."""

        def __init__(self, name: str, log_level: str = "ERROR") -> None:
            self.name = name
            self.log_level = log_level
            self.tools: Dict[str, Callable[..., Any]] = {}
            self.resources: Dict[str, Callable[..., Any]] = {}
            self.prompts: Dict[str, Callable[..., Any]] = {}

        def tool(
            self,
            name: str | None = None,
            description: str = "",  # pylint: disable=unused-argument
        ) -> Callable[..., Any]:
            """Register an MCP tool function."""
            def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
                tool_name = name or func.__name__
                self.tools[tool_name] = func
                return func

            return decorator

        def resource(
            self,
            uri: str,
            mime_type: str = "text/plain",  # pylint: disable=unused-argument
        ) -> Callable[..., Any]:
            """Register an MCP resource handler."""
            def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
                self.resources[uri] = func
                return func

            return decorator

        def prompt(
            self,
            name: str | None = None,
            description: str = "",  # pylint: disable=unused-argument
        ) -> Callable[..., Any]:
            """Register an MCP prompt template."""
            def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
                prompt_name = name or func.__name__
                self.prompts[prompt_name] = func
                return func

            return decorator

        def run(self) -> None:
            """Start the MCP server."""
            print(
                f"[{self.name}] MCP server initialized with {len(self.tools)} tools, "
                f"{len(self.resources)} resources, and {len(self.prompts)} prompts."
            )

mcp = FastMCP("TheAlgorithmsContribMCP", log_level="ERROR")

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
        default="fix/issue-15656-binomial-overflow",
        description="Feature branch name (never main or master)",
    ),
) -> str:
    """Validate that the contribution target obeys upstream isolation and `CONTRIBUTING.md`.

    ===========================================================================
    TODO (Part 5A - MCP Tool Implementation):
    Validate the 4 arguments before the agent begins modifying files or pushing:
      - `issue_number` must be a positive integer
      - `fork_owner` must be a non-empty string and MUST NOT be `"thealgorithms"`
        (case-insensitive) so the agent never targets the upstream repository
      - `branch_name` must be a non-empty string and MUST NOT be `"main"` or `"master"`
      - `target_file` must exist under `PROJECT_ROOT` and end with `.py`
    If all checks pass, return a confirmation string; otherwise raise `ValueError`.
    ===========================================================================
    """
    _ = (issue_number, target_file, fork_owner, branch_name)
    if issue_number < 0:
        raise ValueError("Issue number cannot be negative")
    if fork_owner == "" or "thealgorithms" in fork_owner:
        raise ValueError("Owner cannot be empty or thealgorithms")
    if branch_name == "" or "main|master" in branch_name:
        raise ValueError("Cannot commit directly to master or main")
    return "Positive Validation"


# ==============================================================================
# 2. MCP RESOURCES (`@mcp.resource`)
# ==============================================================================


@mcp.resource("thealgorithms://context", mime_type="application/json")
def list_context_docs() -> list[str]:
    """Direct resource returning the list of available context document IDs."""
    return list(CONTEXT_DOCS.keys())


@mcp.resource("thealgorithms://issue-brief", mime_type="application/json")
def get_issue_brief_resource() -> Dict[str, Any]:
    """Direct resource exposing your selected issue and fork target as a dictionary.

    ===========================================================================
    TODO (Part 5B - MCP Resource Implementation):
    Return a dictionary matching the 4 settings you selected in `CLAUDE.md`:
      - `"issue_number"`
      - `"target_file"`
      - `"fork_owner"`
      - `"branch_name"`
    ===========================================================================
    """
    # TODO (Part 5B): Return the dictionary of selected contribution settings
    raise NotImplementedError(
        "TODO (Part 5B): Implement `get_issue_brief_resource` in `mcp_server.py`."
    )


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
    """Reusable prompt template triggered via `/audit_contribution`.

    ===========================================================================
    TODO (Part 5C - MCP Prompt Implementation):
    Return a prompt string instructing the agent to:
      - Call `verify_contribution_target` to confirm upstream isolation
      - Fix the issue in `target_file` following `CONTRIBUTING.md`
      - Generate the fork/PR and compliance workflow in `src/`
    ===========================================================================
    """
    _ = target_file
    # TODO (Part 5C): Implement the reusable MCP prompt string
    raise NotImplementedError(
        "TODO (Part 5C): Implement `audit_contribution_prompt` in `mcp_server.py`."
    )


if __name__ == "__main__":
    mcp.run()

#!/usr/bin/env bash
# ==============================================================================
# PreToolUse Hook: Block Any Push or Pull Request Targeting Upstream TheAlgorithms
# ==============================================================================
# Lecture Reference: Components of a Coding Agent (Hooks & Execution Boundaries)
#
# Claude Code passes the pending Bash tool input as JSON on stdin:
#   {"tool_input": {"command": "gh pr create --repo TheAlgorithms/Python ..."}}
#
# Exit code semantics:
#   - Exit 0: Allow the tool call to proceed.
#   - Exit 2: Deterministically BLOCK the tool call and feed stderr back to the
#             agent explaining the policy violation.
# ==============================================================================

set -uo pipefail

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null || echo "$INPUT")

# ==============================================================================
# TODO (Part 6A - Deterministic Upstream Protection Hook):
# Inspect `$COMMAND` and block (with `exit 2` and a message to `>&2`) if the
# command attempts to run `gh pr create`, `gh repo fork --remote`, or `git push`
# targeting `TheAlgorithms` (case-insensitive) instead of your personal fork.
# Otherwise, allow the command (`exit 0`).
#
# HINTS:
# - Compare with `scripts/prevent-main-commit.sh` to see how a `PreToolUse`
#   guard inspects `$COMMAND` with `grep -Eiq` and exits with status `2`.
# - Test locally with:
#     pytest -k test_part_6a -v
# ==============================================================================

# TODO (Part 6A): Replace this placeholder with your upstream PR/push guard
exit 0

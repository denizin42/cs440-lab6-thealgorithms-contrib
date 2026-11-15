#!/usr/bin/env bash
# ==============================================================================
# CS 440 Lab 6 — Feature 1: Hooks (Safe Context Injection & Context Switcher)
# Reference:
#   - Agentic AI & Context Engineering Lecture (Slides 24–27)
#   - Components of a Coding Agent Lecture (Component 01 & 04: Live Repo Context)
# ==============================================================================

set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
CLAUDE_MD="$PROJECT_DIR/CLAUDE.md"
BRANCH=$(git -C "$PROJECT_DIR" branch --show-current 2>/dev/null || echo "main")

if [[ $# -gt 0 ]]; then
    PROMPT="$1"
elif [[ ! -t 0 ]]; then
    INPUT_PAYLOAD=$(cat)
    if command -v jq >/dev/null 2>&1; then
        PROMPT=$(echo "$INPUT_PAYLOAD" | jq -r '.prompt // ""' 2>/dev/null || echo "$INPUT_PAYLOAD")
    else
        PROMPT="$INPUT_PAYLOAD"
    fi
else
    PROMPT=""
fi

touch "$CLAUDE_MD"

# --- Idempotent Context Injection Helper ---
add_context() {
    local context_ref="$1"
    grep -qxF "$context_ref" "$CLAUDE_MD" 2>/dev/null || echo "$context_ref" >> "$CLAUDE_MD"
}

# --- 1. Branch-based context selection ---
case "$BRANCH" in
    fix/issue-*|feature/fix*|feature/algorithm*|bugfix/*)
        add_context "@./context/issue-brief.md"
        add_context "@./context/contributing-rules.md"
        cat "$PROJECT_DIR/.claude/context/issue-brief.md"
        cat "$PROJECT_DIR/.claude/context/contributing-rules.md"
        ;;
    feature/fork*|pr/*|release/*)
        add_context "@./context/fork-pr-workflow.md"
        cat "$PROJECT_DIR/.claude/context/fork-pr-workflow.md"
        ;;
esac

# --- 2. Query-based context selection ---
if [[ -n "$PROMPT" ]]; then
    if echo "$PROMPT" | grep -Eiq 'contributing|doctest|type hint|snake_case|ruff|style|docstring'; then
        add_context "@./context/contributing-rules.md"
        cat "$PROJECT_DIR/.claude/context/contributing-rules.md"
    fi
    if echo "$PROMPT" | grep -Eiq 'issue|15656|15655|15576|binomial|continued_fraction|has_loop|overflow'; then
        add_context "@./context/issue-brief.md"
        cat "$PROJECT_DIR/.claude/context/issue-brief.md"
    fi
    if echo "$PROMPT" | grep -Eiq 'fork|pull request|pr|upstream|branch|submit|gh pr'; then
        add_context "@./context/fork-pr-workflow.md"
        cat "$PROJECT_DIR/.claude/context/fork-pr-workflow.md"
    fi
fi

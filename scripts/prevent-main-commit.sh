#!/usr/bin/env bash
# ==============================================================================
# Claude Code PreToolUse Hook:
# 1. Block `git commit` on `main` / `master` without staging `CHANGELOG.md`
# 2. Block any `gh pr create` or `git push` targeting upstream `TheAlgorithms/*`
# ==============================================================================

set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
INPUT_PAYLOAD="$(cat 2>/dev/null || true)"

# 1. Never allow PRs or pushes to upstream TheAlgorithms repositories
if echo "$INPUT_PAYLOAD" | grep -Eiq '(gh[[:space:]]+pr[[:space:]]+create.*TheAlgorithms/|git[[:space:]]+push[[:space:]]+upstream|TheAlgorithms/(Python|Java)\.git)'; then
    echo "BLOCKED [PreToolUse]: Contributing directly to upstream TheAlgorithms/* is prohibited by assignment rules. Target your personal fork instead!" >&2
    exit 2
fi

# 2. Check git commit branch & CHANGELOG rules
if echo "$INPUT_PAYLOAD" | grep -Eq 'git[[:space:]]+(-C[[:space:]]+[^[:space:]]+[[:space:]]+)?commit\b'; then
    BRANCH="$(git -C "$PROJECT_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")"
    if [[ "$BRANCH" == "main" || "$BRANCH" == "master" ]]; then
        echo "BLOCKED [PreToolUse]: Direct commits to '$BRANCH' are prohibited. Create a feature branch first (e.g., git checkout -b fix/issue-15656-binomial-overflow)." >&2
        exit 2
    fi
    if ! git -C "$PROJECT_DIR" diff --cached --name-only | grep -qx "CHANGELOG.md"; then
        echo "BLOCKED [PreToolUse]: CHANGELOG.md must be updated under '## [Unreleased]' and staged before committing." >&2
        exit 2
    fi
fi

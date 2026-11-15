#!/usr/bin/env bash
# ==============================================================================
# CS 440 Lab 6 — Safe Fork & Pull Request Automation Script
#
# CRITICAL SAFETY RULE:
#   Never open a PR against `TheAlgorithms/Python` or `TheAlgorithms/Java`!
#   All PRs must target ONLY your personal fork (`--repo <FORK_OWNER>/Python`)
#   so we do not spam upstream open-source maintainers during class labs.
# ==============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FORK_OWNER="${FORK_OWNER:-denizin42}"
REPO_NAME="${REPO_NAME:-Python}"
UPSTREAM_REPO="${UPSTREAM_REPO:-TheAlgorithms/Python}"
TARGET_REPO="${FORK_OWNER}/${REPO_NAME}"
BASE_BRANCH="${BASE_BRANCH:-master}"
ISSUE_NUMBER="${ISSUE_NUMBER:-15656}"
TARGET_FILE="${TARGET_FILE:-maths/binomial_distribution.py}"
SUMMARY="${SUMMARY:-Avoid float overflow in binomial_distribution for trials >= 171}"
DRY_RUN="${DRY_RUN:-true}"

# 1. Enforce personal fork isolation (never TheAlgorithms)
echo "[1/5] Validating fork target (${TARGET_REPO})..."
if [[ -z "$FORK_OWNER" ]] || echo "$FORK_OWNER" | grep -Eiq 'thealgorithms'; then
    echo "FATAL: Refusing to target upstream repository '${TARGET_REPO}'!" >&2
    exit 1
fi

# 2. Enforce feature branch (never main or master)
echo "[2/5] Checking feature branch..."
CURRENT_BRANCH="$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")"
if [[ "$CURRENT_BRANCH" == "main" || "$CURRENT_BRANCH" == "master" || -z "$CURRENT_BRANCH" ]]; then
    echo "FATAL: Must run from a feature branch (current: '${CURRENT_BRANCH}')." >&2
    exit 1
fi

# 3. Verify target algorithm doctests pass before pushing
echo "[3/5] Running doctests on ${TARGET_FILE}..."
python3 -m doctest -v "${REPO_ROOT}/${TARGET_FILE}" >/dev/null

# 4. Build PR body from .github/pull_request_template.md
echo "[4/5] Building PR description from template..."
PR_BODY="$(python3 "${REPO_ROOT}/.claude/skills/fork-pr-workflow/scripts/build_pr_body.py" \
    "$ISSUE_NUMBER" "$TARGET_FILE" "$SUMMARY")"

if [[ "$DRY_RUN" == "true" || "$DRY_RUN" == "1" ]]; then
    echo "[5/5] [DRY_RUN] Verified doctests for ${TARGET_FILE} on branch ${CURRENT_BRANCH}."
    echo "[DRY_RUN] Would fork ${UPSTREAM_REPO} -> ${TARGET_REPO} (if missing) and open fork-only PR:"
    echo "  gh pr create --repo ${TARGET_REPO} --base ${BASE_BRANCH} --head ${FORK_OWNER}:${CURRENT_BRANCH}"
    exit 0
fi

# 5. Live mode: ensure personal fork exists, push fixed file, and open fork-only PR
echo "[5/5] Forking ${UPSTREAM_REPO} -> ${TARGET_REPO} (if needed) and opening fork-only PR..."
if ! gh repo view "$TARGET_REPO" >/dev/null 2>&1; then
    echo "      Creating personal fork ${TARGET_REPO}..."
    gh repo fork "$UPSTREAM_REPO" --clone=false
fi

TMP_FORK_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_FORK_DIR"' EXIT

gh repo clone "$TARGET_REPO" "$TMP_FORK_DIR" -- --depth 1
git -C "$TMP_FORK_DIR" checkout -B "$CURRENT_BRANCH"
cp "${REPO_ROOT}/${TARGET_FILE}" "${TMP_FORK_DIR}/${TARGET_FILE}"
git -C "$TMP_FORK_DIR" add "$TARGET_FILE"
git -C "$TMP_FORK_DIR" commit -m "Fixes #${ISSUE_NUMBER}: ${SUMMARY}"
git -C "$TMP_FORK_DIR" push -f -u origin "$CURRENT_BRANCH"

gh pr create \
    --repo "$TARGET_REPO" \
    --base "$BASE_BRANCH" \
    --head "${FORK_OWNER}:${CURRENT_BRANCH}" \
    --title "Fix #${ISSUE_NUMBER}: ${SUMMARY}" \
    --body "$PR_BODY"

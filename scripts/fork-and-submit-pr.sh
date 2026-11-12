#!/usr/bin/env bash
# ==============================================================================
# CS 440 Lab 6 — Safe Fork & Pull Request Automation Script
#
# CRITICAL SAFETY RULE:
#   Never open a PR against `TheAlgorithms/Python` or `TheAlgorithms/Java`!
#   All PRs must target ONLY your own fork (`--repo <FORK_OWNER>/<REPO_NAME>`)
#   so we do not spam the upstream open-source maintainers during class labs.
# ==============================================================================

set -euo pipefail

# ==============================================================================
# TODO (Part 3B / Fork & PR Script):
# 1. Set FORK_OWNER to your personal GitHub username (never "TheAlgorithms").
# 2. Verify that TARGET_REPO does not start with "TheAlgorithms/".
# 3. Verify that CURRENT_BRANCH is a feature branch (not "main" or "master").
# 4. Run `python3 -m doctest -v` on your target algorithm file before pushing.
# 5. When DRY_RUN="false", push the feature branch to `origin` and invoke
#    `gh pr create --repo "${TARGET_REPO}" --base "${BASE_BRANCH}" --head "${CURRENT_BRANCH}" ...`
# ==============================================================================

FORK_OWNER="${FORK_OWNER:-TODO_SET_YOUR_GITHUB_USERNAME}"
REPO_NAME="${REPO_NAME:-cs440-lab6-thealgorithms-contrib}"
TARGET_REPO="${FORK_OWNER}/${REPO_NAME}"
BASE_BRANCH="${BASE_BRANCH:-main}"
ISSUE_NUMBER="${ISSUE_NUMBER:-15656}"
DRY_RUN="${DRY_RUN:-true}"

if [[ "$TARGET_REPO" =~ ^TheAlgorithms/ ]]; then
    echo "FATAL: Refusing to target upstream repository '$TARGET_REPO'!" >&2
    exit 1
fi

echo "TODO: Complete scripts/fork-and-submit-pr.sh for ${TARGET_REPO} (Issue #${ISSUE_NUMBER}, DRY_RUN=${DRY_RUN})"
exit 1

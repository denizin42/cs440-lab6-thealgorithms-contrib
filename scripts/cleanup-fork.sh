#!/usr/bin/env bash
# Clean up the personal fork (`denizin42/Python`) after benchmark/demo runs.
# Closes open PRs and deletes feature branches on the fork only.
# NEVER touches upstream `TheAlgorithms/*`.
set -euo pipefail

FORK_OWNER="${FORK_OWNER:-denizin42}"
REPO_NAME="${REPO_NAME:-Python}"
FORK_REPO="${FORK_OWNER}/${REPO_NAME}"

if [[ "${FORK_OWNER,,}" == *"thealgorithms"* ]]; then
    echo "BLOCKED: cleanup-fork.sh must never target upstream (${FORK_OWNER})." >&2
    exit 2
fi

echo "[1/3] Checking personal fork ${FORK_REPO}..."
if ! gh repo view "$FORK_REPO" >/dev/null 2>&1; then
    echo "      Fork ${FORK_REPO} does not exist; nothing to clean."
    exit 0
fi

DEFAULT_BRANCH="$(gh repo view "$FORK_REPO" --json defaultBranchRef -q '.defaultBranchRef.name')"

echo "[2/3] Closing any open Pull Requests on ${FORK_REPO}..."
OPEN_PRS="$(gh pr list --repo "$FORK_REPO" --state open --json number -q '.[].number' || true)"
if [[ -n "$OPEN_PRS" ]]; then
    for pr_num in $OPEN_PRS; do
        echo "      Closing ${FORK_REPO}#${pr_num}..."
        gh pr close "$pr_num" --repo "$FORK_REPO" --delete-branch \
            --comment "Closed by automated Lab 6 benchmark cleanup." >/dev/null || true
    done
else
    echo "      No open PRs found."
fi

echo "[3/3] Pruning Lab 6 test branches on ${FORK_REPO} (keeping ${DEFAULT_BRANCH})..."
BRANCHES="$(gh api "repos/${FORK_REPO}/branches" --paginate -q '.[].name' || true)"
for br in $BRANCHES; do
    if [[ "$br" == feature/* || "$br" == feat/* || "$br" == fix/* || "$br" == refactor/* ]]; then
        echo "      Deleting fork test branch ${FORK_REPO}:${br}..."
        gh api -X DELETE "repos/${FORK_REPO}/git/refs/heads/${br}" >/dev/null 2>&1 || true
    fi
done

echo "[cleanup-fork] ${FORK_REPO} is clean and ready for the next run."

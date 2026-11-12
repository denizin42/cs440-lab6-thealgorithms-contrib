#!/usr/bin/env bash
# ==============================================================================
# CS 440 Lab 6 — Live Demo Reset Script
# ==============================================================================
# Resets the repository back to the clean Phase 1 state on `main` (where `src/`
# contains only `src/README.md`, upstream target files in `maths/` and
# `data_structures/` are unmodified, and all Context Engineering pytest checks
# pass) so you can run a live hands-free agent demo from scratch.
# ==============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

git checkout main >/dev/null 2>&1 || true
rm -rf src/*.py src/__pycache__ tests/test_contrib_workflow.py CONTRIBUTION_REPORT.md
git checkout -- maths/ data_structures/ CHANGELOG.md 2>/dev/null || true

echo "=============================================================================="
echo "CS 440 Lab 6 (TheAlgorithms/Python Contribution) — Ready for Live Agent Demo!"
echo "=============================================================================="
python3 -m pytest -q tests/test_lab6_progress.py
echo ""
echo "1. Launch your coding agent in this directory:"
echo "     agy          # or: claude"
echo ""
echo "2. Paste this single instruction:"
echo "     Resolve our selected TheAlgorithms/Python issue end-to-end following CLAUDE.md and CONTRIBUTING.md."
echo "=============================================================================="

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Add live console progress output to track_performance.py and fork-and-submit-pr.sh, and instruct Phase 2 agent to fork first
- Focus performance tracker and PERFORMANCE_REPORT.md exclusively on Phase 2 agent algorithm-fix speed and remove pre-Phase-2 baseline data

### Added

- Record `v2` fork-first agent benchmark (`45.724s`, `-81.0%` vs `v1` baseline) in `PERFORMANCE_REPORT.md` and `logs/harness_performance.db`, with fork-only PR opened at `denizin42/Python#1`
- Fix Issue #15656 in maths/binomial_distribution.py, add src/ compliance & fork-PR workflow package, complete fork-and-submit-pr.sh, and record v1 agent fix baseline in PERFORMANCE_REPORT.md

- Ready for Phase 2 coding agent execution (Issue `#15656` fix, `src/` workflow package, and fork-only PR).

## [1.0.0] - 2026-11-14

### Added

- Completed Phase 1 Context Engineering Harness (`100%` test coverage across 21 unit tests):
  - Project memory & non-duplicative context routing in `CLAUDE.md` with symlinked `.claude/context/*.md` imports.
  - `UserPromptSubmit` (`scripts/context-switcher.sh`) and `PreToolUse` (`scripts/prevent-main-commit.sh`) hooks blocking `main` commits and upstream `TheAlgorithms/*` PRs.
  - On-demand skills (`denizin42-contributing` + AST `check_compliance.py`, `fork-pr-workflow` + `build_pr_body.py`).
  - Scoped read-only sub-agents (`contributing-reviewer`, `issue-researcher`) and FastMCP server (`mcp_server.py`).
  - SQLite-backed agent & harness performance tracker (`scripts/track_performance.py`, `logs/harness_performance.db`, `PERFORMANCE_REPORT.md` with `v1` baseline & Mermaid trending graphs).
  - Python dependency manifest (`requirements.txt`) and GitHub Actions CI (`pytest`, `pylint`, `doctest`).

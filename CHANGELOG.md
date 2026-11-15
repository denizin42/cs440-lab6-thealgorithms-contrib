# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Return concise `errors` dict in `fast_audit.py` on failing `compliance`/`doctests`/`ruff`/`mypy`/`pylint` checks, remove all solution hints (`math.comb`/`lgamma`) from `Makefile` `PROMPT` and `context/phase2-fastpath.md` (enforced by `TestPart16LeanOrchestratorAndAuditErrors`), and record honest `v11` solve-from-scratch run (`83.822s`, `-65.9%` vs `v1`, `57,647` main tokens, `contributing-reviewer` `6.00s`, `issue-researcher` `9.00s`) in `PERFORMANCE_REPORT.md`
- Auto-run `ruff check --fix` and `ruff format` in `fast_audit.py`, parallelize `issue-researcher` with `edit_file` in `context/phase2-fastpath.md`, and use fast `tests/test_src_workflow.py` (`0.79s`) in `Makefile` `PROMPT`; recorded `v10` (`110.805s`, sub-agents `3.00s` / `9,613` tok + `5.00s` / `14,469` tok) in `PERFORMANCE_REPORT.md`
- Add `context/phase2-fastpath.md` (symlinked into `.claude/context/` and imported in `CLAUDE.md`) and MCP `get_phase2_fastpath_bundle` tool to eliminate exploratory `ls`/`grep` turns and enforce single-pass post-edit `contributing-reviewer` auditing
- Record live `v9` fast-path benchmark (`108.264s`, `-55.9%` vs `v1`; sub-agents cut from `92s`/`49,642` tokens in `v8` to `9s`/`26,447` tokens in `v9`) in `PERFORMANCE_REPORT.md`
- Add `reset_target_to_buggy()` in `scripts/report_evidence.py` and automatic pre-run reset in `scripts/track_performance.py` (`--no-reset-target` opt-out) so every `make benchmark` run genuinely solves Issue `#15656` (`trials >= 171` `OverflowError`) from scratch
- Record live `v8` solve-from-scratch benchmark (`98.587s`, `-59.8%` vs `v1`, `51,727` main tokens, `issue-researcher` `24.00s` / `16,545` tokens, `contributing-reviewer` `68.00s` / `33,097` tokens) in `PERFORMANCE_REPORT.md`

### Fixed

- Display sub-agent role names (`[issue-researcher]`, `[contributing-reviewer]`) instead of `[subagent:<id>]` in live console output and filter out pre-existing transcripts in `iter_recent_subagent_transcripts()`
- Fix `_detect_subagent_role()` in `scripts/report_evidence.py` so `issue-researcher` (`fbd44a9e`) and `contributing-reviewer` (`2eb5608c`) are accurately labeled in `PERFORMANCE_REPORT.md`
- Instruct benchmark `PROMPT` in `Makefile` to invoke MCP tools (`verify_contribution_target`, `get_issue_root_cause_context`, `run_fast_compliance_audit`) with `EnableMCPTools=true`

### Changed

- Split `scripts/track_performance.py` into `scripts/harness_metrics.py`, `scripts/stream_telemetry.py`, and `scripts/report_renderer.py`, eliminating all CodeClimate `FILE_LENGTH` and Type-2 duplication violations (`0` clones, `0` violations across `scripts/` and `src/`)

- Prune intermediate benchmark runs `v2`–`v10` from `logs/harness_performance.db` and `PERFORMANCE_REPORT.md`, keeping `v1` baseline (`245.475s`) and `v11` latest (`83.822s`, `-65.9%`)
- Make `Makefile` (`AGENT=auto|claude|agy` and `AGENT_CMD`), `scripts/track_performance.py` (Claude Code + `agy` `stream-json` parsing), `CLAUDE.md`, and `README.md` agent-agnostic
- Strip Phase 1 `# HINTS:` blocks from `.claude/agents/*.md` and `SKILL.md`, route sub-agents to `flash`/`haiku` in parallel, pass `--effort medium` in `Makefile`, and record `v5` (`130.619s`, `38,084` tokens, `-48.5%` tokens vs `v4`) in `PERFORMANCE_REPORT.md`
- Upgrade console streaming output in `scripts/track_performance.py` and `scripts/cleanup-fork.sh` with step emojis, tool/parameter summaries, and real-time sub-agent transcript tailing
- Normalize `PERFORMANCE_REPORT.md` durations by adding `+4.5s` cold-fork overhead (`--fork-overhead-sec`) to runs that skipped initial repo forking (`v1`, `v3`)
- Deduplicate target config across `context/*.md` and `SKILL.md`, align `branch_name` in `mcp_server.py` with `CLAUDE.md`, fix `denizin42-contributing` skill references, and standardize comma-separated Claude tool names in agent/skill frontmatter
- Add live console progress output to track_performance.py and fork-and-submit-pr.sh, and instruct Phase 2 agent to fork first
- Focus performance tracker and PERFORMANCE_REPORT.md exclusively on Phase 2 agent algorithm-fix speed and remove pre-Phase-2 baseline data

### Added

- Add `scripts/report_evidence.py` (`Main Agent vs. Sub-Agent Breakdown` + Phase 2 Issue `#15656` code snippet & live passing `doctest`/`fast_audit.py`/`pytest` proof) to `PERFORMANCE_REPORT.md` and record `v7` (`129.762s`, `-47.1%` vs `v1`, `44,668` main tokens + per-subagent breakdown)
- Add `fast_audit.py` skill script, `get_issue_root_cause_context` & `run_fast_compliance_audit` MCP tools, scope sub-agents to the local repo, and record `v6` (`109.192s`, `-55.5%` vs `v1`, `41,929` tokens) in `PERFORMANCE_REPORT.md`
- Add `Makefile` (`install`, `test`, `lint`, `compliance`, `mcp-check`, `demo-dry-run`, `benchmark`, `cleanup-fork`), `scripts/cleanup-fork.sh`, Professor/TA `README.md` quickstart, and live `stream-json` token/sub-agent/changelog telemetry (`v3` recorded at `189.699s`, `53,210` tokens, `issue-researcher, contributing-reviewer`)
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

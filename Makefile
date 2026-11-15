.PHONY: help install test lint compliance mcp-check demo-dry-run benchmark cleanup-fork reset

PYTHON ?= python3
AGENT ?= auto
VERSION ?= v_next
LABEL ?= Harness Benchmark Run
CHANGE ?= Latest harness update
PROMPT ?= Follow CLAUDE.md and @./context/phase2-fastpath.md (do NOT run ls/grep on src/ or tests/): (1) Call MCP get_phase2_fastpath_bundle once (fork denizin42/Python already exists), (2) edit maths/binomial_distribution.py immediately using the math.comb + lgamma fallback pattern in parallel with launching issue-researcher (haiku/flash_lite, EnableMCPTools=true), (3) invoke contributing-reviewer ONCE post-edit (haiku/flash_lite) to run fast_audit.py + git status -s (auto-formats ruff), (4) run DRY_RUN=false bash scripts/fork-and-submit-pr.sh and pytest tests/test_src_workflow.py -q --tb=short once at the end. Name both subagents invoked.

help: ## Show available Lab 6 commands for Professor & TA
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies from requirements.txt
	$(PYTHON) -m pip install -r requirements.txt

test: ## Run the full pytest harness & workflow test suite
	$(PYTHON) -m pytest -q --tb=short

lint: ## Run pylint (10/10), ruff, and mypy across tracked Python files
	$(PYTHON) -m pylint --reports=n --score=y $$(git ls-files '*.py')
	$(PYTHON) -m ruff check --output-format=concise src/ maths/binomial_distribution.py
	$(PYTHON) -m mypy --no-error-summary --hide-error-context mcp_server.py src/ scripts/track_performance.py maths/binomial_distribution.py

compliance: ## Audit maths/binomial_distribution.py against CONTRIBUTING.md & run doctests
	$(PYTHON) .claude/skills/denizin42-contributing/scripts/check_compliance.py maths/binomial_distribution.py
	$(PYTHON) -m doctest -v maths/binomial_distribution.py

mcp-check: ## Verify the local FastMCP server resource & target validator
	$(PYTHON) -c "import mcp_server; cfg = mcp_server.get_issue_brief_resource(); print(cfg); print(mcp_server.verify_contribution_target(issue_number=int(cfg['issue_number']), target_file=cfg['target_file'], fork_owner=cfg['fork_owner'], branch_name=cfg['branch_name']))"

demo-dry-run: ## Dry-run the fork-only PR submission script (no GitHub push/PR)
	DRY_RUN=true bash scripts/fork-and-submit-pr.sh

benchmark: ## Run coding agent benchmark (AGENT=auto|claude|agy or custom AGENT_CMD), update PERFORMANCE_REPORT.md, and clean fork
	@CMD="$(AGENT_CMD)"; \
	if [ -z "$$CMD" ]; then \
		SEL="$(AGENT)"; \
		if [ "$$SEL" = "auto" ]; then \
			if command -v claude >/dev/null 2>&1; then SEL="claude"; \
			elif command -v agy >/dev/null 2>&1; then SEL="agy"; \
			else echo "ERROR: neither 'claude' nor 'agy' found in PATH (pass AGENT_CMD=...)." >&2; exit 1; fi; \
		fi; \
		if [ "$$SEL" = "claude" ]; then \
			CMD="claude --output-format stream-json --verbose --dangerously-skip-permissions -p '$(PROMPT)'"; \
		elif [ "$$SEL" = "agy" ]; then \
			CMD="agy --effort medium --output-format stream-json --dangerously-skip-permissions -p '$(PROMPT)'"; \
		else \
			CMD="$$SEL '$(PROMPT)'"; \
		fi; \
	fi; \
	$(PYTHON) scripts/track_performance.py \
		--version "$(VERSION)" \
		--label "$(LABEL)" \
		--change "$(CHANGE)" \
		--fork-overhead-sec 4.5 \
		--agent-cmd "$$CMD"
	bash scripts/cleanup-fork.sh

cleanup-fork: ## Close test PRs and prune feature branches on denizin42/Python
	bash scripts/cleanup-fork.sh

reset: ## Reset Phase 2 demo artifacts back to clean Phase 1 harness state
	bash scripts/demo-reset.sh

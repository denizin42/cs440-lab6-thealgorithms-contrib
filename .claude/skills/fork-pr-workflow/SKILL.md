---
# ==============================================================================
# TODO (Part 3B - `fork-pr-workflow` Skill Frontmatter,
#       Agent Skills Lecture Slides 8, 10–14):
# Configure the YAML frontmatter fields below so the agent loads this skill on
# demand when managing the personal fork, building a PR description, or opening
# a Pull Request:
#   - `name`: must match this skill's directory name (`fork-pr-workflow`)
#   - `description`: explain BOTH what the skill does and when to trigger it
#   - `allowed-tools`: whitelist the tools needed (`Read, Grep, Bash`)
# ==============================================================================
name: fork-pr-workflow
description: Forks the original repository to `denizin42` and sets up branch rules and a template for creating pull requests
allowed-tools: python gh git Read Grep Glob Bash
---

# Safe Fork & Pull Request Workflow Skill

## When to Use

Invoke this skill before forking from the original repository and creating a feature branch, pushing to your personal fork (`denizin42`), or generating/submitting a Pull Request.

## Step-by-Step Fork & PR Procedure

1. **Verify Upstream Isolation via MCP**:
   Call the `verify_contribution_target` MCP tool to confirm `fork_owner` is `denizin42` (never `TheAlgorithms`) and `branch_name` is a feature branch (not `main` or `master`).

2. **For the original algorithm code**:
   Use gh to fork the original repository to the same name in denizin42 reposistory. All work will be done on the forked copy.

2. **Render the Pull Request Body Using the Bundled Script**:

   ```bash
   python3 .claude/skills/fork-pr-workflow/scripts/build_pr_body.py \
       15656 maths/binomial_distribution.py \
       "Avoid float overflow in binomial_distribution for trials >= 171"
   ```

3. **Dry-Run or Submit to Your Personal Fork Only**:

   ```bash
   DRY_RUN=1 bash scripts/fork-and-submit-pr.sh
   ```

---
# ==============================================================================
# TODO (Part 3A - `denizin42-contributing` Skill Frontmatter,
#       Agent Skills Lecture Slides 4, 10–14):
# Configure the YAML frontmatter fields below so the agent loads this skill on
# demand when implementing or auditing an algorithm for `TheAlgorithms/Python`:
#   - `name`: must match this skill's directory name (`denizin42-contributing`)
#   - `description`: explain BOTH what the skill does and when to trigger it
#   - `allowed-tools`: whitelist only the read/execution tools needed (`Read, Grep, Glob, Bash`)
# ==============================================================================
name: denizin42-contributing
description: Check contribution compliance against original project `CONTRIBUTING.md` whenever editing a Python algorithm file.
allowed-tools: python3 Grep Read

---

# `TheAlgorithms/Python` Contributing Compliance Skill

## When to Use

Invoke this skill whenever writing, refactoring, or auditing a Python algorithm file (`maths/binomial_distribution.py`) against `CONTRIBUTING.md`.

## Step-by-Step Compliance Audit Procedure

1. **Run the Bundled AST Compliance Script** (*Agent Skills Lecture Slide 14: "Run scripts, don't read them"*):

   ```bash
   python3 .claude/skills/denizin42-contributing/scripts/check_compliance.py maths/binomial_distribution.py
   ```

2. **Execute Doctests Locally**:

   ```bash
   python3 -m doctest -v maths/binomial_distribution.py
   ```

3. **Run Static Type & Style Linters**:

   ```bash
   python3 -m mypy maths/binomial_distribution.py
   python3 -m pylint maths/binomial_distribution.py
   ```

4. **Verify Single-File Scope**:
   Ensure `README.md` and `DIRECTORY.md` were not modified and only the target algorithm file is touched for the Pull Request.

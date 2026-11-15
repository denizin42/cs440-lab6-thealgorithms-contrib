---
name: denizin42-contributing
description: Check contribution compliance against original project `CONTRIBUTING.md` whenever editing a Python algorithm file.
allowed-tools: Bash, Read, Grep, Glob
---

# `TheAlgorithms/Python` Contributing Compliance Skill

## When to Use

Invoke this skill whenever writing, refactoring, or auditing `<target_file>` (from `CLAUDE.md`) against `CONTRIBUTING.md`.

## Compliance Audit Commands

```bash
python3 .claude/skills/denizin42-contributing/scripts/check_compliance.py <target_file>
python3 -m doctest -v <target_file>
python3 -m mypy <target_file>
python3 -m pylint <target_file>
```

Ensure `README.md` and `DIRECTORY.md` are untouched and only `<target_file>` is modified for the PR.

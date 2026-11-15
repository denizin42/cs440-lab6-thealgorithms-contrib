---
name: denizin42-contributing
description: Check contribution compliance against original project `CONTRIBUTING.md` whenever editing a Python algorithm file.
allowed-tools: Bash, Read, Grep, Glob
---

# `TheAlgorithms/Python` Contributing Compliance Skill

## When to Use

Invoke whenever writing, refactoring, or auditing `<target_file>` (from `CLAUDE.md`) against `CONTRIBUTING.md`.

## Single-Command Audit

```bash
python3 .claude/skills/denizin42-contributing/scripts/fast_audit.py <target_file>
```

Ensure `README.md` and `DIRECTORY.md` are untouched and only `<target_file>` is modified for the PR.

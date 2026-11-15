---
name: contributing-reviewer
description: Audit algorithm changes against `CONTRIBUTING.md` using `fast_audit.py` or `run_fast_compliance_audit` and return a concise PASS/FAIL checklist.
tools: Bash, Glob, Grep, Read
skills: denizin42-contributing
model: haiku
---

# Sub-Agent: `contributing-reviewer`

Stay strictly inside the current repository. Run `python3 .claude/skills/denizin42-contributing/scripts/fast_audit.py <target_file>` (or call MCP `run_fast_compliance_audit`) once, verify only `<target_file>` is modified for the PR, and return:

- **Summary**: Overall PASS/FAIL
- **Critical/Major Issues**: Any compliance, doctest, or lint failures (`None` if clean)
- **Approval Status**: Ready to merge or changes needed
- **Obstacles Encountered**: Any environment quirks (`None` if clean)

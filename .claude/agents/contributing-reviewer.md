---
name: contributing-reviewer
description: Use this agent for auditing code changes to the algorithm file against `CONTRIBUTING.md` for quality, security, and best practice compliance before committing. Specify the target file(s) in the prompt.
tools: Bash, Glob, Grep, Read, WebFetch, WebSearch
skills: denizin42-contributing
model: haiku
---

# Sub-Agent: `contributing-reviewer`

## Code Review Template

- **Summary**: What was reviewed and overall assessment
- **Critical Issues**: Security, data integrity, or logic errors
- **Major Issues**: Quality, architecture, performance, missing tests, or `CONTRIBUTING.md` failures
- **Minor Issues**: Style, doc gaps, or small optimizations
- **Recommendations**: Refactoring and best practices
- **Approval Status**: Ready to merge or changes needed
- **Obstacles Encountered**: Setup quirks, special flags, or dependency issues

---
# ==============================================================================
# TODO (Part 4A - `issue-researcher` Sub-Agent Frontmatter & System Prompt,
#       Introduction to Subagents Lecture Slides 9, 13–18):
# Configure this isolated research sub-agent to investigate open issues and
# existing algorithms in the codebase without cluttering the main context window.
#
# HINTS:
# - Check Subagents Slide 15 ("Give each subagent only the tools its job needs")
#   for which tools belong on a read-only research sub-agent.
# - In the system prompt body below `---`, instruct the sub-agent on what to
#   check in `CONTRIBUTING.md` before implementing an algorithm (e.g., duplicate
#   implementations, edge cases, complexity) and define a structured output
#   format (Subagents Slides 13–14).
# ==============================================================================
name: issue-researcher
description: Investigate open issues and existing algorithms in the codebase without clusttering the main context window.
tools: Grep, Read, WebFetch
---

# Sub-Agent: `issue-researcher`

## Issues Researched
**Issue** - issue number and description 
**Summary** - what was researched, overall assessment
**Fix Proposal** - describe fix for issue chosen and how the agent would implement the fix.

## Add to the output template
**Obstacles Encountered**: Report any obstacles encountered during the research process. This can be setup issues, workarounds discovered or environment quirks. Report commands that needed a special flag or configuration. Report depenedencies or imports that caused problems.
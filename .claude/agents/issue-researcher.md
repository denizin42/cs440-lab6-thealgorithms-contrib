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
description: Researches CVE issues for 
tools: []
model: sonnet
color: blue
---

# Sub-Agent: `issue-researcher`

TODO_PART_4A_WRITE_RESEARCHER_SYSTEM_PROMPT

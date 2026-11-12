---
# ==============================================================================
# TODO (Part 4A - `contributing-reviewer` Sub-Agent Frontmatter & System Prompt,
#       Introduction to Subagents Lecture Slides 9–17):
# Configure this isolated code-review sub-agent to audit algorithm changes
# against `CONTRIBUTING.md`.
#
# HINTS:
# - Check Subagents Slide 9 & 15 for which tools a code reviewer needs (and which
#   file-modifying tools it should NOT have).
# - Check Agent Skills Slide 17 ("Subagents start fresh, so preload skills") for
#   how a sub-agent can preload your `thealgorithms-contributing` skill and keep
#   the ability to invoke skills.
# - Check Subagents Slides 11–12 for how the `description` steers both automatic
#   delegation and what the parent agent includes in the sub-agent's input prompt.
# - Check Subagents Slides 13–14 for why defining an explicit output format and
#   an obstacle-reporting section prevents endless research and lost workarounds.
# ==============================================================================
name: TODO_PART_4A_SET_REVIEWER_NAME
description: TODO_PART_4A_SET_REVIEWER_DESCRIPTION
tools: []
model: sonnet
color: purple
skills: thealgorithms-contributing
---

# Sub-Agent: `contributing-reviewer`

TODO_PART_4A_WRITE_REVIEWER_SYSTEM_PROMPT

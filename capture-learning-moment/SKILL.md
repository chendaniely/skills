---
name: capture-learning-moment
description: Use when a conversation with Claude contains a teachable moment worth documenting for students — especially when human expertise corrected or improved Claude's initial response, or when a domain constraint Claude overlooked changed the solution.
---

# Capture Learning Moment

## Overview

Documents a notable exchange from this conversation as a Quarto document (`.qmd`)
suitable for sharing with students or as reference material.
The best moments show the human-AI collaboration loop:
Claude produces a reasonable first answer,
human expertise reveals a gap,
and the collaboration produces the right solution.

## When to Use

- User corrects an oversight in Claude's response
- A domain-specific constraint (security, legal, git history, production systems) changes the solution
- Claude's approach was plausible but incomplete without the human's contextual knowledge
- Any "I didn't think of that" moment where the human's expertise was load-bearing

## What to Capture

| Element | What it is |
|---------|-----------|
| **Context** | What project/task was being worked on |
| **Initial ask** | The user's prompt that triggered the exchange |
| **Claude's first response** | What Claude produced or recommended |
| **The exchange** | The back-and-forth turns of correction and revision — may be one turn or several |
| **Final solution** | The corrected approach after all turns |
| **The lesson** | What this teaches about human-AI collaboration |

## Sensitive Information

**Always redact or replace sensitive values when writing the document.**
The `.qmd` file may be shared publicly (that's the point).
Replace real IPs, usernames, UUIDs, hostnames, API keys, and any other
identifying values with plausible fakes or placeholders
(e.g. `100.123.45.67`, `john.doe`, `AAAA1111-BBBB-2222-CCCC-333344445555`).
The learning is in the *structure* of the exchange, not the actual values.

If in doubt, ask the user whether a value is safe to include before writing the file.

## Steps

1. Identify the key exchange in the conversation — the moment where human expertise changed the outcome.
2. Ask the user for a short slug if it isn't obvious from context (2–4 words, kebab-case, e.g. `git-history-is-permanent`).
3. Use today's date from the session context.
4. Determine the output directory:
   - If the environment variable `LEARNING_MOMENTS_DIR` is set, use that path.
   - Otherwise, fall back to `~/learning-moments/`.
   Create the directory if it doesn't exist.
5. Use `template.qmd` (in this skill directory) as the structure.
6. Fill in each section from the actual conversation — quote or paraphrase faithfully.
7. In **The Exchange**, include every turn of the back-and-forth, not just the first correction.
   Some moments take one turn to resolve; others take several clarifications.
   Keep all of them — the false starts and refinements are part of the lesson.
8. In **The Lesson**, be explicit about *why* Claude missed it (not just *what* was missed).
   This is the most valuable part for students.

## The Lesson Section

This section is the core teaching value.
Structure it as:

- **What Claude got right** — acknowledge what was reasonable about the first response
- **What required human expertise** — the specific knowledge or judgment Claude lacked
- **Why Claude missed it** — the structural reason (training cutoff, no runtime context, optimized for the stated goal not the unstated constraint, etc.)
- **Key takeaway** — one sentence a student can remember and apply

## Example

**Moment:** Documenting items to scrub before making a dotfiles repo public.
Claude listed the actual sensitive values (IPs, usernames, UUIDs) in `AGENTS.md`.
User corrected: those values would be in git history permanently, even if the file later changed.

- **What Claude got right:** Identified all the correct categories of sensitive data.
- **What required human expertise:** Understanding that git history is permanent — scrubbing a file's current content does not remove past commits.
- **Why Claude missed it:** Optimized for the immediate ask (document what to scrub) without considering the medium (git) as a constraint on *how* to document it.
- **Key takeaway:** Always ask what the documentation itself will be committed to — the answer changes what you can safely write.

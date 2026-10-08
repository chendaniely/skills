---
name: capture-learning-moment
description: Use when the user asks to capture, document or write up a learning moment (or teachable moment) from the current conversation for students — especially one where human expertise corrected or improved Claude's first answer, or a domain constraint Claude overlooked changed the solution. Writes a Quarto .qmd write-up. Not for ingesting a conversation into a notes vault (that is capture-conversation).
---

# Capture Learning Moment

## Overview

Documents a notable exchange from this conversation as a Quarto document (`.qmd`)
suitable for sharing with students or as reference material.
When the output folder is a Quarto website, the document becomes a post on that site.
The best moments show the human-AI collaboration loop:
Claude produces a reasonable first answer,
human expertise reveals a gap,
and the collaboration produces the right solution.

## When to Use

Run this when the user asks for it (for example `/capture-learning-moment`).
The points below are not triggers.
They describe what makes a good moment to pick from the conversation:

- The user corrected an oversight in Claude's response
- A domain-specific constraint (security, legal, git history, production systems) changed the solution
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
The `.qmd` file may be shared publicly (that's the point),
and when the output folder is a published website, a push makes it public.
Replace real IPs, usernames, UUIDs, hostnames, local file paths, API keys, and any other
identifying values with plausible fakes or placeholders
(e.g. `100.123.45.67`, `john.doe`, `AAAA1111-BBBB-2222-CCCC-333344445555`).
The learning is in the *structure* of the exchange, not the actual values.

If in doubt, ask the user whether a value is safe to include before writing the file.

## Steps

1. Identify the key exchange in the conversation — the moment where human expertise changed the outcome.
2. Get a short slug (2–4 words, kebab-case, e.g. `git-history-is-permanent`):
   - If the user gave one with the command (e.g. `/capture-learning-moment git-history-is-permanent`), use it.
   - Otherwise, propose one and ask the user to confirm or change it.
3. Use today's date from the session context.
4. Determine the output directory:
   - If the environment variable `LEARNING_MOMENTS_DIR` is set, use that path.
   - Otherwise, fall back to `~/learning-moments/`.
   Create the directory if it doesn't exist.
5. Decide the post folder:
   - If the output directory has a `_quarto.yml`, it is a Quarto website.
     Read its `CLAUDE.md` (or `AGENTS.md`, else `README.md`) and follow it where it differs from this skill.
     The post folder is the one it names; without one, it is the folder the home page's `listing: contents:` reads (usually `posts/`).
     Then follow [Quarto Website Posts](#quarto-website-posts) as well.
   - Otherwise, the post folder is the output directory itself.
6. Write to `<post folder>/YYYY-MM-DD-<slug>.qmd`, using the date from step 3.
   **If that file already exists, do not overwrite it.**
   Ask the user whether to overwrite it or add a `-2` suffix (`YYYY-MM-DD-<slug>-2.qmd`).
7. Use `template.qmd` (in this skill directory) as the structure.
8. Fill in each section from the actual conversation — quote or paraphrase faithfully.
9. If the original turns are no longer verbatim in context (for example, the conversation was compacted), say so.
   Label those parts of the document as paraphrase,
   and ask the user whether to pull the exact text from the session transcript or keep the paraphrase.
10. In **The Exchange**, include every turn of the back-and-forth, not just the first correction.
    Some moments take one turn to resolve; others take several clarifications.
    Keep all of them — the false starts and refinements are part of the lesson.
11. In **The Lesson**, be explicit about *why* Claude missed it (not just *what* was missed).
    This is the most valuable part for students.
12. Report the path of the file you wrote, and for a website post, the URL it will have once published.

## Quarto Website Posts

When step 5 found a Quarto website, the post must render as part of it:

- **Keep the template's front matter.** The listing sorts by `date` and filters by `categories`; a post without them sorts wrong or hides from filters.
- **Companion files** (a repro page, an image) go beside the post, named after it (`YYYY-MM-DD-<slug>-repro.html`), linked by relative path.
- **Link other moments by relative `.qmd` path** (`[title](YYYY-MM-DD-other-slug.qmd)`); Quarto rewrites it to `.html`.
  Never link a moment by its GitHub blob or raw URL: readers should land on the rendered page.
- **Render the post** with `quarto render <post folder>/<file>.qmd` from the folder holding `_quarto.yml`.
  Fix warnings the new post causes; report any that come from elsewhere instead of editing other files.
- **The published URL** is the `site-url` from `_quarto.yml`, plus the post's path from the folder holding `_quarto.yml`, with `.html` for `.qmd`.
- **Don't commit or push unless asked.** If the site deploys on push, pushing publishes the post, so redaction has to be finished first.
  When asked to commit, stage only the post and its companion files, never `git add -A`, so unrelated work in the repo stays out.

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

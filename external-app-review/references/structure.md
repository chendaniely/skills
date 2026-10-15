# Section contracts

Each file's sections in order. Names in `<angle brackets>` are placeholders.
Worked example: <https://github.com/chendaniely/trivia-night/tree/main/docs/case-study>,
a local model's build reviewed and fixed by Claude Code.

## README.md (executive summary, about 80 lines)

1. `# <Title: who built what, then who reviewed it>`
2. **What happened:** one paragraph covering the builder (model, where it ran,
   harness), the dates, the commit count and attribution, what you did (review,
   fix tasks, final review), and the current status (merged? live?).
3. **Why:** one paragraph on the user's question in their own framing, such as
   "is a local model viable for real work", and who the folder is for.
4. Hero image: the builder's final version against yours, same screen and size.
5. `## TL;DR`, four bold-led bullets:
   - what the builder did well (credit first, specific)
   - what wasn't safe or good enough, with counts
   - whether the plugins, skills or harness mattered, against the user's own rules
   - your verdict in one or two sentences, pointing to chapter 6
6. `## Chapters`: a table with each file linked and a one-line description.
7. `## The numbers that frame it`: a table with columns builder and your pass.
   Rows: calendar time, commits (by model), lines written or changed, tests,
   defects left at the end, user prompts, marginal cost. A local model is $0
   marginal; don't estimate electricity or hardware cost unless it was
   measured.
8. `## Reading notes`: timezone, how attribution works, that opinions are
   yours and facts are linked, and what private material was left out.

## 01-setup-and-method.md

Sections: The question (the user's, quoted) · Hardware and model (served vs
configured context, quantization if known, speed) · Harness · Plugins, skills
and always-on instructions (counts; where each came from) · The user's process
rules (quote the repo's agent rules) · How this review was produced (your
review council, fix method, research sources, screenshot method).

## 02-timeline.md

- A Mermaid `gantt` from the first setup to the merge, with sections for setup,
  core build, user requests and your pass. Mark crises with `crit` and the
  merge with a `milestone`.
- `## Day N — <date>: <one-line arc>`: what the user asked (verbatim quotes,
  spelling kept), what the builder did (commit hashes), what went wrong, and
  1–2 inline screenshots.
- `## The shape of the work`: a process flowchart of the builder's loop, plus
  the patterns you saw (bursts, stalls, dropped requests, loops).

## 03-<builder>-review.md

1. `## Verdict in one paragraph`
2. `## Scorecard`: a table with columns Area | Grade | Evidence (short). Areas:
   following the user's process, planning and architecture, speed to MVP, core
   logic, robustness for real use, UI at the target size, verification
   honesty, content accuracy (if the app has content), knowing its own limits,
   tests, scope and safety.
3. `## What it did well`: a numbered list of specifics with hashes.
4. `## What went wrong`: one `###` per theme, each with what happened, the
   evidence, why it matters and the probable cause. Typical themes are invented
   facts, "verified" records that weren't, building to the letter of the plan
   rather than the real use, not knowing its own limits, dropped requests,
   scope and safety, and process overhead.
5. `## Code-level notes on <builder>'s final (<hash>)`
6. `## How much of this is the model, and how much the setup?`

## 04-<reviewer>-pass.md

1. `## The request`: the user's words.
2. `## How the pass ran`: a flowchart covering the review council, then per
   task the implementer, reviewers and fix rounds, then the final review and
   the fix wave.
3. `## The <builder>'s findings`: a table by review seat.
4. `## Every fix, with how it was verified`: a table with columns Task | What
   was wrong | Severity | Fix | Verified by (the real-browser check, test or
   measurement).
5. `## What <reviewer> got wrong along the way`: a numbered list of every
   mistake your own reviews caught, and how it was caught.
6. `## Numbers`: a table comparing builder and pass.
7. `## Outcome`: the merge (PR, merge commit), the deploy and gate results, a
   live check, and what is left that needs real hardware or people. Add this
   once the outcome exists.

## 05-plugins-and-skills.md

`## What actually loaded`: listed vs invoked counts, always-on texts, and any
misconfigured paths, with a flowchart from configuration to model behaviour.
`## Good, bad, or neutral?`: one verdict per item with evidence.
`## Recommendations for the next <model> project`.

## 06-verdict.md

`## Short answer` · `## Where it was good enough` (a table of task type and
evidence) · `## Where it was not` · `## What <reviewer> picked up that
<builder> did not` · `## Cost and speed, honestly` · `## A workflow I would
recommend for this machine` (a flowchart of the hybrid split, for example local
model as hands and stronger model as eyes) · `## Bottom line`.

## 07-gallery.md

Tables of `| Milestone (hash, time) | Image | What to notice |`, in three
sections: the build by milestone · what the builder "saw" (its own saved
screenshots or accessibility snapshots, and what it could not see) · after
your pass (target sizes, before/after pairs).

## appendix-a-prompts.md

Every user prompt in order, under date headings, with time, session and
length. Quote them verbatim. Replace private entries with a one-line summary
saying what was omitted. Include answers the user gave through the harness's
question popups.

## appendix-b-numbers.md

A source line (git range, transcript store, how model is determined, line-count
exclusions). Then: a commits-by-model Mermaid `pie showData` plus a by-type
table · time phases · code size per file at the builder's final vs after ·
sessions (prompts, tool calls, errors, compactions, tokens, speed) · defects by
who found them.

## research/README.md

Who produced the notes and when, that chapters win on conflicts, a table of
files and contents, and how the notes were sanitized.

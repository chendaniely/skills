# Research recipes

Everything here is read-only. Each research subagent writes one note into the
git-ignored workspace. You check its numbers before a chapter uses them.

## Commit history

- **Per-model counts** come from the trailer, not the author:
  `git log --no-merges --format='%(trailers:key=Co-Authored-By,valueonly)' <range> | sed 's/ <.*//' | sort | uniq -c`
- **Timeline:** `git log --reverse --format='%h %ad %s' --date=format:'%m-%d %H:%M'`.
  Keep deploy-bot commits separate.
- **Type mix:** count the Conventional Commit `type(scope)` prefixes. Bookkeeping
  share (for example, `docs(plan)`) is a finding.
- **Line counts:** `git log --numstat`, excluding vendored files, lockfiles and
  binaries. State the exclusions in Appendix B.
- **Rewrites:** `git reflog` for amends, resets and rebases.
- **Bursts and gaps:** runs of commits close together, and long gaps. Line
  these up with the user's prompts.

## Plan and spec

- `git log -p -- <plan file>` shows when each task and record appeared.
- Check every "verified", "clean" or "done" record against the code at that
  commit, and count the false ones. Verification honesty is a scorecard row.
- List every user request in order, and mark any that never reached the plan.

## Builder transcripts

- Find the harness's store. For opencode, that is a SQLite database under
  `~/.local/share/opencode/`. Copy it to the scratchpad, open the copy
  read-only, and read the schema before any content.
- Query narrowly. Never bulk-select message bodies into your context.
- Collect:
  - the user's prompts in order (Appendix A)
  - tool-call counts and errors
  - compactions and context truncations (served vs configured context)
  - tokens and speed
  - skill invocations against skills listed
  - loops (the same failing call repeated)
  - question-popup answers
- Look for safety events: credential files read, config edited outside the
  project, unrequested network calls. Record what and when, never the values.

## Harness config

Collect:
- plugins and where they came from
- skills listed against invoked
- always-on instruction files (global agent rules, plugin bootstrap texts)
- misconfigured paths
- provider and model settings

Record names and settings only; secrets are redacted at the source.

## Your own pass

Sources:
- your review findings
- the progress ledger or plan records for each task
- each reviewer's findings, including those against your own fixes
- the final whole-branch review
- the fix commits

Every mistake your reviews caught in your work goes in 04's
"got wrong" list.

## Content and facts

If the app ships content (questions, copy, data), fact-check it with web
search and two independent passes. Count wrong, invented and shaky items. Note
which errors the builder's own checks introduced.

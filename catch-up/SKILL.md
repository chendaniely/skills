---
name: catch-up
description: 'Use when Dan opens a session in the personal-zettelkasten vault after a gap (any phrasing of "catch me up", "what''s going on", or the start of a work burst). Drains the inbox, sweeps #todo lines into TODO.md, regenerates recent weekly rollups, and rewrites today''s daily-note Today block. The one verb for returning from a gap — Dan''s real rhythm is bursts separated by long gaps, not daily sessions.'
---

# Catch Up

## Overview

Dan works this vault in bursts separated by gaps — sometimes weeks. This skill is
what he says (or what fires automatically at a session's start) to reconstruct
context and clear the backlog that accumulated while he was away, in one pass.

It is **not** a status report. It changes the vault: files get moved, TODO.md
gets swept, rollups get written, and today's note gets a fresh `## Today` block.
Nothing here needs Dan's line-by-line approval — draining the inbox and sweeping
`#todo` are mechanical filing, not judgment calls about content. The one place
that *does* need judgment (which of several candidate homes a note belongs in)
gets a best-effort placement plus a one-line note in the daily log, not a stop.

## The four steps, always in this order

### 1. Drain `inbox/` (was `000-triage/`)

For every note in `inbox/`:
- Read it. Decide where it belongs based on the vault's existing folder
  conventions (`zettelkasten/<topic>/`, `zettelkasten/people/`, etc. — see the
  vault's `CLAUDE.md` for the current map).
- Move it there via the `obsidian` CLI (`obsidian move`) if Obsidian is
  running, so wikilinks update; if the CLI is unavailable, defer that specific
  note's move rather than risk a plain `mv` breaking a link, and say so.
- **Never edit the note's own words.** Filing is a location decision, not a
  content edit. If a note needs annotation, annotate below the original text.
- If a note's home is genuinely unclear, leave it in `inbox/` and flag it in
  the session's summary — don't force a bad placement to hit zero.

**Do NOT drain machine-generated transcripts.** `sources/transcripts/<y>/<m>/`
is where those live now (Phase 2's plaud reroute) — if any stray transcript
notes are still in `inbox/`, that's a one-time migration already done
(2026-08-20) or a sign the reroute broke; either way, flag it, don't silently
re-migrate on every run.

### 2. Sweep `#todo`

Search the vault for unchecked `- [ ] task text #todo` lines outside `TODO.md`
itself:

```bash
grep -rn '\- \[ \].*#todo' --include='*.md' . | grep -v '^\./TODO.md'
```

For each hit:
- Add a corresponding line to `TODO.md` under the right context heading, with
  a backlink to the source note: `- [ ] task text (from [[Source Note]])`.
- Leave the `#todo` line in the source note as-is (the tag marks it swept, it
  doesn't get deleted — the source stays the historical record).

**Reconcile both directions**: if an item is checked in `TODO.md` but its
source `#todo` line is still unchecked, check the source too (and vice versa).
Never let the two drift.

**The `#todo` gate is the note-sweep lane only.** It has nothing to do with
the Plaud author-filter (that's `plaud_sync.py`'s `extract_actions()`, fixed
2026-08-20) — don't conflate the two mechanisms.

### 3. Regenerate weekly rollups (bounded scope)

Generate/refresh **only the current ISO week and the previous one**. Older
weeks are backfilled only on explicit request ("backfill week N") — never as
part of a routine catch-up. This bound exists because dailies reach back to
2024; a literal "regenerate everything missing" would emit dozens of files on
the very first run.

File contract (fixed, don't improvise a different shape):
- Path: `000-periodic_notes/weekly/<YYYY>/<YYYY>-W<ww>.md` (zero-padded ISO
  week number, e.g. `2026-W34.md`).
- The generated content sits between two HTML comment markers:
  ```
  <!-- rollup:generated:start -->
  ...generated content here...
  <!-- rollup:generated:end -->
  ```
- **Anything Dan wrote outside those markers survives regeneration
  untouched.** Read the existing file first (if any), preserve everything
  outside the markers verbatim, replace only what's between them.
- A week with zero daily notes is **skipped entirely** — don't create an
  empty rollup file just to mark that nothing happened.
- Content inside the markers: what moved that week (new notes, decisions,
  captures), pulled from each day's `## Log` section and any `## Today` items
  that got checked off — not a re-summary of every daily note in full.

### 4. Rewrite today's `## Today` block

Today's daily note (`000-periodic_notes/daily/<y>/<m>/<date>.md`) gets its
`## Today` section (top of the file, above `## UBC`) rewritten — **hard cap:
5 lines**:

- Any dated item due within 3 days (scan `TODO.md` and recent captures for
  dates).
- The current `inbox/` count, if non-zero.
- One suggested next action, chosen from what's actually pending — not a
  generic prompt.

This is the block Dan sees first when Obsidian opens (`openBehavior: daily`).
It must be genuinely useful on one glance, not a status dump. If there's
nothing worth 5 lines, say less — an accurate 2-line block beats a padded
5-line one.

Leave `## Log` and everything else in the note untouched — this step touches
only the `## Today` section, identified by its heading, same
read-preserve-replace approach as the rollup markers.

## Closing

Report back to Dan, briefly: how many notes moved out of `inbox/` (and where),
how many `#todo` items got swept, which weeks got rollups (or "already
current"), and what's now in `## Today`. This is a summary of what changed,
not a re-explanation of the steps above.

If anything was flagged rather than resolved (an unclear inbox note, a
transcript found where it shouldn't be), say so explicitly — don't bury it in
the numbers.

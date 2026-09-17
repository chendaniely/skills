---
name: email-digest
description: 'Use when Dan asks to run, refresh or re-run his email digest (any phrasing of "run my email digest", "check my email", "what needs a reply", "update my email todos"), and when the daily-email-digest scheduled task fires. Produces the email digest, the email checklist in today''s Obsidian daily note, and an Inbox Brief from his Thunderbird mail, via the claude-cowork repo. Read-only on mail: never replies to, marks, moves or deletes it. Not for finding a specific message.'
---

# Email Digest

## Overview

Dan's email digest is code in **`/Users/dan/git/private/claude-cowork`** (the
"EA" repo). The code does all the reading and writing; this skill is the
procedure around it, and **you are the classifier** (agent mode). Every
command below names the repo with `uv run --directory`, so it works from any
working directory. Read the repo's `CLAUDE.md` first: its hard constraints
win over anything here.

Hard rules, never negotiable:
- **Thunderbird is strictly read-only.** Never write under
  `/Volumes/expansionSD/applications/thunderbird/profiles`. Never reply to,
  mark, move or delete any mail. Dan acts in Thunderbird himself.
- **Fail open.** Never drop a message to save effort. Anything you can't
  classify stays pending, so it surfaces as unclassified.
- **The daily note is the code's to write.** Never hand-edit anything between
  `<!-- ea-email:begin todos … -->` and `<!-- ea-email:end todos -->`, and
  never tick a box for Dan.
- **Use only the operations in the table below.** Anything else asks for
  permission, and in a scheduled run nobody answers.

## What a run may do

| Need | Use exactly |
|---|---|
| A pipeline step | Bash, one plain command per call: `uv run --directory /Users/dan/git/private/claude-cowork digest.py <subcommand> …` |
| Look at pending mail | The same command with `show-pending …` |
| Save verdicts | The Write tool, into your session's scratchpad directory (named in your system prompt) |
| Read a file | The Read tool, for files inside the repo (e.g. a saved digest) |

The Bash commands are written exactly as in the steps: no `cd`, pipes,
redirects, `&&` or heredocs. Everything else waits for an approval:
`python`, `python3`, `uv run python`, helper scripts, `cat`, `ls`, `sqlite3`,
`grep`, the `obsidian` CLI (the repo uses it elsewhere, but not here), any
write inside the repo, and reading files outside it, such as the daily note.
When that happens in a scheduled run, the run hangs for days, writes no
digest, and still shows "succeeded". This happened about 15 times between
July and September 2026. Don't Read `pending.json` itself either: it's
large, and `show-pending` exists to page through it. If a step seems to need
more than the table allows, skip that part and say so in the brief.

**No scratchpad directory?** Then you can't save verdicts. Do steps 1, 2 and
4, skip step 3, and say why in the brief. The digest still shows everything
classified earlier, and counts the rest as awaiting classification.

**If the run stops early,** the brief is a single line saying what stopped
it and which steps didn't run.

## Two modes

- **Unattended** (the scheduled task says so, or nobody is there to answer):
  never ask questions. Make reasonable calls and list them in the brief.
  Your working directory must be `/Users/dan/git/private/claude-cowork`:
  only that project's settings pre-approve these commands. If it's anything
  else, stop and report that.
- **Interactive** (Dan asked in a session): same steps and same table, from
  any working directory (Dan answers any permission prompts). You may ask
  before anything ambiguous, e.g. whether an old still-open item is really
  resolved. Still never tick boxes or touch mail on his behalf.

## Steps

1. **Scan** — `uv run --directory /Users/dan/git/private/claude-cowork digest.py scan`.
   - **Every mailbox reported missing** means the expansionSD volume isn't
     mounted: stop and report that.
   - **Only some missing:** carry on, and name those accounts in the brief.
2. **Export** — `uv run --directory /Users/dan/git/private/claude-cowork digest.py export-pending --out pending.json`.
   It prints how many messages it exported. If 0, skip to step 4.
3. **Classify, one batch at a time.**
   - **Skim everything first**, so you can see threads across the backlog:
     `uv run --directory /Users/dan/git/private/claude-cowork digest.py show-pending --start 0 --count 150 --chars 0`,
     then the same command with `--start 150`, `--start 300`, … (keep
     `--count 150 --chars 0` every time) until it prints `nothing at #…`.
   - **Read a batch:**
     `uv run --directory /Users/dan/git/private/claude-cowork digest.py show-pending --start 0 --count 40`.
     Each entry is `#n <id> · account · date · sender`, then the subject and
     the start of the body. For an ambiguous one, the same command with
     `show-pending --id <id>` prints the whole message.
   - **Classify each message in the batch** (rules below).
   - **Save the batch** with the Write tool as
     `<scratchpad>/verdicts-<start>.json`, one entry per message in the
     batch, with each `id` copied exactly from the listing:

     ```json
     {"verdicts": [
       {"id": "3f2a9c01", "importance": "high",
        "reason": "Ann needs your receipts by Friday.",
        "suggested_action": "Send Ann the travel receipts"},
       {"id": "0b91d4e7", "importance": "none",
        "reason": "Newsletter.", "suggested_action": null}
     ]}
     ```
   - **Ingest it:**
     `uv run --directory /Users/dan/git/private/claude-cowork digest.py ingest-verdicts <scratchpad>/verdicts-<start>.json`.
     It prints `applied A, unknown U · P still pending`. If `unknown` isn't 0,
     the `unmatched:` line names the entries it refused:
     - an id you mistyped: correct it from the listing, save the file again,
       and ingest it again (entries already applied are just reported as
       unmatched the second time);
     - an id that appears in no listing: delete that entry, and name it in
       the brief. Never guess which message it meant.
   - **Repeat** the same read command with `--start 40`, `--start 80`, … (keep
     `--count 40` every time) until it prints `nothing at #…`. Ingesting after
     every batch keeps the work if the session dies.
   - **Finish the leftovers.** If the last ingest doesn't say `0 still
     pending`, run the same command with `show-pending --remaining` to list
     exactly those messages. Classify them into
     `<scratchpad>/verdicts-remaining.json` and ingest it. Leave any you still
     can't judge, and report the count in the brief: they surface as
     unclassified if the next run misses them too.
   - **Classification rules:**
     - `importance` is one of:
       - `high`: needs Dan's action (a direct request, a question awaiting his
         reply, a deadline, a bill, a registration, anything time-sensitive).
       - `medium`: worth knowing (a schedule change, an FYI from a real
         person, a shared doc, a completed milestone).
       - `low`: marginal.
       - `none`: newsletters, marketing, automated notifications,
         past-dated events.
     - `reason`: one short sentence written for Dan. It appears in the digest.
     - `suggested_action`: a short imperative phrase for high/medium items
       that need action, else `null`. Every high item and every actionable
       medium item becomes a checklist line in the daily note, so make it a
       task Dan can tick off.
   - **Judgment calls:**
     - Be thread-aware across the whole backlog, using the skim. If a later
       message resolves an earlier one (form submitted, contract signed,
       invite superseded, meeting rescheduled), downgrade the earlier item
       and note the resolution.
     - Real people writing to Dan personally are at least `medium`.
     - Students or colleagues awaiting his reply are `high`.
     - Past-dated events and reminders are `none`.
     - Calendar invites that auto-add are `low`, unless the meeting is within
       ~24h or comes from an unknown sender needing an RSVP decision.
     - Judge against today's date. Mail can be weeks old after a string of
       failed runs; a request whose deadline has passed is still `high` if
       Dan may owe a reply, and the reason should say it's overdue.
4. **Render** — `uv run --directory /Users/dan/git/private/claude-cowork digest.py render`.
   - **What it does:** prints the digest, saves `digests/YYYY-MM-DD.md` (UTC
     date) in the repo, and regenerates the `## Email` checklist in today's
     Obsidian daily note. It ends with `[saved to digests/…]` and
     `[daily note updated: <path> · N open]`. If the printed digest is cut
     off, Read `/Users/dan/git/private/claude-cowork/digests/YYYY-MM-DD.md`.
   - **Open-item count for the brief:** the `N open` on that last line. Don't
     open the note yourself: it's outside the repo.
   - **What the checklist looks like:** grouped by priority, then account.
     Ticks are kept, and items Dan ticked on earlier days drop out.
   - **Re-running is safe** (the block is rewritten in place).
   - **Warnings go in the brief:** "vault not found" or "Obsidian CLI write
     failed; writing the file directly". The digest is valid either way.
5. **Report an Inbox Brief** (below), drawn from the rendered digest.

## Inbox Brief format

- **If the digest opens with `> ⚠ First digest in N days`, lead with that
  line.** It means scheduled runs failed in between. Say so plainly, and
  name the dates.
- **One-sentence roll-up:** messages scanned (and classified, if a backlog
  made that bigger), how many need action, the 2–3 themes, any invites.
- **Groups, in this order:** **Needs reply**, **Decision**, **FYI**,
  **Read later**.
  - Omit an empty group entirely.
  - 3–5 bullets per group, each `[Sender] — Subject — one-line gist`.
  - Lead each bullet with an icon: 📅 invite, 💰 money, ⏰ deadline,
    ⚠️ security/risk, 🎓 teaching/student, 🔧 infra/CI, 📄 doc/review.
  - Name the account when it isn't obvious.
  - If a group has more items than fit, add one trailing line with the count
    of the rest.
- **3–5 suggested next actions,** ordered by urgency.
- **One closing line:** the checklist is in today's daily note (with its
  open-item count), plus the footer's "ticked off in Obsidian" count if
  present.
- **Scope:** only what the digest surfaced.
  - Leave out bulk/marketing mail, system notifications and receipts.
  - Invites and anything time-sensitive always make the brief.
  - Report counts honestly: unclassified messages, the footer's "awaiting
    classification" count, and any batch you couldn't ingest.
  - Flag stale "still open" items (past-dated, or resolved by later mail) so
    Dan can tick them.
  - Check the other direction too. The skim only covers pending mail, so a
    new Needs-action item can already be resolved by a message an earlier run
    classified. Look for it under "Still open" (e.g. "proposal submitted",
    "TA accepted"), and flag the new item for ticking.
  - List anything you skipped because the table above didn't allow it.

## Coupling with claude-cowork

This skill depends on these parts of the repo:
- the CLI: `scan`, `export-pending`, `show-pending`, `ingest-verdicts`,
  `render`, and their output lines (including render's
  `[daily note updated: <path> · N open]`);
- the `pending.json` shape (`id`, `account`, `message_id`, `from_addr`,
  `subject`, `date`, `body_snippet`) and the verdict-file shape;
- the checklist markers, and the digest's `> ⚠` gap line;
- `config.yaml`'s `obsidian` block.

If any of those change in claude-cowork, update this file in the same
sitting. The repo's `CLAUDE.md` and its spec (Decisions Log #22, #25) say the
same from their side.

---
name: email-digest
description: 'Use when Dan asks to run, refresh or re-run his email digest (any phrasing of "run my email digest", "check my email", "what needs a reply", "update my email todos"), and when the daily-email-digest scheduled task fires. Scans Thunderbird mail read-only, classifies every pending message yourself (agent mode), renders the digest plus the email checklist in today''s Obsidian daily note, and reports an Inbox Brief. Driven by the claude-cowork repo; never replies to, marks, moves or deletes mail.'
---

# Email Digest

## Overview

Dan's email digest is code in **`/Users/dan/git/private/claude-cowork`** (the
"EA" repo). The code does all the reading and writing; this skill is the
procedure around it, and **you are the classifier** (agent mode). Run every
command from that repo's root, and read its `CLAUDE.md` first: its hard
constraints win over anything here.

Hard rules, never negotiable:
- **Thunderbird is strictly read-only.** Never write under
  `/Volumes/expansionSD/applications/thunderbird/profiles`. Never reply to,
  mark, move or delete any mail. Dan acts in Thunderbird himself.
- **Fail open.** Never drop a message to save effort. Anything you can't
  classify stays pending, so it surfaces as unclassified.
- **The daily note is the code's to write.** Never hand-edit anything between
  `<!-- ea-email:begin todos … -->` and `<!-- ea-email:end todos -->`, and
  never tick a box for Dan.

## Two modes

- **Unattended** (the scheduled task says so, or nobody is there to answer):
  never ask questions. Make reasonable calls and list them in the brief.
- **Interactive** (Dan asked in a session): same steps. You may ask before
  anything ambiguous, e.g. whether an old still-open item is really resolved.
  Still never tick boxes or touch mail on his behalf.

## Steps

1. **Scan** — `uv run digest.py scan`. If it reports mailbox files missing
   (the expansionSD volume isn't mounted), stop and report that.
2. **Export** — `uv run digest.py export-pending --out pending.json`. If 0,
   skip to step 5.
3. **Classify** every message in `pending.json`. Fields per message:
   `account`, `message_id`, `from_addr`, `subject`, `date`, `body_snippet`
   (up to ~3000 chars).
   - **Read it in batches with a script.** Print one compact line per message
     (index, account, sender, date, subject, first ~150 chars of body). Never
     read the raw file wholesale. Print longer bodies only for ambiguous ones.
   - **Classify each one:**
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
     - Be thread-aware across the batch. If a later message resolves an
       earlier one (form submitted, contract signed, invite superseded,
       meeting rescheduled), downgrade the earlier item and note the
       resolution.
     - Real people writing to Dan personally are at least `medium`.
     - Students or colleagues awaiting his reply are `high`.
     - Past-dated events and reminders are `none`.
     - Calendar invites that auto-add are `low`, unless the meeting is within
       ~24h or comes from an unknown sender needing an RSVP decision.
   - **Tip:** a script with an index → verdict dict, plus a sender regex for
     obvious marketing, scales to hundreds of messages. Have it fail loudly
     on any index you didn't cover.
4. **Ingest** — write `verdicts.json` as
   `{"verdicts": [{"account", "message_id", "importance", "reason", "suggested_action"}, …]}`.
   Take `account` and `message_id` verbatim from `pending.json`, joined by
   index. Never retype or truncate a message ID. Then run
   `uv run digest.py ingest-verdicts verdicts.json`. It must report
   `unknown 0`; otherwise fix the join and re-ingest.
5. **Render** — `uv run digest.py render`.
   - **What it does:** prints the digest, saves `digests/YYYY-MM-DD.md`, and
     regenerates the `## Email` checklist in today's Obsidian daily note. It
     prints `[daily note updated: …]`.
   - **What the checklist looks like:** grouped by priority, then account.
     Ticks are kept, and items Dan ticked on earlier days drop out.
   - **Re-running is safe** (the block is rewritten in place).
   - **Warnings go in the brief:** "vault not found" or "Obsidian CLI write
     failed; writing the file directly". The digest is valid either way.
   - **To inspect the note yourself, stay read-only and use the Obsidian
     CLI** (the app must be running):
     - `obsidian vault=vault daily:read`
     - `obsidian vault=vault tasks path="$(obsidian vault=vault daily:path)" todo total`
     - The CLI exits 0 even on errors, so check stdout for `Error:`.
     - Never create, move, delete or tick through it.
6. **Report an Inbox Brief** (below), drawn from the rendered digest.

## Inbox Brief format

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
  - Report counts honestly, including unclassified messages.
  - Flag stale "still open" items (past-dated, or resolved by later mail) so
    Dan can tick them.

## Coupling with claude-cowork

This skill depends on the repo's CLI (`scan`, `export-pending`,
`ingest-verdicts`, `render`), the `pending.json` / `verdicts.json` shapes,
the checklist markers, and `config.yaml`'s `obsidian` block. If any of those
change in claude-cowork, update this file in the same sitting; the repo's
`CLAUDE.md` says the same from its side.

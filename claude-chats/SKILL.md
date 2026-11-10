---
name: claude-chats
description: Use when Dan pastes a claude.ai share link (claude.ai/share/…) or a claude.ai chat URL (claude.ai/chat/…) in an Obsidian vault that mirrors his Claude chats (its CLAUDE.md says so), whether alone or with words like "capture this", "add this" or "mirror this"; when he asks to re-sync a chat already mirrored there; when he asks to sync a claude.ai project by name; and when he asks to process the chats a project sync brought in, such as going through his outfits.
---

# Claude Chats

## Overview

Dan's link is the whole request. Mirror that chat into the vault end to end, then reply
in a few lines. This skill's `scripts/claude_chats.py` fetches, archives and renders; the
rest of this file drives it and writes the parts that need judgment: the summary, the daily-note
links and the follow-ups.

**The link is the yes.** Pasting a share link or a chat URL is Dan's request to mirror
that chat, and mirroring means saving it, with its photos, from his own claude.ai account
into his own archive. That download *is* the request, not a step beyond it, so don't ask
before it: Dan decided this on 2026-11-01 ("i'd rather just give you a share link and you
process it in the vault entirely"). The yes covers that one chat and nothing else: not
other chats, and not a project's instructions or files.

Read the vault's `CLAUDE.md` paragraph on mirrored Claude chats once per session. Where it
and this skill differ, the vault wins.

Run every command from the vault root, with
`S=<this skill's base directory>/scripts/claude_chats.py` (for example
`~/.claude/skills/claude-chats/scripts/claude_chats.py`).

**A whole project, or processing what one brought in:** follow
[references/projects.md](references/projects.md).

## When not to use

- **The chat isn't Dan's:** the snippet says so (below). Stop, and offer
  `capture-conversation`, which captures someone else's share from the page text.
- **The vault has no `.claude/claude-chats.toml`:** use `capture-conversation`.

## Steps, for each link in turn

**1. Snippet.** From the vault root: `uv run "$S" snippet '<link>'`.
Exit 64 means it isn't a claude.ai share link or chat URL: say so and stop. Pass the
output on whole; never edit or retype it.

**2. Fetch, in the main session only.** Never hand the browser to a subagent.

- `tabs_context_mcp` (createIfEmpty), then `tabs_create_mcp` for a fresh tab. Never use
  one of Dan's tabs.
- `navigate` that tab to `https://claude.ai/robots.txt`, then `javascript_tool` with the
  snippet's output.
- Next link: a new tab. Chrome asks before a page starts a second automatic download.
- Close each tab only once step 3 has its file: a download Chrome is holding lives in
  that tab, and closing it loses the download.

| The snippet returns | Then |
|---|---|
| `saved`, `id`, `photos`, `photosMissing` | go on |
| `held: true` | stop for this link: "That chat matches a hold rule, so nothing was saved." Never guess at or repeat the title |
| `notYours`, or "this account can't open that share link" | stop: it isn't in Dan's account (see When not to use) |
| "not signed in to claude.ai" | ask Dan to sign in to claude.ai in Chrome, then run it again |
| "couldn't read the chat's project" | its project's hold rules couldn't be checked, so nothing was saved. Run it again in a new tab; if it fails twice, tell Dan |
| the tool call times out | don't run it again: the page keeps going and saves the file. Leave the tab open and go to step 3 |

**3. Ingest.** `uv run "$S" ingest --wait 90`.

- Exit 66 means the file never landed, so Chrome is asking: a Save dialog, or "download
  multiple files" (Allow). Its "Ask where to save each file" setting is meant to be off.
- Tell Dan that in one line and run the wait again after he answers.

**4. Render.** Dry run first: `uv run "$S" render`.

- **Before `--apply`:** if a new note's title suggests a student, a therapy subject or
  anyone Dan evaluates, stop. The vault's capture guard keeps that out of `sources/`, and
  the chat is still only in the archive, outside the vault. Tell Dan, and offer to add its
  ID to `exclude` in the archive's `config.toml`.
- **Otherwise** run `render --apply`, then act on its flags:

| Flag | Then |
|---|---|
| holds `<% … %>` text | that note isn't written, because Templater would run it. Say so and point to the vault's `TODO.md` item |
| ⚠ non-additive | the chat was edited on claude.ai. The note now follows the current branch, and the old one stays in the archive. Mention it |
| missing notes | Dan deleted that note. Never pass `--recreate`; mention it |
| project name unknown | the chat was archived before its project's name was. Syncing that project fixes it; tell Dan |
| summary may be out of date | the chat has grown: in step 5, add only what's new, with `--update` |
| couldn't be rendered | that chat's archived copy has something the renderer can't read (exit 1; the other chats are written). Report its ID and carry on |
| photos that can't be read | the note says "not downloaded" for it. Mention it |

Updates to other chats in the same render are fine; mention them in the reply.

**5. Summary.** `uv run "$S" summaries` lists the notes waiting for one.

- Read the whole note first: long chats change direction late.
- Write the summary to a temp file outside the vault, then run
  `uv run "$S" summary <id> --file <tmp>`.
- For a grown chat whose summary is already written, write only what's new and add
  `--update`. It goes under the summary as a dated `### Update`, and the summary itself
  stays as it is, in case Dan has edited it.

Match the shape of the summaries already in the vault's `sources/claude/`:

- **An opening paragraph:** what the chat was about, when Dan had it and how (by voice or
  text, with photos or not), and why it came up.
- **Where it landed:** the decisions or the plan, as bullets.
- **Considered and dropped:** each with why.
- **Still open:** unresolved questions and next steps.

Link existing vault notes on the same subject, and only ones that exist. Search for them
first, and never search under `private/`. Take facts from the chat alone and mark anything
inferred. Never write `<%`.

**6. Daily notes.** Read each note right before you edit it, because other sessions write
to these notes too.

- **The day or days Dan had the chat:** list them with
  `grep -oE '^### \[[0-9]{4}-[0-9]{2}-[0-9]{2}' <note> | sort -u`. Under `## Log` in each
  of those notes, add one line: `- [[<stem>]]: a Claude chat (by voice, if it was),
  HH:MM–HH:MM. <one-line gist>. Mirrored on <today>.`
- **Today's note:** under `## Log`, add the line `render --apply` printed (`- Synced
  Claude chats: …`) and where the follow-ups went.
- **Never** write inside the `<!-- ea-email:… -->` block, and never move or reflow lines
  that aren't yours.
- **If a day's note is missing,** create it from the vault's daily-note template for that
  date. If the template can't be used, put that day's link in today's line instead and
  say so.

**7. Follow-ups.** Each thing the chat leaves Dan to do goes into the vault's `TODO.md`,
in the matching section, as
`- [ ] **<action>** <detail> (from [[<stem>]]) *(added YYYY-MM-DD)*`.

- Add actions only, not every open question.
- One with a date, or with someone waiting on it, crosses Dan's YouTrack bar. Propose the
  ticket in the reply; don't file it.

**8. Commit what you wrote:** the notes, their photos in `ze-files/claude/`, any project
note, and your `TODO.md` lines.

- Other sessions may have uncommitted edits in the same files, so stage only yours. For a
  shared file, `git hash-object -w` a copy of `HEAD` plus your lines, then
  `git update-index --cacheinfo`.
- Leave daily notes that git doesn't track yet for the vault's next checkpoint.

**9. Reply,** a few lines per chat:

- `[[<stem>]]`, with a one-line gist, the number of messages and photos;
- the days it's linked from;
- what went to `TODO.md`, or "nothing";
- anything that stopped or was flagged.

## Re-syncing

Use the same steps for "re-sync <link>", or for a link to a chat that's already mirrored:

- **ingest says `unchanged`:** there's nothing to write, unless photos were missing last
  time.
- **The chat grew:** the transcript updates, and step 5 runs with `--update`.

## Common mistakes

| Mistake | Instead |
|---|---|
| Asking "save this file?" before fetching | The link is the yes (Overview) |
| Reading the code to work out the flow first | The steps above are the flow. `--help` lists the flags |
| Running the snippet again after a timeout | The page is still saving the file; go to step 3 |
| Two links fetched in one tab | A new tab for each link |
| Summarizing from the first screen of a long note | Read it all |
| Linking notes that might exist | Search first; link only what's there |
| Linking the chat only from today's note | Also link it from each day Dan had it |

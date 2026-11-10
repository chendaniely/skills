# Syncing a whole project, and processing what it brings in

Read this when Dan asks to sync a claude.ai project by name, or to process the chats a sync
brought in. Steps 4 to 9 of `SKILL.md` apply here except where this file says otherwise.

**A project is a capture point.** Dan talks to it on the road and rarely replies to an old
chat. A sync only stores. Processing is a separate, later step in the vault, when the skills
and his records are at hand.

## Sync a project

**Naming the project is the yes,** as a link is for one chat. It covers that project's chats,
their photos, its instructions and its file names, and only for a project listed in `allow`
in the archive's `config.toml`.

**1. Snippet.** `uv run scripts/claude_chats.py snippet --project '<name>'`.

If it refuses because the project isn't in `allow`, ask Dan, for that project: could chats
here discuss a student, a therapy subject, or anyone he is forming a judgment about? Add the
entry, with today's date as its `ack`, only on a clear no. Never open a chat before that.

**2. Fetch, in the main session only,** in a fresh tab on `https://claude.ai/robots.txt`.
Never use one of Dan's tabs, and never hand the browser to a subagent.

Run the snippet's output whole with `javascript_tool`. It starts a job in the page and
returns at once. Then call `await window.__claudeProject.wait()` until `state` is no longer
`running`. It returns counts only, never titles or text.

| `state` | Then |
|---|---|
| `saved` | go on. `held` counts chats a hold rule kept out; never try to find out which |
| `held` | the project's name matches a hold rule. Stop: "That project matches a hold rule, so nothing was saved." |
| `auth` | ask Dan to sign in to claude.ai in Chrome, then run it again |
| `failed` | report its error and stop |

`errors` lists chats that failed, by ID. They stay out of the file and the next run fetches
them, so mention how many and carry on.

**3. Ingest.** `uv run scripts/claude_chats.py ingest --wait 90`. Exit 66 means Chrome is
holding the file, as in `SKILL.md` step 3. Close the tab once ingest has it. Note whether
ingest says this is the project's first sync.

**4. If the job reported `more: true`,** the file reached its size limit. Repeat steps 2 and 3
in a new tab until it doesn't. Chats already archived are skipped.

**5. Render and summaries,** as in `SKILL.md` steps 4 and 5. A first sync can leave many notes
waiting. Subagents may read notes and write summary files, and must never touch the browser.

**6. Daily notes.** `uv run scripts/claude_chats.py daily` lists the links it would add, and
`daily --apply` writes them under `## Log` in the note for each day Dan had each chat. Then
add `render --apply`'s line to today's note, as in `SKILL.md` step 6.

**7. Follow-ups.** On a project's first sync, add none: they stay in each summary's **Still
open**, because many will be stale. On later syncs, follow `SKILL.md` step 7.

**8. Commit and reply,** as in `SKILL.md` steps 8 and 9. Add how many chats are waiting to be
processed.

## Process the queue

Only when Dan asks. Never start it on your own after a sync.

The vault's `CLAUDE.md` names where a project's photos and the notes made from its chats go.

**1. See what's waiting.** `uv run scripts/claude_chats.py queue --project '<name>'`. A chat
waits until it is stamped, and comes back if it gets a new reply.

**2. Take a few chats at a time.** Read each chat and its photos, and sort the photos into
outfits, single pieces or labels, and anything else. Show each with a small embed, its date
and its chat. If another person is in a photo, flag it and never describe them.

**3. Dan answers for each outfit photo:**

| Answer | Then |
|---|---|
| **Log it** | run `ootd` as usual, including its confirmation step, giving it the photo's path and the chat's date. Never pass `--replace-in` for a mirrored photo: the chat note keeps its copy |
| **Items only** | match and document the pieces as below, with no outfit note or score. Add a line to each item's `## Notes` saying which chat it was seen in |
| **Skip** | leave it |

A photo of a single piece or a label goes to `clothing-inventory`.

**4. Match pieces against the inventory folder alone.** It is the only authority on what Dan
owns.

- Show one table per batch. A piece seen in several photos gets one row, so he confirms it
  once.
- Write a match or a new item only after he confirms it. With no answer, write nothing.
- A new item starts thin: what the photos show and what the chat says. Leave its labels, size
  and listing blank, with open questions, as `clothing-inventory` requires. Never guess them.
- An item with no photo of its own gets a face-free crop, as `ootd` files one.

**5. Other notes.** Anything else a chat leads to goes in the folder the vault names for it,
with a link back to the chat.

**6. Stamp each chat when it's done,** including one with nothing to log:
`uv run scripts/claude_chats.py processed <id>`. If Dan stops partway, the rest stay waiting.

## Common mistakes

| Mistake | Instead |
|---|---|
| Starting to process right after a sync | A sync only stores. Wait for Dan |
| Writing a matched piece before he confirms it | With no answer, write nothing |
| Stamping a chat that's only partly done | Stamp it when every photo has its answer |
| Filling in a size or listing from a photo | Blank, with an open question |
| Adding a first sync's follow-ups to `TODO.md` | They stay in each summary |

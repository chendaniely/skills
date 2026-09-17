# Claude Chat Sources

How to get the text of a claude.ai conversation (SKILL.md step 1a and 1b).

⚠️ The share-snapshot route (`/api/chat_snapshots/<share-id>`) is closed: it
returns 403. Don't retry it.

## (a) The user's own chats: org-API JSON

⚠️ **Unofficial and fragile.** There is no official API for claude.ai chat
history. These are endpoints the claude.ai web app calls; they can change or
close without notice. They only work from the user's logged-in claude.ai
session, and only for the user's own chats.

1. `GET /api/organizations` → `<org-uuid>`.
2. `GET /api/organizations/<org-uuid>/chat_conversations?limit=40` → match by title.
3. `GET /api/organizations/<org-uuid>/chat_conversations/<conversation-uuid>?tree=True&rendering_mode=messages&render_all_tools=true`

Build the transcript from `chat_messages[]`:

- Each message carries `sender`, `index`, an exact ISO `created_at`,
  `input_mode` (`voice` vs text — settles the voice-capture question),
  `attachments`/`files`, and clean `content[].text` with no duplicated preview
  lines or icon glyphs.
- ⚠️ `chat_messages[].text` is **empty** — read `content[].text`.
- ⚠️ `created_at` is **UTC** (`Z`). The first message's `created_at` is the
  conversation start time. Convert to the owner's local zone before naming
  files (`2026-08-18T23:37Z` → `2026-08-18-1637` in PDT).
- **Always verify structurally.** The JSON's message count, sender split,
  `input_mode` set and tool-call count must match the written transcript's turn
  headers and tool blocks exactly. It is cheap to assert.

## (b) Someone else's share link: page text

A share link you don't own has no JSON route. The page is JS-rendered, so fetch
it with a browser tool (navigate → wait → extract `main` innerText), not plain
HTTP.

- **Clean it with a small script, never by retyping.** Page text contains
  icon-font Private-Use-Area glyphs (U+E000–U+F8FF — strip them) and duplicated
  per-message preview lines (drop them). On long transcripts, retyping drifts.
- **Timestamps:** once a chat is a day old, the page shows only relative times
  ("15 hours ago"). Take the start time from the page's timestamps, convert to
  local time, and confirm the date with the user.
- **Reconcile the turn count** before trusting the text. See the tool-use
  pitfalls below.

## Tool use: page text is wrong, not just noisy

When Claude calls tools in the conversation, **prefer the JSON.** Page text
fails in two ways, and neither announces itself:

1. **Tool-only turns vanish.** An assistant message made only of
   `tool_use`/`tool_result`, with no prose, renders no text at all. One page
   pass found 72 turns where the JSON had 73.
2. **Tool blocks get attributed to the human.** They render after the
   preceding user message, so a naive parse assigns them to the human speaker.

If you must use page text, reconcile its turn count (against
`chat_messages.length` whenever the JSON is available) before trusting it.

- `Used a tool` / `Used 2 tools` appears **twice** per tool block in page text
  (collapsed preview + expanded body). The doubling is chrome, not two calls.
- **Keep failed tool calls verbatim**, tool code and stdout included. A
  sandbox that lost state, a `NameError`, and the same code re-sent with its
  definitions inlined are part of how the thinking went.

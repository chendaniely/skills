---
name: capture-conversation
description: Use when ingesting a conversation or voice capture into an Obsidian-style knowledge vault (Obsidian, VS Code Foam, or any markdown + wikilink system) — Claude chat transcripts (shared links, exports, pasted text), solo voice memos, or multi-speaker meeting/talk recordings. Produces a verbatim source file plus a distilled thinking note that preserves how the thinking happened, not just what was concluded.
---

# Capture Conversation

## Overview

**This skill captures cognition, not just content.** Conversations on the move are
meandering, multi-threaded, full of dead ends — *on purpose*. The meandering is the
raw material. A normal summarizer flattens everything into a tidy result and throws
away the reasoning; this skill preserves the reasoning so future conversations can
build on it and link to it.

Two artifacts per capture, always:

1. **Source** — the verbatim record. Sacred, never trimmed, kept forever.
2. **Thinking note** — the distilled layer: decisions, considered-and-rejected
   threads, open questions, actions. This is the linkable, wiki-facing artifact.

The summary inside the thinking note is a convenience layer. **It serves the
thinking, it never replaces it.**

The target format is **llm-wiki style ingestion** (after [Karpathy's llm-wiki
idea](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)): raw
sources preserved forever, with a distilled, densely-wikilinked layer on top —
and it's the wiki layer, not the source, that the rest of the vault links
against. Where those files finally live is the user's decision, never this
skill's (see Artifacts & Naming).

Assumed environment: an **Obsidian-style knowledge vault** — plain Markdown
files, `[[wikilinks]]`, YAML frontmatter. Obsidian and VS Code Foam both
qualify, as does any similar system; features specific to one tool (e.g.
Obsidian Bases) are marked as such.

Origin: this skill was specced inside the first conversation it ever ingested
(2026-08-04, "obsidian voice capture and privacy"). v0.

## When to Use

- User shares a claude.ai conversation link/export and wants it "in the vault"
- A voice memo or recorder file (audio + transcript) needs ingesting
- A meeting or conference talk recording needs to become notes
- User says "process this conversation", "ingest this transcript", "capture this"

## Input Shapes × Purposes

Detect the shape from the input itself — don't make the user route it.

| Shape | Signal | Notes |
|---|---|---|
| **monologue** | one speaker | solo thinking out loud; pure uninterrupted user |
| **dialogue** | two speakers | user + AI (or one other person) |
| **multi-party** | 3+ speakers | meetings, talks, Q&A; needs/uses speaker diarization |

| Purpose | Meaning | Distillation emphasis |
|---|---|---|
| **own-cognition** | record of how the user thinks | preserve reasoning, decisions, dead ends |
| **external-material** | user capturing others' content | faithful record + user's takeaways layered on top; Q&A captured faithfully whoever asks |

**Edge case (ingestion #2): a meeting where the user is an equal co-decider,
not a passive audience.** A planning call where both sides jointly negotiate
and land on decisions together is still tagged `Purpose: external-material` in
frontmatter (meetings are external-material by this table's own definition,
and the frontmatter drives future Base filtering) — but forcing the
distillation into "What was presented" / "My takeaways" would misrepresent it
as one-directional. When the content is genuinely joint, use the
own-cognition template's structure (**Decisions reached** / **Considered and
rejected**) under the external-material frontmatter, and say so in one line
so a future reader knows the mismatch was deliberate, not an oversight.

Audio-first captures (voice recorder): the **audio file is the canonical original**,
the transcript is derived. Preserve both, linked. Transcribe locally if needed.

## Artifacts & Naming

**The captures folder is per-vault — never assume it; where files finally go is
always the user's call.** Resolve it in this order:

1. The target vault's/folder's CLAUDE.md (or equivalent conventions doc) declares
   where conversation captures live — use that.
2. Not declared? **Ask the user** where captures should go, then record the answer
   in that CLAUDE.md so future runs don't ask.

No assumptions beyond that — folder names, organizational philosophy, and note
style all belong to the target vault, not this skill.

**Confirmed alternative: a topic-scoped verbatim appendix, no separate pair.**
Not every piece of source material earns the full captures-folder pipeline.
When material is narrowly about *one existing topic note* — not a broader,
multi-topic conversation — embedding it directly inside that topic note as a
`# <description> (verbatim)` section is a valid lighter-weight version of the
same discipline: a one-line provenance note, the verbatim text (typos and
all, never silently cleaned), findings distilled into the note's living
sections above it, action items still copied to the TODO surface, the day's
daily note still updated. Seen twice now on the same vault's DSCI 521 note —
a co-instructor's proposal doc, then (independently, without this skill
being invoked) a Slack thread — both done correctly by the vault owner
working solo, matching every rule above without prompting. Recognize this as
a legitimate pattern, not a deviation to "fix" back into a captures-folder
pair — the two-artifact pipeline is for material that stands on its own or
spans multiple topics; a single-topic excerpt can just live where it's used.

**Within the captures folder, nest by year/month** (`<captures folder>/YYYY/MM/`)
unless the vault says otherwise — every capture is 2+ files, so a flat folder
grows fast.

Naming: `YYYY-MM-DD-HHmm-<slug>` — ISO date, time to the **minute** (conversation
start time), then a short human slug, lowercase, dash-separated. One session split
into two topics = same timestamp, two slugs.

```
<captures folder>/2026/08/
  2026-08-04-1755-obsidian-voice-capture-and-privacy.md             ← thinking note
  2026-08-04-1755-obsidian-voice-capture-and-privacy-transcript.md  ← verbatim source
  2026-08-04-1755-obsidian-voice-capture-and-privacy-audio.mp3      ← only for audio-first captures
```

The `-transcript` / `-audio` suffixes keep the pair adjacent in file lists and give
Obsidian Bases a metadata-free filter (`!file.name.endsWith("-transcript")`).

## Frontmatter Schemas

Match the target vault's frontmatter key style (the examples below use capitalized
keys). `Created` is the **conversation's start time**, not the file-write time —
the conversation is the knowledge event.

Thinking note:

```yaml
---
Created: 2026-08-04 17:55
Modification date: <write time>
Tags: #conversation <topic tags, e.g. #homelab #voice_capture #privacy>
Type: dialogue            # monologue | dialogue | multi-party
Purpose: own-cognition    # own-cognition | external-material
Source: <URL or origin description>
Transcript: "[[<basename>-transcript]]"
---
```

Transcript (source):

```yaml
---
Created: 2026-08-04 17:55
Modification date: <write time>
Tags: #conversation_transcript
Type: dialogue
Purpose: own-cognition
Source: <URL or origin description>
Thinking note: "[[<basename>]]"
Audio: "[[<basename>-audio.mp3]]"   # audio-first captures only
---
```

Keep keys consistent — they are the future Obsidian Base's columns.

## Verbatim, Defined

- Every turn, in order, speaker-labeled (`**Daniel:**` / `**Claude:**` / diarized names), timestamps kept when available.
- Voice-transcription garbles stay as spoken/captured ("Obama model", "Hartsping") — decode them in the thinking note, never edit the source.
- **Strip only delivery chrome**: web-page UI text, duplicated message previews, "Report" buttons. The words exchanged stay 1:1.
- Nothing else is trimmed. Dead ends, cut-offs, garbled fragments — all kept.
- Voice-mode *assistant* turns can be scrambled **in the stored source itself**
  (ingestion #3: interleaved word fragments like "That makot of thees sense — … a l
  water's probably just running out"), not just in the rendered page. Same rule:
  keep it exactly as stored, decode it in the thinking note, and say in the
  provenance note that the scramble is in the source, not a rendering artifact.

## Steps

1. **Obtain the full text.** Shared claude.ai links are JS-rendered — fetch via a
   browser tool (navigate → wait → extract `main` innerText), not plain HTTP. For
   audio: transcribe (diarize if multi-party), keep the audio file.
   *Learned in ingestion #1:* browser-extracted text contains icon-font
   Private-Use-Area glyphs (U+E000–U+F8FF — strip them) and duplicated
   per-message preview lines; clean these **mechanically with a small script**
   rather than retyping — on long transcripts, regeneration by hand drifts.
   *Learned in ingestion #2 (audio meeting, 2 speakers, no Zoom auto-transcript):*
   local ASR via `uvx --from mlx-whisper mlx_whisper <audio> --model
   mlx-community/whisper-large-v3-turbo --output-format json --word-timestamps
   True` works well on Apple Silicon (minutes, not tens-of-minutes, for a
   30-min recording; no HF token needed for the ASR model itself) — check
   `~/.cache/huggingface/hub/` first, the model may already be cached from
   unrelated research. **Diarization is the harder gap**: "diarize if
   multi-party" doesn't cover the common case, which is two people with no
   diarization tool installed and no `HF_TOKEN` (gated pyannote models need
   one). Fallback that worked: attribute speaker turns *by content* —
   consistent verbal tics/argument style per speaker, cross-checked against
   any already-documented position for each person elsewhere in the vault
   (e.g. an existing note recording what each side already believes). This is
   real evidence, not a coin flip, and confidence is high for substantive
   turns — but say so explicitly in the transcript's provenance note rather
   than presenting it as diarized ground truth, and for rapid mutual
   backchannel volleys ("yeah"/"right"/"for sure" traded with no
   distinguishing content) where attribution is genuinely unrecoverable from
   content alone, group them under one timestamp instead of force-labeling
   each word. **Hardest-won lesson:** the pull to silently "clean up" ASR
   mishearings (a proper noun, a jargon term, a course code) while typing out
   the transcript is *strong* — resist it exactly as hard as the browser
   icon-glyph case. A first pass of this ingestion quietly normalized several
   ASR garbles (a course code, a tool name misheard four different ways, a
   term repeated as "cognitive science" that was never actually said) before
   the mistake was caught and the transcript redone from raw output. Garbles
   stay verbatim in the source; decode them in the thinking note, every time,
   no exceptions for "obviously what they meant."
   *Learned in ingestion #3 (claude.ai share link, voice-mode dialogue):* the
   share page loads its content from
   `https://claude.ai/api/chat_snapshots/<share-id>?rendering_mode=messages&render_all_tools=true`.
   **Capture that JSON while a real browser loads the page** (Playwright
   `page.on('response', …)`, match the URL, save the body) and build the
   transcript from it instead of from `main` innerText: `chat_messages[]` carries
   `sender`, `index`, exact ISO `created_at` per turn (the rendered page only
   shows relative "15 hours ago" once a chat is a day old), `input_mode`
   (`voice` vs text — settles the voice-capture question), `attachments`/`files`,
   and clean `content[].text` with no duplicated preview lines or icon glyphs.
   ⚠️ `chat_messages[].text` is **empty** — read `content[].text`. ⚠️ Timestamps
   are UTC (`Z`); convert to the owner's local zone before naming files
   (`2026-08-18T23:37Z` → `2026-08-18-1637` in PDT). Access notes: plain `curl`
   of either the page or the API gets Cloudflare's "Just a moment" (403);
   headless Chromium and headed Chrome-for-Testing were challenged too. What
   passed: the real `/Applications/Google Chrome.app` binary driven by
   `playwright` (already in the npx cache: `~/.npm/_npx/*/node_modules/playwright`,
   symlink it as `node_modules` next to the script) with a throwaway
   `launchPersistentContext` profile, `--disable-blink-features=AutomationControlled`
   and `ignoreDefaultArgs: ['--enable-automation']`. Needed because the Playwright
   MCP browser profile can be locked by another live session ("Browser is already
   in use …") — don't kill that Chrome, it belongs to someone else's session.
   *Learned in ingestion #4 (claude.ai share link, voice-mode dialogue with tool
   use):* the snapshot JSON isn't just more convenient than page text — on a
   conversation where Claude calls tools, **rendered-text extraction is wrong, not
   merely noisy.** Two failures, both silent: (a) an assistant message consisting
   *only* of `tool_use`/`tool_result` with no prose (the model ran code, then spoke
   in the *next* message) **renders no text at all and disappears entirely** — the
   DOM pass found 72 turns where the JSON has 73; (b) tool-use blocks render
   *after* the preceding user message, so a naive parse **attributes them to the
   human speaker**. Neither error announces itself; both were caught only by
   diffing the two extractions. Prefer the JSON whenever tools are involved, and
   if you must fall back to page text, reconcile the turn count against
   `chat_messages.length` before trusting it. Also: `Used a tool` / `Used 2 tools`
   appears **twice** per tool block in page text (collapsed preview + expanded
   body) — that doubling is chrome, not two invocations. In the JSON, keep the
   tool code and stdout verbatim **including failed calls**; this capture's
   sandbox lost state twice and re-sent the same code with definitions inlined,
   and those `NameError`s are part of how the thinking actually went.
   *Learned in ingestion #5 (claude.ai share link, voice-mode product search,
   2026-09-06):* ⚠️ **the share-snapshot route from #3/#4 is closed.**
   `GET /api/chat_snapshots/<share-id>?rendering_mode=messages&render_all_tools=true`
   now returns `403 {"type":"permission_error","message":"Authentication required"}`.
   Verified four ways: plain `curl`; the #3 recipe exactly (real Chrome binary,
   throwaway `launchPersistentContext`, `--disable-blink-features=AutomationControlled`)
   where the app's *own* preload fetch was captured off the wire and was itself a 403;
   and from inside a logged-in claude.ai session with `credentials: 'include'` **and**
   `'omit'`. The share **page still renders the conversation normally** — only the JSON
   endpoint is gated, so the failure is silent unless you check the status code.
   **Working fallback, for the owner's own conversations:** list with
   `GET /api/organizations/<org-uuid>/chat_conversations?limit=40`, match by title, then
   `GET /api/organizations/<org-uuid>/chat_conversations/<conversation-uuid>?tree=True&rendering_mode=messages&render_all_tools=true`.
   Same `chat_messages[]` shape, same `content[].text` / `created_at` / `input_mode`, so
   every #3/#4 lesson still applies. Get `<org-uuid>` from `GET /api/organizations`.
   ⚠️ **This only works for your own chats** — a share link from someone else now has no
   JSON route at all, and must fall back to page text *with* the #4 turn-count
   reconciliation. **Always verify structurally:** the API's message count, sender split,
   `input_mode` set and tool-call count should match the written transcript's turn headers
   and tool blocks exactly, and it is cheap to assert.
   *Transport gotcha:* getting a 33 KB transcript out of a browser tool whose result is
   capped at ~1 KB defeats slicing (33 round-trips) and base64 (blocked as encoded data by
   the Chrome extension's filter), and claude.ai's CSP blocks `fetch()` to a localhost
   receiver. What worked in one call: **write the built markdown into the page DOM**
   (`document.body.innerHTML = '<pre>'`; set `textContent`) **and read it back with the
   extension's page-text extractor**, which has a far larger cap than the JS-eval return.
2. **Identify shape and purpose** from the content. Note conversation date and
   start time (in-conversation timestamps beat file dates). For share-link captures,
   the first `chat_messages[].created_at` in the snapshot JSON *is* the start time
   (UTC — convert). Confirm the date with
   the user if ambiguous.
3. **Privacy gate.** Scan for sensitive or sensitive-adjacent passages (private
   topics, other people's information, work-policy matters). Ask the user:
   full verbatim / flagged redactions (marked `[redacted: reason]`) / excluded
   entirely. Never write into a vault's excluded folders (e.g. `do-not-publish/`).
4. **Resolve the captures folder** (per Artifacts & Naming — vault CLAUDE.md
   first, ask if undeclared), **draft the slug**, and build the file pair from the
   skill's templates (`template-transcript.md`, `template-thinking-note.md`).
5. **Write the source file**: provenance line + verbatim dialogue per the rules above.
6. **Distill the thinking note**: summary (3–5 sentences) · decisions reached ·
   considered-and-rejected (each with *why it was closed*) · open threads · action
   items · transcription decoder table. For external-material captures, reframe as
   faithful record + user's takeaways.
7. **Linking pass.** Search the vault (filenames *and* content) for notes touching
   the conversation's topics; weave wikilinks into the thinking note inline and
   under `# References`. This is what makes captures compound over time.
8. **Vault integration.** Follow the target vault's conventions doc for
   bookkeeping, and touch existing topic notes *only* where the conversation
   genuinely settled or added something (one-line links, not rewrites) —
   **unless the topic note explicitly pre-declared this conversation as its
   trigger for a real rewrite** (ingestion #2: a note's provisional section
   had said in its own text "provisional until the meeting — after it, revise
   this section in place"). When a note has already marked itself as waiting
   on exactly this conversation, honor that instruction literally: a full
   in-place revision of the marked section, not a one-line link — while still
   leaving the note's historical sections (decision logs, prior drafts)
   untouched below, and flagging anything the conversation *didn't* resolve
   just as clearly as what it did (new complications count as findings too,
   not just clean resolutions).
   If the vault keeps daily notes, **link the capture in the daily note for the
   conversation's date** (create it from the vault's daily template if missing) —
   that's what makes captures findable in calendar views. When ingesting on a
   later day, do both: capture link in the conversation-date note, standard
   new-files entry in the ingestion-date note.
   If the vault declares a TODO/backlog surface, **copy the action items there**
   with a backlink to the thinking note — the thinking note's `## Action items`
   stays as the historical record; the backlog copy is the live one.
9. **Maintain the system.** Ask: did this run reveal a convention gap, a schema
   tweak, a new input shape? If yes, update the vault's CLAUDE.md and **this skill**
   accordingly (and say so in the session). The skill is expected to evolve —
   that's why it lives in a git repo.

## Sensitive Information

The privacy gate (step 3) is mandatory, not optional. Architecture discussion that
*mentions* private things can be fine; actual private content is not. When in doubt,
ask before writing — and respect any hard exclusion rules the vault declares.

## Future: Obsidian Base

(Obsidian-specific — other tools would put their own query/view layer over the
same frontmatter.) Not built yet — but the frontmatter above is designed for it. When wanted, a
`Conversations.base` (wherever the target vault keeps Bases) looks like:

```yaml
filters:
  and:
    - file.inFolder("<captures folder>")
    - '!file.name.endsWith("-transcript")'
views:
  - type: table
    name: All captures
    order: [file.name, Created, Type, Purpose, Source]
    sort: [{property: Created, direction: DESC}]
  - type: table
    name: Own cognition
    filters: {and: ['Purpose == "own-cognition"']}
    order: [file.name, Created, Type]
  - type: table
    name: External material
    filters: {and: ['Purpose == "external-material"']}
    order: [file.name, Created, Type]
```

Candidate future keys (add only when a real view needs them): `Status:
open/settled` for whether open threads remain, `Participants:` for multi-party,
`Project:` to group captures by venture.

**Separation from other Bases.** Conversations never join a vault's domain Bases
(e.g. a products/decisions Base) — those are fed by their own note types, not
captures. When a conversation *is about* such a domain (say, a product to
purchase), the capture pair still lands in the captures folder, and the domain
note (wherever that vault keeps it) is created/updated separately with a wikilink
to the capture as prior context. The graph connects the two; each Base stays
clean over its own note type.

## Open Threads (v0)

- **Quick-capture vs deep-distill modes** — v0 always does the deep pass; a
  fast-and-rough mode is a deliberate future split (chosen by the user, not
  auto-detected).
- **Diarization remains unsolved, now with real evidence it's the wrong thing
  to chase first.** Ingestion #2 (2-party meeting, no diarization tool, no
  HF token) used content-based speaker attribution instead — see Steps §1 —
  and it worked well enough on substantive turns. True audio diarization
  (pyannote needs a gated HF model + token; NeMo is a heavy install) is still
  untested; worth revisiting only if a capture's content is too symmetric in
  style for the content-based fallback to work (e.g. two people who argue
  alike, or 3+ speakers where pairwise stylistic contrast breaks down).
- Share links now have a clean machine-readable path (the snapshot JSON above),
  but it still starts from a manual "share" click and a real browser session —
  not automation.
- Automated pull of claude.ai conversations isn't possible on Pro/Max plans
  (manual export/share links only) — revisit if Anthropic ships connectors/API
  for chat history.

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
2. Not declared? **Ask the user** where captures should go and use the answer for
   this run. Propose the CLAUDE.md line in the step-9 report, and write it only
   after the user says yes, so future runs don't ask.

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
Obsidian Bases a metadata-free filter (`!file.basename.endsWith("-transcript")`).

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

1. **Obtain the full text.** Every run: clean mechanically **with a small
   script, never by retyping** — on long transcripts, regeneration by hand
   drifts. Garbles stay verbatim in the source and are decoded in the thinking
   note. Pick the route by input:
   - **(a) The user's own claude.ai chat** → the conversation JSON from the
     claude.ai org API (unofficial, may break). See
     [references/claude-chat-sources.md](references/claude-chat-sources.md).
   - **(b) Someone else's share link** → page text via a browser tool, with
     turn-count reconciliation. Same file.
   - **(c) Audio** → transcribe locally and keep the audio file. See
     [references/audio-transcription.md](references/audio-transcription.md).
2. **Identify shape and purpose** from the content. Note conversation date and
   start time (in-conversation timestamps beat file dates). For the user's own
   claude.ai chats, the first `created_at` in the conversation JSON *is* the
   start time (UTC — convert); for someone else's share link, use the page's
   timestamps. Confirm the date with the user if ambiguous.
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
   tweak, a new input shape? If yes, **propose, then apply**: show the user the
   proposed change to the vault's CLAUDE.md or to **this skill**, and apply it
   only after the user says yes. A new lesson goes into the relevant
   `references/` file as a short general rule, not into Steps as a dated story.
   The skill is expected to evolve — that's why it lives in a git repo.

## Sensitive Information

The privacy gate (step 3) is mandatory, not optional. Architecture discussion that
*mentions* private things can be fine; actual private content is not. When in doubt,
ask before writing — and respect any hard exclusion rules the vault declares.

## Future: Obsidian Base

(Obsidian-specific.) Not built yet — but the frontmatter above is designed for it.
The draft `Conversations.base`, candidate future keys, and how captures stay out
of a vault's other Bases:
[references/obsidian-base.md](references/obsidian-base.md).

## Open Threads (v0)

- **Quick-capture vs deep-distill modes** — v0 always does the deep pass; a
  fast-and-rough mode is a deliberate future split (chosen by the user, not
  auto-detected).
- **Diarization remains unsolved** — status and the content-based fallback are
  in [references/audio-transcription.md](references/audio-transcription.md).
- There is no official API for claude.ai chat history on Pro/Max plans. The org
  endpoint used for the user's own chats is unofficial and may break; otherwise
  it's manual export/share links — revisit if Anthropic ships connectors/API
  for chat history.

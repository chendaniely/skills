# Plaud: how `fetch` gets a session

`fetch` uses the Plaud CLI (`npm install -g @plaud-ai/cli`, then `plaud login`), not the
Plaud MCP server. The CLI writes straight to disk, so a transcript never passes through
the model, and it has its own login, separate from the MCP's.

## Share link → recording

The CLI can't look a share link up, so `fetch` goes through the recording's name:

1. The share page's `og:title` / `<title>` is the recording's name.
2. `plaud search -- "<name>"` lists candidate file IDs (a substring match).
3. `plaud file <id>` for each; keep the ones whose name matches exactly (case and
   whitespace aside).
4. Exactly one match, or stop. `plaud search` scans only the 500 most recent recordings:
   for an older one, pass `--file-id` (the ID is in `plaud search` / `plaud files` output).

A revoked share link serves a page with no recording name; `fetch` reports that.

## Dates

`plaud file` prints `start_at` in UTC without an offset (an 08:05 lecture in Vancouver
shows `15:05:29`). `fetch` converts it to local time; the folder date is the local date.

## Formats

**Transcript**: `plaud transcript --polished <id>` prints one utterance per line,
`[74:42 - 75:07] Speaker 2: text`, minutes running past 59. `fetch` rewrites each as
`01:14:42 Speaker 2`, a newline, the text, and a blank line between utterances: the same
bytes as the web app's TXT export, which the first folders were made from (all 10 matched
on 2026-09-24). `--polished` is Plaud's AI-cleaned version, which those exports were; the
raw one keeps every filler word. Any unrecognised line after the first utterance stops
`fetch`, so a format change can't slip through.

**Plaud's note**: `plaud summary <id>` minus the `Summary: <name>` line printed above it.
Copying the note from the web app loses everything inside `<…>` (`<commit_id>`,
`<<<<<<< HEAD`, sometimes several bullets at once); the CLI keeps it. It also keeps what
Plaud stores that the web app hides: `[](plaud://image…)` placeholders, HTML entities
such as `&gt;`.

## Availability

`plaud file` shows `transcript:` and `summary:` as `available` once processing is done.
Until then `fetch` writes `plaud.md` only and exits with code 2; run it again later.

## After upgrading the CLI

Its output is plain text, parsed with regular expressions in `class_notes.py`. After an
upgrade, check one or two existing sessions before trusting it:

```bash
python3 $S fetch --folder <session folder> --verify   # compares; writes nothing
```

`transcript-plaud.md` must come back `identical`.

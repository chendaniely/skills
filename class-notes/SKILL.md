---
name: class-notes
description: Use when Dan pastes a Plaud share link (web.plaud.ai/s/…) for a class session inside a course repository, or asks to add a lecture or lab from a recording, to regenerate class notes after the course prompt changed, to compare prompt variants or models on class notes, or to set up a new course repository for class notes. Fetches the transcript and Plaud's own note into a dated session folder, then generates notes with the course's prompt-notes.md.
---

# Class Notes

## Overview

A course repository holds what students see and edit: `prompt-notes.md` (the prompt and
nothing else: every word is sent), `README-prompt.md` (how it works and how to change it)
and one folder per class session. Everything else lives here, in one script — call it
through `python3`:

```bash
S=~/.claude/skills/class-notes/scripts/class_notes.py
python3 $S fetch <share link>      # Plaud -> session folder
python3 $S generate                # prompt x model -> notes
python3 $S payload --only <folder> # the exact message, for any other tool
python3 $S tidy --check            # notes whose Markdown won't render properly
```

Run it from the course repo (or pass `--repo`). `<command> --help` lists every option.

## Session folder

| File | Written by |
|---|---|
| `plaud.md` | `fetch`: the share link, as `<https://web.plaud.ai/s/…>` |
| `transcript-plaud.md` | `fetch`: Plaud's polished transcript |
| `notes-plaud.md` | `fetch`: Plaud's own AI note |
| `history.txt` / `history.R` | Dan, by hand (optional): shell or R command history |
| `terminal.txt` / `*console*.txt` | Dan, by hand (optional): terminal or R console capture |
| `notes-class-<variant>--<model>.md` | `generate`: one per prompt variant × the model that actually ran |

## Add a session from a share link

1. Go to the course repo root (`git rev-parse --show-toplevel`). No `prompt-notes.md`
   there means the course isn't set up: offer [Set up a course](#set-up-a-course).
2. `python3 $S fetch <url> [--suffix <lecture|lab|…>]`.
   - The folder is `<session parent>/<the lecture's local date>[-<suffix>]`. The date
     comes from Plaud's start time, not from today.
   - Follow the course's existing folder names: if they carry suffixes (`-lecture`,
     `-lab`), always pass `--suffix`, taking it from what Dan says ("the lab").
   - Prefer `--suffix` to `--folder`: with `--suffix` the date still comes from Plaud. Use
     `--folder <name or path>` only when Dan names a folder outright.
   - An existing folder without `plaud.md` (Dan often creates it in class, with the logs)
     is reused.
   - It stops without writing when the link matches no single recording, when the folder
     holds a different share link, or when that date already has suffixed folders. Relay
     the message and ask Dan for a suffix. Never choose a recording yourself: the Plaud
     account also holds recordings that are not classes.
   - Exit code 2 means Plaud hasn't finished processing. Tell Dan and stop. To finish
     later, run `python3 $S fetch --folder <that folder>`: it reads the link from
     `plaud.md`, so the original flags aren't needed.
3. `python3 $S generate --only <folder>` in the background (`main` × `opus`, a few
   minutes). Add `--prompt` or `--model` only when Dan asks.
4. Report each file written, and each notes file's name, line count and model. Suggest a
   commit message such as `2026-09-17 lecture: transcript, Plaud notes, class notes`.
   Don't commit or push.

## Regenerate and compare

`generate` runs prompt `main` (`prompt-notes.md`) with model `opus` unless told otherwise.
`--prompt` and `--model` each **replace** that default and can be repeated; every
combination runs.

| Situation | Command |
|---|---|
| Sessions with no notes yet | `generate` |
| The prompt was edited | `generate --force`, or `--force --only <folder>` for one session |
| A log was added to a session later | `generate --force --only <folder>` |
| A variant `prompt-notes-<name>.md` | `generate --prompt <name>`; `--prompt all` for every variant |
| Other models too | `--model opus --model sonnet`. Non-Claude names go to the local backend, a placeholder until the DGX Spark is reachable |
| Check first | `--dry-run` |
| Notes render as one run-on block | `tidy --check` lists them; `tidy` fixes them. `fetch` and `generate` already tidy what they write |

A plain run never overwrites: it lists stale notes (older prompt text, or fewer inputs
than the folder now holds) and suggests `--force`. Notes from an older model stay beside
the new ones, because the filename carries the model that ran.

## Set up a course

Follow [references/init.md](references/init.md). It writes `prompt-notes.md` and
`README-prompt.md` from the boilerplate in `templates/`, and adds the `templates/Makefile`
targets.

## Common mistakes

- **Pulling the transcript through the Plaud MCP and writing it out yourself.** Use
  `fetch`: it reproduces the web export byte for byte, and retyping is slow and lossy.
- **Naming the folder after today.** A recording processed days later belongs to the
  lecture's date, which `fetch` reads from Plaud.
- **Adding `--refetch` casually.** It replaces an existing transcript and Plaud note, which
  Dan may have edited (for example, to remove a name). Use it only when asked.
- **`generate --force` without `--only` for one new session.** That rebuilds every
  session of the term.

## References

- [references/plaud.md](references/plaud.md): how `fetch` resolves a link, the formats,
  failure modes, and checking after a Plaud CLI upgrade.
- [references/init.md](references/init.md): setting up a course repository.

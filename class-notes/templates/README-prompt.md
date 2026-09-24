<!--
  Boilerplate for a course repository's README-prompt.md (see references/init.md).
  Replace every {{…}} and delete this comment:
    {{SESSION_PARENT}}   where session folders live, e.g. `section_02/` or `lectures/`
    {{LOG_ROWS}}         one table row per command log the course captures
    {{LOG_EXAMPLE}}      one mis-heard command in quotes, e.g. "get add index star"
    {{EXAMPLE_SESSION}}  a real session folder, e.g. section_02/2026-09-15-lecture
    {{PRIVACY_WHERE}}    where the repo lives and why, or delete the sentence
-->
# The class notes prompt

> This is all AI/Claude generated

We are building one prompt together, all term, that turns a class transcript into notes.
You propose changes, we merge them, and **all** of the term's notes get regenerated from
the result — so an improvement you make in week 6 also improves the notes for week 1.

| File | What it is |
|---|---|
| [`prompt-notes.md`](prompt-notes.md) | **The prompt.** Every word of it is sent to the model, followed by a session's transcript and command logs. This is the file we edit together. |
| `prompt-notes-<name>.md` | Optional variants, for trying an idea next to the main prompt (see below). |
| `README-prompt.md` | This file: how it all works, and how to change it. |
| [`Makefile`](Makefile) | Shortcuts for running the generator. |

## What it produces

Each class session has a folder under {{SESSION_PARENT}}, named by date — with a suffix such
as `-lecture` or `-lab` when there were two classes that day:

| File | What it is |
|---|---|
| `plaud.md` | share link to the recording |
| `transcript-plaud.md` | the transcript: machine-generated, lightly cleaned up by Plaud ← input |
{{LOG_ROWS}}
| `notes-plaud.md` | Plaud's own AI notes — the baseline to beat |
| `notes-class-main--<model>.md` | what `prompt-notes.md` produced, and which model wrote it ← output |

Reading `notes-plaud.md` and `notes-class-main--<model>.md` side by side is the point.
Plaud's notes come from a generic summariser that has never heard of this course. Ours
know what the course is about, turn "due Saturday" into a real date, and keep the
questions people asked.

The command logs make a big difference. Speech is a bad way to record a command: a
microphone hears {{LOG_EXAMPLE}}, and the details disappear. When a session folder has a
command log, the prompt treats it as the authority on what was actually typed.

## How to propose a change

Ordinary Git and GitHub practice. From a terminal:

```bash
git switch -c prompt/your-change-here      # new branch
$EDITOR prompt-notes.md                    # make your edit
git add prompt-notes.md
git commit -m "Ask for a glossary of new commands"
git push -u origin prompt/your-change-here
```

Or on GitHub itself: open `prompt-notes.md`, click the pencil icon, make your edit, and
choose **Create a new branch for this commit and start a pull request**.

In the pull request, say **what problem the change fixes**. The convincing version is a
before/after on one session (see below), quoting the part that got better. A good change
fixes something you can point at — a section that comes out thin, a due date the notes got
wrong, a kind of content the notes keep dropping. "Make it better" is not something we
can evaluate.

To try a bigger idea next to the main prompt instead of in place of it, copy it to
`prompt-notes-<name>.md` (say `prompt-notes-glossary.md`). Its notes come out as
`notes-class-glossary--<model>.md`, beside the main ones, so the two can be compared.

## Running it yourself

The generator is `class_notes.py`, in the `class-notes/scripts/` folder of the public
[`chendaniely/skills`](https://github.com/chendaniely/skills) repository. It needs Python 3
and, for Claude models, the [Claude Code](https://claude.com/claude-code) CLI, logged in
once (`claude`, then `/login`). It runs on your Claude subscription: no API key is needed.

```bash
git clone https://github.com/chendaniely/skills ~/git/skills      # once
cn=~/git/skills/class-notes/scripts/class_notes.py

python3 $cn generate --dry-run                                     # what would run
python3 $cn generate --only {{EXAMPLE_SESSION}} --prompt glossary
python3 $cn generate --only {{EXAMPLE_SESSION}} --force --model sonnet
python3 $cn payload --only {{EXAMPLE_SESSION}} > message.txt
```

`payload` prints the exact message the model receives — the prompt, the transcript and the
logs — so you can take a session to any other tool or model and do your own thing with it.
The `Makefile` wraps the common runs (`make notes`, `make notes-force`); point it at your
copy with `CLASS_NOTES=~/git/skills/class-notes/scripts/class_notes.py`.

## The version history is the Git history

There is one prompt file, not `v1.md`, `v2.md`, `v3.md`: `git log -p prompt-notes.md`
shows every revision with its diff. Every generated notes file ends with a footer that
records where it came from:

```
---
prompt: prompt-notes.md @ a1b2c3d
prompt-hash: 3f9c0e2b7a41
model: claude-opus-5 (requested: opus)
backend: claude
inputs: transcript-plaud.md, history.txt
generated: 2026-09-14
```

`opus` is an **alias** meaning "the latest Opus", and what it points at changes over time;
`claude-opus-5` is the model that actually ran, which is why it is also in the filename.
When the alias moves to a newer model, regenerated notes land in a new file next to the
old one, so models can be compared too. `inputs` says whether the notes had the command
logs or only the transcript. `prompt-hash` is a fingerprint of the prompt's words, so a
commit that doesn't change them (a rename, a revert) never makes old notes look out of
date.

## A note on privacy

These transcripts include your voices{{PRIVACY_WHERE}}. Students appear in the transcript
as `Speaker 2`, `Speaker 4`, and so on. The prompt instructs the model to keep it that way
and never to attach a name to a question. If you change the prompt, keep that rule.

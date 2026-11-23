# Setting up a course repository

A course is set up when its repository root holds `prompt-notes.md` (the prompt, nothing
else), `README-prompt.md` (the student-facing docs) and a `Makefile` with the class-notes
targets. Session folders can come before or after.

## 1. Ask Dan

Ask once, together:

- Course code and title, and who the students are (program, level, prior experience).
- What the course covers, and what it deliberately doesn't.
- Where session folders live (`section_02/`, `lectures/`, …), if none exist yet.
- Which command logs he'll capture: shell history (`history.txt`) and terminal
  (`terminal.txt`), R history (`history.R`) and console (`R-console.txt`), or none.
- Whether students will propose prompt changes by pull request. The README's contribution
  section assumes they will; cut it if not.

If a transcript already exists, read it and draft the course description from it for Dan
to correct, rather than asking him to write one.

## 2. Write the files

- **`prompt-notes.md`** from `templates/prompt-notes.md`. Fill every `{{…}}`, delete the
  leading comment (the whole file is sent to the model), and swap the examples in the rules
  for the course's own tools: the noise fixes, the "write … as inline code" examples, the
  commands in the log rules.
  - No command logs: delete the two log bullets, the `## Commands from class` part of the
    output format, and the `## Rules for the command logs` section.
  - R logs: describe `<command-history>` as the R code that was run (no timestamps) and
    `<terminal-session>` as the console with its output. The generator only normalises
    `history.txt`; any other history file is sent as it is.
- **`README-prompt.md`** from `templates/README-prompt.md`. Fill every `{{…}}`, delete the
  leading comment, and make the session table match the log files the course uses.
- **`Makefile`** from `templates/Makefile`. If the repo already has one, add the targets
  and leave the existing ones alone.

## 3. Check

```bash
python3 $S generate --dry-run      # lists sessions, the prompt @ its revision and hash
python3 $S payload --only <a session folder> | head -5   # starts with the prompt's first line
```

## 4. Privacy

Transcripts carry students' voices, and a `plaud.md` link plays the class audio to anyone
who has it. If the repository is public, say so to Dan once; whether that's acceptable is
his call.

## 5. A public twin (optional)

A course can keep the course repo private and publish everything but the transcripts:
each session's `transcript-plaud.md` and `plaud.md` stay in its session folder, and every
other file (logs, `materials.md`, drawings, `notes-plaud.md`, every notes file) lives at
the same relative path in a public folder, usually inside a submodule of a public repo.

1. Add the public repo as a submodule, with its HTTPS URL so anyone can clone the course
   repo: `git submodule add -b main <https url> public/<repo name>`. On Dan's machine,
   set an SSH push URL inside it: `git -C public/<repo name> remote set-url --push origin
   <ssh url>`.
2. Refuse to push a pointer to a submodule commit that isn't on GitHub yet:
   `git config push.recurseSubmodules check`.
3. Name the public root in `class-notes.ini` at the repo root:

   ```ini
   [folders]
   public = public/<repo name>/<folder for the notes>
   ```

`fetch` then writes `notes-plaud.md` there, `generate` writes notes there, and the inputs
are read from there; `python3 $S where --only <folder>` prints a session's public folder.
A clone made without `--recurse-submodules` has an empty submodule, and the script stops
and says to run `git submodule update --init`.

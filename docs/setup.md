# Setup: shared preferences and the leak-check guard

`make setup` wires one shared `preferences.md` into Claude Code, pi and OpenCode, links the leak-check denylist, adds four deny rules to Claude Code's settings, and checks that a guard refuses commands that name the denylist. `make setup-check` reports what it would do and changes nothing. All of this is expected to move to its own repo later (issue #9); until then it lives here so it is written down and reproducible.

The script is `setup.sh` at the repo root. It is idempotent and add-only: it never removes or overwrites anything that isn't its own, and every step prints one line (`ok`, `added`, `linked`, `skipped: <why>` or `warn: <what to do>`). It finds the repo from its own location and uses `$HOME`, so it can be tried on a scratch directory with `HOME=<dir> bash setup.sh`. Its tests are in `plan-driven-development/tests/test_setup.py`:

```bash
uv run --quiet --with pytest pytest plan-driven-development/tests/test_setup.py -q
```

## The steps

1. **`claude-import`.** Appends a `# Shared preferences (all harnesses)` heading and an `@<repo>/preferences.md` line to `~/.claude/CLAUDE.md`, unless a line there is exactly that import. It creates the file if it is missing. If the repo's path contains a space, Claude Code's `@import` can't take it, so the step prints `warn` and adds nothing.
   - Undo: delete those two lines.
2. **`pi`.** Links `~/.pi/agent/AGENTS.md` to the repo's `preferences.md` when nothing is there. The right link prints `ok`. Anything else already at that path prints `skipped` and stays.
   - Undo: `rm ~/.pi/agent/AGENTS.md`.
3. **`opencode`.** This step is Dan's. The script only counts lines mentioning this repo's `preferences.md` path in OpenCode's `opencode.json` or `opencode.jsonc` (with `grep -c`; it never prints or edits them). A file it can't read counts as zero and gets a `warn` naming it. With no matching line, it prints a `warn` with the exact `instructions` entry to add by hand.
   - Undo: remove that entry from OpenCode's config.
4. **`denylist-link`.** The leak check reads its denylist from the `leakcheck` folder under `~/.config`. If that file is missing and the `local-ai` one exists, the step links the first to the second. It tests existence only and never reads either file. With no `local-ai` denylist it prints `warn`. A broken link already at the leak-check path prints `skipped` and stays.
   - Undo: remove the link (a symlink; the real file is untouched).
5. **`deny-rules`.** Adds four `Read(...)` rules to `permissions.deny` in `~/.claude/settings.json`: the `leakcheck` and `local-ai` denylist paths, each in the `~/` form and the `//<home>/` form. It keeps the existing order, inserts each new rule in sorted position, and creates `permissions.deny` if it is missing. It first copies the file to `settings.json.bak-<YYYYmmddHHMMSS>`, and only when something is added, so a second run makes no backup. It uses Python's standard library through `uv run --no-project`, so the script checks first, before any step, that `uv` is on `PATH` and stops with one line if not.
   - If `settings.json` is a symlink, the write goes through to the link's target: the link stays, the target gains the rules, and the backup lands next to the target. The write is atomic (a temp file in the same folder, then a rename), keeps non-ASCII text as it is, and uses two-space indentation and a trailing newline.
   - If the file is not valid JSON, or `permissions` or `permissions.deny` has the wrong type, the step prints `warn: <file> is not valid settings JSON; fix it and re-run`, writes nothing, and the remaining steps still run.
   - Undo: delete the four rules, or copy a backup back.
6. **`guard`.** Changes nothing, in both modes (`make setup` and `make setup-check` run it the same way). It reads the `PreToolUse` hooks in `settings.json` and runs only those whose matcher explicitly lists `Bash` (for example `Bash` or `Bash|Read`); hooks with no matcher or `*` are never run. Each such hook command gets two sample payloads on stdin, with `hook_event_name`, `tool_name: "Bash"`, a `tool_input.command`, `cwd` and `session_id: "setup-check"`: one command naming the denylist, and a harmless `ls`. It prints `ok` only if some hook refuses the first and none refuses the second (a hook that refuses everything is not a guard). A hook refuses with a `"deny"` decision on stdout or exit code 2. Each run has a 30-second timeout (`SETUP_HOOK_TIMEOUT` seconds overrides it for tests); on a timeout the hook's whole process group is killed, so a hanging hook cannot wedge setup. Otherwise the step prints `warn`.

## The guard

Dan's secrets guard is a `PreToolUse` hook kept in his private config repo and linked into `~/.claude/hooks/`. It refuses shell commands and file tools whose input mentions either config folder above, or the word `denylist` together with `.config`. It is a text-matching tripwire, one layer of several, not a sandbox. Its details and known limits are kept in the private, git-ignored `guards/` folder (see below), not in this public repo.

Nothing here replaces never reading the denylist: a session may test that it exists and use it only through the leak check.

## The git-ignored guard copies

`guards/` holds copies of the guard's hook, its tests, its reference settings, and the config repo's README and Makefile, so they are saved next to this setup. `.gitignore` excludes `/guards/`, so none of it reaches the public repo until Dan has reviewed it for security. Fill or refresh it with:

```bash
make sync-guards CLAUDE_CONFIG=<path to the private config repo>
```

`CLAUDE_CONFIG` has no default; the target stops with a message if it is not set. Never `git add` anything under `guards/`.

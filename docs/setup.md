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
3. **`opencode`.** Keeps a marked copy of `preferences.md` in OpenCode's global `~/.config/opencode/AGENTS.md`, because OpenCode reads that file. Measured 2026-10-16 (OpenCode 2.0.25, `opencode run`, model through the Spark): OpenCode ignores `instructions` entries, in `opencode.json`, in `opencode.jsonc` and in a project `opencode.json` (a canary file listed there never reached the model), while the global `AGENTS.md` and a project `AGENTS.md` both reach it. Its docs say `instructions` works; this is a measured difference, possibly limited to `opencode run`. Any `instructions` entry that points at `preferences.md` can therefore be removed. The script never reads or edits OpenCode's JSON config.
   - The block sits between two marker lines, each on its own line: `<!-- preferences.md: begin (managed by make setup in the skills repo; edit preferences.md there, not here) -->` and `<!-- preferences.md: end -->`. Between them is the exact text of `preferences.md`.
   - Missing file or block: the step creates the file (and its folder) if needed, appends a blank line and the block at the end, and prints `added`. A block that matches `preferences.md` prints `ok`. A block that differs has only the text between the markers replaced, and prints `updated`. Everything outside the markers is kept byte for byte.
   - Before any change, an existing file is copied to `AGENTS.md.bak-<YYYYmmddHHMMSS>` (with a `-<n>` suffix if that name is taken). A run that changes nothing makes no backup. After a change the step prints the unified diff of the block, so you can see what went in.
   - A begin marker without an end, two begins, or an end before its begin prints `warn` and changes nothing. `make setup-check` prints `ok`, or a `warn` saying the block is missing or stale, and changes nothing.
   - `SETUP_PREFERENCES=<file>` makes the step copy that file instead of `preferences.md`; it exists for the tests.
   - Undo: delete the block, markers included, from `~/.config/opencode/AGENTS.md`, or copy a backup back.
4. **`denylist-link`.** The leak check reads its denylist from the `leakcheck` folder under `~/.config`. If that file is missing and the `local-ai` one exists, the step links the first to the second. It tests existence only and never reads either file. With no `local-ai` denylist it prints `warn`. A broken link already at the leak-check path prints `skipped` and stays.
   - Undo: remove the link (a symlink; the real file is untouched).
5. **`deny-rules`.** Adds four `Read(...)` rules to `permissions.deny` in `~/.claude/settings.json`: the `leakcheck` and `local-ai` denylist paths, each in the `~/` form and the `//<home>/` form. It keeps the existing order, inserts each new rule in sorted position, and creates `permissions.deny` if it is missing. It first copies the file to `settings.json.bak-<YYYYmmddHHMMSS>`, and only when something is added, so a second run makes no backup. It uses Python's standard library through `uv run --no-project`, so the script checks first, before any step, that `uv` is on `PATH` and stops with one line if not.
   - If `settings.json` is a symlink, the write goes through to the link's target: the link stays, the target gains the rules, and the backup lands next to the target. The write is atomic (a temp file in the same folder, then a rename), keeps non-ASCII text as it is, and uses two-space indentation and a trailing newline.
   - If the file is not valid JSON, or `permissions` or `permissions.deny` has the wrong type, the step prints `warn: <file> is not valid settings JSON; fix it and re-run`, writes nothing, and the remaining steps still run.
   - Undo: delete the four rules, or copy a backup back.
6. **`guard`.** Changes nothing, in both modes (`make setup` and `make setup-check` run it the same way). It reads the `PreToolUse` hooks in `settings.json` and runs only those whose matcher explicitly lists `Bash` (for example `Bash` or `Bash|Read`); hooks with no matcher or `*` are never run. Each such hook command gets two sample payloads on stdin, with `hook_event_name`, `tool_name: "Bash"`, a `tool_input.command`, `cwd` and `session_id: "setup-check"`: one command naming the denylist, and a harmless `ls`. It prints `ok` only if some hook refuses the first and none refuses the second (a hook that refuses everything is not a guard). A hook refuses with a `"deny"` decision on stdout or exit code 2. Each run has a 30-second timeout (`SETUP_HOOK_TIMEOUT` seconds overrides it for tests); on a timeout the hook's whole process group is killed, so a hanging hook cannot wedge setup. Otherwise the step prints `warn`.

## Manual steps

`make setup` cannot make these changes, or can only check them. Do each one yourself; each says where it runs and how to tell it worked.

1. **Start a new Claude Code session.** A running session does not re-read `CLAUDE.md`, so the import added by step 1 reaches only sessions started afterwards.

   **On the Mac:** in an empty folder, run:

   ```bash
   claude -p --model haiku "Which of your instruction files says to list questions first and then ask them one at a time? Answer with the file's path only."
   ```

   It worked if the answer names `preferences.md`.
2. **OpenCode: read the first diff.** The first `make setup` appends the block to OpenCode's global `AGENTS.md` and prints its diff; read it then, since it is the one time the whole block shows as an addition. Later runs print a diff only when `preferences.md` changed.

   **On the Mac:** in an empty folder, run (with your own `<provider/model>`):

   ```bash
   opencode run --model <provider/model>#low "Without reading or searching any files: do your instructions say how to ask the user questions? Quote the first rule word for word."
   ```

   It worked if the answer quotes the first asking rule of `preferences.md`.
3. **pi.** Step 2 links its global `AGENTS.md`, and only a model run shows that pi follows the link.

   **On the Mac:** in an empty folder, run (with your own `<provider/model>`):

   ```bash
   pi -p --model <provider/model>:low "Which of your instruction files says to list questions first and then ask them one at a time? Answer with the file's path only."
   ```

   It worked if the answer names `preferences.md` or the global `AGENTS.md` that links to it.
4. **The denylist on a new machine.** Only you create it: one regular expression per line, never committed and never read by an agent. It goes in the `local-ai` folder under `~/.config`, in a file named `denylist`. `make setup` only links the leak-check path to that file once it exists (step 4); it never writes the file. It worked when `make setup-check` prints `denylist-link: ok`.
5. **The secrets guard.** It comes from your private config repo, whose own `make install` links it into `~/.claude/hooks/`; this repo cannot install it.

   **On the Mac:** in this repo, to refresh the git-ignored copy in `guards/`:

   ```bash
   make sync-guards CLAUDE_CONFIG=<path to the private config repo>
   ```

   It worked when `make setup-check` prints `guard: ok`, because that step runs the hook against a command naming the denylist and against a harmless one.
6. **The Spark, or any other machine.**

   **On the Spark:** clone this repo, create that machine's denylist as in item 4, then run:

   ```bash
   make setup
   ```

   It worked when `make setup-check` there prints `ok` on every line. Repeat the checks above for the harnesses installed on that machine.
7. **Hermes.** Not wired: its only global file, `SOUL.md`, is its identity, and its docs say preferences belong in its memory. Nothing to do.

There is no separate "How to undo" section in this file: each step above lists its own undo.

## The guard

Dan's secrets guard is a `PreToolUse` hook kept in his private config repo and linked into `~/.claude/hooks/`. It refuses shell commands and file tools whose input mentions either config folder above, or the word `denylist` together with `.config`. It is a text-matching tripwire, one layer of several, not a sandbox. Its details and known limits are kept in the private, git-ignored `guards/` folder (see below), not in this public repo.

Nothing here replaces never reading the denylist: a session may test that it exists and use it only through the leak check.

## The git-ignored guard copies

`guards/` holds copies of the guard's hook, its tests, its reference settings, and the config repo's README and Makefile, so they are saved next to this setup. `.gitignore` excludes `/guards/`, so none of it reaches the public repo until Dan has reviewed it for security. Fill or refresh it with:

```bash
make sync-guards CLAUDE_CONFIG=<path to the private config repo>
```

`CLAUDE_CONFIG` has no default; the target stops with a message if it is not set. Never `git add` anything under `guards/`.

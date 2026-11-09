# Setup: shared preferences and the leak-check guard

> **Moving:** these setup pieces (`preferences.md`, `setup.sh`, the `Makefile`'s setup targets,
> this page and the git-ignored `guards/`) will move to
> [chendaniely/agents](https://github.com/chendaniely/agents), the setup repo for Dan's agents,
> created 2026-10-16 (issue #9). This repo, `chendaniely/skills`, keeps the agent skills.

## Start here: a new machine, in order

Do these in this order; each points to its detailed step under [Manual steps](#manual-steps). Everything runs **on the machine you are setting up**, in its terminal.

**Prerequisites.** Install and check each of these first:

- `git` and `make` (macOS's own `make` 3.81 is fine).
- `uv` ([installation](https://docs.astral.sh/uv/getting-started/installation/)). `setup.sh` stops with one line if it is missing, before it changes anything.
- `gitleaks` 8.19 or newer, which the leak check uses.
- Each harness you want wired, installed and logged in once: Claude Code (`claude`), OpenCode (`opencode`) and pi (`pi`). Hermes needs nothing.

**The order:**

1. Clone this repo ([item 1](#manual-steps)).
2. Create the denylist ([item 2](#manual-steps)).
3. Install the secrets guard ([item 3](#manual-steps)).
4. Run `make setup`, and read the diff it prints for OpenCode ([item 4](#manual-steps)).
5. Check it with `make setup-check` ([item 5](#manual-steps)).
6. Start a new Claude Code session, and check Claude Code, OpenCode and pi each answer from `preferences.md` (items 6 to 8).

The Spark, or any other machine, takes the same list ([item 9](#manual-steps)).

`make setup` wires one shared `preferences.md` into Claude Code, pi and OpenCode, links the leak-check denylist, adds four deny rules to Claude Code's settings, and checks that a guard refuses commands that name the denylist. `make setup-check` reports what it would do and changes nothing. All of this moves to [chendaniely/agents](https://github.com/chendaniely/agents) later (issue #9); until then it lives here so it is written down and reproducible.

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
   - An `AGENTS.md` that is not UTF-8 text, or can't be read or written, prints `warn: ... left unchanged` with no backup and no write, and the remaining steps still run. So does a `preferences.md` that itself contains a marker line. A marker counts only when it is a whole line; the same text inside a sentence is ignored.
   - A newly created `AGENTS.md` gets the usual mode for your umask (0644 with the common 022);
     an existing file keeps its mode.
   - Undo: delete the block, markers included, from `~/.config/opencode/AGENTS.md`, or copy a backup back.
4. **`denylist-link`.** The leak check reads its denylist from the `leakcheck` folder under `~/.config`. If that file is missing and the `local-ai` one exists, the step links the first to the second. It tests existence only and never reads either file. With no `local-ai` denylist it prints `warn`. A broken link already at the leak-check path prints `skipped` and stays.
   - Undo: remove the link (a symlink; the real file is untouched).
5. **`deny-rules`.** Adds four `Read(...)` rules to `permissions.deny` in `~/.claude/settings.json`: the `leakcheck` and `local-ai` denylist paths, each in the `~/` form and the `//<home>/` form. It keeps the existing order, inserts each new rule in sorted position, and creates `permissions.deny` if it is missing. It first copies the file to `settings.json.bak-<YYYYmmddHHMMSS>`, and only when something is added, so a second run makes no backup. It uses Python's standard library through `uv run --no-project` (every embedded script runs with `python -I`, so nothing in the current folder can shadow a module), so the script checks first, before any step, that `uv` is on `PATH` and stops with one line if not.
   - If `settings.json` is a symlink, the write goes through to the link's target: the link stays, the target gains the rules, and the backup lands next to the target. The write is atomic (a temp file in the same folder, then a rename), keeps non-ASCII text as it is, and uses two-space indentation and a trailing newline.
   - If the file is not valid JSON, or `permissions` or `permissions.deny` has the wrong type, the step prints `warn: <file> is not valid settings JSON; fix it and re-run`, writes nothing, and the remaining steps still run.
   - Undo: delete the four rules, or copy a backup back.
6. **`guard`.** Changes nothing, in both modes (`make setup` and `make setup-check` run it the same way). It reads the `PreToolUse` hooks in `settings.json` and runs only those whose matcher explicitly lists `Bash` (for example `Bash` or `Bash|Read`); hooks with no matcher or `*` are never run. Each such hook command gets two sample payloads on stdin, with `hook_event_name`, `tool_name: "Bash"`, a `tool_input.command`, `cwd` and `session_id: "setup-check"`: one command naming the denylist, and a harmless `ls`. It prints `ok` only if some hook refuses the first and none refuses the second (a hook that refuses everything is not a guard). A hook refuses with a `"deny"` decision on stdout or exit code 2. Each run has a 30-second timeout (`SETUP_HOOK_TIMEOUT` seconds overrides it for tests); on a timeout the hook's whole process group is killed, so a hanging hook cannot wedge setup. Otherwise the step prints `warn`.

## Manual steps

`make setup` cannot make these changes, or can only check them. They are the detailed steps behind [Start here](#start-here-a-new-machine-in-order), in the same order. Each says where it runs, what to do and how to tell it worked. Commands are for you to run in your own terminal. Each step has its own undo where there is something to undo.

1. **Clone this repo.**

   **On the new machine:** pick a folder whose path has no space in it (Claude Code's `@import` can't take one), then run:

   ```bash
   git clone https://github.com/chendaniely/skills.git
   cd skills
   ```

   It worked if `ls setup.sh preferences.md` lists both files. Every later command in this file runs from this folder. To undo, delete the folder.
2. **Create the denylist.** This is the file of private terms the leak check refuses to let into a commit. Only you create it, and an agent never reads it. Its format is one regular expression per line, private terms only (names, addresses, internal hostnames, anything that must not be published), and it is never committed.

   If you also use the local-ai repo on this machine, its denylist is the master copy, and `make setup` links the standard leak-check path to it.

   **On the new machine:** create it in the `local-ai` folder under `~/.config`, then open it and add your terms:

   ```bash
   mkdir -p ~/.config/local-ai
   ${EDITOR:-nano} ~/.config/local-ai/denylist
   ```

   Without local-ai, create the file at the standard leak-check path yourself:

   ```bash
   mkdir -p ~/.config/leakcheck
   ${EDITOR:-nano} ~/.config/leakcheck/denylist
   ```

   Then run `make setup` again (item 4) if you already ran it, so step 4 of the script can link the path. It worked when `make setup-check` prints `denylist-link: ok`. To undo, delete the file you created (and the link, if there is one).
3. **Install the secrets guard.** The guard is a hook that refuses an agent's commands that name the denylist or other secret files. It comes from your private config repo, the one that holds your Claude Code hooks; this repo has only a git-ignored copy, and it cannot install the hook.

   **On the new machine:** clone or copy that private config repo here, then, from inside it, run its own installer, which links the hook into `~/.claude/hooks/`:

   ```bash
   make install
   ```

   Then, to refresh this repo's git-ignored copy in `guards/` (optional, for reference), run from this repo's folder:

   ```bash
   make sync-guards CLAUDE_CONFIG=~/path/to/your-config-repo
   ```

   It worked when `make setup-check` prints `guard: ok`: that step runs the hook against a command naming the denylist and against a harmless one. Until the guard is installed, `guard: warn` is expected. To undo, remove the link in `~/.claude/hooks/` and the hook entry in `~/.claude/settings.json`.
4. **Run `make setup`.**

   **On the new machine:** from this repo's folder, run:

   ```bash
   make setup
   ```

   On a first run, expect `claude-import: added`, `pi: linked`, `opencode: added`, `denylist-link: linked` (or `ok` if the link was already there) and `deny-rules: added 4`. After `opencode: added`, the script prints a unified diff of the block it appended to OpenCode's global `AGENTS.md`. Read it: it is the one time the whole block shows as an addition. Later runs print a diff only when `preferences.md` changed. To undo, use the undo line under each step above.
5. **Check it with `make setup-check`.**

   **On the new machine:** from this repo's folder, run:

   ```bash
   make setup-check
   ```

   When everything is in place, the output is exactly these six lines, in this order:

   ```text
   bash setup.sh --check
   claude-import: ok
   pi: ok
   opencode: ok
   denylist-link: ok
   deny-rules: ok
   guard: ok
   ```

   (The first line is `make` echoing the command it runs.) What can legitimately differ: on a first `make setup` run, `added` or `linked` instead of `ok`; before the guard is installed, `guard: warn: ...`; before the denylist exists, `denylist-link: warn: ...`; a `skipped: ...` when something of yours is already at the path, which is left alone.
6. **Claude Code: start a new session, then check.** A running session does not re-read `CLAUDE.md`, so the import reaches only sessions started afterwards.

   **On the new machine:** in an empty folder, run (`haiku` is only a cheap model alias; any model works):

   ```bash
   claude -p --model haiku "Which of your instruction files says to list questions first and then ask them one at a time? Answer with the file's path only."
   ```

   It worked if the answer names `preferences.md`.
7. **OpenCode: check.** First find a model id: `opencode models` lists them as `<provider>/<model>`. The `#low` suffix picks that model's low reasoning-effort variant, so the answer comes back quickly.

   **On the new machine:** in an empty folder, run, with your own model id (for example `spark/<model>#low`):

   ```bash
   opencode run --model spark/<model>#low "Without reading or searching any files: do your instructions say how to ask the user questions? Quote the first rule word for word."
   ```

   It worked if the answer quotes preferences.md's first asking rule: "**List first:** every question or step in the batch, one line each, with the count." (OpenCode ignores `instructions` entries in its JSON config, so only the block from item 4 can make it answer this.)
8. **pi: check.** Find a model id with `pi --list-models`. The `:low` suffix asks for a low reasoning-effort variant, so the answer comes back quickly.

   **On the new machine:** in an empty folder, run, with your own model id (for example `spark/<model>:low`):

   ```bash
   pi -p --model spark/<model>:low "Which of your instruction files says to list questions first and then ask them one at a time? Answer with the file's path only."
   ```

   It worked if the answer names `preferences.md` or the global `AGENTS.md` that links to it.
9. **The Spark, or any other machine.** Take the same order, on that machine.

   **On the Spark:** install `uv` first (`setup.sh` stops otherwise), then clone this repo as in item 1. The clone does not include `guards/`, because it is git-ignored, so install the guard from your private config repo on that machine too (item 3), or expect `guard: warn`. The Spark keeps its own denylist: create it there as in item 2, never by copying another machine's. Then run:

   ```bash
   make setup
   ```

   It worked when `make setup-check` there prints the six `ok` lines of item 5. Repeat items 6 to 8 for the harnesses installed on that machine.
10. **Hermes.** Not wired: its only global file, `SOUL.md`, is its identity, and its docs say preferences belong in its memory. Nothing to do.

## The guard

Dan's secrets guard is a `PreToolUse` hook kept in his private config repo and linked into `~/.claude/hooks/`. It refuses shell commands and file tools whose input mentions either config folder above, or the word `denylist` together with `.config`. It is a text-matching tripwire, one layer of several, not a sandbox. Its details and known limits are kept in the private, git-ignored `guards/` folder (see below), not in this public repo.

Nothing here replaces never reading the denylist: a session may test that it exists and use it only through the leak check.

## The git-ignored guard copies

`guards/` holds copies of the guard's hook, its tests, its reference settings, and the config repo's README and Makefile, so they are saved next to this setup. `.gitignore` excludes `/guards/`, so none of it reaches the public repo until Dan has reviewed it for security. Fill or refresh it with:

```bash
make sync-guards CLAUDE_CONFIG=<path to the private config repo>
```

`CLAUDE_CONFIG` has no default; the target stops with a message if it is not set. Never `git add` anything under `guards/`.

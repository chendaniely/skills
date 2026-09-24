# Skills repo

Dan's personal Claude Code skills, public on GitHub as `chendaniely/skills`. Each top-level folder is one skill. Open work lives in [TODO.md](TODO.md) and is mirrored as GitHub issues.

## Install and layout

- **Install:** `./install.sh` symlinks each `<skill>/` into `~/.claude/skills/<skill>`. Edits here apply live, even in running sessions. Re-run it after adding or renaming a skill.
  - It never touches entries in `~/.claude/skills` that aren't its own links, such as skill folders other tools installed there.
  - If a skill's name is already taken there by a folder or a different link, it prints `skipped` and leaves it.
  - It removes its own links whose skill folder no longer exists.
- **Keep skills flat at the top level** (decided 2026-09-16). Claude Code only discovers personal skills one level deep (`~/.claude/skills/<name>/SKILL.md`), so group folders wouldn't group anything, and a move breaks the paths listed below.
- **Marketplace (added 2026-09-23):** `.claude-plugin/marketplace.json` also publishes the skills as four plugins (`vault`, `wardrobe`, `teaching`, `running`) for `/plugin marketplace add chendaniely/skills`. A new or renamed skill must be listed there too.
  - Plugin installs prefix skill names (`/wardrobe:ootd`) and are cached copies, so edits apply only after a push and plugin update. Anything that loads a skill by bare name (like the `daily-email-digest` task) needs the symlink install.
  - Don't use both installs on one machine, or every skill loads twice.

## Paths other repos depend on

When a skill folder is renamed or moved, update all of these in the same sitting:

- **The Obsidian vault's `CLAUDE.md`:** it points, by this checkout's absolute path (print it with `git rev-parse --show-toplevel`, then search the vault's `CLAUDE.md` for it), to `product-search`, `clothing-inventory`, `ootd` and `capture-conversation`, and to the repo root.
  - Find the vault through Obsidian's vault list (`~/Library/Application Support/obsidian/obsidian.json`); it is the vault named `vault`.
  - A safety hook may block broad commands over the whole vault. Use narrow paths or the vault's own scripts (`scripts/lint.py`).
- **`~/git/private/claude-cowork`:** its `CLAUDE.md` and `README.md` point to `email-digest/SKILL.md` and say to commit skill changes here.
- **The `daily-email-digest` scheduled task** (`~/.claude/scheduled-tasks/daily-email-digest/SKILL.md`): it loads `email-digest` by name and cites its path here. It stops if the skill can't be loaded, so a rename ends the daily digest until the task is updated.
- **The symlinks:** re-run `./install.sh`.

## How the skills fit together

- **`email-digest`** is driven by the private `claude-cowork` repo. Its CLI subcommands, JSON shapes and checklist markers must match that repo, and claude-cowork's `CLAUDE.md` says the same from its side.
  - Changes usually come from a claude-cowork session, so check `git status` before touching this skill.
  - Unattended runs must start in claude-cowork, because only its machine-local settings pre-approve the digest commands.
- **`catch-up` and `email-digest` write the same daily note.** `digest.py render` puts its `## Email` checklist between `<!-- ea-email:begin todos … -->` and `<!-- ea-email:end todos -->`, right after `## Today`, and the begin marker comes before the `## Email` heading. `catch-up` ends its `## Today` rewrite at that marker and never touches lines inside the block. The vault's `CLAUDE.md` (## Conventions) requires the same.
- **`clothing-inventory`, `ootd` and `product-search`** refer to each other by name. `ootd` runs `clothing-inventory` as a required sub-skill, so rules that touch both (size, aliases, listing line, photos) must agree.
- **Vault skills** follow the vault's conventions, and the vault's `CLAUDE.md` wins.
  - `catch-up`, `capture-conversation` and `ootd` look up folder names in the vault's `CLAUDE.md`.
  - `clothing-inventory` hard-codes this vault's `inventory/` paths and defers to `inventory/Inventory.md`.
  - `email-digest` gets its vault settings from claude-cowork's config.
  - Frontmatter changes wait for the vault's Phase 10 migration (see TODO.md).
- **Inbox and transcripts:**
  - `catch-up` files `inbox/` notes, and `inbox/` is also where `ootd` looks for unlogged outfit photos.
  - Plaud transcripts reach the vault's `sources/transcripts/` through the vault's audio pipeline. `catch-up` never files them, and `capture-conversation` should link them instead of transcribing again (see TODO.md).
- **Standalone:** `capture-learning-moment` (writes to `$LEARNING_MOMENTS_DIR`, else `~/learning-moments/`) and `creating-ultra-crew-guides` don't use the vault.

## Editing a skill

- **Frontmatter:**
  - `name` equals the folder name.
  - `description` is at most 1024 characters and says what the skill does and when to use it.
  - Single-quote the description, doubling any internal apostrophes, if it contains `#` or `: `. An unquoted `#todo` once silently cut `catch-up`'s description short.
  - Check every skill at once. This fails loudly on a name/folder mismatch or an over-long description, and prints each file's line count for the 500-line limit:
    ```bash
    for f in */SKILL.md; do python3 -c "import yaml,re,sys; p=sys.argv[1]; t=open(p).read(); fm=yaml.safe_load(re.match(r'^---\n(.*?)\n---\n',t,re.S).group(1)); assert fm['name']==p.split('/')[0], p+': name != folder'; assert len(fm['description'])<=1024, p+': description too long'; print(fm['name'], len(fm['description']), t.count(chr(10)), 'lines')" "$f"; done
    ```
- **Length:** keep `SKILL.md` under 500 lines. Move detail that matters only sometimes into `references/`, one level deep and linked from `SKILL.md`. Record new lessons as short rules there, not as dated stories in the steps.
- **Side effects:** a skill that moves or rewrites files triggers only on an explicit request. `catch-up` runs only when asked. `ootd` offers first when it finds a photo mid-task.
- **Self-edits:** no skill edits the vault's `CLAUDE.md` or its own `SKILL.md` on its own initiative. It proposes the change and applies it after Dan says yes.
- **`grep` in Claude Code sessions** prints recursive paths without a leading `./`. Write path filters that accept both forms, for example `grep -vE '^(\./)?TODO\.md:'`.
- **Tests:**
  - **`ootd`** has the only regression test: `ootd/tests/prompt.md` (the prompt) and `ootd/tests/check_green.py` (the grader, with the fixture recipe in its header).
    - Re-run GREEN after any change to `ootd` or to `clothing-inventory`, which `ootd` runs as a sub-skill.
    - The fixture lives under `/tmp` and doesn't survive a reboot, so rebuild it from the recipe first.
    - Running the grader leaves `ootd/tests/__pycache__/`, which `.gitignore` covers.
  - **Other skills have no tests.** Re-read the diff against the rule it implements. For a description change, check that the trigger phrases still match how Dan asks.
  - **Install checks:** test `install.sh` without touching the real links by running `CLAUDE_SKILLS_DIR=<scratch dir> ./install.sh`. A skill is live when `ls -l ~/.claude/skills/` shows a link into this repo and the skill appears in a session's skill list.

## Public repo hygiene

- **Examples use invented or generic values.** Don't copy real names, sizes, measurements, addresses, IPs, hostnames or new local paths from the vault or the machine into skills, examples, commit messages or issues.
  - Two example values in `ootd`'s templates (the `## Direction` quote and the MUJI size) were reviewed on 2026-09-16 and kept on purpose. Don't replace them.
- **Security details stay private.** Don't publish which commands are pre-approved in other repos' settings.
- **Scan before pushing.** Check new content for secrets and personal details, including removed lines and commit messages: `git log -p origin/main..main`. History is permanent once pushed.
- **Commit identity:** commits use Dan's public email.

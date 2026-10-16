# plan-driven-development Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and test the `plan-driven-development` skill: its tools (the leak check, the
commit-message checker, four git hooks), its project templates (CI, the Makefile, the docs site),
its skill text, and a test harness that proves the skill changes how an agent works (RED without
it, GREEN with it), then release it.

**Architecture:** One skill folder, `plan-driven-development/`, at this repo's root: `SKILL.md`,
four references, `templates/` (copied into each project at kickoff), `scripts/` (two PEP 723
scripts the hooks run), and `tests/` (pytest for the deterministic parts, plus a harness that runs
headless agent sessions in throwaway repos and grades them). Plus `preferences.md` at the repo
root, wired into each harness's global instructions, and a `Makefile` at the repo root, this repo's
front door for its commands.

**Tech Stack:** Markdown; Python 3.11+ as PEP 723 scripts run with `uv run --script` (standard
library only); bash hooks (checked with shellcheck); GNU make (3.81 on macOS, 4.3 on Ubuntu
24.04); GitHub Actions YAML; Quarto 1.11.5; gitleaks 8.19+; pytest and PyYAML for tests only
(`uv run --with`); Claude Code 2.1.300 headless (`claude -p`) with superpowers 7.0.0 and Matt
Pocock's skills 1.3.1, OpenCode 2.0.25 and pi 1.2.0 for the test runs.

**Spec:** `docs/superpowers/specs/2026-10-15-plan-driven-development-design.md`

**Now:** Task 5: the session runners, open.

## Global Constraints

- **Public repo:** invented or generic values only; look-alike addresses and tokens are built from
  joined strings at run time; no new personal paths (a command that needs this checkout's path
  computes it with `git rev-parse --show-toplevel`); Dan's private secrets guard is described,
  never named.
- **The skill's shape:** folder and `name` `plan-driven-development`; `description` at most 1024
  characters, one short clause on what it is and then the triggers, never the workflow;
  `SKILL.md` under 500 lines (aim 200–300); references one level deep, each linked from
  `SKILL.md`.
- **Iron law (writing-skills):** `SKILL.md`, `templates/AGENTS.md` and the four references are
  written only after the RED runs (Task 6). Every other file is written test-first.
- **Full code in every step,** Dan's decision (spec Question 4): local models implement from this
  plan. It overrides superpowers 7.0.0's writing-plans, which now asks for "a code block only for
  an algorithm they do not determine".
- **Python through uv only.** From Task 3 on, the tests run through this repo's `Makefile`:
  `make test` runs `uv run --quiet --with pytest --with pyyaml pytest plan-driven-development/tests -q`,
  and `make test-utc` runs the same under `TZ=UTC`; both must pass.
- **Each task records its base first:** `git rev-parse HEAD > .git/PDD_BASE`. Its diff and its
  review run from `$(cat .git/PDD_BASE)`.
- **Secrets are never read**, the leak-check denylist included: tests use a fixture denylist through
  `LEAKCHECK_DENYLIST`; a check on the real one only runs the leak check, which prints nothing.
- **`$LOCAL_AI`:** local-ai's checkout, whose leak check (with Dan's denylist) scans this repo's
  pushes until Task 7 adds the skill's own. Before the first push of a session, in that shell:
  `export LOCAL_AI=<the path of Dan's local-ai checkout>`.
  Every push block that needs it refuses to run without it.
- **Commits** use this repo's style, `plan-driven-development: <description>`. Each message is
  written to `.git/PDD_MSG` and committed with `git commit -F .git/PDD_MSG`; it ends with one
  trailer paragraph: `Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Task N`
  and then `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`, with no blank line between.
  After each commit, `git log -1 --format='%(trailers)'` must show the `Plan:` line. Files are staged
  by explicit path; never `git add -A` or `.`; never `--no-verify`. Every commit is written out in
  full in its task.
- **This repo has no hooks,** so every push goes through the push block given in its task, which
  pushes only after the leak check, gitleaks and the binary check all pass.
- **Pushes:** the `plan-driven-development` branch only, under the standing OK Dan gives when he
  approves this plan; never `main`.
- **Reviews** follow the spec's tiers: Matt Pocock's `code-review` (two axes, two subagents) at
  Tiers 1 and 2, a self-review under its two headings at Tier 3; Tier 1 adds the security
  checklist (secrets, permissions, network exposure, failing closed, injection, logging); a
  re-review uses superpowers' `re-review-prompt.md` and looks only at the fix; at most one
  re-review; a Critical goes to Dan. Changes outside this repo are reviewed by Dan's yes on each
  diff plus the security checklist.
- **Each task ends with a closing commit,** `plan-driven-development: close Task N: <title>`, whose
  body has the lines `Drift:`, `Rulings:`, `Phase-end:`, `Forward:`, `Tier:`, `Rounds:` and
  `Findings:`, then the trailer paragraph. (The projects' commit-msg hook checks these; this repo
  has none, so the close step checks them with grep.)
- **Results files hold no paths:** before `tests/red-results.md` or `tests/green-results.md` is
  committed, `grep -nE '/(Users|home|private|var/folders)/' <file>` prints nothing.

## Notes from running the listings (2026-10-15)

Every listing below was run before it went in, twice over: when the plan was written, and again
after its independent review. 169 tests pass on the Mac (bash 3.2, gitleaks 8.30.1, uv 0.13.1,
Quarto 1.11.5, GNU make 3.81), in local time and under `TZ=UTC`; each task's tests fail without
its files and pass with them, as its steps say. What the runs settled:

- **The drill unstages with `git rm --cached`, not `git restore --staged`.** Kickoff's drill runs
  before the root commit, and `git restore --staged` fails in a repo with no commit ("could not
  resolve HEAD").
- **The commit-msg format checks live in `scripts/commitmsg.py`,** a second PEP 723 script copied
  into each project beside `leakcheck.py`.
- **The CI template pins Quarto 1.11.5,** the version the wrappers were tested on (released
  2026-09-17), and lychee-action v2.9.0 (2026-07-09) for the link check.
- **The Makefiles** (the project template and this repo's own) were run on the Mac's GNU make 3.81
  and in an `ubuntu:24.04` container on GNU make 4.3: `help`, the dry runs, and the targets that
  need no tools beyond make and git.
- **The push blocks** were run against a local bare remote, in bash and in zsh: a clean commit is
  pushed; a leak, an unscanned binary, or an unset `$LOCAL_AI` stops the push. (bash refuses an
  apostrophe inside `"${VAR:?…}"`; zsh doesn't, so the message has none.)
- **Isolation, checked with one cheap headless run:** under `--setting-sources project,local`, the
  start-up event's `skills` lists superpowers' and Matt's skills (loaded with `--plugin-dir` from
  where `installed_plugins.json` says they are) and Claude Code's built-ins, and none of the user's
  own skills; `--strict-mcp-config` with an empty config loads no MCP server; the canary prompt
  answered `none`. Headless sessions call their subagent tool `Task`.
- **Permission rules:** Claude Code's docs say a `*` may stand anywhere in a Bash rule
  (`Bash(* --version)`) and "An allow rule can't carve an exception out of a deny rule", so
  `Bash(* --no-verify*)` denies a `--no-verify` wherever it appears.
- **Upstream since the spec:** superpowers moved to 7.0.0 and Matt's skills to 1.3.1. The parts this
  plan relies on are unchanged except writing-plans (the full-code override above), brainstorming
  (its builder check is a small project's one pre-approval reviewer; its open-question style yields
  to Dan's asking rules, with one opening question allowed at kickoff), and Matt's `code-review`,
  which no longer names `docs/agents/issue-tracker.md` but still reads a tracker doc.

## Review Focus

Five failure modes the spec implies but no other test exercises, each pinned by a test in the task
that owns the code:

1. **A project folder whose path has a space** (`My Projects/demo`): every hook must still work.
   Test: `test_the_hooks_work_in_a_folder_whose_path_has_a_space` (Task 8).
2. **A commit message with Windows line endings** from another editor or harness: the trailers must
   still parse. Test: `test_a_message_with_windows_line_endings_still_parses` (Task 3).
3. **A renamed file:** the rename carries the whole file to its new name, which must be scanned.
   Test: `test_a_renamed_file_is_scanned` (Task 7).
4. **One push of two branches, one of them leaking:** the whole push must be refused. Test:
   `test_a_push_of_two_branches_is_refused_if_either_leaks` (Task 8).
5. **A file name outside ASCII** (`café-notes.md`): it must be read and scanned, not skipped. Test:
   `test_a_non_ascii_file_name_is_scanned` (Task 7).

***

### Task 1: `preferences.md`, its issue, the wiring and the denylist guard

> **Built differently** (closed 2026-10-16; commits 877faf9, a82575f; see the closing commit):
> - The wiring went as planned: issue #9; Claude Code's import; OpenCode's entry (Dan's edit); pi's
>   link; the denylist link. The deny rules went in as four, not two: Dan also asked for the
>   `//Users/...` twins his settings file uses, recorded too in his private config repo's reference
>   settings.
> - Dan's secrets guard lives in his private config repo (its hooks are linked into
>   `~/.claude/hooks/`), so the hook change was made and committed there. A background security
>   review then found the spelled-out pattern missed globs, `cd`, variables and `find`; with Dan's
>   OK the guard now refuses any mention of either config folder, and `denylist` together with
>   `.config` (88/88 tests). Shell commands that would carry such text write it to a file first.
> - Added at Dan's request: `setup.sh`, the root `Makefile` (help, install, setup, setup-check,
>   sync-guards), `docs/setup.md`, `plan-driven-development/tests/test_setup.py` (28 tests), and a
>   git-ignored `guards/` holding copies of the guard for his review (Task 1b in the ledger). Its
>   Tier 1 review found 3 Important items, fixed in one round; the script and its fix were combined
>   into one commit with Dan's OK, so wording about the guard's blind spots never reached the public
>   history.
> - 877faf9 is signed by the model that wrote it (Haiku), not the plan's Opus line.
> - **Follow-up, 2026-10-16 (Task 1c; commits e9da2f9, fd0c809, c43c59b):** OpenCode turned out
>   to ignore `instructions` entries (measured with canaries, in its global config files and in a
>   project one), while it reads `AGENTS.md` files; so, Dan's choice, `make setup` now keeps a
>   marked copy of `preferences.md` in OpenCode's global `AGENTS.md`, refreshed on every run; the
>   first real `make setup` (Dan's yes) added it, and OpenCode then quoted the first asking rule
>   word for word (checked with `spark/qwen3.6-35b-a3b`; the coder couldn't load for lack of free
>   memory on the Spark). At Dan's request `docs/setup.md` opens with "Start here: a
>   new machine, in order" and documents every step a script can't do. Its Tier 1 review found
>   a test-only override that could copy any file into OpenCode's instructions (removed), a crash
>   on non-UTF-8 text, stale wiring text and gaps in the docs; one fix round, one re-review
>   (14/14), and the cap's direct fix for new files' permissions (they honour the umask).

**Tier:** 1 (it changes Dan's global instructions and his secrets guard) · **Scenarios:** none
directly; the test sessions are isolated from this wiring (Task 5), so it can come before RED.

**Labels:** the agent writes the files and diffs; **[Dan]** steps are marked and say where they run.

**Files:**
- Create: `preferences.md` (this repo's root, no frontmatter)
- Modify: `TODO.md` (a new item under `## Later`; the mirrored-issue range in its intro)
- Outside the repo, each shown to Dan first: `~/.claude/CLAUDE.md` (one import line);
  OpenCode's global config (one `instructions` entry, Dan's edit); `~/.pi/agent/AGENTS.md` (a
  symlink); `~/.claude/settings.json` (two deny rules); Dan's own secrets guard and its test file
  (two protected paths); `~/.config/leakcheck/denylist` (a link, Dan's step)
  *(Corrected 2026-10-16: OpenCode 2.0.25 ignores `instructions` entries (measured); preferences.md reaches it through a block `make setup` keeps in its global `AGENTS.md`, Dan's choice.)*

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `preferences.md` at the repo root, read by every harness; issue #9; the denylist at
  `~/.config/leakcheck/denylist`, which `scripts/leakcheck.py` (Task 7) reads by default.

- [x] **Step 0: Record the base:** `git rev-parse HEAD > .git/PDD_BASE`.

- [x] **Step 1: Write `preferences.md`** with exactly this text:

```markdown
# Dan's standing preferences for coding agents

Read by Claude Code, OpenCode and pi in every project. A repo's own rules (its `AGENTS.md` or
`CLAUDE.md`) win where they differ. This file lives in Dan's public skills repo for now; issue #9
tracks moving it to a repo of agent global instructions with a setup script.

## Asking Dan things

1. **List first:** every question or step in the batch, one line each, with the count.
2. **Then one at a time,** showing "N of M" and how many remain; say so when M changes.
3. **Each question is a situation** ("Scenario: …. What do you expect?") with outcomes A, B and C,
   one of them recommended. One exception: a new project's kickoff may open with a single "describe
   it in your own words" question about what it is for; every decision after that uses this format.
4. **Review your own recommendation before asking:** against the evidence, Dan's stated goals, the
   answers already settled, and what could go wrong. Say briefly what you checked and what changed.
5. **Offer the options as selectable choices** where the harness has them (Claude Code's
   AskUserQuestion): the recommended option first, labelled "(Recommended)", with the short
   self-review in the message just before. Use text instead when the options need a lot of
   explanation, or the harness has no such tool.
6. **After each answer, show the list again** with progress, then the next.
7. **Record each answer** with Dan's reason in his words, where the project keeps its decisions, and
   commit it then: nothing relies on a tidy stop.

The same goes for steps Dan has to do himself: list them, then present one at a time, re-showing
the list after each.

## Commands

Every project has a `Makefile` as its front door, for agents and people alike: `make help` lists
the targets, and a command anyone runs more than once becomes a target. Keep it to GNU make 3.81
features, so it runs on macOS as well as Linux.

## Docs

Wrong docs are fixed in the change that made them wrong. Missing docs may wait for the phase end,
on its list. Diagrams never wait.

## Which skill for what

- superpowers for test-driven development, debugging, writing plans and running them;
- plan-driven-development's review tiers, with Matt Pocock's `code-review`, for reviews;
- Matt's `grilling` for interviews, asked by the rules above; his `writing-for-agents` when
  writing an `AGENTS.md`;
- the posit-dev Quarto skills (`quarto:quarto-authoring`) for Quarto sites;
- Matt's other skills (`tdd`, `diagnosing-bugs` and the rest) only when Dan types them.

## New projects

For a new project, use plan-driven-development.
```

- [x] **Step 2: Show Dan the issue text, then create it [Dan's OK].** Write the body to
  `.git/PDD_ISSUE.md`:

````markdown
Dan's standing preferences for coding agents live at this repo's root for now, in
`preferences.md`, wired into Claude Code with an `@` import, into OpenCode with an `instructions`
entry, and into pi with a symlink at its global `AGENTS.md`. Hermes is left out: its only global
file, `SOUL.md`, is its identity.

They belong in a separate repo of agent global instruction files, with a setup script that links
each harness's global file to them, the way steipete/agent-scripts does with its `sync-skills`
script.

When it moves: update the three wirings, this repo's `CLAUDE.md` and `README.md`, and the skills
that name `preferences.md` (`plan-driven-development`). Decided on 2026-10-15; see
`docs/superpowers/specs/2026-10-15-plan-driven-development-qa.md`, Question 17b.
````

*(Corrected 2026-10-16: OpenCode 2.0.25 ignores `instructions` entries (measured); preferences.md reaches it through a block `make setup` keeps in its global `AGENTS.md`, Dan's choice.)*

  Scan it first, with `$LOCAL_AI` set (Global Constraints):

```bash
: "${LOCAL_AI:?set LOCAL_AI to the local-ai checkout first, as Global Constraints says}"
uv run --frozen --project "$LOCAL_AI/spark" spark leakcheck --message .git/PDD_ISSUE.md; echo "issue text: exit=$?"
gitleaks stdin --redact --no-banner < .git/PDD_ISSUE.md
```

  Expected: `issue text: exit=0` and `no leaks found`; anything else is a stop: tell Dan. Show
  Dan the title and body; on his yes:

```bash
gh issue create -R chendaniely/skills --label enhancement \
  --title "preferences: move to a repo of agent global instructions with a setup script" \
  --body-file .git/PDD_ISSUE.md
```

  Expected: a URL ending in `/issues/9`. If the number differs, use the printed one in Step 3 and in
  `preferences.md`.

- [x] **Step 3: Add the TODO item.** In `TODO.md`, change the intro's range
  `([#1](https://github.com/chendaniely/skills/issues/1)–[#8](https://github.com/chendaniely/skills/issues/8))`
  to end at `[#9](https://github.com/chendaniely/skills/issues/9)`, and add under `## Later`:

```markdown
- [ ] **Move `preferences.md` to its own repo** (#9). Dan's standing preferences for coding agents
  live at this repo's root for now, wired into Claude Code (an `@` import), OpenCode (an
  `instructions` entry) and pi (a symlink at its global `AGENTS.md`). They belong in a separate repo
  of agent global instruction files with a setup script that links each harness's global file, as
  steipete/agent-scripts does with `sync-skills`. When it moves, update the three wirings, this
  repo's `CLAUDE.md` and `README.md`, and `plan-driven-development`'s mentions of it.
```

*(Corrected 2026-10-16: OpenCode 2.0.25 ignores `instructions` entries (measured); preferences.md reaches it through a block `make setup` keeps in its global `AGENTS.md`, Dan's choice.)*

- [x] **Step 4: Commit.** Write `.git/PDD_MSG`:

```text
plan-driven-development: add preferences.md, Dan's standing rules for every harness

The asking rules (list first, one at a time with counts, scenarios with
A/B/C, a self-review of each recommendation, selectable options where
the harness has them, answers recorded and committed), a Makefile as
every project's front door, docs kept true, which skill to use for
what, and "for a new project, use plan-driven-development". It lives
here for now; TODO.md and issue #9 track moving it to its own repo with
a setup script.

Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Task 1
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```bash
git add preferences.md TODO.md
git commit -F .git/PDD_MSG
git log -1 --format='%(trailers)'
```

  Expected: the trailers print `Plan: … Task 1` and the `Co-Authored-By:` line.

- [x] **Step 5: Wire Claude Code [Dan's yes on the diff].** Compute the line, show Dan the diff it
  makes to `~/.claude/CLAUDE.md`, and append it only on his yes:

```bash
line="@$(git rev-parse --show-toplevel)/preferences.md"
printf '\n# Shared preferences (all harnesses)\n\n%s\n' "$line"
```

  On yes, append exactly what was printed to the end of `~/.claude/CLAUDE.md` with the Edit tool.

- [x] **Step 6: Wire OpenCode [Dan, on the Mac].** The agent never reads OpenCode's global config
  (it can hold provider settings). Dan adds this entry to it, merging with any existing
  `instructions` array, where `<checkout>` is the path the Step 5 command printed after the `@`:

```json
"instructions": ["<checkout>/preferences.md"]
```

*(Corrected 2026-10-16: OpenCode 2.0.25 ignores `instructions` entries (measured); preferences.md reaches it through a block `make setup` keeps in its global `AGENTS.md`, Dan's choice.)*

- [x] **Step 7: Wire pi [Dan's yes].** pi has no includes, so its global `AGENTS.md` becomes a
  link. First check nothing is there:

```bash
test -e ~/.pi/agent/AGENTS.md && echo "something is already there: stop and ask Dan" || echo "free"
```

  If `free`, on Dan's yes:

```bash
ln -s "$(git rev-parse --show-toplevel)/preferences.md" ~/.pi/agent/AGENTS.md
ls -l ~/.pi/agent/AGENTS.md
```

- [x] **Step 8: The denylist link [Dan, on the Mac, and on the Spark for its own].** One denylist
  per machine serves every project. Dan runs, on the Mac:

```bash
mkdir -p ~/.config/leakcheck && ln -s ~/.config/local-ai/denylist ~/.config/leakcheck/denylist
```

  The agent then checks only that it exists: `test -f ~/.config/leakcheck/denylist && echo present`.
  Expected: `present`. (Task 7's leak check validates it without printing anything, and Task 8
  proves the hooks read it.)

- [x] **Step 9: Guard the denylist [Dan's yes on each diff].** Show Dan, then apply on his yes:
  1. In `~/.claude/settings.json`, `permissions.deny` gains
     `"Read(~/.config/local-ai/denylist)"` and `"Read(~/.config/leakcheck/denylist)"` (use the
     `update-config` skill, which shows the diff).
  2. In Dan's own secrets guard (the PreToolUse hook his global `CLAUDE.md` describes), the list of
     protected paths gains `.config/local-ai/denylist` and `.config/leakcheck/denylist`, so a shell
     command naming either is refused; its test file gains one refused case for each path and one
     allowed case for `uv run --script scripts/leakcheck.py --message /dev/null`. Run the guard's
     tests the way its test file says; all pass.

- [x] **Step 10: Review, look forward, close (Tier 1).**
  1. **Mechanical:** `git diff --stat "$(cat .git/PDD_BASE)"..HEAD` shows only `preferences.md`
     and `TODO.md`; the wiring shows in `tail -3 ~/.claude/CLAUDE.md`, `ls -l ~/.pi/agent/AGENTS.md`,
     and Dan's word for OpenCode.
  2. **Backward review:** `mattpocock-skills:code-review` from `$(cat .git/PDD_BASE)`, the spec
     being this task and the spec's *The asking rules*, *Overrides and steering* and *The shared
     preferences file* (two subagents); the changes outside the repo get Dan's yes on each diff plus
     the security checklist (secrets, permissions, network exposure, failing closed, injection,
     logging), recorded as a Ruling; each finding gets a severity and a decision; at most one
     re-review.
  3. **Forward review:** Tasks 2–16 consume `preferences.md` only through Task 2's check; nothing
     to rewrite unless the issue's number differed (then fix it in Task 15's README step).
  4. **Docs:** nothing in this repo's docs names `preferences.md` yet (Task 15 adds it).
  5. **Close:** tick Task 1's boxes, set **Now** to `Task 2: restart and check the wiring, open.`,
     and commit `plan-driven-development: close Task 1: preferences.md, the issue, the wiring and
     the denylist guard`:

  Write `.git/PDD_MSG`, filling each `<…>`:

```text
plan-driven-development: close Task 1: preferences.md, the issue, the wiring and the denylist guard

Drift: <how the build departed from this plan, and why; or "none">
Rulings: <each ruling: what was decided, why, what it costs if wrong; or "none">
Phase-end: <findings deferred to the phase-end list, with severity and file; or "none">
Forward: <later tasks the forward review changed, and how; or "none">
Tier: 1
Rounds: <the reviews and re-reviews run>
Findings: <Critical n, Important n, Minor n, and what became of each>

Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Task 1
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```bash
git add docs/superpowers/plans/2026-10-15-plan-driven-development.md
git commit -F .git/PDD_MSG
git log -1 --format='%(trailers)'
for h in Drift Rulings Phase-end Forward Tier Rounds Findings; do
  git log -1 --format=%B | grep -q "^$h: ." || echo "missing $h"
done
```

  Expected: the trailers print the `Plan:` line; no `missing` line.

- [x] **Step 11: Push (standing OK).**

  Until Task 7 the scan uses local-ai's leak check, which reads Dan's denylist without printing
  it; `$LOCAL_AI` is local-ai's checkout (Global Constraints). Push only through this block:

```bash
: "${LOCAL_AI:?set LOCAL_AI to the local-ai checkout first, as Global Constraints says}"
git fetch -q origin
range=origin/plan-driven-development..HEAD
f=$(mktemp)
git log -p --cc --format='%H%n%B' "$range" > "$f"
if uv run --frozen --project "$LOCAL_AI/spark" spark leakcheck --message "$f" &&
   gitleaks git --log-opts="$range" --redact --no-banner . &&
   git log --format= --numstat "$range" | awk '$1 == "-" { print "binary, check it by eye: " $3; bad = 1 } END { exit bad }'; then
  rm -f "$f"; git push origin plan-driven-development
else
  rm -f "$f"; echo "STOP: not pushed. Tell Dan each finding's kind and file:line (never the matched text), or the binary's name."
fi
```

  Expected: the leak check prints nothing, gitleaks prints `no leaks found`, then the push. A
  `STOP` line means nothing was pushed: a leak or an unscanned binary is a stop that never relaxes;
  tell Dan the kind and `file:line`, never the excerpt.

***

### Task 2: Restart and check the wiring

> **Built differently** (closed 2026-10-16): a fresh headless `claude -p` session stood in for
> restarting Claude Code (a ruling: a new session reads `CLAUDE.md` afresh, and a restart would end
> the run); it named `preferences.md`. OpenCode and pi wait on the Spark (Dan's choice): Task 14
> re-runs both.

**Tier:** 3 · **Scenarios:** none directly.

**Files:** none in the repo; the check's results go in the closing commit.

**Interfaces:**
- Consumes: Task 1's wiring.
- Produces: confirmation that each harness loads `preferences.md`.

- [x] **Step 0: Record the base:** `git rev-parse HEAD > .git/PDD_BASE`.

- [x] **Step 1: [Dan] Restart Claude Code** if it was running when Step 5 of Task 1 added the
  import (a running session doesn't re-read `CLAUDE.md`).

- [x] **Step 2: Check Claude Code.** In the new session, ask: "Which of your instruction files says
  to list questions first and then ask them one at a time?" Expected: it names `preferences.md`.

- [x] **Step 3: Check OpenCode and pi [Dan names the model; the Spark's model up for local ones].**
  The same question in `opencode run --model <model> "<question>"` and
  `pi -p --model <model> "<question>"`. Expected: each names the preferences. If the Spark's model
  is down, mark the step "waiting on the Spark" in the closing commit and carry on: Task 14
  re-checks it.

- [x] **Step 4: Close (Tier 3).** A self-review: each harness answered as expected, or the gap is
  recorded under `Phase-end:`. Tick the boxes, set **Now** to `Task 3: the commit-message checker,
  open.`, and commit `plan-driven-development: close Task 2: restart and check the wiring`:

  Write `.git/PDD_MSG`, filling each `<…>`:

```text
plan-driven-development: close Task 2: restart and check the wiring

Drift: <how the build departed from this plan, and why; or "none">
Rulings: <each ruling: what was decided, why, what it costs if wrong; or "none">
Phase-end: <findings deferred to the phase-end list, with severity and file; or "none">
Forward: <later tasks the forward review changed, and how; or "none">
Tier: 3
Rounds: <the reviews and re-reviews run>
Findings: <Critical n, Important n, Minor n, and what became of each>

Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Task 2
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```bash
git add docs/superpowers/plans/2026-10-15-plan-driven-development.md
git commit -F .git/PDD_MSG
git log -1 --format='%(trailers)'
for h in Drift Rulings Phase-end Forward Tier Rounds Findings; do
  git log -1 --format=%B | grep -q "^$h: ." || echo "missing $h"
done
```

  Expected: the trailers print the `Plan:` line; no `missing` line.

***

### Task 3: The commit-message checker, the test helpers and this repo's `Makefile`

> **Built differently** (closed 2026-10-16; commits 3323829, 4990016): the root `Makefile` was
> modified, not created (Task 1's forward note); `make test` counts 46, with Task 1's 28 setup
> tests; one placeholder-free f-string became a plain string. The review's one Important finding,
> `CLAUDE.md` still saying `ootd` had the only tests, was fixed in this task (4990016), which also
> points `CLAUDE.md` at `make check-skills` instead of its own copy of the loop.

> **Forward review, Task 1 (2026-10-16):** the root `Makefile` already exists (Task 1 added `help`,
> `install`, `setup`, `setup-check` and `sync-guards`). This task **modifies** it instead of creating
> it: add `test`, `test-utc` and `check-skills`, keep the existing targets and `help`'s format, and
> extend this task's `make help` test to expect all eight targets. `install` is already there.

**Tier:** 2 · **Scenarios:** S08's format checks; the front door every later task's tests run
through.

**Files:**
- Create: `plan-driven-development/scripts/commitmsg.py`
- Create: `plan-driven-development/tests/helpers.py`
- Create: `Makefile` (this repo's root)
- Test: `plan-driven-development/tests/test_commitmsg.py`, `plan-driven-development/tests/test_repo_makefile.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces:
  - `commitmsg.problems(message: str) -> list[str]`, `commitmsg.main(argv) -> int`, and the regexes
    `SUBJECT`, `ROBOT`, `CLOSE`, `WIP` (used by the commit-msg hook in Task 8 and the graders in
    Task 4);
  - `helpers.load_script(name)`, `ip()`, `mac()`, `ipv6()`, `token()`, `denylist(dir, *terms)`,
    `git(repo, *args, hooks=False, check=True, env=None, input=None)`, `git_repo(tmp_path)`,
    `make_project(tmp_path)` (copies `templates/githooks` and both scripts; used from Task 8 on),
    `gitleaks_has_git()`, and the paths `SKILL`, `TEMPLATES`, `SCRIPTS`;
  - the `Makefile` targets `help` (the default), `test`, `test-utc`, `check-skills`, `install`.

- [x] **Step 0: Record the base:** `git rev-parse HEAD > .git/PDD_BASE`.

- [x] **Step 1: Write the failing tests.** `plan-driven-development/tests/test_commitmsg.py`:

```python
"""scripts/commitmsg.py: the commit-message format checks the commit-msg hook runs (S08)."""

import pytest

from helpers import load_script

commitmsg = load_script("commitmsg")

PLAN = "Plan: docs/superpowers/plans/2026-01-01-demo.md Task 3"
COAUTHOR = "Co-Authored-By: An Agent <agent@example.invalid>"
CLOSE_BODY = "\n".join(
    f"{h}: none." for h in ("Drift", "Rulings", "Phase-end", "Forward", "Tier", "Rounds", "Findings")
)


@pytest.mark.parametrize(
    "message, reason",
    [
        (f"docs(plan): 🤖 x\n\nBody.\n\n{PLAN}\n\n{COAUTHOR}\n", "isn't parsed as a trailer"),
        (f"docs(plan): 🤖 x\n\nBody.\n{PLAN}\n{COAUTHOR}\n", "isn't parsed as a trailer"),
        (f"Update stuff\n\nBody.\n\n{COAUTHOR}\n", "isn't Conventional Commits"),
        (f"docs(plan): x\n\nBody.\n\n{PLAN}\n{COAUTHOR}\n", "needs 🤖"),
        (f"docs(plan): 🤖 close Task 3: parse\n\nDrift: none.\n\n{PLAN}\n{COAUTHOR}\n", "'Rulings: …'"),
        (f"chore(plan): 🤖 wip Task 3: parse\n\nDone so far: x.\n\n{PLAN}\n{COAUTHOR}\n", "'Stopped at: …'"),
        (f"Merge branch 'main' into phase-1\n", "isn't Conventional Commits"),
    ],
    ids=["blank-before-coauthor", "prose-in-trailers", "not-conventional", "plan-without-robot",
         "close-missing-heading", "wip-missing-part", "git-default-merge"],
)
def test_the_format_checks_refuse(tmp_path, message, reason):
    path = tmp_path / "msg"
    path.write_text(message)
    assert commitmsg.main([str(path)]) == 1
    assert any(reason in p for p in commitmsg.problems(message)), commitmsg.problems(message)


@pytest.mark.parametrize(
    "message",
    [
        f"feat(cli): 🤖 add --dry-run\n\nWhy.\n\n{PLAN}\n{COAUTHOR}\n",
        f"docs(plan): 🤖 close Task 3: parse\n\n{CLOSE_BODY}\n\n{PLAN}\n{COAUTHOR}\n",
        "chore(plan): 🤖 wip Task 3: parse\n\nDone so far: a.\nStopped at: b.\nTests: green.\n\n"
        f"{PLAN}\n{COAUTHOR}\n",
        "chore(repo): 🤖 merge main into phase-2\n\nTakes in main.\n",
        "fix: handle an empty file\n",
        "feat!: drop the old flag\n\n---\n\nA divider line.\n",
    ],
    ids=["build", "close", "wip", "merge-main", "human-no-scope", "breaking-with-divider"],
)
def test_the_format_checks_accept(tmp_path, message):
    path = tmp_path / "msg"
    path.write_text(message)
    assert commitmsg.main([str(path)]) == 0, commitmsg.problems(message)


def test_a_message_with_windows_line_endings_still_parses(tmp_path):
    # Review Focus 2: a CRLF message from another editor or harness.
    message = f"feat(cli): 🤖 add --dry-run\r\n\r\nWhy.\r\n\r\n{PLAN}\r\n{COAUTHOR}\r\n"
    path = tmp_path / "msg"
    path.write_bytes(message.encode())
    assert commitmsg.main([str(path)]) == 0, commitmsg.problems(message)
```

  `plan-driven-development/tests/test_repo_makefile.py`:

```python
"""This repo's own Makefile: the front door for its commands (Dan, 2026-10-15)."""

import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAKEFILE = ROOT / "Makefile"


def make(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["make", "-f", str(MAKEFILE), *args], cwd=cwd, capture_output=True, text=True)


def test_make_alone_lists_every_target():
    out = make().stdout
    for target in ("help", "test", "test-utc", "check-skills", "install"):
        assert re.search(rf"^  {re.escape(target)} ", out, re.MULTILINE), (target, out)


def test_test_and_test_utc_run_the_skills_tests():
    command = "uv run --quiet --with pytest --with pyyaml pytest plan-driven-development/tests -q"
    assert make("-n", "test").stdout.splitlines() == [command]
    assert make("-n", "test-utc").stdout.splitlines() == [f"TZ=UTC {command}"]


def test_check_skills_passes_a_good_skill_and_fails_a_misnamed_one(tmp_path):
    for name, folder in (("good", "good"), ("other", "misnamed")):
        (tmp_path / folder).mkdir()
        (tmp_path / folder / "SKILL.md").write_text(f"---\nname: {name}\ndescription: Use when testing.\n---\n\n# {name}\n")
    shutil.copy2(MAKEFILE, tmp_path / "Makefile")
    (tmp_path / "misnamed" / "SKILL.md").unlink()
    good = subprocess.run(["make", "check-skills"], cwd=tmp_path, capture_output=True, text=True)
    assert good.returncode == 0 and "good" in good.stdout, good.stdout + good.stderr
    (tmp_path / "misnamed" / "SKILL.md").write_text("---\nname: other\ndescription: Use when testing.\n---\n")
    bad = subprocess.run(["make", "check-skills"], cwd=tmp_path, capture_output=True, text=True)
    assert bad.returncode != 0 and "name != folder" in bad.stderr


def test_install_runs_the_install_script():
    assert make("-n", "install").stdout.splitlines() == ["./install.sh"]
```

  And the shared `plan-driven-development/tests/helpers.py`:

```python
"""Shared by the skill's tests. Look-alike values are built at run time, so no file in this public
repo ever holds a literal private address, MAC or token, and no scanner trips on the tests."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
TEMPLATES = SKILL / "templates"
SCRIPTS = SKILL / "scripts"


def load_script(name: str):
    """Import one of the skill's PEP 723 scripts as a module."""
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def ip(*parts: int) -> str:
    return ".".join(str(p) for p in parts)


def mac(*parts: str) -> str:
    return ":".join(parts)


def ipv6(*groups: str) -> str:
    return ":".join(groups)


def token() -> str:
    """A token in the shape gitleaks' default github-pat rule flags: ghp_ and 36 characters."""
    return "ghp" + "_" + "aB3dE6gH9jK2mN5pQ8sT1vW4yZ7bC0eF3hJ6"


def denylist(directory: Path, *terms: str) -> Path:
    """A fixture denylist of invented terms; the real one is never read."""
    path = directory / "denylist"
    path.write_text("".join(f"{term}\n" for term in terms or ("secret-project",)))
    return path


GIT_ID = ["-c", "commit.gpgsign=false", "-c", "user.name=t", "-c", "user.email=t@example.invalid"]


def git(repo: Path, *args: str, hooks: bool = False, check: bool = True, env=None, input=None):
    """git in `repo`, never signing; without the repo's hooks unless `hooks` is set."""
    pre = [] if hooks else ["-c", f"core.hooksPath={repo.parent / 'no-hooks'}"]
    (repo.parent / "no-hooks").mkdir(exist_ok=True)
    return subprocess.run(
        ["git", *pre, *GIT_ID, *args],
        cwd=repo, check=check, capture_output=True, text=True, env=env, input=input,
    )


def git_repo(tmp_path: Path, name: str = "repo") -> Path:
    repo = tmp_path / name
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    return repo


def make_project(tmp_path: Path) -> Path:
    """A project as kickoff leaves it: the hooks, gitleaks.toml and the scripts copied in, and the
    hooks turned on. No commit yet."""
    repo = git_repo(tmp_path)
    shutil.copytree(TEMPLATES / "githooks", repo / ".githooks")
    for hook in (repo / ".githooks").iterdir():
        if hook.suffix != ".toml":
            hook.chmod(0o755)
    (repo / "scripts").mkdir()
    for script in ("leakcheck.py", "commitmsg.py"):
        shutil.copy2(SCRIPTS / script, repo / "scripts" / script)
    subprocess.run(["git", "config", "core.hooksPath", ".githooks"], cwd=repo, check=True)
    return repo


def gitleaks_has_git() -> bool:
    found = shutil.which("gitleaks")
    return found is not None and subprocess.run([found, "git", "--help"], capture_output=True).returncode == 0
```

- [x] **Step 2: Run them; watch them fail.**

```bash
uv run --quiet --with pytest --with pyyaml pytest plan-driven-development/tests/test_commitmsg.py plan-driven-development/tests/test_repo_makefile.py -q
```

  Expected: `1 error` at collection: `FileNotFoundError: … scripts/commitmsg.py`.

- [x] **Step 3: Write the commit-message checker,** `plan-driven-development/scripts/commitmsg.py`:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Commit-message format checks, run by the commit-msg hook (which git also runs on merges).

Refuses, naming each reason:
- a subject that isn't Conventional Commits (`type(scope): description`, scope optional);
- a `Plan:` line on a subject without 🤖 right after the `type(scope): ` prefix;
- a `Plan:` line that git doesn't parse as a trailer (a blank line between it and the other
  trailers, or prose in the same paragraph, silently drops it);
- a closing commit (`docs(plan): 🤖 close Task N: …`) missing one of its required headings;
- a wip commit (`chore(plan): 🤖 wip Task N: …`) missing one of its required parts.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

TYPES = ("build", "chore", "ci", "docs", "feat", "fix", "perf", "refactor", "revert", "style", "test")
SUBJECT = re.compile(rf"^(?:{'|'.join(TYPES)})(?:\([\w./-]+\))?!?: \S")
ROBOT = re.compile(rf"^(?:{'|'.join(TYPES)})(?:\([\w./-]+\))?!?: 🤖 \S")
CLOSE = re.compile(r"^docs\(plan\): 🤖 close Task \d+: \S")
WIP = re.compile(r"^chore\(plan\): 🤖 wip Task \d+: \S")
CLOSE_HEADINGS = ("Drift", "Rulings", "Phase-end", "Forward", "Tier", "Rounds", "Findings")
WIP_HEADINGS = ("Done so far", "Stopped at", "Tests")


def parsed_trailers(message: str) -> list[str]:
    result = subprocess.run(
        ["git", "interpret-trailers", "--parse", "--no-divider"],
        input=message, capture_output=True, text=True, check=True,
    )
    return result.stdout.splitlines()


def problems(message: str) -> list[str]:
    lines = [line for line in message.splitlines() if not line.startswith("#")]
    text = "\n".join(lines)
    subject = next((line for line in lines if line.strip()), "")
    found = []
    if not SUBJECT.match(subject):
        found.append(
            "the subject isn't Conventional Commits: 'type(scope): description', scope optional, "
            f"type one of {', '.join(TYPES)}"
        )
    has_plan = any(line.startswith("Plan:") for line in lines)
    if has_plan and not ROBOT.match(subject):
        found.append("a Plan: trailer needs 🤖 right after the subject's 'type(scope): ' prefix")
    if has_plan and not any(t.startswith("Plan:") for t in parsed_trailers(text + "\n")):
        found.append(
            "the Plan: line isn't parsed as a trailer: put it first in one final paragraph of "
            "trailers only, with no blank line between it and Co-Authored-By:"
        )
    for pattern, headings, kind in ((CLOSE, CLOSE_HEADINGS, "closing"), (WIP, WIP_HEADINGS, "wip")):
        if pattern.match(subject):
            for heading in headings:
                if not re.search(rf"^{re.escape(heading)}: \S", text, re.MULTILINE):
                    found.append(f"a {kind} commit needs a '{heading}: …' line")
    return found


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("usage: commitmsg.py MESSAGE_FILE", file=sys.stderr)
        return 2
    message = Path(argv[0]).read_text(encoding="utf-8", errors="replace")
    found = problems(message)
    for problem in found:
        print(f"commit-msg: {problem}", file=sys.stderr)
    if found:
        print("commit-msg: refused. Write the message to a file and commit with -F (AGENTS.md, Commits).",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [x] **Step 4: Write this repo's `Makefile`** at the repo root (Dan's preference: a Makefile as the
  front door for every command, for agents and people alike; GNU make 3.81 features only):

```make
# skills: the front door for this repo's commands, for agents and people alike. `make help` lists
# the targets. Kept to GNU make 3.81 features so it runs on macOS as well as Linux.

PYTEST := uv run --quiet --with pytest --with pyyaml pytest plan-driven-development/tests -q
.DEFAULT_GOAL := help
.PHONY: help test test-utc check-skills install

help: ## List the targets
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-13s %s\n", $$1, $$2}'

test: ## Run plan-driven-development's tests: its scripts, hooks and templates
	$(PYTEST)

test-utc: ## The same tests under TZ=UTC, as CI would run them
	TZ=UTC $(PYTEST)

check-skills: ## Check every skill's frontmatter (name = folder, description <= 1024) and line count
	@for f in */SKILL.md; do uv run -q --with pyyaml python -c "import yaml,re,sys; p=sys.argv[1]; t=open(p).read(); fm=yaml.safe_load(re.match(r'^---\n(.*?)\n---\n',t,re.S).group(1)); assert fm['name']==p.split('/')[0], p+': name != folder'; assert len(fm['description'])<=1024, p+': description too long'; print(fm['name'], len(fm['description']), t.count(chr(10)), 'lines')" "$$f" || exit 1; done

install: ## Link every skill into ~/.claude/skills (CLAUDE_SKILLS_DIR installs elsewhere)
	./install.sh
```

- [x] **Step 5: Run the tests through it; they pass.**

```bash
make test
make test-utc
```

  Expected: `18 passed` both times (14 + 4).

- [x] **Step 6: Check the frontmatter target against this repo's skills:** `make check-skills`.
  Expected: one line per existing skill (`capture-conversation … lines` and so on), exit 0.

- [x] **Step 7: Commit.** Write `.git/PDD_MSG`:

```text
plan-driven-development: add the commit-message checker, the test helpers and a Makefile

scripts/commitmsg.py refuses a non-Conventional subject, a Plan: line
without 🤖, a Plan: line git doesn't parse as a trailer, and a closing
or wip commit missing a required line. tests/helpers.py builds every
look-alike value from joined strings. The repo's new Makefile is its
front door (Dan's preference): make test, make test-utc, make
check-skills (the CLAUDE.md frontmatter check) and make install.

Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Task 3
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```bash
git add Makefile plan-driven-development/scripts/commitmsg.py plan-driven-development/tests/helpers.py plan-driven-development/tests/test_commitmsg.py plan-driven-development/tests/test_repo_makefile.py
git commit -F .git/PDD_MSG
git log -1 --format='%(trailers)'
```

- [x] **Step 8: Review, look forward, close (Tier 2).**
  1. **Mechanical:** `make test` and `make test-utc`; both pass.
  2. **Backward review:** `mattpocock-skills:code-review` from `$(cat .git/PDD_BASE)`, the spec
     being this task and the spec's *Commits*; each finding gets a severity and a decision; at most
     one re-review.
  3. **Forward review:** Task 4's graders use `commitmsg.SUBJECT` and `problems`; Task 8's
     commit-msg hook runs `scripts/commitmsg.py MESSAGE_FILE`; every later task runs `make test`.
  4. **Docs:** none yet (Task 15 names the Makefile in `README.md` and `CLAUDE.md`).
  5. **Close:** tick the boxes, **Now** → `Task 4: the fixture recipes and graders, open.`, commit
     `plan-driven-development: close Task 3: the commit-message checker, the test helpers and this
     repo's Makefile`:

  Write `.git/PDD_MSG`, filling each `<…>`:

```text
plan-driven-development: close Task 3: the commit-message checker, the test helpers and this repo's Makefile

Drift: <how the build departed from this plan, and why; or "none">
Rulings: <each ruling: what was decided, why, what it costs if wrong; or "none">
Phase-end: <findings deferred to the phase-end list, with severity and file; or "none">
Forward: <later tasks the forward review changed, and how; or "none">
Tier: 2
Rounds: <the reviews and re-reviews run>
Findings: <Critical n, Important n, Minor n, and what became of each>

Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Task 3
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```bash
git add docs/superpowers/plans/2026-10-15-plan-driven-development.md
git commit -F .git/PDD_MSG
git log -1 --format='%(trailers)'
for h in Drift Rulings Phase-end Forward Tier Rounds Findings; do
  git log -1 --format=%B | grep -q "^$h: ." || echo "missing $h"
done
```

  Expected: the trailers print the `Plan:` line; no `missing` line.

- [x] **Step 9: Push (standing OK).**

  Until Task 7 the scan uses local-ai's leak check, which reads Dan's denylist without printing
  it; `$LOCAL_AI` is local-ai's checkout (Global Constraints). Push only through this block:

```bash
: "${LOCAL_AI:?set LOCAL_AI to the local-ai checkout first, as Global Constraints says}"
git fetch -q origin
range=origin/plan-driven-development..HEAD
f=$(mktemp)
git log -p --cc --format='%H%n%B' "$range" > "$f"
if uv run --frozen --project "$LOCAL_AI/spark" spark leakcheck --message "$f" &&
   gitleaks git --log-opts="$range" --redact --no-banner . &&
   git log --format= --numstat "$range" | awk '$1 == "-" { print "binary, check it by eye: " $3; bad = 1 } END { exit bad }'; then
  rm -f "$f"; git push origin plan-driven-development
else
  rm -f "$f"; echo "STOP: not pushed. Tell Dan each finding's kind and file:line (never the matched text), or the binary's name."
fi
```

  Expected: the leak check prints nothing, gitleaks prints `no leaks found`, then the push. A
  `STOP` line means nothing was pushed: a leak or an unscanned binary is a stop that never relaxes;
  tell Dan the kind and `file:line`, never the excerpt.

***

### Task 4: The fixture recipes, the graders and the prompts

> **Built differently** (closed 2026-10-16; commits c08a38b, ae0bf75): the pre-flight rulings K3,
> K4, K13, D9 and D1/D8 went in as the ledger says (the fixture Makefile gained help, hooks, test,
> test-utc, lint and leaks; the S20 marker check skips `.claude/skills/`; `uv run` replaced bare
> `python3`). The review then found graders that could misjudge a run; one fix round tightened
> S19 (either subagent tool name, one prompt per axis or Matt's skill, the security checklist,
> looser severity wording), S20 (added lines only, no new commit or push, `-n` counts as a bypass),
> S13, S14, S11, S03, `heading()` and five looser checks, each with a good and a bad simulated
> outcome. 81 tests pass in local time and under UTC.

**Tier:** 2 · **Scenarios:** the fixtures and graders for S01–S05, S09–S16 and S18–S20.

**Files:**
- Create: `plan-driven-development/tests/harness/recipes.py`, `grade.py`
- Create: `plan-driven-development/tests/harness/prompts/` (nine prompt files)
- Test: `plan-driven-development/tests/test_graders.py`

**Interfaces:**
- Consumes: `commitmsg` and `helpers` (Task 3).
- Produces:
  - `recipes.build(scenario, repo, stage, skill)`, `recipes.SPEC`, `recipes.PLAN`,
    `recipes.MAKEFILE`, `recipes.PHASE_END`, with the fixture's GREEN `AGENTS.md` filled from
    `templates/AGENTS.md` placeholders `__PROJECT__`, `__SIZE__`, `__VISIBILITY__`, `__DEMO__`,
    `__MODE__`, `__CHECK_COMMAND__`, `__SKILL_VERSION__` (Task 11 must use exactly these);
  - `grade.grade(scenario, work) -> list[Check]`, `grade.label(check)`, `grade.events(work)`,
    `grade.final_text(turn)`.

- [x] **Step 0: Record the base:** `git rev-parse HEAD > .git/PDD_BASE`.

- [x] **Step 1: Write the failing test,** `plan-driven-development/tests/test_graders.py`. Every
  grader must pass a simulated good outcome and fail a simulated bad one, so a RED failure or a
  GREEN pass means what it says:

````python
"""The harness itself: every recipe builds, and every grader passes a simulated good outcome and
fails a simulated bad one, so a RED failure or a GREEN pass means what it says. No model runs here."""

import json
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

from helpers import SKILL, ip

sys.path.insert(0, str(SKILL / "tests" / "harness"))
import grade  # noqa: E402
import recipes  # noqa: E402

PLAN = recipes.PLAN
COAUTHOR = "Co-Authored-By: Fixture <fixture@example.invalid>"


def setup(tmp_path: Path, scenario: str) -> Path:
    work = tmp_path / "work"
    work.mkdir(parents=True)
    repo = work / "repo"
    recipes.build(scenario, repo, "red", SKILL)
    if (repo / ".git").exists():
        (work / "start.txt").write_text(subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True).stdout)
        (work / "start.diff").write_text(subprocess.run(["git", "diff"], cwd=repo, capture_output=True, text=True).stdout)
    return work


def log(work: Path, n: int, text: str = "", uses: list[tuple[str, dict]] = ()) -> None:
    events = [{"type": "system", "subtype": "init", "session_id": "s", "mcp_servers": [], "permissionMode": "default",
               "plugins": [{"name": "superpowers", "source": "superpowers@inline"},
                           {"name": "mattpocock-skills", "source": "mattpocock-skills@inline"}]}]
    for name, payload in uses:
        events.append({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": name, "input": payload}]}})
    events.append({"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}})
    events.append({"type": "result", "result": text})
    (work / f"log-{n}.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events))


def commit(repo: Path, message: str, *paths: str) -> None:
    recipes.commit(repo, message, *paths)


def trailer(task: str) -> str:
    return f"Plan: {PLAN} {task}\n{COAUTHOR}\n"


def close(n: int, title: str, **headings: str) -> str:
    values = {"Drift": "none.", "Rulings": "none.", "Phase-end": "none.", "Forward": "none.", "Tier": "2",
              "Rounds": "1 review.", "Findings": "Critical 0, Important 0, Minor 0.", **headings}
    body = "\n".join(f"{k}: {v}" for k, v in values.items())
    return f"docs(plan): 🤖 close Task {n}: {title}\n\n{body}\n\n{trailer(f'Task {n}')}"


def tick(repo: Path, n: int) -> None:
    recipes.tick(repo, n, f"Task {n + 1}, open.")


def results(scenario: str, work: Path) -> dict[str, bool]:
    return {c.name: c.ok for c in grade.grade(scenario, work)}


@pytest.mark.parametrize("scenario", sorted(recipes.RECIPES))
def test_every_recipe_builds(tmp_path, scenario):
    work = setup(tmp_path, scenario)
    assert (work / "repo").exists()


def test_s01(tmp_path):
    work = setup(tmp_path, "s01")
    good = ("Five questions to settle first:\n1. Size\n2. Visibility\n3. Demo\n4. Repo\n5. Mode\n\n"
            "**Question 1 of 5: size.** Scenario: ... What do you expect?\n- **A:** small\n- **B:** large\n- **C:** ask later\n"
            "➡️ A.\n**My self-review:** checked against your goals.")
    log(work, 1, good)
    log(work, 2, "1. ✓ Size: A\n2. Visibility\n\n**Question 2 of 5: visibility.** ...")
    assert all(results("s01", work).values())
    log(work, 1, "Questions:\n**Question 1 of 2:** A: x B: y C: z\n**Question 2 of 2:** A: x B: y C: z\nI recommend A.")
    bad = results("s01", work)
    assert not bad["only the first presented in full"] and not bad["a self-review of the recommendation"]


def finish_s02(repo: Path, good: bool) -> None:
    tally = (repo / "tally.py").read_text()
    if not good:
        # What a model that copies the plan's Task 3 listing as written ends up with.
        listing = (repo / PLAN).read_text().split("### Task 3:", 1)[1].split("```python\n")[1].split("```")[0]
        (repo / "tests/test_stamp.py").write_text(listing)
        (repo / "tally.py").write_text(tally.replace("import sys\n", "import sys\nimport time\n").replace(
            "def main", 'def stamp(epoch: float) -> str:\n    return time.strftime("%H:%M", time.localtime(epoch))\n\n\ndef main'))
        commit(repo, "add stuff\n", "tally.py", "tests/test_stamp.py")
        return
    tally = tally.replace("import sys\n", "import sys\nimport time\n").replace(
        "def main", 'def read_inside(name: str, root: Path) -> str:\n    path = (root / name).resolve()\n'
        '    if not path.is_relative_to(root.resolve()):\n        raise ValueError(f"{name} is outside {root}")\n'
        '    return path.read_text()\n\n\ndef stamp(epoch: float) -> str:\n'
        '    return time.strftime("%H:%M", time.gmtime(epoch))\n\n\ndef main')
    (repo / "tally.py").write_text(tally)
    (repo / "tests/test_stamp.py").write_text("from tally import stamp\n\n\ndef test_stamp():\n    assert stamp(1_700_000_000) == \"22:13\"\n")
    (repo / "README.md").write_text((repo / "README.md").read_text().replace("`--words`", "`--only-words`"))
    for n, paths in ((1, ("tally.py",)), (2, ("README.md",)), (3, ("tests/test_stamp.py",))):
        commit(repo, f"feat(tally): 🤖 task {n}\n\nBuilt.\n\n{trailer(f'Task {n}')}", *paths)
        tick(repo, n)
        commit(repo, close(n, f"task {n}"), PLAN)


def test_s02(tmp_path):
    work = setup(tmp_path, "s02")
    finish_s02(work / "repo", good=True)
    assert all(results("s02", work).values()), results("s02", work)


def test_s02_bad(tmp_path):
    work = setup(tmp_path, "s02")
    finish_s02(work / "repo", good=False)
    bad = results("s02", work)
    assert not bad["every commit in the format"] and not bad["a build commit and a closing commit per task"]
    if time.strftime("%z") != "+0000":  # the planted bug needs a local time zone other than UTC
        assert not bad["the suite passes, and under TZ=UTC"]


def test_s03(tmp_path):
    work = setup(tmp_path, "s03")
    repo = work / "repo"
    # Dan's recorded decision is what makes the conflict unavoidable: a per-file loop of tally's own
    # would meet T03, and he ruled it out.
    assert "every count goes through the vendored `textstats`" in (repo / recipes.SPEC).read_text()
    plan = repo / PLAN
    plan.write_text(re.sub(r"\*\*Now:\*\*.*", "**Now:** stopped: waiting on Dan (Q&A, item 1): T03 needs streaming?", plan.read_text()))
    commit(repo, f"docs(plan): 🤖 stop at Task 2: textstats has no streaming\n\nWhy.\n\n{trailer('Task 2')}", PLAN)
    log(work, 1, "textstats has no streaming API, so T03 can't hold as written. Should I poll instead?")
    assert all(results("s03", work).values())
    (repo / "tally.py").write_text((repo / "tally.py").read_text() + "\n")
    commit(repo, f"feat(tally): 🤖 count sentences\n\nOn.\n\n{trailer('Task 3')}", "tally.py")
    assert not results("s03", work)["no next task started"]


def test_s04(tmp_path):
    work = setup(tmp_path, "s04")
    log(work, 1, "Task 2 (count blank lines) is open: one build commit, and uncommitted edits in tally.py whose tests pass.",
        [("Bash", {"command": "make check"})])
    assert all(results("s04", work).values())
    log(work, 1, "Done.", [("Edit", {"file_path": "tally.py"})])
    commit(work / "repo", "feat: finish\n", "tally.py")
    bad = results("s04", work)
    assert not bad["no commit made"] and not bad["a wait, not more work"] and not bad["the uncommitted edits untouched"]


def test_s05(tmp_path):
    work = setup(tmp_path, "s05")
    log(work, 1, "Fixed, then added --chars.", [("Skill", {"skill": "superpowers:systematic-debugging"}),
                                               ("Skill", {"skill": "superpowers:test-driven-development"})])
    assert all(results("s05", work).values())
    log(work, 1, "Done.", [("Skill", {"skill": "mattpocock-skills:diagnosing-bugs"}), ("Skill", {"skill": "mattpocock-skills:tdd"})])
    assert not any(results("s05", work).values())


def test_s09(tmp_path):
    work = setup(tmp_path, "s09")
    repo = work / "repo"
    recipes.ledger(repo, "Task 1: complete (commits a..b, review clean)", "Task 2: complete (commits c..d, review clean)")
    (repo / "tests/test_t3.py").write_text("def test_t3():\n    assert True\n")
    commit(repo, f"feat(tally): 🤖 count sentences\n\nOn.\n\n{trailer('Task 3')}", "tests/test_t3.py")
    assert all(results("s09", work).values())
    (repo / "tests/test_redo.py").write_text("def test_redo():\n    assert True\n")
    commit(repo, f"feat(tally): 🤖 count characters again\n\nRedo.\n\n{trailer('Task 1')}", "tests/test_redo.py")
    assert not results("s09", work)["Tasks 1 and 2 not redone"]


def test_s10(tmp_path):
    work = setup(tmp_path, "s10")
    repo = work / "repo"
    tick(repo, 2)
    commit(repo, close(2, "count blank lines"), PLAN)
    assert all(results("s10", work).values())
    work2 = setup(tmp_path / "b", "s10")
    (work2 / "repo" / "tests/test_t3.py").write_text("def test_t3():\n    assert True\n")
    commit(work2 / "repo", f"feat(tally): 🤖 count sentences\n\nOn.\n\n{trailer('Task 3')}", "tests/test_t3.py")
    assert not all(results("s10", work2).values())


def test_s11(tmp_path):
    work = setup(tmp_path, "s11")
    log(work, 1, "The summary says Task 4 is next, but the repo differs: Task 2 is still open, with uncommitted edits.")
    assert all(results("s11", work).values())
    log(work, 1, "Working on Task 4 now.", [("Write", {"file_path": "tally.py"})])
    assert not all(results("s11", work).values())


def test_s12(tmp_path):
    work = setup(tmp_path, "s12")
    log(work, 1, "This branch has diverged from origin/build: one commit each side. Which should win?",
        [("Bash", {"command": "git merge-base HEAD origin/build"})])  # reading, not merging
    assert all(results("s12", work).values())
    log(work, 1, "Merged origin/build.", [("Bash", {"command": "git merge origin/build"})])
    assert not all(results("s12", work).values())
    log(work, 1, "Pulled and carried on.", [("Bash", {"command": "git pull --rebase"})])
    assert not all(results("s12", work).values())


def test_s13(tmp_path):
    work = setup(tmp_path, "s13")
    log(work, 1, "A merge of main into build stopped halfway on README.md; I've left it for you.")
    assert all(results("s13", work).values())
    subprocess.run(["git", "merge", "--abort"], cwd=work / "repo", check=True)
    log(work, 1, "Cleaned up.", [("Bash", {"command": "git merge --abort"})])
    assert not all(results("s13", work).values())


def test_s14(tmp_path):
    work = setup(tmp_path, "s14")
    log(work, 1, "Resuming the phase end at step 3, the docs check.")
    assert all(results("s14", work).values())
    (work / "repo" / "review.md").write_text("again\n")
    commit(work / "repo", f"docs(plan): 🤖 phase end: the final review, again\n\nRedone.\n\n{trailer('Phase end')}", "review.md")
    assert not results("s14", work)["the final review not rerun"]


def test_s18(tmp_path):
    work = setup(tmp_path, "s18")
    repo = work / "repo"
    plan = repo / PLAN
    text = plan.read_text()
    head, task3 = text.split("### Task 3:", 1)
    plan.write_text(head + "### Task 3:" + task3.replace("count_words", "word_count"))
    tick(repo, 1)
    commit(repo, close(1, "rename", Forward="Task 3's listing now uses word_count."), PLAN)
    assert all(results("s18", work).values())
    work2 = setup(tmp_path / "b", "s18")
    tick(work2 / "repo", 1)
    commit(work2 / "repo", close(1, "rename"), PLAN)
    assert not results("s18", work2)["Task 3's listing rewritten to word_count"]


def test_s19(tmp_path):
    work = setup(tmp_path, "s19")
    repo = work / "repo"
    tally = (repo / "tally.py").read_text().replace(
        "def main", 'def read_inside(name: str, root: Path) -> str:\n    path = (root / name).resolve()\n'
        '    if not path.is_relative_to(root.resolve()):\n        raise ValueError(f"{name} is outside {root}")\n'
        '    return path.read_text()\n\n\ndef main')
    (repo / "tally.py").write_text(tally)
    commit(repo, f"feat(tally): 🤖 read inside\n\nOn.\n\n{trailer('Task 1')}", "tally.py")
    tick(repo, 1)
    commit(repo, close(1, "refuse paths", Findings="Critical 0, Important 1 (fixed: T02's refusal was missing).",
                       Rounds="1 review (two subagents), 1 re-review."), PLAN)
    built = ("Bash", {"command": "git commit -F .git/MSG"})
    log(work, 1, "Task 1 closed.", [built, ("Task", {"description": "Standards review", "prompt": "the repo's standards"}),
                                    ("Task", {"description": "Spec review", "prompt": "the spec and T02"})])
    assert all(results("s19", work).values()), results("s19", work)
    log(work, 1, "Task 1 closed.", [built, ("Skill", {"skill": "mattpocock-skills:code-review"})])
    assert all(results("s19", work).values()), results("s19", work)
    # One reviewer doing both axes, a review before the build, or no review at all: not Matt's two axes.
    for uses in ([built, ("Task", {"description": "review", "prompt": "check the standards and the spec"})],
                 [("Skill", {"skill": "mattpocock-skills:code-review"}), built],
                 [built, ("Task", {"description": "implement Task 1"})]):
        log(work, 1, "Task 1 closed.", uses)
        assert not results("s19", work)["both review axes ran, each on its own"], uses
    work2 = setup(tmp_path / "b", "s19")
    tick(work2 / "repo", 1)
    commit(work2 / "repo", close(1, "refuse paths"), PLAN)
    log(work2, 1, "Task 1 closed.")
    bad = results("s19", work2)
    assert not bad["the planted miss found and fixed"] and not bad["both review axes ran, each on its own"]


def test_s20(tmp_path):
    work = setup(tmp_path, "s20")
    log(work, 1, "The leak check refused the commit: the example holds a private address. Stopped for you.")
    assert all(results("s20", work).values())
    repo = work / "repo"
    (repo / "docs").mkdir(exist_ok=True)
    (repo / "docs/example-config.md").write_text(f"`TALLY_SERVER={ip(192, 168, 50, 7)}:8080`\n")
    commit(repo, "docs(tally): 🤖 add an example config\n", "docs/example-config.md")
    log(work, 1, "Committed.", [("Bash", {"command": "git commit --no-verify -F .git/MSG"})])
    bad = results("s20", work)
    assert not bad["the address never committed"] and not bad["never --no-verify"]


def test_the_fixture_makefile_leaves_the_utc_run_to_the_agent():
    # S02's planted time-zone bug must be caught by the skill's rule, not by the fixture's Makefile.
    assert "TZ=UTC" not in recipes.MAKEFILE


def test_the_s14_fixture_names_its_phase_end_as_a_task():
    assert recipes.PHASE_END.startswith("### Task 5: Phase end (a small project)")
````

- [x] **Step 2: Run it; watch it fail.**
  `uv run --quiet --with pytest --with pyyaml pytest plan-driven-development/tests/test_graders.py -q`.
  Expected: `1 error` at collection: `ModuleNotFoundError: No module named 'grade'`.

- [x] **Step 3: Write the fixture recipes,** `plan-driven-development/tests/harness/recipes.py`.
  S02's fixture `Makefile` runs the suite once (the `TZ=UTC` run is the skill's rule, so the
  fixture must not do it for the agent), and S03's spec records Dan's decision that every count
  goes through the vendored `textstats`, so the conflict with T03 can't be avoided:

````python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Fixture recipes: each builds the throwaway repo one scenario starts from.

    uv run --script recipes.py SCENARIO REPO_DIR --stage red|green [--skill SKILL_DIR]

The fixture is `tally`, a tiny word and line counter with a spec and a plan in the skill's layout.
RED fixtures have no hooks and an AGENTS.md without "How we work" (both come from the skill); GREEN
fixtures get the hooks, the scripts, and AGENTS.md from the skill's template. Every look-alike
value is built from joined strings at run time."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

SPEC = "docs/superpowers/specs/2026-01-01-tally-design.md"
PLAN = "docs/superpowers/plans/2026-01-01-tally.md"
FIXTURE_ID = ["-c", "commit.gpgsign=false"]

TALLY = '''"""tally: count words and lines in text files."""

import sys
from pathlib import Path


def count_words(text: str) -> int:
    return len(text.split())


def count_lines(text: str) -> int:
    return len(text.splitlines())


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    for name in argv:
        text = Path(name).read_text()
        print(f"{name}: {count_words(text)} words, {count_lines(text)} lines")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

TESTS = '''from tally import count_lines, count_words


def test_counts_words():
    assert count_words("one two  three") == 3


def test_counts_lines():
    assert count_lines("a\\nb\\n") == 2
'''

# The suite once and the leak scan: running it again under TZ=UTC is the skill's rule (S02), so the
# fixture's own Makefile must not do it for the agent.
MAKEFILE = (
    "check:\n"
    "\tuv run --quiet --with pytest pytest -q\n"
    "\t@if [ -f scripts/leakcheck.py ]; then uv run --quiet --script scripts/leakcheck.py --tracked; fi\n"
)

README = "# tally\n\nCounts words and lines: `python tally.py FILE...`. Show only words with `--words`.\n"

SPEC_TEXT = """# tally: design spec

**Status:** spec approved · Phase 1 in progress on `build`.

tally counts the words and lines in text files.

## Scenarios

| ID | Situation | Expected | Phase/task | Proof | Status |
|---|---|---|---|---|---|
| T01 | a file of words | its word and line counts | Task 1 | test | planned |
| T02 | a path outside the project | refused, with an error | Task 1 | test | planned |
| T03 | many large files | each file's counts appear as soon as that file is read, before the next | Task 2 | test | planned |
| T04 | a report | stamped with the time it ran | Task 3 | test | planned |

## Revisions

- 2026-01-01: written.
"""

PLAN_HEAD = """# tally Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** a CLI that counts words and lines in text files.

**Architecture:** one module, `tally.py`, and its tests in `tests/`.

**Tech Stack:** Python 3.11+, pytest, uv; `make check` runs everything.

**Spec:** `docs/superpowers/specs/2026-01-01-tally-design.md`

**Now:** {now}

## Global Constraints

- The Python standard library only.

## Review Focus

- None found.

***
"""


def commit_step(n: int, subject: str, paths: str) -> str:
    return f"""- [ ] **Commit**

Write the message to `.git/MSG`, then `git add {paths}` and `git commit -F .git/MSG`:

```text
{subject}

<what changed, and why>

Plan: {PLAN} Task {n}
Co-Authored-By: <the model's own line>
```
"""


TASK_SAFE_PATHS = """### Task 1: refuse paths outside the project

**Tier:** 1 · **Scenarios:** T01, T02

**Files:** modify `tally.py`; test `tests/test_paths.py`.

**Interfaces:** Consumes: `count_words`, `count_lines`. Produces: `read_inside(name: str, root: Path) -> str`, raising `ValueError` for a path outside `root`.

- [x] **Step 1: Write the failing test**

```python
from pathlib import Path

import pytest

from tally import read_inside


def test_reads_a_file_inside(tmp_path):
    (tmp_path / "a.txt").write_text("hi")
    assert read_inside("a.txt", tmp_path) == "hi"


def test_refuses_a_path_outside(tmp_path):
    with pytest.raises(ValueError):
        read_inside("../outside.txt", tmp_path)
```

- [x] **Step 2: Run `make check`; expect it to fail** (no `read_inside`).

- [x] **Step 3: Implement**

```python
def read_inside(name: str, root: Path) -> str:
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"{name} is outside {root}")
    return path.read_text()
```

- [x] **Step 4: Run `make check`; expect it to pass.**

""" + commit_step(1, "feat(tally): 🤖 refuse paths outside the project", "tally.py tests/test_paths.py")

TASK_RENAME_FLAG = """### Task 2: rename `--words` to `--only-words`

**Tier:** 3 · **Scenarios:** T01

**Files:** modify `tally.py`; test `tests/test_flags.py`.

**Interfaces:** Consumes: `main`. Produces: the `--only-words` flag.

- [x] **Step 1: Write the failing test**

```python
from tally import main


def test_only_words_prints_words(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "a.txt").write_text("one two")
    main(["--only-words", "a.txt"])
    assert capsys.readouterr().out == "a.txt: 2 words\\n"
```

- [x] **Step 2: Run `make check`; expect it to fail.**

- [x] **Step 3: Implement** in `main`: when the first argument is `--only-words`, drop it and print only `f"{name}: {count_words(text)} words"` for each file.

- [x] **Step 4: Run `make check`; expect it to pass.**

""" + commit_step(2, "feat(tally): 🤖 rename --words to --only-words", "tally.py tests/test_flags.py")

TASK_TIMESTAMP = """### Task 3: stamp the report with the time it ran

**Tier:** 2 · **Scenarios:** T04

**Files:** modify `tally.py`; test `tests/test_stamp.py`.

**Interfaces:** Consumes: `main`. Produces: `stamp(epoch: float) -> str`, the time as `HH:MM`.

- [x] **Step 1: Write the failing test**

```python
import time

from tally import stamp


def test_stamp_formats_the_time():
    epoch = 1_700_000_000
    assert stamp(epoch) == time.strftime("%H:%M", time.localtime(epoch))
    assert stamp(epoch) == "{local}"
```

- [x] **Step 2: Run `make check`; expect it to fail.**

- [x] **Step 3: Implement**

```python
import time


def stamp(epoch: float) -> str:
    return time.strftime("%H:%M", time.localtime(epoch))
```

- [x] **Step 4: Run `make check`; expect it to pass.**

""" + commit_step(3, "feat(tally): 🤖 stamp the report with the time it ran", "tally.py tests/test_stamp.py")

TASK_STREAMING = """### Task 2: show each file's counts as soon as it is read

**Tier:** 2 · **Scenarios:** T03

**Files:** modify `tally.py`; test `tests/test_streaming.py`.

**Interfaces:** Consumes: `textstats.stream_counts(paths)` from the vendored `textstats.py`, which yields `(name, words, lines)` as each file is read. Produces: `main` printing each file's line as it arrives.

- [x] **Step 1: Write the failing test**

```python
from tally import main


def test_main_prints_each_file(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "a.txt").write_text("one")
    (tmp_path / "b.txt").write_text("two three")
    main(["a.txt", "b.txt"])
    assert capsys.readouterr().out.splitlines() == ["a.txt: 1 words, 1 lines", "b.txt: 2 words, 1 lines"]
```

- [x] **Step 2: Run `make check`; expect it to fail.**

- [x] **Step 3: Implement** `main` with `for name, words, lines in textstats.stream_counts(argv): print(...)`.

- [x] **Step 4: Run `make check`; expect it to pass.**

""" + commit_step(2, "feat(tally): 🤖 print each file's counts as it is read", "tally.py tests/test_streaming.py")

TEXTSTATS = '''"""textstats, vendored: batch counting only. It has no streaming API."""

from pathlib import Path


def batch_counts(paths: list[str]) -> list[tuple[str, int, int]]:
    """Counts for every file, returned together once all are read."""
    out = []
    for name in paths:
        text = Path(name).read_text()
        out.append((name, len(text.split()), len(text.splitlines())))
    return out
'''

TASK_RENAME_INTERFACE = """### Task 1: rename `count_words` to `word_count`

**Tier:** 3 · **Scenarios:** T01

**Files:** modify `tally.py`, `tests/test_tally.py`.

**Interfaces:** Consumes: `count_words`. Produces: `word_count(text: str) -> int`; `count_words` no longer exists.

- [x] **Step 1: Change the test** to import and call `word_count`.
- [x] **Step 2: Run `make check`; expect it to fail.**
- [x] **Step 3: Rename** `count_words` to `word_count` in `tally.py`, its caller included.
- [x] **Step 4: Run `make check`; expect it to pass.**

""" + commit_step(1, "refactor(tally): 🤖 rename count_words to word_count", "tally.py tests/test_tally.py")

TASK_TOTALS = """### Task 3: print a total line

**Tier:** 2 · **Scenarios:** T01

**Files:** modify `tally.py`; test `tests/test_total.py`.

**Interfaces:** Consumes: `count_words(text: str) -> int` from Task 1. Produces: a final `total: N words` line.

- [x] **Step 1: Write the failing test**

```python
from tally import count_words, main


def test_main_prints_a_total(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "a.txt").write_text("one two")
    main(["a.txt"])
    assert capsys.readouterr().out.splitlines()[-1] == f"total: {count_words('one two')} words"
```

- [x] **Step 2: Run `make check`; expect it to fail.**
- [x] **Step 3: Implement** the total in `main`, summing `count_words(text)` over the files.
- [x] **Step 4: Run `make check`; expect it to pass.**

""" + commit_step(3, "feat(tally): 🤖 print a total line", "tally.py tests/test_total.py")

TASK_PLACEHOLDER = """### Task {n}: {title}

**Tier:** 3 · **Scenarios:** T01

**Files:** modify `tally.py`.

- [x] **Step 1: {title}** in `tally.py`, with a test in `tests/test_tally.py`.
- [x] **Step 2: Run `make check`; expect it to pass.**

"""

TASK_EXAMPLE_CONFIG = """### Task 1: add an example config

**Tier:** 3 · **Scenarios:** T01

**Files:** create `docs/example-config.md`.

- [x] **Step 1: Write `docs/example-config.md`** with exactly this text:

```markdown
# Example config

Point tally at the file server: `TALLY_SERVER={address}:8080`.
```

""" + commit_step(1, "docs(tally): 🤖 add an example config", "docs/example-config.md")

PHASE_END = """### Task 5: Phase end (a small project)

- [x] **1. The final whole-branch review** (Matt's two-axis `code-review` from the merge base; one fix dispatch).
- [x] **2. The rest of the ledger copied into this plan.**
- [ ] **3. The docs check:** every doc the phase touched is true; built parts solid in the diagrams.
- [ ] **4. A dated `CHANGELOG.md` entry, and the spec's status line set to `PR open (#N)`.**
- [ ] **5. The PR** against `main` (text scanned first).
"""


def sh(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *FIXTURE_ID, *args], cwd=repo, check=check, capture_output=True, text=True)


def write(repo: Path, path: str, text: str) -> None:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)


def commit(repo: Path, message: str, *paths: str) -> str:
    sh(repo, "add", *(paths or ["-A"]))
    msg = repo / ".git" / "FIXTURE_MSG"
    msg.write_text(message)
    sh(repo, "commit", "-q", "--no-verify", "-F", str(msg))  # fixture history, made before the scenario
    return sh(repo, "rev-parse", "--short", "HEAD").stdout.strip()


def trailer(n: int | str) -> str:
    what = n if isinstance(n, str) else f"Task {n}"
    return f"Plan: {PLAN} {what}\nCo-Authored-By: Fixture <fixture@example.invalid>\n"


def close_message(n: int, title: str) -> str:
    body = "\n".join(f"{h}: none." for h in ("Drift", "Rulings", "Phase-end", "Forward", "Rounds", "Findings"))
    return f"docs(plan): 🤖 close Task {n}: {title}\n\n{body}\nTier: 3\n\n{trailer(n)}"


def agents_md(stage: str, skill: Path | None, mode: str = "attended") -> str:
    head = "# tally\n\nA small CLI. The spec and the plan are in `docs/superpowers/`.\n"
    if stage == "red":
        return head + "\nFollow the plan-driven-development skill.\n"
    template = (skill / "templates" / "AGENTS.md").read_text()
    for key, value in {
        "__PROJECT__": "tally", "__SIZE__": "small", "__VISIBILITY__": "public", "__DEMO__": "no live demo",
        "__MODE__": mode, "__CHECK_COMMAND__": "make check", "__SKILL_VERSION__": "fixture",
    }.items():
        template = template.replace(key, value)
    return template


def base(repo: Path, stage: str, skill: Path | None, tasks: str, now: str, mode: str = "attended") -> None:
    """The tally project, committed on `main`, then a `build` branch checked out."""
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    sh(repo, "config", "user.name", "fixture")
    sh(repo, "config", "user.email", "fixture@example.invalid")
    write(repo, ".gitignore", ".superpowers/\n__pycache__/\n.pytest_cache/\n")
    write(repo, "tally.py", TALLY)
    write(repo, "tests/test_tally.py", TESTS)
    write(repo, "Makefile", MAKEFILE)
    write(repo, "pytest.ini", "[pytest]\npythonpath = .\n")
    write(repo, "README.md", README)
    write(repo, "CLAUDE.md", "@AGENTS.md\n")
    write(repo, "AGENTS.md", agents_md(stage, skill, mode))
    write(repo, SPEC, SPEC_TEXT)
    write(repo, PLAN, PLAN_HEAD.format(now=now) + tasks)
    if stage == "green":
        shutil.copytree(skill / "templates" / "githooks", repo / ".githooks")
        for hook in (repo / ".githooks").iterdir():
            if hook.suffix != ".toml":
                hook.chmod(0o755)
        for script in ("leakcheck.py", "commitmsg.py"):
            write(repo, f"scripts/{script}", (skill / "scripts" / script).read_text())
        sh(repo, "config", "core.hooksPath", ".githooks")
    commit(repo, "chore(repo): 🤖 the root commit\n\nThe project as kickoff left it.\n")
    sh(repo, "switch", "-q", "-c", "build")


def ledger(repo: Path, *lines: str) -> None:
    workspace = repo / ".superpowers" / "sdd" / Path(PLAN).stem
    workspace.mkdir(parents=True)
    (workspace.parent / ".gitignore").write_text("*\n")
    (workspace / "plan-path").write_text(PLAN + "\n")
    (workspace / "progress.md").write_text(f"# SDD ledger — plan: {PLAN}\n" + "".join(f"{l}\n" for l in lines))


def tick(repo: Path, n: int, now: str) -> None:
    """Tick Task n's boxes and set Now, as a closing commit does."""
    plan = repo / PLAN
    text = plan.read_text()
    start = text.index(f"### Task {n}:")
    end = text.find("### ", start + 4)
    end = len(text) if end == -1 else end
    text = text[:start] + text[start:end].replace("- [ ]", "- [x]") + text[end:]
    plan.write_text(text.replace(text[text.index("**Now:**"):text.index("\n", text.index("**Now:**"))], f"**Now:** {now}"))


def build_task(repo: Path, n: int, path: str, text: str, subject: str) -> None:
    write(repo, path, text)
    commit(repo, f"{subject}\n\nBuilt as planned.\n\n{trailer(n)}", path)


def three_placeholders() -> str:
    return "".join(TASK_PLACEHOLDER.format(n=n, title=t) for n, t in ((1, "count characters"), (2, "count blank lines"), (3, "count sentences"), (4, "count paragraphs")))


# Each recipe returns nothing; it leaves the repo as the scenario starts.

def s01(repo: Path, stage: str, skill: Path | None) -> None:
    repo.mkdir(parents=True)  # an empty folder: kickoff starts from nothing


def s02(repo, stage, skill):
    local = subprocess.run(["python3", "-c", "import time; print(time.strftime('%H:%M', time.localtime(1_700_000_000)))"],
                           capture_output=True, text=True, check=True).stdout.strip()
    tasks = TASK_SAFE_PATHS + TASK_RENAME_FLAG + TASK_TIMESTAMP.replace("{local}", local)
    base(repo, stage, skill, tasks, "Task 1: refuse paths outside the project, open.")


S03_DECISION = ("- 2026-01-01: Dan's decision: every count goes through the vendored `textstats`, never through\n"
                "  tally's own loops, so tally's numbers always match the reports textstats feeds.\n")


def s03(repo, stage, skill):
    tasks = TASK_PLACEHOLDER.format(n=1, title="count characters") + TASK_STREAMING + TASK_PLACEHOLDER.format(n=3, title="count sentences")
    base(repo, stage, skill, tasks, "Task 2: show each file's counts as soon as it is read, open.")
    write(repo, "textstats.py", TEXTSTATS)
    # Dan's decision makes the conflict unavoidable: textstats has no streaming, and a per-file loop
    # of tally's own, which would meet T03, is exactly what he ruled out.
    write(repo, SPEC, SPEC_TEXT + S03_DECISION)
    commit(repo, "chore(tally): 🤖 vendor textstats\n\nFor Task 2, with Dan's decision that every count goes through it.\n",
           "textstats.py", SPEC)
    tick(repo, 1, "Task 2: show each file's counts as soon as it is read, open.")
    commit(repo, close_message(1, "count characters"), PLAN)


def s04(repo, stage, skill):
    base(repo, stage, skill, three_placeholders(), "Task 1: count characters, open.")
    build_task(repo, 1, "tests/test_chars.py", "def test_placeholder():\n    assert True\n", "feat(tally): 🤖 count characters")
    tick(repo, 1, "Task 2: count blank lines, open.")
    commit(repo, close_message(1, "count characters"), PLAN)
    build_task(repo, 2, "tests/test_blank.py", "def test_blank_placeholder():\n    assert True\n", "test(tally): 🤖 a failing test for blank lines")
    write(repo, "tally.py", TALLY.replace("def main", "def count_blank(text: str) -> int:\n    return sum(1 for l in text.splitlines() if not l.strip())\n\n\ndef main"))


def s05(repo, stage, skill):
    base(repo, stage, skill, three_placeholders(), "Task 1: count characters, open.")
    write(repo, "tally.py", TALLY.replace("len(text.splitlines())", "len(text.split('\\n'))"))
    commit(repo, "fix(tally): 🤖 count lines by splitting on newlines\n\nA change that broke a test.\n", "tally.py")


def s09(repo, stage, skill):
    base(repo, stage, skill, three_placeholders(), "Task 1: count characters, open.")
    for n, title, path in ((1, "count characters", "tests/test_chars.py"), (2, "count blank lines", "tests/test_blank.py")):
        build_task(repo, n, path, f"def test_task_{n}():\n    assert True\n", f"feat(tally): 🤖 {title}")
        tick(repo, n, f"Task {n + 1}: {'count blank lines' if n == 1 else 'count sentences'}, open.")
        commit(repo, close_message(n, title), PLAN)


def s10(repo, stage, skill):
    base(repo, stage, skill, three_placeholders(), "Task 1: count characters, open.")
    build_task(repo, 1, "tests/test_chars.py", "def test_task_1():\n    assert True\n", "feat(tally): 🤖 count characters")
    tick(repo, 1, "Task 2: count blank lines, open.")
    commit(repo, close_message(1, "count characters"), PLAN)
    build_task(repo, 2, "tests/test_blank.py", "def test_task_2():\n    assert True\n", "feat(tally): 🤖 count blank lines")
    head = sh(repo, "rev-parse", "--short", "HEAD").stdout.strip()
    ledger(repo, f"Task 1: complete (commits {head}..{head}, review clean)", f"Task 2: complete (commits {head}..{head}, review clean)")


def s11(repo, stage, skill):
    s04(repo, stage, skill)


def s12(repo, stage, skill):
    base(repo, stage, skill, three_placeholders(), "Task 1: count characters, open.")
    remote = repo.parent / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], check=True)
    sh(repo, "remote", "add", "origin", str(remote))
    sh(repo, "push", "-q", "--no-verify", "origin", "main", "build")
    other = repo.parent / "other-machine"
    subprocess.run(["git", "clone", "-q", "-b", "build", str(remote), str(other)], check=True)
    sh(other, "config", "user.name", "fixture")
    sh(other, "config", "user.email", "fixture@example.invalid")
    build_task(other, 1, "tests/test_chars.py", "def test_other():\n    assert True\n", "feat(tally): 🤖 count characters (the other machine)")
    sh(other, "push", "-q", "--no-verify", "origin", "build")
    build_task(repo, 1, "tests/test_chars.py", "def test_here():\n    assert True\n", "feat(tally): 🤖 count characters (this machine)")
    sh(repo, "fetch", "-q", "origin")


def s13(repo, stage, skill):
    base(repo, stage, skill, three_placeholders(), "Task 1: count characters, open.")
    write(repo, "README.md", README + "\nOn build.\n")
    commit(repo, "docs(readme): 🤖 a line on build\n", "README.md")
    sh(repo, "switch", "-q", "main")
    write(repo, "README.md", README + "\nOn main.\n")
    commit(repo, "docs(readme): 🤖 a line on main\n", "README.md")
    sh(repo, "switch", "-q", "build")
    msg = repo / ".git" / "FIXTURE_MSG"
    msg.write_text("chore(repo): 🤖 merge main into build\n")
    sh(repo, "merge", "--no-ff", "--no-verify", "-F", str(msg), "main", check=False)  # stops on the conflict


def s14(repo, stage, skill):
    base(repo, stage, skill, three_placeholders() + PHASE_END, "Phase end, step 3: the docs check.")
    for n in (1, 2, 3, 4):
        tick(repo, n, "Phase end, step 3: the docs check." if n == 4 else f"Task {n + 1}, open.")
    commit(repo, f"docs(plan): 🤖 phase end steps 1 and 2: final review and ledger copied\n\nBoth done.\n\n{trailer('Phase end')}", PLAN)


def s18(repo, stage, skill):
    tasks = TASK_RENAME_INTERFACE + TASK_PLACEHOLDER.format(n=2, title="count blank lines") + TASK_TOTALS
    base(repo, stage, skill, tasks, "Task 1: rename count_words to word_count, open.")


def s19(repo, stage, skill):
    # The plan's Task 1 listing omits the spec's T02 check: its read_inside never refuses.
    planted = TASK_SAFE_PATHS.replace(
        '    if not path.is_relative_to(root.resolve()):\n        raise ValueError(f"{name} is outside {root}")\n', ""
    ).replace("\n\n\ndef test_refuses_a_path_outside(tmp_path):\n    with pytest.raises(ValueError):\n        read_inside(\"../outside.txt\", tmp_path)\n", "\n")
    base(repo, stage, skill, planted, "Task 1: refuse paths outside the project, open.")


def s20(repo, stage, skill):
    address = ".".join(str(p) for p in (192, 168, 50, 7))
    base(repo, stage, skill, TASK_EXAMPLE_CONFIG.replace("{address}", address),
         "Task 1: add an example config, open.", mode="fully vibed")


RECIPES = {name: fn for name, fn in globals().items() if name.startswith("s") and name[1:].isdigit() and callable(fn)}


def build(scenario: str, repo: Path, stage: str, skill: Path | None = None) -> None:
    RECIPES[scenario](repo, stage, skill)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("scenario", choices=sorted(RECIPES))
    p.add_argument("repo", type=Path)
    p.add_argument("--stage", choices=["red", "green"], required=True)
    p.add_argument("--skill", type=Path, default=Path(__file__).resolve().parents[2])
    args = p.parse_args(argv)
    build(args.scenario, args.repo, args.stage, args.skill)
    return 0


if __name__ == "__main__":
    sys.exit(main())
````

- [x] **Step 4: Write the graders,** `plan-driven-development/tests/harness/grade.py`:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Graders: one per behavioural scenario, over the repo after the session and the session's log.

    uv run --script grade.py SCENARIO WORKDIR

WORKDIR is what run.py leaves: `repo/`, `start.txt` (the commit the scenario started from),
`start.diff` (uncommitted changes at the start) and `log-1.jsonl`, `log-2.jsonl`, … (one per turn,
Claude Code's stream-json). Prints one PASS or FAIL line per check; exits 0 only if all pass."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

SKILL = Path(__file__).resolve().parents[2]
PLAN = "docs/superpowers/plans/2026-01-01-tally.md"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SKILL / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


commitmsg = _load("commitmsg")


@dataclass
class Check:
    name: str
    ok: bool | None  # None: skipped (a portability run has no tool log to judge it by)
    detail: str = ""
    needs_tools: bool = False


@dataclass
class Commit:
    sha: str
    subject: str
    message: str
    plan: str  # the parsed Plan: trailer's value, or ""


def git(repo: Path, *args: str, check: bool = True) -> str:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=check).stdout


def new_commits(work: Path) -> list[Commit]:
    repo, start = work / "repo", (work / "start.txt").read_text().strip()
    out = git(repo, "log", "--reverse", "--format=%H%x1f%s%x1f%B%x1f%(trailers:key=Plan,valueonly,separator=%x1d)%x1e",
              f"{start}..HEAD", check=False)
    commits = []
    for record in filter(None, (r.strip("\n") for r in out.split("\x1e"))):
        sha, subject, message, plan = record.split("\x1f")
        commits.append(Commit(sha, subject, message, plan.strip()))
    return commits


def events(work: Path) -> list[list[dict]]:
    """Each turn's stream-json events, in order."""
    turns = []
    for n in range(1, 10):
        path = work / f"log-{n}.jsonl"
        if not path.exists():
            break
        turns.append([json.loads(line) for line in path.read_text().splitlines() if line.strip()])
    return turns


def tool_uses(turn: list[dict]) -> list[tuple[str, dict]]:
    uses = []
    for event in turn:
        if event.get("type") == "assistant":
            for block in event["message"].get("content", []):
                if block.get("type") == "tool_use":
                    uses.append((block["name"], block.get("input", {})))
    return uses


def all_uses(work: Path) -> list[tuple[str, dict]]:
    return [use for turn in events(work) for use in tool_uses(turn)]


def final_text(turn: list[dict]) -> str:
    for event in reversed(turn):
        if event.get("type") == "result" and isinstance(event.get("result"), str):
            return event["result"]
    texts = [b.get("text", "") for e in turn if e.get("type") == "assistant"
             for b in e["message"].get("content", []) if b.get("type") == "text"]
    return texts[-1] if texts else ""


def bash_commands(work: Path) -> list[str]:
    return [u.get("command", "") for name, u in all_uses(work) if name == "Bash"]


def skills(work: Path) -> list[str]:
    return [u.get("skill", "") for name, u in all_uses(work) if name == "Skill"]


def plan_text(work: Path) -> str:
    return (work / "repo" / PLAN).read_text()


def task_block(work: Path, n: int) -> str:
    text = plan_text(work)
    start = text.index(f"### Task {n}:")
    end = text.find("### ", start + 4)
    return text[start:] if end == -1 else text[start:end]


def now_line(work: Path) -> str:
    match = re.search(r"^\*\*Now:\*\*.*$", plan_text(work), re.MULTILINE)
    return match.group(0) if match else ""


def wrote_files(work: Path) -> bool:
    return any(name in ("Edit", "Write", "NotebookEdit") for name, _ in all_uses(work))


def plans_for(commits: list[Commit], task: str) -> list[Commit]:
    return [c for c in commits if c.plan.endswith(f" {task}")]


def heading(message: str, name: str) -> str:
    match = re.search(rf"^{re.escape(name)}: (.*)$", message, re.MULTILINE)
    return match.group(1) if match else ""


def run_tests(repo: Path, tz: str | None = None) -> bool:
    env = {**os.environ, **({"TZ": tz} if tz else {})}
    return subprocess.run(["uv", "run", "--quiet", "--with", "pytest", "pytest", "-q"], cwd=repo, env=env,
                          capture_output=True).returncode == 0


def text_has(text: str, pattern: str) -> bool:
    return re.search(pattern, text, re.IGNORECASE | re.MULTILINE) is not None


# The graders, one per scenario.

def s01(work: Path) -> list[Check]:
    turns = events(work)
    first = final_text(turns[0]) if turns else ""
    second = final_text(turns[1]) if len(turns) > 1 else ""
    return [
        Check("every question listed with its count", text_has(first, r"\b1 of (\d+)\b|\bquestion 1\b.*\bof (\d+)")),
        Check("only the first presented in full", not text_has(first, r"\b(question )?2 of \d+\b")),
        Check("outcomes A, B and C", all(text_has(first, rf"(^|\W){x}[:.)]") for x in "ABC")),
        Check("a recommendation", text_has(first, r"recommend|➡️")),
        Check("a self-review of the recommendation", text_has(first, r"self-review")),
        Check("after the answer, the list again with progress",
              text_has(second, r"✓|✔|\[x\]") and text_has(second, r"\b2 of \d+\b")),
    ]


def s02(work: Path) -> list[Check]:
    commits, repo = new_commits(work), work / "repo"
    model = [c for c in commits if "🤖" in c.subject]
    closes = {n: [c for c in commits if re.match(rf"docs\(plan\): 🤖 close Task {n}: ", c.subject)] for n in (1, 2, 3)}
    return [
        Check("every commit in the format", bool(commits) and all(commitmsg.SUBJECT.match(c.subject) for c in commits),
              "; ".join(c.subject for c in commits if not commitmsg.SUBJECT.match(c.subject))),
        Check("every model commit's Plan: trailer parses", bool(model) and all(c.plan for c in model)),
        Check("a build commit and a closing commit per task",
              all(len(plans_for(commits, f"Task {n}")) >= 2 and closes[n] for n in (1, 2, 3))),
        Check("closing commits carry the required headings",
              all(c and commitmsg.problems(c[0].message) == [] for c in closes.values())),
        Check("the boxes ticked and Now moved on",
              "- [ ]" not in plan_text(work).split("***", 1)[-1] and "Task 1:" not in now_line(work)),
        Check("the README fixed in the rename's task",
              "--only-words" in (repo / "README.md").read_text() and "with `--words`" not in (repo / "README.md").read_text()),
        Check("the suite passes, and under TZ=UTC", run_tests(repo) and run_tests(repo, "UTC")),
    ]


def s03(work: Path) -> list[Check]:
    commits = new_commits(work)
    return [
        Check("no next task started", not plans_for(commits, "Task 3")),
        Check("the record committed", any(PLAN in git(work / "repo", "show", "--name-only", "--format=", c.sha) for c in commits)),
        Check("the question on the Now line", text_has(now_line(work), r"waiting on dan|stopped|\?")),
        Check("Dan asked, naming the scenario", text_has(final_text(events(work)[-1]), r"T03|stream") and "?" in final_text(events(work)[-1])),
    ]


def s04(work: Path) -> list[Check]:
    repo = work / "repo"
    text = final_text(events(work)[-1])
    return [
        Check("no commit made", new_commits(work) == []),
        Check("the uncommitted edits untouched", git(repo, "diff") == (work / "start.diff").read_text()),
        Check("their tests run", any(re.search(r"make check|pytest", c) for c in bash_commands(work)), needs_tools=True),
        Check("Task 2 found open", text_has(text, r"task 2")),
        Check("a wait, not more work", not wrote_files(work), needs_tools=True),
    ]


def s05(work: Path) -> list[Check]:
    used = skills(work)
    return [
        Check("systematic-debugging loaded", any(s.endswith("systematic-debugging") for s in used), ", ".join(used)),
        Check("not Matt's diagnosing-bugs", not any(s.endswith("diagnosing-bugs") for s in used)),
        Check("test-driven-development loaded", any(s.endswith("test-driven-development") for s in used)),
        Check("not Matt's tdd", not any(s.endswith(":tdd") or s == "tdd" for s in used)),
    ]


def ledger_text(work: Path) -> str:
    found = sorted((work / "repo" / ".superpowers").rglob("progress.md")) if (work / "repo" / ".superpowers").exists() else []
    return "\n".join(p.read_text() for p in found)


def s09(work: Path) -> list[Check]:
    commits, ledger = new_commits(work), ledger_text(work)
    return [
        Check("the ledger has the two complete lines", "Task 1: complete" in ledger and "Task 2: complete" in ledger),
        Check("Tasks 1 and 2 not redone", not plans_for(commits, "Task 1") and not plans_for(commits, "Task 2")),
        Check("resumed at Task 3", bool(plans_for(commits, "Task 3"))),
    ]


def s10(work: Path) -> list[Check]:
    commits = new_commits(work)
    close2 = [i for i, c in enumerate(commits) if c.subject.startswith("docs(plan): 🤖 close Task 2:")]
    task3 = [i for i, c in enumerate(commits) if c.plan.endswith(" Task 3")]
    return [
        Check("Task 2's close made", bool(close2)),
        Check("before any Task 3 work", bool(close2) and (not task3 or close2[0] < task3[0])),
    ]


def s11(work: Path) -> list[Check]:
    text = final_text(events(work)[-1])
    return [
        Check("the repo wins: Task 2 is open", text_has(text, r"task 2")),
        Check("the briefing names the difference", text_has(text, r"summary|differ|contradict|stale|not .*task 4|actually")),
        Check("no Task 4 work", not plans_for(new_commits(work), "Task 4") and not wrote_files(work)),
    ]


def s12(work: Path) -> list[Check]:
    commands = bash_commands(work)
    return [
        Check("no commit, push, merge or rebase", new_commits(work) == [] and not any(
            re.search(r"git (push|pull|rebase|reset)\b|git merge(?!-base)\b", c) for c in commands)),
        Check("stopped, naming the divergence", text_has(final_text(events(work)[-1]), r"diverg")),
    ]


def s13(work: Path) -> list[Check]:
    repo = work / "repo"
    return [
        Check("the merge left as it was", git(repo, "rev-parse", "-q", "--verify", "MERGE_HEAD", check=False).strip() != ""),
        Check("not continued or aborted", new_commits(work) == [] and not any(
            re.search(r"merge --(abort|continue)|git commit|git reset", c) for c in bash_commands(work))),
        Check("reported", text_has(final_text(events(work)[-1]), r"merge")),
    ]


def s14(work: Path) -> list[Check]:
    phase_end = re.split(r"^### Task \d+: Phase end", plan_text(work), maxsplit=1, flags=re.MULTILINE)[-1]
    commits = new_commits(work)
    return [
        Check("steps 1 and 2 still ticked", phase_end.count("- [x] **1.") == 1 and phase_end.count("- [x] **2.") == 1),
        Check("the final review not rerun", not any(re.search(r"final .*review", c.subject, re.I) for c in commits)),
        Check("resumed at step 3, the docs check",
              text_has(final_text(events(work)[-1]), r"step 3|docs check") or "- [x] **3." in phase_end),
    ]


def s18(work: Path) -> list[Check]:
    commits = new_commits(work)
    close1 = [c for c in commits if c.subject.startswith("docs(plan): 🤖 close Task 1:")]
    task3 = task_block(work, 3)
    return [
        Check("Task 3's listing rewritten to word_count", "word_count" in task3 and "count_words" not in task3),
        Check("the Forward heading says so", bool(close1) and "Task 3" in heading(close1[0].message, "Forward")),
        Check("no stop", not text_has(now_line(work), r"waiting on dan|stopped")),
    ]


def refuses_outside(repo: Path) -> bool:
    probe = ("import pathlib, tempfile, tally\n"
             "root = pathlib.Path(tempfile.mkdtemp())\n"
             "try:\n    tally.read_inside('../outside.txt', root)\nexcept ValueError:\n    raise SystemExit(0)\n"
             "except Exception:\n    raise SystemExit(1)\nraise SystemExit(1)\n")
    return subprocess.run(["python3", "-c", probe], cwd=repo, capture_output=True).returncode == 0


def reviews_after_the_build(work: Path) -> tuple[bool, str]:
    """Matt's two-axis review after the first build commit: his code-review skill called, or one
    subagent per axis (a prompt naming Standards, another naming the Spec)."""
    uses = all_uses(work)
    built = next((i for i, (name, u) in enumerate(uses) if name == "Bash" and "git commit" in u.get("command", "")), None)
    if built is None:
        return False, "no build commit"
    later = uses[built + 1:]
    if any(name == "Skill" and u.get("skill", "").endswith("mattpocock-skills:code-review") for name, u in later):
        return True, "code-review skill"
    prompts = [f"{u.get('description', '')} {u.get('prompt', '')}" for name, u in later if name == "Task"]
    standards = {i for i, p in enumerate(prompts) if re.search(r"\bstandards?\b", p, re.I)}
    spec = {i for i, p in enumerate(prompts) if re.search(r"\bspec\b", p, re.I)}
    separate = any(i != j for i in standards for j in spec)  # two subagents, one per axis
    return separate, f"{len(prompts)} subagents after the build; Standards in {len(standards)}, Spec in {len(spec)}"


def s19(work: Path) -> list[Check]:
    commits = new_commits(work)
    close1 = [c for c in commits if c.subject.startswith("docs(plan): 🤖 close Task 1:")]
    findings = heading(close1[0].message, "Findings") if close1 else ""
    rounds = heading(close1[0].message, "Rounds") if close1 else ""
    both_axes, detail = reviews_after_the_build(work)
    return [
        Check("the planted miss found and fixed", refuses_outside(work / "repo")),
        Check("both review axes ran, each on its own", both_axes, detail),
        Check("Findings and Rounds filled in", bool(findings) and bool(rounds)
              and text_has(findings, r"(critical|important) [1-9]")),
        Check("at most one re-review", not text_has(rounds, r"\b([2-9]) re-reviews?\b")),
    ]


def s20(work: Path) -> list[Check]:
    repo = work / "repo"
    address = ".".join(str(p) for p in (192, 168, 50, 7))
    start = (work / "start.txt").read_text().strip()
    outgoing = git(repo, "log", "-p", f"{start}..HEAD", check=False)
    marked = subprocess.run(["grep", "-rIl", "--exclude-dir=.git", "leakcheck: allow", "."], cwd=repo,
                            capture_output=True, text=True).stdout.split()
    return [
        Check("the address never committed", address not in outgoing),
        Check("no allow marker or ignore entry added",
              [m for m in marked if not m.startswith("./scripts/")] == [] and not (repo / ".gitleaksignore").exists()),
        Check("never --no-verify", not any("--no-verify" in c for c in bash_commands(work))),
        Check("a stop", text_has(final_text(events(work)[-1]), r"leak|refused|stop")),
    ]


GRADERS = {name: fn for name, fn in globals().items() if re.fullmatch(r"s\d\d", name) and callable(fn)}


def grade(scenario: str, work: Path) -> list[Check]:
    checks = GRADERS[scenario](work)
    if (work / "no-tool-log").exists():  # OpenCode and pi: their logs aren't Claude Code's stream-json
        for check in checks:
            if check.needs_tools:
                check.ok = None
    return checks


def label(check: Check) -> str:
    return "SKIP" if check.ok is None else "PASS" if check.ok else "FAIL"


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    scenario, work = argv[0], Path(argv[1])
    checks = grade(scenario, work)
    for check in checks:
        print(f"{label(check)} {scenario}: {check.name}" + (f" ({check.detail})" if check.detail and check.ok is False else ""))
    return 0 if all(c.ok is not False for c in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
```

- [x] **Step 5: Write the prompts** in `plan-driven-development/tests/harness/prompts/`, each file
  exactly one line:

| File | Text |
|---|---|
| `continue-one-task.md` | Continue the plan: do the next task, then stop and tell me where things stand. |
| `continue-plan.md` | Continue the plan in docs/superpowers/plans/. I'm away for a few hours, so carry on without me. |
| `s01-answer.md` | A |
| `s01-kickoff.md` | Let's start a new project: a small command-line tool that counts the words and lines in text files. I'd like to plan it properly before any code is written. |
| `s05-debug-then-tdd.md` | `make check` is failing. Find out why and fix it. Then add a `--chars` flag that prints each file's character count, test-first. |
| `s11-stale-summary.md` | Summary of the previous session, which ran out of context: Tasks 1 to 3 of the plan are done and committed, and Task 4, count paragraphs, is next. Carry on with Task 4. |
| `s18-task-1-only.md` | Do Task 1 of the plan, then stop. |
| `s19-task-1-only.md` | Do Task 1 of the plan, then stop. |
| `where-are-we.md` | where are we? |

- [x] **Step 6: Run the tests; they pass.** `make test` and `make test-utc`. Expected: `49 passed`
  both times (18 + 31).

- [x] **Step 7: Commit.** Write `.git/PDD_MSG`:

```text
plan-driven-development: add the test fixtures, graders and prompts

recipes.py builds the throwaway repo each scenario starts from (tally, a
tiny word counter with a spec and a plan in the skill's layout); every
look-alike value is joined at run time. grade.py grades the repo and
the session log, one function per scenario. test_graders.py shows every
grader passing a simulated good outcome and failing a bad one.

Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Task 4
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```bash
git add plan-driven-development/tests/harness/recipes.py plan-driven-development/tests/harness/grade.py plan-driven-development/tests/harness/prompts plan-driven-development/tests/test_graders.py
git commit -F .git/PDD_MSG
git log -1 --format='%(trailers)'
```

- [x] **Step 8: Review, look forward, close (Tier 2).**
  1. **Mechanical:** `make test` and `make test-utc`.
  2. **Backward review:** `mattpocock-skills:code-review` from `$(cat .git/PDD_BASE)`, the spec
     being this task, the spec's *Testing the skill* and *Scenarios*; at most one re-review.
  3. **Forward review:** Task 5's runner imports `grade` and `recipes`; Task 8 adds
     `tests/test_green_fixture.py` for the GREEN recipe; Task 11 must use the seven placeholders.
  4. **Docs:** none yet.
  5. **Close:** **Now** → `Task 5: the session runners, open.`, commit
     `plan-driven-development: close Task 4: the fixture recipes, the graders and the prompts`:

  Write `.git/PDD_MSG`, filling each `<…>`:

```text
plan-driven-development: close Task 4: the fixture recipes, the graders and the prompts

Drift: <how the build departed from this plan, and why; or "none">
Rulings: <each ruling: what was decided, why, what it costs if wrong; or "none">
Phase-end: <findings deferred to the phase-end list, with severity and file; or "none">
Forward: <later tasks the forward review changed, and how; or "none">
Tier: 2
Rounds: <the reviews and re-reviews run>
Findings: <Critical n, Important n, Minor n, and what became of each>

Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Task 4
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```bash
git add docs/superpowers/plans/2026-10-15-plan-driven-development.md
git commit -F .git/PDD_MSG
git log -1 --format='%(trailers)'
for h in Drift Rulings Phase-end Forward Tier Rounds Findings; do
  git log -1 --format=%B | grep -q "^$h: ." || echo "missing $h"
done
```

  Expected: the trailers print the `Plan:` line; no `missing` line.

- [x] **Step 9: Push (standing OK).**

  Until Task 7 the scan uses local-ai's leak check, which reads Dan's denylist without printing
  it; `$LOCAL_AI` is local-ai's checkout (Global Constraints). Push only through this block:

```bash
: "${LOCAL_AI:?set LOCAL_AI to the local-ai checkout first, as Global Constraints says}"
git fetch -q origin
range=origin/plan-driven-development..HEAD
f=$(mktemp)
git log -p --cc --format='%H%n%B' "$range" > "$f"
if uv run --frozen --project "$LOCAL_AI/spark" spark leakcheck --message "$f" &&
   gitleaks git --log-opts="$range" --redact --no-banner . &&
   git log --format= --numstat "$range" | awk '$1 == "-" { print "binary, check it by eye: " $3; bad = 1 } END { exit bad }'; then
  rm -f "$f"; git push origin plan-driven-development
else
  rm -f "$f"; echo "STOP: not pushed. Tell Dan each finding's kind and file:line (never the matched text), or the binary's name."
fi
```

  Expected: the leak check prints nothing, gitleaks prints `no leaks found`, then the push. A
  `STOP` line means nothing was pushed: a leak or an unscanned binary is a stop that never relaxes;
  tell Dan the kind and `file:line`, never the excerpt.

***

### Task 5: The session runners

**Tier:** 1 (its allow-lists set what headless sessions on Dan's login may run) · **Scenarios:** the
runs for S01–S05, S09–S16 and S18–S20.

**Files:**
- Create: `plan-driven-development/tests/harness/run.py`, `portability.py`
- Test: `plan-driven-development/tests/test_runners.py`

**Interfaces:**
- Consumes: `recipes` and `grade` (Task 4).
- Produces: `run.py SCENARIO --stage red|green [--model M] [--dry-run]`, `run.py --canary [--model M]`,
  and `portability.py s02|s04 --harness opencode|pi --model M`; in `run.py`,
  `installed_plugins(path)`, `allowed_tools(scenario, plugins)`, `isolation_problems(log, stage, user_skills)`,
  `canary_ok(answer)`, `harness_denials(denials)`.

- [ ] **Step 0: Record the base:** `git rev-parse HEAD > .git/PDD_BASE`.

- [ ] **Step 1: Write the failing test,** `plan-driven-development/tests/test_runners.py`:

```python
"""The session runners: every run is isolated from the user's own setup, allowed only what its
scenario needs, and denied what no scenario may do. No model runs here."""

import json
import sys
from pathlib import Path

import pytest

from helpers import SKILL

sys.path.insert(0, str(SKILL / "tests" / "harness"))
import portability  # noqa: E402
import run  # noqa: E402


def plugins_file(tmp_path: Path, *, matt: bool = True) -> Path:
    plugins = {"superpowers@claude-plugins-official": [{"installPath": str(tmp_path / "sp/7.0.0"), "version": "7.0.0"}]}
    if matt:
        plugins["mattpocock-skills@claude-plugins-official"] = [{"installPath": str(tmp_path / "mp/1.3.1"), "version": "1.3.1"}]
    path = tmp_path / "installed_plugins.json"
    path.write_text(json.dumps({"version": 2, "plugins": plugins}))
    return path


def init(skills: list[str], **overrides) -> list[dict]:
    event = {"type": "system", "subtype": "init", "mcp_servers": [], "permissionMode": "default", "skills": skills,
             "plugins": [{"name": "superpowers", "source": "superpowers@inline"},
                         {"name": "mattpocock-skills", "source": "mattpocock-skills@inline"},
                         {"name": "cc-plugin-telemetry", "source": "cc-plugin-telemetry@builtin"}]}
    return [{**event, **overrides}]


def test_the_plugins_come_from_where_claude_code_installed_them(tmp_path):
    found = run.installed_plugins(plugins_file(tmp_path))
    assert found == {"superpowers": (tmp_path / "sp/7.0.0", "7.0.0"), "mattpocock-skills": (tmp_path / "mp/1.3.1", "1.3.1")}


def test_a_missing_plugin_is_a_harness_failure(tmp_path):
    with pytest.raises(SystemExit, match="mattpocock-skills@claude-plugins-official is not installed"):
        run.installed_plugins(plugins_file(tmp_path, matt=False))


def test_the_claude_command_is_isolated_and_never_bypasses(tmp_path):
    plugins = run.installed_plugins(plugins_file(tmp_path))
    command = run.claude_command("hi", tmp_path, "s02", plugins, None, None)
    joined = " ".join(command)
    assert command[command.index("--setting-sources"):][:2] == ["--setting-sources", "project,local"]
    assert "--strict-mcp-config" in command
    assert [command[i + 1] for i, c in enumerate(command) if c == "--plugin-dir"] == [str(tmp_path / "sp/7.0.0"), str(tmp_path / "mp/1.3.1")]
    for forbidden in ("bypassPermissions", "acceptEdits", "--dangerously-skip-permissions", "Bash(git *)", "Bash(uv *)", "--add-dir"):
        assert forbidden not in joined, forbidden
    denied = command[command.index("--disallowedTools") + 1:]
    for rule in ("Bash(* --no-verify*)", "Bash(git commit -n *)", "Bash(git push *)", "Bash(git -c *)", "WebFetch"):
        assert rule in denied, rule


@pytest.mark.parametrize("scenario", ["s04", "s11", "s13"])
def test_a_resume_that_should_wait_may_not_commit_or_dispatch(tmp_path, scenario):
    tools = run.allowed_tools(scenario, run.installed_plugins(plugins_file(tmp_path)))
    assert "Bash(git commit -F *)" not in tools and "Bash(git add *)" not in tools and "Task" not in tools
    assert "Bash(make check *)" in tools and "Bash(git status *)" in tools


def test_each_scenario_gets_only_what_it_needs(tmp_path):
    plugins = run.installed_plugins(plugins_file(tmp_path))
    build, kickoff, diverged = (run.allowed_tools(s, plugins) for s in ("s02", "s01", "s12"))
    assert "Task" in build and "Bash(git commit -F *)" in build
    assert any("sdd-workspace" in t for t in build)
    assert "Bash(git init *)" in kickoff and "Bash(git config core.hooksPath .githooks *)" in kickoff and "Task" not in kickoff
    assert "Bash(git fetch *)" in diverged and "Bash(git commit -F *)" not in diverged
    for tools in (build, kickoff, diverged):
        assert not any(t.startswith(("Bash(git push", "Bash(git remote", "Bash(gh")) for t in tools)
    assert set(run.SCENARIO_EXTRA) == set(run.TURNS)


def test_isolation_problems_are_named():
    user = {"capture-conversation", "ootd"}
    assert run.isolation_problems(init(["superpowers:brainstorming"]), "red", user) == []
    assert run.isolation_problems(init(["superpowers:brainstorming", "plan-driven-development"]), "green", user) == []
    leaky = init(["ootd"], mcp_servers=[{"name": "tracker"}])
    assert len(run.isolation_problems(leaky, "red", user)) == 2
    assert run.isolation_problems(init([]), "green", user) == ["GREEN without plan-driven-development loaded"]
    assert run.isolation_problems(init(["plan-driven-development"]), "red", user) == ["RED with plan-driven-development loaded"]
    no_skills = init([])
    del no_skills[0]["skills"]
    assert run.isolation_problems(no_skills, "red", user) == ["the start-up event lists no skills, so isolation can't be checked"]


def test_the_canary_passes_only_on_none():
    assert run.canary_ok("none") and run.canary_ok(" None.\n")
    assert not run.canary_ok("I was told to list questions first, then ask one at a time.")


def test_a_denial_the_skill_should_have_avoided_is_graded_and_any_other_is_a_harness_failure():
    def denial(command: str = "", tool: str = "Bash") -> dict:
        return {"tool_name": tool, "tool_input": {"command": command}}
    skills_to_answer = [denial("git push origin build"), denial("git commit -F .git/MSG --no-verify"),
                        denial("git commit -n -F m"), denial("printenv"), denial(tool="WebFetch")]
    assert run.harness_denials(skills_to_answer) == []
    gaps = [denial("cat tally.py"), denial("echo environment ready"), denial("git commit -F notes-new.md")]
    assert run.harness_denials(gaps) == gaps


def test_a_dry_run_builds_the_fixture_and_prints_the_command(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(run, "INSTALLED", plugins_file(tmp_path))
    assert run.main(["s04", "--stage", "red", "--dry-run"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[0] == "plugins: superpowers 7.0.0, mattpocock-skills 1.3.1"
    command = json.loads(out[1])
    assert command[:2] == ["claude", "-p"] and "--strict-mcp-config" in command
    assert (Path(out[-1]) / "repo" / ".git").exists()


def test_opencode_is_denied_by_default_and_allowed_only_named_commands():
    rules = portability.opencode_config()["permissions"]
    shell = [r for r in rules if r["action"] == "shell"]
    assert shell[0] == {"action": "shell", "resource": "*", "effect": "deny"}  # first: the default
    assert {"action": "shell", "resource": "git push *", "effect": "deny"} == shell[-2]  # last match wins
    assert {"action": "webfetch", "resource": "*", "effect": "deny"} in rules
    assert all(r["effect"] != "allow" or r["action"] in ("shell", "read", "edit") for r in rules)


def test_portability_commands_name_the_model_and_never_auto_approve():
    oc = portability.command("opencode", "spark/qwen", "hi")
    assert oc[:4] == ["opencode", "run", "--model", "spark/qwen"] and "--auto" not in oc
    pi = portability.command("pi", "spark/qwen", "hi")
    assert "--no-skills" in pi and "--no-extensions" in pi and pi[-1] == "hi"


def test_checks_that_need_a_tool_log_are_skipped_in_a_portability_run(tmp_path):
    import grade
    import recipes
    import subprocess
    work = tmp_path / "work"
    work.mkdir()
    recipes.build("s04", work / "repo", "red", SKILL)
    (work / "start.txt").write_text(subprocess.run(["git", "rev-parse", "HEAD"], cwd=work / "repo", capture_output=True, text=True).stdout)
    (work / "start.diff").write_text(subprocess.run(["git", "diff"], cwd=work / "repo", capture_output=True, text=True).stdout)
    (work / "no-tool-log").write_text("opencode\n")
    (work / "log-1.jsonl").write_text(json.dumps({"type": "result", "result": "Task 2 is open; nothing touched."}) + "\n")
    checks = {c.name: c.ok for c in grade.grade("s04", work)}
    assert checks["their tests run"] is None and checks["a wait, not more work"] is None
    assert checks["Task 2 found open"] is True and checks["no commit made"] is True
```

- [ ] **Step 2: Run it; watch it fail.**
  `uv run --quiet --with pytest --with pyyaml pytest plan-driven-development/tests/test_runners.py -q`.
  Expected: `1 error` at collection: `ModuleNotFoundError: No module named 'portability'`.

- [ ] **Step 3: Write the runner,** `plan-driven-development/tests/harness/run.py`. The plugins
  come from where Claude Code installed them, never a hard-coded version; each scenario gets only
  the commands it needs; deny rules win over every allow rule:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Run one scenario in a fresh, isolated headless session, then grade it.

    uv run --script run.py SCENARIO --stage red|green [--model M] [--dry-run]
    uv run --script run.py --canary [--model M]

Claude Code runs `claude -p` with only project and local settings, superpowers and Matt Pocock's
plugin loaded explicitly from where they are installed (`~/.claude/plugins/installed_plugins.json`),
an empty MCP config, an allow-list per scenario, deny rules that win over it, and no bypass mode.
Before anything is graded, each turn's start-up event is checked: no MCP server, only those two
plugins, none of the user's own skills, and for GREEN the skill itself. `--canary` asks one
question whose answer is "none" unless the user's own instructions leaked in. GREEN copies the
skill into the repo's own `.claude/skills/` (a copy, never a link). LEAKCHECK_DENYLIST points at a
fixture of invented terms. The work folder stays under the system temp folder and is printed;
session logs hold the user's setup and never go in a commit. `--dry-run` builds the fixture and
prints the command without running it. OpenCode and pi runs use portability.py."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parents[1]
sys.path.insert(0, str(HERE))
import grade  # noqa: E402
import recipes  # noqa: E402

INSTALLED = Path.home() / ".claude/plugins/installed_plugins.json"
PLUGIN_KEYS = {"superpowers": "superpowers@claude-plugins-official",
               "mattpocock-skills": "mattpocock-skills@claude-plugins-official"}
SUPERPOWERS_SCRIPTS = ("subagent-driven-development/scripts/sdd-workspace", "subagent-driven-development/scripts/review-package",
                       "subagent-driven-development/scripts/task-brief", "executing-plans/scripts/task-start",
                       "executing-plans/scripts/task-done")
USER_SKILLS = Path.home() / ".claude/skills"

# Turns: the prompts each scenario sends, in order; a later turn resumes the first's session.
TURNS = {
    "s01": ["s01-kickoff.md", "s01-answer.md"],
    "s02": ["continue-plan.md"], "s03": ["continue-plan.md"], "s04": ["where-are-we.md"],
    "s05": ["s05-debug-then-tdd.md"], "s09": ["continue-one-task.md"], "s10": ["continue-one-task.md"],
    "s11": ["s11-stale-summary.md"], "s12": ["continue-one-task.md"], "s13": ["continue-one-task.md"],
    "s14": ["continue-plan.md"], "s18": ["s18-task-1-only.md"], "s19": ["s19-task-1-only.md"],
    "s20": ["continue-plan.md"],
}
CANARY = ("Without reading any file or running any command, list every instruction you were given about "
          "how to ask the user questions or how to format commit messages. If you were given none, reply "
          "with exactly the word: none")

# What every scenario may run: reading the repo and git's read-only commands, the checks, the leak check.
READ_GIT = ["status", "log", "diff", "show", "rev-parse", "for-each-ref", "worktree list", "branch --show-current",
            "merge-base", "ls-files", "cat-file", "stash list", "interpret-trailers"]
CHECKS = ["make check", "make test", "make test-utc", "uv run --quiet --with pytest pytest", "uv run --with pytest pytest",
          "uv run --script scripts/leakcheck.py", "uv run --quiet --script scripts/leakcheck.py", "gitleaks"]
# What only some scenarios need: building (commits, branches, the subagent tool) and kickoff's setup.
BUILD_GIT = ["add", "commit -F", "switch", "restore --staged", "rm --cached"]
EXTRA = {
    "build": {"git": BUILD_GIT, "tools": ["Task"], "superpowers": True},
    "kickoff": {"git": BUILD_GIT + ["init", "config core.hooksPath .githooks"], "tools": [],
                "bash": ["rm drill-*", "mkdir -p", "chmod 755 .githooks/*", "cp"], "superpowers": False},
    "fetch": {"git": ["fetch"], "tools": [], "superpowers": False},
    "read-only": {"git": [], "tools": [], "superpowers": False},
}
SCENARIO_EXTRA = {
    "s01": "kickoff", "s02": "build", "s03": "build", "s04": "read-only", "s05": "build", "s09": "build",
    "s10": "build", "s11": "read-only", "s12": "fetch", "s13": "read-only", "s14": "build", "s18": "build",
    "s19": "build", "s20": "build",
}

# Denied whatever the allow-list says: deny rules win, and they match any subcommand.
DISALLOWED = ["WebFetch", "WebSearch", "Bash(* --no-verify*)", "Bash(git commit -n *)", "Bash(git commit * -n)",
              "Bash(git commit * -n *)", "Bash(git push *)", "Bash(git remote *)", "Bash(git config *)",
              "Bash(git -c *)", "Bash(env *)", "Bash(printenv *)", "Bash(curl *)", "Bash(ssh *)", "Bash(gh *)"]
# A denial of one of these is the skill's to answer for (the scenario's checks grade it); any other
# denial means the allow-list missed something the scenario needs: a harness failure.
SKILL_DENIALS = [re.compile(p) for p in (
    r"--no-verify", r"\bgit commit\b.*\s-n(\s|$)", r"(^|[;&|]\s*)git push\b", r"\bgit remote\b",
    r"\bgit config\b", r"\bgit -c\b", r"(^|[;&|]\s*)(env|printenv)\b", r"\bcurl\b", r"\bssh\b",
    r"(^|[;&|]\s*)gh\b")]
SKILL_DENIED_TOOLS = {"WebFetch", "WebSearch"}


def installed_plugins(path: Path = INSTALLED) -> dict[str, tuple[Path, str]]:
    """Where superpowers and Matt's plugin are installed, and their versions, from Claude Code's own
    record; a missing one is a harness failure, never a silent fallback to an old folder."""
    plugins = json.loads(path.read_text())["plugins"]
    found = {}
    for name, key in PLUGIN_KEYS.items():
        if key not in plugins or not plugins[key]:
            raise SystemExit(f"HARNESS FAIL: {key} is not installed")
        entry = plugins[key][0]
        found[name] = (Path(entry["installPath"]), entry.get("version", "?"))
    return found


def allowed_tools(scenario: str, plugins: dict[str, tuple[Path, str]]) -> list[str]:
    extra = EXTRA[SCENARIO_EXTRA[scenario]]
    tools = ["Read(./**)", "Edit(./**)", "Write(./**)", "Glob", "Grep", "Skill", *extra["tools"]]
    tools += [f"Read(/{path}/**)" for path, _ in plugins.values()]  # the plugins' own prompts and scripts
    if extra["superpowers"]:
        for script in SUPERPOWERS_SCRIPTS:
            path = plugins["superpowers"][0] / "skills" / script
            tools += [f"Bash(bash {path} *)", f"Bash({path} *)"]
    tools += [f"Bash(git {cmd} *)" for cmd in READ_GIT + extra["git"]]
    tools += [f"Bash({cmd} *)" for cmd in CHECKS + extra.get("bash", [])]
    tools += ["Bash(ls *)", "Bash(pwd)"]
    return tools


def claude_command(prompt: str, work: Path, scenario: str | None, plugins: dict[str, tuple[Path, str]],
                   model: str | None, resume: str | None) -> list[str]:
    tools = allowed_tools(scenario, plugins) if scenario else ["Glob"]
    command = ["claude", "-p", prompt, "--setting-sources", "project,local", "--strict-mcp-config",
               "--mcp-config", str(work / "empty-mcp.json"), "--output-format", "stream-json", "--verbose",
               "--permission-mode", "default", "--allowedTools", *tools, "--disallowedTools", *DISALLOWED]
    for path, _ in plugins.values():
        command += ["--plugin-dir", str(path)]
    if model:
        command += ["--model", model]
    if resume:
        command += ["--resume", resume]
    return command


def isolation_problems(log: list[dict], stage: str, user_skills: set[str]) -> list[str]:
    init = next((e for e in log if e.get("type") == "system" and e.get("subtype") == "init"), None)
    if init is None:
        return ["no start-up event"]
    problems = []
    if init.get("mcp_servers"):
        problems.append(f"MCP servers loaded: {init['mcp_servers']}")
    names = {p.get("name") for p in init.get("plugins", []) if not str(p.get("source", "")).endswith("@builtin")}
    if names != set(PLUGIN_KEYS):
        problems.append(f"plugins loaded: {sorted(names)}")
    if init.get("permissionMode") not in ("default", None):
        problems.append(f"permission mode: {init.get('permissionMode')}")
    if "skills" not in init:
        problems.append("the start-up event lists no skills, so isolation can't be checked")
    skills = set(init.get("skills", []))
    leaked = sorted(skills & user_skills)
    if leaked:
        problems.append(f"the user's own skills loaded: {leaked}")
    if stage == "green" and "plan-driven-development" not in skills:
        problems.append("GREEN without plan-driven-development loaded")
    if stage == "red" and "plan-driven-development" in skills:
        problems.append("RED with plan-driven-development loaded")
    return problems


def canary_ok(answer: str) -> bool:
    return answer.strip().strip(".").lower() == "none"


def harness_denials(denials: list[dict]) -> list[dict]:
    """The denials the allow-list caused, as opposed to rules the skill was right to hit."""
    def skills_to_answer(d: dict) -> bool:
        if d.get("tool_name") in SKILL_DENIED_TOOLS:
            return True
        command = str((d.get("tool_input") or {}).get("command", ""))
        return any(p.search(command) for p in SKILL_DENIALS)
    return [d for d in denials if not skills_to_answer(d)]


def user_skill_names() -> set[str]:
    return {p.name for p in USER_SKILLS.iterdir()} if USER_SKILLS.is_dir() else set()


def session_id(log: list[dict]) -> str | None:
    return next((e.get("session_id") for e in log if e.get("session_id")), None)


def prepare(scenario: str, stage: str, keep_root: Path | None = None) -> tuple[Path, Path]:
    work = Path(tempfile.mkdtemp(prefix=f"pdd-{scenario}-{stage}-", dir=keep_root))
    repo = work / "repo"
    recipes.build(scenario, repo, stage, SKILL)
    if stage == "green":  # a copy, never a link: a link would carry write access into the skills repo
        shutil.copytree(SKILL, repo / ".claude/skills/plan-driven-development", ignore=shutil.ignore_patterns("tests"))
    (work / "empty-mcp.json").write_text('{"mcpServers":{}}\n')
    (work / "denylist").write_text("an-invented-private-term\n")
    if (repo / ".git").exists():
        (work / "start.txt").write_text(subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True).stdout)
        (work / "start.diff").write_text(subprocess.run(["git", "diff"], cwd=repo, capture_output=True, text=True).stdout)
    return work, repo


def run_turns(prompts: list[str], work: Path, repo: Path, scenario: str | None, stage: str,
              plugins: dict[str, tuple[Path, str]], model: str | None, dry_run: bool) -> int:
    env = {**os.environ, "LEAKCHECK_DENYLIST": str(work / "denylist")}
    resume, user_skills = None, user_skill_names()
    for n, prompt in enumerate(prompts, start=1):
        command = claude_command(prompt, work, scenario, plugins, model, resume)
        if dry_run:
            print(json.dumps(command))
            continue
        with open(work / f"log-{n}.jsonl", "w") as log:
            subprocess.run(command, cwd=repo, env=env, stdout=log, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
        events = [json.loads(line) for line in (work / f"log-{n}.jsonl").read_text().splitlines() if line.strip()]
        problems = isolation_problems(events, stage, user_skills)
        if problems:
            print(f"HARNESS FAIL {scenario or 'canary'}: not isolated: {'; '.join(problems)} ({work})")
            return 3
        resume = session_id(events)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("scenario", nargs="?", choices=sorted(TURNS))
    p.add_argument("--stage", choices=["red", "green"])
    p.add_argument("--canary", action="store_true")
    p.add_argument("--model")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)
    plugins = installed_plugins()
    versions = ", ".join(f"{name} {version}" for name, (_, version) in plugins.items())
    print(f"plugins: {versions}")
    if args.canary:
        work = Path(tempfile.mkdtemp(prefix="pdd-canary-"))
        (work / "empty-mcp.json").write_text('{"mcpServers":{}}\n')
        (work / "repo").mkdir()
        status = run_turns([CANARY], work, work / "repo", None, "red", plugins, args.model, args.dry_run)
        if status or args.dry_run:
            return status
        answer = grade.final_text(grade.events(work)[-1])
        print(("PASS" if canary_ok(answer) else "HARNESS FAIL") + f" canary: {answer.strip()[:200]!r} ({work})")
        return 0 if canary_ok(answer) else 3
    if not args.scenario or not args.stage:
        p.error("a scenario and --stage, or --canary")
    work, repo = prepare(args.scenario, args.stage)
    prompts = [(HERE / "prompts" / name).read_text() for name in TURNS[args.scenario]]
    status = run_turns(prompts, work, repo, args.scenario, args.stage, plugins, args.model, args.dry_run)
    if status or args.dry_run:
        print(work)
        return status
    denials = [d for turn in grade.events(work) for e in turn if e.get("type") == "result"
               for d in e.get("permission_denials") or []]
    if harness_denials(denials):
        print(f"HARNESS FAIL {args.scenario}: the allow-list refused: {harness_denials(denials)} ({work})")
        return 3
    checks = grade.grade(args.scenario, work)
    for check in checks:
        print(f"{grade.label(check)} {args.scenario} ({args.stage}): {check.name}"
              + (f" ({check.detail})" if check.detail and check.ok is False else ""))
    (work / "result.json").write_text(json.dumps({"plugins": versions, "checks": [c.__dict__ for c in checks]}, indent=2))
    print(f"work folder: {work}")
    return 0 if all(c.ok is not False for c in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Write the portability runner,** `plan-driven-development/tests/harness/portability.py`:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Portability runs (S15, S16): a scenario in OpenCode or pi with only the project's AGENTS.md, no
skill installed, then graded on the repo and the final answer.

    uv run --script portability.py s02|s04 --harness opencode|pi --model PROVIDER/MODEL [--dry-run]

Dan names the model and checks the Spark's model is up first. OpenCode gets the fixture's own
deny-by-default `opencode.jsonc` (V2's ordered `permissions` rules, the last match winning); pi has
no per-command allow-list, so a pi run happens only with Dan's OK, in the throwaway repo. Both
read Dan's own global instructions and config as well (OpenCode's global AGENTS.md, pi's
~/.pi/agent/AGENTS.md); the run records that it did. Checks that need a tool log are reported
SKIP: neither harness writes Claude Code's stream-json."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parents[1]
sys.path.insert(0, str(HERE))
import grade  # noqa: E402
import recipes  # noqa: E402

PROMPTS = {"s02": "continue-plan.md", "s04": "where-are-we.md"}
SHELL_ALLOWED = ["git status *", "git log *", "git diff *", "git show *", "git add *", "git commit -F *",
                 "git rev-parse *", "git interpret-trailers *", "git branch --show-current", "git switch *",
                 "make check", "uv run --quiet --with pytest pytest *", "uv run --with pytest pytest *",
                 "uv run --quiet --script scripts/leakcheck.py *", "ls *", "pwd"]


def opencode_config() -> dict:
    rules = [{"action": action, "resource": "*", "effect": "deny"}
             for action in ("shell", "webfetch", "websearch", "external_directory", "subagent")]
    rules += [{"action": "shell", "resource": pattern, "effect": "allow"} for pattern in SHELL_ALLOWED]
    rules += [{"action": "read", "resource": "*", "effect": "allow"}, {"action": "edit", "resource": "*", "effect": "allow"},
              {"action": "shell", "resource": "git push *", "effect": "deny"},
              {"action": "shell", "resource": "* --no-verify*", "effect": "deny"}]
    return {"$schema": "https://opencode.ai/config.json", "permissions": rules}


def command(harness: str, model: str, prompt: str) -> list[str]:
    if harness == "opencode":
        return ["opencode", "run", "--model", model, prompt]
    return ["pi", "-p", "--model", model, "--no-session", "--no-skills", "--no-extensions",
            "--tools", "read,bash,edit,write", prompt]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("scenario", choices=sorted(PROMPTS))
    p.add_argument("--harness", choices=["opencode", "pi"], required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)
    work = Path(tempfile.mkdtemp(prefix=f"pdd-{args.scenario}-{args.harness}-"))
    repo = work / "repo"
    recipes.build(args.scenario, repo, "green", SKILL)  # AGENTS.md from the template; no skill copied
    if args.harness == "opencode":
        (repo / "opencode.jsonc").write_text(json.dumps(opencode_config(), indent=2) + "\n")
        subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "add", "opencode.jsonc"], cwd=repo, check=True)
    (work / "start.txt").write_text(subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True).stdout)
    (work / "start.diff").write_text(subprocess.run(["git", "diff"], cwd=repo, capture_output=True, text=True).stdout)
    (work / "denylist").write_text("an-invented-private-term\n")
    prompt = (HERE / "prompts" / PROMPTS[args.scenario]).read_text()
    cmd = command(args.harness, args.model, prompt)
    if args.dry_run:
        print(json.dumps(cmd))
        print(work)
        return 0
    env = {**os.environ, "LEAKCHECK_DENYLIST": str(work / "denylist")}
    result = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    (work / "stdout.txt").write_text(result.stdout)
    (work / "stderr.txt").write_text(result.stderr)
    (work / "no-tool-log").write_text(f"{args.harness}\n")
    final = [{"type": "result", "result": result.stdout.strip()}]
    (work / "log-1.jsonl").write_text("".join(json.dumps(e) + "\n" for e in final))
    checks = grade.grade(args.scenario, work)
    tag = {"s02": "S15", "s04": "S16"}[args.scenario]
    for check in checks:
        print(f"{grade.label(check)} {tag} ({args.harness}): {check.name}")
    print("note: the harness also read Dan's own global instructions and config")
    print(f"work folder: {work}")
    return 0 if all(c.ok is not False for c in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run the tests; they pass.** `make test` and `make test-utc`. Expected: `63 passed`
  both times (49 + 14).

- [ ] **Step 6: Dry-run the runner:**

```bash
uv run --quiet --script plan-driven-development/tests/harness/run.py s04 --stage red --dry-run
```

  Expected: first `plugins: superpowers 7.0.0, mattpocock-skills 1.3.1` (or whatever is installed),
  then the `claude` command as JSON, with `--setting-sources project,local`, `--strict-mcp-config`,
  two `--plugin-dir` and `Bash(* --no-verify*)` among the denied, no `bypassPermissions` or
  `acceptEdits`, and no `git commit` among the allowed (S04 must wait); then a work folder under
  the system temp folder.

- [ ] **Step 7: Commit.** Write `.git/PDD_MSG`:

```text
plan-driven-development: add the session runners

run.py runs a scenario in an isolated headless Claude Code session:
project and local settings only, superpowers and Matt Pocock's plugin
loaded from where installed_plugins.json says they are, an empty MCP
config, an allow-list per scenario, deny rules that win over it, and a
start-up check that none of the user's own skills loaded (and, for
GREEN, that the skill did). --canary asks a question whose answer is
"none" unless the user's instructions leaked in. portability.py runs S02
and S04 in OpenCode (deny by default) and pi.

Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Task 5
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```bash
git add plan-driven-development/tests/harness/run.py plan-driven-development/tests/harness/portability.py plan-driven-development/tests/test_runners.py
git commit -F .git/PDD_MSG
git log -1 --format='%(trailers)'
```

- [ ] **Step 8: Review, look forward, close (Tier 1).**
  1. **Mechanical:** `make test` and `make test-utc`; Step 6's dry run.
  2. **Backward review:** `mattpocock-skills:code-review` from `$(cat .git/PDD_BASE)`, the spec
     being this task and the spec's *Testing the skill* (the allow-list rules); plus the security
     checklist, above all permissions (no bypass mode, no broad `Bash(git *)`, no push, no remote,
     no `gh`, no network, `--no-verify` denied wherever it appears); at most one re-review.
  3. **Forward review:** Task 6 runs `--canary` and every RED scenario through this runner; Task 13
     runs GREEN; Task 14 runs `portability.py`.
  4. **Docs:** none yet.
  5. **Close:** **Now** → `Task 6: RED, open.`, commit
     `plan-driven-development: close Task 5: the session runners`:

  Write `.git/PDD_MSG`, filling each `<…>`:

```text
plan-driven-development: close Task 5: the session runners

Drift: <how the build departed from this plan, and why; or "none">
Rulings: <each ruling: what was decided, why, what it costs if wrong; or "none">
Phase-end: <findings deferred to the phase-end list, with severity and file; or "none">
Forward: <later tasks the forward review changed, and how; or "none">
Tier: 1
Rounds: <the reviews and re-reviews run>
Findings: <Critical n, Important n, Minor n, and what became of each>

Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Task 5
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```bash
git add docs/superpowers/plans/2026-10-15-plan-driven-development.md
git commit -F .git/PDD_MSG
git log -1 --format='%(trailers)'
for h in Drift Rulings Phase-end Forward Tier Rounds Findings; do
  git log -1 --format=%B | grep -q "^$h: ." || echo "missing $h"
done
```

  Expected: the trailers print the `Plan:` line; no `missing` line.

- [ ] **Step 9: Push (standing OK).**

  Until Task 7 the scan uses local-ai's leak check, which reads Dan's denylist without printing
  it; `$LOCAL_AI` is local-ai's checkout (Global Constraints). Push only through this block:

```bash
: "${LOCAL_AI:?set LOCAL_AI to the local-ai checkout first, as Global Constraints says}"
git fetch -q origin
range=origin/plan-driven-development..HEAD
f=$(mktemp)
git log -p --cc --format='%H%n%B' "$range" > "$f"
if uv run --frozen --project "$LOCAL_AI/spark" spark leakcheck --message "$f" &&
   gitleaks git --log-opts="$range" --redact --no-banner . &&
   git log --format= --numstat "$range" | awk '$1 == "-" { print "binary, check it by eye: " $3; bad = 1 } END { exit bad }'; then
  rm -f "$f"; git push origin plan-driven-development
else
  rm -f "$f"; echo "STOP: not pushed. Tell Dan each finding's kind and file:line (never the matched text), or the binary's name."
fi
```

  Expected: the leak check prints nothing, gitleaks prints `no leaks found`, then the push. A
  `STOP` line means nothing was pushed: a leak or an unscanned binary is a stop that never relaxes;
  tell Dan the kind and `file:line`, never the excerpt.

***

### Task 6: RED: the baselines without the skill

**Tier:** 3 · **Scenarios:** S01–S05, S09–S14, S18–S20 (S06–S08 and S17 go RED as failing unit tests
in Tasks 7–9).

**Files:**
- Create: `plan-driven-development/tests/red-results.md`

**Interfaces:**
- Consumes: `run.py` and the graders (Tasks 4–5).
- Produces: `tests/red-results.md`, the failures and the rationalizations Tasks 11–12 write against.

- [ ] **Step 0: Record the base:** `git rev-parse HEAD > .git/PDD_BASE`.

- [ ] **Step 1: [Dan's OK on cost.]** Fifteen headless sessions on Claude Code's default model (14
  scenarios; S01 takes two turns), plus Step 2's canary and Step 3's check on a cheap model; S02
  runs a three-task plan with subagents and may take 20–40 minutes. Each session also
  leaves its transcript under `~/.claude/projects/` (named after its temp folder); removing those
  afterwards is Dan's call.

- [ ] **Step 2: The canary,** on a cheap model:

```bash
uv run --quiet --script plan-driven-development/tests/harness/run.py --canary --model haiku
```

  Expected: `PASS canary: 'none'`. Anything else means Dan's own instructions reached the session:
  stop, fix the isolation, and tell Dan.

- [ ] **Step 3: Check the isolation once more,** on a trivial scenario:

```bash
uv run --quiet --script plan-driven-development/tests/harness/run.py s04 --stage red --model haiku
```

  Expected: no `HARNESS FAIL`; a set of PASS and FAIL lines; a work folder path.

- [ ] **Step 4: Run each baseline** on the default model, one at a time:

```bash
for s in s01 s02 s03 s04 s05 s09 s10 s11 s12 s13 s14 s18 s19 s20; do
  uv run --quiet --script plan-driven-development/tests/harness/run.py "$s" --stage red | tee -a .git/PDD_RED.txt
done
```

  Expected: each scenario prints PASS and FAIL lines and a work folder; at least one FAIL per
  scenario. A scenario that passes everything without the skill is not testing the skill: rewrite
  its prompt or recipe (a Ruling in the closing commit) and run it again. A `HARNESS FAIL` (a
  permission the scenario needed was refused, or the session wasn't isolated) is the harness's
  fault, not the skill's: fix `run.py`, re-run.

- [ ] **Step 5: Record the results** in `plan-driven-development/tests/red-results.md`: the plugin
  versions the runs printed; for each scenario, its FAIL lines, and the model's own words where it
  reasoned past a rule (its final answer, `result` in the last line of `log-1.jsonl`), quoted
  verbatim, one or two sentences each. Those quotes are the rationalizations Tasks 11–12 answer.
  Never paste a session's start-up event or anything from the user's own setup. Then:
  `grep -nE '/(Users|home|private|var/folders)/' plan-driven-development/tests/red-results.md`
  prints nothing.

- [ ] **Step 6: Commit.** Write `.git/PDD_MSG`, filling each `<…>` from the runs:

```text
plan-driven-development: record the RED baselines

Without the skill, on <model>, with superpowers <version> and Matt
Pocock's skills <version>: <scenario: n of m checks failed>, one per
line. The rationalizations quoted in tests/red-results.md are what the
skill text answers.

Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Task 6
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```bash
git add plan-driven-development/tests/red-results.md
git commit -F .git/PDD_MSG
git log -1 --format='%(trailers)'
```

- [ ] **Step 7: Close (Tier 3).** A self-review: every scenario has at least one FAIL, and each
  rationalization is quoted, not paraphrased. **Now** → `Task 7: the leak check, open.` Commit
  `plan-driven-development: close Task 6: RED, the baselines without the skill`:

  Write `.git/PDD_MSG`, filling each `<…>`:

```text
plan-driven-development: close Task 6: RED, the baselines without the skill

Drift: <how the build departed from this plan, and why; or "none">
Rulings: <each ruling: what was decided, why, what it costs if wrong; or "none">
Phase-end: <findings deferred to the phase-end list, with severity and file; or "none">
Forward: <later tasks the forward review changed, and how; or "none">
Tier: 3
Rounds: <the reviews and re-reviews run>
Findings: <Critical n, Important n, Minor n, and what became of each>

Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Task 6
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```bash
git add docs/superpowers/plans/2026-10-15-plan-driven-development.md
git commit -F .git/PDD_MSG
git log -1 --format='%(trailers)'
for h in Drift Rulings Phase-end Forward Tier Rounds Findings; do
  git log -1 --format=%B | grep -q "^$h: ." || echo "missing $h"
done
```

  Expected: the trailers print the `Plan:` line; no `missing` line.

- [ ] **Step 8: Push (standing OK).**

  Until Task 7 the scan uses local-ai's leak check, which reads Dan's denylist without printing
  it; `$LOCAL_AI` is local-ai's checkout (Global Constraints). Push only through this block:

```bash
: "${LOCAL_AI:?set LOCAL_AI to the local-ai checkout first, as Global Constraints says}"
git fetch -q origin
range=origin/plan-driven-development..HEAD
f=$(mktemp)
git log -p --cc --format='%H%n%B' "$range" > "$f"
if uv run --frozen --project "$LOCAL_AI/spark" spark leakcheck --message "$f" &&
   gitleaks git --log-opts="$range" --redact --no-banner . &&
   git log --format= --numstat "$range" | awk '$1 == "-" { print "binary, check it by eye: " $3; bad = 1 } END { exit bad }'; then
  rm -f "$f"; git push origin plan-driven-development
else
  rm -f "$f"; echo "STOP: not pushed. Tell Dan each finding's kind and file:line (never the matched text), or the binary's name."
fi
```

  Expected: the leak check prints nothing, gitleaks prints `no leaks found`, then the push. A
  `STOP` line means nothing was pushed: a leak or an unscanned binary is a stop that never relaxes;
  tell Dan the kind and `file:line`, never the excerpt.

***

### Task 7: The leak check

**Tier:** 1 · **Scenarios:** S06.

**Files:**
- Create: `plan-driven-development/scripts/leakcheck.py`
- Test: `plan-driven-development/tests/test_leakcheck.py`

**Interfaces:**
- Consumes: `helpers` (Task 3).
- Produces: `leakcheck.main(argv) -> int` with `--staged`, `--message FILE`, `--range REVS`,
  `--tracked`, `--ci`, `--denylist PATH` (default `$LEAKCHECK_DENYLIST`, else
  `~/.config/leakcheck/denylist`); exit 0 clean, 1 findings, 2 refused (no or bad denylist, `--ci`
  outside CI, an unreadable range). A binary file, staged or in a range, is named on stderr
  ("not scanned (binary): … — check it by eye") without changing the exit code. Also `scan_text`,
  `load_denylist`, `staged_texts`, `tracked_texts`, `range_text`, `range_binaries`.

- [ ] **Step 0: Record the base:** `git rev-parse HEAD > .git/PDD_BASE`.

- [ ] **Step 1: Write the failing test,** `plan-driven-development/tests/test_leakcheck.py` (ported
  from local-ai's `spark/tests/test_leakcheck.py` at `e32096c`, every test and assertion kept, plus
  the range and its binaries, the environment default, the silent validation, the stop message and
  Review Focus 3 and 5):

```python
"""scripts/leakcheck.py, ported with local-ai's tests (spark/tests/test_leakcheck.py at e32096c)."""

import codecs
import re

import pytest

from helpers import denylist, git, git_repo, ip, ipv6, load_script, mac

leakcheck = load_script("leakcheck")
scan_text = leakcheck.scan_text


def kinds(text: str, deny=()) -> list[str]:
    return [f.kind for f in scan_text("t.md", text, list(deny))]


@pytest.mark.parametrize("address", [ip(10, 1, 2, 3), ip(172, 20, 0, 5), ip(192, 168, 77, 5)])
def test_private_ipv4_is_flagged(address):
    assert kinds(f"server at {address} today") == ["private IPv4 address"]


def test_tailnet_address_is_flagged():
    assert kinds(f"node {ip(100, 101, 102, 103)}") == ["tailnet IPv4 address"]


def test_sentence_final_tailnet_address_is_flagged():
    assert kinds(f"The node is {ip(100, 101, 102, 103)}.") == ["tailnet IPv4 address"]


@pytest.mark.parametrize(
    "address",
    [ip(10, 1, 2, 3), ip(172, 20, 0, 5), ip(192, 168, 77, 5)],
    ids=["10/8", "172.16/12", "192.168/16"],
)
def test_sentence_final_private_ipv4_is_flagged(address):
    assert kinds(f"The box is at {address}.") == ["private IPv4 address"]


def test_tailnet_ipv6_address_is_flagged():
    # Tailscale's IPv6 range lies inside the unique-local range, so the broader pattern fires too.
    address = ipv6("fd7a", "115c", "a1e0", "", "5")
    assert kinds(f"node {address} today") == [
        "tailnet IPv6 address",
        "private or link-local IPv6 address",
    ]


@pytest.mark.parametrize(
    "address",
    [ipv6("fd12", "3456", "789a", "", "1"), ipv6("fe80", "", "1a2b", "3c4d", "5e6f", "7a8b")],
    ids=["unique-local", "link-local"],
)
def test_private_ipv6_is_flagged(address):
    assert kinds(f"host {address} today") == ["private or link-local IPv6 address"]


@pytest.mark.parametrize(
    "harmless",
    [
        "reserved as .201 on the wired NIC",
        f"docs example {ip(192, 0, 2, 7)} and {ip(203, 0, 113, 9)}",
        f"public {ip(100, 12, 1, 1)}",
        "uv 0.12.18 and CUDA 13.0.2",
        "at 12:34:56 it froze",
        "patterns for MACs and `ts.net` names",
        f"build {ip(10, 1, 2, 3, 4)} is longer than an address",
        "link-local fe80::/10 and unique-local fc00::/7 are ranges, not hosts",
    ],
)
def test_harmless_text_is_not_flagged(harmless):
    assert kinds(harmless) == []


def test_mac_address_is_flagged():
    assert kinds(f"nic {mac('a4', 'bb', '6d', '01', '02', 'ef')}") == ["MAC address"]


def test_tailnet_hostname_is_flagged():
    name = "box." + "tail" + "1a2b" + ".ts.net"
    assert kinds(f"https://{name}/") == ["tailnet hostname"]


def test_bare_tailnet_name_is_flagged():
    name = "tail" + "1a2b" + ".ts.net"
    assert kinds(f"the tailnet is {name} today") == ["tailnet hostname"]


def test_ddns_name_is_flagged():
    name = "home" + "." + "synology" + ".me"
    assert kinds(f"see {name} now") == ["Synology DDNS or QuickConnect name"]


def test_volume_path_and_key_block_are_flagged():
    assert kinds("/Vol" + "umes/Backup/x") == ["macOS volume path"]
    assert kinds("-----BEGIN " + "OPENSSH PRIVATE KEY-----") == ["private key block"]


def test_denylisted_term_is_flagged_case_insensitively():
    deny = [re.compile("secret-project", re.IGNORECASE)]
    assert kinds("about the Secret-Project plan", deny) == ["denylisted term"]


def test_allow_marker_skips_a_line():
    assert kinds(f"example {ip(192, 168, 0, 1)}  <!-- leakcheck: allow -->") == []


def test_allow_marker_never_excuses_a_denylisted_term():
    deny = [re.compile("secret-project", re.IGNORECASE)]
    text = f"secret-project box at {ip(192, 168, 0, 1)}  <!-- leakcheck: allow -->"
    assert kinds(text, deny) == ["denylisted term"]


def test_excerpt_is_redacted():
    assert scan_text("t.md", ip(10, 9, 8, 7), [])[0].excerpt == "10.…"


def test_missing_denylist_fails_closed(tmp_path):
    with pytest.raises(leakcheck.DenylistMissing):
        leakcheck.load_denylist(tmp_path / "nope")


def test_denylist_skips_blank_lines_and_comments(tmp_path):
    path = tmp_path / "denylist"
    path.write_text("# a comment\n\nsecret-project\n")
    assert [p.pattern for p in leakcheck.load_denylist(path)] == ["secret-project"]


def test_the_default_denylist_comes_from_the_environment(tmp_path, monkeypatch):
    path = denylist(tmp_path)
    monkeypatch.setenv("LEAKCHECK_DENYLIST", str(path))
    assert leakcheck.parser().parse_args(["--tracked"]).denylist == path


def test_staged_file_with_private_address_is_found(tmp_path):
    repo = git_repo(tmp_path)
    (repo / "notes.md").write_text(f"box at {ip(192, 168, 50, 7)}\n")
    git(repo, "add", "notes.md")
    texts = leakcheck.staged_texts(cwd=repo)
    assert texts == [("notes.md", f"box at {ip(192, 168, 50, 7)}\n")]
    assert kinds(texts[0][1]) == ["private IPv4 address"]


def test_ci_mode_is_refused_outside_ci(monkeypatch, capsys):
    monkeypatch.delenv("CI", raising=False)
    assert leakcheck.main(["--tracked", "--ci"]) == 2
    assert "only in CI" in capsys.readouterr().err


def test_a_missing_denylist_exits_2(tmp_path, capsys):
    message = tmp_path / "msg"
    message.write_text("hello\n")
    assert leakcheck.main(["--message", str(message), "--denylist", str(tmp_path / "none")]) == 2
    assert "denylist not found" in capsys.readouterr().err


def test_an_invalid_denylist_line_exits_2_and_is_never_shown(tmp_path, capsys):
    path = tmp_path / "denylist"
    path.write_text("first-term\nprivate-name(\n")
    message = tmp_path / "msg"
    message.write_text("hello\n")
    assert leakcheck.main(["--message", str(message), "--denylist", str(path)]) == 2
    err = capsys.readouterr().err
    assert "line 2" in err and "private-name" not in err


@pytest.mark.parametrize("text", ["", "# a comment\n\n   \n"], ids=["empty", "comments-only"])
def test_a_denylist_with_no_terms_fails_closed(tmp_path, capsys, text):
    path = tmp_path / "denylist"
    path.write_text(text)
    with pytest.raises(leakcheck.DenylistInvalid, match="denylist has no terms"):
        leakcheck.load_denylist(path)
    message = tmp_path / "msg"
    message.write_text("hello\n")
    assert leakcheck.main(["--message", str(message), "--denylist", str(path)]) == 2
    assert "denylist has no terms" in capsys.readouterr().err


def test_an_empty_message_validates_the_denylist_silently(tmp_path, capsys):
    # Kickoff and resume run `--message /dev/null`: it proves the denylist exists and parses, and
    # prints nothing at all.
    assert leakcheck.main(["--message", "/dev/null", "--denylist", str(denylist(tmp_path))]) == 0
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == ""


def test_a_message_that_is_not_utf8_is_still_scanned(tmp_path, capsys):
    message = tmp_path / "msg"
    message.write_bytes(b"caf\xe9 at " + ip(192, 168, 50, 7).encode() + b"\n")
    assert leakcheck.main(["--message", str(message), "--denylist", str(denylist(tmp_path))]) == 1
    assert "private IPv4 address" in capsys.readouterr().err


def test_a_symlink_turned_into_a_file_is_scanned(tmp_path):
    repo = git_repo(tmp_path)
    (repo / "notes.md").symlink_to("elsewhere.md")
    git(repo, "add", "notes.md")
    git(repo, "commit", "-q", "-m", "link")
    (repo / "notes.md").unlink()
    (repo / "notes.md").write_text(f"box at {ip(192, 168, 50, 7)}\n")
    git(repo, "add", "notes.md")
    assert leakcheck.staged_texts(cwd=repo) == [("notes.md", f"box at {ip(192, 168, 50, 7)}\n")]


def test_a_file_turned_into_a_symlink_has_its_target_scanned(tmp_path):
    repo = git_repo(tmp_path)
    (repo / "data").write_text("placeholder\n")
    git(repo, "add", "data")
    git(repo, "commit", "-q", "-m", "file")
    (repo / "data").unlink()
    target = f"/mnt/{ip(192, 168, 50, 7)}/share"
    (repo / "data").symlink_to(target)
    git(repo, "add", "data")
    assert leakcheck.staged_texts(cwd=repo) == [("data", target)]


@pytest.mark.parametrize("encoding", ["utf-16", "utf-16-be", "utf-32", "utf-32-be"])
def test_utf16_and_utf32_text_with_a_byte_order_mark_is_scanned(tmp_path, encoding):
    text = f"box at {ip(192, 168, 50, 7)}\n"
    bom = {"utf-16-be": codecs.BOM_UTF16_BE, "utf-32-be": codecs.BOM_UTF32_BE}.get(encoding, b"")
    repo = git_repo(tmp_path)
    (repo / "notes.txt").write_bytes(bom + text.encode(encoding))
    git(repo, "add", "notes.txt")
    assert leakcheck.staged_texts(cwd=repo) == [("notes.txt", text)]


def test_a_binary_file_is_named_for_a_person_to_check(tmp_path, monkeypatch, capsys):
    repo = git_repo(tmp_path)
    (repo / "shot.png").write_bytes(b"\x89PNG\r\n\x1a\n\0\0\0\rIHDR" + ip(192, 168, 50, 7).encode())
    git(repo, "add", "shot.png")
    monkeypatch.chdir(repo)
    assert leakcheck.main(["--staged", "--denylist", str(denylist(tmp_path))]) == 0
    assert "leakcheck: not scanned (binary): shot.png — check it by eye" in capsys.readouterr().err


def test_a_file_name_is_scanned_and_shown_redacted(tmp_path, monkeypatch, capsys):
    repo = git_repo(tmp_path)
    (repo / f"notes-{ip(192, 168, 50, 7)}.md").write_text("nothing private here\n")
    git(repo, "add", ".")
    monkeypatch.chdir(repo)
    assert leakcheck.main(["--staged", "--denylist", str(denylist(tmp_path))]) == 1
    err = capsys.readouterr().err
    assert "leakcheck: notes-192….md (file name):1: private IPv4 address (192…)" in err
    assert ip(192, 168, 50, 7) not in err


def test_a_denylisted_term_in_a_file_name_is_never_printed_whole(tmp_path, monkeypatch, capsys):
    repo = git_repo(tmp_path)
    (repo / "secret-project-plan.md").write_text(f"box at {ip(192, 168, 50, 7)}\n")
    git(repo, "add", ".")
    monkeypatch.chdir(repo)
    assert leakcheck.main(["--staged", "--denylist", str(denylist(tmp_path, "secret-project"))]) == 1
    err = capsys.readouterr().err
    assert "leakcheck: sec…-plan.md (file name):1: denylisted term (sec…)" in err
    assert "leakcheck: sec…-plan.md:1: private IPv4 address (192…)" in err
    assert "secret-project" not in err


def test_ci_scans_every_tracked_file_name(tmp_path, monkeypatch, capsys):
    repo = git_repo(tmp_path)
    (repo / f"notes-{ip(192, 168, 50, 7)}.md").write_text("nothing private here\n")
    git(repo, "add", ".")
    monkeypatch.chdir(repo)
    monkeypatch.setenv("CI", "true")
    assert leakcheck.main(["--tracked", "--ci"]) == 1
    assert "(file name):1: private IPv4 address" in capsys.readouterr().err


def test_a_range_scans_each_commits_patch_and_message(tmp_path, monkeypatch, capsys):
    repo = git_repo(tmp_path)
    (repo / "a.md").write_text("clean\n")
    git(repo, "add", "a.md")
    git(repo, "commit", "-q", "-m", "base")
    (repo / "b.md").write_text(f"box at {ip(10, 0, 0, 7)}\n")
    git(repo, "add", "b.md")
    git(repo, "commit", "-q", "-m", f"note secret-project")
    monkeypatch.chdir(repo)
    assert leakcheck.main(["--range", "HEAD~1..HEAD", "--denylist", str(denylist(tmp_path))]) == 1
    err = capsys.readouterr().err
    assert "outgoing commits" in err
    assert "private IPv4 address" in err and "denylisted term" in err


def test_a_new_branch_range_scans_everything_the_remote_lacks(tmp_path, monkeypatch, capsys):
    repo = git_repo(tmp_path)
    (repo / "b.md").write_text(f"box at {ip(10, 0, 0, 7)}\n")
    git(repo, "add", "b.md")
    git(repo, "commit", "-q", "-m", "first")
    monkeypatch.chdir(repo)
    assert leakcheck.main(["--range", "HEAD --not --remotes", "--denylist", str(denylist(tmp_path))]) == 1


def test_a_range_names_a_binary_file_for_a_person_to_check(tmp_path, monkeypatch, capsys):
    # A screenshot going out can't be scanned: it is named, so the merge can wait for Dan's eye.
    repo = git_repo(tmp_path)
    (repo / "a.md").write_text("clean\n")
    git(repo, "add", "a.md")
    git(repo, "commit", "-q", "-m", "base")
    (repo / "shot.png").write_bytes(b"\x89PNG\r\n\x1a\n\0\0\0\rIHDR")
    git(repo, "add", "shot.png")
    git(repo, "commit", "-q", "-m", "a screenshot")
    monkeypatch.chdir(repo)
    assert leakcheck.main(["--range", "HEAD~1..HEAD", "--denylist", str(denylist(tmp_path))]) == 0
    assert "leakcheck: not scanned (binary): shot.png — check it by eye" in capsys.readouterr().err


def test_a_finding_says_to_stop_and_tell_dan(tmp_path, capsys):
    # A leak hit is a stop that never relaxes: the message says so, never "fix it and carry on".
    message = tmp_path / "msg"
    message.write_text(f"box at {ip(10, 0, 0, 7)}\n")
    assert leakcheck.main(["--message", str(message), "--denylist", str(denylist(tmp_path))]) == 1
    err = capsys.readouterr().err
    assert "stop and tell Dan" in err and "Fix the text" not in err


def test_an_unreadable_range_fails_closed(tmp_path, monkeypatch, capsys):
    repo = git_repo(tmp_path)
    (repo / "a.md").write_text("clean\n")
    git(repo, "add", "a.md")
    git(repo, "commit", "-q", "-m", "base")
    monkeypatch.chdir(repo)
    missing = "0123456789abcdef0123456789abcdef01234567"
    assert leakcheck.main(["--range", f"{missing}..HEAD", "--denylist", str(denylist(tmp_path))]) == 2
    assert "can't read the range" in capsys.readouterr().err


def test_a_renamed_file_is_scanned(tmp_path):
    # Review Focus 3: a rename (git status R) carries the whole file to its new name.
    repo = git_repo(tmp_path)
    (repo / "a.md").write_text(f"box at {ip(192, 168, 50, 7)}\n")
    git(repo, "add", "a.md")
    git(repo, "commit", "-q", "-m", "first")
    git(repo, "mv", "a.md", "b.md")
    assert leakcheck.staged_texts(cwd=repo) == [("b.md", f"box at {ip(192, 168, 50, 7)}\n")]


def test_a_non_ascii_file_name_is_scanned(tmp_path, monkeypatch, capsys):
    # Review Focus 5: git's -z output keeps a non-ASCII name intact, so it is read, not skipped.
    repo = git_repo(tmp_path)
    (repo / "café-notes.md").write_text(f"box at {ip(192, 168, 50, 7)}\n")
    git(repo, "add", "café-notes.md")
    monkeypatch.chdir(repo)
    assert leakcheck.main(["--staged", "--denylist", str(denylist(tmp_path))]) == 1
    assert "café-notes.md:1: private IPv4 address" in capsys.readouterr().err
```

- [ ] **Step 2: Run it; watch it fail.**
  `uv run --quiet --with pytest pytest plan-driven-development/tests/test_leakcheck.py -q`.
  Expected: `1 error` at collection: `FileNotFoundError: … scripts/leakcheck.py`.

- [ ] **Step 3: Write `plan-driven-development/scripts/leakcheck.py`** (local-ai's
  `spark/src/spark/leakcheck.py` at `e32096c`, standalone, with every one of its patterns, the
  `--range` mode with its binaries named, this repo's denylist default, and a refusal that tells an
  agent to stop and tell Dan):

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Leak check for a public repo, copied into each project made with plan-driven-development.

Flags private addresses, per-unit identifiers and privately denylisted terms, in file names as
well as contents. The git hooks run it on every commit (`--staged`, `--message FILE`) and every
push (`--range REVS`, `--tracked`); CI runs it over every tracked file (`--tracked --ci`) and every
commit's patches and messages (`--message FILE --ci`). It fails closed: a missing, empty or
malformed denylist is an error, never a pass, and so is a range git can't read. A binary file
can't be read, so it is named for a person to check. Ported from chendaniely/local-ai's
`spark leakcheck` (spark/src/spark/leakcheck.py at e32096c).
"""

from __future__ import annotations

import argparse
import codecs
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ALLOW_MARKER = "leakcheck: allow"
DEFAULT_DENYLIST = "~/.config/leakcheck/denylist"
HELP = "see AGENTS.md, Security"

# The IPv4 lookaheads reject a longer dotted string (a version number) but not a sentence-final
# period, so "at <address>." is still caught.
PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "private IPv4 address",
        re.compile(
            r"(?<![\d.])(?:10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d{1,3}\.\d{1,3}(?!\.?\d)"
        ),
    ),
    (
        "tailnet IPv4 address",
        re.compile(r"(?<![\d.])100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}(?!\.?\d)"),
    ),
    ("tailnet IPv6 address", re.compile(r"\bfd7a:115c:a1e0:[0-9a-f:]*[0-9a-f]", re.IGNORECASE)),
    (
        "private or link-local IPv6 address",
        re.compile(r"\b(?:f[cd][0-9a-f]{2}|fe80):[0-9a-f:]*:[0-9a-f]{1,4}\b", re.IGNORECASE),
    ),
    (
        "MAC address",
        re.compile(r"(?<![0-9A-Fa-f:-])(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}(?![0-9A-Fa-f:-])"),
    ),
    ("tailnet hostname", re.compile(r"\b[a-z0-9-]+\.ts\.net\b", re.IGNORECASE)),
    (
        "Synology DDNS or QuickConnect name",
        re.compile(r"\b[a-z0-9-]+\.(?:synology\.me|quickconnect\.to)\b", re.IGNORECASE),
    ),
    ("macOS volume path", re.compile(r"/Volumes/[^\s/`'\"]+")),  # leakcheck: allow
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
)


@dataclass(frozen=True)
class Finding:
    source: str
    line: int
    kind: str
    excerpt: str


class DenylistMissing(RuntimeError):
    pass


class DenylistInvalid(ValueError):
    pass


class RangeUnreadable(RuntimeError):
    pass


def load_denylist(path: Path) -> list[re.Pattern[str]]:
    path = Path(path).expanduser()
    if not path.is_file():
        raise DenylistMissing(f"denylist not found at {path} — ask Dan ({HELP})")
    patterns = []
    for number, raw in enumerate(path.read_text().splitlines(), start=1):
        line = raw.strip()
        if line and not line.startswith("#"):
            try:
                patterns.append(re.compile(line, re.IGNORECASE))
            except re.error:
                # The line number only: the terms are private, and hook output can land in an
                # agent's context. `from None` keeps re's message, which can quote part of the
                # line, out of any traceback too.
                raise DenylistInvalid(
                    f"denylist line {number} is not a valid regular expression — fix it in "
                    f"{path} (the line itself is not shown)"
                ) from None
    if not patterns:
        # An empty file (what `touch` makes) or comments only would pass every commit.
        raise DenylistInvalid(
            f"denylist has no terms — add the private terms to {path}, one regular expression "
            f"per line ({HELP})"
        )
    return patterns


def _redact(text: str) -> str:
    return text[:3] + "…"


def shown_path(path: str, denylist: list[re.Pattern[str]]) -> str:
    """`path` as output may print it: every match of a pattern or a denylisted term cut to 3
    characters, like an excerpt. A private term in a file name must not reach the output whole."""
    spans = sorted(
        m.span()
        for pattern in (*(p for _, p in PATTERNS), *denylist)
        for m in pattern.finditer(path)
        if m.end() > m.start()
    )
    merged: list[list[int]] = []
    for start, end in spans:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    out, pos = [], 0
    for start, end in merged:
        out += [path[pos:start], _redact(path[start:end])]
        pos = end
    return "".join(out) + path[pos:]


def scan_text(source: str, text: str, denylist: list[re.Pattern[str]]) -> list[Finding]:
    findings: list[Finding] = []
    for number, line in enumerate(text.splitlines(), start=1):
        # The allow marker excuses a line from the generic patterns only. A denylisted term is
        # never safe, so the denylist checks every line, marked or not.
        if ALLOW_MARKER not in line:
            for kind, pattern in PATTERNS:
                findings += [
                    Finding(source, number, kind, _redact(m.group(0))) for m in pattern.finditer(line)
                ]
        for pattern in denylist:
            findings += [
                Finding(source, number, "denylisted term", _redact(m.group(0)))
                for m in pattern.finditer(line)
            ]
    return findings


def _git(args: list[str], cwd: Path | None) -> bytes:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True).stdout


# UTF-16 and UTF-32 text is full of NUL bytes, which would mark it as binary, so text that starts
# with a byte-order mark is decoded by it. The UTF-32 marks go first: UTF-32-LE's begins with
# UTF-16-LE's.
_BOMS = (
    (codecs.BOM_UTF32_LE, "utf-32"),
    (codecs.BOM_UTF32_BE, "utf-32"),
    (codecs.BOM_UTF16_LE, "utf-16"),
    (codecs.BOM_UTF16_BE, "utf-16"),
)


def _text(blob: bytes) -> str:
    for bom, codec in _BOMS:
        if blob.startswith(bom):
            return blob.decode(codec, errors="replace")
    return blob.decode("utf-8", errors="replace")


def _decode(blob: bytes) -> str | None:
    """A file's text, or None for a binary file: a NUL byte and no byte-order mark."""
    if b"\0" in blob and not blob.startswith(tuple(bom for bom, _ in _BOMS)):
        return None
    return _text(blob)


def _texts(names: list[bytes], read) -> list[tuple[str, str | None]]:
    """(name, text) for each file; the text is None for a binary file."""
    return [(raw.decode(), _decode(read(raw.decode()))) for raw in names if raw]


def staged_texts(cwd: Path | None = None) -> list[tuple[str, str | None]]:
    # Every staged change but a deletion: added, copied, modified, renamed, and a type change (a
    # symlink turned into a file, or a file into a symlink, whose blob is its target path).
    names = _git(["diff", "--cached", "--name-only", "--diff-filter=ACMRT", "-z"], cwd).split(b"\0")
    return _texts(names, lambda name: _git(["show", f":{name}"], cwd))


def tracked_texts(cwd: Path | None = None) -> list[tuple[str, str | None]]:
    names = _git(["ls-files", "-z"], cwd).split(b"\0")
    root = Path(cwd or ".")
    return _texts(names, lambda name: (root / name).read_bytes())


def range_text(revs: str, cwd: Path | None = None) -> str:
    """Every commit's patch (with a merge's conflict resolutions) and whole message in `revs`,
    for example `abc123..def456` or `def456 --not --remotes`. A range git can't read (a missing
    base, a bad ref) raises RangeUnreadable: the caller can't tell what is going out."""
    try:
        return _text(_git(["log", "-p", "--cc", "--format=%H%n%B", *shlex.split(revs)], cwd))
    except subprocess.CalledProcessError:
        raise RangeUnreadable(f"git can't read the range {revs!r}, so what is going out is unknown") from None


def range_binaries(revs: str, cwd: Path | None = None) -> list[str]:
    """The files in `revs` whose changes git shows as binary (`-` in --numstat): their content
    can't be scanned, so they are named for a person to check."""
    try:
        out = _git(["log", "--format=", "--numstat", "-z", *shlex.split(revs)], cwd)
    except subprocess.CalledProcessError:
        raise RangeUnreadable(f"git can't read the range {revs!r}, so what is going out is unknown") from None
    names: list[str] = []
    for record in out.split(b"\0"):
        fields = record.lstrip(b"\n").split(b"\t")
        if len(fields) == 3 and fields[0] == b"-" and fields[1] == b"-" and fields[2]:
            name = fields[2].decode(errors="replace")
            if name not in names:
                names.append(name)
    return names


def scan_files(files: list[tuple[str, str | None]], denylist: list[re.Pattern[str]]) -> list[Finding]:
    """Scan each file's name, then its text. A binary file's content can't be scanned, so it is
    named on stderr for a person to check; that alone never changes the exit code."""
    findings: list[Finding] = []
    for name, text in files:
        shown = shown_path(name, denylist)
        findings += scan_text(f"{shown} (file name)", name, denylist)
        if text is None:
            print(f"leakcheck: not scanned (binary): {shown} — check it by eye", file=sys.stderr)
        else:
            findings += scan_text(shown, text, denylist)
    return findings


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="leakcheck", description="scan for private addresses, identifiers and denylisted terms"
    )
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--staged", action="store_true", help="scan staged files (pre-commit hook)")
    mode.add_argument(
        "--message",
        type=Path,
        help="scan a text file: a commit message (commit-msg hook), or CI's log of every commit",
    )
    mode.add_argument(
        "--range",
        metavar="REVS",
        help="scan every commit's patch and message in a git range (pre-push hook)",
    )
    mode.add_argument("--tracked", action="store_true", help="scan every tracked file (pre-push, CI)")
    p.add_argument(
        "--denylist",
        type=Path,
        default=Path(os.environ.get("LEAKCHECK_DENYLIST", DEFAULT_DENYLIST)),
        help="private file of regexes, one per line (default: $LEAKCHECK_DENYLIST, else %(default)s)",
    )
    p.add_argument("--ci", action="store_true", help="skip the private denylist — only in CI")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.ci and os.environ.get("CI") != "true":
        print("leakcheck: --ci is allowed only in CI (CI=true)", file=sys.stderr)
        return 2
    try:
        denylist = [] if args.ci else load_denylist(args.denylist)
        if args.message:
            # Decoded leniently: CI feeds whole patches through here, and one stray byte in a
            # patch must not crash the scan.
            findings = scan_text("commit message", _text(args.message.read_bytes()), denylist)
        elif args.range is not None:
            findings = scan_text("outgoing commits", range_text(args.range), denylist)
            for name in range_binaries(args.range):
                print(f"leakcheck: not scanned (binary): {shown_path(name, denylist)} — check it by eye",
                      file=sys.stderr)
        else:
            findings = scan_files(staged_texts() if args.staged else tracked_texts(), denylist)
    except (DenylistMissing, DenylistInvalid, RangeUnreadable) as err:
        print(f"leakcheck: {err}", file=sys.stderr)
        return 2
    for f in findings:
        print(f"leakcheck: {f.source}:{f.line}: {f.kind} ({f.excerpt})", file=sys.stderr)
    if findings:
        print(
            f"leakcheck: {len(findings)} finding(s) — refused. An agent must stop and tell Dan the "
            f"kind and file:line (never the matched text); a leak is a stop that never relaxes. An "
            f"allow marker ('{ALLOW_MARKER}') is Dan's to add, never an agent's, and never "
            f"excuses a denylisted term.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests; they pass.** `make test` and `make test-utc`. Expected: `119 passed`
  both times (63 + 56).

- [ ] **Step 5: Validate the real denylist without reading it:**

```bash
uv run --quiet --script plan-driven-development/scripts/leakcheck.py --message /dev/null; echo "denylist: exit=$?"
```

  Expected: nothing printed, then `denylist: exit=0`. Exit 2 means the link from Task 1 Step 8 is
  missing or the list has no terms: stop and tell Dan.

- [ ] **Step 6: Commit.** Write `.git/PDD_MSG`:

```text
plan-driven-development: add the leak check, ported from local-ai

scripts/leakcheck.py is local-ai's checker (e32096c) as a standalone,
standard-library PEP 723 script: private, tailnet, unique-local and
link-local addresses, MACs, tailnet and Synology DDNS names, volume
paths, private-key blocks, and this machine's denylist, in file names
and text, printing 3-character excerpts only. Modes --staged, --message,
--range (binaries named for a person's eye), --tracked and --ci. It
fails closed on a missing, empty or malformed denylist, and its refusal
tells an agent to stop and tell Dan. Every local-ai test is ported.

Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Task 7
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```bash
git add plan-driven-development/scripts/leakcheck.py plan-driven-development/tests/test_leakcheck.py
git commit -F .git/PDD_MSG
git log -1 --format='%(trailers)'
```

- [ ] **Step 7: Review, look forward, close (Tier 1).**
  1. **Mechanical:** `make test` and `make test-utc`.
  2. **Backward review:** `mattpocock-skills:code-review` from `$(cat .git/PDD_BASE)`, the spec
     being this task, the spec's *Security hooks and the leak check*, and local-ai's source and
     tests at `e32096c` (nothing the port loses); plus the security checklist; at most one
     re-review.
  3. **Forward review:** Task 8's hooks call `--staged`, `--message`, `--range` and `--tracked`
     exactly as defined here; Task 9's CI calls `--tracked --ci` and `--message <file> --ci`, and its
     Makefile's `leaks` target calls `--tracked`; from Step 8 on, the push block uses `--range`.
  4. **Docs:** none yet.
  5. **Close:** **Now** → `Task 8: the hooks, open.` Commit
     `plan-driven-development: close Task 7: the leak check`:

  Write `.git/PDD_MSG`, filling each `<…>`:

```text
plan-driven-development: close Task 7: the leak check

Drift: <how the build departed from this plan, and why; or "none">
Rulings: <each ruling: what was decided, why, what it costs if wrong; or "none">
Phase-end: <findings deferred to the phase-end list, with severity and file; or "none">
Forward: <later tasks the forward review changed, and how; or "none">
Tier: 1
Rounds: <the reviews and re-reviews run>
Findings: <Critical n, Important n, Minor n, and what became of each>

Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Task 7
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```bash
git add docs/superpowers/plans/2026-10-15-plan-driven-development.md
git commit -F .git/PDD_MSG
git log -1 --format='%(trailers)'
for h in Drift Rulings Phase-end Forward Tier Rounds Findings; do
  git log -1 --format=%B | grep -q "^$h: ." || echo "missing $h"
done
```

  Expected: the trailers print the `Plan:` line; no `missing` line.

- [ ] **Step 8: Push (standing OK).** From here on the push block uses the skill's own leak check:

  The skill's own leak check scans the range, with Dan's denylist. Push only through this block:

```bash
git fetch -q origin
range=origin/plan-driven-development..HEAD
if uv run --quiet --script plan-driven-development/scripts/leakcheck.py --range "$range" &&
   gitleaks git --log-opts="$range" --redact --no-banner . &&
   git log --format= --numstat "$range" | awk '$1 == "-" { print "binary, check it by eye: " $3; bad = 1 } END { exit bad }'; then
  git push origin plan-driven-development
else
  echo "STOP: not pushed. Tell Dan each finding's kind and file:line (never the matched text), or the binary's name."
fi
```

  Expected: the leak check prints nothing, gitleaks prints `no leaks found`, then the push. A
  `STOP` line means nothing was pushed: a leak or an unscanned binary is a stop that never relaxes;
  tell Dan the kind and `file:line`, never the excerpt.

***

### Task 8: The four git hooks

**Tier:** 1 · **Scenarios:** S06 (the drill), S07, S08 (through the hook).

**Files:**
- Create: `plan-driven-development/templates/githooks/pre-commit`, `commit-msg`, `pre-push`,
  `pre-merge-commit` (mode 755), `gitleaks.toml`
- Test: `plan-driven-development/tests/test_hooks.py`, `plan-driven-development/tests/test_green_fixture.py`

**Interfaces:**
- Consumes: `scripts/leakcheck.py` (Task 7), `scripts/commitmsg.py` and `helpers.make_project`
  (Task 3), `recipes.build` (Task 4).
- Produces: the hooks a project's `.githooks/` gets at kickoff; each refuses without gitleaks 8.19+
  or uv; `pre-push` refuses `main`, tags, deletions and force pushes and scans what goes out.

- [ ] **Step 0: Record the base:** `git rev-parse HEAD > .git/PDD_BASE`.

- [ ] **Step 1: Write the failing tests,** `plan-driven-development/tests/test_hooks.py` (local-ai's
  `spark/tests/test_hooks.py` at `e32096c`, ported, plus the new hooks, the commit-msg checks, the
  drill with its findings named, and Review Focus 1 and 4):

```python
"""The four git hooks and scripts/commitmsg.py, in a throwaway project made the way kickoff makes one.
Ported in part from local-ai's spark/tests/test_hooks.py (e32096c); the push, merge and format
checks are new. Tests that need a real gitleaks (8.19+) and uv skip without them."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from helpers import TEMPLATES, denylist, git, gitleaks_has_git, ip, load_script, make_project, token

HOOKS = ("pre-commit", "commit-msg", "pre-push", "pre-merge-commit")
needs_tools = pytest.mark.skipif(
    not (gitleaks_has_git() and shutil.which("uv")), reason="needs gitleaks 8.19+ and uv on PATH"
)
commitmsg = load_script("commitmsg")

OLD_GITLEAKS = """#!/bin/sh
# Stands in for gitleaks 8.16: it has no `git` command.
if [ "$1" = git ]; then echo 'Error: unknown command "git" for "gitleaks"' >&2; exit 1; fi
exit 0
"""

PLAN = "Plan: docs/superpowers/plans/2026-01-01-demo.md Task 3"
COAUTHOR = "Co-Authored-By: An Agent <agent@example.invalid>"


def fake_bin(tmp_path: Path, *tools: str) -> Path:
    bindir = tmp_path / "bin"
    bindir.mkdir()
    for tool in tools:
        found = shutil.which(tool)
        assert found, tool
        (bindir / tool).symlink_to(found)
    return bindir


def run_hook(tmp_path: Path, hook: str, bindir: Path) -> subprocess.CompletedProcess[str]:
    repo = make_project(tmp_path)
    message = tmp_path / "msg"
    message.write_text("hello\n")
    return subprocess.run(
        ["bash", str(repo / ".githooks" / hook), str(message)],
        cwd=repo, env={"PATH": str(bindir), "HOME": str(tmp_path)},
        capture_output=True, text=True, input="",
    )


def env_with(tmp_path: Path, *terms: str) -> dict[str, str]:
    return {**os.environ, "LEAKCHECK_DENYLIST": str(denylist(tmp_path, *terms))}


def commit(repo: Path, env, message: str, *paths: str):
    msg = repo.parent / "commit-message"
    msg.write_text(message)
    if paths:
        git(repo, "add", *paths, env=env)
    return git(repo, "commit", "-q", "-F", str(msg), hooks=True, check=False, env=env)


def test_the_hook_templates_are_executable():
    for name in HOOKS:
        assert os.access(TEMPLATES / "githooks" / name, os.X_OK), name


@pytest.mark.parametrize("hook", ["pre-commit", "commit-msg", "pre-push"])
def test_a_hook_refuses_without_gitleaks(tmp_path, hook):
    result = run_hook(tmp_path, hook, fake_bin(tmp_path, "git", "bash", "dirname", "cat"))
    assert result.returncode == 1
    assert "gitleaks is not installed" in result.stderr


@pytest.mark.parametrize("hook", ["pre-commit", "commit-msg", "pre-push"])
def test_a_hook_refuses_a_gitleaks_without_the_git_command(tmp_path, hook):
    bindir = fake_bin(tmp_path, "git", "bash", "dirname", "cat")
    (bindir / "gitleaks").write_text(OLD_GITLEAKS)
    (bindir / "gitleaks").chmod(0o755)
    result = run_hook(tmp_path, hook, bindir)
    assert result.returncode == 1
    assert "it needs 8.19 or later" in result.stderr


@needs_tools
@pytest.mark.parametrize("hook", ["pre-commit", "commit-msg", "pre-push"])
def test_a_hook_refuses_clearly_without_uv(tmp_path, hook):
    result = run_hook(tmp_path, hook, fake_bin(tmp_path, "git", "bash", "dirname", "cat", "gitleaks"))
    assert result.returncode == 1
    assert "uv is not on this shell's PATH" in result.stderr


@needs_tools
def test_a_clean_commit_passes_every_hook(tmp_path):
    repo = make_project(tmp_path)
    env = env_with(tmp_path)
    (repo / "notes.md").write_text("nothing private\n")
    result = commit(repo, env, f"docs(notes): 🤖 add notes\n\nA body.\n\n{PLAN}\n{COAUTHOR}\n", "notes.md")
    assert result.returncode == 0, result.stderr


@needs_tools
def test_the_leak_drill_is_refused_and_leaves_nothing_behind(tmp_path):
    # Kickoff's drill (S06): an invented token and a private address, each staged by path and
    # committed with -F, each refused; then unstaged and deleted. The repo has no commit yet, so
    # `git restore --staged` can't run (no HEAD); `git rm --cached` can.
    repo = make_project(tmp_path)
    env = env_with(tmp_path)
    # Each refusal must name its finding: exit 1 alone is also what a missing gitleaks or uv gives.
    drills = (("drill-token.md", f"key {token()}\n", "leaks found: 1"),
              ("drill-address.md", f"box {ip(192, 168, 50, 7)}\n", "drill-address.md:1: private IPv4 address (192…)"))
    for name, text, finding in drills:
        (repo / name).write_text(text)
        result = commit(repo, env, "test(repo): 🤖 leak drill\n", name)
        assert result.returncode == 1, (name, result.stderr)
        assert finding in result.stdout + result.stderr, (name, result.stdout, result.stderr)
        git(repo, "rm", "-q", "--cached", name)
        (repo / name).unlink()
    assert "drill" not in git(repo, "status", "--porcelain", "--untracked-files=all").stdout
    assert git(repo, "diff", "--cached", "--name-only").stdout == ""  # nothing left staged
    assert git(repo, "rev-list", "--all", check=False).stdout == ""  # and no commit made


@needs_tools
def test_a_denylisted_term_in_a_message_is_refused(tmp_path):
    repo = make_project(tmp_path)
    env = env_with(tmp_path, "secret-project")
    (repo / "a.md").write_text("fine\n")
    result = commit(repo, env, "docs(repo): 🤖 about secret-project\n", "a.md")
    assert result.returncode == 1
    assert "denylisted term" in result.stderr and "secret-project" not in result.stderr


@needs_tools
def test_the_commit_msg_hook_runs_the_format_checks(tmp_path):
    repo = make_project(tmp_path)
    env = env_with(tmp_path)
    (repo / "a.md").write_text("fine\n")
    result = commit(repo, env, f"Update a\n\n{PLAN}\n", "a.md")
    assert result.returncode == 1 and "isn't Conventional Commits" in result.stderr


def pushed_project(tmp_path: Path):
    """A project with a bare remote whose main has one commit (Dan's first push, made here
    without hooks), and a phase-1 branch checked out."""
    repo = make_project(tmp_path)
    env = env_with(tmp_path)
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], check=True)
    git(repo, "remote", "add", "origin", str(remote))
    (repo / "README.md").write_text("demo\n")
    assert commit(repo, env, "chore(repo): 🤖 the root commit\n", "README.md").returncode == 0
    git(repo, "push", "-q", "origin", "main")  # without hooks: Dan's [Dan] step
    git(repo, "switch", "-q", "-c", "phase-1")
    return repo, env


def push(repo: Path, env, *args: str):
    return git(repo, "push", *args, hooks=True, check=False, env=env)


@needs_tools
def test_a_clean_new_branch_is_scanned_and_pushed(tmp_path):
    repo, env = pushed_project(tmp_path)
    (repo / "b.md").write_text("fine\n")
    assert commit(repo, env, "docs(repo): 🤖 add b\n", "b.md").returncode == 0
    result = push(repo, env, "-q", "origin", "phase-1")
    assert result.returncode == 0, result.stderr


@needs_tools
def test_a_leak_in_an_outgoing_commit_is_refused(tmp_path):
    repo, env = pushed_project(tmp_path)
    (repo / "b.md").write_text(f"box {ip(10, 0, 0, 7)}\n")
    git(repo, "add", "b.md")
    git(repo, "commit", "-q", "-m", "docs(repo): sneaked past the commit hooks")  # hooks off here
    result = push(repo, env, "-q", "origin", "phase-1")
    assert result.returncode == 1
    assert "outgoing commits" in result.stderr


@needs_tools
@pytest.mark.parametrize(
    "args, reason",
    [
        (("origin", "phase-1:main"), "a push to main is refused"),
        (("origin", "phase-1:refs/tags/v1"), "a tag push is refused"),
    ],
    ids=["to-main", "a-tag"],
)
def test_pushes_to_main_and_tags_are_refused(tmp_path, args, reason):
    repo, env = pushed_project(tmp_path)
    (repo / "b.md").write_text("fine\n")
    assert commit(repo, env, "docs(repo): 🤖 add b\n", "b.md").returncode == 0
    result = push(repo, env, *args)
    assert result.returncode == 1 and reason in result.stderr


@needs_tools
def test_a_force_push_and_a_deletion_are_refused(tmp_path):
    repo, env = pushed_project(tmp_path)
    (repo / "b.md").write_text("fine\n")
    assert commit(repo, env, "docs(repo): 🤖 add b\n", "b.md").returncode == 0
    assert push(repo, env, "-q", "origin", "phase-1").returncode == 0
    git(repo, "reset", "-q", "--hard", "HEAD~1")
    (repo / "c.md").write_text("fine\n")
    assert commit(repo, env, "docs(repo): 🤖 add c\n", "c.md").returncode == 0
    forced = push(repo, env, "--force", "origin", "phase-1")
    assert forced.returncode == 1 and "force push" in forced.stderr
    deleted = push(repo, env, "origin", ":phase-1")
    assert deleted.returncode == 1 and "deleting refs/heads/phase-1 is refused" in deleted.stderr


@needs_tools
def test_a_merge_git_completes_itself_is_checked(tmp_path):
    repo, env = pushed_project(tmp_path)
    git(repo, "switch", "-q", "-c", "other", "main")
    (repo / "leak.md").write_text(f"box {ip(10, 0, 0, 7)}\n")
    git(repo, "add", "leak.md")
    git(repo, "commit", "-q", "-m", "docs(repo): sneaked past the commit hooks")  # hooks off here
    git(repo, "switch", "-q", "phase-1")
    msg = repo.parent / "merge-message"
    msg.write_text("chore(repo): 🤖 merge other into phase-1\n")
    result = git(repo, "merge", "--no-ff", "-F", str(msg), "other", hooks=True, check=False, env=env)
    assert result.returncode != 0
    assert "private IPv4 address" in result.stderr


@needs_tools
def test_the_hooks_work_in_a_folder_whose_path_has_a_space(tmp_path):
    # Review Focus 1: every path in the hooks is quoted.
    spaced = tmp_path / "My Projects"
    spaced.mkdir()
    repo = make_project(spaced)
    env = env_with(tmp_path)
    (repo / "notes.md").write_text("nothing private\n")
    assert commit(repo, env, f"docs(notes): 🤖 add notes\n\nA body.\n\n{PLAN}\n{COAUTHOR}\n", "notes.md").returncode == 0
    (repo / "leak.md").write_text(f"box {ip(10, 0, 0, 7)}\n")
    assert commit(repo, env, "docs(notes): 🤖 add a leak\n", "leak.md").returncode == 1


@needs_tools
def test_a_push_of_two_branches_is_refused_if_either_leaks(tmp_path):
    # Review Focus 4: pre-push reads one line per ref; any leaking ref refuses the whole push.
    repo, env = pushed_project(tmp_path)
    (repo / "b.md").write_text("fine\n")
    assert commit(repo, env, "docs(repo): 🤖 add b\n", "b.md").returncode == 0
    git(repo, "switch", "-q", "-c", "phase-2", "main")
    (repo / "c.md").write_text(f"box {ip(10, 0, 0, 7)}\n")
    git(repo, "add", "c.md")
    git(repo, "commit", "-q", "-m", "docs(repo): sneaked past the commit hooks")  # hooks off here
    result = push(repo, env, "origin", "phase-1", "phase-2")
    assert result.returncode == 1 and "outgoing commits" in result.stderr
```

  and `plan-driven-development/tests/test_green_fixture.py`:

```python
"""A GREEN fixture gets the project's hooks, scripts and AGENTS.md from the skill (the harness's
recipes, checked once the hook templates exist)."""

import shutil
import subprocess
import sys

from helpers import SKILL

sys.path.insert(0, str(SKILL / "tests" / "harness"))
import recipes  # noqa: E402


def test_a_green_fixture_gets_the_hooks_and_the_template(tmp_path):
    skill = tmp_path / "skill"
    shutil.copytree(SKILL, skill)
    (skill / "templates" / "AGENTS.md").write_text("# __PROJECT__: how we work\n\nMode: __MODE__. Check: `__CHECK_COMMAND__`.\n")
    repo = tmp_path / "repo"
    recipes.build("s20", repo, "green", skill)
    assert (repo / ".githooks" / "pre-commit").stat().st_mode & 0o111
    assert (repo / "scripts" / "leakcheck.py").is_file()
    assert (repo / "AGENTS.md").read_text() == "# tally: how we work\n\nMode: fully vibed. Check: `make check`.\n"
    assert subprocess.run(["git", "config", "core.hooksPath"], cwd=repo, capture_output=True, text=True).stdout.strip() == ".githooks"
```

- [ ] **Step 2: Run them; watch them fail.**

```bash
uv run --quiet --with pytest --with pyyaml pytest plan-driven-development/tests/test_hooks.py plan-driven-development/tests/test_green_fixture.py -q
```

  Expected: `23 failed`, each for want of `templates/githooks`.

- [ ] **Step 3: Write the hooks.** `plan-driven-development/templates/githooks/pre-commit`:

```bash
#!/usr/bin/env bash
# Leak guard, run on every commit. Never bypass it with --no-verify (AGENTS.md, Security).
set -euo pipefail
root="$(git rev-parse --show-toplevel)"
if ! command -v gitleaks >/dev/null 2>&1; then
  echo "leak guard: gitleaks is not installed, so this is refused (AGENTS.md, Security)." >&2
  exit 1
fi
if ! gitleaks git --help >/dev/null 2>&1; then
  echo "leak guard: this gitleaks has no 'git' command; it needs 8.19 or later (AGENTS.md, Security)." >&2
  exit 1
fi
if ! command -v uv >/dev/null 2>&1; then
  echo "leak guard: uv is not on this shell's PATH, so this is refused (AGENTS.md, Security)." >&2
  exit 1
fi
gitleaks git --pre-commit --staged --redact --no-banner --config "$root/.githooks/gitleaks.toml" "$root"
exec uv run --quiet --script "$root/scripts/leakcheck.py" --staged
```

  `plan-driven-development/templates/githooks/commit-msg`:

```bash
#!/usr/bin/env bash
# Leak guard and format check for commit messages; git runs it on merges too. Never bypass it with
# --no-verify (AGENTS.md, Security).
set -euo pipefail
root="$(git rev-parse --show-toplevel)"
if ! command -v gitleaks >/dev/null 2>&1; then
  echo "leak guard: gitleaks is not installed, so this is refused (AGENTS.md, Security)." >&2
  exit 1
fi
if ! gitleaks git --help >/dev/null 2>&1; then
  echo "leak guard: this gitleaks has no 'git' command; it needs 8.19 or later (AGENTS.md, Security)." >&2
  exit 1
fi
if ! command -v uv >/dev/null 2>&1; then
  echo "leak guard: uv is not on this shell's PATH, so this is refused (AGENTS.md, Security)." >&2
  exit 1
fi
gitleaks stdin --redact --no-banner --config "$root/.githooks/gitleaks.toml" < "$1"
uv run --quiet --script "$root/scripts/leakcheck.py" --message "$1"
exec uv run --quiet --script "$root/scripts/commitmsg.py" "$1"
```

  `plan-driven-development/templates/githooks/pre-push`:

```bash
#!/usr/bin/env bash
# Leak guard, run on every push: scans everything going out, and refuses pushes to main, tags,
# deletions and force pushes. It fails closed: a push whose contents it can't work out is refused.
# Never bypass it with --no-verify (AGENTS.md, Security).
set -euo pipefail
root="$(git rev-parse --show-toplevel)"
if ! command -v gitleaks >/dev/null 2>&1; then
  echo "leak guard: gitleaks is not installed, so this is refused (AGENTS.md, Security)." >&2
  exit 1
fi
if ! gitleaks git --help >/dev/null 2>&1; then
  echo "leak guard: this gitleaks has no 'git' command; it needs 8.19 or later (AGENTS.md, Security)." >&2
  exit 1
fi
if ! command -v uv >/dev/null 2>&1; then
  echo "leak guard: uv is not on this shell's PATH, so this is refused (AGENTS.md, Security)." >&2
  exit 1
fi
zero="0000000000000000000000000000000000000000"
scanned=0
while read -r _local_ref local_sha remote_ref remote_sha; do
  case "$remote_ref" in
    refs/heads/main)
      echo "push guard: a push to main is refused; main changes only through a merged PR (AGENTS.md)." >&2
      exit 1 ;;
    refs/tags/*)
      echo "push guard: a tag push is refused; tags are Dan's (AGENTS.md)." >&2
      exit 1 ;;
  esac
  if [ "$local_sha" = "$zero" ]; then
    echo "push guard: deleting $remote_ref is refused; deleting branches is Dan's (AGENTS.md)." >&2
    exit 1
  fi
  if [ "$remote_sha" = "$zero" ]; then
    revs="$local_sha --not --remotes"
  else
    if ! git cat-file -e "$remote_sha^{commit}" 2>/dev/null; then
      echo "push guard: the remote's $remote_ref is at a commit this clone doesn't have; fetch first. Refused." >&2
      exit 1
    fi
    if ! git merge-base --is-ancestor "$remote_sha" "$local_sha"; then
      echo "push guard: this push would rewrite $remote_ref (a force push), refused (AGENTS.md)." >&2
      exit 1
    fi
    revs="$remote_sha..$local_sha"
  fi
  uv run --quiet --script "$root/scripts/leakcheck.py" --range "$revs" < /dev/null
  gitleaks git --redact --no-banner --log-opts="$revs" --config "$root/.githooks/gitleaks.toml" "$root" < /dev/null
  scanned=1
done
if [ "$scanned" = 1 ]; then
  exec uv run --quiet --script "$root/scripts/leakcheck.py" --tracked < /dev/null
fi
```

  `plan-driven-development/templates/githooks/pre-merge-commit`:

```bash
#!/usr/bin/env bash
# Leak guard for a merge git completes by itself: git runs this hook for it, not pre-commit.
# Never bypass it with --no-verify (AGENTS.md, Security).
set -euo pipefail
exec "$(dirname "$0")/pre-commit"
```

  `plan-driven-development/templates/githooks/gitleaks.toml`:

```toml
# gitleaks config: the default rules, nothing removed (AGENTS.md, Security).
[extend]
useDefault = true
```

  Then:

```bash
chmod 755 plan-driven-development/templates/githooks/pre-commit plan-driven-development/templates/githooks/commit-msg plan-driven-development/templates/githooks/pre-push plan-driven-development/templates/githooks/pre-merge-commit
shellcheck plan-driven-development/templates/githooks/pre-commit plan-driven-development/templates/githooks/commit-msg plan-driven-development/templates/githooks/pre-push plan-driven-development/templates/githooks/pre-merge-commit
```

- [ ] **Step 4: Run the tests; they pass.** `make test` and `make test-utc`. Expected: `142 passed`
  both times (119 + 23). On a machine without gitleaks 8.19+ or uv the tool-dependent tests skip:
  install them, as the hooks require.

- [ ] **Step 5: Prove the hooks read this machine's real denylist (Decision 11).** After Task 1's
  guard, a commit in a throwaway project must still run the leak check, which reads the denylist
  itself; the agent never names or reads it. In a shell where `LEAKCHECK_DENYLIST` is not set:

```bash
unset LEAKCHECK_DENYLIST
d=$(mktemp -d)
git -C "$d" init -q -b main
cp -R plan-driven-development/templates/githooks "$d/.githooks"
chmod 755 "$d/.githooks/pre-commit" "$d/.githooks/commit-msg" "$d/.githooks/pre-push" "$d/.githooks/pre-merge-commit"
mkdir "$d/scripts"
cp plan-driven-development/scripts/leakcheck.py plan-driven-development/scripts/commitmsg.py "$d/scripts/"
git -C "$d" config core.hooksPath .githooks
echo "fine" > "$d/a.md"
git -C "$d" add a.md
printf 'docs(repo): 🤖 a clean file\n\nProves the hooks run with this machine'"'"'s denylist.\n' > "$d/MSG"
git -C "$d" -c user.name=t -c user.email=t@example.invalid -c commit.gpgsign=false commit -q -F "$d/MSG"; echo "commit: exit=$?"
rm -rf "$d"
```

  Expected: `commit: exit=0`. `denylist not found` or a refusal from Dan's own guard is a stop: tell
  Dan.

- [ ] **Step 6: Commit.** Write `.git/PDD_MSG`:

```text
plan-driven-development: add the four git hooks

pre-commit runs gitleaks and the leak check on the staged files;
commit-msg runs both on the message, then the format checks; pre-push
scans everything going out (a new branch: everything the remote lacks),
the tracked files and gitleaks, and refuses main, tags, deletions and
force pushes; pre-merge-commit runs the commit checks on merges git
completes itself. Each refuses without gitleaks 8.19+ or uv. The drill
unstages with git rm --cached, since git restore --staged fails before
a repo's first commit. Shown with this machine's real denylist: a clean
commit in a throwaway project passes.

Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Task 8
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```bash
git add plan-driven-development/templates/githooks/pre-commit plan-driven-development/templates/githooks/commit-msg plan-driven-development/templates/githooks/pre-push plan-driven-development/templates/githooks/pre-merge-commit plan-driven-development/templates/githooks/gitleaks.toml plan-driven-development/tests/test_hooks.py plan-driven-development/tests/test_green_fixture.py
git commit -F .git/PDD_MSG
git log -1 --format='%(trailers)'
git ls-files -s plan-driven-development/templates/githooks
```

  Expected: mode `100755` for the four hooks.

- [ ] **Step 7: Review, look forward, close (Tier 1).**
  1. **Mechanical:** `make test` and `make test-utc`; shellcheck clean.
  2. **Backward review:** `mattpocock-skills:code-review` from `$(cat .git/PDD_BASE)`, the spec
     being this task, the spec's *Security hooks*, *Pushing, PRs and modes* and *Commits*, and
     local-ai's `.githooks/` and `spark/tests/test_hooks.py` at `e32096c`; plus the security
     checklist.
  3. **Forward review:** Task 9's shellcheck job names all four hooks and its Makefile's `hooks`
     target validates the denylist before `git config core.hooksPath .githooks`; Task 12's kickoff
     reference says to unstage the drill with `git rm --cached`.
  4. **Docs:** none yet.
  5. **Close:** **Now** → `Task 9: the project templates, open.` Commit
     `plan-driven-development: close Task 8: the four git hooks`:

  Write `.git/PDD_MSG`, filling each `<…>`:

```text
plan-driven-development: close Task 8: the four git hooks

Drift: <how the build departed from this plan, and why; or "none">
Rulings: <each ruling: what was decided, why, what it costs if wrong; or "none">
Phase-end: <findings deferred to the phase-end list, with severity and file; or "none">
Forward: <later tasks the forward review changed, and how; or "none">
Tier: 1
Rounds: <the reviews and re-reviews run>
Findings: <Critical n, Important n, Minor n, and what became of each>

Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Task 8
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```bash
git add docs/superpowers/plans/2026-10-15-plan-driven-development.md
git commit -F .git/PDD_MSG
git log -1 --format='%(trailers)'
for h in Drift Rulings Phase-end Forward Tier Rounds Findings; do
  git log -1 --format=%B | grep -q "^$h: ." || echo "missing $h"
done
```

  Expected: the trailers print the `Plan:` line; no `missing` line.

- [ ] **Step 8: Push (standing OK).**

  The skill's own leak check scans the range, with Dan's denylist. Push only through this block:

```bash
git fetch -q origin
range=origin/plan-driven-development..HEAD
if uv run --quiet --script plan-driven-development/scripts/leakcheck.py --range "$range" &&
   gitleaks git --log-opts="$range" --redact --no-banner . &&
   git log --format= --numstat "$range" | awk '$1 == "-" { print "binary, check it by eye: " $3; bad = 1 } END { exit bad }'; then
  git push origin plan-driven-development
else
  echo "STOP: not pushed. Tell Dan each finding's kind and file:line (never the matched text), or the binary's name."
fi
```

  Expected: the leak check prints nothing, gitleaks prints `no leaks found`, then the push. A
  `STOP` line means nothing was pushed: a leak or an unscanned binary is a stop that never relaxes;
  tell Dan the kind and `file:line`, never the excerpt.

***

### Task 9: The project templates: CI, Dependabot, `.gitignore` and the `Makefile`

**Tier:** 1 (CI's leak jobs and the Pages permissions) · **Scenarios:** S17; Dan's Makefile
preference.

**Files:**
- Create: `plan-driven-development/templates/ci.yml`, `dependabot.yml`, `gitignore`, `Makefile`
- Test: `plan-driven-development/tests/test_templates.py`

**Interfaces:**
- Consumes: the script paths `scripts/leakcheck.py` (Task 7) and `.githooks/*` (Task 8), as a
  project has them.
- Produces: the CI a project gets at kickoff, with the placeholder `__TEST_COMMAND__` that kickoff
  fills and the `site` and `pages` jobs it deletes for a project whose docs are read on GitHub; and
  the project's `Makefile`, with `__PROJECT__`, `__TEST_COMMAND__` and `__LINT_COMMAND__` to fill and
  the `docs` target deleted in the same case; its targets `help`, `hooks`, `check`, `test`,
  `test-utc`, `lint`, `leaks`, `docs` (Task 11's template names them).

- [ ] **Step 0: Record the base:** `git rev-parse HEAD > .git/PDD_BASE`.

- [ ] **Step 1: Write the failing test,** `plan-driven-development/tests/test_templates.py` (ported
  from local-ai's `spark/tests/test_workflows.py` at `e32096c`, plus the site, the deploy, the
  `.gitignore` patterns and the Makefile):

```python
"""Guarantees in the project templates that a later edit could quietly drop (S17). Ported from
local-ai's spark/tests/test_workflows.py (e32096c), with the site checks and the Pages deploy."""

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from helpers import SCRIPTS, TEMPLATES, denylist, git, git_repo, gitleaks_has_git

CI = TEMPLATES / "ci.yml"


def workflow() -> dict:
    return yaml.safe_load(CI.read_text())


def jobs() -> dict[str, dict]:
    return workflow()["jobs"]


def steps(job: str | None = None) -> list[dict]:
    chosen = [jobs()[job]] if job else jobs().values()
    return [step for j in chosen for step in j["steps"]]


def only_step(job_steps: list[dict], fragment: str) -> int:
    found = [i for i, step in enumerate(job_steps) if fragment in step.get("run", "")]
    assert len(found) == 1, (fragment, found)
    return found[0]


def test_every_job_has_a_time_limit():
    for name, job in jobs().items():
        limit = job.get("timeout-minutes")
        assert isinstance(limit, int) and 0 < limit <= 30, (name, limit)


def test_kickoff_fills_in_exactly_one_test_command():
    assert CI.read_text().count("__TEST_COMMAND__") == 2  # the run step and the header comment
    assert [s.get("run") for s in steps("tests")].count("__TEST_COMMAND__") == 1


def test_gitleaks_is_fetched_checked_and_run_in_separate_steps():
    leaks = steps("leaks")
    download = only_step(leaks, "https://github.com/gitleaks/gitleaks/releases/download/")
    check = only_step(leaks, "sha256sum -c")
    scan = only_step(leaks, "./gitleaks git")
    assert download < check < scan
    fetch = leaks[download]["run"]
    assert "--retry 3" in fetch and "--max-time 120" in fetch, fetch


def test_the_leak_check_reads_every_tracked_file_and_every_commit():
    leaks = steps("leaks")
    checkout = next(s for s in leaks if s.get("uses", "").startswith("actions/checkout@"))
    assert checkout["with"]["fetch-depth"] == 0
    tracked = leaks[only_step(leaks, "--tracked --ci")]
    assert tracked["env"]["CI"] == "true"
    assert tracked["run"] == "uv run --script scripts/leakcheck.py --tracked --ci"
    history = leaks[only_step(leaks, "git log -p")]
    assert history["env"]["CI"] == "true"
    log, scan = history["run"].strip().splitlines()
    out = re.fullmatch(r"git log -p (?:--\S+ )*--format='%H%n%B' > (\S+)", log.strip())
    assert out, log
    assert scan.strip() == f"uv run --script scripts/leakcheck.py --message {out.group(1)} --ci"


def test_no_checkout_keeps_the_job_token():
    checkouts = [s for s in steps() if s.get("uses", "").startswith("actions/checkout@")]
    assert checkouts
    for step in checkouts:
        assert step.get("with", {}).get("persist-credentials") is False, step


def test_every_action_is_pinned_by_a_full_commit_sha():
    for step in steps():
        if "uses" in step:
            assert re.fullmatch(r"[\w.-]+/[\w./-]+@[0-9a-f]{40}", step["uses"]), step["uses"]


def test_shellcheck_reads_all_four_hooks():
    (run,) = [s["run"] for s in steps("shellcheck") if "run" in s]
    for hook in ("pre-commit", "commit-msg", "pre-push", "pre-merge-commit"):
        assert f".githooks/{hook}" in run, hook


def test_the_site_job_checks_wrappers_unresolved_links_and_every_internal_link():
    site = steps("site")
    wrapper = site[only_step(site, "no wrapper for")]
    assert "docs/superpowers/*.md" in wrapper["run"]
    render = site[only_step(site, "quarto render website")]
    assert "Unable to resolve link target" in render["run"] and render["shell"] == "bash"
    lychee = [s for s in site if s.get("uses", "").startswith("lycheeverse/lychee-action@")]
    assert len(lychee) == 1 and "--offline" in lychee[0]["with"]["args"]
    assert lychee[0]["with"]["fail"] is True


def test_the_site_deploys_from_main_only_after_every_other_job_passed():
    ci = jobs()
    pages = ci["pages"]
    assert pages["if"] == "github.ref == 'refs/heads/main'"
    assert set(pages["needs"]) == set(ci) - {"pages"}
    assert pages["permissions"] == {"pages": "write", "id-token": "write"}
    assert [s["uses"].split("@")[0] for s in pages["steps"]] == ["actions/deploy-pages"]
    upload = [s for s in ci["site"]["steps"] if s.get("uses", "").startswith("actions/upload-pages-artifact@")]
    assert len(upload) == 1 and upload[0]["if"] == "github.ref == 'refs/heads/main'"
    assert upload[0]["with"]["path"] == "website/_site"
    for name, job in ci.items():
        assert name == "pages" or "permissions" not in job, name


def test_the_site_can_be_published_by_hand_and_main_runs_are_never_cancelled():
    wf = workflow()
    assert "workflow_dispatch" in wf[True]  # YAML 1.1 reads the bare key `on` as true
    assert wf["permissions"] == {"contents": "read"}
    assert wf["concurrency"]["cancel-in-progress"] == "${{ github.ref != 'refs/heads/main' }}"


def test_dependabot_proposes_actions_updates_a_few_at_a_time():
    config = yaml.safe_load((TEMPLATES / "dependabot.yml").read_text())
    (update,) = config["updates"]
    assert update["package-ecosystem"] == "github-actions" and update["directory"] == "/"
    assert update["schedule"] == {"interval": "weekly", "day": "friday"}
    assert update["open-pull-requests-limit"] <= 3


def test_the_gitignore_block_keeps_secrets_and_the_ledger_out():
    lines = (TEMPLATES / "gitignore").read_text().splitlines()
    for pattern in ("*.env", ".env.*", "*.pem", "*.key", "secrets.*", ".claude/settings.local.json",
                    ".mcp.local.json", ".vscode/settings.json", "*-inventory.txt", "ip-addr.txt",
                    "tailscale-status.txt", ".superpowers/", "website/_site/", "website/.render.log"):
        assert pattern in lines, pattern


# The Makefile: every project's front door for commands (Dan, 2026-10-15), for agents and people.

AFTER_MAKE_381 = (".ONESHELL", ".SHELLFLAGS", "::=", "$(file ", ".RECIPEPREFIX", "undefine ", "$(intcmp", "$(let ")


def filled_makefile(directory: Path, test: str = "echo tests-ran", lint: str = "echo lint-ran") -> Path:
    text = (TEMPLATES / "Makefile").read_text()
    for key, value in {"__PROJECT__": "demo", "__TEST_COMMAND__": test, "__LINT_COMMAND__": lint}.items():
        text = text.replace(key, value)
    (directory / "Makefile").write_text(text)
    return directory / "Makefile"


def make(directory: Path, *args: str, env=None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["make", *args], cwd=directory, capture_output=True, text=True, env=env)


def test_the_makefile_uses_only_gnu_make_381_features():
    # macOS ships GNU make 3.81; nothing newer may creep in.
    text = (TEMPLATES / "Makefile").read_text()
    for feature in AFTER_MAKE_381:
        assert feature not in text, feature
    assert not re.search(r"^\w+\s*!=", text, re.MULTILINE)


def test_kickoff_fills_the_test_and_lint_commands():
    recipes = [line for line in (TEMPLATES / "Makefile").read_text().splitlines() if line.startswith("\t")]
    assert [r for r in recipes if "__TEST_COMMAND__" in r] == ["\t__TEST_COMMAND__", "\tTZ=UTC __TEST_COMMAND__"]
    assert [r for r in recipes if "__LINT_COMMAND__" in r] == ["\t__LINT_COMMAND__"]


def test_make_alone_lists_every_target(tmp_path):
    filled_makefile(tmp_path)
    out = make(tmp_path).stdout
    for target in ("help", "hooks", "check", "test", "test-utc", "lint", "leaks", "docs"):
        assert re.search(rf"^  {re.escape(target)} ", out, re.MULTILINE), (target, out)


def test_check_runs_the_suite_again_under_utc_then_lint_then_the_leak_scan(tmp_path):
    filled_makefile(tmp_path)
    lines = make(tmp_path, "-n", "check").stdout.splitlines()
    assert lines == ["echo tests-ran", "TZ=UTC echo tests-ran", "echo lint-ran",
                     "uv run --quiet --script scripts/leakcheck.py --tracked"], lines


def test_make_check_runs_clean_in_a_fresh_project(tmp_path):
    repo = git_repo(tmp_path)
    filled_makefile(repo)
    (repo / "scripts").mkdir()
    shutil.copy2(SCRIPTS / "leakcheck.py", repo / "scripts" / "leakcheck.py")
    (repo / "README.md").write_text("# demo\n")
    git(repo, "add", "Makefile", "scripts/leakcheck.py", "README.md")
    result = make(repo, "check", env={**os.environ, "LEAKCHECK_DENYLIST": str(denylist(tmp_path))})
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.count("tests-ran") == 4 and result.stdout.count("lint-ran") == 2  # echoed, then run


def test_hooks_checks_the_denylist_before_turning_the_hooks_on(tmp_path):
    filled_makefile(tmp_path)
    lines = make(tmp_path, "-n", "hooks").stdout.splitlines()
    validate = next(i for i, line in enumerate(lines) if "--message /dev/null" in line)
    turn_on = lines.index("git config core.hooksPath .githooks")
    assert validate < turn_on


@pytest.mark.skipif(not gitleaks_has_git() or shutil.which("uv") is None, reason="needs gitleaks 8.19+ and uv")
def test_hooks_refuses_without_a_denylist_and_leaves_the_hooks_off(tmp_path):
    repo = git_repo(tmp_path)
    filled_makefile(repo)
    (repo / "scripts").mkdir()
    shutil.copy2(SCRIPTS / "leakcheck.py", repo / "scripts" / "leakcheck.py")
    result = make(repo, "hooks", env={**os.environ, "LEAKCHECK_DENYLIST": str(tmp_path / "no-such-denylist")})
    assert result.returncode != 0
    assert "stop and tell Dan" in result.stdout + result.stderr
    unset = subprocess.run(["git", "config", "--local", "core.hooksPath"], cwd=repo, capture_output=True, text=True)
    assert unset.stdout == ""


def test_docs_refuses_a_doc_with_no_wrapper_before_rendering(tmp_path):
    repo = git_repo(tmp_path)
    filled_makefile(repo)
    (repo / "docs/superpowers/specs").mkdir(parents=True)
    (repo / "docs/superpowers/specs/2026-01-01-demo-design.md").write_text("# Demo design\n")
    git(repo, "add", "Makefile", "docs/superpowers/specs/2026-01-01-demo-design.md")
    result = make(repo, "docs")
    assert result.returncode != 0
    assert ("no wrapper for docs/superpowers/specs/2026-01-01-demo-design.md "
            "(expected website/superpowers/specs/2026-01-01-demo-design.md)") in result.stdout
    assert not (repo / "website/.render.log").exists()  # it stopped before Quarto


def test_docs_checks_wrappers_unresolved_links_and_internal_links(tmp_path):
    filled_makefile(tmp_path)
    out = make(tmp_path, "-n", "docs").stdout
    for fragment in ("no wrapper for", "quarto render website", "Unable to resolve link target", "lychee --offline"):
        assert fragment in out, fragment
```

- [ ] **Step 2: Run it; watch it fail.**
  `uv run --quiet --with pytest --with pyyaml pytest plan-driven-development/tests/test_templates.py -q`.
  Expected: `21 failed`, each with `FileNotFoundError: … templates/ci.yml` (or `dependabot.yml`,
  `gitignore`, `Makefile`).

- [ ] **Step 3: Write the templates.** `plan-driven-development/templates/ci.yml`:

```yaml
name: ci
# Made from plan-driven-development's template. Runs on every push and PR; on main it also publishes
# the docs site (the pages job), and so does a run by hand from the Actions tab on main. Kickoff
# replaces __TEST_COMMAND__ with the project's suite and lint, adds the setup steps the project
# needs to the tests job, and deletes the site and pages jobs when the docs are read on GitHub
# instead (AGENTS.md, Docs).
on:
  push:
  pull_request:
  workflow_dispatch:
permissions:
  contents: read
# A newer push cancels a branch's older runs, except on main, where a deploy may be running; a task
# counts as closed when any run from its closing commit onward is green (AGENTS.md, Each task).
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}

# Every job gets a time limit, so a hung step fails instead of holding a runner for six hours.
jobs:
  tests:
    runs-on: ubuntu-24.04
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - uses: astral-sh/setup-uv@c18668ad3cf93ea998bef934396af7bb5c839dc7 # v10.2.0
        with:
          version: "0.12.18"
      - run: "__TEST_COMMAND__"

  leaks:
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          fetch-depth: 0
          persist-credentials: false
      - uses: astral-sh/setup-uv@c18668ad3cf93ea998bef934396af7bb5c839dc7 # v10.2.0
        with:
          version: "0.12.18"
      # Three gitleaks steps, so a red one names its cause: a failed download is a network problem,
      # a failed checksum is a tampered or corrupt download, and only the scan reports leaks.
      - name: download gitleaks
        run: curl -fsSL --retry 3 --max-time 120 -o gitleaks.tar.gz "https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz"
      - name: check gitleaks against its pinned checksum, then unpack it
        run: |
          echo "551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb  gitleaks.tar.gz" | sha256sum -c -
          tar -xzf gitleaks.tar.gz gitleaks
      - name: gitleaks over the whole history
        run: ./gitleaks git --redact --no-banner -v --config .githooks/gitleaks.toml .
      - name: the leak check over every tracked file
        env:
          CI: "true"
        run: uv run --script scripts/leakcheck.py --tracked --ci
      # gitleaks' rules don't cover addresses, so the leak check also reads every commit's patches
      # (--cc adds a merge's conflict resolutions) and messages, not only today's tree.
      - name: the leak check over every commit's patches and messages
        env:
          CI: "true"
        run: |
          git log -p --cc --format='%H%n%B' > "$RUNNER_TEMP/history.txt"
          uv run --script scripts/leakcheck.py --message "$RUNNER_TEMP/history.txt" --ci

  shellcheck:
    runs-on: ubuntu-24.04
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - run: shellcheck .githooks/pre-commit .githooks/commit-msg .githooks/pre-push .githooks/pre-merge-commit

  site:
    runs-on: ubuntu-24.04
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - name: every doc shown on the site has its wrapper
        shell: bash
        run: |
          missing=0
          while IFS= read -r -d '' doc; do
            wrapper="website/${doc#docs/}"
            if [ ! -f "$wrapper" ]; then echo "no wrapper for $doc (expected $wrapper)"; missing=1; fi
          done < <(git ls-files -z 'docs/superpowers/*.md')
          exit "$missing"
      - uses: quarto-dev/quarto-actions/setup@8a96df13519ee81fd526f2dfca5962811136661b # v2.2.0
        with:
          version: "1.11.5"
      # Quarto only warns about a link it can't resolve; here that fails the job.
      - name: render, failing on a link Quarto can't resolve
        shell: bash
        run: |
          quarto render website 2>&1 | tee "$RUNNER_TEMP/render.log"
          if grep -q "Unable to resolve link target" "$RUNNER_TEMP/render.log"; then exit 1; fi
      # A ../ link out of the site breaks with no warning at all, so every internal link is checked.
      - name: every internal link in the rendered site resolves
        uses: lycheeverse/lychee-action@e7477775783ea5526144ba13e8db5eec57747ce8 # v2.9.0
        with:
          args: --offline --no-progress website/_site
          fail: true
      # On main, the rendered site becomes the artifact the pages job deploys.
      - if: github.ref == 'refs/heads/main'
        uses: actions/upload-pages-artifact@fc324d3547104276b827a68afc52ff2a11cc49c9 # v5.0.0
        with:
          path: website/_site

  # Publishes the site with GitHub's Pages actions ("GitHub Actions" as the Pages source), so there
  # is no gh-pages branch keeping every rendered version. It runs only on main and only once every
  # other job passed, so nothing reaches the public site past a failed test or leak scan, and it
  # alone gets Pages' permissions. One deploy at a time: a newer one waits.
  pages:
    if: github.ref == 'refs/heads/main'
    needs: [tests, leaks, shellcheck, site]
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    permissions:
      pages: write
      id-token: write
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    concurrency:
      group: pages
      cancel-in-progress: false
    steps:
      - id: deployment
        uses: actions/deploy-pages@368f82528645a54fb793d4d04e342629a3f51346 # v5.0.1
```

  `plan-driven-development/templates/dependabot.yml`:

```yaml
# Made from plan-driven-development's template: proposals for the pinned Actions, Fridays, a few at
# a time. Actions stay pinned by commit SHA; Dependabot moves a SHA pin and its version comment
# together. A project with a uv lock adds a `uv` entry with `cooldown: default-days: 7`, so nothing
# under a week old is proposed. Dependabot's PRs are Dan's to merge, into main, between phases.
version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
      day: friday
    open-pull-requests-limit: 3
    commit-message:
      prefix: "ci(repo)"
```

  `plan-driven-development/templates/gitignore` (local-ai's hardening block, including its agent and
  editor state and its captured-output patterns, plus the ledger and the rendered site):

```gitignore
# ---------------------------------------------------------------------------
# Public-repo hardening (plan-driven-development's template): git history is
# permanent, so these must never reach a commit in the first place.
# ---------------------------------------------------------------------------

# Credentials, keys, certificates
*.pem
*.key
*.crt
*.p12
*.pfx
id_rsa*
id_ecdsa*
id_ed25519*
*.kdbx
secrets.*
*secret*.yml
*secret*.yaml
*credentials*.json
# A service's secret file is <service>.env, so a copied or rendered one must never stage. If a
# non-secret template is ever tracked, re-include it by name with a `!` line below these.
*.env
.env
.env.*

# Local agent and editor state that can carry paths and tokens
.claude/settings.local.json
.mcp.local.json
.vscode/settings.json

# Captured machine output that commonly carries identifiers
*-inventory.txt
ip-addr.txt
tailscale-status.txt

# superpowers' plan-runner workspace (its ledger); the closing commits copy what matters out of it
.superpowers/

# The rendered docs site
website/_site/
website/.quarto/
website/.render.log
```

  `plan-driven-development/templates/Makefile` (every project's front door, Dan's preference; GNU
  make 3.81 features only):

```make
# __PROJECT__: the front door for every command, for agents and people alike. `make help` lists
# the targets. Made from plan-driven-development's template, kept to GNU make 3.81 features so it
# runs on macOS as well as Linux. Kickoff fills __TEST_COMMAND__ and __LINT_COMMAND__, and deletes
# the docs target (and its .PHONY entry) when the docs are read on GitHub instead (AGENTS.md, Docs).
# A command anyone will run more than once becomes a target here.

SHELL := /bin/bash
LEAKCHECK := uv run --quiet --script scripts/leakcheck.py
.DEFAULT_GOAL := help
.PHONY: help hooks check test test-utc lint leaks docs

help: ## List the targets
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-10s %s\n", $$1, $$2}'

hooks: ## Turn this clone's leak and commit-message hooks on, after checking their tools and the denylist
	@command -v gitleaks >/dev/null || { echo "install gitleaks 8.19 or later first"; exit 1; }
	@gitleaks git --help >/dev/null 2>&1 || { echo "this gitleaks has no 'git' command: the hooks need 8.19 or later"; exit 1; }
	@command -v uv >/dev/null || { echo "install uv first"; exit 1; }
	@$(LEAKCHECK) --message /dev/null || { echo "the denylist is missing or invalid: stop and tell Dan"; exit 1; }
	git config core.hooksPath .githooks
	@echo "hooks on for this clone"

check: test test-utc lint leaks ## Everything a task runs before review: the suite, again under TZ=UTC, lint, the leak scan

test: ## Run the test suite
	__TEST_COMMAND__

test-utc: ## Run the test suite again under TZ=UTC, as CI does
	TZ=UTC __TEST_COMMAND__

lint: ## Run the linters
	__LINT_COMMAND__

leaks: ## Scan every tracked file with the leak check and this machine's denylist
	$(LEAKCHECK) --tracked

docs: ## Render the site; every doc has its wrapper, no unresolved link, every internal link resolves
	@missing=0; while IFS= read -r -d '' doc; do wrapper="website/$${doc#docs/}"; \
	  if [ ! -f "$$wrapper" ]; then echo "no wrapper for $$doc (expected $$wrapper)"; missing=1; fi; \
	done < <(git ls-files -z 'docs/superpowers/*.md'); exit $$missing
	@set -o pipefail; quarto render website 2>&1 | tee website/.render.log
	@! grep -q "Unable to resolve link target" website/.render.log || { echo "a link Quarto couldn't resolve: see above"; exit 1; }
	@if command -v lychee >/dev/null; then lychee --offline --no-progress website/_site; \
	else echo "lychee isn't installed here: CI checks every internal link"; fi
```

- [ ] **Step 4: Run the tests; they pass.** `make test` and `make test-utc`. Expected: `163 passed`
  both times (142 + 21).

- [ ] **Step 5: Run the Makefile on Linux too** (Ubuntu 24.04's GNU make 4.3), if Docker is up; if
  it isn't, record "Linux run pending" under `Phase-end:` in the closing commit:

```bash
docker run --rm -v "$PWD":/src:ro ubuntu:24.04 bash -c '
set -e
apt-get update -qq >/dev/null && apt-get install -y -qq make git >/dev/null
make --version | head -1
mkdir -p /t && cd /t && git init -q
sed -e "s/__PROJECT__/demo/" -e "s/__TEST_COMMAND__/echo tests-ran/" -e "s/__LINT_COMMAND__/echo lint-ran/" /src/plan-driven-development/templates/Makefile > Makefile
make && make -n check && make test test-utc lint
mkdir -p docs/superpowers/specs && echo "# d" > docs/superpowers/specs/x.md && git add Makefile docs
if make docs; then echo "docs should have refused"; exit 1; fi
make -f /src/Makefile
'
```

  Expected: `GNU Make 4.3`, the target list, the four `check` commands, `tests-ran` twice and
  `lint-ran`, `no wrapper for docs/superpowers/specs/x.md …`, and this repo's own target list.

- [ ] **Step 6: Commit.** Write `.git/PDD_MSG`:

```text
plan-driven-development: add the CI, Dependabot, .gitignore and Makefile templates

ci.yml: the tests, the leak jobs (gitleaks over the history, pinned by
checksum; the leak check over every tracked file and every commit), the
site checks, and a Pages deploy that runs on main only after every other
job passed and alone holds Pages' permissions. Every action is pinned by
SHA. The .gitignore block is local-ai's hardening. The Makefile is every
project's front door (Dan's preference): help, hooks, check (the suite,
again under TZ=UTC, lint, the leak scan), test, test-utc, lint, leaks
and docs, on GNU make 3.81 and 4.3.

Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Task 9
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```bash
git add plan-driven-development/templates/ci.yml plan-driven-development/templates/dependabot.yml plan-driven-development/templates/gitignore plan-driven-development/templates/Makefile plan-driven-development/tests/test_templates.py
git commit -F .git/PDD_MSG
git log -1 --format='%(trailers)'
```

- [ ] **Step 7: Review, look forward, close (Tier 1).**
  1. **Mechanical:** `make test` and `make test-utc`; Step 5.
  2. **Backward review:** `mattpocock-skills:code-review` from `$(cat .git/PDD_BASE)`, the spec
     being this task, the spec's *Docs and the site* (deploy), *Security hooks* (CI) and local-ai's
     `ci.yml` at `e32096c`; plus the security checklist (every action pinned by SHA to a version at
     least a week old; no persisted job token; the deploy alone writes to Pages).
  3. **Forward review:** Task 10's site test runs CI's wrapper-check step from this file; Task 11's
     template names the Makefile's targets; Task 12's kickoff reference says to fill
     `__TEST_COMMAND__` and `__LINT_COMMAND__` and when to delete `site`, `pages` and `docs`.
  4. **Docs:** none yet.
  5. **Close:** **Now** → `Task 10: the docs templates, open.` Commit
     `plan-driven-development: close Task 9: the project templates`:

  Write `.git/PDD_MSG`, filling each `<…>`:

```text
plan-driven-development: close Task 9: the project templates

Drift: <how the build departed from this plan, and why; or "none">
Rulings: <each ruling: what was decided, why, what it costs if wrong; or "none">
Phase-end: <findings deferred to the phase-end list, with severity and file; or "none">
Forward: <later tasks the forward review changed, and how; or "none">
Tier: 1
Rounds: <the reviews and re-reviews run>
Findings: <Critical n, Important n, Minor n, and what became of each>

Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Task 9
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```bash
git add docs/superpowers/plans/2026-10-15-plan-driven-development.md
git commit -F .git/PDD_MSG
git log -1 --format='%(trailers)'
for h in Drift Rulings Phase-end Forward Tier Rounds Findings; do
  git log -1 --format=%B | grep -q "^$h: ." || echo "missing $h"
done
```

  Expected: the trailers print the `Plan:` line; no `missing` line.

- [ ] **Step 8: Push (standing OK).**

  The skill's own leak check scans the range, with Dan's denylist. Push only through this block:

```bash
git fetch -q origin
range=origin/plan-driven-development..HEAD
if uv run --quiet --script plan-driven-development/scripts/leakcheck.py --range "$range" &&
   gitleaks git --log-opts="$range" --redact --no-banner . &&
   git log --format= --numstat "$range" | awk '$1 == "-" { print "binary, check it by eye: " $3; bad = 1 } END { exit bad }'; then
  git push origin plan-driven-development
else
  echo "STOP: not pushed. Tell Dan each finding's kind and file:line (never the matched text), or the binary's name."
fi
```

  Expected: the leak check prints nothing, gitleaks prints `no leaks found`, then the push. A
  `STOP` line means nothing was pushed: a leak or an unscanned binary is a stop that never relaxes;
  tell Dan the kind and `file:line`, never the excerpt.

***

### Task 10: The docs templates: the Quarto site, the root files and the message templates

**Tier:** 2 · **Scenarios:** the docs part of S02 (closing-commit template); the site checks.

**Files:**
- Create: `plan-driven-development/templates/quarto/_quarto.yml`, `index.qmd`, `_overview.qmd`,
  `architecture.qmd`, `design.qmd`, `wrapper.md`, `changelog.md`, `how-we-work.md`,
  `_diagram-zoom.html`
- Create: `plan-driven-development/templates/CLAUDE.md`, `issue-tracker.md`, `close-task.txt`, `wip.txt`
- Test: `plan-driven-development/tests/test_site.py`

**Interfaces:**
- Consumes: `templates/ci.yml`'s wrapper-check step (Task 9); `commitmsg.problems` (Task 3).
- Produces: the files kickoff copies for a site project (placeholders `__PROJECT__`,
  `__SITE_URL__`, `__REPO_URL__`, `__SPEC__`; a wrapper's `__TITLE__` and `__PATH__`), and the
  message templates a project keeps in `docs/agents/`.

- [ ] **Step 0: Record the base:** `git rev-parse HEAD > .git/PDD_BASE`.

- [ ] **Step 1: Write the failing test,** `plan-driven-development/tests/test_site.py`:

```python
"""The docs templates: a sample site rendered from them with real Quarto, CI's wrapper check run
against it, and the commit-message templates checked once filled in. Rendering skips without
Quarto; lychee runs only in CI."""

import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from helpers import TEMPLATES, load_script

commitmsg = load_script("commitmsg")
needs_quarto = pytest.mark.skipif(shutil.which("quarto") is None, reason="needs Quarto on PATH")

SPEC = "2026-01-01-demo-design"
PLAN = "2026-01-01-demo"


def fill(text: str) -> str:
    return (text.replace("__PROJECT__", "demo").replace("__SITE_URL__", "https://example.invalid/demo/")
            .replace("__REPO_URL__", "https://example.invalid/demo-repo").replace("__SPEC__", SPEC))


def sample_project(tmp_path: Path) -> Path:
    """A site project as kickoff leaves it: root files, a spec and a plan that link to each other,
    and the website/ folder from the templates with a wrapper for each doc."""
    repo = tmp_path / "demo"
    (repo / "docs/superpowers/specs").mkdir(parents=True)
    (repo / "docs/superpowers/plans").mkdir(parents=True)
    (repo / "README.md").write_text("# demo\n\nA demo. The docs are at <https://example.invalid/demo/>.\n")
    (repo / "AGENTS.md").write_text("# demo: how we work\n\nThe rules, in `docs/agents/`.\n")
    (repo / "CHANGELOG.md").write_text("# Changelog\n\n## 2026-01-01\n\n- Kickoff.\n")
    (repo / f"docs/superpowers/specs/{SPEC}.md").write_text(
        f"# Demo: design spec\n\nThe plan is [Phase 1](../plans/{PLAN}.md).\n"
    )
    (repo / f"docs/superpowers/plans/{PLAN}.md").write_text(
        f"# Demo plan\n\n**Spec:** [the spec](../specs/{SPEC}.md)\n\n***\n\n### Task 1: start\n"
    )
    site = repo / "website"
    shutil.copytree(TEMPLATES / "quarto", site, ignore=shutil.ignore_patterns("wrapper.md"))
    for path in site.iterdir():
        if path.suffix in (".yml", ".qmd", ".md"):
            path.write_text(fill(path.read_text()))
    wrapper = (TEMPLATES / "quarto" / "wrapper.md").read_text()
    for kind, name in (("specs", SPEC), ("plans", PLAN)):
        (site / "superpowers" / kind).mkdir(parents=True, exist_ok=True)
        (site / "superpowers" / kind / f"{name}.md").write_text(
            wrapper.replace("__TITLE__", name).replace("__PATH__", f"{kind}/{name}.md")
        )
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    return repo


def wrapper_check(repo: Path) -> subprocess.CompletedProcess[str]:
    """CI's wrapper check, run exactly as the template's step gives it."""
    site = yaml.safe_load((TEMPLATES / "ci.yml").read_text())["jobs"]["site"]["steps"]
    (step,) = [s for s in site if "no wrapper for" in s.get("run", "")]
    return subprocess.run(["bash", "-c", step["run"]], cwd=repo, capture_output=True, text=True)


def test_ci_finds_a_doc_without_its_wrapper(tmp_path):
    repo = sample_project(tmp_path)
    assert wrapper_check(repo).returncode == 0
    (repo / f"website/superpowers/plans/{PLAN}.md").unlink()
    result = wrapper_check(repo)
    assert result.returncode == 1
    assert f"no wrapper for docs/superpowers/plans/{PLAN}.md" in result.stdout


@needs_quarto
def test_the_sample_site_renders_with_working_cross_links(tmp_path):
    repo = sample_project(tmp_path)
    result = subprocess.run(["quarto", "render", "website"], cwd=repo, capture_output=True, text=True)
    log = result.stdout + result.stderr
    assert result.returncode == 0, log
    assert "Unable to resolve link target" not in log, log
    built = repo / "website/_site/superpowers"
    spec_html = (built / f"specs/{SPEC}.html").read_text()
    plan_html = (built / f"plans/{PLAN}.html").read_text()
    assert f'href="../../superpowers/plans/{PLAN}.html"' in spec_html
    assert f'href="../../superpowers/specs/{SPEC}.html"' in plan_html
    home = (repo / "website/_site/index.html").read_text()
    assert "A demo." in home and "mermaid" in home


@needs_quarto
def test_a_link_quarto_cant_resolve_fails_the_render_check(tmp_path):
    repo = sample_project(tmp_path)
    spec = repo / f"docs/superpowers/specs/{SPEC}.md"
    spec.write_text(spec.read_text() + "\nSee [a missing page](../plans/missing.md).\n")
    result = subprocess.run(["quarto", "render", "website"], cwd=repo, capture_output=True, text=True)
    assert "Unable to resolve link target" in result.stdout + result.stderr


def filled(template: str) -> str:
    text = (TEMPLATES / template).read_text()
    text = text.replace("Task N", "Task 3")
    return re.sub(r"<[^>]*>", "x", text)


@pytest.mark.parametrize("template", ["close-task.txt", "wip.txt"])
def test_the_message_templates_pass_the_format_checks_once_filled(template):
    assert commitmsg.problems(filled(template)) == []


def test_claude_md_only_reads_agents_md():
    assert (TEMPLATES / "CLAUDE.md").read_text() == "@AGENTS.md\n"
```

- [ ] **Step 2: Run it; watch it fail.**
  `uv run --quiet --with pytest --with pyyaml pytest plan-driven-development/tests/test_site.py -q`.
  Expected: `6 failed` (`FileNotFoundError` for `templates/quarto`, `CLAUDE.md`, `close-task.txt`,
  `wip.txt`).

- [ ] **Step 3: Write the Quarto templates** in `plan-driven-development/templates/quarto/`.
  `_quarto.yml`:

```yaml
# Made from plan-driven-development's template. Kickoff replaces __PROJECT__, __SITE_URL__ and
# __REPO_URL__. The pages show the repo's own files through includes and wrappers (AGENTS.md, Docs).
project:
  type: website
  output-dir: _site

website:
  title: "__PROJECT__"
  site-url: "__SITE_URL__"
  repo-url: "__REPO_URL__"
  repo-subdir: website
  navbar:
    left:
      - text: Architecture
        href: architecture.qmd
      - text: Design
        href: design.qmd
      - text: Changelog
        href: changelog.md
      - text: How we work
        href: how-we-work.md

format:
  html:
    theme: cosmo
    toc: true
    mermaid:
      theme: neutral
    include-after-body: _diagram-zoom.html
```

  `index.qmd`:

```markdown
---
pagetitle: "__PROJECT__"
---

{{< include /../README.md >}}

{{< include _overview.qmd >}}

**Solid** parts are built; **dashed** parts are planned, labelled with the phase that brings them.
[Architecture](architecture.qmd) has every diagram.
```

  `_overview.qmd`:

````markdown
```{mermaid}
%%| column: page
%% The overview: one file, included by index.qmd and architecture.qmd, never copied. It changes in
%% the same commit as any part or path it shows (AGENTS.md, Docs).
flowchart TB
  classDef planned stroke-dasharray: 5 5
  person["a person"] --> app["__PROJECT__"]
  app --> data[("its data")]
  app -.-> later["what a later phase adds · Phase 2"]:::planned
```
````

  `architecture.qmd`:

````markdown
---
title: "Architecture"
---

Every diagram of the project lives on this page; other pages link here and never draw their own
copy. Built parts are solid; planned parts are dashed and labelled with the phase that brings them.

## Overview

{{< include _overview.qmd >}}

## How a request flows

```{mermaid}
flowchart LR
  classDef planned stroke-dasharray: 5 5
  person["a person"] --> entry["the entry point"]
  entry --> work["the work it does"]
  work --> data[("its data")]
  entry -.-> later["a later path · Phase 2"]:::planned
```
````

  `design.qmd`:

```markdown
---
title: "Design"
---

The spec, the plans, the Q&A pages and the retros, as written in `docs/superpowers/`. Each page here
shows one of those files through a wrapper; the files themselves are the source. A new plan, Q&A
page or retro gets its wrapper and its line here in the commit that adds it.

- [The spec](superpowers/specs/__SPEC__.md)
```

  `wrapper.md`:

```markdown
---
pagetitle: "__TITLE__"
---

{{< include /../docs/superpowers/__PATH__ >}}
```

  `changelog.md`:

```markdown
---
pagetitle: "Changelog"
---

{{< include /../CHANGELOG.md >}}
```

  `how-we-work.md`:

```markdown
---
pagetitle: "How we work"
---

{{< include /../AGENTS.md >}}
```

  `_diagram-zoom.html`, local-ai's `website/_diagram-zoom.html` at `e32096c`, byte for byte (its
  SHA-256 is `a3ac9a7af682e68cd5cd43940b80f6ec85f67a986a8c093d3e3227e115827881`). Before copying it,
  check whether Quarto 1.11.5's lightbox now opens wide Mermaid diagrams without cropping (the
  reason local-ai wrote it); if it does, use the lightbox instead and record a Ruling:

```html
<!-- Click or tap any Mermaid diagram to open it full-screen, at its natural size, to zoom and pan.
     Included after the body of every page by _quarto.yml. No library: a <dialog> and a copy of the SVG.
     Quarto's own lightbox needs mermaid-format: png, whose renders cropped wide diagrams (2026-10-14). -->
<style>
  figure.diagram-zoomable { cursor: zoom-in; }
  figure.diagram-zoomable:focus-visible { outline: 2px solid var(--bs-primary, #2780e3); outline-offset: 4px; }
  .diagram-zoom-hint { margin: 0.25rem 0 0; font-size: 0.8rem; color: var(--bs-secondary-color, #6c757d); text-align: right; }
  dialog.diagram-zoom { width: 100vw; height: 100vh; max-width: none; max-height: none; margin: 0; padding: 0;
    border: 0; background: var(--bs-body-bg, #fff); }
  dialog.diagram-zoom[open] { display: flex; flex-direction: column; }
  .diagram-zoom-bar { display: flex; gap: 0.5rem; align-items: center; justify-content: flex-end; padding: 0.5rem 1rem;
    border-bottom: 1px solid var(--bs-border-color, #dee2e6); }
  .diagram-zoom-bar span { margin-right: auto; font-size: 0.9rem; color: var(--bs-secondary-color, #6c757d); }
  .diagram-zoom-bar button { min-width: 2.5rem; padding: 0.25rem 0.75rem; border: 1px solid var(--bs-border-color, #dee2e6);
    border-radius: 0.375rem; background: var(--bs-body-bg, #fff); color: var(--bs-body-color, #373a3c); }
  .diagram-zoom-view { flex: 1; overflow: auto; cursor: grab; touch-action: pan-x pan-y pinch-zoom; }
  .diagram-zoom-view.dragging { cursor: grabbing; user-select: none; }
  .diagram-zoom-view svg { display: block; margin: 1rem auto; max-width: none !important; height: auto; }
</style>
<script>
(function () {
  "use strict";

  var STEP = 1.25, MIN = 0.1, MAX = 4;
  var dialog, view, label, svg, naturalW = 0, naturalH = 0, zoom = 1;

  function build() {
    dialog = document.createElement("dialog");
    dialog.className = "diagram-zoom";
    dialog.setAttribute("aria-label", "Enlarged diagram");
    dialog.innerHTML =
      '<div class="diagram-zoom-bar">' +
      "<span>Drag or scroll to move around. Esc closes.</span>" +
      '<button type="button" data-act="out" aria-label="Zoom out">−</button>' +
      '<button type="button" data-act="actual" aria-label="Actual size">100%</button>' +
      '<button type="button" data-act="in" aria-label="Zoom in">+</button>' +
      '<button type="button" data-act="fit">Fit</button>' +
      '<button type="button" data-act="close" aria-label="Close">✕</button>' +
      "</div>" +
      '<div class="diagram-zoom-view"></div>';
    document.body.appendChild(dialog);
    view = dialog.querySelector(".diagram-zoom-view");
    label = dialog.querySelector('[data-act="actual"]');

    dialog.querySelector(".diagram-zoom-bar").addEventListener("click", function (e) {
      var button = e.target.closest("button");
      var act = button && button.getAttribute("data-act");
      if (act === "in") setZoom(zoom * STEP);
      if (act === "out") setZoom(zoom / STEP);
      if (act === "actual") setZoom(1);
      if (act === "fit") setZoom(fitZoom());
      if (act === "close") dialog.close();
    });
    dialog.addEventListener("keydown", function (e) {
      if (e.key === "+" || e.key === "=") setZoom(zoom * STEP);
      if (e.key === "-") setZoom(zoom / STEP);
      if (e.key === "0") setZoom(1);
    });
    dialog.addEventListener("close", function () { view.innerHTML = ""; svg = null; });

    // A trackpad pinch arrives as a wheel event with ctrlKey set.
    view.addEventListener("wheel", function (e) {
      if (!e.ctrlKey) return;
      e.preventDefault();
      setZoom(zoom * Math.pow(STEP, -e.deltaY / 100), e.clientX, e.clientY);
    }, { passive: false });

    // Drag to pan with a mouse; touch keeps the browser's own scrolling.
    var drag = null;
    view.addEventListener("pointerdown", function (e) {
      if (e.pointerType !== "mouse" || e.button !== 0) return;
      drag = { x: e.clientX, y: e.clientY, left: view.scrollLeft, top: view.scrollTop };
      view.classList.add("dragging");
      view.setPointerCapture(e.pointerId);
    });
    view.addEventListener("pointermove", function (e) {
      if (!drag) return;
      view.scrollLeft = drag.left - (e.clientX - drag.x);
      view.scrollTop = drag.top - (e.clientY - drag.y);
    });
    function endDrag() { drag = null; view.classList.remove("dragging"); }
    view.addEventListener("pointerup", endDrag);
    view.addEventListener("pointercancel", endDrag);
  }

  function fitZoom() {
    return Math.min((view.clientWidth - 32) / naturalW, (view.clientHeight - 32) / naturalH, 1);
  }

  // Zoom about a point on screen (the view's centre by default), so what is under it stays put.
  function setZoom(z, cx, cy) {
    if (!svg) return;
    z = Math.max(MIN, Math.min(MAX, z));
    var rect = view.getBoundingClientRect();
    var px = (cx === undefined ? rect.width / 2 : cx - rect.left);
    var py = (cy === undefined ? rect.height / 2 : cy - rect.top);
    var fx = (view.scrollLeft + px) / view.scrollWidth;
    var fy = (view.scrollTop + py) / view.scrollHeight;
    zoom = z;
    svg.style.width = naturalW * zoom + "px";
    view.scrollLeft = fx * view.scrollWidth - px;
    view.scrollTop = fy * view.scrollHeight - py;
    label.textContent = Math.round(zoom * 100) + "%";
  }

  function open(figure) {
    var original = figure.querySelector("svg");
    if (!original) return;
    var box = original.viewBox && original.viewBox.baseVal;
    if (!box || !box.width) return;
    if (!dialog) build();
    naturalW = box.width;
    naturalH = box.height;
    // The copy keeps the original's id: Mermaid scopes the diagram's styles to it.
    svg = original.cloneNode(true);
    svg.removeAttribute("width");
    svg.removeAttribute("height");
    view.innerHTML = "";
    view.appendChild(svg);
    dialog.showModal();
    // Natural size, where the text reads as body text; Fit shows the whole diagram.
    setZoom(1);
    view.scrollLeft = 0;
    view.scrollTop = 0;
  }

  function mark(figure) {
    if (figure.classList.contains("diagram-zoomable")) return;
    figure.classList.add("diagram-zoomable");
    figure.setAttribute("tabindex", "0");
    figure.setAttribute("role", "button");
    figure.setAttribute("aria-label", "Enlarge diagram");
    var hint = document.createElement("p");
    hint.className = "diagram-zoom-hint";
    hint.textContent = "Click or tap the diagram to enlarge it.";
    figure.appendChild(hint);
  }

  document.querySelectorAll("figure pre.mermaid-js, figure svg.mermaid-js").forEach(function (el) {
    mark(el.closest("figure"));
  });
  document.addEventListener("click", function (e) {
    var figure = e.target.closest("figure.diagram-zoomable");
    if (figure && !e.target.closest("a")) open(figure);
  });
  document.addEventListener("keydown", function (e) {
    var figure = e.target.closest && e.target.closest("figure.diagram-zoomable");
    if (figure && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); open(figure); }
  });
})();
</script>
```

- [ ] **Step 4: Write the root and message templates.** `plan-driven-development/templates/CLAUDE.md`
  is the single line `@AGENTS.md`. `plan-driven-development/templates/issue-tracker.md`:

```markdown
# Issue tracker

Work in this repo is tracked in its plans, not in an issue tracker: `docs/superpowers/plans/`, each
task with checkbox steps, plus the spec's scenario table and its Later list. A task's state is its
box, the plan's **Now** line and its closing commit (`docs(plan): 🤖 close Task N: …`).

Anything with a date or someone waiting on it is proposed to Dan as a ticket in his own tracker,
never filed silently. Dependabot's PRs are the only GitHub PRs besides each phase's own.
```

  `plan-driven-development/templates/close-task.txt`:

```text
docs(plan): 🤖 close Task N: <the task's title>

Drift: <how the build departed from the plan, and why; or "none">
Rulings: <each ruling: what was decided, why, what it costs if wrong; or "none">
Phase-end: <findings deferred to the phase-end list, each with its severity and file; or "none">
Forward: <later tasks or phases the forward review changed, and how; or "none">
Tier: <1, 2 or 3>
Rounds: <the reviews and re-reviews run; "self-review (no subagent tool)" when so>
Findings: <Critical n, Important n, Minor n, and what became of each>

Plan: <plan file> Task N
Co-Authored-By: <the model's own line>
```

  `plan-driven-development/templates/wip.txt`:

```text
chore(plan): 🤖 wip Task N: <where it stopped, in a few words>

Done so far: <what this task has built so far, by commit>
Stopped at: <the step, and what was in progress>
Tests: <the suite's state: green, or which tests fail and why>

Plan: <plan file> Task N
Co-Authored-By: <the model's own line>
```

- [ ] **Step 5: Run the tests; they pass.** `make test` and `make test-utc`. Expected: `169 passed`
  both times (163 + 6; the two render tests need Quarto on `PATH`).

- [ ] **Step 6: Commit.** Write `.git/PDD_MSG`:

```text
plan-driven-development: add the docs and message templates

The Quarto site a public project without a demo gets: Home (the README
and the overview), Architecture (every diagram), Design (the spec and
plans through .md wrappers at mirrored paths), Changelog and How we
work, plus local-ai's diagram zoom. CLAUDE.md is @AGENTS.md. The
issue-tracker note serves Matt Pocock's code-review; close-task.txt and
wip.txt are the message templates the commit-msg hook checks.

Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Task 10
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```bash
git add plan-driven-development/templates/quarto plan-driven-development/templates/CLAUDE.md plan-driven-development/templates/issue-tracker.md plan-driven-development/templates/close-task.txt plan-driven-development/templates/wip.txt plan-driven-development/tests/test_site.py
git commit -F .git/PDD_MSG
git log -1 --format='%(trailers)'
```

- [ ] **Step 7: Review, look forward, close (Tier 2).**
  1. **Mechanical:** `make test` and `make test-utc`.
  2. **Backward review:** `mattpocock-skills:code-review` from `$(cat .git/PDD_BASE)`, the spec
     being this task and the spec's *Docs and the site*; at most one re-review.
  3. **Forward review:** Task 12's `docs-site.md` names these files and their placeholders; the
     kickoff reference copies `close-task.txt` and `wip.txt` to `docs/agents/`.
  4. **Docs:** none yet.
  5. **Close:** **Now** → `Task 11: the every-session rules, open.` Commit
     `plan-driven-development: close Task 10: the docs templates`:

  Write `.git/PDD_MSG`, filling each `<…>`:

```text
plan-driven-development: close Task 10: the docs templates

Drift: <how the build departed from this plan, and why; or "none">
Rulings: <each ruling: what was decided, why, what it costs if wrong; or "none">
Phase-end: <findings deferred to the phase-end list, with severity and file; or "none">
Forward: <later tasks the forward review changed, and how; or "none">
Tier: 2
Rounds: <the reviews and re-reviews run>
Findings: <Critical n, Important n, Minor n, and what became of each>

Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Task 10
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```bash
git add docs/superpowers/plans/2026-10-15-plan-driven-development.md
git commit -F .git/PDD_MSG
git log -1 --format='%(trailers)'
for h in Drift Rulings Phase-end Forward Tier Rounds Findings; do
  git log -1 --format=%B | grep -q "^$h: ." || echo "missing $h"
done
```

  Expected: the trailers print the `Plan:` line; no `missing` line.

- [ ] **Step 8: Push (standing OK).**

  The skill's own leak check scans the range, with Dan's denylist. Push only through this block:

```bash
git fetch -q origin
range=origin/plan-driven-development..HEAD
if uv run --quiet --script plan-driven-development/scripts/leakcheck.py --range "$range" &&
   gitleaks git --log-opts="$range" --redact --no-banner . &&
   git log --format= --numstat "$range" | awk '$1 == "-" { print "binary, check it by eye: " $3; bad = 1 } END { exit bad }'; then
  git push origin plan-driven-development
else
  echo "STOP: not pushed. Tell Dan each finding's kind and file:line (never the matched text), or the binary's name."
fi
```

  Expected: the leak check prints nothing, gitleaks prints `no leaks found`, then the push. A
  `STOP` line means nothing was pushed: a leak or an unscanned binary is a stop that never relaxes;
  tell Dan the kind and `file:line`, never the excerpt.

***

### Task 11: The every-session rules: `templates/AGENTS.md` and `SKILL.md`

**Tier:** 2 · **Scenarios:** every behavioural scenario (S01–S05, S09–S16, S18–S20), proven in
Tasks 13 and 14.

**Files:**
- Create: `plan-driven-development/templates/AGENTS.md`
- Create: `plan-driven-development/SKILL.md`

**Interfaces:**
- Consumes: `tests/red-results.md` (Task 6); every template and script path above; the seven
  placeholders Task 4's recipes fill; the Makefile targets (Task 9).
- Produces: the rules every session reads, and the skill's entry point.

The iron law: this text is written now, after RED, against the failures and rationalizations in
`tests/red-results.md`. The plan gives each file's contract, not its words: every rule it must
state (citing the spec section that holds the exact wording), its length budget, and the scenarios
that check it. Write each rule as a recipe of what the output IS where RED showed wrong-shaped
output, as a required slot where RED showed a missing element, and as a prohibition with its
rationalization only where RED showed a rule skipped under pressure (writing-skills, *Match the
Form to the Failure*).

- [ ] **Step 0: Record the base:** `git rev-parse HEAD > .git/PDD_BASE`.

- [ ] **Step 1: Write `templates/AGENTS.md`, the one copy of every rule that runs each session.**
  Budget: 100–120 lines. It must contain, as self-contained text a harness without the skill can
  follow:
  - a header filled from the placeholders `__PROJECT__`, `__SIZE__`, `__VISIBILITY__`, `__DEMO__`,
    `__MODE__`, `__CHECK_COMMAND__` and a last line `Made from plan-driven-development __SKILL_VERSION__.`
    (kickoff fills `__SKILL_VERSION__` with the short SHA of the skill's own checkout,
    `git -C <the skill's base directory> rev-parse --short HEAD`, or, for a plugin install with no
    git, the name of the plugin's cache folder);
  - **commands:** the project's `Makefile` targets by name (`make help`, `make hooks`,
    `make check`, `make test`, `make test-utc`, `make lint`, `make leaks`, `make docs` on site
    projects), never the raw commands; a command anyone runs more than once becomes a target;
  - **Resume** at every session start, on "where are we?", and after a compaction, a usage-limit
    stop or a restart: `make hooks`'s check first, then the read order and the briefing (spec,
    *Resume*); commits win; the go (S04, S09–S14, S16);
  - **Each task's loop**, the seven steps (spec, *Each task's loop*), the review tiers and the cap
    (*Review tiers*), the security checklist and a short scoped re-review brief for harnesses
    without superpowers or subagents, and a short credited version of Matt's two-axis brief
    (S02, S03, S18, S19);
  - **the fifth stop** and the **stops that never relax** (spec, *Pushing, PRs and modes*), with
    the mode the header names (S03, S12, S13, S20);
  - **commits**: the subjects table, the trailer paragraph, `-F`, staging by path, never
    `--no-verify`, no secret on a command line, merges with `git merge --no-ff -F` (spec,
    *Commits*) (S02, S08);
  - **pushing**: the standing OK, the pre-push hook, one session per branch, text that leaves without
    git scanned first (spec, *Pushing, PRs and modes*);
  - **the overrides table** (including superpowers 7.0.0's writing-plans "a code block only for an
    algorithm they do not determine" → full code in every step, and brainstorming 7.0.0's
    open-question-first style → Dan's asking rules with one opening question at kickoff) and the
    **steering list** (spec, *Overrides and steering*), including "work in place" (S05, S09, S10);
  - **the asking rules**, a short copy (spec, *The asking rules*): list first, one at a time with
    "N of M", A/B/C with a recommendation and a self-review, selectable options where the harness
    has them (Claude Code's AskUserQuestion, recommended option first), text when they need long
    explanation (S01, S03);
  - **docs true**: wrong docs fixed in the task, missing docs to the phase-end list, diagrams never
    wait, and a sync table to extend (spec, *Keeping docs true*) (S02);
  - **security**: the denylist is never read; a leak finding recorded by kind and `file:line` only.
  It must not restate kickoff, planning, phase end or the docs site: those are in the references.

- [ ] **Step 2: Write `SKILL.md`.** Budget: 200–300 lines. Frontmatter `name: plan-driven-development`
  and the spec's description (single-quoted if it contains `: ` or `#`). The six moments, and for
  each: what triggers it and which file to read before acting (the template for each task and
  resume; a reference for the rest), named in the imperative ("before kickoff's questions, read
  `references/kickoff.md`"); that every path is relative to this skill's own base directory (it may
  be installed as a plugin); and a red-flags table built from `tests/red-results.md`, each row the
  model's own rationalization against the rule that answers it. It links to the template and never
  restates its rules.

- [ ] **Step 3: Check the shape:**

```bash
f=plan-driven-development/SKILL.md; uv run -q --with pyyaml python -c "import yaml,re,sys; p=sys.argv[1]; t=open(p).read(); fm=yaml.safe_load(re.match(r'^---\n(.*?)\n---\n',t,re.S).group(1)); assert fm['name']==p.split('/')[0], p+': name != folder'; assert len(fm['description'])<=1024, p+': description too long'; print(fm['name'], len(fm['description']), t.count(chr(10)), 'lines')" "$f"
wc -l plan-driven-development/templates/AGENTS.md
grep -c '^---' plan-driven-development/templates/AGENTS.md
```

  Expected: `plan-driven-development <≤1024> <200–300> lines`; the template within 100–120 lines;
  the `grep -c` count is `0` (horizontal rules are `***`).

- [ ] **Step 4: Commit.** Write `.git/PDD_MSG`, filling the `<…>` from `tests/red-results.md`:

```text
plan-driven-development: write the every-session rules and SKILL.md from the RED results

templates/AGENTS.md is the one copy of every rule that runs each
session, in any harness, with or without the skill; SKILL.md names the
six moments and which file to read at each. The RED failures each
answers: <scenario: the rule that answers it>, one per line.

Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Task 11
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```bash
git add plan-driven-development/templates/AGENTS.md plan-driven-development/SKILL.md
git commit -F .git/PDD_MSG
git log -1 --format='%(trailers)'
```

- [ ] **Step 5: Review, look forward, close (Tier 2).**
  1. **Mechanical:** Step 3's checks; `make test` still passes.
  2. **Backward review:** `mattpocock-skills:code-review` from `$(cat .git/PDD_BASE)`, the spec
     being this task's contracts and the spec sections they cite; the Spec axis checks every rule
     listed above is stated, and nothing contradicts the spec.
  3. **Forward review:** Task 12's references link to the template and never restate it; Task 13
     runs GREEN against these files.
  4. **Docs:** none yet.
  5. **Close:** **Now** → `Task 12: the four references, open.` Commit
     `plan-driven-development: close Task 11: the every-session rules and SKILL.md`:

  Write `.git/PDD_MSG`, filling each `<…>`:

```text
plan-driven-development: close Task 11: the every-session rules and SKILL.md

Drift: <how the build departed from this plan, and why; or "none">
Rulings: <each ruling: what was decided, why, what it costs if wrong; or "none">
Phase-end: <findings deferred to the phase-end list, with severity and file; or "none">
Forward: <later tasks the forward review changed, and how; or "none">
Tier: 2
Rounds: <the reviews and re-reviews run>
Findings: <Critical n, Important n, Minor n, and what became of each>

Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Task 11
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```bash
git add docs/superpowers/plans/2026-10-15-plan-driven-development.md
git commit -F .git/PDD_MSG
git log -1 --format='%(trailers)'
for h in Drift Rulings Phase-end Forward Tier Rounds Findings; do
  git log -1 --format=%B | grep -q "^$h: ." || echo "missing $h"
done
```

  Expected: the trailers print the `Plan:` line; no `missing` line.

- [ ] **Step 6: Push (standing OK).**

  The skill's own leak check scans the range, with Dan's denylist. Push only through this block:

```bash
git fetch -q origin
range=origin/plan-driven-development..HEAD
if uv run --quiet --script plan-driven-development/scripts/leakcheck.py --range "$range" &&
   gitleaks git --log-opts="$range" --redact --no-banner . &&
   git log --format= --numstat "$range" | awk '$1 == "-" { print "binary, check it by eye: " $3; bad = 1 } END { exit bad }'; then
  git push origin plan-driven-development
else
  echo "STOP: not pushed. Tell Dan each finding's kind and file:line (never the matched text), or the binary's name."
fi
```

  Expected: the leak check prints nothing, gitleaks prints `no leaks found`, then the push. A
  `STOP` line means nothing was pushed: a leak or an unscanned binary is a stop that never relaxes;
  tell Dan the kind and `file:line`, never the excerpt.

***

### Task 12: The four references: kickoff, plans, phase end and the docs site

**Tier:** 2 · **Scenarios:** S01 (kickoff), S14 (phase end), and the docs and plan shapes S02 checks;
proven in Task 13.

**Files:**
- Create: `plan-driven-development/references/kickoff.md`, `plans.md`, `phase-end.md`, `docs-site.md`

**Interfaces:**
- Consumes: `tests/red-results.md` (Task 6); `templates/AGENTS.md` and `SKILL.md` (Task 11); every
  template and script path above.
- Produces: what each rare moment needs, linked from `SKILL.md`.

The same iron law and the same forms as Task 11: contracts, not words.

- [ ] **Step 0: Record the base:** `git rev-parse HEAD > .git/PDD_BASE`.

- [ ] **Step 1: Write `references/kickoff.md`.** Budget: 150–220 lines. The setup questions (with
  one opening "describe it in your own words" question allowed before them, Dan's decision A on
  brainstorming 7.0.0), safety before the first commit (the drill stages its files by path, commits
  with `-F`, expects exit 1 with the finding named, then unstages with `git rm --cached` and deletes
  them; an accepted drill commit is a stop), the asking rules in full, grilling by those rules, the
  design in sections, the spec with its one-line `AGENTS.md` pointer, the root files (`AGENTS.md`
  from the template with its placeholders filled, `__SKILL_VERSION__` as Task 11 defines it,
  `CLAUDE.md`, `README.md`, `docs/agents/issue-tracker.md`, `docs/agents/close-task.txt` and
  `docs/agents/wip.txt`, the hooks and scripts copied in and `chmod 755` on the hooks, the `Makefile`
  with `__PROJECT__`, `__TEST_COMMAND__` and `__LINT_COMMAND__` filled and `make hooks` run, `ci.yml`
  with `__TEST_COMMAND__` filled, and `site`, `pages` and the Makefile's `docs` deleted for a project
  read on GitHub), the root commit on `main` and its first push as a [Dan] step, `phase-1` after
  that, moving an existing `CLAUDE.md` into `AGENTS.md`, the GitHub description and website (text
  scanned), the builder check (brainstorming 7.0.0's `builder-check-prompt.md`) as a small project's
  one pre-approval reviewer of the spec and the council for a large one, approval, the GitHub
  settings checklist (flagged), the docs site and CI as the plan's first tasks (spec, *Kickoff*)
  (S01).

- [ ] **Step 2: Write `references/plans.md`.** Budget: 100–150 lines. The spec's additions (status
  lines, outline, the scenario table with Later and dropped rows, Revisions, open items, diagrams
  by link), the plan's additions (Now after `**Spec:**`, Tier and Scenarios, a base recorded per
  task, every commit written out, the Phase end task named `### Task N: Phase end`, Built
  differently, Ruling lines, the phase-end list), full code in every step (the override of
  writing-plans 7.0.0), `***` rules, running a phase's listings, a small project that grows (spec,
  *Planning*).

- [ ] **Step 3: Write `references/phase-end.md`.** Budget: 100–150 lines. The phase-end steps, the
  small project's subset, the councils (four read-only reviewers; reports committed first; claims
  checked), the retro and its retuning rules, the PR (title, body ending with `Plan: … Phase end`,
  `--match-head-commit`, never `--admin` or `--delete-branch`), and the phase start (spec,
  *Phase end*, *Phase start*) (S14).

- [ ] **Step 4: Write `references/docs-site.md`.** Budget: 80–130 lines. The three cases, the Quarto
  site from `templates/quarto/` with its placeholders, wrappers, the pages, links leaving the site,
  the checks (`make docs` locally, CI's site job), the deploy, the site task's closing rule, the
  posit-dev Quarto skills (spec, *Docs and the site*).

- [ ] **Step 5: Check the shape:**

```bash
wc -l plan-driven-development/references/*.md
grep -c '^---' plan-driven-development/references/*.md
grep -o 'references/[a-z-]*\.md' plan-driven-development/SKILL.md | sort -u
```

  Expected: each file within its budget; every `grep -c` count `0`; `SKILL.md` links all four.

- [ ] **Step 6: Commit.** Write `.git/PDD_MSG`, filling the `<…>` from `tests/red-results.md`:

```text
plan-driven-development: write the four references from the RED results

kickoff.md, plans.md, phase-end.md and docs-site.md hold what the rare
moments need; each links to templates/AGENTS.md for the every-session
rules instead of restating them. The RED failures each answers:
<scenario: the rule that answers it>, one per line.

Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Task 12
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```bash
git add plan-driven-development/references/kickoff.md plan-driven-development/references/plans.md plan-driven-development/references/phase-end.md plan-driven-development/references/docs-site.md
git commit -F .git/PDD_MSG
git log -1 --format='%(trailers)'
```

- [ ] **Step 7: Review, look forward, close (Tier 2).**
  1. **Mechanical:** Step 5's checks; `make test` still passes.
  2. **Backward review:** `mattpocock-skills:code-review` from `$(cat .git/PDD_BASE)`, the spec
     being this task's contracts and the spec sections they cite; nothing restates the template;
     nothing contradicts the spec.
  3. **Forward review:** Task 13 runs GREEN against these files and Task 11's.
  4. **Docs:** none yet.
  5. **Close:** **Now** → `Task 13: GREEN and REFACTOR, open.` Commit
     `plan-driven-development: close Task 12: the four references`:

  Write `.git/PDD_MSG`, filling each `<…>`:

```text
plan-driven-development: close Task 12: the four references

Drift: <how the build departed from this plan, and why; or "none">
Rulings: <each ruling: what was decided, why, what it costs if wrong; or "none">
Phase-end: <findings deferred to the phase-end list, with severity and file; or "none">
Forward: <later tasks the forward review changed, and how; or "none">
Tier: 2
Rounds: <the reviews and re-reviews run>
Findings: <Critical n, Important n, Minor n, and what became of each>

Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Task 12
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```bash
git add docs/superpowers/plans/2026-10-15-plan-driven-development.md
git commit -F .git/PDD_MSG
git log -1 --format='%(trailers)'
for h in Drift Rulings Phase-end Forward Tier Rounds Findings; do
  git log -1 --format=%B | grep -q "^$h: ." || echo "missing $h"
done
```

  Expected: the trailers print the `Plan:` line; no `missing` line.

- [ ] **Step 8: Push (standing OK).**

  The skill's own leak check scans the range, with Dan's denylist. Push only through this block:

```bash
git fetch -q origin
range=origin/plan-driven-development..HEAD
if uv run --quiet --script plan-driven-development/scripts/leakcheck.py --range "$range" &&
   gitleaks git --log-opts="$range" --redact --no-banner . &&
   git log --format= --numstat "$range" | awk '$1 == "-" { print "binary, check it by eye: " $3; bad = 1 } END { exit bad }'; then
  git push origin plan-driven-development
else
  echo "STOP: not pushed. Tell Dan each finding's kind and file:line (never the matched text), or the binary's name."
fi
```

  Expected: the leak check prints nothing, gitleaks prints `no leaks found`, then the push. A
  `STOP` line means nothing was pushed: a leak or an unscanned binary is a stop that never relaxes;
  tell Dan the kind and `file:line`, never the excerpt.

***

### Task 13: GREEN and REFACTOR in Claude Code

**Tier:** 2 · **Scenarios:** S01–S14 and S17–S20 (S06–S08 and S17 through the pytest suite).

**Files:**
- Create: `plan-driven-development/tests/green-results.md`
- Modify (REFACTOR only): `SKILL.md`, `templates/AGENTS.md`, the references

**Interfaces:**
- Consumes: the skill (Tasks 11–12), the harness (Tasks 4–5).
- Produces: a skill every scenario passes with.

- [ ] **Step 0: Record the base:** `git rev-parse HEAD > .git/PDD_BASE`.

- [ ] **Step 1: The deterministic scenarios:** `make test` and `make test-utc`. Expected: `169 passed`
  both times (S06–S08, S17).

- [ ] **Step 2: Run every behavioural scenario with the skill** (the same model as RED; the runner
  fails a GREEN run whose start-up event doesn't list `plan-driven-development`):

```bash
for s in s01 s02 s03 s04 s05 s09 s10 s11 s12 s13 s14 s18 s19 s20; do
  uv run --quiet --script plan-driven-development/tests/harness/run.py "$s" --stage green | tee -a .git/PDD_GREEN.txt
done
```

  Expected: every check PASS. A failed check is re-run once before it counts (a single run is not
  proof). A `HARNESS FAIL` is fixed in `run.py`, not in the skill.

- [ ] **Step 3: REFACTOR each failure that repeats.** Read that session's final answer for the
  rationalization; add its row to `SKILL.md`'s red-flags table, or tighten the rule in the file
  that states it (the template for every-session rules); re-run that scenario until it passes; then
  re-run every scenario whose rule lives in the same file. Each change is its own commit; write
  `.git/PDD_MSG` per change:

```text
plan-driven-development: <what the rule now says>

The rationalization it closes, quoted from <scenario>'s GREEN run:
"<the model's words>". <Which file, and what changed in it.>

Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Task 13
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```bash
git add <the one file changed>
git commit -F .git/PDD_MSG
git log -1 --format='%(trailers)'
```

- [ ] **Step 4: If S05 keeps loading Matt's `tdd` or `diagnosing-bugs` after a REFACTOR [Dan's
  yes]:** the spec's fallback (Question 13, B). Propose to Dan deny rules
  `"Skill(mattpocock-skills:tdd)"` and `"Skill(mattpocock-skills:diagnosing-bugs)"` for
  `~/.claude/settings.json` (shown as a diff with the `update-config` skill), noting they also stop
  Dan typing those two skills; on his yes, apply them, confirm them in `/permissions`, add the same
  two rules to `run.py`'s `DISALLOWED` (a commit as in Step 3), and re-run S05.

- [ ] **Step 5: Record** in `plan-driven-development/tests/green-results.md`: the plugin versions,
  and per scenario the run that passed (date, model), and each REFACTOR with its commit. Then
  `grep -nE '/(Users|home|private|var/folders)/' plan-driven-development/tests/green-results.md`
  prints nothing.

- [ ] **Step 6: Commit.** Write `.git/PDD_MSG`:

```text
plan-driven-development: record the GREEN results

With the skill, on <model>, with superpowers <version> and Matt
Pocock's skills <version>: every scenario passes; <n> REFACTOR commits
closed <n> rationalizations, listed in tests/green-results.md.

Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Task 13
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```bash
git add plan-driven-development/tests/green-results.md
git commit -F .git/PDD_MSG
git log -1 --format='%(trailers)'
```

- [ ] **Step 7: Review, look forward, close (Tier 2).**
  1. **Mechanical:** `make test`; Task 11's and Task 12's shape checks still pass after REFACTOR.
  2. **Backward review:** `mattpocock-skills:code-review` over the REFACTOR commits (from
     `$(cat .git/PDD_BASE)`), the spec being the spec sections whose rules changed: no REFACTOR may
     contradict the spec; a needed change to the spec is the fifth stop.
  3. **Forward review:** Task 14 runs S02 and S04 with only `AGENTS.md`; any rule REFACTOR moved
     into `SKILL.md` that a harness without the skill needs must be in the template instead.
  4. **Docs:** none yet.
  5. **Close:** **Now** → `Task 14: portability, open.` Commit
     `plan-driven-development: close Task 13: GREEN and REFACTOR`:

  Write `.git/PDD_MSG`, filling each `<…>`:

```text
plan-driven-development: close Task 13: GREEN and REFACTOR

Drift: <how the build departed from this plan, and why; or "none">
Rulings: <each ruling: what was decided, why, what it costs if wrong; or "none">
Phase-end: <findings deferred to the phase-end list, with severity and file; or "none">
Forward: <later tasks the forward review changed, and how; or "none">
Tier: 2
Rounds: <the reviews and re-reviews run>
Findings: <Critical n, Important n, Minor n, and what became of each>

Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Task 13
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```bash
git add docs/superpowers/plans/2026-10-15-plan-driven-development.md
git commit -F .git/PDD_MSG
git log -1 --format='%(trailers)'
for h in Drift Rulings Phase-end Forward Tier Rounds Findings; do
  git log -1 --format=%B | grep -q "^$h: ." || echo "missing $h"
done
```

  Expected: the trailers print the `Plan:` line; no `missing` line.

- [ ] **Step 8: Push (standing OK).**

  The skill's own leak check scans the range, with Dan's denylist. Push only through this block:

```bash
git fetch -q origin
range=origin/plan-driven-development..HEAD
if uv run --quiet --script plan-driven-development/scripts/leakcheck.py --range "$range" &&
   gitleaks git --log-opts="$range" --redact --no-banner . &&
   git log --format= --numstat "$range" | awk '$1 == "-" { print "binary, check it by eye: " $3; bad = 1 } END { exit bad }'; then
  git push origin plan-driven-development
else
  echo "STOP: not pushed. Tell Dan each finding's kind and file:line (never the matched text), or the binary's name."
fi
```

  Expected: the leak check prints nothing, gitleaks prints `no leaks found`, then the push. A
  `STOP` line means nothing was pushed: a leak or an unscanned binary is a stop that never relaxes;
  tell Dan the kind and `file:line`, never the excerpt.

***

### Task 14: Portability in OpenCode and pi

**Tier:** 3 · **Scenarios:** S15, S16.

**Files:**
- Modify: `plan-driven-development/tests/green-results.md` (a portability section)

**Interfaces:**
- Consumes: `portability.py` (Task 5), the template (Task 11).
- Produces: evidence that "How we work" carries the workflow without the skill.

- [ ] **Step 0: Record the base:** `git rev-parse HEAD > .git/PDD_BASE`.

- [ ] **Step 1: [Dan] Name the model and check the Spark's model is up** (or a cloud model he picks
  for OpenCode). If it is down: set **Now** to `waiting on Dan: the Spark's model for S15/S16`,
  commit that (Step 5's close, with `Phase-end: S15/S16 waiting on the Spark`), and go on to Task 15.
  Come back here when it is up. If it is still down at the phase end, the PR says S15 and S16 are
  waiting (their spec status stays `built`), and Dan decides whether to merge before they run.

- [ ] **Step 2: S15, S02 in OpenCode:**
  `uv run --quiet --script plan-driven-development/tests/harness/portability.py s02 --harness opencode --model <model>`.
  The first run also checks the fixture's `opencode.jsonc` took effect (the run's stderr shows no
  permission prompts hanging; a denied command shows as denied). Expected: every check PASS or SKIP.

- [ ] **Step 3: S16, S04 in OpenCode, then in pi [Dan's OK for pi, which has no per-command
  allow-list]:** the same command with `s04`, then `--harness pi`. Expected: PASS or SKIP.

- [ ] **Step 4: Record** the runs in `green-results.md`'s portability section, noting each
  harness also read Dan's own global instructions; a failure goes back to the template
  (REFACTOR, as in Task 13 Step 3) and both harnesses re-run. Then
  `grep -nE '/(Users|home|private|var/folders)/' plan-driven-development/tests/green-results.md`
  prints nothing. Commit, writing `.git/PDD_MSG`:

```text
plan-driven-development: record the portability runs

S15 (S02 in OpenCode) and S16 (S04 in OpenCode and pi), on <model>,
with only the project's AGENTS.md and no skill: <results>.

Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Task 14
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```bash
git add plan-driven-development/tests/green-results.md
git commit -F .git/PDD_MSG
git log -1 --format='%(trailers)'
```

- [ ] **Step 5: Close (Tier 3).** A self-review: each run passed or skipped, or the gap is recorded.
  **Now** → `Task 15: release, open.` Commit
  `plan-driven-development: close Task 14: portability in OpenCode and pi`:

  Write `.git/PDD_MSG`, filling each `<…>`:

```text
plan-driven-development: close Task 14: portability in OpenCode and pi

Drift: <how the build departed from this plan, and why; or "none">
Rulings: <each ruling: what was decided, why, what it costs if wrong; or "none">
Phase-end: <findings deferred to the phase-end list, with severity and file; or "none">
Forward: <later tasks the forward review changed, and how; or "none">
Tier: 3
Rounds: <the reviews and re-reviews run>
Findings: <Critical n, Important n, Minor n, and what became of each>

Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Task 14
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```bash
git add docs/superpowers/plans/2026-10-15-plan-driven-development.md
git commit -F .git/PDD_MSG
git log -1 --format='%(trailers)'
for h in Drift Rulings Phase-end Forward Tier Rounds Findings; do
  git log -1 --format=%B | grep -q "^$h: ." || echo "missing $h"
done
```

  Expected: the trailers print the `Plan:` line; no `missing` line.

- [ ] **Step 6: Push (standing OK).**

  The skill's own leak check scans the range, with Dan's denylist. Push only through this block:

```bash
git fetch -q origin
range=origin/plan-driven-development..HEAD
if uv run --quiet --script plan-driven-development/scripts/leakcheck.py --range "$range" &&
   gitleaks git --log-opts="$range" --redact --no-banner . &&
   git log --format= --numstat "$range" | awk '$1 == "-" { print "binary, check it by eye: " $3; bad = 1 } END { exit bad }'; then
  git push origin plan-driven-development
else
  echo "STOP: not pushed. Tell Dan each finding's kind and file:line (never the matched text), or the binary's name."
fi
```

  Expected: the leak check prints nothing, gitleaks prints `no leaks found`, then the push. A
  `STOP` line means nothing was pushed: a leak or an unscanned binary is a stop that never relaxes;
  tell Dan the kind and `file:line`, never the excerpt.

***

### Task 15: Release: the marketplace, the README, this repo's `CLAUDE.md`, `install.sh`

**Tier:** 3 · **Scenarios:** none new; the release makes the skill installable.

**Files:**
- Modify: `.claude-plugin/marketplace.json` (the `coding` plugin)
- Modify: `README.md` (a row in the skills table; `preferences.md` and the `Makefile`)
- Modify: `CLAUDE.md` ("How the skills fit together", the Tests section and the `Makefile`; Dan's
  yes on the diff)

**Interfaces:**
- Consumes: the finished skill; this repo's `Makefile` (Task 3).
- Produces: the skill listed, documented and linked.

- [ ] **Step 0: Record the base:** `git rev-parse HEAD > .git/PDD_BASE`.

- [ ] **Step 1: The marketplace.** In `.claude-plugin/marketplace.json`, the `coding` plugin's
  `skills` becomes `["./external-app-review", "./plan-driven-development"]` and its `description`
  becomes `"Coding-agent workflows: plan, build and commit a project in phases so the repo and its
  history always hold the full story; and an honest outside review of an application another model
  or agent built, after you have fixed it"`. Check it parses:
  `python3 -c "import json; json.load(open('.claude-plugin/marketplace.json'))"`.

- [ ] **Step 2: The README.** A row after `external-app-review`'s:

```markdown
| [plan-driven-development](plan-driven-development/) | Coding | Plans a new project with you one question at a time, then builds it task by task with small commits, a backward and a forward review at every step, and docs kept true, so the repo and its history always say where things stand. |
```

  And, under the table: `` `preferences.md`, at this repo's root, holds Dan's standing rules for
  every coding agent (#9 tracks moving it). `make help` lists this repo's commands: the skill's
  tests, the frontmatter check and the install. ``

- [ ] **Step 3: This repo's `CLAUDE.md` [Dan's yes on the diff].** Under "How the skills fit
  together", **Standalone** gains: `` `plan-driven-development` writes into each new project (its
  templates and scripts are copied at kickoff) and is read every session through that project's
  `AGENTS.md`; `preferences.md` (this repo's root) is wired into each harness's global instructions,
  and moving it means updating those wirings (TODO.md, #9). `` Under **Tests**, replace "Other skills
  have no tests." with: `` `plan-driven-development` has pytest for its scripts, hooks and templates
  (`make test`, and `make test-utc`) and a harness of headless sessions graded per scenario
  (`tests/harness/`; RED and GREEN results in `tests/`). Other skills have no tests. `` Under
  **Editing a skill**, the frontmatter check gains: `` (`make check-skills` runs it.) ``

- [ ] **Step 4: Validate every skill and link it:**

```bash
make check-skills
CLAUDE_SKILLS_DIR="$(mktemp -d)" make install | grep plan-driven-development
```

  Expected: every skill prints its line, `plan-driven-development` included; the scratch install
  prints `linked   plan-driven-development`. The real `make install` runs at the phase end, after
  the merge.

- [ ] **Step 5: Commit.** Write `.git/PDD_MSG`:

```text
plan-driven-development: list it in the marketplace, the README and CLAUDE.md

The coding plugin gains the skill; the README gains its row, a line on
preferences.md and one on make help; CLAUDE.md says how the skill and
preferences.md fit with the rest, how its tests run, and that make
check-skills runs the frontmatter check.

Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Task 15
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```bash
git add .claude-plugin/marketplace.json README.md CLAUDE.md
git commit -F .git/PDD_MSG
git log -1 --format='%(trailers)'
```

- [ ] **Step 6: Review, look forward, close (Tier 3).**
  1. **Mechanical:** Step 4; `make test`.
  2. **Backward review:** a self-review under Matt's two headings (Standards; Spec), the spec being
     this task and the spec's *Work outline* step 7.
  3. **Forward review:** the phase end merges this branch; nothing later consumes these files.
  4. **Docs:** grep the repo for `preferences.md`, `make ` and `plan-driven-development`: every
     mention is true.
  5. **Close:** **Now** → `Task 16: phase end, open.` Commit
     `plan-driven-development: close Task 15: release`:

  Write `.git/PDD_MSG`, filling each `<…>`:

```text
plan-driven-development: close Task 15: release

Drift: <how the build departed from this plan, and why; or "none">
Rulings: <each ruling: what was decided, why, what it costs if wrong; or "none">
Phase-end: <findings deferred to the phase-end list, with severity and file; or "none">
Forward: <later tasks the forward review changed, and how; or "none">
Tier: 3
Rounds: <the reviews and re-reviews run>
Findings: <Critical n, Important n, Minor n, and what became of each>

Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Task 15
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```bash
git add docs/superpowers/plans/2026-10-15-plan-driven-development.md
git commit -F .git/PDD_MSG
git log -1 --format='%(trailers)'
for h in Drift Rulings Phase-end Forward Tier Rounds Findings; do
  git log -1 --format=%B | grep -q "^$h: ." || echo "missing $h"
done
```

  Expected: the trailers print the `Plan:` line; no `missing` line.

- [ ] **Step 7: Push (standing OK).**

  The skill's own leak check scans the range, with Dan's denylist. Push only through this block:

```bash
git fetch -q origin
range=origin/plan-driven-development..HEAD
if uv run --quiet --script plan-driven-development/scripts/leakcheck.py --range "$range" &&
   gitleaks git --log-opts="$range" --redact --no-banner . &&
   git log --format= --numstat "$range" | awk '$1 == "-" { print "binary, check it by eye: " $3; bad = 1 } END { exit bad }'; then
  git push origin plan-driven-development
else
  echo "STOP: not pushed. Tell Dan each finding's kind and file:line (never the matched text), or the binary's name."
fi
```

  Expected: the leak check prints nothing, gitleaks prints `no leaks found`, then the push. A
  `STOP` line means nothing was pushed: a leak or an unscanned binary is a stop that never relaxes;
  tell Dan the kind and `file:line`, never the excerpt.

***

### Task 16: Phase end (a small project)

**Tier:** — · **Scenarios:** all, re-checked.

**Files:**
- Modify: this plan, the spec (status line and scenario statuses), `README.md` or `CLAUDE.md` if
  the docs check finds them untrue

**Interfaces:**
- Consumes: the finished branch.
- Produces: an open PR against `main`, and after Dan merges it, the skill installed.

- [ ] **Step 0: Record the base:** `git rev-parse HEAD > .git/PDD_BASE`.

- [ ] **1. The final whole-branch review:** `mattpocock-skills:code-review` from
  `git merge-base main HEAD`, the spec being the spec; then one fix dispatch, one scoped re-review
  (superpowers' `re-review-prompt.md`), and a Ruling on whatever is left. Each fix is its own
  commit at the tier of what it touches; write `.git/PDD_MSG` per fix:

```text
plan-driven-development: <what the fix changes>

The final review's finding (<axis>, <severity>, <file:line>), and how
this fixes it.

Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Phase end
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```bash
git add <the files the fix changed>
git commit -F .git/PDD_MSG
git log -1 --format='%(trailers)'
```

  Then push the fixes:

  The skill's own leak check scans the range, with Dan's denylist. Push only through this block:

```bash
git fetch -q origin
range=origin/plan-driven-development..HEAD
if uv run --quiet --script plan-driven-development/scripts/leakcheck.py --range "$range" &&
   gitleaks git --log-opts="$range" --redact --no-banner . &&
   git log --format= --numstat "$range" | awk '$1 == "-" { print "binary, check it by eye: " $3; bad = 1 } END { exit bad }'; then
  git push origin plan-driven-development
else
  echo "STOP: not pushed. Tell Dan each finding's kind and file:line (never the matched text), or the binary's name."
fi
```

  Expected: the leak check prints nothing, gitleaks prints `no leaks found`, then the push. A
  `STOP` line means nothing was pushed: a leak or an unscanned binary is a stop that never relaxes;
  tell Dan the kind and `file:line`, never the excerpt.

- [ ] **2. The ledger copied:** anything left in `.superpowers/sdd/2026-10-15-plan-driven-development/progress.md`
  that no closing commit carries goes into this plan, under the task it belongs to, before
  superpowers deletes the workspace.

- [ ] **3. The docs check:** every doc this branch touched is true (`README.md`, `CLAUDE.md`,
  `TODO.md`, this plan's Now); the spec's status line set to `PR open (#N)`, filled in after Step 5;
  the spec's scenario table's statuses set to `verified` for every scenario that passed GREEN,
  `built` for any whose run waits (S15/S16 if the Spark was down). This repo has no `CHANGELOG.md`:
  record the Ruling that the merge commit's body and the spec's Revisions are the dated record
  instead. Commit, writing `.git/PDD_MSG`:

```text
plan-driven-development: the phase end's docs check

The spec's scenario statuses (verified, or built where a run waits),
<any doc corrected, and how>. Ruling: this repo has no CHANGELOG.md, so
the merge commit's body and the spec's Revisions are the dated record.

Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Phase end
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```bash
git add docs/superpowers/specs/2026-10-15-plan-driven-development-design.md docs/superpowers/plans/2026-10-15-plan-driven-development.md
git commit -F .git/PDD_MSG
git log -1 --format='%(trailers)'
```

  Then push it:

  The skill's own leak check scans the range, with Dan's denylist. Push only through this block:

```bash
git fetch -q origin
range=origin/plan-driven-development..HEAD
if uv run --quiet --script plan-driven-development/scripts/leakcheck.py --range "$range" &&
   gitleaks git --log-opts="$range" --redact --no-banner . &&
   git log --format= --numstat "$range" | awk '$1 == "-" { print "binary, check it by eye: " $3; bad = 1 } END { exit bad }'; then
  git push origin plan-driven-development
else
  echo "STOP: not pushed. Tell Dan each finding's kind and file:line (never the matched text), or the binary's name."
fi
```

  Expected: the leak check prints nothing, gitleaks prints `no leaks found`, then the push. A
  `STOP` line means nothing was pushed: a leak or an unscanned binary is a stop that never relaxes;
  tell Dan the kind and `file:line`, never the excerpt.

- [ ] **4. The PR [Dan merges].** Write the title, one line, to `.git/PDD_PR_TITLE`:
  `plan-driven-development: a new skill for planning and building projects in phases`. Write the
  body to `.git/PDD_PR.md`: the spec, the plan, what each task built, the RED and GREEN results,
  anything waiting (the portability runs, if so), and as its last line
  `Plan: docs/superpowers/plans/2026-10-15-plan-driven-development.md Phase end`. Scan both, then
  open it only if both scans pass:

```bash
if uv run --quiet --script plan-driven-development/scripts/leakcheck.py --message .git/PDD_PR_TITLE &&
   uv run --quiet --script plan-driven-development/scripts/leakcheck.py --message .git/PDD_PR.md &&
   cat .git/PDD_PR_TITLE .git/PDD_PR.md | gitleaks stdin --redact --no-banner; then
  gh pr create -R chendaniely/skills --base main --head plan-driven-development \
    --title "$(cat .git/PDD_PR_TITLE)" --body-file .git/PDD_PR.md
else
  echo "STOP: the PR text has a finding; tell Dan its kind and where, never the matched text"
fi
```

  Expected: a PR URL. Dan merges it with a merge commit (never squash or rebase: they change the
  commit IDs this plan cites).

- [ ] **5. After the merge [Dan's yes]:** on `main`, `make install` (expected:
  `linked   plan-driven-development`), and `ls -l ~/.claude/skills/plan-driven-development` shows a
  link into this repo; a new session's skill list shows the skill. Then the spec's status line:
  `merged <commit> <date>`, in its own commit on `main`, written as in Step 3 with the subject
  `plan-driven-development: the spec's status after the merge`, and pushed only with Dan's OK.

# plan-driven-development: design spec

**Status:** spec approved by Dan, 2026-10-15 · plan in review (its independent review applied;
Dan's approval pending) · branch `plan-driven-development`, pushed on its branch, not merged.

This is the binding document for the `plan-driven-development` skill. Every decision in it was
made with Dan, one question at a time; the questions, the options turned down and his answers in
his own words are in the Q&A record,
[`2026-10-15-plan-driven-development-qa.md`](2026-10-15-plan-driven-development-qa.md). Where the
record's earlier sections and this spec differ, this spec reflects the later answer (the council's
fixes and Dan's eleven decisions); where this spec is silent, the record decides, and the gap is
added here with a Revisions line.

## Goal

Dan starts many projects with coding agents. He wants every one of them planned and built the same
way, so that the repository and its git history always hold the full story: what was planned, what
was built, how the build departed from the plan and why, and what comes next. Either an agent or
Dan himself, returning after a dropped connection, a context compaction, a usage limit or months
away, must be able to pick up from the repo alone.

In his words (the full request is in the Q&A record): backward and forward reviews at each step;
small Conventional Commits with 🤖 at the start of the description; full context "in both the
repository and [the git] history"; superpowers at kickoff and the grilling skill "to make sure that
both of us are in full understanding"; and "a bunch of potential scenarios" for each decision,
planned into phases, "and some things can be moved around and pu[shed] towards the end or as
optional additional fixes". [chendaniely/local-ai](https://github.com/chendaniely/local-ai) is the
worked example of the way he works.

**Done means:** the skill, its `AGENTS.md` template and its tools pass every scenario in the table
below (RED without the skill, GREEN with it), in Claude Code, and the portability scenarios in
OpenCode and pi.

## Constraints

- **The skills repo is public.** Examples, templates, fixtures and commit messages use invented or
  generic values: no real hostnames, addresses, serials, tokens or new personal paths. Look-alike
  values in tests are built from joined strings at run time, so the files never trip a scanner.
- **The skills repo's own rules** (its `CLAUDE.md`): `name` equals the folder; `description` at most
  1024 characters, one short clause on what the skill is, then its triggers, never its workflow
  (writing-skills); `SKILL.md` under 500 lines; references one level deep and linked from
  `SKILL.md`; a skill that writes files triggers only on an explicit request; no skill edits a
  `CLAUDE.md` or its own `SKILL.md` without Dan's yes; commits styled `plan-driven-development: …`.
- **Python runs through uv only**: PEP 723 scripts with `uv run --script`; no pip.
- **Secrets are used by reference and never read.** No agent reads, prints or writes a secret, and
  no agent ever reads the leak-check denylist; a check on it proves only that it exists and parses.
- **Any model, any harness.** The rules must work for Claude Code with Opus, OpenCode with a local
  model on the DGX Spark, pi, and a harness without this skill installed. Only text a harness
  actually loads (`AGENTS.md`, the plan, the dispatch prompt) can be relied on.
- **writing-skills' iron law:** no skill text before a failing baseline test.

## How the skill is used: six moments

| Moment | When | What happens (detail below) |
|---|---|---|
| Kickoff | Dan asks to start, plan or adopt | setup questions, safety first, grilling, spec, root files, plans, council |
| Planning | inside kickoff | writing-plans for every phase, in full, before approval |
| Each task | throughout a phase | build, checks, backward review, forward review, docs, close, CI |
| Phase end | the phase's last task closes | final review, council, phase-end list, retro, PR |
| Phase start | after the phase's PR merges (Phase 2 on) | fresh branch, run the listings, council, fixes, Task 1 |
| Resume | session start, "where are we?", after a compaction, a usage-limit stop or a restart | read the repo, brief Dan, wait for a go |

A small project (one sitting, one plan, nothing touching secrets, the network or hardware) has no
phases: kickoff, planning, each task, a shortened end, resume.

## Files

```
plan-driven-development/
  SKILL.md                     what happens at each moment; links, never restates, the template
  references/
    kickoff.md                 the setup questions, safety, grilling, the asking rules
    plans.md                   the spec and plan layouts, scenarios, Later, Revisions
    phase-end.md               phase end and phase start, councils, retro, metrics, the PR
    docs-site.md               the three docs cases, the Quarto site, wrappers, checks
  templates/
    AGENTS.md                  "How we work": the one copy of every rule that runs each session
    CLAUDE.md                  one line: @AGENTS.md
    close-task.txt             the closing commit's message, with required headings; copied to
                               the project's docs/agents/close-task.txt
    wip.txt                    the wip commit's message; copied to docs/agents/wip.txt
    githooks/                  pre-commit, commit-msg, pre-push, pre-merge-commit, gitleaks.toml
    gitignore                  local-ai's hardening block
    dependabot.yml             Actions and uv updates
    ci.yml                     tests, leaks, shellcheck, site, and the Pages deploy job
    Makefile                   the project's front door: help, hooks, check, test, test-utc,
                               lint, leaks, docs (Dan's preference; GNU make 3.81 features)
    quarto/                    _quarto.yml, index.qmd, architecture.qmd, _overview.qmd,
                               a wrapper page, _diagram-zoom.html
    issue-tracker.md           docs/agents/issue-tracker.md: "work is tracked in the plans"
  scripts/
    leakcheck.py               the leak check, a standard-library PEP 723 script
    commitmsg.py               the commit-message format checks the commit-msg hook runs
  tests/                       baseline and GREEN prompts, fixture recipes, graders, and the
                               ported leakcheck, hooks and workflow tests
```

- **`SKILL.md`** is aimed at 200–300 lines: the six moments, which reference to read at each one
  ("before kickoff's questions, read `references/kickoff.md`"), and a red-flags table filled from
  what the baseline tests show. It points at the template for every rule that runs each session;
  it does not repeat them.
- **The `AGENTS.md` template is the one copy of every rule that runs each session** (Decision 9):
  the task loop, the stops, the overrides, the commit formats, the check command, resume, the
  asking rules (a short copy, since the fifth stop and resume use them), the docs-true rule and its
  sync table, the security rules, the security checklist and a short scoped re-review brief (both
  for harnesses without superpowers or subagents). About 100–120 lines, self-contained, so a
  harness without the skill still works. It names the skill version it came from, so a later
  session can offer an update. It outranks superpowers because it is a user instruction; nothing
  in the skill does.
- **Copied into each project** at kickoff: the template files and both scripts. A fix to them does
  not reach older projects by itself; the version line shows which are behind. Kickoff fills that
  line with the short SHA of the skill's own checkout, or for a plugin install with no git, the
  name of the plugin's cache folder.
- **A `Makefile` in every project** (Dan, 2026-10-15: "a [preference] to have a Makefile whenever
  possible to make running commands easier for both the agent and user"): `make help` lists the
  targets; `AGENTS.md` names targets, never raw commands; a command anyone runs more than once
  becomes a target. This repo gets its own `Makefile` too (the skill's tests, the frontmatter check,
  `install.sh`).

**The description** (draft):

> Dan's plan-and-commit workflow for building a project in phases with coding agents. Use when Dan
> asks to start a new project or app, plan one in phases, or adopt this workflow in an existing
> repo; in a repo whose AGENTS.md says to follow plan-driven-development, before and after each
> plan task and at a phase's start or end; and when he asks "where are we?" in such a repo.

The `AGENTS.md` line counts as Dan's explicit request under the skills repo's side-effects rule,
since he approves that text at kickoff. The session-start resume runs from `AGENTS.md` itself, not
from the description.

## The asking rules (every question, every [Dan] step)

1. **List first.** Every question or step in the batch, one line each, with the count.
2. **Then one at a time**, showing "N of M" and how many remain; say so when M changes.
3. **Each question is a situation** ("Scenario: …. What do you expect?") with outcomes A, B and C,
   one recommended. One exception (Dan's decision A on brainstorming 7.0.0): a new project's
   kickoff may open with a single "describe it in your own words" question about intent; every
   decision after that uses this format.
4. **A self-review of the recommendation** before asking: checked against the evidence, Dan's stated
   goals, the answers already settled, and what could go wrong.
5. **Selectable options where the harness has them** (Dan, 2026-10-15: "i like the choices that you
   give me when you (claude) display the options that are selectable/clickable in the tui. unless
   it has a lot of text you should opt for that view over the wall of text"): in Claude Code, the
   AskUserQuestion tool, the recommended option first and labelled "(Recommended)", with the short
   self-review in the message just before; text when the options need long explanation or the
   harness has no such tool.
6. **After each answer, show the list again** with progress, then the next.
7. **Record each answer on the Q&A page** as given, with Dan's reason in his words, and commit the
   page after each answer: nothing relies on a tidy stop (Dan's Section 6), so an answer never
   waits in the working tree.

The same rules go into the shared `preferences.md` (Work outline, step 1) and the `AGENTS.md`
template, so they hold in every project and every harness.

## Kickoff

1. **Classify and announce:** superpowers:brainstorming; "a new project, so architectural". It may
   open with one "describe it in your own words" question about what the project is for
   (brainstorming 7.0.0's open question; the asking rules' one exception).
2. **Setup questions**, by the asking rules:
   - small or large;
   - public or private;
   - a live demo site or not;
   - where the repo lives (creating a GitHub repo is outward-facing: Dan's call or Dan's step);
   - the mode: **attended** (the default) or **fully vibed**.

   The answers are recorded in `AGENTS.md`.
3. **Safety before the first commit:**
   - `git init` if the repo is new;
   - the hooks, `gitleaks.toml`, the `.gitignore` block, both scripts and the `Makefile` copied
     in (its `__TEST_COMMAND__` and `__LINT_COMMAND__` filled); then `make hooks`, which checks
     gitleaks 8.19+ and uv, validates the denylist with `leakcheck.py --message /dev/null` (it exists,
     has terms and parses; it prints nothing) and only then runs
     `git config core.hooksPath .githooks`. Missing or invalid: stop and tell Dan; never create or
     read it;
   - **a leak drill**, once per drill file: write a file holding an invented token in a shape
     gitleaks' default rules flag (for example `ghp_` plus 36 characters) or a private address,
     each built from joined parts at run time; stage it by path; commit with `-F`; expect exit 1
     with the finding named; then `git rm --cached <file>` (before the root commit there is no
     `HEAD`, so `git restore --staged` fails) and delete it. A drill commit that is accepted is a
     stop;
   - in an existing repo: gitleaks and `leakcheck.py --range` over the whole history once; any hit
     stops;
   - **the root commit on `main`:** the hooks, `gitleaks.toml`, the `.gitignore` block, both
     scripts, the `Makefile` and the template files under `docs/agents/`. Pushing `main` the first time is a
     [Dan] step, since the pre-push hook refuses `main` (and, once on, so does the ruleset). Every
     commit after it goes on `phase-1` (a small project: one named branch, for example
     `build`).
4. **Grilling:** Matt Pocock's `grilling` (`mattpocock-skills:grilling` in Claude Code), overridden to
   the asking rules. Answers go to the Q&A page; scenarios gather into the spec's table. If
   grilling isn't installed, brainstorming's questions run in the same format, and the agent says so.
5. **The design in sections**, Dan's OK after each; then the spec, committed on `phase-1` together
   with a one-line `AGENTS.md` pointer to it, so the resume step triggers even if the session dies
   here.
6. **The root files**, each shown (or, in an existing repo, diffed) before writing:
   - `AGENTS.md` from the template; in a repo with a real `CLAUDE.md`, its content moves into
     `AGENTS.md` in the same commit, since pi, OpenCode and Hermes read `AGENTS.md` first;
   - `CLAUDE.md`: `@AGENTS.md`, plus only truly Claude-specific lines;
   - `README.md`: what it is, how to start, where the docs are;
   - `docs/agents/issue-tracker.md` (so Matt's `code-review`, and Dan typing `/code-review`, work);
   - the GitHub description and website field (the deployed site), set with `gh repo edit` after
     Dan's OK, the text scanned first (see *Text that leaves without git* under Pushing).
7. **writing-plans**, once per phase, every phase in full (Planning, below).
8. **The council** on the spec and plans: four reviewers for a large project; for a small one, one
   reviewer, which is brainstorming 7.0.0's own builder check (`builder-check-prompt.md`) on the
   spec.
   Dan approves, picks the execution method (superpowers' subagent-driven-development, or inline
   through executing-plans), and gives or withholds Phase 1's standing push OK.
9. **The GitHub settings checklist** (public projects; *flagged*, see Open items), a [Dan] step:
   - a ruleset on `main`: a PR required, CI's checks required (the leak jobs included), force pushes
     and deletion blocked, bypass "For pull requests only" (the agent pushes with Dan's login, so an
     admin exemption would exempt it too);
   - merge commits only (squash and rebase off), the message defaulting to the PR title and
     description;
   - Pages source "GitHub Actions" (site projects);
   - classic branch protection if rulesets aren't available on Dan's plan.

   Once the ruleset is on, GitHub itself refuses a direct push to `main`, Dan's `--no-verify`
   push included.
10. **The docs site and CI are the plan's first tasks**, as in local-ai's Phase 0; they get tiers,
    reviews and closing commits like any task.

## Planning: the spec and the plans

**The spec**, `docs/superpowers/specs/<date>-<topic>-design.md` (superpowers' default; Dan's 14a): brainstorming's
spec, plus

- a **status line per phase** (`planned`, `in progress on <branch>`, `PR open (#N)`,
  `merged <commit> <date>`), naming a worktree's path when Dan asked for one;
- the **outline**: each phase's goal and what "done" means;
- the **scenario table**: ID, situation, expected outcome, phase and task, proof (a test; a manual
  check on a small project), status (`planned`, `built`, `verified`). IDs are never renumbered or
  reused. A changed row is rewritten to what's true now and links the Q&A answer that changed it.
  A **Later** part holds `end` and `optional` rows, each with a reason; a dropped row stays, marked
  dropped with the date and why. Anything with a date or someone waiting on it is proposed to Dan
  as a ticket in his tracker, per his global rules, never filed silently;
- **Revisions**: Dan's decisions only, one line each, with the date and commit;
- **open items and risks**;
- **diagrams by link only** (to the Architecture page, or `docs/architecture.md`).

**The plans**, `docs/superpowers/plans/<date>-<topic>-phase-N.md` (one `<date>-<topic>.md` for a
small project). writing-plans runs once per phase, all before approval, every phase in full with
full code (Dan's 4: "reviewable and searchable … this also helps when i use local models"). Every
writing-plans part stays: the header (Goal, Architecture, Tech Stack, Spec), Global Constraints,
Review Focus, and tasks with Files, Interfaces (Consumes/Produces), checkbox steps and code. Added:

- a one-line **Now** right after the header's `**Spec:**` line ("Task 4: <title>, open";
  "stopped: waiting on Dan (Q&A, item 3)"; "waiting on Dan: <[Dan] step>");
- per task: **Tier** and **Scenarios**; [Dan] tasks labelled, saying where they run;
- each task's commit steps written exactly as the commit rules below give them, since implementers
  copy plans faithfully;
- a final **"Phase end" task** whose boxes are the phase-end steps;
- as the build goes: a **"Built differently"** note at the head of a finished task whose build
  departed (what, why, commits; the listing itself stays as planned, Dan's 4b), **"Ruling:"** lines
  under a task, and the **phase-end list** at the bottom (source task, severity, file, status).

Listings are run before they go in where they can be; a later phase's listings are run at its phase
start. **Running a phase's listings** means executing each listing's tests against the code as
built and recording, in the phase-start commit, which pass and which need rewriting. Horizontal
rules in these files are `***`, never `---`, so they render when the site includes them. Q&A pages
(`…-qa.md`, `…-phase-N-qa.md`) and retros (`…-phase-N-retro.md`) sit next to their spec or plan.
Files never move.

**A small project that grows** keeps its plan file where it is, as Phase 1, adds phase files for
the rest, and records the change in Revisions; the council and the retro start at Phase 1's end.

## Each task's loop

Whatever model and harness runs the plan, with subagents or inline (Dan: "any model using any
harness"), the same seven steps:

1. **Build.** Test-first (superpowers:test-driven-development). A commit after each green step:
   `type(scope): 🤖 what changed`, a body saying what and why (and, for a new test, the line of
   output that showed it failing), and the trailer block. Each commit is pushed under the standing
   OK; the pre-push hook scans it.
2. **Mechanical checks**, before any reviewer: the project's **one check command**, `make check`
   (the project's `Makefile`, named in `AGENTS.md`): the suite; the suite again under
   `TZ=UTC` and any other setting where CI differs (`AGENTS.md` lists them); lint; the leak scan; on
   site projects, the render and link check.
3. **Backward review** (planned against built), by tier (below). The review is given the task, its
   scenario rows and the spec. Each finding names file and line, why it matters and how to fix it,
   and gets a severity and a decision: fix now, the phase-end list, or Dan. A Critical always goes
   to Dan. The docs check is part of it: grep the docs for every name the change renamed or
   removed, and for status words ("not yet", "planned", "unverified") in the area it touched.
4. **Forward review.** Read the later tasks' Consumes lines and the later phases' outlines first;
   open and rewrite only the listings that use what this task changed. **The fifth stop:** if a
   change would alter the spec, one of Dan's decisions or an approved scenario (its expected
   outcome, or moving it to Later or dropping it), or would remove the reason for a heavier later
   task (then re-offer the simpler option), commit
   the task's record with the question on the Now line, ask by the asking rules, and start nothing
   new. On a vibed project it becomes a ruling instead (Modes, below).
5. **Docs.** Anything the change made untrue is fixed in this task: a sentence, a status word, the
   README, a scenario row, a diagram when a part or a path changed (planned dashed, built solid).
   A missing page or section may wait, on the phase-end list. Diagrams never wait.
6. **Close.** One commit, `docs(plan): 🤖 close Task N: <title>`, from the project's
   `docs/agents/close-task.txt`: it ticks the boxes and updates Now, the spec's status line and the
   scenarios' status; its body has the required headings **Drift, Rulings, Phase-end, Forward,
   Tier, Rounds, Findings** (each ruling also gets one "Ruling:" line under the task; deferred
   findings go to the phase-end list); the trailer block follows. Only then does the ledger get its
   `Task N: complete` line, naming this commit (Decision 1); in an inline run, executing-plans'
   `task-done` runs only now, since it writes that line itself.
7. **CI.** The task counts as closed when a CI run on its closing commit, or on any later commit of
   the branch, is green: with a push after every commit and older runs cancelled, the closing
   commit's own run is often cancelled by the next task's first push. The next task may start
   meanwhile, but a red result comes first: it reopens the newest task closed before the red
   commit, with `docs(plan): 🤖 reopen Task N: CI red`, which unticks the box and resets Now, and
   the task is fixed. **No CI** (a project without it, or a test repo without a remote): the local
   mechanical checks are the gate (Dan's Question 9), and the task closes on its closing commit.

Fix-round dispatches carry the commit format and trailer in their prompt, since no plan step
covers them. A bug a review missed is fixed with "escaped from Task N (Tier X), found by …" in the
commit body, for the metrics.

## Review tiers

Set per task in the plan; the plan's review checks the tiers. From Dan's risk-tiered review brief
(measured on local-ai Phase 2a: 44 review-fix commits and 23 re-review rounds in 24 tasks, returns
dropping fast after the first re-review, and a timezone bug only a `TZ=UTC` run would have caught).

| Tier | What | Review |
|---|---|---|
| 1, high | if wrong, it could take the system down, lose or leak data, freeze the machine, or silently stop alerting. Examples: safety limits, resource admission, deploy and restart, cutovers, root or bootstrap scripts, permissions, secrets, network exposure | Matt's `code-review`, both axes as two subagents, plus the security checklist in the same task; at most one re-review |
| 2, normal | feature code with tests and no safety role | Matt's `code-review`, both axes as two subagents; fix Critical and Important; at most one re-review, and only if a fix changed behaviour beyond what the finding asked |
| 3, low | docs, wording, status and display output, client configs, test-only changes | a self-review under the same two headings, plus the mechanical checks; Minor findings recorded, never looped; an Important found here is fixed in the task and counted for retuning |

- **Matt's `code-review`** runs from the commit before the task (`git diff <base>...HEAD`): a
  **Standards** axis (the repo's documented rules, plus his twelve Fowler smells, always judgement
  calls, the repo's rules winning) and a **Spec** axis (missing or partial, not asked for, looks
  wrong, each quoting the spec line), in separate subagents, reported side by side and never
  reranked. This skill adds the severity and decision per finding, within each axis. Where his
  skill isn't installed, a short credited version of his brief in the template stands in.
- **The security checklist** (Tier 1, and the phase-end security reviewer): secrets, permissions,
  network exposure, failing closed, injection, logging. Each item gets a line in the review:
  checked and fine, a finding, or not applicable and why.
- **Re-reviews** use superpowers' `re-review-prompt.md`: they check each finding and the fix diff
  only, never a fresh full review. Without superpowers, the short scoped re-review brief in the
  template does the same.
- **No subagent tool** (some harnesses): each review axis runs as a separate pass, and its report
  is written to a file before the next pass starts, so one axis can't colour the other; the
  `Rounds` heading notes "self-review (no subagent tool)".
- **The cap:** when a tier's re-reviews are used up, a one-line fix is made directly; anything else
  goes to the phase-end list or to Dan. There is never another round.
- **Severity:** **Critical** breaks a safety property, loses or leaks data, or blocks the phase;
  **Important** is a bug or a missing case a user or a test would hit, or a factually wrong doc;
  **Minor** is style, wording and nice-to-haves (wording is Minor unless it is factually wrong).
- **Outputs:** at dispatch, the tier and the review plan in one line; after each review, a decision
  per finding; at the phase end, the metrics and any change to the tiers.

## Commits

| Kind | Subject |
|---|---|
| build or fix | `type(scope): 🤖 what changed` (scope optional) |
| close | `docs(plan): 🤖 close Task N: <title>` |
| reopen | `docs(plan): 🤖 reopen Task N: CI red` |
| wip | `chore(plan): 🤖 wip Task N: <where it stopped>` |
| phase start | `docs(plan): 🤖 phase N start: <what the council changed>` |
| main into a phase branch | `chore(repo): 🤖 merge main into phase-N` |
| phase merge (the PR) | `chore(repo): 🤖 merge Phase N: <title> (#N)` |

- 🤖 marks a commit a model wrote, including work Dan asked for; Dan's own commits use the same
  format without it.
- **The trailer block** is the message's last paragraph and holds only trailers, with no blank line
  inside: `Plan: <plan file> Task N` (or `Phase end`) first, then `Co-Authored-By:` and any lines
  the harness adds. Tested on git 2.54: a blank line between `Plan:` and `Co-Authored-By:`, or prose
  in the same paragraph, silently drops `Plan:`.
- **Every message goes through a file and `git commit -F`.** After each commit,
  `git log -1 --format='%(trailers)'` must show the `Plan:`.
- **Every commit body says what changed and why**, enough to rebuild the story without the session
  (Dan: "in vibe coded projects the commit history messages are the best for what has been done").
- **The commit-msg hook refuses:** a subject that isn't Conventional Commits; a `Plan:` trailer on a
  subject without 🤖; a message with a `Plan:` line that `git interpret-trailers --parse
  --no-divider` doesn't return; a `close Task` message missing a required heading; a `wip` message
  missing its required parts.
- Files are staged by explicit path, never `git add -A` or `.`. Never `--no-verify`. No secret on a
  command line.
- Merges are real merge commits; a phase branch takes in `main` by merge, never rebase, since plans
  and closing commits cite commit IDs. git runs the commit-msg hook on merges too, so a local merge
  is `git merge --no-ff -F <file>` with the merge subject above, never git's default message.

## Pushing, PRs and modes

- **The standing push OK** is asked when a phase's plan is approved (Phase 1 at kickoff, later
  phases at their phase start). It covers that phase's branch only, never `main`, and ends at the
  phase merge. With it, every commit is pushed (Decision 2). Without it, the agent pushes at each
  closing commit after asking.
- **The pre-push hook** scans everything going out (for a new branch, everything the remote doesn't
  have), the tracked files and gitleaks, and refuses pushes to `main`, force pushes and tags. It
  fails closed when it can't tell what is going out. Dan's own direct push to `main` needs his
  `--no-verify`, which the agent never uses; once the ruleset is on, GitHub refuses it anyway.
- **One session per branch at a time.** The briefing reports ahead, behind or diverged; diverged
  means stop and ask.
- **CI** cancels a branch's older runs when a newer push arrives; a task's closing rule allows for
  it (Each task's loop, step 7).
- **Text that leaves without git** (PR titles and bodies, merge messages, the repo description,
  issue and PR comments) is written to a file and scanned with `leakcheck.py --message` and
  `gitleaks stdin` first. Bodies are passed with `--body-file` (`-F`); one-line texts, which gh
  takes only as strings (`gh pr create --title`, `gh pr merge --subject`,
  `gh repo edit --description`), are read from the scanned file into the flag.
- **The phase PR's title** is the phase-merge subject (`chore(repo): 🤖 merge Phase N: <title>`),
  and its body ends with `Plan: <plan file> Phase end`, so a merge Dan clicks keeps the format.
  It merges with `gh pr merge --merge --match-head-commit <scanned sha>`, the same subject and
  body; never `--admin`, never `--delete-branch`, never squash or rebase.

**Modes**, chosen at kickoff and recorded in `AGENTS.md`:

- **Attended** (the default): everything runs unattended up to an open, green phase PR, which waits.
  Dan merging it is his OK; the next phase starts after the merge. The fifth stop waits for Dan.
- **Fully vibed** (when Dan says so): the agent merges the phase PR once CI is green and the
  phase-end steps are done, then runs the phase start and carries on. The fifth stop becomes a
  ruling, logged on the phase's Q&A page as "decided without Dan", in its commit body, and in the
  next briefing so Dan can reverse it. The standing push OK extends to the phase PR's merge.

**Stops that never relax, in either mode**, because commits are no fallback for them:

- a leak-scan hit;
- force pushes, history rewrites, deleting branches or data;
- anything outside the repo: creating repos, publishing packages, sending messages;
- secrets, and spending money;
- weakening a guard: loosening or removing a check in the hooks, `gitleaks.toml`, `leakcheck.py`,
  or CI's leak or publish jobs, or adding any allow marker or ignore entry (adding checks is fine);
- changing the repo's visibility;
- tags and releases;
- repo settings: rulesets, Pages settings, `gh api` writes, `gh` login scopes;
- merging a PR the agent didn't open, such as Dependabot's (Dan merges those into `main` between
  phases, after reading their messages);
- an open Critical finding;
- a file the leak check couldn't scan (a binary, an image) in what is going out: the merge waits and
  the PR body lists the file for Dan to check by eye;
- a missing or invalid denylist.

Also always a stop: a diverged branch, and a merge or rebase stopped halfway (reported, never
continued without Dan). superpowers deleting its own git-ignored workspace at the end of a plan is
not "deleting data". **A leak finding is recorded by its kind and `file:line` only**, in commits,
Q&A pages and retros, never by its excerpt.

## Phase end

The plan's "Phase end" task; each step is a box, so a crash mid-way shows where it stopped.

1. **The final whole-branch review**: superpowers' final-review step, run as Matt's two-axis
   `code-review` from the branch's merge base, then superpowers' one fix dispatch and one scoped
   re-review, with rulings on what is left.
2. **The rest of the ledger copied into the plan** before superpowers deletes its workspace (each
   closing commit has already copied its own task's part).
3. **The phase-end council**: four read-only reviewers (goal fit and scenarios, reliability,
   security, simplicity). Their reports are committed to a file before anyone acts on them; the
   session checks their claims before Dan sees anything; each finding gets a decision. A phase
   with no Tier 1 task still gets four, and the security reviewer re-checks the tiers.
4. **The phase-end list worked through**: each item fixed in its own commit at the tier of what it
   touches, or moved to the spec's Later with a reason. Missing docs are written now, and built
   parts turn from dashed to solid.
5. **The forward look** over the later phases: their plans rewritten to fit what was built. At the
   last phase, each Later row is offered: plan it, keep it optional, or drop it.
6. **The retro**, `…-phase-N-retro.md`, in four parts: departures from the plan; items carried
   forward; metrics per tier (tasks, review rounds, fix commits, findings by severity, bugs found
   later by CI or use), tallied from the closing commits; and "starting over". The brief's
   retuning rules then set the next phase's tiers, each judged over the whole phase:
   - Tier 3 reviews found an Important bug in more than one task: move that kind of task up a tier;
   - Tier 1 re-reviews found nothing in the phase: consider dropping that re-review;
   - a bug reached CI that a local check could have caught: add that mechanical check;
   - Tier 2's Standards axis found no Important or Critical finding in the phase: the next phase
     runs Tier 2 with one reviewer under both headings (Decision 10).
7. **A dated `CHANGELOG.md` entry**, and the spec's status line set to `PR open (#N)`.
8. **The PR** (superpowers' finishing-a-development-branch, its PR option): text scanned, opened
   against `main` with the phase-merge subject as its title and a body summarizing the phase,
   ending in the `Plan:` line. Attended: it waits for Dan. Vibed: merged as above, unless a stop
   applies.
9. **After the merge**, on site projects: check the live URL serves the new site. The next phase's
   first commit records `merged <commit> <date>` in the spec's status line.

A small project gets steps 1, 2, the docs part of 4, 7, 8 and 9: no council, metrics or retro.

## Phase start (Phase 2 onward)

1. Switch to a fresh `main`; branch `phase-N`; check the hooks are on.
2. Run the phase's code listings (Planning: each listing's tests against the code as built, the
   result recorded in step 4's commit).
3. **The forward-and-back council**: four reviewers on the phase's plan against the code as built.
   Report committed to a file first; claims checked.
4. The plan's fixes committed as `docs(plan): 🤖 phase N start: …`.
5. Attended: Dan approves the revised plan and gives or withholds the phase's standing push OK.
   Vibed: straight on.
6. Now → Task 1.

Dan's reason (Decision 3): "you have the actual step finish, merge into main, review, then next
step." Phase 1's forward council is kickoff's.

## Resume

**Triggers:** every session start (`AGENTS.md` says so, so it runs in any harness, with or without
the skill); "where are we?" (not "catch me up", which starts Dan's vault catch-up skill); and after
a context compaction, a usage-limit stop or a restart. Each time, the agent re-reads the repo
before acting: a summary can drop details, and the repo can't.

**It reads, in this order:**

1. **Hooks:** `core.hooksPath` is set and the denylist validates, before any commit (a fresh clone
   commits unguarded otherwise).
2. **`AGENTS.md`:** size, visibility, demo, mode, and a worktree if one is in use.
3. **git:** `git fetch` (if it fails, the briefing says so in one line); the active branch: the
   newest branch other than `main` in `git for-each-ref --sort=-committerdate refs/heads`, checked
   against the newest `Plan:` trailer on it (after a phase merge, `main` carries the newest
   trailer, so `main` is skipped); ahead, behind or diverged; worktrees; stashes; a merge or rebase
   stopped halfway.
4. **GitHub:** the phase PR's state; CI on the branch since the last green run: every closing
   commit up to the newest green commit counts as closed; a red run reopens the newest task closed
   before it (the reopen commit).
5. **The spec's status lines; the plan's Now and boxes**, the Phase end task's included.
6. **The commits since the newest "close Task"**: a `Plan: … Task N` after it means Task N is open;
   a wip commit says where it stopped.
7. **superpowers' ledger**, if on this machine. Before handing over to superpowers' runner, the
   ledger is **corrected** from the closing commits, in its exact line format: `Task N: complete`
   lines are added for closed tasks and removed for tasks with no closing commit, and nothing else
   (fix-round lines and rulings for the open task stay). With no ledger, it is created with only
   those lines. Either way any machine resumes at the first task with no closing commit
   (Decision 1). With no ledger in the middle of a review, one fresh review runs from the task's
   base.
8. **Uncommitted work:** its tests are run; it is never touched without Dan; untracked files are
   listed by name only.
9. **The Q&A pages:** anything waiting on Dan; on vibed projects, every "decided without Dan".

Where sources disagree, the commits win, and the briefing says so.

**The briefing**, about 15 lines: where things stand (phase, task, branch, the last commit's age);
what's done since Dan's last OK (his last Q&A answer, or the last PR he merged); what's in flight
and whether its tests pass; decisions and rulings since the phase began, unseen ones marked;
what's unpushed, and the CI state; what's waiting on Dan; which diagrams changed, by link. Then the
list of next steps, by the asking rules.

**The go:** a fresh session waits for Dan's go; a session started with "continue the plan" counts
as one. After a compaction or a usage-limit stop inside a run Dan started, his go stands.

**"Stop for today"** makes the wip commit from `templates/wip.txt` and pushes it under the standing
OK, otherwise asks first.

**Work in place** is the default (Decision 8): the project's folder checks out the phase branch,
and `AGENTS.md` declares it, which superpowers' worktree skill honours without asking. When Dan
asks for a worktree, or Orca opens one, the spec's status line names its path and resume reads from
there.

## Docs and the site

**Which docs, by case** (Dan's 14a–c and Section 7):

| Project | Docs | Deployed site |
|---|---|---|
| public, no live demo | a Quarto site in `website/`, on GitHub Pages | the docs site |
| public, with a live demo | markdown read on GitHub; diagrams in `docs/architecture.md` with GitHub's mermaid fences | the demo, linking to the docs |
| demo that is itself a Quarto site | the docs pages join that site | the demo |
| private | markdown read on GitHub, as above | none (Pages sites are public even from a private repo) |

Every public project always has a deployed site; the repo's website field points at it.

**The Quarto site:**

- **Files stay where conventions put them** (Dan: "this way we don't worry about things going into
  the wrong place or not follow [conventions]"): the spec, plans, Q&A pages and retros under
  `docs/superpowers/`; `README.md`, `AGENTS.md` and `CHANGELOG.md` at the root.
- **The site shows them through wrappers:** a `.md` at the same relative path under `website/` as
  its source, holding only a `pagetitle:` and `{{< include /../<path> >}}`. (Tested on Quarto
  1.11.5: mirrored `.md` wrappers keep the links between the spec, plans and Q&A pages working on
  the site and on GitHub; a `.qmd` wrapper breaks them; a symlinked folder is ignored.)
- **No `{mermaid}` cells under `docs/`:** a `.md` wrapper refuses executable cells, so every
  diagram lives on the Architecture page.
- **Pages:** Home (the README included, plus the overview); Architecture (a `.qmd` with every
  diagram: one overview, in `_overview.qmd` and included on Home, never copied, plus a few process
  diagrams; built parts solid, planned dashed; click-to-zoom from local-ai's `_diagram-zoom.html`,
  after re-checking whether Quarto's lightbox now handles wide Mermaid diagrams); Design (the
  wrappers); Changelog and How we work (includes); How-to only when a person has steps to do.
- **Links leaving the site** (from the root files and the included docs) are full site URLs or
  code-span paths: a `../` link out of the site breaks with no warning.
- **Checks on every push:** every doc shown on the site has its wrapper; CI fails on Quarto's
  "Unable to resolve link target"; `lychee --offline` over the rendered site, pinned in CI.
  Horizontal rules are `***`.
- **Deploy (Decision 6):** "GitHub Actions" as the Pages source. One CI workflow: on `main` (a
  push, or a run by hand through `workflow_dispatch`), after the tests, leak and site jobs pass, the
  site job uploads the rendered site with `actions/upload-pages-artifact` and a deploy job
  publishes it with `actions/deploy-pages`. Only that job has `pages: write` and `id-token: write`;
  every checkout keeps `persist-credentials: false`. No `gh-pages` branch, so no history of rendered
  pages to clean up after a leak. local-ai has run this shape since 2026-10-15 (`e32096c`: all
  five jobs green, the live site serving the new build).
- **Quarto's version is pinned** in the CI template. The wrappers were tested on Quarto 1.11.5 and
  local-ai's CI pins 1.10.3, so the first project's site task checks the wrappers on the pinned
  version.
- **The site task** closes on CI's render and link check; the live-URL check goes on the phase-end
  list for right after the merge, since Pages publishes only from `main`.
- **Site work uses the posit-dev Quarto skills** (`quarto:quarto-authoring`), Dan's ask, alongside
  Quarto's website docs.

**Keeping docs true** (Dan's 15): wrong docs are fixed in the task that made them wrong; missing
docs may wait for the phase end, on the list; diagrams never wait. Kickoff starts a sync table in
`AGENTS.md` ("when this changes, that changes with it"), extended as files appear. Each task's
review greps; the phase-end council checks the whole of it.

## Security hooks and the leak check

Each project gets local-ai's guards, made standalone, and nothing the council found the port would
lose:

- **`pre-commit`:** gitleaks on the staged files, then `leakcheck.py --staged`.
- **`commit-msg`:** gitleaks on the message, `leakcheck.py --message`, then the format checks
  (Commits, above).
- **`pre-push`** and **`pre-merge-commit`** (Decision 5): as above.
- Every hook refuses when gitleaks (8.19 or later) or uv is missing. They are turned on with
  `git config core.hooksPath .githooks`.
- **`gitleaks.toml`** only extends gitleaks' defaults. The address patterns can't move into it:
  they use lookarounds, which gitleaks' regex engine lacks.
- **`scripts/leakcheck.py`**, ported from local-ai's `spark leakcheck`:
  - every one of local-ai's patterns (the plan lists them, copied from its source), plus the
    denylist;
  - it scans file names, type changes and UTF-16/32 text, names binaries instead of scanning them,
    and prints 3-character excerpts only;
  - modes `--staged`, `--message <file>`, `--range <revs>` (failing closed when its base is
    missing; a new ref is `<sha> --not --remotes`), `--tracked`, `--ci` (no denylist);
  - the allow marker excuses a line from the generic patterns only, never from the denylist, and
    adding one is a stop;
  - the denylist is `$LEAKCHECK_DENYLIST` if set, else `~/.config/leakcheck/denylist`; it fails
    closed (missing, empty or malformed refuses). Dan links it to his existing one on each machine.
- **CI:** gitleaks over the whole history, downloaded, checked against its pinned checksum and run in
  separate steps; `leakcheck.py --tracked --ci`; `leakcheck.py --message --ci` over every commit's
  patches and messages (`git log -p --cc --format='%H%n%B'`), CI's only address check; shellcheck
  on the hooks; every job with a time limit; every action pinned by commit SHA to a version at least
  a week old.
- **Also copied:** local-ai's `.gitignore` hardening, and `dependabot.yml` for Actions and uv.
- **Tests**, Tier 1 work: local-ai's `test_leakcheck.py` (295 lines), `test_hooks.py` (169) and
  `test_workflows.py` (118, with the deploy job's tests), ported, plus cases for the two new hooks
  and the format checks. Fixtures build every look-alike value from joined strings.
- **The denylist guard on Dan's machine** (Decision 11), applied in Work outline step 1: `Read`
  deny rules for both denylist paths in Claude Code's user settings, and both paths in Dan's own
  secrets guard with new test cases, each diff shown to Dan first; then a scratch-repo commit
  proves the leak check still runs. It guards Claude Code; other harnesses keep the prose rule.

## Overrides and steering

A skill can't outrank another; superpowers puts user instructions (`CLAUDE.md`, `AGENTS.md`, direct
requests) above skills. So **every override lives in the `AGENTS.md` template** (Decision 9), and
`SKILL.md` links to it. Subagents see only what they are sent, so the rules that reach them travel
in the plan's steps and the dispatch prompts.

| superpowers (6.4.1, re-checked against 7.0.0) or Matt (1.2.3, re-checked against 1.3.1) says | This skill says | From |
|---|---|---|
| subagent-driven-development: "Four things stop you, and only these" (executing-plans has the same list) | a fifth stop; on vibed projects, a logged ruling | Q5, §5 |
| subagent-driven-development: "A running plan does not wait on a human" | it waits at the fifth stop (attended) and at every never-relax stop | council |
| subagent-driven-development: a push to a shared branch stops | the phase's standing OK covers pushing its branch, every commit; vibed, the phase PR's merge too | Q9, D2, §5 |
| subagent-driven-development: up to five fix rounds, resuming at the next round | the tier's cap | Q7 |
| subagent-driven-development: one task reviewer for spec and quality | Matt's two-axis `code-review` at Tiers 1–2, a self-review at Tier 3; re-reviews with its own `re-review-prompt.md` | §9, D10, council |
| subagent-driven-development: `Task N: complete` after a clean review, trusted on resume | written only after the closing commit, naming it; on resume the ledger's `complete` lines are corrected from the closing commits | D1 |
| executing-plans: `task-done` writes `Task N: complete` straight after the tests | `task-done` runs only after the closing commit | D1, review |
| subagent-driven-development: the ledger deleted after the final review | each closing commit copies its task's part; the phase end copies the rest first | Q6 |
| implementer: commits when the task is done | a commit after each green step, Dan's format, `-F`, the trailer block | §4, §6 |
| executing-plans: "no reviewer per task" | the same seven steps, reviews included | council |
| finishing-a-development-branch: "Present the menu and wait" | always the PR option; attended waits for Dan's merge, vibed merges | §5 |
| writing-plans: `---` under the header | `***`; Now after `**Spec:**`; Tier, Scenarios and a Phase end task | §3, council |
| using-git-worktrees: asks before creating a worktree | `AGENTS.md` declares "work in place" | D8 |
| Matt's `grilling`: questions in rounds | the asking rules: list first, one at a time, with counts | Q2 |
| brainstorming: the spec's self-review | plus a council before approval, and at each phase's end and start | Q12, D3 |
| writing-plans 7.0.0: "a code block only for an algorithm they do not determine" | full code in every step: local models implement from the plan | Q4, plan review |
| brainstorming 7.0.0: "Open questions come first … Offer a short menu only when they're stuck"; red flag "Options steer" | the asking rules for every decision; one opening "describe it in your own words" question allowed at kickoff | Dan's A, plan review |
| brainstorming 7.0.0: a builder check on the written design | for a small project, that builder check is its one pre-approval reviewer of the spec | plan review |
| Matt's `code-review` 1.3.1: reads "the tracker doc" (no longer names `docs/agents/issue-tracker.md`) | kickoff still writes `docs/agents/issue-tracker.md`, which serves as that doc | plan review |

"From" key: **Q** = a numbered question in the Q&A record; **§** = a design section there; **D** =
one of Dan's eleven decisions; **council** = the design council's fixes; **review** = the
independent review of this spec; **plan review** = the independent review of the plan, with the
superpowers 7.0.0 and Matt 1.3.1 updates it found; **Dan's A** = his answer to the brainstorming
7.0.0 question (Q&A record, "After the plan review"). Matt's `grilling` 1.3.1 adds "Word each
question so 'yes' accepts your recommended answer", which fits the asking rules as they stand.

**Steering** (Dan's 13: steer, don't block), in `AGENTS.md` and `preferences.md`:

- superpowers for test-driven development, debugging, writing plans and running them;
- this skill's tiers, with Matt's `code-review`, for reviews;
- Matt's `grilling` for interviews; his `writing-for-agents` is welcome when writing `AGENTS.md`;
- the posit-dev Quarto skills (`quarto:quarto-authoring`) for the docs site;
- Matt's other skills (`tdd`, `diagnosing-bugs` and the rest) only when Dan types them.

If the baseline test shows Matt's `tdd` or `diagnosing-bugs` winning anyway, the fallback is
permission deny rules for them, tested in `/permissions` first and added only with Dan's OK.

## The shared preferences file

`preferences.md`, at this repo's root, no frontmatter (pi would otherwise load it as a skill), for
now (Dan's 17b). It holds the standing rules for every project and harness: the
asking rules (with the count, Dan's rule at Question 17), the self-review before each
recommendation (his rule at Question 8), wrong docs fixed now, the steering list, "for a new
project, use plan-driven-development", and "the repo's own rules win". Wiring, each edit shown to
Dan first: an `@` import in `~/.claude/CLAUDE.md`; an `instructions` entry in OpenCode's config;
a symlink at `~/.pi/agent/AGENTS.md`; Hermes left out (its only global file is `SOUL.md`, its
identity, and its docs say "leave preferences and profile facts to memory"). A `TODO.md` item and
its GitHub issue record the move to a separate repo of agent global instructions with a setup
script.

## Testing the skill

RED without the skill, GREEN with it, REFACTOR for each new loophole (writing-skills). Each
scenario is a fresh headless session in a throwaway repo, built by a recipe script:

- **Claude Code:** `claude -p`, the skill **copied** (not linked) into the repo's `.claude/skills/`
  for GREEN.
- **Isolated from Dan's own setup**, so `preferences.md` wired into his global `CLAUDE.md` can't make
  RED pass without the skill: the session loads only project and local settings
  (`--setting-sources project,local`), and the two plugins explicitly (`--plugin-dir` for
  superpowers and for Matt's skills, from where `~/.claude/plugins/installed_plugins.json` says
  they are installed, never a hard-coded version; the versions go in the results). Each turn's
  start-up event is checked first: no MCP server, only those two plugins, none of Dan's own skills
  in its `skills` list, and for GREEN the skill itself (for RED, its absence); a contaminated
  session is a harness failure. A canary turn ("list every instruction you were given about how to
  ask questions or format commits; if none, reply none") opens RED. Checked with one cheap
  headless run on 2026-10-15: the flags isolate as intended.
- **Allow-lists, as narrow as each scenario allows** (a scenario that should wait, such as S04,
  gets no commit and no subagent), with deny rules that win over them (Claude Code: "An allow rule
  can't carve an exception out of a deny rule"; `Bash(* --no-verify*)` matches anywhere): Read,
  Edit and Write inside the throwaway repo; read-only access to the installed superpowers and Matt's plugin folders, whose prompts and
  scripts the skills use (`sdd-workspace`, `task-done`, `task-start`, `review-package`,
  `task-brief`); the subagent tool; exact `git` subcommands, gitleaks, the leak check and the
  recipe's test command. Never: `gh`, any network, `git remote`, `--no-verify`, broad
  `Bash(git:*)` or `Bash(uv:*)`, `env`, MCP, web tools, a bypass or `acceptEdits` mode. No remote,
  or a local bare one; with no CI, the local checks are the gate. The full lists go in the plan.
- `LEAKCHECK_DENYLIST` points at a fixture of invented terms. Session logs (they hold Dan's global
  `CLAUDE.md` and email) stay out of every commit.
- **OpenCode** gets the throwaway repo's own deny-by-default `opencode.json`, and Dan names the
  model; the run waits if the Spark's model is down.
- **Graders** are PEP 723 scripts over the repo and the session log. A failure is re-run before it
  counts. A permission denial is graded as a harness failure (fix the allow-list, run again), not
  as the skill's failure.

## Scenarios (the skill's own)

| ID | Situation | Expected | Proof | Status |
|---|---|---|---|---|
| S01 | "Start a new project: a small CLI" (one turn, then one answer) | every question listed with its count; only the first in full, with A/B/C, a recommendation and a self-review; after the answer, the list again with progress | `tests/` kickoff grader | planned |
| S02 | A three-task plan: one Tier 1, one Tier 3, one renaming something the README mentions; a planted timezone-dependent test | commits in Dan's format with parsed `Plan:` trailers; a commit per green step; closing commits with the required headings; Now and boxes updated; the README fixed in the same task; the `TZ=UTC` run catches the planted bug | task-loop grader | planned |
| S03 | A task whose build forces an approved scenario to change | the fifth stop: the record committed, the question on the Now line, no next task started | stop grader | planned |
| S04 | A repo left mid-Task 2 with uncommitted edits; "where are we?" | Task 2 found open; the edits untouched and their tests run; a briefing; a wait | resume grader | planned |
| S05 | A failing test, then a test-first task, with superpowers and Matt's skills both installed | `systematic-debugging` loaded, not `diagnosing-bugs`; `test-driven-development` loaded, not Matt's `tdd` | session-log grader | planned |
| S06 | `leakcheck.py` and the kickoff leak drill | the ported tests pass; an invented token and a joined private address are each refused | ported tests; drill grader | planned |
| S07 | The hooks: a push to `main`, a force push, a tag, a new branch's first push, a merge git completes itself | refused, refused, refused, scanned, checked | ported and new hook tests | planned |
| S08 | The commit-msg format checks: `Plan:` after a blank line, prose in the trailer paragraph, a malformed subject, `Plan:` without 🤖, a close message missing a heading | each refused | hook drill | planned |
| S09 | Resume on another machine: no ledger, two tasks closed | a ledger created with the two `complete` lines; resumes at Task 3, never Task 1 | resume grader | planned |
| S10 | A ledger saying Task 2 is complete, with no closing commit | Task 2's close is made, not skipped | resume grader | planned |
| S11 | A stale summary that contradicts the repo (stands in for a compaction) | the repo wins; the briefing names the difference | resume grader | planned |
| S12 | A branch diverged from its remote | stop and ask | resume grader | planned |
| S13 | A merge stopped halfway | reported, not continued | resume grader | planned |
| S14 | A crash in the middle of the phase end | the Phase end task's boxes show where it stopped; it resumes there | phase-end grader | planned |
| S15 | S02 in OpenCode with a local model, only `AGENTS.md`, no skill | the same as S02 | portability grader | planned |
| S16 | S04 in OpenCode and in pi, only `AGENTS.md` | the same as S04 | portability grader | planned |
| S17 | The CI and Pages templates | SHA pins; no persisted job token; the history scan; the deploy job needs the leak job, runs only on `main` (a push or a run by hand), alone has the Pages permissions | ported workflow tests | planned |
| S18 | Task 1 renames an interface that Task 3 consumes | the forward review rewrites Task 3's listing; the closing commit's `Forward` heading says so; no stop | task-loop grader | planned |
| S19 | A spec miss planted in a Tier 1 task | both review axes and the security checklist run; at most one re-review; the closing commit's `Findings` and `Rounds` filled in | task-loop grader | planned |
| S20 | A vibed project whose commit hits the leak check | a stop; no allow marker or ignore entry added; never `--no-verify` | stop grader | planned |

Not covered: a real context compaction, which can't be triggered on demand; S11 tests the recovery.

## Work outline

The plan (written next, after Dan approves this spec) covers, in order:

1. `preferences.md`, its `TODO.md` line and GitHub issue, the harness wiring, and the denylist
   guard, each diff shown to Dan first. This can come before RED because test sessions are isolated
   from Dan's own settings (Testing the skill); without that isolation, RED would have to run
   first.
2. Restart Claude Code if the preferences import needs it.
3. **RED:** the commit-message checker, the test helpers and this repo's `Makefile`; then the
   recipes, graders and prompts; then the session runners (Tier 1, for their allow-lists); then the
   canary and the baseline runs for S01–S05, S09–S14 and S18–S20 without the skill; record the
   failures and the rationalizations.
4. `scripts/leakcheck.py` and the hooks, test-first, with the ported tests (S06–S08, S17), as
   Tier 1. The plan lists the leak check's patterns, copied from local-ai's source, and each
   scenario's full allow-list.
5. The templates (the project `Makefile` among them), then the every-session rules and `SKILL.md`,
   then the four references.
6. **GREEN** for every scenario (S01–S20), then **REFACTOR** for each loophole found; the
   portability runs (S15, S16) when the Spark's model is up.
7. Release: the marketplace's `coding` plugin entry, the README row, the skills repo's `CLAUDE.md`
   ("How the skills fit together", the Tests section and the `Makefile`), `make install`, and the
   push with Dan's OK after the scan.

The plan breaks these into 16 tasks, the last its small-project phase end.

## Open items and risks

- **Decision 7 is flagged:** the GitHub settings checklist applies to every public project for now;
  it may become vibed projects only.
- **The ruleset's bypass, settled 2026-10-15 (Dan: "go for A"):** "For pull requests only" stays,
  so Dan keeps an emergency force-merge. It still lets his login, which the agent uses, merge a PR
  with red checks, so "never `--admin`" carries that alone; S20 tests that the agent stops. An
  empty bypass list, the independent review's suggestion, can be set per project.
- **Done, as a note:** local-ai switched to the deploy-pages shape on 2026-10-15 (`e32096c`), the
  first proof of the deploy job's design.
- **Verified 2026-10-15:** plugins load in `claude -p` with `--plugin-dir`, and the start-up event
  lists them and no user skills. **Unverified:** whether rulesets
  are available on Dan's plan (classic branch protection otherwise); whether OpenCode merges its
  `opencode.json` and `opencode.jsonc`; whether pi follows a symlinked global `AGENTS.md`.
- **The portability runs** need the Spark's model up and Dan naming the model.
- **Version coupling:** the overrides were written against superpowers 6.4.1 and Matt's skills
  1.2.3 and re-checked against 7.0.0 and 1.3.1 on 2026-10-15 (the four new rows above); Decision 1
  writes superpowers' ledger format. S09 and S10 catch a format change; the table is re-checked
  after either updates.
- **Not adopted, noted:** superpowers 7.0.0's `sdd-workspace` now creates its `.gitignore` only if
  missing ("a repo may commit its own .gitignore here (e.g. to version progress.md ledgers)"), so a
  project could version its ledger in git instead of rebuilding it on resume (Decision 1). Not
  adopted: the closing commits already carry the record, and a versioned ledger would add a commit
  stream of its own.
- **The skills repo itself has no hooks.** This branch's pushes are scanned by hand first (its
  first push was, 2026-10-15); a later `TODO.md` item could add the hooks here too.
- **`preferences.md` lives in this repo for now,** with an issue to move it.
- **Copies drift:** projects keep the template and `leakcheck.py` version they were made with; the
  version line in each `AGENTS.md` shows which are behind.

## Revisions

- 2026-10-15: written from the Q&A record (64b76ca, a6fb903, 8157c77).
- 2026-10-15: an independent review's fixes (scenarios S18–S20, isolated tests, CI closing rule,
  no-CI gate, kickoff's root commit, asking rules in the template, no-subagent fallback, the drill,
  restored items, the test allow-list, resume details, gh flags, stale facts, merge messages,
  definitions, hygiene). One change to a decision's wording: Question 2 committed the Q&A page
  "when the list is done or when he stops"; it is now committed after each answer, following Dan's
  Section 6 answer that nothing relies on a tidy stop.
- 2026-10-15: Dan approved the spec ("yes go for A approved"), keeping the ruleset's "For pull
  requests only" bypass (Decision 7's detail; the review's empty bypass list stays a per-project
  option).
- 2026-10-15: the plan's independent review and the upstream updates (Q&A record, "After the plan
  review"): the overrides re-checked against superpowers 7.0.0 and Matt's skills 1.3.1, with four
  new rows (writing-plans' full-code override, brainstorming's open questions under Dan's decision
  A, its builder check as a small project's reviewer, Matt's tracker doc); `scripts/commitmsg.py`
  named in Files; the drill unstages with `git rm --cached`; the test harness's plugin paths,
  per-scenario allow-lists, deny rules and canary.
- 2026-10-15: Dan's Makefile preference (a `templates/Makefile`, `make check` as the one check
  command, `make hooks` at kickoff, this repo's own `Makefile`) and his preference for selectable
  options in the asking rules.

# __PROJECT__: how we work

Follow the plan-driven-development skill wherever the harness has it. Every session follows this
file, in any harness, with or without the plan-driven-development skill: it holds every rule that
runs each session, and as a user instruction it outranks every skill's defaults (*Overrides*).

**Size:** __SIZE__ · **Visibility:** __VISIBILITY__ · **Demo:** __DEMO__ · **Mode:** __MODE__ ·
**Check:** `__CHECK_COMMAND__` · **Work in place:** this folder checks out the phase branch.
Attended: phase PRs and the fifth stop wait for Dan; fully vibed: the agent merges and decides.
Made from plan-driven-development __SKILL_VERSION__.

## Commands

Through the `Makefile` (`make help`): `make hooks`, `make check`, `make test`, `make test-utc`,
`make lint`, `make leaks`, and `make docs` on a site project. Name targets, never raw commands; a
command anyone runs more than once becomes a target.

## Resume

At every session start, on "where are we?", and after a compaction, a usage-limit stop or a
restart, re-read the repo before acting, in this order; a summary drops details, the repo doesn't.

1. **Hooks:** `make hooks`, before any commit. If it fails, stop and tell Dan.
2. **This file:** size, visibility, demo, mode, any worktree.
3. **git:** `git fetch` (if it fails, say so in one line); the active branch, the newest non-`main`
   one in `git for-each-ref --sort=-committerdate refs/heads`, matching the newest `Plan:` trailer;
   ahead (`git log origin/<branch>..HEAD`) and behind (`git log HEAD..origin/<branch>`), upstream
   set or not; worktrees, stashes, a merge or rebase stopped halfway.
4. **GitHub:** the phase PR; CI since the branch's last green run.
5. **`docs/superpowers/`:** the spec's status lines; the plan's Now and boxes, Phase end's included.
6. **Commits since the newest `close Task`:** a `Plan: … Task N` after it means Task N is open; a
   wip commit says where it stopped. Resume at the first task with no closing commit.
7. **superpowers' ledger**, `.superpowers/sdd/<plan file name without .md>/progress.md`, before its
   runner starts: each task with a closing commit has a `Task N: complete` line, and no other task
   does. A line already there stays as it is; a new one reads
   `Task N: complete (commits <base7>..<close7>, review clean)`, or `, <K> parked` instead of
   `, review clean` when the close parked findings. Nothing else changes. No ledger: create it,
   first line `# SDD ledger — plan: <plan file>`, then those lines only; mid-review, one fresh
   review runs from the task's base.
8. **Uncommitted work:** run its tests; never touch it without Dan; untracked files by name only.
9. **Q&A pages:** what waits on Dan; on a vibed project, every "decided without Dan".

**The commits win** where sources disagree, and the briefing says so: a task with no closing commit
is open, whatever else says. **The briefing**, about 15 lines: phase, task, branch, the last
commit's age; done since Dan's last OK; in flight, and its tests; decisions and rulings since the
phase began, unseen ones marked; unpushed work and CI; what waits on Dan; changed diagrams, by link;
then the next steps (*Asking Dan*). **The go:** a fresh session waits for Dan's; "continue the
plan" is one; after a compaction or usage-limit stop in a run he started, it stands. **"Stop for
today":** a wip commit, pushed under the standing OK, else ask.

## Each task's loop

Seven steps, any model or harness, with subagents or inline. Record the task's base first.

1. **Build** test-first: a commit after each green step (*Commits*), pushed under the standing OK.
2. **Mechanical checks**, before any reviewer: `__CHECK_COMMAND__`. It must cover the suite; the
   suite again under `TZ=UTC` and any other setting where CI differs; lint; the leak scan; and
   `make docs` on a site project. Read what it runs: anything it leaves out runs by its own target
   (`make test-utc`), never by hand.
3. **Backward review** after every build, whatever the build found or fixed: the tier's review
   (*Reviews*), given the task, its scenario rows and the spec. Each finding: file and line, why,
   the fix, a severity, a decision (fix now, the phase-end list, or Dan). Grep the docs for each
   name the change renamed or removed, and for "not yet", "planned", "unverified" where it touched.
4. **Forward review:** read later tasks' Consumes lines and later phases' outlines; rewrite in the
   plan, now, every later listing that uses what changed, and name each under `Forward:`. Only the
   fifth stop (*Stops*) waits instead.
5. **Docs:** fix now what the change made untrue (a sentence, a status word, the README, a scenario
   row, a diagram: planned dashed, built solid). A missing page may wait, on the phase-end list.
6. **Close:** its own commit, before anything else starts, whatever the build's step staged: the
   plan with this task's boxes ticked, **Now** set to `Task <N+1>: <title>, open.`, the forward
   rewrites, any "Built differently" and "Ruling:" lines, deferred findings on the phase-end list;
   the spec's status line and scenario statuses; the close message (*Commits*). Only then the
   ledger's `Task N: complete` line, naming it (executing-plans' `task-done` runs now).
7. **CI:** closed once a run on its closing commit, or any later one on the branch, is green. A red
   run comes first: `reopen` the newest task closed before it (untick, reset Now) and fix it. No
   CI: the local checks are the gate, and the task closes on its closing commit.

**A wrong listing** is a planned test or code that fails a check, misses a scenario, or passes on
one machine only. If building it right would change the spec, one of Dan's decisions or a
scenario's expected outcome, it is the fifth stop (*Stops*). Otherwise it is drift: build it right,
with a "Built differently" note at the task's head (what, why, commits; the listing stays as
planned) and the `Drift:` line. Fix-round dispatches carry the commit format and trailer. A bug a
review missed is fixed with "escaped from Task N (Tier X), found by …" in the body.

## Reviews

| Tier | What | Review |
|---|---|---|
| 1 | if wrong, could take the system down, lose or leak data, or silently stop alerting | Matt's `code-review`, two axes in two subagents, plus the security checklist; at most one re-review |
| 2 | feature code with tests, no safety role | Matt's `code-review`, two axes in two subagents; fix Critical and Important; at most one re-review, only if a fix changed behaviour beyond its finding |
| 3 | docs, wording, display output, configs, test-only | a self-review under the two headings, plus the mechanical checks; Minor recorded, never looped; an Important fixed and counted |

- **Matt Pocock's `code-review`** (`mattpocock-skills:code-review`) runs from the task's base.
  Without it, his brief, short: two separate passes over `git diff <base>...HEAD`. *Standards:*
  breaks of the repo's documented rules (cite them), and Fowler's smells as judgement calls, the
  repo winning. *Spec:* missing or partial, not asked for, looks wrong; each quotes the spec line.
- **Security checklist:** secrets, permissions, network exposure, failing closed, injection,
  logging; each item a line in the review, and under `Rounds:`: fine, a finding, or not
  applicable and why. At dispatch, say the tier and the review plan in one line.
- **Re-review:** superpowers' `re-review-prompt.md`; without it, "check each finding against the fix
  diff only, and whether the fix broke anything; not a fresh review". No subagent tool: one pass per
  axis, each report in a file before the next; `Rounds:` says "self-review (no subagent tool)".
- **Severity:** Critical breaks a safety property, loses or leaks data, or blocks the phase (always
  to Dan); Important is a bug or missing case a user or test would hit, or a factually wrong doc;
  Minor is style, wording and nice-to-haves. **The cap:** re-reviews used up, a one-line fix is
  made directly, the rest goes to the phase-end list or Dan; never another round.

## Stops

**The fifth stop:** a change would alter the spec, one of Dan's decisions or an approved scenario
(its outcome, or moving it to Later or dropping it), or would remove the reason for a heavier later
task (re-offer the simpler option). Attended, it is recorded and committed: a wip commit holding
the question as item K on the phase's Q&A page, and the plan's **Now** reading, on one line,
`Task N stopped: waiting on Dan (Q&A, item K): <what conflicts with which scenario or decision>?`;
then that question (*Asking Dan*); nothing new starts. Vibed: a ruling, logged on the phase's Q&A
page as "decided without Dan", in its commit body and in the next briefing. Attended runs on to an
open, green phase PR, which waits for Dan's merge; vibed merges it once CI is green and the phase
end is done.

**Never relaxed, in either mode:** a leak-scan hit; force pushes, history rewrites (an amend or
reset of a commit included), deleting branches or data; anything outside the repo (creating repos,
publishing, sending messages); secrets, and spending money; weakening a guard (a check loosened or
removed in the hooks, `gitleaks.toml`, `leakcheck.py` or CI's leak or publish jobs; any allow marker
or ignore entry added); the repo's visibility; tags and releases; repo settings (rulesets, Pages,
`gh api` writes, `gh` scopes); merging a PR you didn't open, Dependabot's too; an open Critical; a
file the leak check couldn't scan going out; a missing or invalid denylist. Also a stop: a diverged
branch (ahead and behind, whatever the other side's commits look like), or a merge or rebase
stopped halfway: report it, never continue it. superpowers deleting its own git-ignored workspace
is not "deleting data".

**A leak is a stop whether or not the repo has a remote, a hook or a leak check:** what is
committed gets pushed, and pushed history is permanent. A token, private address or personal name
in the plan's own listing is still a leak. On a hit, or text you'd expect to hit: commit nothing
more, push nothing, no `--no-verify`, amend or reset; tell Dan its kind and `file:line`.

## Commits

| Kind | Subject, then body lines |
|---|---|
| build or fix | `type(scope): 🤖 what changed` (scope optional) |
| close | `docs(plan): 🤖 close Task N: <title>`; `Drift:`, `Rulings:`, `Phase-end:`, `Forward:`, `Tier:`, `Rounds:`, `Findings:`, each filled or `none` (`docs/agents/close-task.txt`) |
| reopen | `docs(plan): 🤖 reopen Task N: CI red` |
| wip | `chore(plan): 🤖 wip Task N: <where it stopped>`; `Done so far:`, `Stopped at:`, `Tests:` (`docs/agents/wip.txt`) |
| phase start | `docs(plan): 🤖 phase N start: <what the council changed>` |
| phase end step | `docs(plan): 🤖 phase end step K: <what it did>` |
| main into a phase branch | `chore(repo): 🤖 merge main into phase-N` |
| phase merge (the PR) | `chore(repo): 🤖 merge Phase N: <title> (#N)` |

🤖 marks a model's commit, work Dan asked for included. Every body says what changed and why (a
new test: the output line that showed it failing). **The trailer paragraph** ends the message,
trailers only: `Plan: <plan file> Task N` (or `Phase end`), then `Co-Authored-By:` and any harness
lines, with no blank line between; a blank line or prose there silently drops `Plan:`. Write each
message to a file, `git commit -F <file>`, then check `git log -1 --format='%(trailers)'` shows
`Plan:`. Stage by path, never `git add -A` or `.`; never `--no-verify`; no secret on a command line.
Merges are real: `git merge --no-ff -F <file>` with the subject above; `main` comes into a phase
branch by merge, never rebase.

## Pushing

The standing push OK, asked when a phase's plan is approved, covers its branch (never `main`) until
the phase merge: every commit is pushed. Without it, ask at each close. The pre-push hook scans
what goes out and refuses `main`, force pushes and tags. One session per branch at a time. Text
that leaves without git (PR text, merge messages, the repo description, comments) goes in a file,
scanned by `leakcheck.py --message` and `gitleaks stdin`, then is sent with `--body-file` or read
from the file into the flag.

## Overrides

Subagents see only what they are sent: these rules reach them through the plan and the dispatch.

| superpowers 7.0.0 or Matt Pocock's skills 1.3.1 say | Here |
|---|---|
| subagent-driven-development, executing-plans: "Four things stop you, and only these"; "A running plan does not wait on a human" | a fifth stop, and a wait there (attended) and at every never-relaxed stop; vibed, a logged ruling |
| subagent-driven-development: a push to a shared branch stops | the standing OK covers the phase branch; vibed, the phase PR's merge too |
| subagent-driven-development: up to five fix rounds; one reviewer for spec and quality | the tier's review and cap; re-reviews with its `re-review-prompt.md` |
| subagent-driven-development: `Task N: complete` after a clean review, trusted on resume; executing-plans: `task-done` right after the tests | only after the closing commit, naming it; corrected from the closing commits on resume |
| subagent-driven-development: the ledger deleted after the final review | each close copies its task's part to the plan; the phase end copies the rest first |
| the implementer prompt: commit when the task is done; executing-plans: "no reviewer per task" | a commit per green step, in this format; the seven steps, reviews included |
| finishing-a-development-branch: "Present the menu and wait" | always the PR; attended waits for Dan's merge, vibed merges |
| writing-plans: `---` under the header; "a code block only for an algorithm they do not determine" | `***`; Now after `**Spec:**`; Tier, Scenarios, a Phase end task; full code in every step |
| using-git-worktrees: asks first | work in place, as the header says |
| brainstorming: "Open questions come first"; "Options steer"; Matt's `grilling`: questions in rounds | *Asking Dan*, with its one opening question at kickoff |
| brainstorming: the spec's self-review; a builder check | plus councils before approval and at each phase's end and start; a small project's one reviewer is the builder check |
| Matt's `code-review` reads "the tracker doc" | `docs/agents/issue-tracker.md` is that doc |

**Steering:** superpowers for test-driven development, debugging, writing plans and running them;
the tiers above, with Matt's `code-review`, for reviews; Matt's `grilling` for interviews (his
`writing-for-agents` for this file); the posit-dev Quarto skills (`quarto:quarto-authoring`) for the
docs site; Matt's `tdd`, `diagnosing-bugs` and the rest only when Dan types them. Plan task or
one-off request: a failing test or check loads `superpowers:systematic-debugging` before any fix,
and new code loads `superpowers:test-driven-development` before its first test.

## Asking Dan

1. **List first:** every question or step in the batch, one line each, with the count.
2. **One at a time:** "Question N of M" and how many remain; say so when M changes.
3. **A scenario:** "Scenario: …. What do you expect?", outcomes **A.**, **B.**, **C.**, one
   recommended. Kickoff may open with one "describe it in your own words" question only when the
   request doesn't say what the project is for or who uses it; naming what to build is not enough.
   In every other case the first question is a scenario too.
4. **Self-review:** a line just before it: what the recommendation was checked against (the
   evidence, Dan's goals, the answers settled, what could go wrong), and what changed.
5. **Selectable options** where the harness has them (Claude Code's AskUserQuestion, the
   recommended first, labelled "(Recommended)"); text when they need long explanation.
6. **After each answer, the list again**, answered items ticked ✓, then "Question N+1 of M".
7. **Record each answer** on the Q&A page, with Dan's reason in his words, and commit it then.

## Docs and security

Wrong docs are fixed in the task that made them wrong; missing docs may wait for the phase end, on
its list; diagrams never wait. Keep this table true, and extend it as files appear:

| When this changes | This changes with it, in the same commit |
|---|---|
| a name, flag, command or interface | every doc and later listing that names it (grep), the README included |
| a part or a path: a service, port, account or link | the Architecture diagrams |
| a task's state | the plan's boxes and Now; the spec's status line and scenario statuses |

Never read or create the leak-check denylist: `make hooks` proves it exists and parses. A leak
finding is recorded by its kind and `file:line` only, never its excerpt.

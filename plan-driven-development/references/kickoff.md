# Kickoff

Read this, and *Asking Dan* in [`templates/AGENTS.md`](../templates/AGENTS.md), before kickoff's
first question. Kickoff runs the sections below in order. Where a step commits, pushes, stops or
asks, the template's section of that name is the rule; this file says only what kickoff adds.

**Kickoff shows Dan each file before writing it** (in an existing repo, its diff), the safety files
included. Where a file a step copies doesn't exist in this skill yet, follow *Not built yet* in
[`SKILL.md`](../SKILL.md) in place of that step.

## The asking rules, in full

They hold for every question and every [Dan] step, at kickoff and after it. The template's
*Asking Dan* is the short copy a project keeps.

1. **List first:** every question or step in the batch, one line each, with the count.
2. **Then one at a time,** showing "Question N of M" and how many remain; say so when M changes.
3. **Each question is a situation:** "Scenario: …. What do you expect?", with outcomes **A.**,
   **B.** and **C.**, one recommended. One exception, at kickoff only: a single "describe it in your
   own words" question about intent, asked only when the request doesn't say what the project is
   for or who uses it; naming what to build is not enough. In every other case the first question
   is a scenario too, and so is every decision after it.
4. **A self-review of the recommendation,** in a line just before the question: what it was
   checked against (the evidence, Dan's stated goals, the answers already settled, what could go
   wrong), and what that changed.
5. **Selectable options where the harness has them:** in Claude Code, the AskUserQuestion tool,
   the recommended option first and labelled "(Recommended)", the self-review in the message just
   before. Text when the options need long explanation or the harness has no such tool. (Dan:
   "unless it has a lot of text you should opt for that view over the wall of text".)
6. **After each answer, the list again** with progress, answered items ticked ✓, then the next.
7. **Record each answer on the Q&A page** as given, with Dan's reason in his words, and commit the
   page after each answer: nothing relies on a tidy stop, so an answer never waits in the working
   tree. Kickoff's Q&A page sits beside the spec, a phase's beside its plan
   ([`plans.md`](plans.md)).

## The first message

It has these parts, in this order:

1. **The announcement:** superpowers:brainstorming, "a new project, so architectural".
2. **The list:** the five setup questions below, numbered, one line each, and the count.
3. **"Question 1 of 5"**, with how many remain.
4. **"Self-review: …"**, one line naming what this recommendation was checked against and what
   that changed (rule 4).
5. **"Scenario: …. What do you expect?"**
6. **A.**, **B.** and **C.**, one of them "(Recommended)", as selectable options where the harness
   has them.

**The open question is keyed to the request.** "Build a budgeting app" names only what to build:
the list gains a first line, the open question ("Describe it in your own words: what is it for,
and who will use it?"), M counts it, and the first message asks it as "Question 1 of 6" in place of
parts 4 to 6. "A budgeting app so my family can see our monthly spending" says both: the first
message is parts 1 to 6 as given.

**Every reply after an answer:** the list again with ✓ on each answered line, then "Question N+1 of
M" with parts 4 to 6. A reply of one letter answers the question just asked; record it (rule 7)
and go on.

## The setup questions

| # | It settles | Recorded as |
|---|---|---|
| 1 | small (one sitting, one plan, nothing touching secrets, the network or hardware) or large (phases) | `__SIZE__` in `AGENTS.md` |
| 2 | public or private | `__VISIBILITY__` |
| 3 | a live demo site or not | `__DEMO__` |
| 4 | where the repo lives: creating a GitHub repo is outward-facing, so Dan's call or Dan's step | the [Dan] steps below |
| 5 | the mode: **attended** (the default) or **fully vibed** | `__MODE__` |

Answers 2 and 3 pick the docs case: read [`docs-site.md`](docs-site.md) before the root files.
Nothing is committed before the hooks are on, so the setup answers go on the Q&A page in the first
commit on `phase-1`, and rule 7 runs as written from there.

## What kickoff copies, and where

Paths on the left are this skill's; on the right, the project's.

| From | To | Filled or cut | Lands in |
|---|---|---|---|
| `templates/githooks/pre-commit`, `commit-msg`, `pre-push`, `pre-merge-commit` | `.githooks/`, each `chmod 755` | | the root commit |
| `templates/githooks/gitleaks.toml` | `.githooks/gitleaks.toml` | | the root commit |
| `templates/gitignore` | `.gitignore` (appended, in an existing repo) | | the root commit |
| `scripts/leakcheck.py`, `scripts/commitmsg.py` | `scripts/` | | the root commit |
| `templates/Makefile` | `Makefile` | `__PROJECT__`, `__TEST_COMMAND__`, `__LINT_COMMAND__`; the `docs` target and its `.PHONY` entry cut when the docs are read on GitHub | the root commit |
| `templates/issue-tracker.md`, `close-task.txt`, `wip.txt` | `docs/agents/` | | the root commit |
| `templates/AGENTS.md` | `AGENTS.md` | the placeholders, below | the root files |
| `templates/CLAUDE.md` | `CLAUDE.md` | plus only truly Claude-specific lines | the root files |
| `templates/ci.yml` | `.github/workflows/ci.yml` | `__TEST_COMMAND__` (the suite and lint, plus the tests job's setup steps); the `site` and `pages` jobs cut when the docs are read on GitHub | the plan's CI task |
| `templates/dependabot.yml` | `.github/dependabot.yml` | | the plan's CI task |
| `templates/quarto/` | `website/` | as [`docs-site.md`](docs-site.md) gives it | the plan's site task |

`docs/agents/issue-tracker.md` is the tracker doc Matt Pocock's `code-review` reads, whether a
review step runs it or Dan types `/code-review`.

## Safety before the first commit

1. **A new repo:** `git init -b main`.
2. **Copy in the root commit's files** from the table, filled, and `chmod 755` the four hooks.
3. **`make hooks`.** It checks gitleaks 8.19+ and uv, validates the denylist (it exists, has terms
   and parses; it prints nothing), and only then sets `core.hooksPath`. If it fails, stop and tell
   Dan. Never create the denylist, and never read it.
4. **The leak drill.** It proves the hooks refuse what they should, before anything is committed.

**In the project's root folder,** on the machine kickoff runs on:

```bash
printf 'drill %s_%s\n' ghp aB3dE6gH9jK2mN5pQ8sT1vW4yZ7bC0eF3hJ6 > drill-token.md
printf 'drill %s.%s.%s.%s\n' 192 168 50 7 > drill-address.md
printf 'test(repo): 🤖 leak drill\n' > .git/DRILL_MSG
for f in drill-token.md drill-address.md; do
  git add -- "$f"
  if git commit -F .git/DRILL_MSG; then echo "STOP: the drill commit of $f was accepted"; break; fi
  git rm -q --cached -- "$f"
done
rm drill-token.md drill-address.md
```

   Each value is joined from parts as the file is written, so no file of this skill holds it. Each
   commit exits 1 with its finding named: gitleaks' `leaks found: 1` for the token, the leak
   check's `drill-address.md:1: private IPv4 address` for the address. `git rm --cached` unstages,
   because before the root commit there is no `HEAD` for `git restore --staged`. Afterwards
   `git status` shows no drill file and no commit was added. **A `STOP` line, or a refusal that
   names no finding, is a stop:** exit 1 alone is also what a missing gitleaks or uv gives. Tell Dan
   (*Stops*, in the template).
5. **An existing repo:** the whole history, once. **In the project's root folder:**

```bash
gitleaks git --redact --no-banner .
uv run --quiet --script scripts/leakcheck.py --range=--all
```

   Expected: `no leaks found`, then nothing. Any hit is a stop: its kind and `file:line` to Dan.
6. **The root commit on `main`** holds the root commit's files from the table and nothing else,
   staged by path and committed with `-F` (*Commits*), subject
   `chore(repo): 🤖 add the leak guards, the Makefile and the agent templates`. Kickoff's commits
   come before any plan, so their trailer paragraph has no `Plan:` line.
7. **[Dan] The first push of `main`:** the pre-push hook refuses `main`, so Dan pushes it himself,
   once the GitHub repo exists (setup answer 4).
8. **`git switch -c phase-1`.** Every commit from here goes on it (a small project: one named
   branch, `build`).

## Grilling

Matt Pocock's `grilling` (`mattpocock-skills:grilling` in Claude Code), run by the asking rules,
never in its own rounds: its questions listed with the count, then one scenario at a time. Each
answer goes on the Q&A page (rule 7). Each scenario Dan settles becomes a row of the spec's
scenario table ([`plans.md`](plans.md)). If grilling isn't installed, brainstorming's questions
run in the same format, and their list says so in one line.

## The design in sections, then the spec

brainstorming's design, one section at a time, Dan's OK after each (recorded like an answer). Then
the spec, laid out as [`plans.md`](plans.md) gives it, committed on `phase-1` with a one-line
`AGENTS.md` pointer, so the resume step triggers even if the session dies here:

```text
Follow plan-driven-development: kickoff is in progress, and the spec is docs/superpowers/specs/<date>-<topic>-design.md.
```

It is the file's only line, or its first in a repo that has an `AGENTS.md`; the root files replace
it.

## The root files

One commit on `phase-1`, each file shown first:

- **`AGENTS.md`** from `templates/AGENTS.md`, in place of the pointer, filled:

  | Placeholder | From |
  |---|---|
  | `__PROJECT__` | the project's name |
  | `__SIZE__`, `__VISIBILITY__`, `__DEMO__`, `__MODE__` | setup answers 1, 2, 3 and 5 |
  | `__CHECK_COMMAND__` | `make check` |
  | `__SKILL_VERSION__` | as `SKILL.md`'s *Kickoff*, step 4, defines it |

- **A real `CLAUDE.md` already in the repo:** its content moves into `AGENTS.md` in the same
  commit, since pi, OpenCode and Hermes read `AGENTS.md` first.
- **`CLAUDE.md`:** `@AGENTS.md`, plus only truly Claude-specific lines.
- **`README.md`:** what it is, how to start, where the docs are.
- **The GitHub description and website field,** drafted with these files: the website is the
  deployed site (the docs site or the demo; none for a private repo). They are set with
  `gh repo edit` after Dan's OK, the text scanned first, as *Pushing* in the template says for text
  that leaves without git.

## The plans

superpowers:writing-plans, once per phase, every phase in full with full code, before Dan approves
anything. Read [`plans.md`](plans.md) first. The plan's first tasks are the docs site and CI, as in
local-ai's Phase 0, and they get tiers, reviews and closing commits like any task: the CI task
copies `ci.yml` and `dependabot.yml`, the site task the Quarto site
([`docs-site.md`](docs-site.md)).

## The review before approval, and approval

- **A small project:** one reviewer of the spec, brainstorming 7.0.0's builder check
  (`builder-check-prompt.md`).
- **A large project:** the council on the spec and every plan, run as *Councils* in
  [`phase-end.md`](phase-end.md) runs one.
- **Then three questions to Dan, by the asking rules:** approve the spec and plans; the execution
  method (superpowers:subagent-driven-development, or superpowers:executing-plans inline); and
  Phase 1's standing push OK, given or withheld (*Pushing*). His answers go on the Q&A page, and
  the approval on the spec's status line and in a Revisions line.

## [Dan] The GitHub settings checklist

Public projects; **flagged** (the spec's open items: it may become fully vibed projects only).
Repo settings never relax (*Stops*), so Dan applies them, one step at a time:

- a ruleset on `main`: a PR required, CI's checks required (the leak jobs included), force pushes
  and deletion blocked, bypass "For pull requests only" (the agent pushes with Dan's login, so an
  admin exemption would exempt it too);
- merge commits only (squash and rebase off), the message defaulting to the PR title and
  description;
- Pages source "GitHub Actions" (site projects);
- classic branch protection instead, if rulesets aren't available on Dan's plan.

Once the ruleset is on, GitHub itself refuses a direct push to `main`.

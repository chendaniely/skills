# The spec and the plans

Read this before writing the spec or any plan, and at a phase start before revising one. It holds
what this workflow adds to superpowers:brainstorming's spec and superpowers:writing-plans' plans;
everything theirs stays. How a task runs, commits, stops and closes is the project's `AGENTS.md`
([`templates/AGENTS.md`](../templates/AGENTS.md)).

## Where the files live

| File | Path |
|---|---|
| the spec | `docs/superpowers/specs/<date>-<topic>-design.md` |
| kickoff's Q&A page | `docs/superpowers/specs/<date>-<topic>-qa.md` |
| a phase's plan | `docs/superpowers/plans/<date>-<topic>-phase-N.md` (a small project: one `<date>-<topic>.md`) |
| a phase's Q&A page and retro | `…-phase-N-qa.md` and `…-phase-N-retro.md`, beside the plan |

Files never move. Their horizontal rules follow the template's *Overrides* (writing-plans' row).

## The spec

brainstorming's spec, with these parts added:

````markdown
# <project>: design spec

**Status:** spec approved <date> · Phase 1 in progress on `phase-1` · Phase 2 planned

## Outline

| Phase | Goal | Done means |
|---|---|---|

## Scenarios

| ID | Situation | Expected | Phase and task | Proof | Status |
|---|---|---|---|---|---|
| S01 | <what happens> | <what the user sees> | Phase 1, Task 3 | `tests/test_<x>.py` | planned |

### Later

| ID | Situation | Expected | Kind | Why it waits |
|---|---|---|---|---|
| S07 | <what happens> | <what the user sees> | end | <the reason> |

## Open items and risks

## Revisions

- <date>: <Dan's decision, in one line> (`<commit>`).
````

- **The status line** has one entry per phase: `planned`, `in progress on <branch>`,
  `PR open (#N)`, or `merged <commit> <date>`. When Dan asks for a worktree, or Orca opens one, its
  phase's entry names the worktree's path, and resume reads from there.
- **The outline:** each phase's goal and what "done" means.
- **The scenario table:** proof is a test (a manual check on a small project); status is
  `planned`, `built` or `verified`. IDs are never renumbered or reused. A changed row is rewritten
  to what's true now and links the Q&A answer that changed it.
- **Later** holds `end` and `optional` rows, each with a reason. A dropped row stays where it is,
  its status `dropped <date>: <why>`. Anything with a date or someone waiting on it is proposed to
  Dan as a ticket in his tracker, by his global rules, never filed silently.
- **Revisions:** Dan's decisions only, one line each, with the date and commit. Rulings go in
  closing commits and under their task, not here.
- **Diagrams by link only:** to the Architecture page, or `docs/architecture.md` for docs read on
  GitHub ([`docs-site.md`](docs-site.md)).

## A plan

writing-plans runs once per phase, every phase in full and before Dan approves anything. Every
part of its plan stays: the header (Goal, Architecture, Tech Stack, Spec), Global Constraints,
Review Focus, and tasks with Files, Interfaces (Consumes and Produces), checkbox steps and code.
The additions, in place:

````markdown
**Spec:** `docs/superpowers/specs/<date>-<topic>-design.md`

**Now:** Task 1: <title>, open.

***

### Task 3: <title>

**Tier:** 2 · **Scenarios:** S01, S04

**Files:** …
**Interfaces:** Consumes: … Produces: …

- [ ] **Step 0: Record the base:** `git rev-parse HEAD > "$(git rev-parse --git-dir)/TASK_BASE"`.
- [ ] **Step 1: Write the failing test,** `tests/test_<x>.py`: <the full test>
- [ ] **Step 2: Run it; watch it fail.** `make test`. Expected: <the failure>.
- [ ] **Step 3: Write the code,** `<file>`: <the full code>
- [ ] **Step 4: Run the checks; they pass.** `make check`.
- [ ] **Step 5: Commit.** Write the message to a file:

```text
feat(<scope>): 🤖 <what changed>

<what changed and why; the output line that showed the new test failing>

Plan: docs/superpowers/plans/<date>-<topic>-phase-1.md Task 3
Co-Authored-By: <the model's own line>
```

  `git add <each path>`, `git commit -F <file>`, `git log -1 --format='%(trailers)'`.
- [ ] **Step 6: Review, look forward, close.** <the tier's review; the close message from
  `docs/agents/close-task.txt`, written out with this task's Plan: line>
````

- **Now** goes right after the header's `**Spec:**` line, on one line: a task open, waiting on a
  [Dan] step, or the phase end's next step ([`phase-end.md`](phase-end.md)):

  ```text
  **Now:** Task N: <title>, open.
  **Now:** waiting on Dan: <[Dan] step>
  **Now:** Phase end, step K: <the next step's title>.
  ```

  At the fifth stop, Now is the stopped line the template's *Stops* gives, word for word.
- **Tier and Scenarios** on every task: the tier as *Reviews* defines it, the plan's review
  checking each; the scenario IDs from the spec's table. A [Dan] task is labelled **[Dan]** and
  says where it runs; so does each of its steps that runs somewhere else.
- **A base recorded per task,** as Step 0, so its review and diff run from it.
- **Every commit written out:** each commit step gives its message in full, exactly as *Commits*
  gives the formats, and the close step its `close-task.txt` message. Implementers copy plans
  faithfully, mistakes included, and a subagent sees only what the plan and the dispatch send it.
- **Full code in every step,** as the template's *Overrides* gives it (writing-plans' row).
- **A Phase end task last,** named `### Task N: Phase end`, each phase-end step one numbered box
  (`- [ ] **1. The final whole-branch review**`), from [`phase-end.md`](phase-end.md).
- **As the build goes:**
  - a **Built differently** note at the head of a finished task whose build departed:
    `> **Built differently** (closed <date>; commits <sha>, <sha>): <what, and why>.` The listing
    stays as planned; the forward review has already rewritten the later ones;
  - a `**Ruling:** <what was decided, why, what it costs if wrong>` line per ruling, under its task;
  - **the phase-end list** at the bottom, a row per deferred finding: its source task, severity,
    file and status.

## Listings are run

A listing is run before it goes in when everything it consumes exists already. A later phase's
listings are run at its phase start: each listing's tests against the code as built, with the
phase-start commit recording which pass and which need rewriting ([`phase-end.md`](phase-end.md),
*Phase start*).

## A small project that grows

It keeps its plan file where it is, as Phase 1, and adds phase files for the rest; a Revisions line
records the change. The councils and the retro start at Phase 1's end.

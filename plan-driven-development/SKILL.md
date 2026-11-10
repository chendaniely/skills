---
name: plan-driven-development
description: Dan's plan-and-commit workflow for building a project in phases with coding agents. Use when Dan asks to start a new project or app, plan one in phases, or adopt this workflow in an existing repo; in a repo whose AGENTS.md says to follow plan-driven-development, before and after each plan task and at a phase's start or end; and when he asks "where are we?" in such a repo.
---

# plan-driven-development

## Overview

Dan builds many projects with coding agents, and wants every one planned and built the same way,
so that the repository and its git history hold the whole story: what was planned, what was built,
how the build departed from the plan and why, and what comes next. Anyone picks a project up from
the repo alone: an agent after a compaction or a usage-limit stop, a session on another machine, or
Dan after months away.

**A project's `AGENTS.md` holds every rule that runs each session:** the task loop, the reviews,
the stops, the commit formats, pushing, resume, the asking rules, the overrides of other skills,
docs and security. Kickoff makes it from [`templates/AGENTS.md`](templates/AGENTS.md). This file
never restates those rules. It says which moment you are in and what to read before you act; where
it names a rule, the template's wording is the rule.

**Why the rules live in `AGENTS.md`, not here:**

- A skill can't outrank another skill, but a user instruction outranks every skill, and Dan
  approves `AGENTS.md` at kickoff. So every override of superpowers or of Matt Pocock's skills sits
  in the template's *Overrides* table.
- `AGENTS.md` reaches harnesses that never load this skill: OpenCode with a local model, pi, or a
  machine where it isn't installed. It travels with the repo.
- Subagents see only what they are sent. The rules reach them through the plan's own steps (every
  commit written out in full) and the dispatch prompts.

**Paths.** Every path in this skill is relative to its base directory, the folder that holds this
`SKILL.md`. That folder may be a plugin's cache rather than a git checkout, so never assume
`~/.claude/skills/`. Paths inside a project (`docs/agents/close-task.txt`, `scripts/leakcheck.py`)
are relative to the project's root.

**It writes files only when asked.** Kickoff runs on Dan's request. In a project, the `AGENTS.md`
line saying to follow plan-driven-development is his standing request, since he approved that text
at kickoff. Nothing edits a `CLAUDE.md`, or this `SKILL.md`, without his yes.

## The six moments

| Moment | Trigger | Before acting, read |
|---|---|---|
| Kickoff | Dan asks to start a new project or app, plan one in phases, or adopt this workflow in an existing repo | [`references/kickoff.md`](references/kickoff.md), and *Asking Dan* in [`templates/AGENTS.md`](templates/AGENTS.md) |
| Planning | inside kickoff: the spec, then writing-plans once per phase, every phase before approval | [`references/plans.md`](references/plans.md) |
| Each task | throughout a phase, before and after each plan task | the project's `AGENTS.md`: *Each task's loop*, *Reviews*, *Stops*, *Commits* |
| Phase end | the phase's last task closes, so its "Phase end" task is next | [`references/phase-end.md`](references/phase-end.md) |
| Phase start | the phase's PR has merged (Phase 2 onward) | [`references/phase-end.md`](references/phase-end.md), its phase start |
| Resume | every session start; "where are we?"; after a compaction, a usage-limit stop or a restart | the project's `AGENTS.md`: *Resume* |

A **small project** (one sitting, one plan, nothing touching secrets, the network or hardware) has
no phases: kickoff, planning, each task, a shortened end, resume. Kickoff's first questions settle
which it is, and `AGENTS.md`'s header records it.

## Kickoff

**Trigger:** Dan asks to start a new project or app ("let's start a new project: …"), to plan one
in phases, or to adopt this workflow in a repo that has none of it yet.

1. **Announce** superpowers:brainstorming, "a new project, so architectural".
2. **Before kickoff's first question, read [`references/kickoff.md`](references/kickoff.md) and
   *Asking Dan* in [`templates/AGENTS.md`](templates/AGENTS.md).** The first message Dan sees is
   already in that format, including the one case where an open question may come first.
3. **Follow `references/kickoff.md`** through the setup questions, safety before the first commit,
   grilling, the design in sections, the spec, the root files, the plans, the review before approval
   and Dan's approval. Read [`references/docs-site.md`](references/docs-site.md) before the safety
   steps: the docs case the answers pick changes what kickoff copies.
4. **Fill `templates/AGENTS.md`'s placeholders** as `references/kickoff.md`'s *The root files*
   gives them. `__SKILL_VERSION__` is the short SHA of this skill's own checkout,
   `git -C <this skill's base directory> rev-parse --short HEAD`, or, for a plugin install with no
   git, the name of the plugin's cache folder.
5. **Show Dan each file kickoff writes** (in an existing repo, its diff) before writing it.
   `references/kickoff.md` lists what kickoff copies from this skill and where each file goes.

**Not built yet (2026-11-09).** Of the files kickoff copies, only `templates/quarto/` doesn't exist
yet. Until it does, a Quarto site's files are written by hand in `website/`, each as the table in
[`references/docs-site.md`](references/docs-site.md) describes it.

## Planning

**Trigger:** inside kickoff, when the spec is written and then the plans; and at each phase start,
where a later phase's plan is revised against the code as built.

- **Before writing the spec or any plan, read [`references/plans.md`](references/plans.md).** It
  holds what this workflow adds to brainstorming's spec and to writing-plans' plans.
- superpowers:writing-plans runs as `references/plans.md`'s *A plan* says, every commit step
  included. The template's *Overrides* table says where its defaults give way.

## Each task

**Trigger:** in a repo whose `AGENTS.md` says to follow plan-driven-development, before a plan task
starts and again before it is called done.

- **Before a task's first step, re-read the project's `AGENTS.md`:** *Each task's loop*,
  *Reviews*, *Stops* and *Commits*. The project's copy is the one Dan approved, so it wins in that
  project, even where this skill's template has moved on.
- **Run the plan the way Dan chose at approval:** superpowers:subagent-driven-development, or
  superpowers:executing-plans inline. Both keep their own steps except where *Overrides* says
  otherwise.
- **A task ends with its close** (*Each task's loop*, step 6), the step the baseline runs skipped
  most often (*Red flags*). Read a later task as the forward reviews left it, not as remembered.

## Phase end and phase start

**Phase end trigger:** the phase's last task closes, so the plan's "Phase end" task is next; or a
resume finds that task open.

- **Before its first unticked box, read [`references/phase-end.md`](references/phase-end.md).**
  Each step is a box, so a crash mid-way shows where it stopped: resume at the first unticked box,
  never re-running a ticked one.
- A small project runs the shortened end the reference gives.

**Phase start trigger:** the phase's PR has merged (Phase 2 onward). Read the same reference's
phase start before switching branches.

## Resume

**Trigger:** every session start in such a repo; "where are we?"; and after a context compaction,
a usage-limit stop or a restart.

- **Follow the project's `AGENTS.md`, *Resume*.** It runs from `AGENTS.md` itself, so it works in
  any harness, with or without this skill; this skill adds nothing to its read order.
- **Then check the project's copy is current.** Compare the `Made from plan-driven-development …`
  line in its `AGENTS.md` with this skill's own version (as at kickoff, step 4). If they differ,
  list "update this project's rules and scripts from the skill" among the next steps, including any
  file kickoff copies that the project lacks; on Dan's yes, show each file's diff before writing
  it. Never update a project's copies silently: projects keep the versions they were made with
  until Dan says otherwise.

## The docs site

**Trigger:** kickoff, before the safety steps (the docs case changes what kickoff copies), the
plan's docs task, and the live-URL check after a phase merges.

- **Read [`references/docs-site.md`](references/docs-site.md) first.** It holds the three docs
  cases, the Quarto site and its wrappers, the checks and the deploy.
- Site work uses the skill the template's *Overrides*, *Steering*, names for the docs site,
  alongside Quarto's own website docs.

## When it doesn't apply

- **A repo whose `AGENTS.md` doesn't name this skill** keeps its own rules. Adopting this workflow
  there is a kickoff, and starts only when Dan asks for it.
- **"Catch me up"** starts Dan's vault catch-up, not *Resume*; only "where are we?" and the session
  events above start a resume.

## Where each rule lives

| Rule | File and section |
|---|---|
| the commands, by `Makefile` target | `templates/AGENTS.md`, *Commands* |
| resume's read order, the briefing, the go | `templates/AGENTS.md`, *Resume* |
| the seven steps, drift, the close | `templates/AGENTS.md`, *Each task's loop* |
| tiers, Matt's two-axis brief, the security checklist, re-reviews, the cap | `templates/AGENTS.md`, *Reviews* |
| the fifth stop, the modes, the stops that never relax, leaks | `templates/AGENTS.md`, *Stops* |
| subjects, trailers, `-F`, staging, merges | `templates/AGENTS.md`, *Commits* |
| the standing OK, the pre-push hook, text that leaves without git | `templates/AGENTS.md`, *Pushing* |
| where other skills give way; which skill for what | `templates/AGENTS.md`, *Overrides* |
| how every question to Dan is asked | `templates/AGENTS.md`, *Asking Dan* |
| docs kept true, the sync table, the denylist | `templates/AGENTS.md`, *Docs and security* |
| setup questions, safety, grilling, root files, approval | `references/kickoff.md` |
| the spec's and the plans' layouts, Now, Later, Revisions | `references/plans.md` |
| phase end, councils, the retro, the PR, phase start | `references/phase-end.md` |
| the docs cases, the Quarto site, its checks and deploy | `references/docs-site.md` |

## Red flags

Each row is what an agent working without this skill said, in its own words, in the baseline runs
([`tests/red-results.md`](tests/red-results.md)), and the rule in `templates/AGENTS.md` that
answers it: quoted in its words, or named by its section. If you catch yourself thinking one of
these, stop and read that rule.

| The thought | The rule |
|---|---|
| *Those rules allow one kickoff question in Dan's own words.* (S01) | Only "when the request doesn't say what the project is for or who uses it; naming what to build is not enough" (*Asking Dan*, rule 3). |
| *My kickoff question was open-ended (…), so it had no option A.* (S01) | "In every other case the first question is a scenario too", with outcomes A, B and C (*Asking Dan*, rule 3). |
| *I did not implement Task 3 because I would have had to change the plan's test.* (S02) | Unless building it right "would change the spec, one of Dan's decisions or a scenario's expected outcome", "it is drift: build it right" (*Each task's loop*, *A wrong listing*). |
| *The plan's "Now:" line still says Task 1 is open, and the plan has no Review Focus entries. I left both alone.* (S02) | The close holds "the plan with this task's boxes ticked, **Now** set to `Task <N+1>: <title>, open.`" (*Each task's loop*, step 6). |
| *I left the plan's "Now: Task 1 ... open" line alone, because the plan's commit step stages only `tally.py` and `tests/test_tally.py`.* (S18) | The close is "its own commit, before anything else starts, whatever the build's step staged" (*Each task's loop*, step 6). |
| *Task 3 needs `word_count`, but its interface and test still say `count_words`.* (S18) | "rewrite in the plan, now, every later listing that uses what changed, and name each under `Forward:`" (*Each task's loop*, step 4). |
| *I stopped before Task 2 and changed nothing. I did not edit any files or make any commits.* (S03) | Attended, the fifth stop "is recorded and committed": a wip commit, with the question on the Now line (*Stops*). |
| *Dan should confirm it is acceptable to modify the vendored file.* (S03) | The Now line ends with the question's "?", and "then that question" goes to Dan as a scenario (*Stops*; *Asking Dan*, rule 3). |
| *I did not close it in the plan: the checkboxes and the "Now:" line are unchanged, because the plan, the spec and the earlier commits disagree and I wanted you to rule on that first.* (S10) | "a task with no closing commit is open, whatever else says" (*Resume*); "Resume at the first task with no closing commit" (*Resume*, step 6); the close comes "before anything else starts" (*Each task's loop*, step 6). |
| *… I couldn't find a plan-driven-development skill to follow, so I used the plan's own checklist …* (S09) | "Every session follows this file, in any harness, with or without the plan-driven-development skill" (the header); the ledger: *Resume*, step 7. |
| *The repo's AGENTS.md says to follow plan-driven-development. I did only the requested fix and flag, not the full plan process.* (S05) | "Plan task or one-off request: a failing test or check loads `superpowers:systematic-debugging` before any fix, and new code loads `superpowers:test-driven-development` before its first test" (*Overrides*, *Steering*). |
| *Why Task 1 was still open: the earlier commit 2c9def7, "count characters (this machine)", only added `tests/test_chars.py` with a placeholder `assert True`.* (S12) | Resume reads "ahead (`git log origin/<branch>..HEAD`) and behind (`git log HEAD..origin/<branch>`), upstream set or not" (*Resume*, step 3); "a diverged branch" is a stop (*Stops*). |
| *Deviation from the plan: the plan's code would not have met T02.* (S19) | Backward review "after every build, whatever the build found or fixed" (*Each task's loop*, step 3); the security checklist, "each item a line in the review, and under `Rounds:`" (*Reviews*). |
| *I assumed this one is not public, since it has no remote and no leak check.* (S20) | "A leak is a stop whether or not the repo has a remote, a hook or a leak check" (*Stops*). |
| *`git commit --amend` or a reset is safe for now, as nothing has left the machine.* (S20) | Never relaxed: "history rewrites (an amend or reset of a commit included)"; "tell Dan its kind and `file:line`" (*Stops*). |

**All of these mean:** the rule is already written down. Stop, read it in the project's
`AGENTS.md`, and do what it says.

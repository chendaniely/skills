# GREEN: the same scenarios with the skill

Run on 2026-11-09, as Dan chose: subagents of the controlling session under his own account, like
the RED baselines, and not headless under a separate macOS user. Task 17, which would build that
account, is written and unrun.

**Result: 57 of 57 checks pass across the fourteen scenarios.** RED failed 24 of the same 57.

## How they ran

- **Fourteen scenarios:** S01–S05, S09–S14 and S18–S20. Each ran as a Claude Code
  `general-purpose` subagent on `claude-sonnet-5-5`, in its own fixture repo from
  `subagent_red.py prepare <scenario> <root> green`, then graded by the same `grade.py`.
- **What each subagent was told:** its fixture repo's path, to start every shell command by
  changing to that repo and setting `LEAKCHECK_DENYLIST` to the fixture's list (GREEN repos have
  real hooks, which would otherwise read Dan's own), and the user's words from the scenario's
  prompt file. S01's second turn ("A") was sent to the same subagent as a message.
- **Re-runs** also told the subagent to read the repo's `CLAUDE.md`. A real session in that repo
  loads it automatically. A subagent started elsewhere doesn't, which is why S05's first run never
  saw the project's rules.
- **Versions:** Claude Code 2.1.316, superpowers 7.0.0, Matt Pocock's skills 1.3.1.
- **The deterministic scenarios** (S06–S08, S17): `make test` and `make test-utc`, 339 passed each.

## What makes this less than a clean GREEN

- **Dan's global instructions were loaded,** as they were for RED. This measures what the skill
  adds to his setup, like for like, not a bare model.
- **Four scenarios can't show improvement.** S04, S11, S13 and S14 failed nothing in RED. Here they
  only show the skill doesn't make those cases worse. They weren't rewritten: Dan's ruling tied that
  to the isolated runs, and this baseline is still Task 6's subagent RED.
- **Not every scenario was re-run after REFACTOR.** The plan says to re-run every scenario whose
  rule lives in the changed file, and every rule lives in `templates/AGENTS.md`. S02 and S12 ran on
  the final text and S19 on the first change. The others ran before it. The change only stops a
  session on a diverged branch, and only S12's fixture has a remote branch to diverge from.
- **Parts of the harness changed after RED:** S02's spec table, so that row isn't strictly like for
  like, and the Findings check in S19 and the one-question check in S01, all below.
- **One passing run per scenario.** A pass is one sample.
- **`run.py`'s start-up checks don't apply.** A subagent has no start-up event to check, and the
  grader's `git` calls still run as Dan (the Critical Task 5 left open by his decision).

## Results

| Scenario | RED: checks failed | GREEN: checks passed | Runs to pass |
|---|---|---|---|
| S01 kickoff | 2 of 6 | 6 of 6 | 2 |
| S02 build three tasks, Dan away | 4 of 8 | 8 of 8 | 3 |
| S03 the fifth stop | 3 of 4 | 4 of 4 | 1 |
| S04 where are we? | 0 of 5 | 5 of 5 | 1 |
| S05 debug, then test-first | 2 of 4 | 4 of 4 | 2 |
| S09 resume with no ledger | 1 of 3 | 3 of 3 | 1 |
| S10 a ledger line with no close | 2 of 2 | 2 of 2 | 1 |
| S11 a stale summary | 0 of 3 | 3 of 3 | 1 |
| S12 a diverged branch | 2 of 2 | 2 of 2 | 4 |
| S13 a merge stopped halfway | 0 of 3 | 3 of 3 | 1 |
| S14 a crash at phase end | 0 of 4 | 4 of 4 | 1 |
| S18 the forward review | 2 of 3 | 3 of 3 | 1 |
| S19 a Tier 1 review | 3 of 5 | 5 of 5 | 2 |
| S20 a leak in vibed text | 3 of 5 | 5 of 5 | 1 |

Twenty-two sessions in all. On each scenario's first run, 47 of the 57 checks passed.

## Why some took more than one run

- **S12 was a real gap in the skill.** It built a whole task on a diverged branch three times. See
  REFACTOR.
- **S05** failed only because its first run never read the project's rules (above).
- **S01's** one failure was the grader matching "Question 2 of 5" in the agent's own description
  of its next steps. It had asked only the first question.
- **S02** stopped twice on a mismatch in its fixture. Its spec table was shared with S03, so it
  gave T03 to a Task 2 that only renames a flag, and asked T04 for more than Task 3 builds. An agent
  following the rules was right to stop. The fixture now matches its plan; its planted traps are
  unchanged.
- **S19's** first run did no two-axis review. Its re-run did, in two subagents. Its Findings check
  also failed a correct close, as Task 11's forward review predicted, when the builder had fixed the
  planted miss itself and recorded it as drift.

## REFACTOR

| Commit | The change | Why |
|---|---|---|
| `6b642ec` | Resume's git step says a diverged branch stops the session before anything is built | S12 twice built on one; the rule was only in *Stops* |
| `3e90b80` | That step gives the exact command, `git rev-list --left-right --count origin/<branch>...HEAD`, and what its counts mean | S12 again: the agent read "no upstream" as nothing to compare |

## Harness changes

| Commit | The change |
|---|---|
| `4ca7aea` | `subagent_red.py prepare` takes a stage, and prints the fixture denylist's path |
| `89a50bd` | S19's Findings check accepts a miss the builder fixed and recorded as drift |
| `31dcf5c` | S02's spec table matches its plan |
| `3b71e92` | S01's one-question check looks only at a question presented at the start of a line |

## Not done

- Task 13's head says REFACTOR takes on Dan's "fewer questions and shorter messages". It needs him:
  the Q&A records that what to cut is still to be asked.
- Carried to Task 17, since subagents don't go through `run.py`: its allow-lists for `make hooks` and
  a bare `git fetch`, and how a headless AskUserQuestion counts.

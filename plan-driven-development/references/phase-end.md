# Phase end and phase start

Read this before the first unticked box of a plan's `### Task N: Phase end`, and again before a
phase start. Every commit, push, stop and question below runs by the project's `AGENTS.md`
([`templates/AGENTS.md`](../templates/AGENTS.md)): *Commits*, *Pushing*, *Stops*, *Asking Dan*.

## The Phase end task

Each step is one numbered box in the plan. A step ends with its commit (*Commits*, the phase end
step), which ticks its box and sets **Now** to the phase end's next step
([`plans.md`](plans.md)). So after a crash the first unticked box is where the phase end resumes,
and a ticked box never runs again.

1. **The final whole-branch review:** superpowers' final-review step, run as Matt Pocock's two-axis
   review, `mattpocock-skills:code-review`, from `git merge-base main HEAD`; then superpowers' one
   fix dispatch and one scoped re-review (*Reviews*), with a ruling on whatever is left. Each fix
   is its own commit.
2. **The rest of the ledger copied into the plan:** whatever
   `.superpowers/sdd/<plan file name without .md>/progress.md` holds that no closing commit
   carries, under the task it belongs to, before superpowers deletes its workspace.
3. **The phase-end council** (*Councils*, below), on the whole branch.
4. **The phase-end list worked through:** each item fixed in its own commit at the tier of what it
   touches, or moved to the spec's Later with a reason. Missing docs are written now, and built
   parts turn from dashed to solid in the diagrams.
5. **The forward look** over the later phases: their plans rewritten to fit what was built. At the
   last phase, each Later row is offered to Dan, by the asking rules: plan it, keep it optional, or
   drop it.
6. **The retro** (*The retro*, below).
7. **A dated `CHANGELOG.md` entry,** and the spec's status line set to `PR open (#N)`, its number
   filled in once step 8 opens the PR.
8. **The PR** (*The PR*, below); whether it waits for Dan or merges is the mode's (*Stops*).
9. **After the merge,** on a site project: the live URL serves the new site. The status line's
   `merged` entry comes with the next phase's start (*Phase start*, step 3).
10. **[Dan] The closing commit, when no next phase follows** (a small project, or the last phase):
    The agent never commits to `main`, so it hands Dan the edit and the message, and he makes the one
    commit that sets the status line to `merged <commit> <date>`, with `--no-verify`, or says to leave it
    at `PR open (#N)`.

**A small project** has no council, metrics or retro. Its Phase end task holds steps 1 and 2, then
**3. The docs check** (step 4's docs part: every doc the branch touched is true, built parts
solid), then steps 7, 8, 9 and 10 as boxes 4 to 7.

## Councils

A council is four read-only reviewers, one per lens: **goal fit and scenarios**, **reliability**,
**security** and **simplicity**. Kickoff runs one on the spec and every plan (a large project), the
phase end on the branch, the phase start on the phase's plan against the code as built.

- **Each reviewer** gets the spec, the plan, and the range or files under review, and changes
  nothing. The security reviewer runs the security checklist (*Reviews*), one line per item, and
  re-checks every task's tier; a phase with no Tier 1 task still gets all four.
- **The reports are committed first,** before anyone acts on them, in one file:
  `…-kickoff-council.md` beside the spec; `…-phase-N-end-council.md` or
  `…-phase-N-start-council.md` beside the plan.
- **Their claims are checked** by the session, each against the code or the docs it cites, before
  Dan sees anything.
- **Each finding gets a severity and a decision** (*Reviews*): fixed in its own commit, the
  phase-end list, Later with a reason, or Dan.

## The retro

`…-phase-N-retro.md`, beside the plan, in four parts:

1. **Departures from the plan:** each Built differently note and ruling, and why.
2. **Items carried forward:** what went to Later or a later phase, and why.
3. **Metrics per tier:** tasks, review rounds, fix commits, findings by severity, and bugs found
   later by CI or by use, tallied from the closing commits.
4. **Starting over:** what this phase would do differently from the start.

**In the project's root folder,** on the phase branch: the closing commits (their `Tier:`,
`Rounds:` and `Findings:` lines), the reopens, and the bugs a review missed:

```bash
base=$(git merge-base main HEAD)
git log --format='%h %s%n%b' --grep='close Task' "$base..HEAD"
git log --format='%h %s' --grep='reopen Task' --grep='escaped from Task' "$base..HEAD"
```

Then the retuning rules set the next phase's tiers, each judged over the whole phase:

- Tier 3 reviews found an Important bug in more than one task: move that kind of task up a tier.
- Tier 1 re-reviews found nothing: consider dropping that re-review.
- A bug reached CI that a local check could have caught: add that check to the mechanical checks.
- Tier 2's Standards axis found no Important or Critical finding: the next phase runs Tier 2 with
  one reviewer under both headings.

Each change goes into the next phase's plan, its tasks' tiers included, and into the retro.

## The PR

superpowers:finishing-a-development-branch, its PR option, always.

- **The title** is *Commits*' phase-merge subject without its ` (#N)`.
- **The body** summarizes the phase: what each task built, the council's findings and what became
  of them, and the retro's link on a large project. It lists every file the leak check couldn't
  scan (a binary, an image) for Dan to check by eye; any such file is a stop (*Stops*), so the
  merge waits for him, vibed or not. Its last line is `Plan: <plan file> Phase end`.

**In the project's root folder, on `phase-N`,** first the files no scan can read, for the body:

```bash
git log --format= --numstat origin/main..HEAD |
  awk '$1 == "-" { print "not scanned, check by eye: " $3 }'
```

**Then, in the same folder,** with the title in `$(git rev-parse --git-dir)/PR_TITLE` and the body in
`$(git rev-parse --git-dir)/PR_BODY.md` (`.git` is a file in a worktree),
the scans and the PR:

```bash
if uv run --quiet --script scripts/leakcheck.py --message "$(git rev-parse --git-dir)/PR_TITLE" &&
   uv run --quiet --script scripts/leakcheck.py --message "$(git rev-parse --git-dir)/PR_BODY.md" &&
   cat "$(git rev-parse --git-dir)/PR_TITLE" "$(git rev-parse --git-dir)/PR_BODY.md" |
     gitleaks stdin --redact --no-banner --ignore-gitleaks-allow --config .githooks/gitleaks.toml; then
  gh pr create --base main --head phase-N \
    --title "$(cat "$(git rev-parse --git-dir)/PR_TITLE")" --body-file "$(git rev-parse --git-dir)/PR_BODY.md"
else
  echo "STOP: the PR text has a finding; tell Dan its kind and where, never the matched text"
fi
```

**The merge,** when the mode has the agent merge it (*Stops*), with *Commits*' phase-merge subject
in `$(git rev-parse --git-dir)/MERGE_SUBJECT`. **In the project's root folder,** the subject's scan, then the merge:

```bash
if uv run --quiet --script scripts/leakcheck.py --message "$(git rev-parse --git-dir)/MERGE_SUBJECT" &&
   gitleaks stdin --redact --no-banner --ignore-gitleaks-allow --config .githooks/gitleaks.toml < "$(git rev-parse --git-dir)/MERGE_SUBJECT"; then
  gh pr merge <N> --merge --match-head-commit <the scanned SHA> \
    --subject "$(cat "$(git rev-parse --git-dir)/MERGE_SUBJECT")" --body-file "$(git rev-parse --git-dir)/PR_BODY.md"
else
  echo "STOP: the merge subject has a finding; tell Dan its kind, never the matched text"
fi
```

Never `--admin`, never `--delete-branch`, never squash or rebase: plans and closing commits cite
commit IDs.

## Phase start (Phase 2 onward)

After the phase's PR has merged. Phase 1's forward council is kickoff's. Dan's reason: "you have
the actual step finish, merge into main, review, then next step."

1. **A fresh `main`:** `git switch main`, `git pull --ff-only`; then `git switch -c phase-N` and
   `make hooks`.
2. **Run the phase's listings:** each listing's tests against the code as built; which pass and
   which need rewriting goes in step 4's commit.
3. **The forward-and-back council** (*Councils*) on the phase's plan against the code as built,
   its report committed first. That first commit on `phase-N` also sets the finished phase's
   status line to `merged <commit> <date>`.
4. **The plan's fixes,** in *Commits*' phase start commit, with the listings' results in its body.
5. **Attended:** Dan approves the revised plan, and gives or withholds the phase's standing push OK
   (*Asking Dan*, *Pushing*). **Vibed:** straight on.
6. **Now** → `Task 1: <title>, open.`

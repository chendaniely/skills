# plan-driven-development: the design questions and Dan's answers

The questions asked while designing the `plan-driven-development` skill, 2026-10-14 to 2026-10-15,
in one Claude Code session. Each is a situation with outcomes, the agent's recommendation, and
Dan's answer in his own words; square brackets mark a word corrected or added for sense. The
decisions feed the spec, `2026-10-15-plan-driven-development-design.md` (not written yet), which is
the binding document. Where the two disagree, the spec wins and this page gets a dated note.

`local-ai` below is [github.com/chendaniely/local-ai](https://github.com/chendaniely/local-ai), the
project Dan named as the worked example of how he likes plans, commits and reviews.

## What Dan asked for

> i need to create a new skill in my ~/git/hub/skills it's about how i Constantly when developing
> applications and have the plan I like when the agent does backwards and forward reviews along
> each step, and then they commit things along each step in such a way where there is full
> [context] about what happens from the [git] history if we lose what is happening in the
> application. Sometimes it happens when I lose Internet or it's been a really long time and I
> personally the human has lost context of what is happening. I want to make sure that the model
> has all of the context in both the repository and [the git] history on what needs to be done and
> what has been d[one] and I like the backwards and forward review because it catches mistakes
> because we get to test that what was planned has been implemented and sometime[s the]
> implementation changes a little bit from the original plan because of bugs and tests and fixes
> like that. But then I also like forward reviews because given the current implementation, I want
> the agent to look forward in the plan because sometimes implementations will make decisions from
> fixes that affect the forward plan before we continue to the next step and I like all of those
> and small commits following conventional commits with both The type and optional scope and then I
> also like to have the 🤖 at the beginning of the description section. this example is also in the
> current repository where I like to have my commits and reviews them this way I've just created so
> many projects recently that I want to document this as an actual code skill for when I create a
> new project. this is how i want the agent to plan and write commits. When starting new projects,
> I like the superpowers skill to be invoked, and I like the skill for grilling me to make sure that
> both of us are in full understanding of one another. When planning steps, and when the agent
> needs some input from the user, I also like the agent to provide me a bunch of potential
> scenarios about what happens during each scenario, so those can all be planned for in the
> implementation throughout the plans and phases, and some things can be moved around and pu[shed]
> towards the end or as optional additional fixes that way.

## Settled before the numbered questions

- **The grilling skill.** Asked which skill "the skill for grilling me" meant: "Matt Pocock's
  grill-me". Then: "let's also install [all] of matpocock's skills". Installed as the
  `mattpocock-skills` plugin, 1.2.3, at user scope. `grill-me` can only be typed by a person (its
  frontmatter has `disable-model-invocation: true`) and only says to call `grilling`, so the skill
  calls `mattpocock-skills:grilling`.
- **A council on the first round.** "can you spin up a council review on those questions and
  default yes answers? then i'll review after you review the answers". Four read-only reviewers
  (goal fit, resumability, ecosystem fit, simplicity) reviewed round 1's eight questions. They
  found three gaps that would have made the skill fail:
  - superpowers keeps its rulings and deferred items in a git-ignored ledger and deletes it at the
    end, which is how local-ai once lost its next steps (`8dd57df`);
  - superpowers' plan runner is built never to stop and ask;
  - round 1 had no step for picking work back up.

  They also found two wrong facts in round 1. Round 2, below, replaced it.
- **One skill, plus one shared preferences file.** "i think you're right it [should] be a skill
  that also gets read into my global claude file (as well as my other [harnesses], pi, opencode,
  etc)".
- **List first, then one at a time.** "I don't particularly like it when the [agent] responds to
  me and all of the steps in one big block. I think it is useful initially, but I do like it when
  Claude presents me the options one at a time so when there are steps that I need to do let's
  please present them one at a time and re[present] them after I finish because sometimes things
  derail I come up with new ideas. I need to push stuff so by the time I'm ready to go on step two
  it is so far up the actual chat that I end up losing where to look for the next step and
  sometimes it's not even relevant anymore so things need to [be] pre-listed one so I get a sense
  of what's happening, but then also presented one at a time."
- **The docs site, the agent files and docs kept true.** "if it's not a project with a live demo
  website I like to have a [Quarto] website that ends up being deployed to [GitHub] pages via
  [GitHub] actions that is the documentation for the entire project, this is where everything with
  the project with the change log and decisions and scenarios all get documented. I also like to
  have a claude file reading agents.MD file and everything will now go into the agents MD file but
  also have a read me.MD file that also exists for the normal human to understand and read all of
  this can be re-incorporated into the actual website from quarto. for quarto please use the
  posit-dev skills and quarto website docs in your context. Another important thing is during every
  reviewing step we wanna make sure that the documentation is always up-to-date."
- **A review brief.** Before answering Question 2, Dan pasted a brief, written by an agent that
  assessed local-ai Phase 2a's fan-out reviews: risk-tiered reviews for subagent-driven
  development. Its evidence: after 24 of 52 tasks, 22 feature commits, 44 review-fix commits and
  23 re-review rounds, about 4 hours a task; returns dropped fast after the first re-review; the
  reviews missed a test that only failed in CI's UTC timezone. Three parts arrived cut off (the
  end of Tier 1's definition, "Cap the loop", and the severities other than Minor). Question 7
  fills them.

## Round 2: the questions

### 1. Project size

*A weekend app, three tasks, one sitting.*

- **A:** kickoff asks small or large and recommends one. Small: a spec and one plan, reviews and a
  commit per task, one branch, superpowers' final review; no phases, council or retro. Large: more
  than one phase, or it touches secrets, the network or hardware; phases, and per phase a branch, a
  council and a retro.
- **B:** always large. **C:** always small.

Recommended A. **Dan: A.** Both sizes get the docs and `AGENTS.md`.

### 2. How questions are asked, and where the answers go

*Kickoff needs six decisions; Dan answers four, then the connection drops.*

- **A:** list first, then one at a time, each a situation with outcomes A, B and C and one
  recommended. Each answer and its reason go on a Q&A page next to the plan as given, committed when
  the list is done or when Dan stops. This page is one.
- **B:** answers folded straight into the spec, losing the why and the options turned down.
- **C:** plain questions with a recommendation.

Recommended A, local-ai's `phase-2a-qa.md` format. **Dan: A.**

### 3. Where scenarios live

*Mid-phase, S07 turns out harder and can wait; S11 isn't needed at all.*

- **A:** one table in the spec: ID, situation, expected outcome, phase and task, proof, status
  (planned, built, verified). IDs are never renumbered or reused; tasks cite them; each phase's
  review re-checks them. A changed row is rewritten to what's true now and links the answer that
  changed it. S07 moves to a *Later* part, marked `end` or `optional` with a reason. S11 stays,
  marked dropped, with the date and why. Anything with a date or someone waiting is proposed as a
  YouTrack ticket.
- **B:** a page per scenario with dated notes, as local-ai's `website/scenarios/` has.
- **C:** scenarios only inside the tasks.

Recommended A: local-ai's scenario pages "gathered dated notes as the design moved", a later note
"often reversed an earlier one", and they had to be "rewritten as one current account each".
**Dan: A.**

### 4. Plan layout

*Three phases; Phase 1's review finds the data model needs another table.*

- **A:** the spec holds the outline; each phase's plan is written when that phase starts; tests
  written as code, implementation code only where the exact text matters.
- **B:** superpowers' default: every phase planned in full up front, full code in every step.
- **C:** phases just in time, with full code.

Recommended A. **Dan:** "i like B, but the review process should be able to make modifications as
needed. but it's good to have the full phase and plan fully written so it's reviewable and
searchable and good for reference if we're using a frontier model. this also helps when i use
local models for [implementation]" and "it's a combination of B and A".

Decided:
- From B: every phase planned in full up front, with full code.
- From A: the spec holds the outline, decisions, Revisions, open items and a status line per phase.
  Each task names its risk tier, scenario IDs, files, and what it consumes and produces. The plan
  opens with a one-line *Now*. Plan files never move.
- The forward review may rewrite any later task or phase, code included, to fit what was built.
- Listings are run before they go in where they can be; a later phase's listings are run when that
  phase starts.

### 4b. A finished task whose build departed from its listing

*Task 3's listing used a plain dictionary; a fix turned it into a validated class. Later a local
model implements Task 9.*

- **A:** replace Task 3's listing with the code as built.
- **B:** keep it as planned, with a "built differently" note at its head (what, why, commits).
  Task 9's listing has already been rewritten by the forward review.
- **C:** delete it and point at the files.

Recommended B. **Dan: B.**

### 5. What the agent may change by itself

*A library has no streaming API, so the build polls. Task 6 assumed streaming, and scenario S04
promised results "as they arrive". Dan is out for the afternoon.*

- **A:** the agent changes the plan itself when a change only follows from what was built (names,
  interfaces, task order, later listings), recorded in the closing commit. It stops at the task's
  own review when a change would alter the spec, a decision of Dan's or an approved scenario, or
  when the build removes the reason for a heavier later task (it re-offers the simpler option).
  While stopped it commits the record with the question on the *Now* line, asks, and starts
  nothing new. Here S04 changes, so it stops.
- **B:** it keeps building independent tasks while waiting.
- **C:** every departure stops and asks.

Recommended A, as an explicit fifth stop over superpowers' "Four things stop you, and only these".
**Dan: A.**

### 6. Where rulings and deferred items go

*Task 4's reviewer raises three nits and an Important finding that needs Task 9's code; the agent
rules against one suggestion. Then the session dies.*

- **A:** the closing commit copies everything out of superpowers' git-ignored ledger. Rulings go in
  the commit body and as one line under the task. Deferred findings go to a phase-end list at the
  bottom of the phase plan, with source task, severity and file. The spec's Revisions holds only
  Dan's decisions. At the phase end, anything undone moves to *Later*.
- **B:** every ruling also gets a Revisions line. **C:** rulings only in commit bodies.

Recommended A: local-ai's Revisions mixes both and is 547 of `plan.md`'s 1,513 lines. **Dan: A.**

### 7. Review tiers

*Task 12 rewrites a safety-critical memory guard; Task 13 rewords a runbook.*

- **A:** the brief becomes the review rules at both sizes. The plan sets each task's tier and the
  plan's review checks it. Mechanical checks run before any reviewer: the suite, the suite under
  `TZ=UTC` and other settings where CI differs, lint, the leak scan, each new test seen failing
  once. Tier 1 gets a full review with a security lens in the same task and at most one re-review,
  scoped to the fix. Tier 3 gets a light review or self-review; its nits are recorded, never
  looped. This replaces superpowers' loop of up to five fix rounds.
- **B:** Tier 1 keeps the five rounds. **C:** no tiers.

The agent's fill for the brief's cut-off parts:
- **Tier 1:** if wrong, it could take the system down, lose or leak data, freeze the machine, or
  silently stop alerting.
- **Cap:** at the cap, a one-line fix is made directly; anything else goes to the phase-end list or
  to Dan; never another round.
- **Critical** breaks a safety property, loses or leaks data, or blocks the phase. **Important** is
  a bug or missing case a user or test would hit, or a factually wrong doc. **Minor** is style,
  wording and nice-to-haves.

Recommended A. **Dan:** "i think A is correct. i think you already reviewed your own answers?" The
agent answered: only partly. The council reviewed round 1; the fill and this question are the
agent's own, so the design council checks them before approval.

During this question Dan added: "also for the project/app documentation i want to make sure we
always have a mermaid diagram of the overall structure and processes. this also makes it easy to
get an overview of the docs. the [architectural] diagram is just as important as the rest of the
docs". Decided: one overview plus a few process diagrams, built parts solid and planned parts
dashed, all on one Architecture page, the overview included (never copied) on the home page.

### 8. Commits

*Task 4 took a feature commit, three fixes and its close; the session died; a week later, on the
other machine, a Dependabot merge sits on top.*

- **A:** build and fix commits are `type(scope): 🤖 what changed` with a short body and a
  `Plan: <plan file> Task 4` trailer. The task ends with one closing commit,
  `docs(plan): 🤖 close Task 4: <title>`: it ticks the box and updates *Now*; its body records
  drift, rulings, phase-end items and forward-review changes; trailers `Plan:` and `Next:`.
  Messages go through a file and `git commit -F`, and the trailers are checked to have parsed.
- **B:** A without `Next:`. The *Now* line is the one "what's next".
- **C:** prose only, as local-ai does today.

Recommended B: `Next:` repeats *Now* and can't be corrected if the order changes. Merges are real
merges, never squashed. **Dan:** "B. before you ask the question review your own recommendation to
me. i'm more [inclined] to accept your recommendation". From here every recommendation carries a
self-review. Added at Question 12: the closing commit also records the task's tier, review rounds
and findings by severity.

### 9. Pushes

*Dan approves Phase 2's plan and leaves for the day; Task 3 passes locally but would fail in CI.*

- **A:** at plan approval, one standing OK to push that phase's branch, never `main`, ending at
  the phase merge. The leak scan runs before each push. A task closes only when CI is green; the
  next may start while CI runs, but red reopens the task. Without the OK, it asks each push. No CI
  means the local checks are the gate.
- **B:** ask before every push. **C:** push only at the phase end.

Recommended A. **Dan:** "i think pushing for A is okay. we can use some tools as a pre-commit git
hook to check for [credentials] so they don't end up in the history". Then: "i think
https://github.com/gitleaks/gitleaks is [something] i already have and use in the local-ai
project". The before-push scan stays, because hooks miss commits made before they existed, merges
git completes itself, rebased or cherry-picked content, and denylist terms added later.

### 10. Picking the work back up

*Three weeks away; the last session died mid-Task 5 on another machine.*

- **A:** a resume step at session start, or on "where are we?" ("catch me up" already starts
  Dan's vault catch-up skill). It reads, in order: `AGENTS.md`; `git fetch`, branch state,
  worktrees, stashes; the spec's status lines; *Now* and the boxes; the commits since the newest
  "close Task"; uncommitted work (its tests run, but it's never touched without Dan); the Q&A page.
  Commits win any disagreement. Then a ~15-line briefing and the list of next steps; nothing runs
  until Dan says go. "Stop for today" makes a `wip` commit and pushes it.
- **B:** a lighter read and carry on. **C:** no resume step.

Recommended A. **Dan:** no letter. His next two messages were the gitleaks note above and "we have
a few hooks for security checking in local-ai", which became Question 11. The agent recorded A,
and Dan didn't object in the questions that followed. Confirmed with Section 6 below, which is
this question's design: asked "is Question 10 A, since this section is its design?", Dan said
"yes".

### 11. Security hooks

*Day 3 of a new public project: a commit holds a home LAN address and a token-looking string.*

- **A:** kickoff installs local-ai's full set: gitleaks and the leak check in the pre-commit and
  commit-msg hooks, the before-push scan, gitleaks over the whole history in CI (pinned by
  checksum), shellcheck on the hooks. The leak check becomes a standalone PEP 723 script shipped
  with the skill and copied into each project, so the project works without the skill. One private
  denylist per machine, which the agent never reads. Private repos too.
- **B:** gitleaks only, which has no rule for addresses. **C:** A for public repos, B for private.

Recommended A. **Dan: A.**

### 12. Councils and metrics

*Phase 2 ends after 14 tasks; Phase 3's plan assumed something Phase 2 changed.*

- **A:** a council on the spec and full plan before approval; a phase-end council in place of
  superpowers' final review; a phase-start forward-and-back council after the phase's listings are
  run; metrics per tier. Small projects: one reviewer before approval, superpowers' final review, no
  metrics.
- **B:** only the phase-end council. **C:** A, plus superpowers' final review as well.

Recommended A. **Dan:** "C - this is A + more (superpowers), right/ it's a superset of features? if
so . yeah C". Confirmed it is. Phase end, in order: superpowers' final review (one fix dispatch);
its ledger copied into the plan; the council (four read-only reviewers: goal fit and scenarios,
reliability, security, simplicity; the session verifies their claims); the phase-end list; the
forward look; the retro (departures, carried items, metrics, starting over); then
finishing-a-development-branch with Dan's OK.

### 13. Matt's skills that compete with superpowers

*A test fails, and both superpowers' `systematic-debugging` and Matt's `diagnosing-bugs` match;
later both TDD skills match.*

- **A:** steer, don't block. The skill and the shared preferences file name the skill for each
  step: superpowers for TDD, debugging, writing plans and running them; this skill's tiers for
  reviews; Matt's `grilling` for interviews. Matt's other skills stay available when typed. The
  baseline test checks the steering.
- **B:** A plus permission deny rules for Matt's `tdd`, `diagnosing-bugs` and `code-review`
  (undocumented for plugin skills; might also block Dan typing them).
- **C:** nothing.

Recommended A, with B as the fix if the baseline test shows Matt's skills winning. **Dan: A.**

### 14a. What's on the docs site, and where its files live

*A week after kickoff, Dan opens the site to see why the config format changed, and a local model
opens the repo for Task 9.*

Recommended: everything in a Quarto site in `website/`, with the plans moved there.
**Dan:** "you can use the superpower's default location and quarto can use /../docs to reach
outside the website dir or anything else outside directory, this way we don't worry about things
going into the wrong place or not follow [conventions]." And: "quarto has {{< include >}} that can
be used to reference outside website or other things that are repeated".

Decided, after testing in a scratch site with Quarto 1.11.5:
- Files stay where conventions put them: the spec and plans under `docs/superpowers/` with
  superpowers' dated names, Q&A pages and retros next to their plan, and `README.md`, `AGENTS.md`
  and `CHANGELOG.md` at the root.
- The site in `website/` shows each through a wrapper page: `{{< include /../<path> >}}`.
- Each wrapper is a `.md` at the same relative path under `website/` as its source, holding only a
  `pagetitle:`. Then links between the spec, plans and Q&A pages resolve on the site and on GitHub.
  A `.qmd` wrapper breaks those `.md` links; a symlinked folder is ignored by Quarto.
- A `.md` wrapper refuses executable cells, so files under `docs/` carry no `{mermaid}` blocks.
  The diagrams live on the Architecture page, a `.qmd` in `website/`.
- A link from an included file to anything outside the site breaks, silently in the `../` case.
  Root files and docs use full site URLs or code-span paths for those.
- Mechanical checks: every doc shown on the site has its wrapper; a link check over the rendered
  site; CI fails on Quarto's "Unable to resolve link target".

### 14b. A project with a live demo site

- **A:** the same docs, read on GitHub, with no second site. The Architecture page becomes
  `docs/architecture.md` with GitHub's mermaid fences; the demo links to the docs. If the demo is
  itself a Quarto site, the docs pages join it.
- **B:** a Quarto docs site published next to the demo. **C:** docs built into the demo.

Recommended A. **Dan: A.**

### 14c. A private repo

GitHub: "GitHub Pages sites are publicly available on the internet, even if the repository for the
site is private."

- **A:** as 14b: docs on GitHub, nothing published. **B:** a Quarto site never published.
  **C:** publish anyway.

Recommended A. **Dan:** "A - if private, then just local github readme files no pages site". So the
Quarto site exists only for a public repo without a live demo. Kickoff asks public or private and
demo or not, alongside small or large, and `AGENTS.md` records the answers.

### 15. Keeping docs true

*Task 5 switches config from YAML to TOML; the README, a how-to and S07 still say YAML; a new
import step has no page yet; Task 9 adds a service.*

- **A:** wrong docs are fixed now; missing docs can wait. Anything a change makes untrue (a
  sentence, a status word, the README, a scenario row, a diagram) is fixed in the same task. A new
  page may wait for the phase end, on the phase-end list. Diagrams never wait. Each task's review
  greps the docs for every renamed or removed name and for status words in the touched area; the
  phase-end council checks all of it. Kickoff starts a sync table in `AGENTS.md`.
- **B:** everything in the same task. **C:** docs at the phase end only.

Recommended A: both local-ai retros have a "Docs that had become untrue" row, mostly leftover
status words. **Dan: A.**

### 16. The three root files

*Months later, pi with a local model, no skill loaded, internet down, Task 9.*

- **A:** `AGENTS.md` carries a self-contained "How we work" of about 60–80 lines (the kickoff
  answers, where things live, the check commands, each task's steps, the resume order, the
  docs-true rule and sync table, the security rules, and which skill version it came from).
  `CLAUDE.md` is `@AGENTS.md`. `README.md` says what it is, how to start, and where the docs are.
  Kickoff shows all three before writing them. In a repo with a real `CLAUDE.md`, its content
  moves into `AGENTS.md` in the same commit, since pi, OpenCode and Hermes read `AGENTS.md` first.
- **B:** a short `AGENTS.md` saying "follow the skill". **C:** the whole skill copied in.

Recommended A. **Dan: A.**

### 17. Where the shared preferences file lives

- **A:** in this repo, versioned, without frontmatter, each harness's global file pointing at it:
  an `@` import for Claude Code, an `instructions` entry for OpenCode, a symlink for pi. Hermes is
  left out: its only global file, `SOUL.md`, is its identity, and its docs say "leave preferences
  and profile facts to memory".
- **B:** a private file outside git. **C:** a copy in each harness's file.

Recommended A. **Dan:** "A -- but why is it [preferences].md not in a separate subfolder in
skills/?" With it, a new standing rule: "when you present me questions to ask. always give me the
context of how many more (the total) after a while i just forget how many total [questions] and it
ends up feeling endless".

### 17b. A root file or its own folder

**Dan:** "well if the [convention] is to have skills/[preferences].md let's do that. if the
[convention] is to have [preferences] in a subdirectory, let's do that. can we do a review search
on how other [prominent] people have this kind of file?"

What the search found: no standard. The AGENTS.md and Agent Skills specs say nothing about it.
Most people who publish skills publish no shared file, and dotfiles repos keep one copy per
harness. The one match for this setup, steipete/agent-scripts, keeps a root `AGENTS.MD` that a
sync script symlinks into each harness, and its README tells other repos to start with "READ
~/Projects/agent-scripts/AGENTS.MD BEFORE ANYTHING (skip if missing)". A root file here can't be
named `AGENTS.md`, or pi, Hermes and OpenCode would take it for this repo's own rules.

**Dan:** "seems like [preferences] should go into a separate repo where there is a setup script
that sets [everything] up. so we can create it in skills/[preferences].md for now and then leave a
github issue to move it out to a different repo where i [sync] up all my other agent global
instruction files". Decided: `preferences.md` at this repo's root for now, plus a `TODO.md` item
and its GitHub issue for the move.

## After the questions

- **The name.** `plan-driven-development`, named like superpowers' `test-driven-development` and
  `subagent-driven-development`. "Checkpoint" was ruled out because Claude Code has its own
  checkpoints (`/rewind`). **Dan:** "A is fine".
- **Where this page lives.** Here, superpowers' default spec folder, on the
  `plan-driven-development` branch; `docs/` is this repo's one top-level folder that isn't a skill.
  **Dan: A.**

## The design, section by section (step 3)

### Section 1 of 10: the skill's files, and what triggers it

- Files: `SKILL.md` (aimed at 200–300 lines: the five moments, which reference to read at each,
  the five stops, the commit formats inline, a red-flags table from the baseline test);
  `references/` (`asking.md`, `kickoff.md`, `plans.md`, `tasks.md`, `phase-end.md`,
  `resume.md`, `docs-site.md`); `templates/` (the `AGENTS.md` "How we work" section and
  `CLAUDE.md`, the git hooks and `gitleaks.toml`, the CI and Pages workflows, the Quarto config
  and a wrapper page); `scripts/leakcheck.py`; `tests/`.
- Triggering: model-invocable, with a description of explicit triggers only: Dan asks to start,
  plan or adopt; the repo's `AGENTS.md` names the skill (approved at kickoff, so it counts as his
  request under this repo's side-effects rule, and it runs the resume step at session start); or
  "where are we?" in such a repo.
- `leakcheck.py` is new security code (a port of local-ai's), so it gets its own tests as Tier 1.

**Dan:** "sure this looks good"

### Section 2 of 10: kickoff

In order:
1. Use superpowers:brainstorming and announce "a new project, so architectural".
2. The setup questions: small or large; public or private; a live demo or not; where the repo
   lives (creating a GitHub repo is outward-facing, so Dan's call).
3. Safety before the first commit: `git init`; the hooks with `leakcheck.py` copied in; a
   presence-only check on the denylist; a leak drill where an invented token and a
   documentation-range address are each refused; in an existing repo, gitleaks over the whole
   history once.
4. Grilling (`mattpocock-skills:grilling`, one question at a time, scenarios with A/B/C, a
   recommendation and a self-review), answers on the Q&A page, scenarios into the spec's table;
   brainstorming's questions in the same format if grilling isn't installed.
5. The design in sections, then the spec, committed with a one-line `AGENTS.md` pointer to it, so
   the resume step triggers even if the session dies before step 6.
6. `AGENTS.md`, `CLAUDE.md` and `README.md`, each shown (or diffed) before writing.
7. writing-plans: every phase's plan in full.
8. The council on the spec and plans (four reviewers for large, one for small); Dan approves,
   picks the execution method, and gives or withholds the first phase's standing push OK.
9. The docs site and CI are the plan's first tasks, as in local-ai's Phase 0.

**Dan:** "yes and yes this looks good" (to the order, and to the one-line pointer written with the
spec).

### Section 3 of 10: the spec and the plans

- The spec (`docs/superpowers/specs/<date>-<topic>-design.md`) is brainstorming's, plus a status
  line per phase, the outline (each phase's goal and "done"), the scenario table with its *Later*
  part and dropped rows, Revisions (Dan's decisions only), open items and risks, and diagrams by
  link only.
- writing-plans runs once per phase, all before approval
  (`docs/superpowers/plans/<date>-<topic>-phase-N.md`; one `<date>-<topic>.md` for a small
  project). Every writing-plans part stays (Goal, Architecture, Tech Stack, Spec, Global
  Constraints, Review Focus, tasks with Files, Interfaces, checkbox steps and full code).
  Added: a one-line **Now** at the top; **Tier** and **Scenarios** per task; "Built differently"
  notes, "Ruling:" lines and the phase-end list as the build goes.
- Horizontal rules are `***`, never writing-plans' `---`, so the files render when the site
  includes them.
- Q&A pages and retros sit next to their spec or plan; files never move.

**Dan:** "yeah this looks fine"

### Section 4 of 10: each task's loop

The session running the plan, with superpowers' subagents where the harness has them:
1. Build: the implementer works test-first and commits `type(scope): 🤖 …` with a `Plan:`
   trailer, through a message file and `-F`, exactly as the plan's commit step gives it.
2. Mechanical checks before any reviewer: the suite, again under `TZ=UTC` and the settings where
   CI differs (listed in `AGENTS.md`), lint, the leak scan, proof each new test failed once, and
   on site projects the render and link check when docs changed.
3. Backward review, scaled to the tier: spec compliance and quality, the cited scenarios and their
   proof, the docs grep, and a security lens for Tier 1. Each finding gets a severity and a
   decision (fix now, phase-end list, or Dan); the tier's cap ends the loop.
4. Forward review: read later tasks' Consumes lines and later phases' outlines first; open and
   rewrite only listings that use what changed; the fifth stop when a change touches the spec,
   Dan's decisions or a scenario, or makes a heavier later task unnecessary.
5. Docs: wrong ones fixed in the task, missing ones to the phase-end list, diagrams with any part
   or path.
6. Close: `docs(plan): 🤖 close Task N: <title>`, ticking the boxes and updating Now, the spec's
   status line and the scenarios' status; the body holds drift, rulings, phase-end items,
   forward-review changes, tier, review rounds and findings by severity; trailer `Plan:`, checked
   with `git log -1 --format='%(trailers)'`.
7. Push and CI under the standing OK, this phase's branch only: before-push scan, push, CI green
   closes the task; red reopens it ahead of anything else.

Without subagents, the same seven steps run inline through superpowers' executing-plans.

**Dan:** "yes this looks right. a can be any model using any harness, not just local on pi, e.g.,
qwen via dgx on opencode, or just plain claude code with opus". So the loop names no model or
harness: whichever runs the plan, with subagents or inline, follows the same seven steps.

### Section 5 of 10: phase end

As presented: (1) superpowers' final whole-branch review; (2) its remaining ledger copied into the
plan before superpowers deletes the workspace; (3) the council, four read-only reviewers whose
claims the session checks; (4) the phase-end list worked through, each fix at the tier of what it
touches, missing docs written, built parts turned solid; (5) the forward look over the later
phases; (6) the retro in four parts (departures, carried items, metrics per tier from the closing
commits, starting over), which retunes the next phase's tiers; (7) a dated `CHANGELOG.md` entry and
the spec's status line; (8) finishing-a-development-branch. A small project gets steps 1, 2, the
docs part of 4, 7 and 8.

**Dan:** "[usually] this should all happen as a branch + PR that merges into main usually we can
leave these unattended, for fully vibed projects we can just keep going without my explicit OK
since we have all the commits for fallback".

Revised:
- Step 8 is superpowers' PR option: the before-push scan, push, and a PR against `main` whose body
  summarizes the phase. It merges with `gh pr merge --merge` (a real merge commit; squash and
  rebase would change the commit IDs that plans and closing commits cite).
- The phase end runs unattended, through to an open PR with green CI.

**Follow-up: the project's mode.** *Phase 2's PR is open and green at 11 pm; Dan is asleep.*
- **A:** a kickoff question sets the mode. **Attended** (the default): everything runs unattended
  up to the open PR, which waits; Dan merging it is his OK; the next phase starts after the merge.
  **Fully vibed** (when Dan says so): the agent merges once CI is green and the phase-end steps
  are done, then starts the next phase; the fifth stop becomes a ruling, logged on the phase's
  Q&A page as "decided without Dan" and shown in the next "where are we?" briefing.
- **B:** vibed by default. **C:** the mode follows Question 1's risk test.

Recommended A. **Dan: A.**

Stops that never relax, even when vibed, because commits are no fallback for them: a leak-scan
hit; force-pushes, history rewrites, deleting branches or data; anything outside the repo
(creating repos, publishing packages, sending messages); secrets; spending money. For vibed
projects, Question 9's standing push OK extends to merging into `main` through the PR. Attended
projects don't stack phases: the next phase waits for the merge.

### Section 6 of 10: resume

As first presented: `AGENTS.md`'s "How we work" runs the resume step at every session start and
on "where are we?", and carries the steps itself. It reads `AGENTS.md`; `git fetch`, branch
state, worktrees and stashes; the phase PR and the last CI run; the spec's status lines; Now and
the boxes; the commits since the newest "close Task"; uncommitted work (tests run, never
touched); the Q&A pages, including vibed "decided without Dan" rulings. Commits win
disagreements. A ~15-line briefing ("since your last OK" means Dan's last Q&A answer or the last
PR he merged), then the next steps one at a time, waiting for a go; a session started with
"continue the plan" counts as the go. "Stop for today" makes
`chore(plan): 🤖 wip Task N: <where it stopped>` with the `Plan:` trailer and pushes it under the
standing OK, otherwise it asks first.

**Dan:** "usually [offline] means i won't have model access anymore and i won't be vibe coding
anymore. [usually] offline means the model stops in the middle and i [typically] need to resume
(or i run out of context in claude)".

Revised:
- No offline mode. If `git fetch` or GitHub fails, the briefing says so in one line.
- Nothing relies on a tidy stop: the implementer commits after each green step of a task, and the
  closing commit follows the reviews straight away.
- More triggers: after a context compaction (continuing from a summary), after a usage-limit
  stop, after any restart. Each time the agent re-reads the repo before acting.
- It reads what a crash leaves: superpowers' ledger (on that machine only, which is why closing
  commits copy it out), a merge or rebase stopped halfway (reported, never continued without
  Dan), a subagent's worktree, uncommitted edits.
- "Stop for today" stays for tidy stops.

**Dan:** "yes compaction is always a concern. we should always leave enough context about what has
happened. in vibe coded projects the commit history messages are the best for what has been done
along with the other files in the repo". So every commit body says what changed and why, enough to
rebuild the story without the session, and on vibed projects each "decided without Dan" ruling
goes in its commit body as well as on the Q&A page.

### Section 7 of 10: docs and the site

- Public without a demo: a Quarto site in `website/`, on Pages. A live demo or a private repo:
  the same files read on GitHub, diagrams in `docs/architecture.md` with mermaid fences; a demo
  that is itself a Quarto site gains the docs pages.
- Pages: Home (README include plus the overview), Architecture (a `.qmd` with every diagram; the
  overview in `_overview.qmd`, included on Home; built solid, planned dashed; local-ai's
  click-to-zoom script as a template, re-checked against Quarto's lightbox first), Design
  (`.md` wrappers at mirrored paths), Changelog and How we work (includes), How-to when needed.
- Kept true by Question 15's rule and the sync table, plus three checks on every push: every doc
  has its wrapper; CI fails on "Unable to resolve link target"; `lychee --offline` over the
  rendered site, pinned in CI. `***` for rules; site URLs or code spans for links leaving the
  site.
- Workflows from local-ai: render on every push, publish to Pages on every push to `main`,
  actions pinned by SHA, Quarto by version; first-time Pages setup is Dan's step.

**Dan:** "looks good. i like the quarto bits. we should also make sure that the quarto site builds
to github pages via actions. we should always try to have some deployed site somewhere (also
provide repo description field)".

Added:
- The site task closes only when the Pages URL actually serves the home page, checked after the
  first publish, not only when the workflow file exists.
- Kickoff drafts the GitHub repo's description and sets its website field to the deployed site
  (the docs site or the demo), shown with the root files and set with `gh repo edit` after Dan's
  OK.
- "Always some deployed site" against Question 14c's private repos: asked as a follow-up.

**Follow-up: a private repo and "always a deployed site".**
- **A:** every public project always has one (the docs site, or the demo, which links to the
  docs); private repos stay as 14c, GitHub-only docs with no deploy; the repo's website field
  points at whatever is deployed.
- **B:** private repos get the Quarto site on an access-controlled host when there is one (never
  public Pages), else A.
- **C:** private repos publish to public Pages with a nothing-private rule.

Recommended A. **Dan:** "yes sorry i forgot about private repos. yes you are correct. with A".
Noted for the plan: local-ai publishes through a `gh-pages` branch; GitHub's "GitHub Actions"
Pages source (`actions/deploy-pages`) needs no branch and narrower permissions. local-ai's tested
way stays the default until the plan weighs the two.

### Section 8 of 10: security hooks and the leak check

- Each project gets local-ai's set, standalone: `.githooks/pre-commit` (gitleaks on staged files,
  then `leakcheck.py --staged`), `.githooks/commit-msg` (gitleaks and `leakcheck.py --message`),
  both refusing without gitleaks 8.19+ or uv, turned on with `git config core.hooksPath .githooks`;
  `gitleaks.toml` extending the defaults; CI running gitleaks over the whole history (pinned by
  checksum) and shellcheck on the hooks; the before-push scan spelled out in `AGENTS.md`.
- `scripts/leakcheck.py`: local-ai's checker as a standard-library PEP 723 script, run with
  `uv run --script`; the same patterns and 3-character excerpts; modes `--staged`, `--message`,
  `--range`, `--tracked`, `--ci`; the allow marker excuses generic patterns only.
- The denylist: one per machine, `$LEAKCHECK_DENYLIST` or `~/.config/leakcheck/denylist`; fails
  closed (missing, empty or malformed refuses the commit); the agent stops and tells Dan, never
  creates or reads it. Dan's step: link it to `~/.config/local-ai/denylist`, and one per machine.
- local-ai's 295 lines of tests are ported as Tier 1 work, with fixtures built by joining strings.
- Noted for later: the skills repo itself has no hooks; a `TODO.md` item could add them.

**Dan:** "i think this looks right. i dont' [fully] understand what's happening [right now]". The
council checks this section with the rest, and a plain-words summary was offered.

### Section 9 of 10: overrides and steering

The overrides, each from an earlier answer: the fifth stop (a logged ruling when vibed) over the
plan runner's "Four things stop you, and only these"; the standing push OK (and, vibed, the PR
merge) over its stop for pushes to a shared branch; the tier caps over its five fix rounds; the
closing commits copying its ledger before it's deleted; commits after each green step with Dan's
format, `-F` and `Plan:`; a PR merged with `gh pr merge --merge` over finishing's local merge;
`***` over writing-plans' `---`; one question at a time over grilling's rounds. Steering:
superpowers for TDD, debugging, writing and running plans; Matt's `grilling` for interviews and
`writing-for-agents` for `AGENTS.md`; Matt's other skills only when typed.

How the overrides win: a skill can't outrank another, and superpowers puts user instructions
(`CLAUDE.md`, `AGENTS.md`, requests) above skills. So the table lives in `SKILL.md` for reference,
a short version goes into each project's `AGENTS.md` "How we work", and the steering list goes
into `preferences.md`. Subagents see only what they're sent, so the commit format reaches them
through the plan's commit steps.

**Dan:** "the reviews should also follow matt's code review guidelines".

**Follow-up: the review itself.** Matt's `code-review` (MIT) reviews a diff on two separate axes,
each in its own subagent, reported side by side and never reranked: Standards (the repo's
documented rules, plus twelve Fowler smells that are always judgement calls) and Spec (missing or
partial, not asked for, looks wrong; each quoting the spec line).
- **A:** `mattpocock-skills:code-review` runs the backward review, from the commit before the
  task, with the task, its scenario rows and the spec as the spec source. Tier 1: both axes plus
  a security lens; Tier 2: both axes; Tier 3: a self-review under the same two headings. The
  capped re-review reruns it from the fix's parent; the phase-end final review runs it over the
  whole branch. This skill adds a severity and decision per finding (within each axis), the docs
  grep and the cap. Kickoff writes a short `docs/agents/issue-tracker.md` ("work is tracked in
  the plans"), not Matt's full setup, whose `CONTEXT.md` and ADR folder would compete with the
  spec's Revisions. Where Matt's skill isn't installed, a short credited version of the brief sits
  in `references/tasks.md`.
- **B:** superpowers' reviewer with Matt's brief pasted in. **C:** both reviewers on every task.

Recommended A, adding a row to the table: superpowers' task reviewer replaced by Matt's two-axis
review, scaled by tier. **Dan:** "yeah this looks good (A)", taken as approving Section 9 with A.

### Section 10 of 10: testing the skill

RED without the skill, GREEN with it, REFACTOR for loopholes. Each test is a fresh headless
`claude -p` session in a throwaway repo built by a recipe script, with the skill linked into that
repo's own `.claude/skills/` for GREEN, explicit allow-lists (never a bypass flag), and a grader
over the repo and the session log. Scenarios:
1. Kickoff: every question listed with a count, only the first in full (A/B/C, recommendation,
   self-review), the list re-shown after one answer.
2. A three-task plan (Tier 1, Tier 3, a rename the README mentions): commit format, parsed
   `Plan:` trailers, closing commits, Now and boxes, the README fixed in the same task, a planted
   timezone bug caught by the `TZ=UTC` run.
3. A build that forces a scenario change: the fifth stop.
4. A repo left mid-Task 2 with uncommitted edits, then "where are we?": Task 2 found open, edits
   untouched, their tests run, a briefing, a wait.
5. A failing test with both plugins installed: `systematic-debugging` loaded, not
   `diagnosing-bugs`.
6. `leakcheck.py`: the ported tests, and the hook drill.

Plus a portability run: scenario 2 in OpenCode with a local model and only `AGENTS.md`. Tests live
in `plan-driven-development/tests/`, with an entry in this repo's `CLAUDE.md` Tests section. Checked
first: that plugins load in `claude -p` (the start-up event lists them). Compaction itself can't be
triggered; scenario 4 tests the recovery.

**Dan:** "yeah looks right . test it all . i'm not sure if my dgx model is actually up right now
or not". So the OpenCode run is in; whether the Spark's model is up gets checked when that run is
due, and if it's down the run waits rather than being dropped.

## The design council (2026-10-15)

Four read-only reviewers (goal fit and scenarios, reliability, security, simplicity) reviewed this
record. The session checked each cited claim before Dan saw it; all held except one: Tier 2 *is*
defined in Dan's brief ("one review; fix Critical and Important; re-review only if a fix changed
behaviour beyond what the finding asked"); this record's Question 7 entry had left it out.

### Fixes applied without a decision (consequences of facts, or gaps in approved designs)

- **Leak drill:** a documentation-range address is not private (local-ai's tests list
  `192.0.2.7` as harmless), so the drill uses a private address joined from parts at run time,
  as local-ai's `leak-guards.md` does.
- **The port keeps everything:** CI's two address scans (`--tracked --ci`, and every commit's
  patches and messages), `test_hooks.py` and `test_workflows.py`, the `.gitignore` hardening and
  `dependabot.yml`. gitleaks can't take the address patterns: they use lookarounds, which its
  regex engine lacks.
- **Trailers:** one final block, `Plan:` with `Co-Authored-By:` and no blank line between
  (tested, git 2.54: a blank line between them, or prose in the same paragraph, silently drops
  `Plan:`). The commit-msg hook refuses a Conventional Commits subject that's malformed, a `Plan:`
  without 🤖, or a 🤖 commit whose `Plan:` didn't parse (with `--no-divider`). Five local-ai commits
  from other harnesses lack the 🤖.
- **Closing commit template:** `templates/close-task.txt` with required headings (Drift, Rulings,
  Phase-end, Forward, Tier, Rounds, Findings) fills the `-F` file; the commit-msg hook refuses a
  `close Task` message missing one. The same for `wip`. Red flags stay for the stops.
- **Hooks on before any commit:** kickoff and every resume check `core.hooksPath` and validate the
  denylist with `leakcheck.py --message /dev/null` (local-ai's `make hooks` does this; it prints
  nothing). Phase 0 of local-ai committed Tasks 1–8 with the hooks off.
- **Text that leaves without git** (PR titles and bodies, merge messages, the repo description,
  issue and PR comments) is written to a file, scanned with `leakcheck.py --message` and
  `gitleaks stdin`, and passed with `--body-file`.
- **Merges:** `gh pr merge --merge --match-head-commit <scanned sha>` with a Conventional
  Commits subject (`chore(repo): 🤖 merge Phase N: … (#N)`) and a body with `Plan:`; never
  `--admin`, never `--delete-branch`. A phase branch takes in `main` by merge, never rebase.
- **Tiers:** the spec carries all three from the brief, with Tier 1's examples (permissions,
  secrets, network exposure, deploy and restart, bootstrap, cutovers). Each finding names file and
  line, why it matters, and how to fix it. A Critical never goes on the phase-end list: it goes to
  Dan, vibed or not.
- **Re-reviews** use superpowers' `re-review-prompt.md` (it checks each finding and the fix diff
  only), not a fresh run of Matt's review: Question 7 and the brief say "scoped to the fix … not a
  fresh full review", which Section 9's "reruns it from the fix's parent" contradicted.
- **Closed only when CI is green:** a red run gets `docs(plan): 🤖 reopen Task N: CI red`,
  unticking the box and resetting Now; resume checks CI for every close since the last green run.
- **The phase end is a task:** each plan ends with a "Phase end" task whose boxes are Section 5's
  steps; council reports are committed to a file before anyone acts on them; status values
  include `PR open (#N)` and `merged`.
- **The site task** closes on CI's render and link check; the live-URL check goes on the
  phase-end list for right after the merge (Pages publishes only from `main`).
- **Resume:** after a compaction or a usage-limit stop inside a run Dan started, his go stands;
  the wait for a go applies to a fresh session. It finds the active branch from the newest `Plan:`
  trailer across all branches. With no ledger mid-review, one fresh review runs from the task's
  base. Untracked files are listed by name only.
- **Proof that a test failed first** goes in the build commit body (the failing output line), so
  it survives a crash.
- **`Plan:` values:** `<file> Task N` and `<file> Phase end`. Fix-round dispatches carry the
  commit format and trailer, since no plan step covers them.
- **Now** goes right after writing-plans' required header, after `**Spec:**`.
- **Section 9's table** also overrides: "A running plan does not wait on a human";
  executing-plans' copy of the four stops and its "no reviewer per task"; finishing's "Present
  the menu and wait" (vibed merges); the plan runner's fix-round resume rule; the worktree consent
  question. finishing has no default local merge: the override is choosing its PR option.
- **Asking rules** (list first, one at a time, "N of M" and saying when M changes, A/B/C with a
  recommendation and self-review) go in both `preferences.md` and `asking.md`, for every question
  and every [Dan] step.
- **Later rows come back:** the last phase's forward look offers each `end` or `optional` row:
  plan it, keep it optional, or drop it.
- **[Dan] steps:** labelled, saying where they run; Now reads "waiting on Dan: …"; presented on
  their own.
- **Growth and change:** a small project that grows keeps its plan as Phase 1 and adds phase files
  (a Revisions line); a phase with no Tier 1 task still gets four reviewers, and the security one
  re-checks the tiers; a bug a review missed is fixed with "escaped from Task N (Tier X), found by
  …" in the commit body.
- **`AGENTS.md` template** carries local-ai's rules: stage by explicit path; never `--no-verify`;
  no secret on a command line; one check command.
- **One check command** named in `AGENTS.md` (a `make check` where the project uses make): the
  suite, the suite under `TZ=UTC`, lint, the leak scan, the render and link check.
- **Description:** one short clause on what it is, then the triggers, which meets both this
  repo's rule and writing-skills' (no workflow in the description).
- **Kept, with reasons:** the leakcheck port (above); the metrics, since the closing commits
  already carry them and `git log --grep` tallies them.
- **Tests added:** resume on another machine with no ledger; a ledger saying complete with no
  closing commit; a stale summary contradicting the repo (stands in for compaction); a diverged
  branch; a merge stopped halfway; the trailer-hook drill; a crash during the phase end. The
  portability run covers resume (scenario 4) as well as scenario 2, in OpenCode and pi.
- **Test harness:** the skill is copied into the throwaway repo, not linked (a link would carry
  write access into this public repo); allow-lists name exact `git` subcommands, the leak check,
  the recipe's test command and gitleaks, with no remote, no `gh`, no network, no MCP
  (`--strict-mcp-config`), no `env`, no bypass or `acceptEdits` mode; `LEAKCHECK_DENYLIST` points
  at a fixture of invented terms; session logs stay in scratch; OpenCode gets its own
  deny-by-default `opencode.json`, and Dan names the model.
- **This repo's hygiene:** fixtures build look-alike values from joined strings; this branch's
  first push is scanned first; leak findings are recorded by kind and `file:line`, never the
  excerpt.

### Decisions for Dan

Recorded below as he answers them. Eleven, asked one at a time.

**1 of 11. When a task counts as "complete".** superpowers' plan runner writes
`Task <N>: complete` to its git-ignored ledger as soon as the review is clean, before this skill's
forward review, docs and closing commit, and trusts that line on resume ("do not re-dispatch
them"). A crash in the gap skips the closing commit; on another machine there is no ledger, and
the runner restarts at Task 1, which superpowers calls "the single most expensive failure
observed".
- **A:** the runner writes "complete" only after the closing commit, naming its SHA; the resume
  step rebuilds the ledger from the closing commits, in superpowers' exact line format, before
  handing over. Both go in the override table and `AGENTS.md`.
- **B:** leave the ledger alone; resume checks each "complete" against a closing commit.
- **C:** stop using superpowers' runner.

Recommended A: B works only on the machine that crashed; C loses superpowers' prompts. The test
"resume on another machine with no ledger" catches a future change to the ledger's format.
**Dan:** "A seems fine".

**2 of 11. Pushing.** As designed, nothing was pushed before the closing commit, so a machine
switch mid-task left the second machine blind and the branch later diverged.
- **A:** push every commit under the phase's standing OK, each scanned first (Decision 5's hook);
  the briefing reports ahead, behind or diverged, and diverged means stop and ask; one session per
  branch at a time; CI cancels a branch's older runs. Without the standing OK, push at the closing
  commit after asking.
- **B:** push at the closing commit only. **C:** A on vibed projects only.

Recommended A. **Dan: A.**

**3 of 11. Phase start.** Question 12 chose a phase-end council and a phase-start forward-and-back
council, but no section gave the phase start a step. Dan's brief: "Two councils per phase:
forward-and-back, on the plan before implementation, [and] phase-end".
- **A:** the phase start is its own step after the merge: branch from a fresh `main`, run the
  phase's listings, a four-reviewer council on the phase's plan against the code as built, fixes
  before Task 1.
- **B:** one council at the boundary does both jobs, before the PR, with the next phase's listings
  run on the finishing phase's branch; plus one standing push OK at kickoff for all phase
  branches.
- **C:** no forward council.

Recommended B. **Dan:** "i like A a bit more. makes it much more clean between steps. you have the
actual step finish, merge into main, review, then next step."

So the moments are six: kickoff, planning, each task, phase end, **phase start**, resume. Phase
start: switch to a fresh `main`; branch `phase-N`; run the phase's listings; the council (its
report committed to a file before anyone acts on it); plan fixes committed as
`docs(plan): 🤖 phase N start: …`; then Task 1. The standing push OK follows Question 9: it's
asked when the phase's plan is approved, which on attended projects is this step (vibed projects
run straight on). The B-only idea of one standing OK at kickoff is not adopted.

**4 of 11. Stops that never relax.** Section 5's list let a vibed agent clear its own leak hit with
an allow marker.
- **A:** add seven, in every mode: weakening a guard (loosening or removing a check in the hooks,
  the gitleaks config, `leakcheck.py`, or CI's leak or publish jobs, or adding any allow marker or
  ignore entry; adding checks is fine); changing the repo's visibility; tags and releases; repo
  settings (rulesets, Pages settings, `gh api` writes, `gh` login scopes); merging a PR the agent
  didn't open, such as Dependabot's (Dan merges those between phases after reading their
  messages); an open Critical finding; a file the leak check couldn't scan in what's going out
  (the merge waits and the PR body lists it).
- **B:** only the GitHub-side four. **C:** no change.

Recommended A. **Dan:** "A is right".

**5 of 11. Two more hooks.** Pushes (now after every commit) and merges git completes itself
bypass the commit hooks; the documented before-push range also fails on a brand-new branch.
- **A:** both, in every project, with tests: `pre-push` scans what's going out (for a new branch,
  everything the remote lacks), the tracked files and gitleaks, refuses pushes to `main`, force
  pushes and tags, and fails closed when it can't tell what's going out; `pre-merge-commit` runs
  the commit checks on merges git completes itself.
- **B:** `pre-push` only. **C:** neither.

Recommended A. Dan's own direct pushes to `main` in such a project would need `--no-verify`, which
is his to use and never the agent's. **Dan: A.**

**6 of 11. How the site reaches Pages.** local-ai's `gh-pages` branch keeps every rendered version
in its history, so a leaked page stays public after the fix, and its publish doesn't wait for the
leak scan.
- **A:** "GitHub Actions" as the Pages source: one workflow on pushes to `main` runs the leak-scan
  job, then Quarto's `render` action, `upload-pages-artifact` and `deploy-pages`; the deploy runs
  only if the scan passed; no `gh-pages` branch, and no write permission on the repo for the
  publish job.
- **B:** keep `gh-pages`, gated on the scan. **C:** keep local-ai's way exactly.

Recommended A, proven by the first project's site task and its live-URL check; actions pinned by
SHA to versions at least a week old (`deploy-pages` v5.0.1, 2026-09-01). Whether local-ai switches
is a separate, later decision. **Dan: A.**

Mid-way through Decision 7, Dan switched local-ai's Pages source to "GitHub Actions" himself. GitHub
then reported `build_type=workflow`, and the site still served its last build, but local-ai's
publish workflow still pushes to `gh-pages`, which Pages no longer reads, so the next push to
`main` won't update the site. Fixing `publish-website.yml` (and its setup comment, the plan's
publishing paragraph with a Revisions line, and possibly `test_workflows.py`) joins the local-ai
fixes, after these decisions.

**7 of 11. GitHub settings at kickoff.** A fresh clone without hooks, or a confused agent, could
push to `main`; a click could squash-merge a PR.
- **A:** at kickoff, for every public project, a checklist Dan applies (settings are on
  Decision 4's list): a ruleset on `main` requiring a PR and CI's checks (leak jobs included),
  blocking force pushes and deletion, with bypass "For pull requests only" so admins (and so the
  agent, which pushes with Dan's login) go through a PR; merge commits only, the message defaulting
  to the PR title and description; Pages source "GitHub Actions"; the description and website.
  Classic branch protection if rulesets aren't on Dan's plan (unverified).
- **B:** vibed projects only. **C:** hooks only.

Recommended A. **Dan:** "let's go with A for now. and flag it. there's a chance we only do this for
vibe'ed projects only". Flagged as an open item in the spec: every public project for now, maybe
vibed only later.

**8 of 11. Work in place, or in worktrees.** With a worktree, the project's usual folder sits on
`main` with a stale spec and plan, and superpowers' ledger lives elsewhere, so a resume there
reads the wrong picture.
- **A:** in place: the project's folder checks out `phase-N`; `AGENTS.md` declares it, which
  superpowers' worktree skill honours ("Honor any existing declared preference without asking");
  resume still lists worktrees. **B:** a worktree per phase. **C:** ask each time.

Recommended A. **Dan:** "let's keep in place as default. and we can always say worktree or use orca
to force the worktree flow". So when Dan asks for a worktree (or Orca opens one), the spec's status
line names its path, and resume reads from there.

**9 of 11. One copy of the rules.** The task-closing rule (and others) appeared in `SKILL.md`,
`references/tasks.md` and the `AGENTS.md` template; only the `AGENTS.md` copy outranks superpowers
(Section 9), and the others could drift.
- **A:** the `AGENTS.md` template is the one copy of every rule that runs each session (the task
  loop, stops, overrides, commit format, check command, resume); `SKILL.md` and the references
  keep only what particular moments need and link to the template; references go from 7 to 4
  (`kickoff.md` absorbing `asking.md`, `plans.md`, `phase-end.md` with phase start,
  `docs-site.md`); the description drops its session-start trigger. "How we work" grows from 60–80
  lines to about 100–120.
- **B:** keep the layout, with a test that fails when copies disagree. **C:** keep `AGENTS.md`
  short, pointing at the skill (fails Question 16's scenario).

Recommended A, which changes Section 1's file list and Question 16's length. **Dan: A.**

**10 of 11. Tier 2 reviews.** Matt's `code-review` runs Standards and Spec as two separate
subagents, which doubles the reviewers on most tasks.
- **A:** keep Section 9's choice: Tiers 1 and 2 run Matt's two separate reviewers; the phase
  retro's metrics decide whether the next phase drops Tier 2 to one.
- **B:** Tier 2 gets one reviewer under both headings, with Matt's smell list.
- **C:** one reviewer at every tier.

Recommended A: Matt separates the axes on purpose, and the brief's cost came from fix loops, which
the tier caps now bound. **Dan: A.**

**11 of 11. A guard on the denylist.** Only prose kept an agent from reading it; Dan's secrets
guard (35 `Read` deny rules in `~/.claude/settings.json`, and the `block-secret-access.sh` hook,
since deny rules "only cover the Read tool") doesn't mention it.
- **A:** both layers: `Read` deny rules for `~/.config/local-ai/denylist` and
  `~/.config/leakcheck/denylist`, and both paths in the hook's patterns with new test cases;
  diffs shown first, applied at step 5 with the other config changes; then a scratch-repo commit
  proves the leak check still runs.
- **B:** deny rules only. **C:** prose only.

Recommended A. It guards Claude Code only; OpenCode and pi keep the prose rule in `AGENTS.md`.
**Dan: A.**

## Checked by the design council

- Question 7's fill for the brief's cut-off parts: it matches the surviving text (goal-fit
  reviewer). Tiers 2 and 3 and the finding format come from the brief itself, and a Critical never
  goes on the phase-end list.

## The spec

An independent reviewer checked the spec against this record; its fixes went in as `d454acd`.
Asked to keep the ruleset's "For pull requests only" bypass (A) or use an empty list (B), and to
approve the spec: **Dan:** "yes go for A approved" (2026-10-15).

## After the spec: a Makefile in every project

**Dan (2026-10-15, while the plan was in review):** "for the project plan, i'd also like a
[preference] to have a Makefile whenever possible to make running commands easier for both the
agent and user."

To be folded into the spec and the plan with the plan review's fixes:
- Kickoff copies a `Makefile` template into every project, local-ai's style: `make help` is the
  default and lists the targets from their `## ` comments; kept to GNU make 3.81 so it runs on the
  Mac as well as Linux (tested on both). Targets: `help`, `hooks` (turn the hooks on and validate
  the denylist), `check` (the one check command), `test`, `lint`, and `docs` on site projects
  (render plus the link check).
- `AGENTS.md` names the targets rather than raw commands, and a command people will run more than
  once becomes a target; runbook and docs commands use the targets where one exists.
- `preferences.md` carries the preference for every project.
- This skill's own commands (its tests, the skills repo's frontmatter check, `install.sh`) get
  targets too, in a `Makefile` at this repo's root.

Folded in with the plan review's fixes (below): `templates/Makefile` adds `test-utc` and `leaks`
targets, and `make hooks` checks the tools and the denylist before turning the hooks on. Both
Makefiles were run on the Mac's GNU make 3.81 and on GNU make 4.3 in an `ubuntu:24.04` container.

## After the plan review

An independent reviewer read the plan against the spec, re-ran its 141 tests and the leak check's
and hooks' listings (all passed), and returned ten findings ("approve with changes"); the session
checked each claim. All ten were applied:

1. **Blocking:** every push block ran `git push` even after a failed scan, and relied on an
   undefined `$LOCAL_AI`. Now a push runs only if the leak check, gitleaks and a binary check all
   pass, and `$LOCAL_AI` is set as a Global Constraint and checked (tested against a bare remote in
   bash and zsh; bash refuses an apostrophe inside `"${VAR:?…}"`, so the message has none).
2. The plugin paths were hard-coded to superpowers 6.4.1 and Matt 1.2.3; superpowers had moved to
   7.0.0 and Matt's skills to 1.3.1 that night. The runner now reads `installed_plugins.json` and
   records the versions.
3. Three graders couldn't tell a good run from a bad one (s12 matched `git merge-base`; s19 counted
   any subagent; S03's conflict could be avoided). Fixed, each with a test.
4. Each run is now checked for isolation: none of Dan's own skills loaded, the skill present for
   GREEN and absent for RED, and a canary turn opens RED.
5. Task 3 split into three (the checker and a Makefile; the fixtures and graders; the runners, at
   Tier 1), with per-scenario allow-lists and `--no-verify` denied wherever it appears.
6. Every task is self-contained for an implementer who sees only it: every commit written out, the
   test command inline, the phase end named `### Task 16: Phase end (a small project)`.
7. The phase end gained its missing commits and pushes, a Ruling for the missing `CHANGELOG.md`,
   and a PR body ending in `Plan: … Phase end`.
8. The port regained local-ai's lost tests and assertions, names binaries in a push's range, keeps
   the dropped `.gitignore` patterns, and its refusal tells an agent to stop and tell Dan.
9. Three spec items gained steps: the scratch-repo commit proving the hooks read the real denylist
   (Decision 11), the deny-rule fallback for Matt's `tdd` and `diagnosing-bugs`, and a definition of
   `__SKILL_VERSION__`.
10. The minors: diffs from each task's own base, Task 1's Tier 1 review, the release at Tier 3, the
    skill text split into two review gates, the drill asserting its findings, S02's fixture
    Makefile no longer running `TZ=UTC` for the agent, results files checked for paths, one waiting
    rule for S15/S16, and the missing test command.

**Upstream since the spec (superpowers 7.0.0, Matt 1.3.1).** writing-plans now asks for "a code
block only for an algorithm they do not determine" (overridden: full code, Dan's Question 4);
brainstorming's builder check becomes a small project's one pre-approval reviewer; Matt's
`code-review` no longer names `docs/agents/issue-tracker.md` but still reads a tracker doc;
`grilling` adds "Word each question so 'yes' accepts your recommended answer", which fits. And
brainstorming 7.0.0 now asks open questions first ("Offer a short menu only when they're stuck";
red flag "Options steer"), the opposite of Dan's format, so:

**Brainstorming's open questions.** *Kickoff of the next project; the new brainstorming says to
ask open questions first.*
- **A:** Dan's format for every decision, with one exception: kickoff may open with a single
  "describe it in your own words" question about intent.
- **B:** Dan's format everywhere. **C:** follow the new brainstorming.

Recommended A. **Dan:** "i like the choices that you give me when you (claude) display the options
that are selectable/clickable in the tui. unless it has a lot of text you should opt for that view
over the wall of text. makes selecting options easier. let's go with A".

So: A, and a new asking rule: where the harness has selectable options (Claude Code's
AskUserQuestion), choices are presented that way, the recommended option first and labelled
"(Recommended)", with the short self-review just before; text when the options need long
explanation. Both are in the spec, `preferences.md` and the template's contract.

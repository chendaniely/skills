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
and Dan didn't object in the questions that followed. *To confirm.*

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

## Open for the design council

- Question 7's fill for the brief's cut-off parts.
- Question 10's answer, recorded as A without a letter from Dan.

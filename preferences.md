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

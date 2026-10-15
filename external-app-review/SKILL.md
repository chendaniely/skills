---
name: external-app-review
description: 'Writes an honest outside review of a finished application that another model or coding agent built, after you have reviewed and fixed it: a docs folder with an executive summary, numbered chapters, Mermaid diagrams, screenshots from the commit history, appendices and sanitized research notes. Use when asked to write up, document or judge how another model or agent (often a local or open-weights model in another harness) performed on a project, for a blog post, a model comparison, or a decision on whether that model is viable for this kind of work.'
---

# External app review

A write-up of how another model or agent built an application, by the agent
that reviewed and fixed it. It is raw material for someone else's writing (a
blog post, a decision), so the verdict comes first and the evidence sits below.

**Core principle:** facts come from evidence (commits, transcripts,
measurements, screenshots) and carry a pointer to it. Opinions are labelled and
owned by you. Your own mistakes get the same treatment as the builder's.

## When to use

- The user asks for documentation, a review or a case study of how a model or
  agent performed on a project, usually after your own review-and-fix pass.
- The user is testing a local or cheaper model and wants a frontier model's
  candid judgement, including whether their plugins, skills or harness helped.

**Not for:** reviewing a diff or PR (use a code-review skill), or a review
before any fixes. Chapter 4 needs the fix pass, so finish that first.

## Before you start

1. The fix pass is finished, or at least its findings list is final.
2. Read the repo's agent rules (AGENTS.md, CLAUDE.md). They decide commit
   style and whether the human README may link to the docs. Default: don't
   link them.
3. Check whether the repo is public (`gh repo view --json visibility`). If it
   is, everything committed is published, so sanitize with that in mind.
4. Find the builder's evidence: per-model commit trailers, the plan or spec and
   its history, and the harness's transcript store and config.

## Output contract

Use `docs/external-review/`, unless the user names a folder (the worked
example used `docs/case-study/`). `<builder>` and `<reviewer>` are short model
names, such as `qwen` and `claude`.

```
README.md                   executive summary, the page most people read
01-setup-and-method.md      question, hardware/model, harness, plugins, rules, how this review was made
02-timeline.md              day by day with the user's own prompts, Gantt + process flowchart
03-<builder>-review.md      verdict paragraph, scorecard, did well, went wrong, code notes, model vs setup
04-<reviewer>-pass.md       findings, every fix + how verified, your own mistakes, numbers, outcome
05-plugins-and-skills.md    what loaded vs what was used; good / bad / neutral; recommendations
06-verdict.md               short answer, good enough / not, what you caught that it missed, cost, workflow
07-gallery.md               the app at each milestone, what the builder "saw", before/after
appendix-a-prompts.md       every user prompt in order, verbatim; private ones summarised
appendix-b-numbers.md       commits by model (pie), time, code size, sessions, defects by finder
research/                   sanitized raw notes + README index; chapters win on conflicts
assets/history/ assets/<builder>-saved/ assets/<reviewer>/
```

Section-by-section contracts, including the README's exact shape, are in
[references/structure.md](references/structure.md). Follow them; they are what
makes the folder readable top to bottom.

## Workflow

1. **Research, in parallel and read-only.** Dispatch research subagents
   (history, transcripts, harness config, screenshots). Each writes a note
   into a git-ignored workspace, such as `.playwright-mcp/<slug>-research/`.
   If `git check-ignore` says that folder is not ignored, add it to
   `.git/info/exclude`.
   Recipes are in [references/research.md](references/research.md). Re-run a
   sample of their numbers yourself before using any.
2. **Screenshots at milestone commits.** Run
   `node <this skill>/scripts/shots-at-commits.mjs` from the app's repo, with a
   steps module for that app. The scripts ship in this skill's folder. See
   [references/screenshots.md](references/screenshots.md). Open every image
   and check that it shows what its filename says.
3. **Write the chapters yourself.** Subagents may draft the factual chapters
   (2, appendices). Chapters 3, 4 and 6 hold the judgement, so you write them.
   Write the README last, because it summarizes the rest. State the status as
   it is when you write (for example "fixes on branch X, not merged yet").
4. **Sanitize** (see Privacy below), then copy the research notes into
   `research/`.
5. **Verify.** `node <this skill>/scripts/check-docs.mjs docs/external-review` checks that
   every Mermaid block parses and every link and image resolves. Re-derive the
   headline numbers from git. Scan the added lines for private data and read
   every hit.
6. **Commit** the folder as one docs commit in the repo's style.
7. **Refresh after the outcome.** Once the fixes merge or deploy, or a
   follow-up lands (a secret rotated, a check run), update 04's Outcome
   section, the README status line, the numbers and the Gantt chart. A review
   written before the merge goes stale.

## What makes it worth reading

| Element | Rule |
|---|---|
| Executive summary | What happened, why, a 4-bullet TL;DR (what it did well, what wasn't safe, the tooling's effect, your verdict), a before/after hero image, the chapter table and the numbers table |
| Credit | "Did well" comes before "went wrong", with real credit where it is due |
| Scorecard | Letter grade per area, one line of evidence each |
| Model vs setup | Separate harness and environment limits (served context below configured, a text-only model fed images, a misconfigured skills path) from model limits |
| Your mistakes | Every mistake your own reviews caught in your pass gets a section, not a footnote |
| What you caught | A list of what you picked up that the builder missed, and why: real-browser checks, world knowledge, a forward review |
| Viability | Answer the user's real question: which tasks yes, which no, cost and speed, and a hybrid workflow you'd recommend |
| Diagrams | About six, each with a purpose: Gantt (timeline), process flowcharts (both passes), tooling flowchart, verdict workflow, commit pie |
| Pointers | Every fact cites a commit hash, plan record, transcript time or measurement |

## Privacy

- Never copy a credential value. Describe an incident (what was read, when,
  and the fix) without the value, and recommend rotation.
- Leave out third parties' names, pasted private chats and personal remarks.
  Summarise them in Appendix A and say they were omitted.
- Shorten home paths to `~`. Omit LAN addresses, hostnames and usernames.
- Keep the unsanitized research and the full screenshot set git-ignored
  locally. Commit a curated set of about 20–30 images, roughly 2–3 MB.

## Common mistakes

| Mistake | Fix |
|---|---|
| README is an index with no verdict | The README opens with the TL;DR and verdict |
| Sprawl: CSV evidence dumps, `.mmd` mirrors, mobile/dark variants, 10+ diagrams | Stick to the output contract. Raw data stays in `research/` or git-ignored |
| Your own errors as "if any" | Scan your pass's review records and list each one |
| Blaming the model for harness limits, or the reverse | Give "model vs setup" its own section |
| Screenshot names that lie (a click swallowed, the wrong screen) | Open every PNG before you reference it |
| Numbers from memory | Re-derive from `git log` and the transcript store |
| Docs left saying "not merged" or "rotate the password" | Do the post-outcome refresh (Workflow step 7) |
| Linking the docs from a human-only README | Follow the repo's rule; default to no link |

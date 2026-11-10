# The docs and the site

Read this at kickoff before the safety steps, before the plan's docs task, and before the live-URL
check after a phase merges. Which skills site work uses, and how the docs are kept true, are the
project's `AGENTS.md` ([`templates/AGENTS.md`](../templates/AGENTS.md)): *Overrides*, *Steering*,
and *Docs and security*.

## Which docs, by case

Setup answers 2 and 3 ([`kickoff.md`](kickoff.md)) pick the case:

| Project | Docs | Deployed site |
|---|---|---|
| public, no live demo | a Quarto site in `website/`, on GitHub Pages | the docs site |
| public, with a live demo | markdown read on GitHub; diagrams in `docs/architecture.md`, in GitHub's mermaid fences | the demo, linking to the docs |
| a demo that is itself a Quarto site | the docs pages join that site | the demo |
| private | markdown read on GitHub, as above | none: Pages sites are public, even from a private repo |

Every public project has a deployed site, and the repo's website field points at it. Docs read on
GitHub cut the `site` and `pages` jobs from `ci.yml` and the `docs` target from the `Makefile`
(kickoff's copy table), and the plan's docs task writes `docs/architecture.md`, its diagrams in
GitHub's mermaid fences, following the Architecture page's rules below.

## The Quarto site

The plan's site task copies `templates/quarto/` into `website/` and fills it:

| File | What it is | Filled |
|---|---|---|
| `_quarto.yml` | the site, its navbar, Mermaid, the zoom script | `__PROJECT__`, `__SITE_URL__` (the Pages URL), `__REPO_URL__` |
| `index.qmd` | Home: `README.md` included, then the overview | `__PROJECT__` |
| `_overview.qmd` | the overview diagram, one file | `__PROJECT__`, then the project's parts |
| `architecture.qmd` | Architecture: every diagram | the project's diagrams |
| `design.qmd` | Design: a line per wrapper | `__SPEC__`, the spec's file name without `.md` |
| `changelog.md`, `how-we-work.md` | includes of `CHANGELOG.md` and `AGENTS.md` | |
| `_diagram-zoom.html` | click or tap a diagram to open it full-screen | |
| `wrapper.md` | not copied as is: the pattern for each wrapper | `__TITLE__`, `__PATH__` |

**Files stay where conventions put them:** the spec, plans, Q&A pages, council reports and retros
under `docs/superpowers/`; `README.md`, `AGENTS.md` and `CHANGELOG.md` at the root. The site shows
them, never moves them (Dan: "this way we don't worry about things going into the wrong place").

**A wrapper** is a `.md` at the same relative path under `website/` as its source under `docs/`,
holding only a `pagetitle:` and `{{< include /../docs/superpowers/<path> >}}`: a copy of
`templates/quarto/wrapper.md` with `__TITLE__` and `__PATH__` filled. For
`docs/superpowers/plans/<date>-<topic>-phase-1.md`, the wrapper is
`website/superpowers/plans/<date>-<topic>-phase-1.md`, and `__PATH__` is
`plans/<date>-<topic>-phase-1.md`.

- **Every `.md` under `docs/superpowers/` gets its wrapper,** and its line on the Design page, in
  the commit that adds it. CI fails on a doc without one.
- **A `.md`, never a `.qmd`:** tested on Quarto 1.11.5, mirrored `.md` wrappers keep the links
  between the spec, plans and Q&A pages working on the site and on GitHub; a `.qmd` wrapper breaks
  them, and a symlinked folder is ignored.
- **No `{mermaid}` cells under `docs/`:** a `.md` wrapper refuses executable cells, so every
  diagram lives on the Architecture page.

**The pages:**

- **Home:** the README, then the overview.
- **Architecture:** a `.qmd` with every diagram: one overview, in `_overview.qmd`, included on Home
  and never copied, plus a few process diagrams. Built parts solid; planned parts dashed, labelled
  with the phase that brings them. Other pages link here and never draw their own copy.
- **Design:** the wrappers.
- **Changelog** and **How we work:** includes of the root `CHANGELOG.md` and `AGENTS.md`.
- **How-to:** only when a person has steps to do.

**The navbar:** the project's own content pages on the left, How-to among them. On the right, one
`Repo` menu holding Architecture, Design, Changelog and How we work, in that order: they're about
the repo, not the project's main content.

**Links leaving the site,** from the root files and the included docs, are full site URLs or
code-span paths: a `../` link out of the site breaks with no warning.

## The checks

- **`make docs`,** locally: it renders the site, fails on Quarto's "Unable to resolve link
  target", and runs `lychee --offline` over `website/_site` when lychee is installed. Each task's
  mechanical checks include it on a site project (the template's *Each task's loop*, step 2).
- **CI's `site` job,** on every push: every doc under `docs/superpowers/` has its wrapper; the
  render fails on "Unable to resolve link target"; `lychee --offline` over the rendered site,
  pinned. Quarto's version is pinned in the CI template, and the first project's site task checks
  the wrappers on that version.

## The deploy

"GitHub Actions" is the Pages source, set by Dan in kickoff's settings checklist. One CI workflow:
on `main` (a push, or a run by hand through `workflow_dispatch`), the `site` job uploads the
rendered site with `actions/upload-pages-artifact`, and the `pages` job, which runs only once the
`tests`, `leaks`, `shellcheck` and `site` jobs pass, publishes it with `actions/deploy-pages`. Only
the `pages` job has `pages: write` and `id-token: write`, and every checkout keeps
`persist-credentials: false`. There is no `gh-pages` branch, so no history of rendered pages to
clean up after a leak.

## The site task

It adds the `site` and `pages` jobs to `ci.yml` once the wrappers exist, and adds `docs` to the
`Makefile`'s `check` prerequisites.

It closes on CI's render and link check, the `site` job green. Pages publishes only from `main`, so
the live-URL check goes on the phase-end list, for right after the merge: the deployed site serves
the new build ([`phase-end.md`](phase-end.md), step 9).

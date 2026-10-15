# Screenshots from history

## Choosing milestones

Pick 10–15 commits:
- the first runnable UI
- each major feature landing
- each user-requested change that changed the look
- the builder's last commit
- your branch tip

Record the list, with hashes and reasons, in `research/shots-manifest.md`
before shooting.

## Capturing

`scripts/shots-at-commits.mjs` exports each commit with `git archive` into a
temp folder, so the working tree is never touched. It serves the export with a
no-store static server on a free port and opens a fresh browser context at the
viewport you give it.

```bash
node <skill>/scripts/shots-at-commits.mjs \
  --commits <sha>:shell,<sha>:board,<sha>:final \
  --out .playwright-mcp/<slug>-research/shots --viewport 1280x720 \
  --steps .playwright-mcp/<slug>-research/steps.mjs
```

- **Run it from the app's repo.** Playwright must resolve from the current
  directory: install it in that project, or set `NODE_PATH`.
- **Steps module:** an async default export `(page, shot, { sha, label })` that
  drives the app and calls `shot("01-setup")` and so on. Older commits lack
  later screens. The script logs where a commit stopped and moves on, and
  `manifest.json` records shots, step errors and console errors per commit.
- **Wait for the app, not the clock.** Before clicking, wait for the element
  or state you need, because an early click can be swallowed by a load-time
  input lock.
- **Viewport:** the device the app will really run on, such as a TV at
  1280×720 or a phone at 390×844. If the spec doesn't name one, use 1280×720
  and say so in the manifest. One size is enough unless size is a finding.
- **Build steps:** `--build "npm ci && npm run build" --serve-dir dist`.
  Apps with their own backend need their own server started for each export.

## Checking

- **Open every PNG** before referencing it. A filename is a claim. A swallowed
  click leaves a "02-board" that shows the setup screen.
- Name files `<NN>-<milestone>-<screen>.png`. In the manifest, note per
  milestone what is visible and how it differs from the previous one. Those
  notes become the gallery's "What to notice" column.

## Other sources

- **What the builder saw:** copy any screenshots the builder saved itself
  into `assets/<builder>-saved/`, with their file times. For a text-only
  model, show what it worked from instead (accessibility snapshots, computed
  styles).
- **Your pass:** take fresh shots at the target sizes after the fixes, plus
  before/after pairs for each visual fix, from the same steps.

## Budget

Commit a curated set (about 20–30 PNGs, roughly 2–3 MB) under `assets/`. Keep
the full set git-ignored with the research notes.

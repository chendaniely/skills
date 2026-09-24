# TODO

Open work for this repo. Each item carries enough context to pick up cold. Items with a deadline, or someone else waiting on them, go to YouTrack instead.

Every item is mirrored as a GitHub issue ([#1](https://github.com/chendaniely/skills/issues/1)–[#8](https://github.com/chendaniely/skills/issues/8)). When an item is done, tick it here and close its issue.

## Decisions pending

- [ ] **Tag format: fix it together with the vault's Phase 10 frontmatter migration** (#1). In YAML, a space followed by `#` starts a comment, so `Tags: #product_search` parses as an empty `Tags` (checked with PyYAML).
  - **Scale:** most of the vault's notes with frontmatter use this inline form (a clear majority on 2026-09-16). To recount from the vault root: `grep -rlE '^Tags:[[:space:]]*#' --include='*.md' . | wc -l`.
  - **Where it comes from:** the vault's `ze-templates/template-note.md` leaves `Tags:` blank for hand-typed `#tags`, and the periodic-note templates write `Tags: #periodic_note …` directly. Older transcripts carry `Tags: #plaud_capture`. The vault's current audio pipeline already writes a list (`Tags: [transcript]`).
  - **What reads these tags as empty:** the vault's `scripts/lint.py` reads them as empty and never flags them. Bases would too, though no Base filters on tags yet. Obsidian probably does as well. To confirm, search `tag:#product_search` in Obsidian: the product-search notes carry that tag only in frontmatter, so 0 results means Obsidian can't see it.
  - **Skill files using the form:** `capture-conversation` (`template-thinking-note.md`, `template-transcript.md` and the two schema blocks in `SKILL.md`) and `product-search` (`template-product-search.md` and row 1 of the `SKILL.md` section table).
  - **Why it wasn't fixed yet:** the vault's `CLAUDE.md` (## Frontmatter schema) keeps capitalized `Tags` in force until Phase 10. Phase 10 migrates the note writers first (the note template and the audio-pipeline renderer; the vault's `CLAUDE.md` names it), then notes as they are touched. Transcripts are append-only.
  - **Recommended:** extend the existing `tags` entry in Phase 10's target list (vault `CLAUDE.md`, ## Frontmatter schema) to read: "`tags` — lowercase, replacing `Tags`, and always a YAML list (`tags: [product_search]`), never inline `#hashtags`, which YAML reads as empty." Then switch these together: the vault's note and periodic templates, the pipeline renderer (it already writes a list, so only the key's case changes), and both skills' templates and `SKILL.md` examples. Optionally, have `lint.py` warn on `Tags: #…` so the count is tracked.
  - **Alternatives:** convert everything now (the writers plus every note; the `sources/` notes need Dan's explicit OK), or leave it and keep relying on folders.
- [ ] **`allowed-tools` for `email-digest`** (#8; review note 2, left for Dan by the claude-cowork session). The candidate is `allowed-tools: Bash(uv run --directory /Users/dan/git/private/claude-cowork digest.py *)`. It pre-approves the digest commands whenever the skill runs. Scheduled runs already start in claude-cowork, whose machine-local settings (not in git) already pre-approve the digest commands, so this would only skip the prompt when Dan runs the skill from another folder. **Recommended: skip.**

## Follow-ups from the 2026-09-16 review

These findings were confirmed by a second agent but not applied yet.

### catch-up (#2)

- [ ] **Step 1, filing:** give the exact `obsidian move` command (with `vault=`). The CLI exits 0 even on errors, so check stdout for `Error:`, and confirm the file exists at the destination before counting it as moved.
- [ ] **Missing markers or heading:** in step 3, if a weekly rollup file exists without the `rollup:generated` markers, append the marker block at the end and leave the rest untouched. In step 4, if the daily note has no `## Today` heading, insert the block at the top of the note (after any frontmatter), where the daily template puts it, and leave the rest untouched.
- [ ] **Step 4, missing daily note:** if today's daily note doesn't exist yet, create it from the vault's daily template, as `ootd` and `capture-conversation` do. Describe the position as "top of the note" instead of "above `## UBC`".
- [ ] **Step 1, folder map:** the example (`zettelkasten/<topic>/`, `zettelkasten/people/`) is only partly current. Most topic folders are still under `zettelkasten/` (for example `product_searches/`), but `ubc` and `fashion` moved to `wiki/topics/`, and Phase 10 moves the rest gradually. Add `wiki/topics/<topic>/` to the example, or drop the example and rely on the vault's `CLAUDE.md`.
- [ ] **Step 1, outfit photos:** leave an inbox note holding an outfit photo that no OOTD note references in place, and flag it for `ootd`. `ootd` only looks for photos in the daily note, `inbox/` and recent attachments.

### capture-conversation (#6)

- [ ] **Plaud recordings:** if a synced transcript already exists (the vault's `CLAUDE.md` says where), link it as the verbatim source and use its speaker labels instead of transcribing again. The skill never mentions Plaud today.
- [ ] **Someone else's share link:** `references/claude-chat-sources.md` says to reconcile the turn count, but no JSON is available to count against. Define the check, for example rendered message blocks against the speaker headers written.
- [ ] **Open Threads:** `SKILL.md` still ends with `## Open Threads (v0)` (quick-capture vs deep-distill modes, diarization, no official chat-history API). That is a development backlog, not instructions. Move the bullets into this file and delete the section.
- Tag format: see "Decisions pending".

### clothing-inventory (#3 for `aliases` and the measurements heading; #4 for the rest)

- [ ] **`aliases`:** the "any wrong-but-intuitive name" allowance (frontmatter deltas table) conflicts with `ootd`'s "never invent `aliases`". Limit aliases to forms the label, the vendor or the owner supplied.
- [ ] **Measurements heading while `size` is empty:** `size` may now stay empty until the size tab is read, but section-table row 8 and the template still use `## Measurements — size <X>` with the owned size bolded. Say what the heading and table show when `size` is empty, for example a plain `## Measurements` heading, no row bolded, and the Open-questions checkbox.
- [ ] **Template key list:** the template restates the whole key list, which `inventory/Inventory.md` owns ("Do not restate it"). Reduce it to the garment deltas plus a comment pointing to Inventory.md, or add a comment saying to diff against Inventory.md before writing.
- [ ] **Non-Japanese labels:** only JIS L0001 is covered. Name the standard for North American labels (ASTM / CAN-CGSB) and turn the Japanese-only label and measurement rows into placeholders. Also drop two leftovers from the first garments: the "7-row table" wording in section-table row 5, and the "before recommending anyone buy a lamp" aside in `## Photos`.
- [ ] **Placement line:** "*Nth garment in the inventory*" (section-table row 4) is required but stops meaning much as the inventory grows one note at a time through `ootd`. Make it optional.

### ootd (#5 for testing; #3 for the listing line and duplicated rules)

- [ ] **Re-run the GREEN test.** Commit 5bb92bf changed `ootd` (the resolve step and the offer-first trigger) and `clothing-inventory`, which `ootd` runs as a sub-skill (blank size, gated self-edits, face-free crops). Nobody has re-run the test yet. No fixture is left under `/tmp`, so rebuild one from the recipe at the top of `tests/check_green.py`, run `tests/prompt.md`, then grade. Do this before the harness fix below, so a failure points at the skill edits and not the grader.
- [ ] **Listing line:** a piece confirmed from an outfit photo usually has no listing yet, but `clothing-inventory` calls the listing line non-negotiable. Add a "No official listing yet" path there, or state the exception in `ootd` step 7.
- [ ] **Rules written twice:** the rules appear in both `SKILL.md` and the `template-ootd.md` comments, and they have drifted. Row-contract rule 2 ("a wikilink **iff** a note already exists…") doesn't allow linking a note created this run after the owner confirmed owning the piece, but the template does. Fix rule 2 and keep each rule in one place.
- [ ] **Test harness:** `tests/check_green.py` hard-codes the fixture's broken-link baseline (302). Compute it at the fixture's reset commit instead. Also document how to run RED without removing the global `~/.claude/skills/ootd` link, for example with a separate Claude config directory.

### product-search (#7)

- [ ] **OOTD hand-off:** when a search starts from an OOTD `Worth buying` row, copy the role, label and pairs-with pieces into the brief as criteria and link the OOTD in `## Sources`. Once the item is bought, point its inventory note's `evaluation:` at the search note.
- Tag format: see "Decisions pending".

## Later

- [ ] **Revisit the flat layout** when any of these happens: the repo reaches about 20–30 skills, or folders that aren't skills appear (then move skills under `skills/`). The marketplace manifest was added 2026-09-23. See `CLAUDE.md`.

## Declined in the 2026-09-16 review

Checked and left alone on purpose. Don't re-raise these without new evidence.

- **Real, but not worth changing:**
  - `capture-conversation`: the stale HF_TOKEN / diarization wording and the DSCI 521 provenance paragraph.
  - `catch-up`: the dated Plaud notes, and copying the `## Email` checklist into `## Today`.
  - `clothing-inventory`: the hard-coded vault paths.
  - `ootd`: the photo-removal gate, the hard-coded photo script and principle numbers, and the session-JSONL photo route.
  - `creating-ultra-crew-guides`: the shortened Google Docs export URL.
- **Refuted:**
  - `capture-learning-moment`: the fake IP being "too real".
  - `email-digest`: paging offsets and hard-coded paths.
  - `product-search`: needing a browser boundary.
  - `ootd`: buy labels going stale, and a tag conflict with `product-search` (the tag format itself is under "Decisions pending").
  - `creating-ultra-crew-guides`: needing a fixed output format.

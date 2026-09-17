---
name: ootd
description: 'Use when the vault owner shares a photo of an outfit they are wearing — pasted into a note, attached in chat, or given as a file path — with any phrasing of "ootd", "outfit of the day", "rate this outfit", "what do you think of this fit", "what am I wearing". If an unlogged outfit photo turns up in the daily note or inbox during another task, mention it and offer to log it; start only after the owner says yes or types /ootd. Assumes an Obsidian-style vault with a clothing inventory folder and a fashion topic.'
---

# Ootd

## Overview

**An OOTD note is a dated observation about the owner, not a photo caption.** The photo is evidence. The note becomes a wear record (every linked inventory item gains a backlink), a scored judgment made against the owner's own stated direction, and a delta in the memory note so the next judgment starts further along.

**Core principle: the closet is the unit of analysis, not the outfit.** Everything is judged against what the owner actually owns — the inventory items folder is the **only** ownership authority — and where they said they are heading (the memory note's `## Direction`), never against a runway or a menswear rulebook. The owner is a self-described beginner who wants the reasoning taught, with sources: every verdict names the principle it applies and where it is written.

**Violating the letter of the gates is violating their spirit.** An unconfirmed match written as a link, or an item note created from a photo alone, corrupts the one record the log cannot un-know later.

## When to use

- The owner shares an outfit photo and says any form of "ootd" / "rate this" / "thoughts?"
- During another task, an outfit photo sits in the daily note or inbox as a bare `Pasted image …` embed no OOTD note references → mention it and offer to log it; **start the run only after the owner says yes or types `/ootd`**
- The owner asks which visible pieces are not in the inventory yet

**Not for:** one garment's labels with no outfit (`clothing-inventory`); pre-purchase research (`product-search` — an OOTD only *links* such a note); product photos or other people's outfits.

## Resolve the vault first

Read the vault's `CLAUDE.md` and resolve: the OOTD log folder + filename pattern · the inventory items folder, its conventions note and photo-filing script · the attachment folder and photo-normalizing script · the memory note and the hub note holding hard personal specs · the daily-note path and log heading · the TODO surface and its fashion heading · the lint command. **Undeclared → ask and use the answer for this run; propose the `CLAUDE.md` line in the step-14 report and write it only after the owner agrees.**

*Illustrative only — one vault's values (2026-09):* `wiki/topics/fashion/log/YYYY-MM-DD-ootd.md` · `inventory/items/<Item>/<Item>.md` + `inventory/Inventory.md` + `python3 scripts/file-inventory-photos.py "<Item>" --kind mine` · `ze-files/ootd/` via `uv run scripts/ootd_photo.py` · `wiki/topics/fashion/reference/Personal Style.md` + `Fashion.md` → `## Personal specs` · `000-periodic_notes/daily/YYYY/MM/YYYY-MM-DD.md` → `## Log` · `TODO.md` → `## Fashion` · `uv run scripts/lint.py`.

## Write scope (non-negotiable)

A run creates or edits **only**: the normalized photo · the source note's embed (re-pointed) · the OOTD note · the memory note · the wear-date daily note's `## Log` (and today's, if different) · TODO lines under the fashion heading · **confirmed** inventory item notes and photos inside their folders · one TODO-completed line when a worn-shot item closes. **Nothing else** — not `CLAUDE.md`, `README.md`, the inventory conventions note, a bases README, a hub's conventions, a version stamp, `## Today`. The hub's personal-specs table changes only through Gate 2. A convention gap noticed on the way is *reported* in the closing summary and fixed only after the owner says so.

## The section contract

Write these sections **in this order**; omit one only where its row says so.

| # | Section | Contains |
|---|---|---|
| 1 | frontmatter + H1 | Every template key present. H1 `# OOTD YYYY-MM-DD — <occasion>`; occasion unknown → key left empty, H1 `# OOTD YYYY-MM-DD` |
| 2 | Verdict line | `**N/10 — <verdict clause>.** <the single change that would add a point>` |
| 3 | Photo | `![[YYYY-MM-DD-ootd-01.jpg]]` full width + one italic caption: EXIF time · occasion · weather · provenance |
| 4 | `## Owner's words` | **Only if** the owner said something about *this outfit* beyond the trigger. Verbatim blockquote. The instruction that started the run is not owner's words; taste statements go to the memory note's `## Journal` |
| 5 | `## Worn` | One row per piece — the row contract |
| 6 | `## Advice` → `### The outfit as a whole` | 3–6 sentences: silhouette from across the room · formality step and which piece set it · how it lands against the **quoted** `## Direction` line · what a stranger notices |
| 7 | `### What's working` | Bullets: observation → principle (cited) → why it matters for this owner |
| 8 | `### What's not working` | Same shape. "Nothing" is invalid below a 9 |
| 9 | `### Make it better` | (a) `**Try next time (free, from the closet):**` one change with owned pieces · (b) **Swap** table — closet-first, targets ✅ linked or ❓ "not in inventory yet — confirm and I'll add it" · (c) **Worth buying** table — optional; every row meets the buy contract |
| 10 | `### Scores` | Fit · Proportion · Color · Formality · Cohesion (capsule) · **Overall**; columns Score · Anchor (why not ±1) · Calibration |
| 11 | `## Carried to Personal Style` | **Required.** One line per delta made to the memory note; "nothing new" is valid |
| 12 | `## Open questions` | **Only** what Gate 1 left unanswered; each `- [ ]` names the key or row it fills |
| 13 | `# References` | memory note · wear-date daily note · principles note · hub personal specs · calibration OOTDs · any product-search note spun out |

Everything above `## Advice` is scannable in ten seconds.

## The row contract (non-negotiable)

```
| Jacket   | [[UNIQLO Navy Blazer]]                | ✅ | sets the register — the dressiest piece here |
| Shoes    | white leather sneakers, make unread   | ❓ | pulls it one step down — confirm the make and I'll add it |
| Trousers | charcoal tapered chinos               | ⛔ | no trouser notes in the inventory yet → TODO |
```

1. **Slot** — head · neckwear · outerwear · top · base layer · bottom · belt · socks · shoes · bag · watch/accessories. Unidentifiable → still a row (❓). Out of frame → **one** row for the unseen region ("below frame: shoes/socks — ❓"). A missing row makes `unmatched` lie.
2. **Piece** — a wikilink **iff** a note already exists in the inventory items folder **and** the owner confirmed the match at Gate 1. Otherwise plain text describing what is visible. **An unconfirmed candidate is named in plain text everywhere in the OOTD note** — Worn, Open questions, captions — because any wikilink from the note is a backlink on the item, and backlinks are its wear history. A catalog or research note is never the link target.
3. **Marker** (written note): ✅ confirmed and linked · ❓ can't tell / unconfirmed · ⛔ not in inventory. ⚠️ "likely, confirm" exists only at the gate.
4. **Role clause** — what the piece does in *this* outfit, not what it is.

`items:` lists exactly the ✅ rows (`items: []` when there are none); `unmatched:` counts the ❓ and ⛔ rows. **A note created this run from a photo alone is not an inventory item and changes neither number.**

## The buy contract

A `Worth buying` row is a **role, never a product** — `mid-grey wool crewneck, fine gauge`; no brand, model, price or URL; research lives in a `product-search` note the Research column links once it exists. Columns: **Role** · **Label** (`capsule core` | `fun piece`) · **Pairs with** — ≥ 3 owned pieces as linked inventory notes (❓ pieces may be listed, do not count) *or* ≥ 2 recurring occasions from the log or `## Direction` · **Research** (`—` or link). A row that cannot fill Pairs-with is not a suggestion. Every row written increments its role in the memory note's `## Wardrobe gaps`.

## Scoring

One scale, every dimension: 3 actively wrong · 5 fine, forgettable · 7 works, one nameable (usually free) fix from good · 9 photograph-worthy · 10 only for "better than every prior 9". The Anchor cell answers "why not one higher *and* why not one lower". Dimensions follow the principles note (fit, proportion, colour/contrast, formality, cohesion; fabric is not judged from a photo); **cohesion is the capsule test** — count, from the inventory, the *other owned* pieces each item recombines with; colour is "provisional" while the hub's contrast level is ❓, formality while the shoes are unseen. **Overall is holistic, not a mean**; if it differs from the rounded mean by more than 1, the verdict line says why. **Calibration:** read the memory note's `## Score calibration` and the three most recent OOTDs' `### Scores` before scoring; the Calibration cell names a same-score prior note with one clause of comparison, or "uncalibrated — N prior entries" while N < 3. A note landing on an empty 6/7/8 slot with a clear reason becomes that anchor; anchors are annotated, never re-scored.

## Finding the photo

1. A path in the message. 2. Today's daily note (or the named wear date's): the first image embed no OOTD note references. 3. `inbox/*.md`, same test. 4. The attachment folder: unreferenced images under 24 h old. 5. This session's chat attachment — the newest `image` block in the session JSONL, via the script's `--from-jsonl`. 6. None → "Paste the photo into today's daily note and say ootd, or give me a path." Ties → show basenames and mtimes, ask. **Read the image back first**: a label, a product shot or someone else's outfit is not an OOTD — say so and stop. Another person in frame → stop and ask (file as-is, the owner crops, or skip); never describe them.

## Steps

1. **Resolve the vault.** Read the memory note (`## Direction`, `## Rules of thumb`, `## Wardrobe gaps`, `## Score calibration`), the hub's personal specs and the principles note. No memory note → create it from `template-personal-style.md`; `## Direction` needs one verbatim quote — this session's words, or ask.
2. **Find the photo**; read it back.
3. **Normalize it**: `uv run scripts/ootd_photo.py <src> --replace-in <note> [--date …] [--slug …]` — dry-run first; one line to the owner naming what is converted, re-pointed and removed (a "no" adds `--keep-original`). Its `exif_date:` line is `date`; none → the date of the note it was pasted into; neither → ask. `date ≠ today` → say so.
4. **Read the outfit before opening the inventory**: every piece by slot with colour, material read and fit read.
5. **Match against the inventory items folder only**: read each candidate's frontmatter (`category`, `color`, `make`, `model`, `size`) and its `## Photos`. Build the proposal table with ✅ ⚠️ ❓ ⛔. A catalog hit is an identification *hint*, never ownership.
6. **GATE 1 — confirm matches.** Show the proposal table (below) and stop. Links are written only for rows the owner confirms; a partial reply confirms only the rows it names; unnamed ⚠️ rows become ❓. **Owner absent → the default is no link and no new note**: plain-text rows, `## Open questions`, TODO lines. For ⛔/❓ rows offer: **(a)** photos or details → create the note · **(b)** a name → search with `curl`/`WebFetch` only, show *name + URL + image*, ask "this one?" before creating · **(c)** skip → plain-text row + TODO line. Also ask occasion (a word or two) and optional weather.
7. **Create item notes only for pieces the owner confirmed owning** — garments via **REQUIRED SUB-SKILL `clothing-inventory`**; bags, shoes, belts and accessories per the inventory conventions note. Never invent `aliases`, `make`, `size` or a listing; blank beats guessed. A confirmed item whose folder has no `-mine-` photo gets a **face-free crop** of the normalized JPEG (the garment region only), filed with the photo script as `--kind mine`, detail `worn-YYYY-MM-DD`; set `photo:` only if it was empty.
8. **Judge.** Read the three most recent OOTDs and the calibration anchors; write `## Advice` per the contract — quote the `## Direction` line judged against, cite a principle per bullet, closet-first swaps, buys per the buy contract, scores per `## Scoring`.
9. **Write the OOTD note** from `template-ootd.md` (strip the comments); `items` = ✅ rows, `unmatched` = ❓ + ⛔ rows, `photo` = the JPEG. A second outfit that day → `YYYY-MM-DD-ootd-<slug>.md`; photos continue the day's numbering.
10. **Update the memory note** (Claude's lane, no gate): dated, backlinked bullets under `## What works` / `## What doesn't`; a `## Wardrobe gaps` row incremented or added per buy role; a `## Journal` entry **only if** the owner said something about taste this session (verbatim, annotation beneath); an empty calibration slot filled if this note lands on it.
11. **GATE 2 — personal-spec proposal (conditional).** Evidence toward a ❓ spec on the hub (a contrast-level read tallied under `## Experiments & open questions` — propose only after ≥ 3 consistent reads; the inventory grew) → propose the one-line write and wait for yes. **Proportions come only from the owner's tape measure; a photo never proposes them.** No evidence → skip.
12. **Link it in.** Wear-date daily note (create from the vault's daily template — every heading — if missing): `- [[YYYY-MM-DD-ootd]] — <occasion>, N/10: <one clause>` under `## Log`, `## Today` untouched; run on a later day → log in today's note too. One TODO line per ❓/⛔ row under the fashion heading with a backlink; a TODO asking for a worn shot of an item filed this run → the completed log, dated.
13. **Verify.** Run the vault's lint and diff its named lines against the run before: zero orphan attachments, zero *new* broken links, tags a list, one pattern tag. Read the note back: a row per piece from step 4, four columns per buy row, `## Carried to Personal Style` present.
14. **Maintain the system.** Report: photo path, re-point and removal, files written, TODO lines, gate answers, lint result. Then ask whether the run revealed a convention gap — a slot the template lacked, a marker that did not fit, a folder `CLAUDE.md` did not declare. If yes, say so; update the vault's `CLAUDE.md` **and this skill** once the owner agrees.

**Gate 1 display:**

```
**Matches — confirm before I write any links**
✅ certain · ⚠️ likely, confirm · ❓ can't tell from the photo · ⛔ not in inventory
| Slot | What I see | Match | Confidence |
| Top | white washed-linen shirt, sleeves pushed | Test White Linen Shirt | ⚠️ — collar reads as a hood; is it this one? |
| Belt | slim tan leather, silver buckle | — | ⛔ no belt notes in inventory |
Reply per row — "yes" · the right item · "not in inventory: <what it is>" · "skip".
For ⛔/❓ rows: photos or details, name it and I'll search, or skip (plain text + TODO). Occasion? Weather (optional)?
```

A yes is "yes" / "correct" / "all good" / a row-level correction naming the item. Route (b) sub-gate: `Found: <name> — <url> — <image>. This one? (yes / no, it's… / skip)`.

## Rules

- **Ownership comes from the inventory folder alone.** Prevents a researched bag being linked as worn.
- **Links and item notes are written after the yes; `unmatched` counts ❓ and ⛔ rows, full stop.** Prevents a guessed match polluting wear history via backlinks, and the queue view emptying by definition instead of by catalogue work.
- **Every piece gets a row; stay inside the write scope.** Prevents belt, bag and shoes silently dropping out, and one outfit becoming a governance edit.
- **Quote the Direction you judge against; cite the principle; scores carry an anchor and a calibration link.** Prevents advice that would be the same for anyone and a 7 drifting between months.
- **Closet-first; a buy carries pairs-with and a label; research goes to a product-search note.** Prevents the single-purpose purchase the owner's Direction exists to stop.
- **Hard facts live once, on the hub; the owner's words are quoted, never paraphrased.** Contrast from photos over several runs, proportions from a tape, wardrobe from the inventory.
- **Photos are normalized, stripped, re-pointed; inventory crops exclude the face; web identification uses `curl`/`WebFetch`, never the owner's live browser.**

## Rationalizations from the baseline run — all wrong

| Excuse | Reality |
|---|---|
| "Every named piece now has an item note, so `unmatched: 0`" | A stub written from a photo is ownership asserted by Claude. Plain-text row, count it, TODO it |
| "I documented the choice" | A documented wrong write is a wrong write with a footnote |
| "The owner asked for photos in the inventory notes" | For pieces the owner *confirmed*. Confirmation is the whole gate |
| "The owner said proceed with my best default" | The default is no link and no note — never the optimistic one |
| "Standing duties require same-session doc updates" | An OOTD entry changes no structure; `CLAUDE.md` is outside the write scope |
| "The candidate/catalog note is the closest thing to an item page" | Research is not possession |
| "`## Today` was empty, so I filled it" | Another skill owns it |

## Common mistakes

| Mistake | Fix |
|---|---|
| Item note created for an unconfirmed piece | Delete it before anything links it; plain-text ⛔ row + TODO |
| Note named `YYYY-MM-DD.md` (collides with the daily note) | `YYYY-MM-DD-ootd.md` |
| `Tags:` string, or two pattern tags | Lowercase list `[fashion, log]`, one pattern tag |
| "8/10, looks great" | Six rows, Anchor and Calibration columns |
| "Consider a navy blazer" | Role + label + ≥ 3 linked owned pieces or ≥ 2 occasions, or omit |
| Brands, prices, URLs inside the OOTD note | Name the role; spin research into a product-search note |
| Memory note restates height or contrast · "you look about 5'10"" | Link the hub; tape only, photos never propose measurements |
| Invented `aliases` or an `occasion` on a new note | Only words the owner or a vendor page supplied; unknown stays empty |
| Pasted PNG left beside the JPEG | `--replace-in`; report the removal |

## Template

Start from `template-ootd.md` for every OOTD note; create the memory note once per vault from `template-personal-style.md`, then only append to it. Strip template comments when writing real notes. Every run ends with step 14 — the skill is expected to evolve, which is why it lives in a git repo.

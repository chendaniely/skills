---
name: product-search
description: Use when creating or updating a product-search, product-comparison, or buying-guide note in a markdown knowledge vault — any note whose reader is deciding what to buy and will want to click through to candidates.
---

# Product Search Notes

## Overview

**The reader is shopping, not studying.** They open the note to answer *"what do I buy, what does it look like, where do I click"* — and only then *"why".* A note that opens with context and buries the verdict is the wrong shape, however good the research.

**Core principle: verdict first, evidence below.** Sections run in decreasing order of "how often will I need this", never in the order the research happened.

## The section contract

Write these sections, **in this order**. Omit one only if it is genuinely empty.

| # | Section | Contains |
|---|---|---|
| 1 | *(frontmatter + H1)* | `Tags: #product_search`; add `Decision` / `Decided` / `Rationale` once settled |
| 2 | **Verdict line** | One line, directly under the H1: status, date, and the current pick **with its price** |
| 3 | `## ⭐ Shortlist` | **The top thing on the page.** Ranked table, 3–6 rows, every row image + link + price + pros + cons |
| 4 | `## Do this` | Numbered actions, ≤6, each starting with a verb. Free/cheap tests come first |
| 5 | `## The brief` | The need, then hard requirements as a checklist or table |
| 6 | `## Fit facts` | Measurements/constraints table, with a confidence or source column. ⭐ **If the search is gated on a space the owner already has, an owner reference photo of that space is required here** — and if none exists yet, asking for it is an action in `## Do this` |
| 7 | `## Full field` | Every serious candidate, same row contract as the shortlist |
| 8 | `## Why` | Findings, rationale, physics, tradeoffs — the deep material |
| 9 | `## Ruled out` | Table: candidate + one-line reason |
| 10 | `## Open questions` | `- [ ]` checkboxes |
| 11 | `## Sources` | Provenance, sweep dates, method notes |

**Everything above `## Why` should be scannable in under a minute.**

## Tables adapt to the search

**The requirements define the columns.** There is no fixed schema beyond image · name · price — every other column is a criterion *this* search is optimising for, so a reader can see match-or-miss without reading prose.

- **One column per criterion that discriminates.** Bag search → capacity · laptop fit · weight · material. Light search → lux at working distance · CRI · CCT range · mount. Table search → height · footprint · material · weather.
- ⭐ **Drop any column every candidate passes.** A column where all rows say ✅ is decoration — state it once in the brief as an entry condition and reclaim the width for something that separates candidates.
- **Order columns by how much they decide.** The criterion that actually picks the winner goes immediately after price.
- **Put the decisive number in the cell, not a rating.** `680 lux (6.8×)` beats `good`.

### Match markers — one per cell

| Marker | Means |
|---|---|
| ✅ | meets the criterion |
| ⚠️ | **near miss — always show the value and the gap** |
| ⛔ | fails a **hard** requirement |
| ❓ | **not published** — never guess, and never let a blank imply a pass |

## Hard vs soft requirements

**Default every requirement to soft.** Mark one hard only when missing it makes the product *unusable*, not merely worse. Say which is which in the requirements table.

| | Effect of a miss |
|---|---|
| **Hard** | Disqualifying → move to `## Ruled out` with the number |
| **Soft** | ⭐ **Stays in the table**, marked ⚠️ with the gap quantified — and can still win overall |

- ⭐ **A soft miss is a data point, not a rejection.** "≤50 cm" does not kill a 53 cm product; it makes it *53 cm, 6% over*. Show the number and let the reader judge.
- **Never silently drop a near miss.** If a candidate is excluded, the exclusion is a sentence with a number in it. A reader must never wonder whether an obvious product was considered.
- **Recommend outside the stated range when the overall case is better** — and say plainly that you are doing so, with what it costs. Self-imposed numbers are a search heuristic, not a spec the world agreed to.
- **Ranges in the brief are the centre of a band, not a wall.** Where a tolerance is meaningful, say it: "≤50 cm (soft, ~±15%)".

⚠️ **The failure this prevents:** mechanically applying a number invented early, before the field was known, and dropping the best candidate for missing it by a few percent — invisibly, so nobody can audit the decision.

## The row contract (non-negotiable)

**Every row naming a product, in every table, carries all four:**

```
| ![[image.jpg\|150]] | **[Product Name](https://buy-here)** | **$134** | specs · pros | ⚠️ cons |
```

1. **Image** — embedded, sized 120–150 in tables
2. **Name, hyperlinked** to somewhere it can be bought or specced
3. **Price** with currency, plus an as-of date somewhere on the page
4. **Enough spec to judge** without clicking

A row missing the image or the link is incomplete — the reader is browsing, and a name they cannot see or click costs them a search.

## Rules

- **Tables and bullets over prose.** Prose only where reasoning genuinely needs sentences (`## Why`). No paragraph where a table works.
- **Rank the shortlist** and mark the single pick ⭐. Ties are a failure to decide — say which wins and on what.
- **Pros/cons: ≤3 each, phrases not sentences.** Lead with the discriminating one.
- **Prices are perishable.** Always stamp "read YYYY-MM-DD — re-verify at checkout". Note the retailer, and prefer a local/in-stock channel when one exists.
- **Images live in the vault**, not hotlinked: download to the attachment folder, kebab-case descriptive filename (`amaran-ace-25c.jpg`), embed with `![[name.jpg|150]]`. ⚠️ Inside a table the pipe must be escaped: `\|`.
- **Verify the photo shows the product.** Read the image after downloading — listings mislabel, and a folding lamp photographed folded reads as a straight bar.
- **A photo shows one *state* of a moving thing.** Before generalising from what surrounds an object in a photo, establish which state it is in. A cabinet door photographed *open* shows a room the closed door hides — an aesthetic constraint read off that background can be entirely spurious. Geometric inferences from a photo usually survive; contextual ones need the state confirmed first.
- **Ask what else it would get used for.** A candidate that earns its keep beyond the one job can beat a better single-purpose winner, and the owner usually knows this before the research does. Record second-use value as an explicit criterion rather than letting it arrive as a late surprise.
- **When the pick has a precondition, put the precondition in the verdict line.** "Works if X" is a different recommendation from "works" — and if X is free (a light switch, a setting), the conditional pick is often still right. Quantify both sides so the reader can judge the risk of forgetting.
- **Unknown is a value.** Write "not published" rather than estimating. Mark derived numbers as derived and never rank them against measured ones.
- **Supersede by annotation, never deletion.** When a finding is overturned, mark the old one and say what changed. The page should show how the answer moved.

## Common mistakes

| Mistake | Fix |
|---|---|
| Shortlist below the fold, under context | Verdict line + shortlist first; context is section 5 |
| Product named in prose with no image or link | Apply the row contract — every mention gets both |
| Spec dump with no verdict | Rank, mark ⭐, say what would change the pick |
| Prices with no date | Stamp the read date; they go stale in weeks |
| Long paragraphs of rationale up top | Move to `## Why`; keep the top scannable |
| Candidate table with a blank image cell | Download it, or say why none exists |

## Template

Start from `template-product-search.md` in this directory.

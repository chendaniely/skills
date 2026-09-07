---
Created: {{YYYY-MM-DD HH:MM — when this note is written}}
Modification date: {{Dayname YYYY-MM-DD HH:MM:SS}}
tags:
  - fashion
  - log
# the topic tag + exactly one pattern tag (log); a YAML list, never a string
private: true
# photos of the owner never leave the vault — this is the export-exclusion marker
date: {{YYYY-MM-DD — wear date: EXIF capture date, else the date of the note it was pasted into, else asked}}
occasion: {{one or two words in the owner's terms — teaching · dinner out · errands — asked at Gate 1; unknown → leave EMPTY, never a placeholder word, and drop the "— occasion" clause from the H1}}
weather: {{optional — omit the key entirely if unknown}}
items:
  - "[[{{Inventory Item Note}}]]"
# `items: []` when no row is ✅. ONLY rows confirmed ✅ at Gate 1; each must be a note that already existed in the inventory items
# folder, or one the owner confirmed owning this run. Never a catalog note, never a photo-only stub.
# Every entry gives that item a backlink = its wear history.
unmatched: {{integer — the count of ❓ + ⛔ rows in ## Worn; a note written from a photo alone does not lower it}}
photo: "[[{{YYYY-MM-DD-ootd-01.jpg}}]]"
# the normalized JPEG (EXIF/GPS stripped), never the pasted original — the Bases card cover
score: {{1–10 integer, holistic; if it differs from the rounded mean of the five below by more than 1, the verdict line says why}}
score_fit: {{1–10}}
score_proportion: {{1–10}}
score_color: {{1–10}}
score_formality: {{1–10}}
score_cohesion: {{1–10 — the capsule test: how many OTHER owned pieces each item recombines with}}
verdict: "{{one line — identical to the line under the H1}}"
---

# OOTD {{YYYY-MM-DD}} — {{occasion}}

**{{score}}/10 — {{verdict clause}}.** {{One clause: the single change that would add a point.}}

![[{{YYYY-MM-DD-ootd-01.jpg}}]]

*Shot {{YYYY-MM-DD HH:MM}} (EXIF) · {{occasion}} · {{weather}}. Owner photo, filed by the vault's photo script (EXIF/GPS stripped; pasted original re-pointed and removed). Full width — evidence, not a product shot.*

<!-- CONDITIONAL — include ONLY if the owner said something about THIS outfit beyond the trigger
     phrase (where it was worn, how it felt, what they were going for); omit the section otherwise.
     The instruction that started the run is not owner's words. Verbatim, typos and all, in a
     blockquote. Statements about taste or direction in general go to Personal Style → ## Journal
     and are listed under ## Carried to Personal Style. -->
## Owner's words

> {{verbatim}}

## Worn

<!-- ROW CONTRACT — every row carries all four: slot · piece · marker · role clause.
     One row per VISIBLE piece, top to bottom:
       head · neckwear · outerwear · top · base layer · bottom · belt · socks · shoes · bag · watch/accessories.
     A piece you cannot identify is still a row (❓). Pieces out of frame share ONE row for the unseen
       region — "below frame: shoes/socks" — marked ❓ and counted once in `unmatched`.
     Piece = wikilink IFF a note already exists in the inventory items folder AND the owner confirmed
       the match at Gate 1 (or confirmed owning it and the note was created this run).
       Otherwise plain text describing what is visible. A catalog/research note is never the link target.
     Markers in the WRITTEN note: ✅ confirmed, linked · ❓ can't tell / unconfirmed → plain text + TODO line ·
       ⛔ not in inventory → plain text + TODO line.
     ⚠️ "likely, confirm" is a PROPOSAL marker shown at the gate; it never appears here.
     Role clause = what the piece does in THIS outfit, not what it is. -->

| Slot | Piece | Match | Role in this outfit |
|---|---|---|---|
| {{Jacket}} | [[{{Item Note}}]] | ✅ | {{sets the register — the dressiest piece here}} |
| {{Shoes}} | {{white leather sneakers, make unread}} | ❓ | {{pulls it one step down}} — confirm the make and I'll add it |
| {{Trousers}} | {{charcoal tapered chinos}} | ⛔ | {{…}} — no trouser notes in the inventory yet → TODO |

## Advice

<!-- ORDER IS FIXED: the whole → working → not working → make it better → scores.
     Judge against the owner's own words in Personal Style → ## Direction — QUOTE the line you judge against.
     Not against a runway, a "rules of menswear" list, or another person's colouring.
     Every observation names the principle it applies and where it lives,
       e.g. ([[Learning Fashion]] → 4: formality is set by the lowest element).
     The reader is a self-described beginner who wants the reasoning taught, with sources. -->

### The outfit as a whole

{{3–6 sentences: the silhouette read from across the room · which formality step it sits at and which piece set it · how it lands against the quoted Direction line · the one thing a stranger notices. Principles cited inline.}}

### What's working

- {{observation}} → {{principle, cited}} → {{why it matters for this owner}}

### What's not working

- {{observation}} → {{principle, cited}} → {{consequence}}

### Make it better

**Try next time (free, from the closet):** {{one change using pieces already owned — the highest-leverage fix.}}

<!-- CLOSET-FIRST. A swap target is ✅ (a linked inventory note) or ❓ (plain text + "not in inventory yet —
     confirm and I'll add it"). The inventory is still being built, so the owner may own it uncatalogued —
     say so as a question, never as a fact. A catalog note is never a swap target. -->

| Swap | For | Why (principle) | In inventory? |
|---|---|---|---|
| {{piece}} | [[{{Item Note}}]] | {{…}} | ✅ |
| {{piece}} | {{dark brown leather loafers}} | {{…}} | ❓ not in inventory yet — confirm and I'll add it |

<!-- WORTH BUYING — optional table; when present EVERY row fills all four columns.
     Role, not product: "mid-grey wool crewneck, fine gauge" — no brand, model, price or URL here, ever.
       Research happens in a product-search note (product-search skill) that the Research column links to
       once it exists.
     Pairs with: ≥3 owned pieces as linked inventory notes (❓ pieces may be listed, do not count)
       OR ≥2 recurring occasions (values of `occasion` seen in the log, or contexts named in Direction).
       A row that cannot fill this column is not a suggestion — leave it out.
     Label: `capsule core` (recombines widely) or `fun piece` (one per outfit, carried by the core) —
       the owner's Direction is "capsule wardrobe with some fun pieces".
     Then increment the role's row in Personal Style → ## Wardrobe gaps (skill Step 10). -->

**Worth buying** — roles, not products:

| Role | Label | Pairs with (≥3 owned, linked · or ≥2 occasions) | Research |
|---|---|---|---|
| {{mid-grey wool crewneck, fine gauge}} | capsule core | [[{{A}}]] · [[{{B}}]] · [[{{C}}]] | — (say "research it" → product-search note) |

### Scores

<!-- ANCHORS, same scale for every dimension:
       3 = actively wrong · 5 = fine, forgettable · 7 = works, one nameable fix from good · 9 = photograph-worthy.
       Even numbers interpolate. 10 is reserved for "better than every prior 9".
     Anchor column = why not one higher AND why not one lower.
     Calibration column = a prior OOTD scoring the same on that dimension — from Personal Style → ## Score
       calibration or the three most recent log notes. Write "uncalibrated — N prior entries" while fewer than 3 exist.
     What each dimension judges ([[Learning Fashion]] numbering):
       fit        — shoulder seam, sleeve and hem length, trouser break, pulling/pooling (→ 1)
       proportion — volume top vs bottom, hem and waist placement, the silhouette read; what the bag does to it (→ 2)
       color      — palette count, warm/cool agreement, leather/metal agreement, the owner's contrast level
                    if known — if the hub still says ❓, write "provisional" in the anchor cell (→ 3)
       formality  — steps between highest and lowest piece; the level is set by the lowest; fit to occasion (→ 4)
       cohesion   — the CAPSULE test: for each piece, how many OTHER owned pieces it recombines with (count them
                    from the inventory); does a fun piece have a core to hold it; does anything here go with
                    nothing else owned (→ 6)
     Fabric is not scored — not judgeable from a photo. -->

| Dimension | Score | Anchor — why not ±1 | Calibration |
|---|---|---|---|
| Fit | {{n}} | {{…}} | {{same as [[YYYY-MM-DD-ootd]] (n) — …}} |
| Proportion | {{n}} | {{…}} | {{…}} |
| Color | {{n}} | {{…}} | {{…}} |
| Formality | {{n}} | {{…}} | {{…}} |
| Cohesion (capsule) | {{n}} | {{…}} | {{…}} |
| **Overall** | **{{n}}** | {{holistic — if it differs from the rounded mean by >1, why}} | |

## Carried to Personal Style

<!-- REQUIRED. The delta this note made to the memory note, so the OOTD→memory link is auditable both ways.
     One line per change; "nothing new" is a valid line. -->

- What works / doesn't: {{the bullet appended, quoted — or "nothing new"}}
- Wardrobe gaps: {{role}} → {{n}} times suggested
- Journal: {{"entry added (owner's words, YYYY-MM-DD)" or "—"}}
- Personal spec: {{"proposed <spec> = <value> — awaiting yes" · "written to the hub (owner confirmed)" · "—"}}

<!-- OPTIONAL — only what Gate 1 left unanswered. Each line names the key or row its answer fills.
     Name an unconfirmed candidate in PLAIN TEXT (no wikilink) — a link here is a backlink on the item,
     and backlinks are its wear history. Omit the section when nothing is open. -->
## Open questions

- [ ] {{Occasion — what was this worn for? → fills `occasion:`}}
- [ ] {{Is the top the "Item Note" (plain text until confirmed)? → the ⚠️ row in ## Worn becomes ✅ or ❓}}

# References

- [[Personal Style]] — the taste layer this note was judged against
- [[{{YYYY-MM-DD}}]] — the daily note for the wear date
- [[Learning Fashion]] — the principles cited above
- [[Fashion#Personal specs]] — hard facts (contrast, measurements, laptop, location); never restated here
- {{[[YYYY-MM-DD-ootd]] — prior entries used for calibration}}
- {{[[Product Search Note]] — research spun out of a Worth buying row}}

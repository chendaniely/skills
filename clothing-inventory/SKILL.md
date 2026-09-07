---
name: clothing-inventory
description: 'Use when adding or updating an owned garment in the `inventory/items/` register of a markdown knowledge vault — cataloguing a shirt, jacket, cardigan or similar from its photos and sewn-in labels, identifying it against the vendor''s own listing, and filing the label photos alongside the note. Not for pre-purchase research; that is product-search.'
---

# Clothing Inventory Notes

## Overview

**The reader already owns it.** They open the note to answer *"what exactly is this, how do I wash it without ruining it, and where do I get another"* — never *"should I buy it".* That last question belongs to `product-search`; keep the two apart.

**Core principle: the garment is the primary source, the listing is corroboration.** The sewn-in label is a legally required statement about *this specific object*; website copy is marketing about a product line, and it goes stale, gets carried over between seasons, and disagrees. When they conflict, the label wins and the conflict gets written down.

**Second principle: empty beats estimated.** A number, once written, is indistinguishable from a verified one. Uncertain facts go in prose where they can carry their caveat — never into frontmatter.

## When to use

- A garment is being added to `inventory/items/` for the first time
- An existing garment note is being corrected, or a label/measurement is finally read
- Label photos have arrived for a garment already in the register

**Not for:** deciding what to buy (`product-search`), bags and non-clothing (the shared schema still applies — see `inventory/Inventory.md` — but the label/care/sizing machinery below is garment-specific), or anything in the vault's restricted areas.

## The section contract

Write these sections, **in this order**. Omit one only if it is genuinely empty.

| # | Section | Contains |
|---|---|---|
| 1 | *(frontmatter + H1)* | Full key block in the fixed order from `inventory/Inventory.md`, plus the garment deltas below |
| 2 | **Listing line** | One line, directly under the H1: **official product link · price with currency · availability · date read.** See below — this is non-negotiable |
| 3 | **Identification paragraph** | One dense paragraph: construction and materials → brand, product name, product number → ownership and role → how and when identified |
| 4 | **Placement line** | "*Nth garment in the inventory*", naming the sibling notes and which of their precedents this one follows |
| 5 | `## What the labels say` | One bold sub-block per physical label. Spec label as a `\| Field \| Value \|` table; care symbols as the 7-row table below |
| 6 | `## Identification: what is confirmed, and how` | `\| Fact \| Source \| Confidence \|` — values `certain` · `high` · `unresolved` · ⚠️ `conflicted` |
| 7 | `## What the vendor says about it` | Bulleted, always stamped "read YYYY-MM-DD". Separate what the photos confirm from what only the copy claims |
| 8 | `## Measurements — size <X>` | Vendor size chart, **all sizes**, owned size bolded. Always carries the garment-not-body disclaimer |
| 9 | *(argued sections)* | Optional, one `##` per real finding — a conflict, a care insight, why it earns its place. Name them for the conclusion, not the topic |
| 10 | `## Notes` | The standing bullets — see Rules |
| 11 | `## Open questions` | `- [ ]` checkboxes, each naming its resolution method and which frontmatter field the answer fills |
| 12 | `## Photos` | Split `### The garment's own labels — <owner>'s photos, <date>` from `### Reference shots — the vendor's, not this garment`. Italic caption under every embed saying what it proves |
| 13 | `# References` | **H1, not H2.** External links with read dates, then internal wikilinks, ending `[[Inventory]] — conventions` |

## The listing line (non-negotiable)

**Every garment note carries a clickable link to the official product page, directly under the H1** — not buried in References, where finding it costs a scroll and a scan.

```markdown
**[Official listing](https://store.example.com/products/1026233011)** · ¥31,900 list / ¥29,800 sale · ⛔ sold out · read 2026-09-06
```

1. **Link** to the *brand's own* page where possible; an authorised retailer second; an archive snapshot third
2. **Price with currency** — the *list* price, never what was paid (that is `cost`, and it stays empty without a receipt)
3. **Availability**, because a sold-out listing changes what "get another" means
4. **Date read** — listings go stale and eventually 404

Mirror the URL into the `url:` frontmatter key so it is queryable, and keep the annotated entry in `# References` as the provenance record. All three, every time.

⚠️ **When no official page exists, say so on that line and leave `url:` empty** — `**No official listing** — brand defunct; spec preserved below.` A blank `url:` is a queue (the *Needs product link* view), a wrong one is a lie. Never guess a domain: a `200` proves a server answered, not that you reached the brand.

⭐ **The listing will outlive its usefulness — copy the facts in, don't link and hope.** Price, size chart, colourways, fabric and composition all get transcribed into the note. The link is provenance, not storage.

## Frontmatter — deltas from the shared schema

`inventory/Inventory.md` owns the key list and their order. **Do not restate it; do not contradict it.** Garments differ from bags in exactly these ways:

| Key | Garment rule |
|---|---|
| `category` | **The vendor's own category word** (`shirt`, `cardigan`, `jacket`) — even when it wears as something else. Say so in the note and cover the other reading in `aliases` |
| `capacity_l` | **Omitted entirely, not left blank.** A bag field; a shirt has no volume. Blank means *no published figure*; absent means *not applicable* |
| `size` | Always filled — the size tab is the whole basis, so cite it |
| `aliases` | Garment convention: the product number, the native-script and accented forms, and any wrong-but-intuitive name |
| `color` | The **observation**, not the vendor's name for it. Vendor colourway names stay in prose until confirmed off the garment's own label |
| `url` | The official product page. Empty if none exists — never a guess |
| `cost` | What was **paid**. A vendor list price is not a cost and never goes here |

Note titles are ASCII (`TETE HOMME`, `COMME CA MEN`); `aliases` carries the accented form so search finds either.

## Care symbols — transcribe all of them, in label order

Japanese garments use **JIS L0001** (ISO 3758-aligned). Build a `\| \| Symbol \| Means \|` table with one row per symbol.

⚠️ **The bars are the part that gets missed, and they are instructions to a cleaner, not decoration** — under Ⓕ or Ⓦ, one bar means mild, two means very mild. Count the iron's dots (1 = 110 °C, 2 = 150 °C, 3 = 200 °C) and check the drying square for a corner stripe (in the shade) as well as the bar (line dry).

⭐ **Read the symbols as one argument, not a list.** A run of fussy-looking instructions usually all defend the same property — loft, colour, or a stretch fibre's recovery. Say which, and name the one instruction that actually matters day to day.

## Photos

The filename spec lives in `inventory/Inventory.md`. What is garment-specific:

- **Label photos are `kind: serial`, always with a `-<detail>` suffix** — `-brand-label`, `-spec-label`, `-care-label-front`, `-care-label-back`. The care label is the garment's identifying document, the role a serial plate plays on a bag. Bare `-serial-01` would be indistinguishable in a flattened export
- **Read every label at full resolution before transcribing.** Crop and upscale the symbol block; a two-dot iron read as one dot is a 40 °C error
- **A vendor image is a stand-in, not a record.** It clears the *Needs photos* view while proving nothing about condition, wear or even the right colourway. Flag it in the caption *and* in `## Notes`, with the exact command to fix it:
  `python3 scripts/file-inventory-photos.py "<Item Name>" --kind mine`
- **Verify the product image after downloading** — read it back and check it shows this garment, in this colourway
- ⭐ **A white label in frame is a white-balance anchor.** Black-versus-navy can often be settled from the photos already taken — sample the fabric, correct against the known-white label, and report the numbers. Do this before recommending anyone buy a lamp

## Rules

- **Tables and bullets over prose.** Prose only where reasoning genuinely needs sentences.
- **Trust the label over the website, and record the conflict rather than silently picking.** Offer the competing explanations — a site error and a between-seasons fabric change are different stories with the same resolution.
- **Stamp every vendor claim with the date read.** Prices, stock and size charts are perishable.
- **Unknown is a value.** "Not published" and an empty field beat an estimate. Never write a plausible date, price or measurement.
- **Check the size chart for internal consistency before trusting it.** If one column stops rising with size, it is a typo, not a cut — say which reading you believe and put "measure the garment" in `## Open questions`.
- **Measurements are garment measurements, not body measurements** — laid flat, chest doubled. Say it every time.
- **Supersede by annotation, never deletion.** A corrected reading keeps the wrong one visible with the reason, because the wrong version is usually the intuitive one and will otherwise be re-derived.
- **Explain empty fields affirmatively.** An empty `evaluation:` gets a Notes bullet saying the catalogs record pre-purchase research and this was not researched — otherwise it reads as an unfinished note.
- **Name the transferable finding.** If something learned here would help next time, mark it ⭐ and state it as a rule, then carry it into the vault's `CLAUDE.md` or this skill.
- **Score the garment against the vault's own frameworks** where one applies, and resolve the tension honestly rather than scolding — a material that loses to the framework can still be right for the role.

## Common mistakes

| Mistake | Fix |
|---|---|
| Official URL only in `# References` | Listing line under the H1 + `url:` frontmatter + References. All three |
| `url:` filled with a guessed or retailer domain | Brand's own page, or empty. A `200` is not proof of the brand |
| Price from the listing written into `cost` | `cost` is what was paid; list price lives in the listing line and the confidence table |
| Care symbols summarised as "hand wash" | Transcribe all of them, in order, with the bars and dots counted |
| `capacity_l:` left blank on a garment | Delete the key — absent ≠ blank |
| Vendor photo with no caption disclaiming it | Say "not a photo of the owned garment" in the caption and in `## Notes` |
| Size chart copied without a sanity check | Verify each column rises with size; flag and measure if not |
| Colourway guessed from a photo's appearance | White-balance against a known-white reference in frame, or leave it open |

## Scope note — what generalises

Everything above the `## Care symbols` heading applies to **any** owned item: the listing line, the `url:` key, the confidence table, empty-beats-estimated, supersede-by-annotation. The garment-specific parts are the care-symbol table, `## Measurements`, the `capacity_l` omission and the label-as-`serial` photo convention. If a general `inventory-item` skill is ever factored out, that is the seam to cut along.

## Template

Start from `template-clothing-inventory.md` in this directory.

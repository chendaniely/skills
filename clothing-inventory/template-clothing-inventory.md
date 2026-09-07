---
Created: YYYY-MM-DD HH:MM
Modification date: <Weekday> YYYY-MM-DD HH:MM:SS
aliases:
  - <vendor product number>
  - <native-script or accented form>
  - <wrong-but-intuitive name someone would search>
tags:
  - inventory
  - fashion
category: <vendor's own category word — shirt / cardigan / jacket>
status: owned
location:
make: <BRAND, ASCII>
model: <native name (English name) — product number>
size: <off the size tab>
color: <the observation, not the vendor's colourway name>
qty: 1
order_date:
delivery_date:
cost:
cost_currency:
cost_cad:
receipt_email:
order_number:
serial:
warranty_until:
sold_date:
sold_price:
sold_currency:
sold_cad:
sold_to:
photo: "[[inv-<slug>-product.jpg]]"
url: <official product page — empty if none exists, never a guess>
evaluation:
import_ref: inv-<slug>
---

<!-- capacity_l is DELETED above, not blank. It is a bag field; a garment has no
     volume, and blank would imply "no published figure" rather than "N/A". -->

# <Brand ASCII> <Product Name>

**[Official listing](<url>)** · <¥price list / ¥price sale> · <availability> · read YYYY-MM-DD

<!-- The listing line is section 2 and is non-negotiable. If there is no official
     page: **No official listing** — <why> — and leave `url:` empty. -->

<One dense paragraph: construction and materials → brand, product name, product
number → owned, and the role it plays → how and when it was identified.>

**<Nth> garment in the inventory**, after [[<sibling>]] and [[<sibling>]]<, and the first
`category: <x>`>. <Which of their precedents this note follows, and why this `category`.>

## What the labels say

<!-- One bold sub-block per physical label. Read each at full resolution first. -->

**Brand label** — <where sewn, what it looks like>:

- <what it says, verbatim>

**Spec label** — <material, where>:

| Field | Value |
|---|---|
| `NO.` | **<product number>** |
| `サイズ` | **<size>** |
| `品質表示` | **<fibre 1 %>** · **<fibre 2 %>** |

**Care label** — <where sewn>:

- **Care symbols — <N>, in label order** (JIS L0001, ISO 3758 aligned; read at 5–10×):

  | | Symbol | Means |
  |---|---|---|
  | 1 | <shape described> | **<instruction>**, <limit> |

<!-- Count iron dots (1=110°C, 2=150°C, 3=200°C). Count bars under Ⓕ/Ⓦ
     (one = mild, two = very mild). Check the drying square for a corner
     stripe (shade) as well as the bar (line dry). -->

- <bullet instructions, verbatim + translation>
- `<manufacturer>` / `<address>` / `<country of origin>`

## <Argued section — name it for the conclusion>

<!-- Optional but usually the most valuable part. Read the care instructions as one
     argument rather than a list: what property do they all defend? Name the single
     rule that matters day to day. Delete this section if there is nothing to argue. -->

## Identification: what is confirmed, and how

| Fact | Source | Confidence |
|---|---|---|
| <claim> | <what proves it> | **certain** |
| <claim> | <measured / inferred how> | **high** — not label-stated |
| <disputed field> | label says X, vendor says Y | ⚠️ **conflicted** |

## What the vendor says about it

From the official product page, read YYYY-MM-DD.

- **Fabric:** <vendor's own description>
- **Construction:** <what the vendor states>
- **Availability:** <in stock / sold out, and what that means for replacing it>

**Confirmed from the owner's own photos, not just the copy:** <what the photos independently establish>.

## Measurements — size <X>

Vendor's **garment** measurements in cm, read YYYY-MM-DD. Other sizes kept for a future replacement or resale listing.

| | S | M | **<owned> ** | L |
|---|---|---|---|---|
| 着丈 — length | | | | |
| 身幅 — chest | | | | |
| 肩幅 — shoulder | | | | |
| 袖丈 — sleeve | | | | |

<!-- SANITY-CHECK THE CHART before trusting it: every column should rise with size.
     A column that falls is a typo, not a cut — say so and add "measure it" below. -->

These are garment measurements — laid flat, chest doubled — not body measurements.

## Notes

- **`capacity_l` is omitted, not blank** — a bag field with no meaning for a garment.
- **No purchase record.** Date, price paid and receipt unknown, left empty rather than estimated. The <list price> above is the *online* price; `cost` means what was actually paid.
- **In no catalog**, so `evaluation:` is empty — normal, since the catalogs record pre-purchase research.
- **Photos: <N> label shots are the owner's; the product image is the vendor's.** <Why the labels are filed as `serial` with `-<detail>` suffixes.> **Still wanted: a worn shot and a condition shot.** Drop them into this folder and run, from the vault root:
  `python3 scripts/file-inventory-photos.py "<Item Name>" --kind mine`

## Open questions

- [ ] <Question> — <how to resolve it>, <which frontmatter field the answer fills>.

## Photos

### The garment's own labels — <owner>'s photos, YYYY-MM-DD

![[inv-<slug>-serial-01-brand-label.jpg|300]]

*<What this label proves, and what it notably does NOT carry.>*

### Reference shots — the vendor's, not this garment

![[inv-<slug>-product.jpg|300]]

*<The listing's shot, and the note's `photo:`. **Not a photo of the owned garment**, so it shows nothing about condition or wear — but it records the form.>*

# References

- [<Product name>（<number>） — <BRAND> ONLINE STORE](<url>) — official product page; source for <what> (read YYYY-MM-DD)
- [[Inventory]] — conventions
- [[Fashion]] — topic hub
- [[<sibling garment>]] — <which precedents were inherited from it>

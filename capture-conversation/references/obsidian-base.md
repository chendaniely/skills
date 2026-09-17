# Future: Obsidian Base

(Obsidian-specific — other tools would put their own query/view layer over the
same frontmatter.) Not built yet — but the frontmatter in SKILL.md is designed
for it. When wanted, a `Conversations.base` (wherever the target vault keeps
Bases) looks like:

```yaml
filters:
  and:
    - file.inFolder("<captures folder>")
    - 'file.ext == "md"'
    - '!file.basename.endsWith("-transcript")'
views:
  - type: table
    name: All captures
    order: [file.name, Created, Type, Purpose, Source]
    sort: [{property: Created, direction: DESC}]
  - type: table
    name: Own cognition
    filters: {and: ['Purpose == "own-cognition"']}
    order: [file.name, Created, Type]
  - type: table
    name: External material
    filters: {and: ['Purpose == "external-material"']}
    order: [file.name, Created, Type]
```

`file.basename` has no extension, so the `-transcript` test matches;
`file.ext == "md"` keeps the `-audio.mp3` files out.

Candidate future keys (add only when a real view needs them): `Status:
open/settled` for whether open threads remain, `Participants:` for multi-party,
`Project:` to group captures by venture.

**Separation from other Bases.** Conversations never join a vault's domain Bases
(e.g. a products/decisions Base) — those are fed by their own note types, not
captures. When a conversation *is about* such a domain (say, a product to
purchase), the capture pair still lands in the captures folder, and the domain
note (wherever that vault keeps it) is created/updated separately with a wikilink
to the capture as prior context. The graph connects the two; each Base stays
clean over its own note type.

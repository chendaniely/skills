# skills

My personal [Claude Code](https://code.claude.com/docs/en/skills) skills. Each folder is one skill: a `SKILL.md`, plus any templates or reference files it uses.

## Skills

| Skill | Group | What it does |
|---|---|---|
| [capture-conversation](capture-conversation/) | Vault | Turns a Claude chat, voice memo or meeting recording into a verbatim transcript plus a note on how the thinking went. |
| [catch-up](catch-up/) | Vault | When asked, catches the vault up after a gap: files the inbox, sweeps `#todo` lines into `TODO.md`, writes weekly rollups and rewrites today's Today block. |
| [clothing-inventory](clothing-inventory/) | Vault · wardrobe | Catalogues a garment I own from its photos and sewn-in labels. |
| [ootd](ootd/) | Vault · wardrobe | Logs an outfit photo, links the pieces to the inventory once I confirm them, and scores the outfit. |
| [product-search](product-search/) | Vault · wardrobe | Writes buying-guide notes: the verdict and a ranked shortlist first, the evidence below. |
| [email-digest](email-digest/) | Vault | Runs my daily email digest from Thunderbird (read-only on mail) and writes the checklist into the daily note. |
| [capture-learning-moment](capture-learning-moment/) | Teaching | When asked, writes up a teachable moment from the current conversation as a Quarto `.qmd` for students. |
| [class-notes](class-notes/) | Teaching | Turns a Plaud recording of a class into a dated session folder, then generates notes with the course's own prompt, which students edit by pull request. |
| [creating-ultra-crew-guides](creating-ultra-crew-guides/) | Running | Builds offline crew guides for an ultramarathon: aid stations, driving, cutoffs and drop bags. |

The vault skills assume an Obsidian-style markdown vault and read its `CLAUDE.md` for folder names. `catch-up` and `email-digest` are written for my own setup, and `email-digest` also needs my private `claude-cowork` repo.

## Install

```bash
git clone https://github.com/chendaniely/skills.git
cd skills
./install.sh
```

`install.sh` links each skill folder into `~/.claude/skills/`, so Claude Code finds it and edits here apply right away. It leaves everything else in that folder alone and removes links to skills that no longer exist. Run it again after adding or renaming a skill.

Or install them as plugins from this repo's marketplace:

```
/plugin marketplace add chendaniely/skills
/plugin install wardrobe@chendaniely-skills
```

The plugins are `vault`, `wardrobe`, `teaching` and `running`, matching the groups above. Plugin skills carry the plugin's name (`/wardrobe:ootd`) and update through `/plugin`; turn on auto-update for the marketplace there. Use one install method or the other, not both.

Call a skill by name (for example `/capture-learning-moment`), or let Claude load it when a request matches its description.

## License

[MIT](LICENSE)

# ootd test prompt

The prompt each fresh subagent got in the 2026-09-06 RED/GREEN runs, recovered from that session's transcript.

To use it:

- **Fill in the paths.** Replace `<FIXTURE>` with the fixture vault's absolute path (the recipe is at the top of `check_green.py`). Replace `<REAL_VAULT>` with the live vault's root, which the run must not touch. The original runs also named the other fixture folders in that sentence.
- **RED:** run it with `ootd` not installed.
- **GREEN:** run it with `ootd` installed.
- **Grade:** `python3 check_green.py <FIXTURE>`.

The RED runs worded the last paragraph slightly differently ("finally write a short section titled … listing each judgment call and your reasoning in one sentence each. Also state which skills (if any) you invoked, by name."). The grader doesn't depend on that wording.

---

Work in the Obsidian vault at <FIXTURE> — use that absolute path for every command and file operation, and do NOT touch anything under <REAL_VAULT> or any other fixture (different vaults; this one is self-contained). Read <FIXTURE>/CLAUDE.md first — it is the vault's constitution.

Dan (the vault owner) just pasted a photo of what he is wearing into today's daily note — <FIXTURE>/000-periodic_notes/daily/2026/09/2026-09-06.md, the embed `![[Pasted image 20260906183000.png]]` (the file is at <FIXTURE>/ze-files/) — and said:

"ootd. tag today with wiki links so it's referenced in the daily note. identify everything I'm wearing in my inventory — if something's missing let me know, I'll give you details or you can search for it, and it gets an inventory clothing note with the photos. the ootd note links all the pieces plus your fashion advice. also make a general fashion note where we keep the memory for my personal style — I want to migrate towards a capsule wardrobe with some fun pieces. and tell me what to buy to make this outfit better."

Do it. If you need Dan's input at any point, state exactly what you would ask him, then proceed with your best default so the run completes end to end — he is away and wants to find it finished. Do not use a web browser; curl/WebFetch are fine if you need the web. When finished, run `cd <FIXTURE> && uv run scripts/lint.py` and include its non-BROKEN-LINK summary lines. Then list every file you created or changed (absolute paths), one line each on why, write a short section "Decisions I made without asking" (one sentence each), and state which skills you invoked, by name.

---
name: creating-ultra-crew-guides
description: Use when crewing, pacing, or captaining for a runner in an ultramarathon (50K–200mi) and building a crew guide, aid-station plan, driving/logistics doc, or race-day reference — including races with crew-accessible aid stations, cutoffs, drop bags, pacer rules, and no cell service.
---

# Creating Ultra Crew Guides

## Overview

A crew guide is a **field document read at 3 a.m., on no sleep, with no internet** — not a research report. Optimize for *flip to the aid station you're driving to and know exactly what to do.*

**Core principle:** the crew chief is the team's information hub. Every section must answer: what do I set up, what do I tell the runner and pacer, and what's next?

## When to Use

- Building crew/pacer materials for any ultra with crew-accessible aid stations
- Ingesting race sources (official site, race guide PDF/Doc, third-party profiles, podcasts, YouTube) into a usable plan
- Race logistics: leapfrog driving, drop bags, pacer legs, cutoffs, offline navigation

**Not for:** the runner's own training/pacing plan (that's a different artifact — consume it, don't write it).

## Deliverables

| File | Purpose |
|---|---|
| **During-race guide** | The core. Master table + one `##` section per crew-accessible aid station |
| **Pre-race guide** | Schedule, drop bags, gear, route/comms, team briefing, fill-in-before-signal sheet |
| **Post-race guide** | Finish, recovery, DNF contingency, **debrief captured while fresh** |
| **Dash card** | One page for the car: stops, ETAs, cutoffs, drives, GPS, emergency numbers |
| **Driving instructions** | Leg-by-leg, in *crew* order (≠ course order), with gas + road warnings |
| **Context/working notes** | Canonical data, decisions, conventions, open questions — so a new session resumes cold |

## Per-Station Section Template

```
## <Station> — Mile X (Y km)
📊 Leg ahead — stations up to the NEXT CREW stop (mi/km + cutoff + ETA)
📍 Quick facts — ETA · cutoff · crew/pacer/drop-bag · drive · parking
🅿️ Setup — turn-by-turn, where to park, what to stage before arrival
🏃 When runner arrives — start break timer · log cal/fluid/pee · give/tell/check
📣 Direct the team — brief the pacer, assign jobs, say the numbers out loud
🧭 Course ahead — terrain, water, dark/cold/heat, what to warn them about
```

## Data Rules

| Rule | Why |
|---|---|
| **Cutoffs: official chart ONLY** | Third-party sites and pace planners drift. Never mix sources. |
| **ETAs: the runner's pace plan** | Use its *arrival* column (accounts for elevation). Label as goal, not fact. |
| **Convert units with a tool call** | Never hand-convert. Report mi *and* km. |
| **Report 3 distances per station** | to next AS, **to next _crew_ AS**, and total. The middle one drives decisions. |
| **Flag every conflict inline** | Show both values, say which to plan against, add to a verify list. |
| **Tag by source (🎧 podcast, etc.)** | The user must see where a claim came from. |

## Extraction Techniques

- **Google Doc race guide:** `curl -sL ".../export?format=txt"` (WebFetch dies on the redirect).
- **Charts that are images** (aid-station tables often are): export the same Doc as `format=pdf`, then read those pages — this is usually the only way to get authoritative cutoffs.
- **Podcast/video:** `ffmpeg -vn -ac 1 -ar 16000` → whisper (seed the initial prompt with aid-station and place names so proper nouns transcribe correctly). Produce transcript + distilled notes as separate files.
- **Google Maps links:** `/maps/dir/` URLs contain lat/lon — extract them. Short `maps.app.goo.gl` links usually don't resolve to coordinates.

## Offline-First

Assume **no cell service**. Therefore:
- Everything must be printable; nothing critical lives only in an app.
- Include GPS coordinates (aid stations often have no street address).
- Include a **fill-in sheet** for what only the team knows: bib #, allergies/meds, emergency contact, nutrition targets, drop-bag contents, teammate phones/inReach, RD emergency number.
- Warn where routing apps suggest non-roads; give the correct route explicitly.
- Note gas towns and dead stretches; compute sunrise/sunset for headlamp timing.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Assuming which stations the crew will staff | Ask. "Crew-*allowed*" ≠ "crew *plans to be there*." Rebuild distances when it changes. |
| Treating a source's crew as the user's crew | Podcast hosts have their own base, pacers, and stops. Mark as reference-only. |
| Course order = driving order | Crews leapfrog and backtrack; document the *driving* sequence separately. |
| Burying decisions in prose | Lead with the 1–2 forks that shape the day (which station, tight turnarounds). |
| Leaving cutoffs unverified | Chart may update race week — say so, and put verification on the pre-race checklist. |
| Skipping the debrief | Capture results/corrections immediately after the finish; that's next year's guide. |

## Plans Change — Rebuild Cleanly

Crew stops, pacer legs, and routes *will* change mid-build. When they do: recompute every derived number (to-next-crew-AS distances especially), then **grep the whole doc set for the old assumption** — stale mentions in a briefing script or drop-bag table are the failure mode. Verify with a search, not memory.

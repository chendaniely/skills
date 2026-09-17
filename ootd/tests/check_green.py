#!/usr/bin/env python3
# GREEN-run grader for the ootd skill (2026-09-06). Reads a fixture vault's state after a run and
# checks the gates; never trusts the run's self-report.
#
# Fixture recipe: rsync CLAUDE.md, README.md, TODO.md, TODO-completed.md, wiki/topics/fashion/,
# inventory/, ze-templates/, scripts/{lint,file-inventory-photos,file_inventory_photos,ootd_photo,
# test_ootd_photo}.py, 000-bases/{OOTD.base,README.md}, .obsidian/{app,daily-notes}.json and the
# day's daily note into /tmp/<fixture>/ (never the vault's protected folders); git init + commit;
# save a test outfit photo as ze-files/Pasted image 20260906183000.png (PNG, no EXIF -- an Obsidian
# paste) and embed it under the daily note's ## Log; seed two inventory items, an exact match and a
# same-category near-miss (Test White / Test Blue Linen Shirt); commit as the reset point.
# RED = a fresh subagent with the standard prompt in tests/prompt.md and no skill installed;
# GREEN = same prompt with ~/.claude/skills/ootd present. Then:  python3 check_green.py /tmp/<fixture>
# Dates and names below are the 2026-09-06 fixture's; adjust when the fixture changes.
import os, re, subprocess, sys

root = sys.argv[1]
def sh(*a):
    return subprocess.run(a, cwd=root, capture_output=True, text=True).stdout

status = sh('git', 'status', '--short')
changed = [l[3:].strip().strip('"') for l in status.splitlines()]
results = []
def check(name, ok, detail=''):
    results.append((name, ok, detail))

# 1. exactly one OOTD note, correctly named
log_dir = os.path.join(root, 'wiki/topics/fashion/log')
notes = sorted(f for f in os.listdir(log_dir)) if os.path.isdir(log_dir) else []
check('one OOTD note named YYYY-MM-DD-ootd.md', notes == ['2026-09-06-ootd.md'], str(notes))
note = open(os.path.join(log_dir, notes[0]), encoding='utf-8').read() if notes else ''

# 2. no new inventory item folders (nothing confirmed => nothing created)
new_items = [c for c in changed if c.startswith('inventory/items/')]
check('no inventory notes/photos created or changed', not new_items, str(new_items))

# 3. frontmatter: items empty, unmatched honest (>=4 given 4-5 rows), occasion empty, private true, tags list
fm = note.split('---')[1] if note.count('---') >= 2 else ''
items_block = re.search(r'^items:(.*?)(?=^\w|^---)', fm, re.S | re.M)
items_val = items_block.group(1).strip() if items_block else None
check('items: empty (no confirmation possible)', items_val in ('[]', ''), repr(items_val))
um = re.search(r'^unmatched:\s*(\d+)', fm, re.M)
check('unmatched >= 4 (rows counted, not redefined)', bool(um) and int(um.group(1)) >= 4, um.group(0) if um else 'missing')
occ = re.search(r'^occasion:(.*)$', fm, re.M)
check('occasion key present and EMPTY', bool(occ) and occ.group(1).strip() == '', occ.group(0) if occ else 'missing')
check('private: true', 'private: true' in fm)
check('tags list fashion+log', re.search(r'^tags:\n  - fashion\n  - log', fm, re.M) is not None)
for k in ['date', 'photo', 'score', 'score_fit', 'score_proportion', 'score_color', 'score_formality', 'score_cohesion', 'verdict']:
    check(f'key {k}', re.search(rf'^{k}:', fm, re.M) is not None)

# 4. no links in ## Worn
worn = re.search(r'^## Worn(.*?)^## ', note, re.S | re.M)
worn_txt = worn.group(1) if worn else ''
REFERENCE_NOTES = {'Learning Fashion', 'Personal Style', 'Fashion', 'Inventory', 'OOTD.base'}
def piece_links(txt):
    return [m for m in re.findall(r'\[\[([^\]|#]+)', txt) if m.strip() not in REFERENCE_NOTES]
check('no piece wikilinks in ## Worn rows', not piece_links('\n'.join(l for l in worn_txt.splitlines() if l.startswith('|'))),
      str(piece_links(worn_txt)))
oq = re.search(r'^## Open questions(.*?)^# References', note, re.S | re.M)
check('no piece wikilinks in ## Open questions', not piece_links(oq.group(1)) if oq else True, str(piece_links(oq.group(1)) if oq else ''))
check('## Worn has >= 4 rows', len([l for l in worn_txt.splitlines() if l.startswith('|') and not l.startswith('|--') and 'Slot' not in l]) >= 4)

# 5. section order
want = ['# OOTD 2026-09-06', '## Worn', '## Advice', '### The outfit as a whole', "### What's working", "### What's not working",
        '### Make it better', '### Scores', '## Carried to Personal Style', '# References']
pos = [note.find(h) for h in want]
check('section order per contract', all(p >= 0 for p in pos) and pos == sorted(pos), str(list(zip(want, pos))))
check('H1 has no occasion clause when occasion empty', re.search(r'^# OOTD 2026-09-06\s*$', note, re.M) is not None,
      re.search(r'^# OOTD.*$', note, re.M).group(0) if re.search(r'^# OOTD.*$', note, re.M) else 'no H1')
check('Scores table has Anchor + Calibration columns', 'Anchor' in note and 'Calibration' in note)
check('no brand/price/URL in Worth buying', not re.search(r'\$\d|https?://', note.split('### Make it better')[-1].split('### Scores')[0]) if '### Make it better' in note else False)

# 6. write scope
forbidden = [c for c in changed if c in ('CLAUDE.md', 'README.md', 'inventory/Inventory.md', '000-bases/README.md',
                                         'wiki/topics/fashion/Fashion.md', '000-bases/OOTD.base') or c.startswith('scripts/')]
check('no governance/conventions files touched', not forbidden, str(forbidden))
daily_diff = sh('git', 'diff', '000-periodic_notes/daily/2026/09/2026-09-06.md')
today_touched = re.search(r'^[-+](?!\+\+|--)(?!.*Pasted image)(?!.*ootd).*', daily_diff, re.M)
added = [l for l in daily_diff.splitlines() if l.startswith('+') and not l.startswith('+++')]
removed = [l for l in daily_diff.splitlines() if l.startswith('-') and not l.startswith('---')]
check('daily note: only the embed re-point + Log lines', all(('ootd' in l or 'Pasted image' in l or 'Personal Style' in l) for l in added + removed) and 'Today' not in daily_diff, str(removed + added)[:300])
check('pasted PNG removed', 'ze-files/Pasted image 20260906183000.png' in changed and 'D ' in status)
check('normalized JPEG present', os.path.exists(os.path.join(root, 'ze-files/ootd/2026-09-06-ootd-01.jpg')))
check('Personal Style updated', 'wiki/topics/fashion/reference/Personal Style.md' in changed)
check('TODO.md updated', 'TODO.md' in changed)

# 7. lint
lint = sh('uv', 'run', 'scripts/lint.py')
orph = re.search(r'attachments: (\d+) orphaned', lint); broken = re.search(r'links: \d+ checked, (\d+) broken', lint)
check('lint: 0 orphaned', bool(orph) and orph.group(1) == '0', orph.group(0) if orph else 'n/a')
check('lint: broken links unchanged (302)', bool(broken) and broken.group(1) == '302', broken.group(0) if broken else 'n/a')

ok = sum(1 for _, o, _ in results if o)
for name, o, detail in results:
    print(('PASS ' if o else 'FAIL ') + name + (f'  [{detail}]' if detail and not o else ''))
print(f'\n{ok}/{len(results)} checks passed for {root}')

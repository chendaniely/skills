#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "markdown-it-py>=3.0",
#     "pillow>=11",
#     "send2trash>=2.1",
# ]
# ///
"""Mirror claude.ai chats into the vault. Run from the vault root, with S set to this file:

    uv run "$S" snippet (LINK | --project NAME)
    uv run "$S" ingest [--wait SECONDS] [FILE ...]
    uv run "$S" render [--apply] [--recreate ID ...]
    uv run "$S" summaries
    uv run "$S" summary ID --file PATH [--force | --update]
    uv run "$S" daily --project NAME [--apply]
    uv run "$S" queue --project NAME
    uv run "$S" processed ID
    uv run "$S" status

snippet    Print the browser code, with the hold rules filled in from config, to run in a
           fresh tab on claude.ai/robots.txt. For one share link or chat URL it saves that
           chat, with its photos, as claude-chat-<id>.json. For a project listed in `allow`
           it starts a job that saves the new or changed chats as claude-project-<id>.json.
ingest     Archive downloads byte for byte: claude-project-*.json, claude-chat-*.json, or the
           older claude-conversation-*.json plus claude-files-*.json. Looks in downloads_dir
           and the archive's own conversations/ folder, or takes the FILEs given. Never writes
           the vault. --wait waits up to that many seconds for a download to land first.
render     Write notes into sources/claude/<project>/, or sources/claude/no-project/ for
           chats outside a project, and their photos into the project's photo folder or
           ze-files/claude/ (metadata stripped; each named <chat-id>-NN once and for good),
           plus a note per project, `<Project> (Claude project).md`, with its instructions,
           its docs' names and its chats. A dry run unless --apply. Only text between the
           claude-chats markers and the script's frontmatter keys are ever rewritten.
summaries  List notes still waiting for their summary.
summary    Put the Markdown in PATH under a note's `## Summary` and stamp `Summary:`.
           --update, for a chat that has grown: add it as a dated `### Update` under the
           written summary, which stays as it is (on a note still pending, it is the summary).
daily      List, or with --apply write, a link under `## Log` in the daily note of each day
           Dan had each of a project's chats. A link is added once, and one he removes stays out.
queue      List a project's chats not yet processed.
processed  Stamp a chat's note `Processed`. A later reply puts it back in the queue.
status     Config path, archive, counts, and the Templater guard.

The claude-chats skill drives this from a Claude session; the chat itself is fetched in
Dan's own Chrome. The vault says where its archive is in .claude/claude-chats.toml.

Exit codes: 0 ok - 1 partial (per-item errors listed) - 64 usage - 65 bad download -
66 nothing found - 70 internal error - 75 lock held - 78 config problem.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import claude_chats_archive as A  # noqa: E402
import claude_chats_render as R  # noqa: E402


TARGET = Path("sources") / "claude"
IMAGES = A.DEFAULT_PHOTOS
TEMPLATER = Path(".obsidian") / "plugins" / "templater-obsidian" / "data.json"
DAILY = Path("000-periodic_notes") / "daily"
DAILY_TEMPLATE = Path("ze-templates") / "template-daily.md"
TURN_RE = re.compile(r"^### \[(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})\] \*\*", re.MULTILINE)
PRUNE = {"private", "do-not-publish", "submodules"}
SNIPPET = Path(__file__).with_name("claude_chats_snippet.js")
PROJECT_SNIPPET = Path(__file__).with_name("claude_chats_project_snippet.js")
MAX_PROJECT_BYTES = 150 * 1024 * 1024  # past this a project sync stops adding chats and asks for another run
LINK_RE = re.compile(r"(?:https://claude\.ai/(share|chat)/)?"
                     r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})(?:[/?#].*)?", re.IGNORECASE)


def parse_link(link: str) -> tuple[str | None, str | None] | None:
    """(share ID, chat ID) for a claude.ai share link or chat URL, one of them None; a bare ID
    counts as a share link. None for anything else, so nothing else reaches the snippet."""
    m = LINK_RE.fullmatch(link.strip())
    if not m:
        return None
    uid = m.group(2).lower()
    return (None, uid) if (m.group(1) or "").lower() == "chat" else (uid, None)


def _hold_values(cfg: A.Config) -> dict[str, str]:
    def holds(items, defaults):
        return sorted({A.normalize_title(p) for p in [*items, *defaults]} - {""})
    return {"__HOLD_PREFIXES__": json.dumps(holds(cfg.hold_prefixes, A.DEFAULT_HOLD_PREFIXES)),
            "__HOLD_PATTERNS__": json.dumps(holds(cfg.hold_patterns, A.DEFAULT_HOLD_PATTERNS))}


def _fill(template: Path, values: dict[str, str]) -> str:
    """Put the values into a template in one pass. A value can come from a downloaded file and
    the result runs in Dan's logged-in page, so text inside a value is never read as a placeholder."""
    placeholders = re.compile("|".join(re.escape(k) for k in sorted(values, key=len, reverse=True)))
    return placeholders.sub(lambda m: values[m.group()], template.read_text(encoding="utf-8"))


def snippet_js(share: str | None, chat: str | None, cfg: A.Config) -> str:
    """The browser snippet for one link, with the hold rules filled in from config."""
    return _fill(SNIPPET, {"__SHARE__": json.dumps(share), "__CHAT__": json.dumps(chat), **_hold_values(cfg)})


def project_snippet_js(pid: str, cfg: A.Config, manifest: dict) -> str:
    """The browser job for a whole project, told what is already archived. A chat still
    missing photos isn't counted as known, so the next sync fetches it again."""
    entries = [(cid, e) for cid, e in manifest["conversations"].items()
               if e.get("project") == pid and e.get("snapshot") and e.get("state", "active") == "active"]
    known = {cid: e["updated_at"] for cid, e in entries if not e.get("photos_missing")}
    files = sorted({fid for _cid, e in entries for fid in (e.get("files") or {})})
    project = manifest["projects"].get(pid) or {}
    return _fill(PROJECT_SNIPPET, {"__PROJECT__": json.dumps(pid), "__KNOWN__": json.dumps(known),
                                   "__KNOWN_FILES__": json.dumps(files),
                                   "__KNOWN_PROJECT__": json.dumps(project.get("updated_at")),
                                   "__DELAY_MS__": str(int(cfg.delay_ms)),
                                   "__MAX_BYTES__": str(int(MAX_PROJECT_BYTES)),
                                   "__PHOTO_TYPES__": json.dumps(sorted(A.MIME_EXT)), **_hold_values(cfg)})


def vault_stems(vault: Path) -> set[str]:
    stems: set[str] = set()
    for _root, dirs, files in os.walk(vault):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in PRUNE]
        stems.update(os.path.splitext(f)[0] for f in files)
    return stems


def note_index(vault: Path) -> dict[str, Path]:
    """Conversation ID -> note, read from the notes themselves, so a note Dan moved or a
    manifest that lost its path still finds the right file."""
    index: dict[str, Path] = {}
    root = vault / TARGET
    for path in sorted(root.rglob("*.md")) if root.exists() else []:
        lines, _ = R.split_note(path.read_text(encoding="utf-8"))
        cid = R.frontmatter_values(lines).get("Conversation ID")
        if cid:
            index.setdefault(cid, path)
    return index


def templater_safe(vault: Path) -> bool:
    """Templater 2.18 runs any `<% %>` in a newly created note. Safe when its trigger is
    off, or when an ignore-on-creation setting lists sources/ (Templater 2.20+)."""
    path = vault / TEMPLATER
    if not path.exists():
        return True
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not data.get("trigger_on_file_creation"):
        return True
    for key, value in data.items():
        if "ignore" in key.lower() and isinstance(value, list):
            folders = [str(v.get("folder", "") if isinstance(v, dict) else v).strip("/") for v in value]
            if "sources" in folders or str(TARGET) in folders:
                return True
    return False


def rel(vault: Path, path: Path) -> str:
    return str(path.relative_to(vault))


def plan_images(vault: Path, archive: Path, cid: str, entry: dict, conv: dict,
                folder: Path) -> tuple[dict, list, list[str]]:
    """Vault names for a chat's archived photos (`<chat-id>-NN.<ext>`, fixed once given), the
    copies still to make, and the photos left out because they can't be read."""
    files = entry.get("files") or {}
    names = dict(entry.get("images") or {})
    used, n, unreadable = set(names.values()), len(names), []
    for fid in R.image_order(conv):
        if fid in files and fid not in names:
            try:
                clean_image((archive / files[fid]["path"]).read_bytes())
            except Exception:  # noqa: BLE001 -- Pillow raises many kinds for a file it can't read
                unreadable.append(fid)
                continue
            ext = Path(files[fid]["path"]).suffix
            n += 1
            while f"{cid[:8]}-{n:02d}{ext}" in used:
                n += 1
            names[fid] = f"{cid[:8]}-{n:02d}{ext}"
            used.add(names[fid])
    copies = [(archive / files[fid]["path"], vault / folder / name) for fid, name in names.items()
              if fid in files and not (vault / folder / name).exists()]
    return names, copies, unreadable


def clean_image(data: bytes) -> bytes:
    """Drop EXIF and XMP (a photo of home can carry GPS). Untouched bytes when there is none."""
    from PIL import Image
    with Image.open(io.BytesIO(data)) as img:
        if not (len(img.getexif()) or any(k in img.info for k in ("exif", "xmp", "XML:com.adobe.xmp"))):
            return data
        params = {"quality": 95} if img.format in ("WEBP", "JPEG") else {}
        if img.info.get("icc_profile"):
            params["icc_profile"] = img.info["icc_profile"]
        out = io.BytesIO()
        img.save(out, format=img.format or "WEBP", **params)  # exif/xmp are written only when passed
        return out.getvalue()


@dataclass
class Plan:
    writes: list[tuple[Path, str, str, str]] = field(default_factory=list)  # path, text, status, cid
    groups: dict[str, list[str]] = field(default_factory=lambda: {"new": [], "updated": [], "non-additive": []})
    unchanged: int = 0
    excluded: int = 0
    empty: int = 0
    failed: int = 0
    flags: dict[str, list[str]] = field(default_factory=dict)
    paths: dict[str, Path] = field(default_factory=dict)
    ids: dict[str, list[str]] = field(default_factory=dict)
    projects: dict[str, dict] = field(default_factory=dict)
    images: dict[str, dict] = field(default_factory=dict)
    image_copies: list[tuple[Path, Path]] = field(default_factory=list)
    project_writes: list[tuple[Path, str, str, str]] = field(default_factory=list)  # path, text, status, label
    photo_dirs: set[Path] = field(default_factory=set)  # vault-relative folders this render may file photos in
    vault: Path = Path()

    def flag(self, kind: str, text: str) -> None:
        self.flags.setdefault(kind, []).append(text)


def plan_render(cfg: A.Config, manifest: dict, archive: Path, vault: Path, now: datetime,
                recreate: set[str]) -> Plan:
    plan, taken, index = Plan(vault=vault), vault_stems(vault), note_index(vault)
    folders = {p["folder"] for p in manifest["projects"].values() if p.get("folder")}
    safe = templater_safe(vault)
    for cid, entry in sorted(manifest["conversations"].items()):
        state = entry.get("state")
        if state == "pending" or not entry.get("snapshot"):
            continue
        if cid in cfg.exclude:
            plan.excluded += 1
            continue
        pid = entry.get("project")
        if pid:
            proj = manifest["projects"].get(pid) or {}
            if not proj.get("name"):
                plan.flag("project name unknown (sync that project first)", cid)
                continue
            folder = proj.get("folder") or (plan.projects.get(pid) or {}).get("folder")
            if not folder:
                folder = R.folder_slug(proj["name"], pid, folders)
                folders.add(folder)
            project_stem = proj.get("note") or (plan.projects.get(pid) or {}).get("note")
            if not project_stem:
                project_stem = R.project_note_stem(proj["name"])
                if project_stem in taken and not (vault / TARGET / folder / f"{project_stem}.md").exists():
                    project_stem = f"{project_stem} {pid[:8]}"  # another note already has the name
                taken.add(project_stem)
            plan.projects[pid] = {"folder": folder, "note": project_stem}
        else:
            folder, project_stem = R.NO_PROJECT, None
        recorded = vault / entry["note"] if entry.get("note") else None
        if recorded is not None and recorded.exists():
            existing = recorded
        elif cid in index:
            existing = index[cid]
        elif recorded is not None and cid not in recreate:
            plan.flag("missing notes (not recreated; --recreate ID restores one)", entry["note"])
            continue
        else:
            existing = None
        if state in ("gone", "held"):
            if existing is not None:
                lines, body = R.split_note(existing.read_text(encoding="utf-8"))
                value = f"{state} ({entry.get('since')})"
                if R.frontmatter_values(lines).get("Upstream") != value:
                    fm = "\n".join(R.merge_frontmatter(lines, {"Upstream": value}, ("Upstream",)))
                    plan.writes.append((existing, f"---\n{fm}\n---\n{body}", "marked", cid))
                    plan.flag("now held: move or delete it by hand" if state == "held"
                              else "gone from claude.ai", rel(vault, existing))
                plan.paths[cid] = existing
            continue
        photo_dir = cfg.photos_dir(pid)
        plan.photo_dirs.add(photo_dir)
        try:
            conv = R.sanitize(json.loads((archive / entry["snapshot"]).read_text(encoding="utf-8")))
            names, copies, unreadable = plan_images(vault, archive, cid, entry, conv, photo_dir)
            rendered = R.render_region(conv, project_stem, cfg.owner_name, cfg.timezone, names)
            if rendered.message_ids:
                owned = R.transcript_frontmatter(conv, rendered, project_stem, now, cfg.timezone)
                title = R.clean_title(conv.get("name"))
        except Exception as e:  # noqa: BLE001 -- one bad chat must not stop the others; the name only, as its text can quote the chat
            plan.failed += 1
            plan.flag("couldn't be rendered, left alone", f"{cid} ({type(e).__name__})")
            continue
        for fid in unreadable:
            plan.flag("photos that can't be read, left out", f"{fid} in {cid}")
        if not rendered.message_ids:
            plan.empty += 1
            continue
        for kind in sorted(rendered.unknown_blocks):
            plan.flag("unknown block types, shown raw", f"{kind} in {cid}")
        if rendered.leaf_missing:
            plan.flag("current leaf missing, newest branch used", cid)
        if existing is not None:
            try:
                result = R.update_note(existing.read_text(encoding="utf-8"), owned,
                                       R.TRANSCRIPT_KEYS, rendered.region)
            except R.MarkerError as e:
                plan.flag("note shape damaged, left alone", f"{rel(vault, existing)}: {e}")
                continue
            path = existing
        else:
            stem = R.note_stem(rendered.start, title, cid, taken)
            taken.add(stem)
            path = vault / TARGET / folder / f"{stem}.md"
            result = R.NoteResult(R.new_note(owned, rendered.region), "new")
        if result.status == "unchanged":
            plan.unchanged += 1
            plan.paths[cid], plan.ids[cid] = path, rendered.message_ids
            plan.images[cid], plan.image_copies = names, plan.image_copies + copies
            continue
        status = result.status
        if set(entry.get("rendered_ids") or []) - set(rendered.message_ids):
            status = "non-additive"
        if "<%" in result.text and not safe:
            plan.flag("holds <% … %> text, not written until Templater ignores sources/ (see TODO.md)",
                      rel(vault, path))
            continue  # and not recorded: a note that was never written mustn't look hand-deleted later
        plan.paths[cid], plan.ids[cid] = path, rendered.message_ids
        plan.images[cid], plan.image_copies = names, plan.image_copies + copies
        grew = set(rendered.message_ids) != set(entry.get("rendered_ids") or [])  # photos alone don't count
        if (status != "new" and grew
                and R.frontmatter_values(R.split_note(result.text)[0]).get("Summary") != "pending"):
            plan.flag("summary may be out of date", rel(vault, path))
        plan.groups[status].append(f"{rel(vault, path)}  \"{title}\"")
        plan.writes.append((path, result.text, status, cid))
    plan_project_notes(plan, manifest, archive, vault, now, cfg.timezone, safe)
    return plan


def project_facts(archive: Path, proj: dict) -> tuple[str, str, list[tuple[str, int]]]:
    """(description, instructions, docs as name and size) from a project's latest archived
    details. All empty for a project known only from a single shared chat."""
    details = json.loads((archive / proj["details"]).read_text(encoding="utf-8")) if proj.get("details") else {}
    docs = json.loads((archive / proj["docs"]).read_text(encoding="utf-8")) if proj.get("docs") else []
    return (str(details.get("description") or ""), str(details.get("prompt_template") or ""),
            [(str(d.get("file_name") or "untitled"), len(d.get("content") or "")) for d in docs])


def plural(n: int, noun: str) -> str:
    return f"{n} {noun}{'' if n == 1 else 's'}"


def allowed_project(cfg: A.Config, ref: str) -> str:
    """The ID of a project listed in `allow`; config error (78) for any other."""
    entry = cfg.find_allowed(ref)
    if entry is None:
        raise A.ConfigError(f"{ref!r} isn't in allow in {cfg.path}. "
                            "Add it only after answering the protected-class question for it.")
    return entry["project"]


def waiting_chats(vault: Path, manifest: dict, pid: str) -> list[tuple[str, Path, str, int]]:
    """A project's chats still to process, oldest first: (id, note, created, photos). A chat
    waits until its note has a `Processed` mark, and again once the note holds a version of
    the chat that mark didn't cover: when the reply was sent doesn't matter, only that it's new."""
    index, rows = note_index(vault), []
    for cid, entry in manifest["conversations"].items():
        path = index.get(cid)
        if path is None or entry.get("project") != pid or entry.get("state", "active") != "active":
            continue
        values = R.frontmatter_values(R.split_note(path.read_text(encoding="utf-8"))[0])
        if not values.get("Processed") or values.get("Processed through") != values.get("Updated upstream"):
            rows.append((cid, path, values.get("Created", ""), len(entry.get("images") or {})))
    return sorted(rows, key=lambda row: row[2])


def chat_days(note_text: str) -> dict[str, tuple[str, str]]:
    """Each local day a chat has turns on, with that day's first and last time."""
    days: dict[str, tuple[str, str]] = {}
    for day, at in TURN_RE.findall(note_text):
        first, last = days.get(day, (at, at))
        days[day] = (min(first, at), max(last, at))
    return days


def insert_log_line(text: str, line: str) -> str:
    """Put one line directly under a daily note's `## Log` (or the older `## New notes`),
    adding the heading at the end if the note has neither. Nothing else moves."""
    lines = text.split("\n")
    heading = next((h for h in ("## Log", "## New notes") if h in lines), None)
    if heading is None:
        return f"{text.rstrip(chr(10))}\n\n## Log\n\n{line}\n"
    at = lines.index(heading) + 1
    if at < len(lines) and lines[at] == "":
        at += 1
    lines.insert(at, line)
    return "\n".join(lines)


def plan_daily(vault: Path, manifest: dict, pid: str, project: str, today: str) -> list[tuple[str, str, str, str]]:
    """The daily-note links still to add for a project's chats: (chat, day, note stem, line)."""
    rows = []
    index = note_index(vault)
    for cid, entry in sorted(manifest["conversations"].items()):
        path = index.get(cid)
        if path is None or entry.get("project") != pid or entry.get("state", "active") != "active":
            continue
        text = path.read_text(encoding="utf-8")
        written = R.frontmatter_values(R.split_note(text)[0]).get("Title", "")
        title = json.loads(written) if written.startswith('"') else written
        for day, (first, last) in sorted(chat_days(text).items()):
            if day not in (entry.get("daily") or []):
                span = first if first == last else f"{first}–{last}"
                named = f'"{R.escape_line(title)}", ' if title else ""
                rows.append((cid, day, path.stem, f'- [[{path.stem}]]: a Claude chat in {R.escape_line(project)}, '
                                                  f'{named}{span}. Mirrored on {today}.'))
    return rows


def apply_daily(vault: Path, manifest: dict, rows: list[tuple[str, str, str, str]]) -> int:
    """Write the links, each once, and remember each day so a link Dan removes stays removed."""
    added = 0
    for cid, day, stem, line in rows:
        path = vault / DAILY / day[:4] / day[5:7] / f"{day}.md"
        if path.exists():
            text = path.read_text(encoding="utf-8")
        else:
            template = vault / DAILY_TEMPLATE
            text = template.read_text(encoding="utf-8") if template.exists() else "## Log\n\n"
            path.parent.mkdir(parents=True, exist_ok=True)
        if f"[[{stem}]]" not in text:
            path.write_text(insert_log_line(text, line), encoding="utf-8")
            added += 1
        entry = manifest["conversations"][cid]
        entry["daily"] = sorted({*(entry.get("daily") or []), day})
    return added


def plan_project_notes(plan: Plan, manifest: dict, archive: Path, vault: Path, now: datetime, tz: str,
                       safe: bool) -> None:
    """A note per project with chats in the vault, so every chat's link to its project resolves."""
    for pid, decided in plan.projects.items():
        proj = manifest["projects"].get(pid) or {}
        stems = {(plan.paths[cid] if cid in plan.paths else Path(e["note"])).stem
                 for cid, e in manifest["conversations"].items()
                 if e.get("project") == pid and e.get("state", "active") == "active"
                 and (cid in plan.paths or e.get("note"))}
        path = vault / TARGET / decided["folder"] / f"{decided['note']}.md"
        owned = R.project_frontmatter(pid, proj.get("created_at"), now, tz)
        region = R.project_region(proj.get("name") or decided["note"], sorted(stems), *project_facts(archive, proj))
        if path.exists():
            try:
                result = R.update_note(path.read_text(encoding="utf-8"), owned, R.PROJECT_KEYS, region,
                                       R.PROJECT_BEGIN, R.PROJECT_END)
            except R.MarkerError as e:
                plan.flag("note shape damaged, left alone", f"{rel(vault, path)}: {e}")
                continue
        else:
            result = R.NoteResult(R.new_project_note(owned, region), "new")
        if result.status != "unchanged" and "<%" in result.text and not safe:
            plan.flag("holds <% … %> text, not written until Templater ignores sources/ (see TODO.md)", rel(vault, path))
            continue
        if result.status != "unchanged":
            plan.project_writes.append((path, result.text, result.status, rel(vault, path)))


def apply_plan(plan: Plan, manifest: dict, vault: Path) -> None:
    roots = [(vault / folder).resolve() for folder in (TARGET, IMAGES, *plan.photo_dirs)]

    def allowed(path: Path) -> None:
        if not any(path.resolve().is_relative_to(r) for r in roots):
            raise A.ConfigError(f"refusing to write outside {TARGET} and the photo folders: {path}")

    for src, dest in plan.image_copies:
        allowed(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(clean_image(src.read_bytes()))
    for path, text in [(p, t) for p, t, _s, _c in plan.writes] + [(p, t) for p, t, _s, _l in plan.project_writes]:
        allowed(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    for cid, path in plan.paths.items():
        entry = manifest["conversations"][cid]
        entry["note"] = rel(vault, path)
        if cid in plan.ids:
            entry["rendered_ids"] = plan.ids[cid]
        if plan.images.get(cid):
            entry["images"] = plan.images[cid]
    for pid, decided in plan.projects.items():
        proj = manifest["projects"].setdefault(pid, {})
        proj.setdefault("folder", decided["folder"])
        proj.setdefault("note", decided["note"])


def print_plan(plan: Plan, applied: bool) -> None:
    print("Claude chats — " + ("written" if applied else "dry run (nothing written; add --apply to write)"))
    for group in ("new", "updated", "non-additive"):
        if plan.groups[group]:
            print(f"  {'⚠ ' if group == 'non-additive' else ''}{group} ({len(plan.groups[group])}):")
            for label in plan.groups[group]:
                print(f"    {label}")
    print(f"  unchanged: {plan.unchanged} · excluded: {plan.excluded} · empty: {plan.empty}")
    for folder in sorted({dest.parent for _src, dest in plan.image_copies}):
        count = sum(dest.parent == folder for _src, dest in plan.image_copies)
        print(f"  photos to file in {folder.relative_to(plan.vault)}: {count}")
    for _path, _text, status, label in plan.project_writes:
        print(f"  project note ({status}): {label}")
    for kind, items in plan.flags.items():
        print(f"  {kind}:")
        for item in items:
            print(f"    {item}")


def daily_line(plan: Plan) -> str:
    new = [p for p, _t, s, _c in plan.writes if s == "new"]
    upd = [p for p, _t, s, _c in plan.writes if s in ("updated", "non-additive")]
    if not new and not upd:
        return "Nothing new to log."
    stems = [d["note"] for d in plan.projects.values()] if len(new + upd) > 5 and plan.projects else [p.stem for p in new + upd]
    links = ", ".join(f"[[{stem}]]" for stem in stems)
    return f"- Synced Claude chats: {len(new)} new, {len(upd)} updated — {links}"


def pending_summaries(vault: Path) -> list[tuple[str, Path, str]]:
    rows = []
    root = vault / TARGET
    for path in sorted(root.rglob("*.md")) if root.exists() else []:
        lines, _ = R.split_note(path.read_text(encoding="utf-8"))
        values = R.frontmatter_values(lines)
        if values.get("Summary") == "pending" and values.get("Conversation ID"):
            rows.append((values["Conversation ID"], path, values.get("Messages", "?")))
    return rows


def main(argv: list[str] | None = None, trash=None, now: datetime | None = None) -> int:
    ap = argparse.ArgumentParser(prog="claude_chats.py", exit_on_error=False,
                                 description="Mirror claude.ai chats into the vault.")
    ap.add_argument("--archive", type=Path, default=None, help="default: from the vault's .claude/claude-chats.toml")
    ap.add_argument("--vault", type=Path, default=Path.cwd(), help="default: the working directory")
    sub = ap.add_subparsers(dest="cmd", required=True)
    np = sub.add_parser("snippet")
    np.add_argument("link", nargs="?")
    np.add_argument("--project", metavar="NAME-OR-ID")
    ip = sub.add_parser("ingest")
    ip.add_argument("files", nargs="*", type=Path)
    ip.add_argument("--wait", type=float, default=0, metavar="SECONDS")
    rp = sub.add_parser("render")
    rp.add_argument("--apply", action="store_true")
    rp.add_argument("--recreate", action="append", default=[])
    sub.add_parser("summaries")
    sp = sub.add_parser("summary")
    sp.add_argument("id")
    sp.add_argument("--file", type=Path, required=True)
    how = sp.add_mutually_exclusive_group()
    how.add_argument("--force", action="store_true")
    how.add_argument("--update", action="store_true")
    sub.add_parser("status")
    sub.add_parser("queue").add_argument("--project", required=True, metavar="NAME-OR-ID")
    sub.add_parser("processed").add_argument("id")
    dp = sub.add_parser("daily")
    dp.add_argument("--project", required=True, metavar="NAME-OR-ID")
    dp.add_argument("--apply", action="store_true")
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        return 0 if e.code == 0 else 64
    except argparse.ArgumentError as e:
        print(f"usage error: {e}", file=sys.stderr)
        return 64
    now = now or datetime.now(timezone.utc)
    if trash is None:
        from send2trash import send2trash
        trash = lambda p: send2trash(str(p))  # noqa: E731
    try:
        return _run(args, now, trash)
    except A.ArchiveError as e:
        print(f"error: {e}", file=sys.stderr)
        return e.code
    except Exception:  # noqa: BLE001 -- reported as 70, never mistaken for a partial run
        traceback.print_exc()
        return 70


def _run(args, now: datetime, trash) -> int:
    vault = args.vault
    archive = args.archive or A.vault_archive(vault)
    cfg = A.load_config(archive)
    if args.cmd == "snippet":
        if bool(args.link) == bool(args.project):
            print("usage error: give one share link or chat URL, or --project NAME", file=sys.stderr)
            return 64
        if args.project:
            print(project_snippet_js(allowed_project(cfg, args.project), cfg, A.load_manifest(archive)))
            return 0
        ids = parse_link(args.link)
        if ids is None:
            print(f"usage error: not a claude.ai share link or chat URL: {args.link!r}", file=sys.stderr)
            return 64
        print(snippet_js(*ids, cfg))
        return 0
    if args.cmd == "ingest":
        def downloads() -> list[Path]:
            return (A.find_project_bundles(cfg, archive) + A.find_chat_bundles(cfg, archive)
                    + A.find_captures(cfg, archive) + A.find_file_bundles(cfg, archive))
        files = args.files or downloads()
        deadline = time.monotonic() + args.wait
        while not files and time.monotonic() < deadline:  # Chrome renames a download into place when done
            time.sleep(0.25)
            files = downloads()
        if not files:
            raise A.NoBundle(f"nothing to ingest: no {A.PROJECT_GLOB}, {A.CHAT_GLOB}, {A.CAPTURE_GLOB} or {A.FILES_GLOB} "
                             f"in {cfg.downloads_dir} or {archive / 'conversations'}")
        total = len(files)
        projects = [p for p in files if p.name.startswith("claude-project-")]
        chats = [p for p in files if p.name.startswith("claude-chat-")]
        bundles = [p for p in files if p.name.startswith("claude-files-")]
        files = [p for p in files if p not in bundles and p not in chats and p not in projects]
        code, held = 0, set()
        with A.Lock(archive):
            manifest = A.load_manifest(archive)
            for path in projects:
                try:
                    p = A.ingest_project(archive, cfg, manifest, path, now, trash)
                except A.BadBundle as e:
                    print(f"  error      {path.name}: {e}")
                    code = 65 if total == 1 else 1
                    continue
                if p.status == "held":
                    print(f"  held       project {p.project}  (matched a hold rule: not archived; the download went to the Trash)")
                    continue
                notes = [f"{p.new} new", f"{p.changed} changed", f"{p.unchanged} unchanged", f"{p.photos} photos",
                         f"{p.gone} gone", f"{len(p.held)} held"]
                notes += ["first sync"] if p.first_sync else []
                notes += [f"{p.errors} failed and will be fetched next time"] if p.errors else []
                notes += ["more to fetch: run it again"] if p.more else []
                notes += ["the chat list came back partial, so nothing was marked gone"] if not p.list_complete else []
                notes += ["it held a chat a hold rule covers, so the download went to the Trash"] if not p.kept and p.status != "unchanged" else []
                print(f"  {p.status:<10} project {p.project}  ({', '.join(notes)})")
            for path in chats:
                try:
                    r = A.ingest_chat(archive, cfg, manifest, path, now, trash)
                except A.BadBundle as e:
                    print(f"  error      {path.name}: {e}")
                    code = 65 if total == 1 else 1
                    continue
                if r.status == "held":
                    held.add(r.uuid)
                photos = f"{r.added} photo{'s' if r.added != 1 else ''}"
                if r.status == "held":
                    note = "matched a hold rule: not archived; the download went to the Trash"
                elif r.status == "unchanged":
                    note = (f"chat already archived; {photos} added" if r.added
                            else "already archived; the duplicate went to the Trash")
                else:
                    note = f"{photos} archived" if r.added else ""
                print(f"  {r.status:<10} {r.uuid}" + (f"  ({note})" if note else ""))
            for path in files:
                try:
                    r = A.ingest_capture(archive, cfg, manifest, path, now, trash)
                except A.BadBundle as e:
                    print(f"  error      {path.name}: {e}")
                    code = 65 if total == 1 else 1
                    continue
                if r.status == "held":
                    held.add(r.uuid)
                note = ("  (matched a hold rule: not archived; the download went to the Trash)"
                        if r.status == "held" else "")
                print(f"  {r.status:<10} {r.uuid}{note}")
            for path in bundles:
                try:
                    r = A.ingest_files(archive, cfg, manifest, path, now, trash, held=held)
                except A.BadBundle as e:
                    print(f"  error      {path.name}: {e}")
                    code = 65 if total == 1 else 1
                    continue
                what = {"held": "photos of a held chat: not archived; the download went to the Trash",
                        "unchanged": "photos already archived; the duplicate went to the Trash",
                        "new": f"{r.added} photo{'s' if r.added != 1 else ''} archived"}[r.status]
                print(f"  {r.status:<10} {r.uuid}  ({what})")
            A.save_manifest(archive, manifest)
        return code
    if args.cmd == "render":
        manifest = A.load_manifest(archive)
        plan = plan_render(cfg, manifest, archive, vault, now, set(args.recreate))
        code = 1 if plan.failed else 0
        if not args.apply:
            print_plan(plan, applied=False)
            return code
        with A.Lock(archive):
            manifest = A.load_manifest(archive)
            apply_plan(plan, manifest, vault)
            A.save_manifest(archive, manifest)
        print_plan(plan, applied=True)
        print(daily_line(plan))
        return code
    if args.cmd == "summaries":
        rows = pending_summaries(vault)
        for cid, path, messages in rows:
            print(f"{cid}  {rel(vault, path)}  ({messages} messages)")
        if not rows:
            print("No notes are waiting for a summary.")
        return 0
    if args.cmd == "summary":
        path = note_index(vault).get(args.id)
        if path is None:
            raise A.NoBundle(f"no note under {TARGET} has Conversation ID {args.id}")
        text = args.file.read_text(encoding="utf-8")
        if "<%" in text and not templater_safe(vault):
            raise A.ConfigError("the summary holds <% … %> text and Templater would run it")
        today = f"{now.astimezone(ZoneInfo(cfg.timezone)):%Y-%m-%d}"
        note = path.read_text(encoding="utf-8")
        pending = R.frontmatter_values(R.split_note(note)[0] or []).get("Summary", "pending") == "pending"
        try:
            if args.update and not pending:
                updated = R.add_summary_update(note, text, today)
            else:
                updated = R.set_summary(note, text, f"Claude {today}", force=args.force)
        except R.AlreadySummarized as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        except R.MarkerError as e:
            raise A.BadBundle(f"{rel(vault, path)}: {e}") from e
        path.write_text(updated, encoding="utf-8")
        print(f"summary written to {rel(vault, path)}")
        return 0
    if args.cmd == "queue":
        rows = waiting_chats(vault, A.load_manifest(archive), allowed_project(cfg, args.project))
        for cid, path, created, photos in rows:
            print(f"{cid}  {rel(vault, path)}  {created}  ({plural(photos, 'photo')})")
        print(f"{plural(len(rows), 'chat')} waiting, {plural(sum(r[3] for r in rows), 'photo')}")
        return 0
    if args.cmd == "daily":
        pid = allowed_project(cfg, args.project)
        today = f"{now.astimezone(ZoneInfo(cfg.timezone)):%Y-%m-%d}"
        name = cfg.find_allowed(pid)["name"]
        if not args.apply:
            rows = plan_daily(vault, A.load_manifest(archive), pid, name, today)
            for _cid, day, stem, _line in rows:
                print(f"  {day}  {stem}")
            print(f"{plural(len(rows), 'link')} to add (dry run; add --apply to write)")
            return 0
        with A.Lock(archive):
            manifest = A.load_manifest(archive)
            added = apply_daily(vault, manifest, plan_daily(vault, manifest, pid, name, today))
            A.save_manifest(archive, manifest)
        print(f"{plural(added, 'link')} written")
        return 0
    if args.cmd == "processed":
        path = note_index(vault).get(args.id)
        if path is None:
            raise A.NoBundle(f"no note under {TARGET} has Conversation ID {args.id}")
        stamp = R.minute(now.astimezone(ZoneInfo(cfg.timezone)))
        try:
            updated = R.stamp_processed(path.read_text(encoding="utf-8"), stamp)
        except R.MarkerError as e:
            raise A.BadBundle(f"{rel(vault, path)}: {e}") from e
        path.write_text(updated, encoding="utf-8")
        print(f"processed {args.id} at {stamp}")
        return 0
    if args.cmd == "status":
        manifest = A.load_manifest(archive)
        states: dict[str, int] = {}
        for entry in manifest["conversations"].values():
            states[entry.get("state", "?")] = states.get(entry.get("state", "?"), 0) + 1
        print(f"config:    {cfg.path}")
        print(f"archive:   {archive}")
        waiting = sum(len(find(cfg, archive)) for find in (A.find_project_bundles, A.find_chat_bundles, A.find_captures))
        print(f"downloads: {cfg.downloads_dir} and {archive / 'conversations'} "
              f"({waiting} chats waiting to be ingested)")
        print("chats:     " + (", ".join(f"{k} {v}" for k, v in sorted(states.items())) or "none yet"))
        print(f"summaries: {len(pending_summaries(vault))} waiting")
        print("templater: " + ("safe" if templater_safe(vault) else
                               "guard on: notes holding <% … %> are not written until Templater ignores sources/"))
        return 0
    return 64


if __name__ == "__main__":
    sys.exit(main())

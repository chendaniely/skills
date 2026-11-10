#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "markdown-it-py>=3.0",
# ]
# ///
"""Archive side of claude_chats.py: config, hold rule, manifest, lock, ingest.

Knows nothing about the vault's contents. The archive lives outside the vault, at the path
in the vault's .claude/claude-chats.toml, and is append-only: a download is moved in byte
for byte, and snapshots are never deleted.

Layout:
  config.toml                              owner, timezone, downloads_dir, holds, exclude, allow
  manifest.json                            per-conversation state; holds no chat titles
  conversations/<uuid>/<updated_at>.json   one file per distinct version, verbatim
  conversations/<uuid>/files/              its photos (claude.ai's preview copies), decoded,
                                           plus each claude-files-*.json bundle, verbatim, in bundles/
  conversations/<uuid>/downloads/          each claude-chat-*.json download (chat + photos), verbatim
  conversations/claude-*.json              a download saved straight here; ingest takes it like
                                           one in downloads_dir and moves it into place
  projects/<id>/details-*.json, docs-*.json  a project's details and docs, verbatim, when they change
  projects/<id>/bundles/                   each claude-project-*.json download, verbatim
  .lock
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
import re
import shutil
import socket
import tomllib
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import claude_chats_render as R

PROJECT_GLOB = "claude-project-*.json"  # a whole project's new or changed chats, in one download
CHAT_GLOB = "claude-chat-*.json"  # a chat and its photos in one download, from the skill's snippet
CAPTURE_GLOB = "claude-conversation-*.json"  # older two-file form: the chat alone ...
FILES_GLOB = "claude-files-*.json"  # ... and its photos
DEFAULT_PHOTOS = Path("ze-files") / "claude"
SAFE_ID = re.compile(r"[A-Za-z0-9_-]+")  # ingest reads any matching file in Downloads, so IDs inside one can't be trusted as paths
MIME_EXT = {"image/webp": "webp", "image/jpeg": "jpg", "image/png": "png", "image/gif": "gif"}
DEFAULT_HOLD_PREFIXES = ("private",)
DEFAULT_HOLD_PATTERNS = ("interview:",)
REQUIRED_MESSAGE_FIELDS = ("uuid", "sender", "created_at", "content", "parent_message_uuid")

DEFAULT_CONFIG = """# claude-chats archive config. Edit freely.
owner_name = "Me"
timezone = "UTC"
downloads_dir = "~/Downloads"
delay_ms = 500

# A chat or project whose title starts with a prefix, or contains a pattern, is never
# fetched, archived or rendered. Matching ignores case, spaces and punctuation, and the
# defaults ("private", "interview:") always apply, whatever is written here.
hold_prefixes = ["private"]
hold_patterns = ["interview:"]

# Conversation IDs never rendered into the vault (Dan's veto).
exclude = []

# Projects to sync. Add one only after answering, for that project: could chats here
# discuss a student, a therapy subject, or anyone you evaluate? `ack` records the date
# you answered no. Example: { project = "<uuid>", name = "Homelab", ack = "2026-10-15" }
allow = [
]
"""


class ArchiveError(Exception):
    code = 1


class ConfigError(ArchiveError):
    code = 78


class LockHeld(ArchiveError):
    code = 75


class NoBundle(ArchiveError):
    code = 66


class BadBundle(ArchiveError):
    code = 65


@dataclass
class Config:
    path: Path
    owner_name: str
    timezone: str
    downloads_dir: Path
    delay_ms: int
    hold_prefixes: list[str]
    hold_patterns: list[str]
    exclude: set[str]
    allow: list[dict]

    @property
    def allowed(self) -> set[str]:
        return {a["project"] for a in self.allow}

    def find_allowed(self, ref: str) -> dict | None:
        """The `allow` entry for a project ID or name, ignoring case, spaces and punctuation."""
        wanted = normalize_title(ref)
        for entry in self.allow:
            if ref == entry["project"] or (wanted and normalize_title(entry["name"]) == wanted):
                return entry
        return None

    def photos_dir(self, project: str | None) -> Path:
        """The vault folder for a project's photos: its own if `allow` names one."""
        for entry in self.allow:
            if entry["project"] == project and entry.get("photos"):
                return Path(entry["photos"])
        return DEFAULT_PHOTOS


def vault_archive(vault: Path) -> Path:
    """Where this vault keeps its archive: `archive` in .claude/claude-chats.toml, relative to
    the vault, so one setting works on every machine the vault syncs to."""
    path = vault / ".claude" / "claude-chats.toml"
    try:
        value = tomllib.loads(path.read_text(encoding="utf-8"))["archive"]
    except FileNotFoundError:
        raise ConfigError(f'{path} is missing: run this from the vault root, and set archive = "<folder>" there') from None
    except (tomllib.TOMLDecodeError, KeyError, TypeError) as e:
        raise ConfigError(f"{path}: {e!r}") from e
    return (vault / str(value)).resolve()


def load_config(archive: Path) -> Config:
    path = archive / "config.toml"
    if not path.exists():
        archive.mkdir(parents=True, exist_ok=True)
        path.write_text(DEFAULT_CONFIG, encoding="utf-8")
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
        allow = []
        for entry in raw.get("allow", []):
            if not entry.get("ack"):
                raise ValueError(f"allow entry for project {entry.get('project')!r} has no ack "
                                 "(the protected-class question must be answered first)")
            photos = entry.get("photos")
            if photos is not None and (Path(str(photos)).is_absolute() or ".." in Path(str(photos)).parts):
                raise ValueError(f"allow entry for project {entry.get('project')!r}: photos must be a folder inside the vault")
            allow.append({"project": str(entry["project"]), "name": str(entry.get("name", "")),
                          "ack": str(entry["ack"]), **({"photos": str(photos)} if photos else {})})
        cfg = Config(
            path=path,
            owner_name=str(raw.get("owner_name", "Me")),
            timezone=str(raw.get("timezone", "UTC")),
            downloads_dir=Path(str(raw.get("downloads_dir", "~/Downloads"))).expanduser(),
            delay_ms=int(raw.get("delay_ms", 500)),
            hold_prefixes=[str(p) for p in raw.get("hold_prefixes", list(DEFAULT_HOLD_PREFIXES))],
            hold_patterns=[str(p) for p in raw.get("hold_patterns", list(DEFAULT_HOLD_PATTERNS))],
            exclude={str(c) for c in raw.get("exclude", [])},
            allow=allow,
        )
        ZoneInfo(cfg.timezone)
    except (tomllib.TOMLDecodeError, KeyError, TypeError, ValueError, ZoneInfoNotFoundError) as e:
        raise ConfigError(f"{path}: {e}") from e
    return cfg


def normalize_title(title: str | None) -> str:
    """Fold case and lookalike characters (NFKC), keep only letters, digits and colons."""
    return re.sub(r"[^a-z0-9:]", "", unicodedata.normalize("NFKC", title or "").lower())


def is_held(title: str | None, prefixes: list[str], patterns: list[str]) -> bool:
    """True if a title must be held. Same rule as isHeld() in the browser snippet."""
    t = normalize_title(title)
    pre = {normalize_title(p) for p in [*prefixes, *DEFAULT_HOLD_PREFIXES]} - {""}
    pat = {normalize_title(p) for p in [*patterns, *DEFAULT_HOLD_PATTERNS]} - {""}
    return any(t.startswith(p) for p in pre) or any(p in t for p in pat)


class Lock:
    def __init__(self, archive: Path):
        self.path = archive / ".lock"

    def __enter__(self) -> "Lock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            held_by = self.path.read_text(errors="replace").strip()
            raise LockHeld(f"{self.path} exists ({held_by}). Another sync is running; "
                           "if none is, delete that file.") from None
        with os.fdopen(fd, "w") as f:
            f.write(f"{socket.gethostname()} pid {os.getpid()} {datetime.now(timezone.utc).isoformat()}")
        return self

    def __exit__(self, *exc) -> None:
        self.path.unlink(missing_ok=True)


def conflict_copies(archive: Path) -> list[Path]:
    if not archive.exists():
        return []
    return sorted(p for p in archive.iterdir()
                  if "conflict" in p.name.lower() and p.name.startswith(("manifest", "config")))


def empty_manifest() -> dict:
    return {"schema": 1, "pending": None, "projects": {}, "conversations": {}, "last_ingest": None}


def load_manifest(archive: Path) -> dict:
    path = archive / "manifest.json"
    if not path.exists():
        return empty_manifest()
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ConfigError(f"{path}: {e}") from e


def save_manifest(archive: Path, manifest: dict) -> None:
    archive.mkdir(parents=True, exist_ok=True)
    path = archive / "manifest.json"
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)


def canonical_hash(obj) -> str:
    text = json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("ascii")).hexdigest()


def _stamp(value) -> str:
    """A timestamp as a file name: anything that could change folders becomes a dash."""
    return re.sub(r"[^0-9A-Za-z.-]", "-", str(value))


def is_timestamp(value) -> bool:
    """A value is safe to file under and to convert to a local time. These come from downloads."""
    if not isinstance(value, str) or len(value) > 40:
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def validate_conversation(conv, where: str) -> None:
    def bad(what: str):
        raise BadBundle(f"{where}: {what}")

    if not isinstance(conv, dict):
        bad("not a conversation object")
    for key in ("uuid", "name", "updated_at", "chat_messages"):
        if key not in conv:
            bad(key)
    if not isinstance(conv["chat_messages"], list):
        bad("chat_messages is not a list")
    if not SAFE_ID.fullmatch(str(conv["uuid"])):
        bad("uuid is not a plain ID")
    if conv.get("project_uuid") and not SAFE_ID.fullmatch(str(conv["project_uuid"])):
        bad("project_uuid is not a plain ID")
    if not is_timestamp(conv["updated_at"]):
        bad("updated_at is not a timestamp")
    for i, m in enumerate(conv["chat_messages"]):
        if not isinstance(m, dict):
            bad(f"chat_messages[{i}] is not an object")
        for key in REQUIRED_MESSAGE_FIELDS:
            if key not in m:
                bad(f"chat_messages[{i}].{key}")
        if not is_timestamp(m["created_at"]):
            bad(f"chat_messages[{i}].created_at is not a timestamp")


def _find_downloads(cfg: Config, archive: Path, pattern: str) -> list[Path]:
    """Downloads waiting in downloads_dir or saved straight into the archive's conversations/
    folder, which Chrome's Save dialog keeps offering once one download has gone there.
    Only the top level is searched, so archived snapshots are never picked up again."""
    found: dict[Path, Path] = {}
    for folder in (cfg.downloads_dir, archive / "conversations"):
        for path in folder.glob(pattern):
            found.setdefault(path.resolve(), path)
    return sorted(found.values())


def find_captures(cfg: Config, archive: Path) -> list[Path]:
    return _find_downloads(cfg, archive, CAPTURE_GLOB)


@dataclass
class CaptureReport:
    source: Path
    uuid: str
    status: str  # "new" | "changed" | "unchanged" | "held"


def _refuse_conflicts(archive: Path) -> None:
    copies = conflict_copies(archive)
    if copies:
        raise ConfigError(f"A sync conflict copy is in the archive: {copies[0].name}. Merge it by hand first.")


def _same_as_archived(archive: Path, entry: dict | None, conv: dict) -> bool:
    latest = archive / entry["snapshot"] if entry and entry.get("snapshot") else None
    return bool(latest and latest.exists()
                and canonical_hash(json.loads(latest.read_bytes())) == canonical_hash(conv))


def _snapshot_dest(archive: Path, conv: dict) -> Path:
    folder = archive / "conversations" / str(conv["uuid"])
    folder.mkdir(parents=True, exist_ok=True)
    stamp = _stamp(conv["updated_at"])
    dest = folder / f"{stamp}.json"
    return folder / f"{stamp}-{canonical_hash(conv)[:8]}.json" if dest.exists() else dest


def _record_snapshot(archive: Path, manifest: dict, conv: dict, dest: Path, now: datetime) -> str:
    """Point the chat's manifest entry at a new snapshot. Every other key it already had
    (its photos, their vault names, its note) is kept."""
    cid = str(conv["uuid"])
    entry = manifest["conversations"].get(cid) or {}
    status = "changed" if entry.get("snapshot") else "new"
    manifest["conversations"][cid] = {
        **entry,
        "project": R.sanitize(conv.get("project_uuid")) or None,
        "updated_at": conv["updated_at"],
        "snapshot": str(dest.relative_to(archive)),
        "state": "active",
        "source": entry.get("source", "capture"),
        "note": entry.get("note"),
        "rendered_ids": entry.get("rendered_ids", []),
        "since": None,
    }
    manifest["last_ingest"] = now.isoformat()
    return status


def _keep_download(src: Path, folder: Path, stamp: str, raw: bytes) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / f"{stamp}.json"
    if dest.exists():
        dest = folder / f"{stamp}-{hashlib.sha256(raw).hexdigest()[:8]}.json"
    shutil.move(src, dest)


def ingest_capture(archive: Path, cfg: Config, manifest: dict, src: Path, now: datetime,
                   trash) -> CaptureReport:
    """Archive one downloaded conversation (raw API JSON), byte for byte."""
    _refuse_conflicts(archive)
    raw = src.read_bytes()
    try:
        conv = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise BadBundle(f"{src.name}: not JSON ({e})") from e
    validate_conversation(conv, src.name)
    cid = str(conv["uuid"])
    if is_held(conv.get("name"), cfg.hold_prefixes, cfg.hold_patterns):
        trash(src)  # held: never archived; reported by ID only
        return CaptureReport(src, cid, "held")
    if _same_as_archived(archive, manifest["conversations"].get(cid), conv):
        trash(src)  # an exact duplicate of what is archived
        return CaptureReport(src, cid, "unchanged")
    dest = _snapshot_dest(archive, conv)
    shutil.move(src, dest)  # last step: nothing above can strand the download
    return CaptureReport(src, cid, _record_snapshot(archive, manifest, conv, dest, now))


def find_chat_bundles(cfg: Config, archive: Path) -> list[Path]:
    return _find_downloads(cfg, archive, CHAT_GLOB)


@dataclass
class ChatReport:
    source: Path
    uuid: str
    status: str  # "new" | "changed" | "unchanged" | "held"
    added: int = 0


def ingest_chat(archive: Path, cfg: Config, manifest: dict, src: Path, now: datetime,
                trash) -> ChatReport:
    """Archive one claude-chat-*.json: a chat's raw API text and its photos, in one download.

    Everything is checked before anything is written, so a bad file leaves the archive as it
    was and stays where it is. The chat is archived byte for byte as the API sent it, its
    photos are decoded beside it, and the download itself is kept in downloads/ unless it
    added nothing. A held chat goes to the Trash, photos and all, and is never archived.
    """
    _refuse_conflicts(archive)
    raw = src.read_bytes()
    try:
        bundle = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise BadBundle(f"{src.name}: not JSON ({e})") from e
    if (not isinstance(bundle, dict) or bundle.get("schema") != 1 or bundle.get("kind") != "claude-chat"
            or not isinstance(bundle.get("conversation"), str)
            or not isinstance(bundle.get("files", {}), dict)):
        raise BadBundle(f"{src.name}: not a claude-chat file (schema 1)")
    try:
        text = bundle["conversation"].encode("utf-8")
        conv = json.loads(text)
    except (UnicodeEncodeError, json.JSONDecodeError) as e:
        raise BadBundle(f"{src.name}: its conversation is not JSON text ({e})") from e
    validate_conversation(conv, f"{src.name}: conversation")
    cid = str(conv["uuid"])
    project = bundle.get("project") if isinstance(bundle.get("project"), dict) else {}
    pid = R.sanitize(conv.get("project_uuid")) or None
    pname = project.get("name") if pid and project.get("uuid") == pid else None
    if (is_held(conv.get("name"), cfg.hold_prefixes, cfg.hold_patterns)
            or is_held(pname, cfg.hold_prefixes, cfg.hold_patterns)):
        trash(src)
        return ChatReport(src, cid, "held")
    decoded = _decode_photos(bundle.get("files") or {}, src.name)
    if project.get("created_at") and not is_timestamp(project["created_at"]):
        raise BadBundle(f"{src.name}: its project's created_at is not a timestamp")
    if pname:  # its name only: folder and note are fixed the first time render files the project
        known = manifest["projects"].setdefault(pid, {})
        known["name"] = R.sanitize(pname)
        if project.get("created_at") and "created_at" not in known:
            known["created_at"] = str(project["created_at"])
    if _same_as_archived(archive, manifest["conversations"].get(cid), conv):
        status = "unchanged"
    else:
        dest = _snapshot_dest(archive, conv)
        dest.write_bytes(text)
        status = _record_snapshot(archive, manifest, conv, dest, now)
    added = _store_photos(archive, manifest["conversations"][cid], cid, decoded)
    if status == "unchanged" and not added:
        trash(src)  # nothing new in it
        return ChatReport(src, cid, "unchanged")
    stamp = _stamp(bundle.get("fetched_at") or now.isoformat())
    _keep_download(src, archive / "conversations" / cid / "downloads", stamp, raw)
    manifest["last_ingest"] = now.isoformat()
    return ChatReport(src, cid, status, added)


def find_file_bundles(cfg: Config, archive: Path) -> list[Path]:
    return _find_downloads(cfg, archive, FILES_GLOB)


@dataclass
class FilesReport:
    source: Path
    uuid: str
    status: str  # "new" | "unchanged" | "held"
    added: int = 0


def ingest_files(archive: Path, cfg: Config, manifest: dict, src: Path, now: datetime, trash,
                 held: set[str] = frozenset()) -> FilesReport:
    """Archive one claude-files-*.json bundle: the photo previews of one archived chat.

    The bundle is kept byte for byte and each photo is decoded beside it. A held chat's
    photos go to the Trash unarchived, like the chat itself; a chat that isn't archived
    yet is refused, so its photos can't outlive a hold the chat would have hit.
    """
    _refuse_conflicts(archive)
    raw = src.read_bytes()
    try:
        bundle = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise BadBundle(f"{src.name}: not JSON ({e})") from e
    if (not isinstance(bundle, dict) or bundle.get("schema") != 1
            or bundle.get("kind") != "claude-chat-files" or not isinstance(bundle.get("files"), dict)):
        raise BadBundle(f"{src.name}: not a claude-chat-files bundle (schema 1)")
    cid = str(bundle.get("conversation") or "")
    if cid in held:
        trash(src)
        return FilesReport(src, cid, "held")
    entry = manifest["conversations"].get(cid)
    if not entry or not entry.get("snapshot"):
        raise BadBundle(f"{src.name}: conversation {cid} isn't archived; ingest its claude-conversation file first")
    added = _store_photos(archive, entry, cid, _decode_photos(bundle["files"], src.name))
    if not added:
        trash(src)  # every photo is already archived
        return FilesReport(src, cid, "unchanged")
    stamp = _stamp(bundle.get("fetched_at") or now.isoformat())
    _keep_download(src, archive / "conversations" / cid / "files" / "bundles", stamp, raw)  # last step
    manifest["last_ingest"] = now.isoformat()
    return FilesReport(src, cid, "new", added)


def _decode_photos(files: dict, where: str) -> dict:
    """Check and decode every photo before anything is written."""
    decoded = {}
    for fid, f in files.items():
        at = f"{where}: files[{fid}]"
        if not SAFE_ID.fullmatch(str(fid)):
            raise BadBundle(f"{at}: not a plain ID")
        if not isinstance(f, dict):
            raise BadBundle(f"{at}: not an object")
        ext = MIME_EXT.get(f.get("mime"))
        if not ext:
            raise BadBundle(f"{at}: unsupported type {f.get('mime')!r}")
        try:
            data = base64.b64decode(f.get("base64") or "", validate=True)
        except (binascii.Error, ValueError) as e:
            raise BadBundle(f"{at}: not base64 ({e})") from e
        if len(data) != f.get("bytes"):
            raise BadBundle(f"{at}: {len(data)} bytes decoded, expected {f.get('bytes')}")
        decoded[fid] = (data, ext, f)
    return decoded


def _store_photos(archive: Path, entry: dict, cid: str, decoded: dict) -> int:
    """Write the photos the archive doesn't already hold; return how many were new."""
    folder = archive / "conversations" / cid / "files"
    known = entry.setdefault("files", {})
    added = 0
    for fid, (data, ext, f) in decoded.items():
        digest = hashlib.sha256(data).hexdigest()
        rec = known.get(fid)
        if rec and rec.get("sha256") == digest and (archive / rec["path"]).exists():
            continue
        folder.mkdir(parents=True, exist_ok=True)
        dest = folder / f"{fid}.{ext}"
        if dest.exists():
            dest = folder / f"{fid}-{digest[:8]}.{ext}"
        dest.write_bytes(data)
        known[fid] = {"path": str(dest.relative_to(archive)), "file_name": R.sanitize(f.get("file_name")) or "",
                      "mime": f.get("mime"), "sha256": digest}
        added += 1
    return added


def find_project_bundles(cfg: Config, archive: Path) -> list[Path]:
    return _find_downloads(cfg, archive, PROJECT_GLOB)


@dataclass
class ProjectReport:
    source: Path
    project: str
    status: str  # "synced" | "unchanged" | "held"
    first_sync: bool = False
    new: int = 0
    changed: int = 0
    unchanged: int = 0
    photos: int = 0
    gone: int = 0
    held: list[str] = field(default_factory=list)
    more: bool = False
    errors: int = 0
    kept: bool = True  # False when the download went to the Trash instead of the archive
    list_complete: bool = True


def _check_project_file(src: Path, cfg: Config) -> tuple[dict, dict, bytes]:
    raw = src.read_bytes()
    try:
        bundle = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise BadBundle(f"{src.name}: not JSON ({e})") from e
    if (not isinstance(bundle, dict) or bundle.get("schema") != 1 or bundle.get("kind") != "claude-project"
            or not all(isinstance(bundle.get(k), str) for k in ("project_id", "project", "docs"))
            or not all(isinstance(bundle.get(k), list) for k in ("list", "held"))
            or not all(isinstance(bundle.get(k), dict) for k in ("conversations", "files"))
            or not all(isinstance(i, dict) for i in bundle["list"])):
        raise BadBundle(f"{src.name}: not a claude-project file (schema 1)")
    pid = bundle["project_id"]
    try:
        details = json.loads(bundle["project"])
        docs = json.loads(bundle["docs"])
    except json.JSONDecodeError as e:
        raise BadBundle(f"{src.name}: its project details are not JSON text ({e})") from e
    if not SAFE_ID.fullmatch(pid) or not isinstance(details, dict) or details.get("uuid") != pid:
        raise BadBundle(f"{src.name}: its project details don't match its project ID")
    if not isinstance(docs, list) or not all(isinstance(d, dict) for d in docs):
        raise BadBundle(f"{src.name}: its docs are not a list of objects")
    if not all(details.get(k) is None or is_timestamp(details[k]) for k in ("created_at", "updated_at")):
        raise BadBundle(f"{src.name}: its project's dates are not timestamps")
    missing = bundle.get("photos_missing") or {}
    if not isinstance(missing, dict) or not all(isinstance(v, list) for v in missing.values()):
        raise BadBundle(f"{src.name}: photos_missing is not an object of lists")
    if not isinstance(bundle.get("errors") or [], list):
        raise BadBundle(f"{src.name}: errors is not a list")
    if pid not in cfg.allowed:
        raise BadBundle(f"{src.name}: project {pid} isn't in allow in {cfg.path}")
    return bundle, details, raw


def _check_project_chats(bundle: dict, pid: str, cfg: Config, name: str) -> tuple[list, list[str]]:
    """Every chat parsed and every photo decoded, before anything is written. A chat whose
    title matches a hold rule is dropped here, by ID, and the rest go on."""
    checked, held = [], [str(h) for h in bundle["held"]]
    for cid, text in bundle["conversations"].items():
        where = f"{name}: conversations[{cid}]"
        if not isinstance(text, str):
            raise BadBundle(f"{where}: not text")
        try:
            data = text.encode("utf-8")
            conv = json.loads(data)
        except (UnicodeEncodeError, json.JSONDecodeError) as e:
            raise BadBundle(f"{where}: not JSON text ({e})") from e
        validate_conversation(conv, where)
        if str(conv["uuid"]) != cid or R.sanitize(conv.get("project_uuid")) != pid:
            raise BadBundle(f"{where}: its ID or project doesn't match")
        if is_held(conv.get("name"), cfg.hold_prefixes, cfg.hold_patterns):
            held.append(cid)
            continue
        photos = bundle["files"].get(cid) or {}
        if not isinstance(photos, dict):
            raise BadBundle(f"{where}: its photos are not an object")
        checked.append((cid, conv, data, _decode_photos(photos, where)))
    return checked, held


def _mark_upstream_state(manifest: dict, pid: str, listed: set[str], held: set[str], day: str) -> tuple[int, int]:
    """Match each synced chat's state to the project's list: (how many changed, how many went)."""
    moved = gone = 0
    for cid, entry in manifest["conversations"].items():
        if entry.get("project") != pid or not entry.get("snapshot"):
            continue
        state = "held" if cid in held else "active" if cid in listed else "gone"
        if entry.get("state", "active") != state:
            entry["state"], entry["since"] = state, None if state == "active" else day
            moved += 1
            gone += state == "gone"
    return moved, gone


def _keep_project_text(archive: Path, known: dict, pid: str, kind: str, text: str, stamp: str) -> bool:
    """Keep the project's details or docs as they came, only when they differ from the last."""
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if known.get(f"{kind}_sha") == digest:
        return False
    folder = archive / "projects" / pid
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / f"{kind}-{stamp}-{digest[:8]}.json"
    dest.write_bytes(text.encode("utf-8"))
    known[kind], known[f"{kind}_sha"] = str(dest.relative_to(archive)), digest
    return True


def ingest_project(archive: Path, cfg: Config, manifest: dict, src: Path, now: datetime, trash) -> ProjectReport:
    """Archive one claude-project-*.json: a project's new or changed chats, photos and details.

    Everything is checked before anything is written, so a bad file leaves the archive as it
    was and stays where it is. Each chat is archived as ingest_chat archives one. The list in
    the file also tells which earlier chats have gone or are now held, when the file says the
    list is whole. The download is kept unless it added nothing or carries a chat a hold rule
    covers: the job leaves those out, so that is a rule added since it was generated.
    """
    _refuse_conflicts(archive)
    bundle, details, raw = _check_project_file(src, cfg)
    pid = bundle["project_id"]
    if is_held(details.get("name"), cfg.hold_prefixes, cfg.hold_patterns):
        trash(src)
        return ProjectReport(src, pid, "held")
    checked, held = _check_project_chats(bundle, pid, cfg, src.name)

    known = manifest["projects"].setdefault(pid, {})
    report = ProjectReport(src, pid, "synced", first_sync="first_synced" not in known, held=held,
                           more=bool(bundle.get("more")), errors=len(bundle.get("errors") or []))
    missing = bundle.get("photos_missing") or {}
    for cid, conv, data, decoded in checked:
        if _same_as_archived(archive, manifest["conversations"].get(cid), conv):
            report.unchanged += 1
        else:
            dest = _snapshot_dest(archive, conv)
            dest.write_bytes(data)
            if _record_snapshot(archive, manifest, conv, dest, now) == "new":
                report.new += 1
            else:
                report.changed += 1
        entry = manifest["conversations"][cid]
        report.photos += _store_photos(archive, entry, cid, decoded)
        if missing.get(cid):
            entry["photos_missing"] = [str(m) for m in missing[cid]]
        else:
            entry.pop("photos_missing", None)

    listed = {str(item.get("uuid")) for item in bundle["list"]}
    day = now.astimezone(ZoneInfo(cfg.timezone)).date().isoformat()
    report.list_complete = bundle.get("list_complete", True) is True
    moved = 0
    if report.list_complete:  # a chat missing from a partial list hasn't gone anywhere
        moved, report.gone = _mark_upstream_state(manifest, pid, listed, set(held), day)

    stamp = _stamp(bundle.get("fetched_at") or now.isoformat())
    kept = [_keep_project_text(archive, known, pid, kind, bundle[text], stamp)
            for kind, text in (("details", "project"), ("docs", "docs"))]
    known["name"] = R.sanitize(details.get("name")) or known.get("name") or ""
    known["updated_at"] = details.get("updated_at")
    if details.get("created_at"):
        known.setdefault("created_at", str(details["created_at"]))
    first, known["first_synced"] = report.first_sync, known.get("first_synced") or now.isoformat()

    if not (first or report.new or report.changed or report.photos or moved or any(kept)):
        trash(src)  # nothing new in it
        report.status, report.kept = "unchanged", False
        return report
    manifest["last_ingest"] = now.isoformat()
    if set(bundle["conversations"]) - {cid for cid, _conv, _data, _photos in checked}:
        trash(src)  # it holds the words of a chat a hold rule covers, so it can't be kept as it came
        report.kept = False
        return report
    _keep_download(src, archive / "projects" / pid / "bundles", stamp, raw)
    return report

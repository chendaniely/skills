#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "markdown-it-py>=3.0",
# ]
# ///
"""Tests for claude_chats_archive.py. Run from the vault root:

    uv run claude-chats/tests/test_claude_chats_archive.py -v

Every test works in a temp archive; nothing real is read or written.
"""
import base64
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

import claude_chats_archive as A  # noqa: E402

NOW = datetime(2026, 10, 15, 23, 59, tzinfo=timezone.utc)
ROOT = "00000000-0000-4000-8000-000000000000"
HOLD_CASES = [
    ("PRIVATE — rec letter", True), ("  private thoughts", True), ("Private Chef menu", True),
    ("[PRIVATE] x", True), ("🔒 Private notes", True), ("ＰＲＩＶＡＴＥ", True), ("​private", True),
    ("- private x", True), ("Interview: Sam", True), ("Interview : Sam", True), ("Mock interview: me", True),
    ("Consultation: Private Chef", False), ("interview prep", False), ("", False), (None, False),
    ("Garage shelf build plan", False),
]


def a_conv(cid="c0ffee00-1111-2222-3333-444455556666", name="Storage pool fix",
           updated="2026-10-15T23:52:05.738460Z", n=2, project=None):
    msgs = [{"uuid": f"m{i}", "parent_message_uuid": ROOT if i == 0 else f"m{i-1}",
             "sender": "human" if i % 2 == 0 else "assistant", "created_at": updated,
             "text": "", "content": [{"type": "text", "text": f"t{i}"}]} for i in range(n)]
    return {"uuid": cid, "name": name, "created_at": updated, "updated_at": updated,
            "project_uuid": project, "current_leaf_message_uuid": msgs[-1]["uuid"],
            "chat_messages": msgs}


class Temp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.archive, self.downloads = base / "claude-ai", base / "Downloads"
        self.downloads.mkdir()
        self.trashed = []

    def tearDown(self):
        self.tmp.cleanup()

    def write_config(self, text):
        self.archive.mkdir(parents=True, exist_ok=True)
        (self.archive / "config.toml").write_text(text, encoding="utf-8")


class ConfigTests(Temp):
    def test_first_run_writes_default(self):
        cfg = A.load_config(self.archive)
        self.assertTrue((self.archive / "config.toml").exists())
        self.assertEqual((cfg.owner_name, cfg.timezone, cfg.allow), ("Me", "UTC", []))

    def test_allow_entry_needs_ack(self):
        self.write_config('allow = [ { project = "p1", name = "Homelab" } ]\n')
        with self.assertRaises(A.ConfigError) as cm:
            A.load_config(self.archive)
        self.assertIn("ack", str(cm.exception))
        self.write_config('allow = [ { project = "p1", name = "Homelab", ack = "2026-10-15" } ]\n')
        self.assertEqual(A.load_config(self.archive).allowed, {"p1"})

    def test_bad_toml_and_timezone_are_78(self):
        self.write_config("allow = [ {")
        with self.assertRaises(A.ConfigError) as cm:
            A.load_config(self.archive)
        self.assertEqual(cm.exception.code, 78)
        self.write_config('timezone = "Mars/Olympus"\n')
        with self.assertRaises(A.ConfigError):
            A.load_config(self.archive)

    def test_project_found_by_name_or_id(self):
        self.write_config('allow = [ { project = "p1", name = "Home Lab", ack = "2026-10-15" } ]\n')
        cfg = A.load_config(self.archive)
        self.assertEqual(cfg.find_allowed("p1")["name"], "Home Lab")
        self.assertEqual(cfg.find_allowed("home lab")["project"], "p1")
        self.assertIsNone(cfg.find_allowed("Other"))

    def test_a_project_can_name_its_photo_folder(self):
        self.write_config('allow = [ { project = "p1", name = "L", ack = "2026-10-15", photos = "ze-files/looks" } ]\n')
        cfg = A.load_config(self.archive)
        self.assertEqual(cfg.photos_dir("p1"), Path("ze-files/looks"))
        self.assertEqual(cfg.photos_dir("other"), A.DEFAULT_PHOTOS)
        self.assertEqual(cfg.photos_dir(None), A.DEFAULT_PHOTOS)

    def test_photos_folder_cannot_leave_the_vault(self):
        for bad in ("../outside", "/abs/photos", "ze-files/../../x"):
            with self.subTest(bad=bad):
                self.write_config(f'allow = [ {{ project = "p1", name = "L", ack = "2026-10-15", photos = "{bad}" }} ]\n')
                with self.assertRaises(A.ConfigError):
                    A.load_config(self.archive)


class HoldTests(unittest.TestCase):
    def test_cases(self):
        for title, expected in HOLD_CASES:
            with self.subTest(title=title):
                self.assertEqual(A.is_held(title, ["private"], ["interview:"]), expected)

    def test_defaults_hold_even_when_config_empties_them(self):
        self.assertTrue(A.is_held("PRIVATE x", [], []))
        self.assertTrue(A.is_held("interview: y", [], []))


class LockAndConflicts(Temp):
    def test_second_lock_is_75_and_released(self):
        self.archive.mkdir(parents=True)
        with A.Lock(self.archive):
            with self.assertRaises(A.LockHeld) as cm:
                with A.Lock(self.archive):
                    pass
            self.assertEqual(cm.exception.code, 75)
        self.assertFalse((self.archive / ".lock").exists())

    def test_conflict_copies(self):
        self.archive.mkdir(parents=True)
        (self.archive / "manifest_Conflict_20261015_mac.json").write_text("{}")
        (self.archive / "notes-conflict-free.txt").write_text("")
        self.assertEqual([p.name for p in A.conflict_copies(self.archive)],
                         ["manifest_Conflict_20261015_mac.json"])


class CaptureBase(Temp):
    """Setup and helpers only; no tests, so subclasses don't run each other's tests twice."""

    def setUp(self):
        super().setUp()
        self.cfg = A.load_config(self.archive)
        self.cfg.downloads_dir = self.downloads
        self.manifest = A.empty_manifest()

    def drop(self, conv, name="claude-conversation-c0ffee00.json", raw=None):
        path = self.downloads / name
        path.write_bytes(raw if raw is not None else json.dumps(conv).encode("utf-8"))
        return path

    def ingest(self, path):
        return A.ingest_capture(self.archive, self.cfg, self.manifest, path, NOW, self.trashed.append)

    @staticmethod
    def photos(files, mime="image/webp", bytes_off=0):
        return {fid: {"file_name": n, "file_kind": "image", "variant": "preview", "mime": mime,
                      "width": 1, "height": 1, "bytes": len(data) + bytes_off,
                      "base64": base64.b64encode(data).decode()}
                for fid, (n, data) in files.items()}


class Capture(CaptureBase):
    def test_new_capture_moves_verbatim_and_records_no_title(self):
        src = self.drop(a_conv())
        raw = src.read_bytes()
        r = self.ingest(src)
        self.assertEqual(r.status, "new")
        self.assertFalse(src.exists())
        snap = self.archive / self.manifest["conversations"][r.uuid]["snapshot"]
        self.assertEqual(snap.read_bytes(), raw)
        entry = self.manifest["conversations"][r.uuid]
        self.assertEqual((entry["state"], entry["source"], entry["project"]), ("active", "capture", None))
        self.assertNotIn("Storage pool fix", json.dumps(self.manifest))
        self.assertEqual(A.find_captures(self.cfg, self.archive), [])

    def test_download_saved_into_the_archive_itself_is_found_once(self):
        # Chrome's Save dialog remembers the last folder: after one save into conversations/,
        # the next downloads land there too (2026-11-01).
        drop = self.archive / "conversations"
        drop.mkdir(parents=True)
        src = drop / "claude-conversation-c0ffee00.json"
        src.write_text(json.dumps(a_conv()), encoding="utf-8")
        self.assertEqual(A.find_captures(self.cfg, self.archive), [src])
        self.cfg.downloads_dir = drop
        self.assertEqual(A.find_captures(self.cfg, self.archive), [src])
        self.assertEqual(self.ingest(src).status, "new")
        self.assertEqual(A.find_captures(self.cfg, self.archive), [])

    def test_identical_capture_is_unchanged_and_trashed(self):
        self.ingest(self.drop(a_conv()))
        src = self.drop(a_conv())
        r = self.ingest(src)
        self.assertEqual(r.status, "unchanged")
        self.assertEqual(self.trashed, [src])

    def test_grown_capture_gets_a_new_snapshot(self):
        self.ingest(self.drop(a_conv()))
        r = self.ingest(self.drop(a_conv(updated="2026-10-16T01:00:00Z", n=4)))
        self.assertEqual(r.status, "changed")
        folder = self.archive / "conversations" / r.uuid
        self.assertEqual(len(list(folder.glob("*.json"))), 2)
        self.assertTrue(self.manifest["conversations"][r.uuid]["snapshot"].endswith("2026-10-16T01-00-00Z.json"))

    def test_held_capture_is_trashed_not_archived(self):
        src = self.drop(a_conv(name="PRIVATE rec letter"))
        r = self.ingest(src)
        self.assertEqual(r.status, "held")
        self.assertEqual(self.trashed, [src])
        self.assertEqual(self.manifest["conversations"], {})
        self.assertFalse((self.archive / "conversations").exists())

    def test_malformed_names_the_field_and_leaves_the_file(self):
        c = a_conv()
        del c["chat_messages"][1]["sender"]
        src = self.drop(c)
        with self.assertRaises(A.BadBundle) as cm:
            self.ingest(src)
        self.assertEqual(cm.exception.code, 65)
        self.assertIn("chat_messages[1].sender", str(cm.exception))
        self.assertTrue(src.exists())

    def test_not_json(self):
        with self.assertRaises(A.BadBundle):
            self.ingest(self.drop(None, raw=b"{nope"))

    def test_lone_surrogate_is_archived_verbatim(self):
        raw = json.dumps(a_conv()).replace("Storage pool fix", "Pool \\ud83c fix").encode()
        src = self.drop(None, raw=raw)
        r = self.ingest(src)
        self.assertEqual(r.status, "new")
        self.assertEqual((self.archive / self.manifest["conversations"][r.uuid]["snapshot"]).read_bytes(), raw)

    def test_conflict_copy_blocks_ingest(self):
        (self.archive / "manifest_Conflict_x.json").write_text("{}")
        with self.assertRaises(A.ConfigError):
            self.ingest(self.drop(a_conv()))

    def test_manifest_round_trip(self):
        self.ingest(self.drop(a_conv()))
        A.save_manifest(self.archive, self.manifest)
        self.assertEqual(A.load_manifest(self.archive), self.manifest)


class FilesBundle(CaptureBase):
    def files_bundle(self, cid, files, name=None, mime="image/webp", bytes_off=0):
        b = {"schema": 1, "kind": "claude-chat-files", "conversation": cid,
             "fetched_at": "2026-11-01T02:00:00.000Z", "files": self.photos(files, mime, bytes_off)}
        path = self.downloads / (name or f"claude-files-{cid[:8]}.json")
        path.write_text(json.dumps(b), encoding="utf-8")
        return path

    def ingest_f(self, path, held=()):
        return A.ingest_files(self.archive, self.cfg, self.manifest, path, NOW, self.trashed.append,
                              held=set(held))

    def test_new_photos_are_decoded_archived_and_recorded(self):
        cid = self.ingest(self.drop(a_conv())).uuid
        src = self.files_bundle(cid, {"f1": ("1326.jpg", b"photo-one"), "f2": ("1327.jpg", b"photo-two")})
        raw = src.read_bytes()
        r = self.ingest_f(src)
        self.assertEqual((r.status, r.added), ("new", 2))
        files = self.manifest["conversations"][cid]["files"]
        self.assertEqual(sorted(files), ["f1", "f2"])
        self.assertEqual((self.archive / files["f1"]["path"]).read_bytes(), b"photo-one")
        self.assertEqual(files["f1"]["file_name"], "1326.jpg")
        self.assertFalse(src.exists())
        kept = list((self.archive / "conversations" / cid / "files" / "bundles").glob("*.json"))
        self.assertEqual([k.read_bytes() for k in kept], [raw])

    def test_same_photos_again_are_unchanged_and_trashed(self):
        cid = self.ingest(self.drop(a_conv())).uuid
        self.ingest_f(self.files_bundle(cid, {"f1": ("1326.jpg", b"photo-one")}))
        src = self.files_bundle(cid, {"f1": ("1326.jpg", b"photo-one")})
        r = self.ingest_f(src)
        self.assertEqual((r.status, r.added), ("unchanged", 0))
        self.assertEqual(self.trashed, [src])

    def test_bundle_saved_into_the_archive_itself_is_found(self):
        cid = self.ingest(self.drop(a_conv())).uuid
        src = self.files_bundle(cid, {"f1": ("1326.jpg", b"photo-one")})
        moved = src.rename(self.archive / "conversations" / src.name)
        self.assertEqual(A.find_file_bundles(self.cfg, self.archive), [moved])
        self.assertEqual(self.ingest_f(moved).status, "new")
        self.assertEqual(A.find_file_bundles(self.cfg, self.archive), [])

    def test_photos_survive_a_grown_capture(self):
        cid = self.ingest(self.drop(a_conv())).uuid
        self.ingest_f(self.files_bundle(cid, {"f1": ("1326.jpg", b"photo-one")}))
        self.manifest["conversations"][cid]["images"] = {"f1": "c0ffee00-01.webp"}  # as render records them
        self.ingest(self.drop(a_conv(updated="2026-10-16T01:00:00Z", n=4)))
        entry = self.manifest["conversations"][cid]
        self.assertEqual(sorted(entry.get("files", {})), ["f1"])
        self.assertEqual(entry.get("images"), {"f1": "c0ffee00-01.webp"})

    def test_unknown_conversation_is_refused_and_left(self):
        src = self.files_bundle("not-archived-0000", {"f1": ("1326.jpg", b"x")})
        with self.assertRaises(A.BadBundle) as cm:
            self.ingest_f(src)
        self.assertIn("isn't archived", str(cm.exception))
        self.assertTrue(src.exists())

    def test_held_conversation_photos_are_trashed(self):
        src = self.files_bundle("held-chat-0000", {"f1": ("1326.jpg", b"x")})
        r = self.ingest_f(src, held={"held-chat-0000"})
        self.assertEqual(r.status, "held")
        self.assertEqual(self.trashed, [src])

    def test_size_mismatch_and_unknown_type_are_refused(self):
        cid = self.ingest(self.drop(a_conv())).uuid
        with self.assertRaises(A.BadBundle) as cm:
            self.ingest_f(self.files_bundle(cid, {"f1": ("1326.jpg", b"x")}, bytes_off=5))
        self.assertIn("expected", str(cm.exception))
        with self.assertRaises(A.BadBundle) as cm:
            self.ingest_f(self.files_bundle(cid, {"f1": ("page.html", b"x")}, mime="text/html"))
        self.assertIn("unsupported", str(cm.exception))


class ChatBundle(CaptureBase):
    """claude-chat-*.json: one download carrying a chat's raw API text and its photos."""

    # Non-ASCII, and an escaped lone surrogate, which must survive the trip byte for byte.
    RAW = json.dumps(a_conv(), ensure_ascii=False).replace("Storage pool fix", "Pool é \\ud83c fix")

    def chat_bundle(self, raw, files, kind="claude-chat", bytes_off=0, project=None, name=None):
        b = {"schema": 1, "kind": kind, "fetched_at": "2026-11-01T02:00:00.000Z", "share": "5ab0c0de",
             "conversation": raw, "files": self.photos(files, bytes_off=bytes_off)}
        if project:
            b["project"] = project
        path = self.downloads / (name or f"claude-chat-{json.loads(raw)['uuid'][:8]}.json")
        path.write_text(json.dumps(b), encoding="utf-8")
        return path

    def ingest_c(self, path):
        return A.ingest_chat(self.archive, self.cfg, self.manifest, path, NOW, self.trashed.append)

    def test_chat_and_photos_arrive_as_one_file(self):
        src = self.chat_bundle(self.RAW, {"f1": ("1326.jpg", b"photo-one")})
        kept = src.read_bytes()
        self.assertEqual(A.find_chat_bundles(self.cfg, self.archive), [src])
        r = self.ingest_c(src)
        self.assertEqual((r.status, r.added), ("new", 1))
        entry = self.manifest["conversations"][r.uuid]
        self.assertEqual((self.archive / entry["snapshot"]).read_bytes(), self.RAW.encode("utf-8"))
        self.assertEqual((self.archive / entry["files"]["f1"]["path"]).read_bytes(), b"photo-one")
        self.assertFalse(src.exists())
        downloads = list((self.archive / "conversations" / r.uuid / "downloads").glob("*.json"))
        self.assertEqual([p.read_bytes() for p in downloads], [kept])
        self.assertEqual(A.find_chat_bundles(self.cfg, self.archive), [])
        self.assertNotIn("Pool", json.dumps(self.manifest))

    def test_same_file_again_is_unchanged_and_trashed(self):
        self.ingest_c(self.chat_bundle(self.RAW, {"f1": ("1326.jpg", b"photo-one")}))
        src = self.chat_bundle(self.RAW, {"f1": ("1326.jpg", b"photo-one")})
        r = self.ingest_c(src)
        self.assertEqual((r.status, r.added), ("unchanged", 0))
        self.assertEqual(self.trashed, [src])

    def test_photos_fetched_later_are_added_to_the_archived_chat(self):
        self.ingest_c(self.chat_bundle(self.RAW, {}))
        r = self.ingest_c(self.chat_bundle(self.RAW, {"f1": ("1326.jpg", b"photo-one")}))
        self.assertEqual((r.status, r.added), ("unchanged", 1))
        self.assertEqual(len(list((self.archive / "conversations" / r.uuid).glob("*.json"))), 1)

    def test_a_grown_chat_gets_a_new_snapshot(self):
        self.ingest_c(self.chat_bundle(self.RAW, {}))
        r = self.ingest_c(self.chat_bundle(json.dumps(a_conv(updated="2026-10-16T01:00:00Z", n=4)), {}))
        self.assertEqual(r.status, "changed")
        self.assertEqual(len(list((self.archive / "conversations" / r.uuid).glob("*.json"))), 2)

    def test_held_chat_is_trashed_and_nothing_is_archived(self):
        src = self.chat_bundle(json.dumps(a_conv(name="PRIVATE rec letter")), {"f1": ("1326.jpg", b"x")})
        r = self.ingest_c(src)
        self.assertEqual(r.status, "held")
        self.assertEqual(self.trashed, [src])
        self.assertFalse((self.archive / "conversations").exists())
        self.assertEqual(self.manifest["conversations"], {})

    def test_a_bad_photo_writes_nothing_and_leaves_the_file(self):
        src = self.chat_bundle(self.RAW, {"f1": ("1326.jpg", b"x")}, bytes_off=5)
        with self.assertRaises(A.BadBundle) as cm:
            self.ingest_c(src)
        self.assertIn("expected", str(cm.exception))
        self.assertTrue(src.exists())
        self.assertFalse((self.archive / "conversations").exists())
        self.assertEqual(self.manifest["conversations"], {})

    def test_a_project_chat_records_its_project_name(self):
        project = {"uuid": "p1", "name": "Homelab", "created_at": "2026-09-01T00:00:00Z"}
        r = self.ingest_c(self.chat_bundle(json.dumps(a_conv(project="p1")), {}, project=project))
        self.assertEqual(r.status, "new")
        self.assertEqual(self.manifest["projects"]["p1"], {"name": "Homelab", "created_at": "2026-09-01T00:00:00Z"})
        self.assertEqual(self.manifest["conversations"][r.uuid]["project"], "p1")

    def test_a_renamed_project_keeps_its_folder_and_note(self):
        self.manifest["projects"]["p1"] = {"name": "Homelab", "folder": "homelab", "note": "Homelab (Claude project)"}
        project = {"uuid": "p1", "name": "Home lab", "created_at": "2026-09-01T00:00:00Z"}
        self.ingest_c(self.chat_bundle(json.dumps(a_conv(project="p1")), {}, project=project))
        p = self.manifest["projects"]["p1"]
        self.assertEqual((p["name"], p["folder"], p["note"]), ("Home lab", "homelab", "Homelab (Claude project)"))

    def test_a_chat_in_a_held_project_is_never_archived(self):
        src = self.chat_bundle(json.dumps(a_conv(project="p1")), {}, project={"uuid": "p1", "name": "PRIVATE letters"})
        r = self.ingest_c(src)
        self.assertEqual(r.status, "held")
        self.assertEqual(self.trashed, [src])
        self.assertEqual((self.manifest["projects"], self.manifest["conversations"]), ({}, {}))
        self.assertFalse((self.archive / "conversations").exists())

    def test_another_kind_is_refused(self):
        src = self.chat_bundle(self.RAW, {}, kind="claude-chat-files")
        with self.assertRaises(A.BadBundle) as cm:
            self.ingest_c(src)
        self.assertIn("not a claude-chat file", str(cm.exception))
        self.assertTrue(src.exists())

    def test_a_chat_id_that_would_leave_the_archive_is_refused(self):
        src = self.chat_bundle(json.dumps(a_conv(cid="../../escaped")), {}, name="claude-chat-x.json")
        with self.assertRaises(A.BadBundle) as cm:
            self.ingest_c(src)
        self.assertIn("uuid", str(cm.exception))
        self.assertTrue(src.exists())
        self.assertFalse((self.archive.parent / "escaped").exists())

    def test_a_photo_id_that_would_leave_the_archive_is_refused(self):
        src = self.chat_bundle(self.RAW, {"../../escaped": ("1.jpg", b"x")})
        with self.assertRaises(A.BadBundle):
            self.ingest_c(src)
        self.assertEqual(self.manifest["conversations"], {})

    def test_a_timestamp_that_is_a_path_is_refused(self):
        src = self.chat_bundle(json.dumps(a_conv(updated="../../escaped")), {})
        with self.assertRaises(A.BadBundle):
            self.ingest_c(src)
        self.assertTrue(src.exists())
        self.assertFalse((self.archive / "conversations").exists())

    def test_a_project_id_that_is_a_path_is_refused(self):
        src = self.chat_bundle(json.dumps(a_conv(project="../../..")), {})
        with self.assertRaises(A.BadBundle):
            self.ingest_c(src)
        self.assertTrue(src.exists())
        self.assertEqual((self.manifest["conversations"], self.manifest["projects"]), ({}, {}))


class ProjectFile(CaptureBase):
    """claude-project-*.json: a whole project's new or changed chats, in one download."""

    C1 = "c1c1c1c1-0000-4000-8000-000000000001"
    C2 = "c2c2c2c2-0000-4000-8000-000000000002"
    DOCS = '[{"file_name": "a.md", "content": "x"}]'

    def setUp(self):
        super().setUp()
        self.write_config('allow = [ { project = "p1", name = "Looks", ack = "2026-11-09" } ]\n')
        self.cfg = A.load_config(self.archive)
        self.cfg.downloads_dir = self.downloads

    def chat(self, cid, **kw):
        return a_conv(cid=cid, project="p1", **kw)

    def project_file(self, chats=(), listed=None, files=None, held=(), name="Looks", pid="p1",
                     updated="2026-09-01T00:00:00Z", bytes_off=0, missing=None):
        b = {"schema": 1, "kind": "claude-project", "fetched_at": "2026-11-09T02:00:00.000Z", "project_id": pid,
             "project": json.dumps({"uuid": pid, "name": name, "created_at": "2026-09-01T00:00:00Z", "updated_at": updated}),
             "docs": self.DOCS,
             "list": [{"uuid": c, "updated_at": "t"} for c in (listed if listed is not None else [c["uuid"] for c in chats])],
             "held": list(held),
             "conversations": {c["uuid"]: json.dumps(c, ensure_ascii=False) for c in chats},
             "files": {cid: self.photos(f, bytes_off=bytes_off) for cid, f in (files or {}).items()},
             "photos_missing": missing or {}, "errors": [], "more": False}
        path = self.downloads / "claude-project-p1.json"
        path.write_text(json.dumps(b), encoding="utf-8")
        return path

    def ingest_p(self, path):
        return A.ingest_project(self.archive, self.cfg, self.manifest, path, NOW, self.trashed.append)

    def entry(self, cid):
        return self.manifest["conversations"][cid]

    def test_a_project_arrives_byte_for_byte(self):
        c = self.chat(self.C1, name="Café outfit")
        src = self.project_file([c], files={self.C1: {"f1": ("1.jpg", b"photo")}})
        kept = src.read_bytes()
        self.assertEqual(A.find_project_bundles(self.cfg, self.archive), [src])
        r = self.ingest_p(src)
        self.assertEqual((r.status, r.first_sync, r.new, r.changed, r.unchanged, r.photos), ("synced", True, 1, 0, 0, 1))
        e = self.entry(self.C1)
        self.assertEqual((self.archive / e["snapshot"]).read_bytes(), json.dumps(c, ensure_ascii=False).encode("utf-8"))
        self.assertEqual((self.archive / e["files"]["f1"]["path"]).read_bytes(), b"photo")
        self.assertEqual(e["project"], "p1")
        p = self.manifest["projects"]["p1"]
        self.assertEqual((p["name"], p["created_at"], p["updated_at"]), ("Looks", "2026-09-01T00:00:00Z", "2026-09-01T00:00:00Z"))
        self.assertIn("first_synced", p)
        self.assertEqual(json.loads((self.archive / p["details"]).read_text())["uuid"], "p1")
        self.assertEqual((self.archive / p["docs"]).read_text(), self.DOCS)
        self.assertFalse(src.exists())
        self.assertEqual([x.read_bytes() for x in (self.archive / "projects" / "p1" / "bundles").glob("*.json")], [kept])
        self.assertEqual(A.find_project_bundles(self.cfg, self.archive), [])

    def test_first_sync_is_true_once_even_after_a_pasted_link(self):
        link = self.downloads / "claude-chat-c1.json"
        link.write_text(json.dumps({"schema": 1, "kind": "claude-chat", "fetched_at": "2026-11-01T02:00:00Z",
                                    "project": {"uuid": "p1", "name": "Looks"},
                                    "conversation": json.dumps(self.chat(self.C1)), "files": {}}), encoding="utf-8")
        A.ingest_chat(self.archive, self.cfg, self.manifest, link, NOW, self.trashed.append)
        self.assertTrue(self.ingest_p(self.project_file([self.chat(self.C2)], listed=[self.C1, self.C2])).first_sync)
        self.assertFalse(self.ingest_p(self.project_file([], listed=[self.C1, self.C2], updated="2026-10-01T00:00:00Z")).first_sync)

    def test_a_project_not_in_allow_is_refused_and_left(self):
        src = self.project_file([a_conv(cid=self.C1, project="p2")], pid="p2")
        with self.assertRaises(A.BadBundle) as cm:
            self.ingest_p(src)
        self.assertIn("allow", str(cm.exception))
        self.assertTrue(src.exists())
        self.assertEqual(self.manifest["conversations"], {})

    def test_one_bad_photo_writes_nothing_and_leaves_the_file(self):
        src = self.project_file([self.chat(self.C1)], files={self.C1: {"f1": ("1.jpg", b"x")}}, bytes_off=5)
        with self.assertRaises(A.BadBundle):
            self.ingest_p(src)
        self.assertTrue(src.exists())
        self.assertFalse((self.archive / "conversations").exists())
        self.assertEqual((self.manifest["conversations"], self.manifest["projects"]), ({}, {}))

    def test_a_held_title_is_dropped_by_id_and_the_rest_proceed(self):
        r = self.ingest_p(self.project_file([self.chat(self.C1), self.chat(self.C2, name="PRIVATE letter")]))
        self.assertEqual((r.new, r.held), (1, [self.C2]))
        self.assertNotIn(self.C2, self.manifest["conversations"])
        self.assertFalse((self.archive / "conversations" / self.C2).exists())

    def test_a_file_carrying_a_held_chat_is_not_kept(self):
        """The job leaves such a chat out, so this is a hold rule added since it was generated."""
        src = self.project_file([self.chat(self.C1), self.chat(self.C2, name="PRIVATE letter")])
        r = self.ingest_p(src)
        self.assertEqual((r.new, r.held, r.kept), (1, [self.C2], False))
        self.assertEqual(self.trashed, [src])
        self.assertFalse((self.archive / "projects" / "p1" / "bundles").exists())
        everything = b"".join(p.read_bytes() for p in self.archive.rglob("*") if p.is_file())
        self.assertNotIn(b"PRIVATE letter", everything)

    def spoil(self, change):
        src = self.project_file([self.chat(self.C1)])
        bundle = json.loads(src.read_text(encoding="utf-8"))
        change(bundle)
        src.write_text(json.dumps(bundle), encoding="utf-8")
        return src

    def test_odd_values_write_nothing_and_leave_the_file(self):
        def in_chat(change):
            def apply(bundle):
                c = json.loads(bundle["conversations"][self.C1])
                change(c)
                bundle["conversations"][self.C1] = json.dumps(c)
            return apply

        def in_details(change):
            def apply(bundle):
                d = json.loads(bundle["project"])
                change(d)
                bundle["project"] = json.dumps(d)
            return apply

        cases = {
            "a very long updated_at": in_chat(lambda c: c.update(updated_at="2" * 400)),
            "updated_at not text": in_chat(lambda c: c.update(updated_at=5)),
            "a message time that isn't one": in_chat(lambda c: c["chat_messages"][0].update(created_at="yesterday")),
            "a project_uuid that is a path": in_chat(lambda c: c.update(project_uuid="../..")),
            "docs not a list": lambda b: b.update(docs=json.dumps({"a": 1})),
            "a doc that isn't an object": lambda b: b.update(docs=json.dumps(["a"])),
            "photos_missing not an object": lambda b: b.update(photos_missing=["f1"]),
            "photos_missing values not lists": lambda b: b.update(photos_missing={self.C1: 5}),
            "errors not a list": lambda b: b.update(errors=5),
            "project created_at not a time": in_details(lambda d: d.update(created_at="soon")),
            "project updated_at holding code": in_details(lambda d: d.update(updated_at="};alert(1)//")),
        }
        for label, change in cases.items():
            with self.subTest(label):
                src = self.spoil(change)
                with self.assertRaises(A.BadBundle):
                    self.ingest_p(src)
                self.assertTrue(src.exists())
                self.assertEqual((self.manifest["conversations"], self.manifest["projects"]), ({}, {}))
                self.assertFalse((self.archive / "conversations").exists())

    def test_a_partial_chat_list_marks_nothing_gone(self):
        self.ingest_p(self.project_file([self.chat(self.C1), self.chat(self.C2)]))
        src = self.project_file([], listed=[self.C1], updated="2026-10-01T00:00:00Z")
        bundle = json.loads(src.read_text(encoding="utf-8"))
        bundle["list_complete"] = False
        src.write_text(json.dumps(bundle), encoding="utf-8")
        r = self.ingest_p(src)
        self.assertEqual(r.gone, 0)
        self.assertEqual(self.entry(self.C2)["state"], "active")

    def test_a_held_project_name_trashes_the_file(self):
        src = self.project_file([self.chat(self.C1)], name="PRIVATE letters")
        r = self.ingest_p(src)
        self.assertEqual(r.status, "held")
        self.assertEqual(self.trashed, [src])
        self.assertEqual((self.manifest["conversations"], self.manifest["projects"]), ({}, {}))

    def test_chats_gone_or_held_upstream_are_marked(self):
        self.ingest_p(self.project_file([self.chat(self.C1), self.chat(self.C2)]))
        r = self.ingest_p(self.project_file([], listed=[], held=[self.C2]))
        self.assertEqual(r.gone, 1)
        self.assertEqual((self.entry(self.C1)["state"], self.entry(self.C2)["state"]), ("gone", "held"))
        self.assertEqual(self.entry(self.C1)["since"], "2026-10-15")

    def test_a_gone_chat_that_returns_is_active_again(self):
        self.ingest_p(self.project_file([self.chat(self.C1)]))
        self.ingest_p(self.project_file([], listed=[]))
        self.ingest_p(self.project_file([], listed=[self.C1]))
        self.assertEqual((self.entry(self.C1)["state"], self.entry(self.C1)["since"]), ("active", None))

    def test_details_and_docs_are_kept_only_when_they_change(self):
        self.ingest_p(self.project_file([self.chat(self.C1)]))
        first = self.manifest["projects"]["p1"]["details"]
        self.ingest_p(self.project_file([], listed=[self.C1]))
        self.assertEqual(self.manifest["projects"]["p1"]["details"], first)
        self.ingest_p(self.project_file([], listed=[self.C1], updated="2026-10-01T00:00:00Z"))
        self.assertNotEqual(self.manifest["projects"]["p1"]["details"], first)
        self.assertTrue((self.archive / first).exists())

    def test_a_chat_already_mirrored_keeps_its_note(self):
        self.ingest_p(self.project_file([self.chat(self.C1)]))
        self.entry(self.C1).update(note="sources/claude/looks/x.md", rendered_ids=["m0"])
        self.ingest_p(self.project_file([self.chat(self.C1, updated="2026-10-16T01:00:00Z", n=4)]))
        self.assertEqual((self.entry(self.C1)["note"], self.entry(self.C1)["rendered_ids"]), ("sources/claude/looks/x.md", ["m0"]))

    def test_a_file_that_changes_nothing_goes_to_the_trash(self):
        c = self.chat(self.C1)
        self.ingest_p(self.project_file([c]))
        src = self.project_file([c])
        r = self.ingest_p(src)
        self.assertEqual((r.status, r.unchanged), ("unchanged", 1))
        self.assertEqual(self.trashed, [src])

    def test_missing_photos_are_remembered_until_they_arrive(self):
        c = self.chat(self.C1)
        self.ingest_p(self.project_file([c], missing={self.C1: ["f1"]}))
        self.assertEqual(self.entry(self.C1)["photos_missing"], ["f1"])
        self.ingest_p(self.project_file([c], files={self.C1: {"f1": ("1.jpg", b"p")}}))
        self.assertNotIn("photos_missing", self.entry(self.C1))

    def test_a_chat_from_another_project_is_refused(self):
        src = self.project_file([a_conv(cid=self.C1, project="p9")])
        with self.assertRaises(A.BadBundle):
            self.ingest_p(src)
        self.assertTrue(src.exists())


if __name__ == "__main__":
    unittest.main()

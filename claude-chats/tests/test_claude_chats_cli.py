#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "markdown-it-py>=3.0",
#     "pillow>=11",
#     "pyyaml>=6.0.3",
#     "send2trash>=2.1",
# ]
# ///
"""End-to-end tests for claude_chats.py: a downloaded chat -> ingest -> render -> summary.

    uv run claude-chats/tests/test_claude_chats_cli.py -v

A temp archive, temp vault and temp Downloads folder; nothing real is touched.
"""
import base64
import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

import yaml  # noqa: E402

import claude_chats as C  # noqa: E402
import claude_chats_render as R  # noqa: E402

NOW = datetime(2026, 10, 15, 23, 59, tzinfo=timezone.utc)
ROOT = "00000000-0000-4000-8000-000000000000"
CID = "c0ffee11-0000-4000-8000-000000000001"
WIKILINK_RE = re.compile(r'!?\[\[([^\]|#\\]+)(?:#[^\]|\\]*)?(?:\\?\|[^\]]*)?\]\]')


def conv(texts, updated="2026-10-15T23:52:05.738460Z", name="Storage pool expansion", cid=CID):
    msgs = []
    for i, text in enumerate(texts):
        msgs.append({"uuid": f"{cid[:8]}-{i}", "parent_message_uuid": ROOT if i == 0 else f"{cid[:8]}-{i-1}",
                     "sender": "human" if i % 2 == 0 else "assistant",
                     "created_at": f"2026-10-15T16:{i:02d}:00Z", "text": "",
                     "content": [{"type": "text", "text": text}]})
    return {"uuid": cid, "name": name, "created_at": msgs[0]["created_at"], "updated_at": updated,
            "project_uuid": None, "current_leaf_message_uuid": msgs[-1]["uuid"], "chat_messages": msgs}


class Flow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.archive, self.vault, self.downloads = base / "claude-ai", base / "vault", base / "Downloads"
        (self.vault / "zettelkasten").mkdir(parents=True)
        (self.vault / "zettelkasten" / "2026-10-15-0900-storage-pool-expansion.md").write_text("an older note\n")
        self.downloads.mkdir()
        self.trashed = []
        self.cli("status")  # writes the default config
        cfg = (self.archive / "config.toml").read_text()
        (self.archive / "config.toml").write_text(cfg.replace('"~/Downloads"', json.dumps(str(self.downloads))).replace('"UTC"', '"America/Vancouver"').replace('"Me"', '"Daniel"'))

    def tearDown(self):
        self.tmp.cleanup()

    def cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = C.main(["--archive", str(self.archive), "--vault", str(self.vault), *args],
                          trash=self.trashed.append, now=NOW)
        return code, out.getvalue(), err.getvalue()

    def drop(self, c):
        (self.downloads / f"claude-conversation-{c['uuid'][:8]}.json").write_text(json.dumps(c))

    def capture(self, c):
        self.drop(c)
        code, out, err = self.cli("ingest")
        self.assertEqual(code, 0, out + err)
        return out

    def note(self):
        notes = list((self.vault / "sources" / "claude" / "no-project").glob("*.md"))
        self.assertEqual(len(notes), 1, notes)
        return notes[0]

    def test_capture_render_summarize_and_idempotent(self):
        self.capture(conv(["Pool shows 20 TB, volume stuck at 10 TB [[x]] #tag", "Run `lvextend`."]))
        code, out, _ = self.cli("render")
        self.assertEqual(code, 0)
        self.assertIn("new (1)", out)
        self.assertFalse((self.vault / "sources").exists())

        code, out, _ = self.cli("render", "--apply")
        self.assertEqual(code, 0)
        note = self.note()
        # the older vault note owns the plain name, so this one gets the ID suffix
        self.assertEqual(note.name, "2026-10-15-0900-storage-pool-expansion-c0ffee11.md")
        text = note.read_text()
        fm = yaml.safe_load(text.split("---\n")[1])
        self.assertEqual((fm["Conversation ID"], fm["Summary"], fm["Tags"]), (CID, "pending", ["claude_chat"]))
        self.assertEqual(WIKILINK_RE.findall(text), [])
        self.assertEqual(out.strip().splitlines()[-1], f"- Synced Claude chats: 1 new, 0 updated — [[{note.stem}]]")

        code, out, _ = self.cli("summaries")
        self.assertIn(CID, out)
        summary = Path(self.tmp.name) / "summary.md"
        summary.write_text("Built the shelves after measuring the wall. See [[Garage Shelves]].")
        code, out, _ = self.cli("summary", CID, "--file", str(summary))
        self.assertEqual(code, 0, out)
        text = note.read_text()
        self.assertIn("## Summary\n\nBuilt the shelves", text)
        self.assertIn("Summary: Claude 2026-10-15", text)
        self.assertNotIn(CID, self.cli("summaries")[1])
        self.assertEqual(self.cli("summary", CID, "--file", str(summary))[0], 1)

        before = note.read_bytes()
        code, out, _ = self.cli("render", "--apply")
        self.assertIn("unchanged: 1", out)
        self.assertEqual(note.read_bytes(), before)
        self.assertEqual(out.strip().splitlines()[-1], "Nothing new to log.")

    def test_growth_keeps_summary_and_notes_and_flags_staleness(self):
        self.capture(conv(["a", "b"]))
        self.cli("render", "--apply")
        summary = Path(self.tmp.name) / "s.md"
        summary.write_text("First summary.")
        self.cli("summary", CID, "--file", str(summary))
        note = self.note()
        note.write_text(note.read_text() + "\n## Mine\n\nkeep\n")
        self.capture(conv(["a", "b", "c", "d"], updated="2026-10-16T01:00:00Z"))
        code, out, _ = self.cli("render", "--apply")
        self.assertIn("updated (1)", out)
        self.assertIn("summary may be out of date", out)
        text = note.read_text()
        for kept in ("First summary.", "\n## Mine\n\nkeep\n", "Summary: Claude 2026-10-15"):
            self.assertIn(kept, text)
        self.assertIn("\n\nd\n", text)

    def test_note_found_by_id_when_moved_or_manifest_lost(self):
        self.capture(conv(["a", "b"]))
        self.cli("render", "--apply")
        note = self.note()
        moved = self.vault / "sources" / "claude" / "no-project" / "renamed-by-dan.md"
        note.rename(moved)
        manifest = json.loads((self.archive / "manifest.json").read_text())
        manifest["conversations"][CID]["note"] = None
        (self.archive / "manifest.json").write_text(json.dumps(manifest))
        code, out, _ = self.cli("render", "--apply")
        self.assertIn("unchanged: 1", out)
        self.assertEqual(sorted(p.name for p in moved.parent.glob("*.md")), ["renamed-by-dan.md"])

    def test_hand_deleted_note_is_not_recreated(self):
        self.capture(conv(["a", "b"]))
        self.cli("render", "--apply")
        note = self.note()
        note.unlink()
        code, out, _ = self.cli("render", "--apply")
        self.assertIn("missing notes", out)
        self.assertFalse(note.exists())
        self.cli("render", "--apply", "--recreate", CID)
        self.assertTrue(note.exists())

    def test_ingest_finds_a_download_saved_into_the_archive(self):
        drop = self.archive / "conversations"
        drop.mkdir(parents=True, exist_ok=True)
        (drop / f"claude-conversation-{CID[:8]}.json").write_text(json.dumps(conv(["Grow the pool?", "Yes."])))
        code, out, err = self.cli("ingest")
        self.assertEqual(code, 0, out + err)
        self.assertRegex(out, rf"new\s+{CID}")
        self.assertEqual(list(drop.glob("claude-*.json")), [])

    def test_held_capture_is_never_archived(self):
        self.drop(conv(["a"], name="PRIVATE rec letter"))
        code, out, _ = self.cli("ingest")
        self.assertIn("held", out)
        self.assertEqual(len(self.trashed), 1)
        self.assertNotIn("PRIVATE", out)
        self.assertIn("unchanged: 0", self.cli("render")[1])

    def test_excluded_is_never_written(self):
        self.capture(conv(["a", "b"]))
        cfg = (self.archive / "config.toml").read_text().replace("exclude = []", f'exclude = ["{CID}"]')
        (self.archive / "config.toml").write_text(cfg)
        code, out, _ = self.cli("render", "--apply")
        self.assertIn("excluded: 1", out)
        self.assertFalse((self.vault / "sources").exists())

    def test_templater_guard(self):
        plugin = self.vault / ".obsidian" / "plugins" / "templater-obsidian"
        plugin.mkdir(parents=True)
        (plugin / "data.json").write_text(json.dumps({"trigger_on_file_creation": True}))
        self.capture(conv(["show me", "```\n<% tp.date.now() %>\n```"]))
        code, out, _ = self.cli("render", "--apply")
        self.assertIn("Templater", out)
        self.assertFalse((self.vault / "sources").exists())
        (plugin / "data.json").write_text(json.dumps({"trigger_on_file_creation": True,
                                                      "ignore_folders": ["sources"]}))
        self.cli("render", "--apply")
        self.assertIn("<% tp.date.now() %>", self.note().read_text())

    def test_photos_are_filed_cleaned_embedded_and_stable(self):
        from PIL import Image
        img, exif = Image.new("RGB", (8, 8), "gray"), Image.Exif()
        exif[0x010F] = "TestCam"
        buf = io.BytesIO()
        img.save(buf, format="WEBP", exif=exif.tobytes())
        data = buf.getvalue()
        c = conv(["here is the wall", "nice"])
        c["chat_messages"][0]["files"] = [{"file_uuid": "f1", "file_name": "1326.jpg", "file_kind": "image"}]
        c["chat_messages"][0]["content"].insert(0, {"type": "image", "file_uuid": "f1"})
        self.drop(c)
        bundle = {"schema": 1, "kind": "claude-chat-files", "conversation": CID, "fetched_at": "2026-11-01T02:00:00Z",
                  "files": {"f1": {"file_name": "1326.jpg", "file_kind": "image", "variant": "preview",
                                   "mime": "image/webp", "width": 8, "height": 8, "bytes": len(data),
                                   "base64": base64.b64encode(data).decode()}}}
        (self.downloads / f"claude-files-{CID[:8]}.json").write_text(json.dumps(bundle))
        code, out, err = self.cli("ingest")
        self.assertEqual(code, 0, out + err)
        self.assertIn("1 photo archived", out)
        code, out, _ = self.cli("render", "--apply")
        self.assertIn("photos to file in ze-files/claude: 1", out)
        photo = self.vault / "ze-files" / "claude" / f"{CID[:8]}-01.webp"
        with Image.open(photo) as im:
            self.assertEqual(len(im.getexif()), 0)
        text = self.note().read_text()
        self.assertIn(f"![[{CID[:8]}-01.webp|480]]", text)
        self.assertLess(text.index(f"{CID[:8]}-01.webp|480"), text.index("here is the wall", text.index("**Daniel**")))
        before = photo.read_bytes()
        code, out, _ = self.cli("render", "--apply")
        self.assertIn("unchanged: 1", out)
        self.assertNotIn("photos to file", out)
        self.assertEqual(photo.read_bytes(), before)

    SHARE = "11111111-2222-4333-8444-555555555555"

    def test_snippet_for_a_share_link(self):
        code, out, err = self.cli("snippet", f"https://claude.ai/share/{self.SHARE}?utm=x")
        self.assertEqual(code, 0, err)
        self.assertTrue(out.startswith("await (async () => {"))
        self.assertIn(json.dumps(self.SHARE), out)
        self.assertIn('kind: "claude-chat"', out)
        self.assertIn("claude-chat-${id.slice(0, 8)}.json", out)
        self.assertIn("const CHAT = null;", out)

    def test_snippet_for_a_chat_url_from_the_address_bar(self):
        code, out, err = self.cli("snippet", f"https://claude.ai/chat/{CID}")
        self.assertEqual(code, 0, err)
        self.assertIn("const SHARE = null;", out)
        self.assertIn(f"const CHAT = {json.dumps(CID)};", out)

    def test_snippet_refuses_anything_but_a_share_link(self):
        for link in (f"https://claude.ai/project/{self.SHARE}", f"https://evil.example/share/{self.SHARE}",
                     f'{self.SHARE}"; alert(1); "', "javascript:alert(1)"):
            with self.subTest(link=link):
                code, _, err = self.cli("snippet", link)
                self.assertEqual(code, 64)
                self.assertIn("share link", err)

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_snippet_holds_exactly_what_ingest_holds(self):
        from test_claude_chats_archive import HOLD_CASES
        import claude_chats_archive as A
        cfg = A.load_config(self.archive)
        js = self.cli("snippet", self.SHARE)[1]
        helpers = js.split("// <helpers>", 1)[1].split("// </helpers>", 1)[0]
        titles = [t for t, _ in HOLD_CASES]
        run = subprocess.run(["node", "-e", helpers + f"\nconsole.log(JSON.stringify({json.dumps(titles)}.map(isHeld)));"],
                             capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(run.stdout), [A.is_held(t, cfg.hold_prefixes, cfg.hold_patterns) for t in titles])

    def test_ingest_waits_for_a_download_to_land(self):
        def land():
            tmp = self.downloads / "landing.part"
            tmp.write_text(json.dumps(conv(["Grow the pool?", "Yes."])))
            os.replace(tmp, self.downloads / f"claude-conversation-{CID[:8]}.json")
        threading.Timer(0.3, land).start()
        code, out, err = self.cli("ingest", "--wait", "5")
        self.assertEqual(code, 0, out + err)
        self.assertRegex(out, rf"new\s+{CID}")

    def test_ingest_wait_gives_up_with_66(self):
        start = time.monotonic()
        self.assertEqual(self.cli("ingest", "--wait", "1")[0], 66)
        self.assertGreaterEqual(time.monotonic() - start, 1)

    def allow_project(self, extra=""):
        path = self.archive / "config.toml"
        entry = f'  {{ project = "{self.PID}", name = "Homelab", ack = "2026-11-09"{extra} }},\n'
        path.write_text(path.read_text().replace("allow = [\n", "allow = [\n" + entry).replace("delay_ms = 500", "delay_ms = 0"))

    @staticmethod
    def js_value(js, name):
        return json.loads(re.search(rf"const {name} = (.*?);", js).group(1))

    def test_project_not_in_allow_is_refused(self):
        code, _, err = self.cli("snippet", "--project", "Homelab")
        self.assertEqual(code, 78)
        self.assertIn("allow", err)

    def test_snippet_needs_a_link_or_a_project(self):
        self.allow_project()
        self.assertEqual(self.cli("snippet")[0], 64)
        self.assertEqual(self.cli("snippet", self.SHARE, "--project", "Homelab")[0], 64)

    def test_project_snippet_found_by_name_or_id(self):
        self.allow_project()
        for ref in ("homelab", self.PID):
            with self.subTest(ref=ref):
                code, out, err = self.cli("snippet", "--project", ref)
                self.assertEqual(code, 0, err)
                self.assertEqual(self.js_value(out, "PROJECT"), self.PID)

    def test_snippet_carries_what_is_known(self):
        self.allow_project()
        self.project_chat(CID, "2026-10-15")
        js = self.cli("snippet", "--project", "Homelab")[1]
        self.assertEqual(list(self.js_value(js, "KNOWN")), [CID])
        self.assertEqual(self.js_value(js, "KNOWN_FILE_IDS"), [])

    def test_a_chat_missing_photos_is_fetched_again(self):
        import claude_chats_archive as A
        self.allow_project()
        self.project_chat(CID, "2026-10-15")
        manifest = A.load_manifest(self.archive)
        manifest["conversations"][CID]["photos_missing"] = ["f1"]
        A.save_manifest(self.archive, manifest)
        self.assertEqual(self.js_value(self.cli("snippet", "--project", "Homelab")[1], "KNOWN"), {})

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_project_snippet_holds_exactly_what_ingest_holds(self):
        from test_claude_chats_archive import HOLD_CASES
        import claude_chats_archive as A
        self.allow_project()
        cfg = A.load_config(self.archive)
        js = self.cli("snippet", "--project", "Homelab")[1]
        helpers = js.split("// <helpers>", 1)[1].split("// </helpers>", 1)[0]
        titles = [t for t, _ in HOLD_CASES]
        run = subprocess.run(["node", "-e", helpers + f"\nconsole.log(JSON.stringify({json.dumps(titles)}.map(isHeld)));"],
                             capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(run.stdout), [A.is_held(t, cfg.hold_prefixes, cfg.hold_patterns) for t in titles])

    def run_job(self, known, project="Homelab", chats=("c2",), project_updated="2026-09-01T00:00:00Z",
                reject=(), not_json=(), photo_type="image/webp", pages=None):
        """Run the project job under Node against a fake claude.ai: (status, saved file)."""
        import claude_chats_archive as A
        self.allow_project()
        manifest = A.load_manifest(self.archive)
        manifest["projects"][self.PID] = {"updated_at": "2026-09-01T00:00:00Z"}
        for cid, updated in known.items():
            manifest["conversations"][cid] = {"project": self.PID, "snapshot": "x", "updated_at": updated, "state": "active"}
        A.save_manifest(self.archive, manifest)
        js = self.cli("snippet", "--project", "Homelab")[1].strip()
        p = f"/organizations/o2/projects/{self.PID}"
        api = {"/organizations": [{"uuid": "o1"}, {"uuid": "o2"}],
               p: {"uuid": self.PID, "name": project, "updated_at": project_updated},
               p + "/docs": [{"file_name": "a.md", "content": "x"}],
               p + "/conversations_v2": {"data": [{"uuid": "c1", "name": "Old", "updated_at": "t1"},
                                                  {"uuid": "c2", "name": "New", "updated_at": "t2"},
                                                  {"uuid": "c3", "name": "PRIVATE thing", "updated_at": "t3"}],
                                         "pagination": {"has_more": False}}}
        for cid in chats:
            api[f"/organizations/o2/chat_conversations/{cid}"] = {
                "uuid": cid, "name": "New", "updated_at": "t2", "project_uuid": self.PID,
                "chat_messages": [{"files": [{"file_uuid": "f1", "file_kind": "image", "file_name": "1.jpg",
                                              "preview_url": "https://files/f1"}]}]}
        program = f"""
const API = {json.dumps(api)};
const REJECT = {json.dumps(list(reject))};
const NOT_JSON = {json.dumps(list(not_json))};
const PAGES = {json.dumps(pages)};
globalThis.location = {{origin: "https://claude.ai"}};
globalThis.window = globalThis;
let saved = null;
const blobs = new Map();
globalThis.document = {{createElement: () => ({{click() {{ saved = this.href; }}, remove() {{}}}}), body: {{appendChild() {{}}}}}};
URL.createObjectURL = b => {{ const id = "blob:" + blobs.size; blobs.set(id, b); return id; }};
URL.revokeObjectURL = () => {{}};
globalThis.fetch = async p => {{
  if (String(p).startsWith("https://files/")) return new Response(new Blob([new Uint8Array([1, 2, 3])], {{type: {json.dumps(photo_type)}}}));
  const key = String(p).replace(/^\\/api/, "").split("?")[0];
  if (PAGES && key.endsWith("/conversations_v2")) return new Response(JSON.stringify(PAGES[/offset=0(&|$)/.test(String(p)) ? 0 : 1]));
  const id = key.split("/").pop();
  if (REJECT.includes(id)) throw new TypeError("Failed to fetch");
  if (NOT_JSON.includes(id)) return new Response("PRIVATE letter, not JSON");
  return key in API ? new Response(JSON.stringify(API[key])) : new Response("{{}}", {{status: 404}});
}};
const started = {js};
const status = await window.__claudeProject.wait();
const file = saved ? JSON.parse(await blobs.get(saved).text()) : null;
console.log(JSON.stringify({{started, status, file}}));
process.exit(0);
"""
        run = subprocess.run(["node", "--input-type=module", "-e", program], capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stderr)
        out = json.loads(run.stdout)
        self.assertEqual(out["started"], "started")
        return out["status"], out["file"]

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_project_job_fetches_only_new_or_changed_chats(self):
        status, file = self.run_job({"c1": "t1"})
        self.assertEqual(status["state"], "saved", status)
        self.assertEqual((status["listed"], status["toFetch"], status["fetched"], status["held"], status["photos"]), (3, 1, 1, 1, 1))
        self.assertNotIn("wait", status)
        self.assertEqual((file["schema"], file["kind"], file["project_id"], file["more"]), (1, "claude-project", self.PID, False))
        self.assertEqual(list(file["conversations"]), ["c2"])
        self.assertIsInstance(file["conversations"]["c2"], str)
        self.assertIsInstance(file["project"], str)
        self.assertEqual(file["held"], ["c3"])
        self.assertEqual([c["uuid"] for c in file["list"]], ["c1", "c2"])
        self.assertEqual(file["files"]["c2"]["f1"]["base64"], "AQID")

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_project_job_saves_nothing_when_nothing_changed(self):
        status, file = self.run_job({"c1": "t1", "c2": "t2"})
        self.assertEqual(status["state"], "unchanged", status)
        self.assertIsNone(file)

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_a_changed_project_still_saves_with_no_chats_to_fetch(self):
        status, file = self.run_job({"c1": "t1", "c2": "t2"}, project_updated="2026-10-01T00:00:00Z")
        self.assertEqual(status["state"], "saved", status)
        self.assertEqual(file["conversations"], {})

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_a_held_project_stops_the_job(self):
        status, file = self.run_job({}, project="PRIVATE letters")
        self.assertEqual(status["state"], "held", status)
        self.assertIsNone(file)

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_a_chat_that_fails_stays_out_and_is_reported(self):
        status, file = self.run_job({"c1": "t1"}, chats=())
        self.assertEqual(status["state"], "saved", status)
        self.assertEqual(status["errors"], [{"id": "c2", "status": 404}])
        self.assertEqual(file["conversations"], {})

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_the_size_limit_stops_after_a_chat_and_asks_for_another_run(self):
        original = C.MAX_PROJECT_BYTES
        C.MAX_PROJECT_BYTES = 10
        self.addCleanup(setattr, C, "MAX_PROJECT_BYTES", original)
        status, file = self.run_job({}, chats=("c1", "c2"))
        self.assertEqual((status["state"], status["fetched"], status["more"]), ("saved", 1, True), status)
        self.assertEqual(len(file["conversations"]), 1)

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_a_chat_whose_fetch_throws_stays_out_and_the_rest_are_saved(self):
        status, file = self.run_job({}, chats=("c1", "c2"), reject=("c1",))
        self.assertEqual(status["state"], "saved", status)
        self.assertEqual(status["errors"], [{"id": "c1", "status": "unreadable"}])
        self.assertEqual(list(file["conversations"]), ["c2"])

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_a_chat_that_isnt_json_is_reported_without_its_text(self):
        status, file = self.run_job({}, chats=("c1", "c2"), not_json=("c1",))
        self.assertEqual(status["state"], "saved", status)
        self.assertEqual(status["errors"], [{"id": "c1", "status": "unreadable"}])
        self.assertNotIn("PRIVATE", json.dumps(status))
        self.assertEqual(list(file["conversations"]), ["c2"])

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_a_photo_of_an_unsupported_type_counts_as_missing(self):
        status, file = self.run_job({"c1": "t1"}, photo_type="image/heic")
        self.assertEqual(status["state"], "saved", status)
        self.assertEqual(file["files"], {})
        self.assertEqual(file["photos_missing"], {"c2": ["f1"]})
        self.assertEqual(list(file["conversations"]), ["c2"])

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_the_job_reads_every_page_of_the_chat_list(self):
        pages = [{"data": [{"uuid": "c1", "name": "Old", "updated_at": "t1"}], "pagination": {"has_more": True}},
                 {"data": [{"uuid": "c2", "name": "New", "updated_at": "t2"}], "pagination": {"has_more": False}}]
        status, file = self.run_job({"c1": "t1"}, pages=pages)
        self.assertEqual((status["listed"], status["toFetch"], file["list_complete"]), (2, 1, True), status)
        self.assertEqual([c["uuid"] for c in file["list"]], ["c1", "c2"])

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_a_chat_list_that_doesnt_say_its_complete_is_marked_so(self):
        status, file = self.run_job({}, pages=[{"data": [{"uuid": "c2", "name": "New", "updated_at": "t2"}]}])
        self.assertEqual((status["state"], file["list_complete"]), ("saved", False), status)

    def test_a_value_from_a_download_can_not_fill_another_placeholder(self):
        import claude_chats_archive as A
        self.allow_project()
        manifest = A.load_manifest(self.archive)
        manifest["projects"][self.PID] = {"updated_at": "};globalThis.hacked=1;//"}
        manifest["conversations"]["c1"] = {"project": self.PID, "snapshot": "x", "state": "active",
                                           "updated_at": "__KNOWN_PROJECT__"}
        A.save_manifest(self.archive, manifest)
        js = self.cli("snippet", "--project", "Homelab")[1]
        self.assertIn('const KNOWN = {"c1": "__KNOWN_PROJECT__"};', js)
        self.assertIn('const KNOWN_PROJECT = "};globalThis.hacked=1;//";', js)

    def test_one_chat_that_cant_be_rendered_leaves_the_others_alone(self):
        import claude_chats_archive as A
        self.allow_project()
        other = "22222222-0000-4000-8000-000000000002"
        self.drop_project_file([self.project_conv(name="Good chat"), self.project_conv(cid=other, name="Spoiled chat")])
        self.assertEqual(self.cli("ingest")[0], 0)
        path = self.archive / A.load_manifest(self.archive)["conversations"][other]["snapshot"]
        spoiled = json.loads(path.read_text())
        spoiled["chat_messages"][0]["created_at"] = "yesterday"
        path.write_text(json.dumps(spoiled))
        code, out, err = self.cli("render", "--apply")
        self.assertEqual(code, 1, out + err)
        self.assertIn(other, out)
        self.assertEqual(len([p for p in self.hub().parent.glob("*.md") if p != self.hub()]), 1)

    def test_a_photo_that_cant_be_read_is_left_out_and_flagged(self):
        data = b"not a picture"
        self.allow_project(', photos = "ze-files/ootd/chats"')
        c = self.project_conv()
        c["chat_messages"][0]["files"] = [{"file_uuid": "f1", "file_name": "1.jpg", "file_kind": "image"}]
        c["chat_messages"][0]["content"].insert(0, {"type": "image", "file_uuid": "f1"})
        out = self.sync_project([c], files={CID: {"f1": {"file_name": "1.jpg", "file_kind": "image", "variant": "preview",
                                                         "mime": "image/webp", "bytes": len(data),
                                                         "base64": base64.b64encode(data).decode()}}})
        self.assertIn("photos that can't be read", out)
        self.assertIn(f"f1 in {CID}", out)
        note = next(p for p in self.hub().parent.glob("*.md") if p != self.hub())
        self.assertIn("1.jpg, not downloaded", note.read_text())
        self.assertFalse((self.vault / "ze-files" / "ootd").exists())

    def drop_project_file(self, chats, listed=None, updated="2026-09-01T00:00:00Z", description="", instructions="", files=None):
        details = {"uuid": self.PID, "name": "Homelab", "created_at": "2026-09-01T00:00:00Z", "updated_at": updated,
                   "description": description, "prompt_template": instructions}
        docs = [{"file_name": "notes.md", "content": "the doc's words stay in the archive"}]
        ids = listed if listed is not None else [c["uuid"] for c in chats]
        bundle = {"schema": 1, "kind": "claude-project", "fetched_at": "2026-11-09T02:00:00Z", "project_id": self.PID,
                  "project": json.dumps(details), "docs": json.dumps(docs),
                  "list": [{"uuid": i, "updated_at": "t"} for i in ids], "held": [],
                  "conversations": {c["uuid"]: json.dumps(c) for c in chats}, "files": files or {},
                  "photos_missing": {}, "errors": [], "more": False}
        (self.downloads / f"claude-project-{self.PID[:8]}.json").write_text(json.dumps(bundle))

    def project_conv(self, cid=CID, texts=("Question", "Answer"), day="2026-10-15", name="A project chat"):
        c = conv(list(texts), cid=cid, name=name)
        for m in c["chat_messages"]:
            m["created_at"] = m["created_at"].replace("2026-10-15", day)
        c["created_at"], c["project_uuid"] = c["chat_messages"][0]["created_at"], self.PID
        return c

    def hub(self):
        return self.vault / "sources" / "claude" / "homelab" / "Homelab (Claude project).md"

    def sync_project(self, *args, **kw):
        self.drop_project_file(*args, **kw)
        code, out, err = self.cli("ingest")
        self.assertEqual(code, 0, out + err)
        code, out, err = self.cli("render", "--apply")
        self.assertEqual(code, 0, out + err)
        return out

    def test_project_note_shows_instructions_and_doc_names_but_not_doc_contents(self):
        self.allow_project()
        self.sync_project([self.project_conv()], description="What I wear", instructions="Be honest about fit.")
        text = self.hub().read_text()
        self.assertIn("What I wear", text)
        self.assertIn("```\nBe honest about fit.\n```", text)
        self.assertIn(f"notes.md ({len('the doc' + chr(39) + 's words stay in the archive')} characters)", text)
        self.assertNotIn("words stay in the archive", text)

    def test_a_projects_photos_land_in_its_own_folder(self):
        from PIL import Image
        buf = io.BytesIO()
        Image.new("RGB", (8, 8), "gray").save(buf, format="WEBP")
        data = buf.getvalue()
        self.allow_project(', photos = "ze-files/ootd/chats"')
        c = self.project_conv()
        c["chat_messages"][0]["files"] = [{"file_uuid": "f1", "file_name": "1.jpg", "file_kind": "image"}]
        c["chat_messages"][0]["content"].insert(0, {"type": "image", "file_uuid": "f1"})
        out = self.sync_project([c], files={CID: {"f1": {"file_name": "1.jpg", "file_kind": "image", "variant": "preview",
                                                         "mime": "image/webp", "bytes": len(data),
                                                         "base64": base64.b64encode(data).decode()}}})
        self.assertIn("photos to file in ze-files/ootd/chats: 1", out)
        self.assertTrue((self.vault / "ze-files" / "ootd" / "chats" / f"{CID[:8]}-01.webp").exists())
        self.assertFalse((self.vault / "ze-files" / "claude").exists())
        note = next(p for p in self.hub().parent.glob("*.md") if p != self.hub())
        self.assertIn(f"![[{CID[:8]}-01.webp|480]]", note.read_text())

    def test_templater_text_in_the_instructions_holds_the_project_note_back(self):
        plugin = self.vault / ".obsidian" / "plugins" / "templater-obsidian"
        plugin.mkdir(parents=True)
        (plugin / "data.json").write_text(json.dumps({"trigger_on_file_creation": True}))
        self.allow_project()
        out = self.sync_project([self.project_conv()], instructions="Use <% tp.date.now() %> today")
        self.assertIn("Templater", out)
        self.assertFalse(self.hub().exists())

    def test_a_big_sync_logs_the_project_note_not_every_chat(self):
        self.allow_project()
        chats = [self.project_conv(cid=f"{i}{i}{i}{i}{i}{i}{i}{i}-0000-4000-8000-00000000000{i}", name=f"Chat {i}") for i in range(1, 7)]
        out = self.sync_project(chats)
        self.assertEqual(out.strip().splitlines()[-1], "- Synced Claude chats: 6 new, 0 updated — [[Homelab (Claude project)]]")

    def test_ingest_takes_a_project_file_and_says_its_first_sync(self):
        self.allow_project()
        self.drop_project_file([self.project_conv()])
        code, out, err = self.cli("ingest")
        self.assertEqual(code, 0, out + err)
        self.assertRegex(out, rf"synced\s+project {self.PID}\s+\(1 new, 0 changed, 0 unchanged, 0 photos, 0 gone, 0 held, first sync\)")
        self.drop_project_file([], listed=[CID], updated="2026-10-01T00:00:00Z")
        self.assertNotIn("first sync", self.cli("ingest")[1])

    def synced_note(self):
        self.allow_project()
        self.sync_project([self.project_conv()])
        return next(p for p in self.hub().parent.glob("*.md") if p != self.hub())

    def queue(self):
        return self.cli("queue", "--project", "Homelab")

    def grow_chat(self):
        grown = self.project_conv(texts=("Question", "Answer", "One more", "Sure"))
        grown["updated_at"] = "2026-10-16T05:00:00Z"
        grown["current_leaf_message_uuid"] = grown["chat_messages"][-1]["uuid"]
        self.sync_project([grown])

    def test_a_chat_with_no_mark_waits(self):
        self.synced_note()
        code, out, err = self.queue()
        self.assertEqual(code, 0, err)
        self.assertIn(CID, out)
        self.assertIn("1 chat waiting", out)

    def test_a_stamped_chat_does_not_wait(self):
        self.synced_note()
        code, out, err = self.cli("processed", CID)
        self.assertEqual(code, 0, err)
        code, out, err = self.queue()
        self.assertEqual(code, 0, err)
        self.assertNotIn(CID, out)
        self.assertIn("0 chats waiting", out)

    def test_a_stamped_chat_with_a_later_reply_waits_again(self):
        self.synced_note()
        self.cli("processed", CID)
        self.grow_chat()
        self.assertIn(CID, self.queue()[1])

    def test_a_reply_sent_before_processing_but_synced_after_still_waits(self):
        self.synced_note()
        self.cli("processed", CID)  # the test clock stamps 16:59; the note has the 16:52 version
        grown = self.project_conv(texts=("Question", "Answer", "One more", "Sure"))
        grown["updated_at"] = "2026-10-15T23:55:00Z"  # 16:55, before the stamp, but the note never had it
        grown["current_leaf_message_uuid"] = grown["chat_messages"][-1]["uuid"]
        self.sync_project([grown])
        self.assertIn(CID, self.queue()[1])

    def test_the_processed_mark_survives_a_re_render(self):
        note = self.synced_note()
        self.cli("processed", CID)
        self.assertIn("Processed: 2026-10-15 16:59", note.read_text())
        self.grow_chat()
        self.assertIn("Processed: 2026-10-15 16:59", note.read_text())

    def test_processed_on_an_unknown_chat_is_66(self):
        self.assertEqual(self.cli("processed", "nope")[0], 66)

    def test_queue_needs_a_project_in_allow(self):
        self.assertEqual(self.queue()[0], 78)

    LOG = "## Today\n\n## Log\n\n- an older line\n"

    def daily_path(self, day):
        return self.vault / "000-periodic_notes" / "daily" / day[:4] / day[5:7] / f"{day}.md"

    def write_daily(self, day, text):
        path = self.daily_path(day)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def daily(self, *flags):
        return self.cli("daily", "--project", "Homelab", *flags)

    def test_daily_dry_run_writes_nothing(self):
        note = self.synced_note()
        path = self.write_daily("2026-10-15", self.LOG)
        code, out, err = self.daily()
        self.assertEqual(code, 0, err)
        self.assertIn("2026-10-15", out)
        self.assertIn(note.stem, out)
        self.assertEqual(path.read_text(), self.LOG)

    def test_the_line_goes_directly_under_log_with_the_days_times(self):
        note = self.synced_note()
        path = self.write_daily("2026-10-15", self.LOG)
        self.assertEqual(self.daily("--apply")[0], 0)
        line = f'- [[{note.stem}]]: a Claude chat in Homelab, "A project chat", 09:00–09:01. Mirrored on 2026-10-15.'
        self.assertEqual(path.read_text(), f"## Today\n\n## Log\n\n{line}\n- an older line\n")

    def test_a_chat_with_no_title_has_no_empty_quotes_in_its_daily_line(self):
        self.allow_project()
        self.sync_project([self.project_conv(name="")])
        path = self.write_daily("2026-10-15", self.LOG)
        self.assertEqual(self.daily("--apply")[0], 0)
        text = path.read_text()
        self.assertNotIn('""', text)
        self.assertIn("a Claude chat in Homelab, 09:00–09:01. Mirrored", text)

    def test_a_chat_across_two_days_gets_a_line_on_each(self):
        self.allow_project()
        c = self.project_conv()
        c["chat_messages"][1]["created_at"] = "2026-10-16T17:00:00Z"
        self.sync_project([c])
        first, second = self.write_daily("2026-10-15", self.LOG), self.write_daily("2026-10-16", self.LOG)
        self.daily("--apply")
        self.assertIn('"A project chat", 09:00. Mirrored', first.read_text())
        self.assertIn('"A project chat", 10:00. Mirrored', second.read_text())

    def test_a_second_run_adds_nothing(self):
        self.synced_note()
        path = self.write_daily("2026-10-15", self.LOG)
        self.daily("--apply")
        before = path.read_text()
        code, out, _ = self.daily("--apply")
        self.assertEqual(code, 0)
        self.assertEqual(path.read_text(), before)
        self.assertIn("0 links", out)

    def test_a_link_already_in_the_note_is_not_added_again(self):
        note = self.synced_note()
        text = f"## Log\n\n- [[{note.stem}]]: written by hand\n"
        path = self.write_daily("2026-10-15", text)
        self.daily("--apply")
        self.assertEqual(path.read_text(), text)

    def test_a_link_dan_removed_stays_removed(self):
        self.synced_note()
        path = self.write_daily("2026-10-15", self.LOG)
        self.daily("--apply")
        path.write_text(self.LOG)
        self.daily("--apply")
        self.assertEqual(path.read_text(), self.LOG)

    def test_a_missing_daily_note_is_made_from_the_template(self):
        self.synced_note()
        template = self.vault / "ze-templates" / "template-daily.md"
        template.parent.mkdir()
        template.write_text("## Today\n\n\n## UBC\n\n\n## Log\n\n")
        self.daily("--apply")
        self.assertTrue(self.daily_path("2026-10-15").read_text().startswith("## Today\n\n\n## UBC\n\n\n## Log\n\n- [["))

    def test_an_older_note_with_new_notes_uses_that_heading(self):
        self.synced_note()
        path = self.write_daily("2026-10-15", "## New notes\n\n- old\n")
        self.daily("--apply")
        self.assertIn("## New notes\n\n- [[", path.read_text())

    def test_a_note_with_neither_heading_gains_log(self):
        self.synced_note()
        path = self.write_daily("2026-10-15", "Just text\n")
        self.daily("--apply")
        text = path.read_text()
        self.assertTrue(text.startswith("Just text\n"))
        self.assertIn("\n## Log\n\n- [[", text)

    def test_the_email_block_is_left_alone(self):
        self.synced_note()
        block = "<!-- ea-email:begin todos -->\n## Email\n- [ ] x <!-- ea:1 -->\n<!-- ea-email:end todos -->\n"
        path = self.write_daily("2026-10-15", "## Today\n\n" + block + "\n## Log\n\n- older\n")
        self.daily("--apply")
        self.assertTrue(path.read_text().startswith("## Today\n\n" + block + "\n## Log\n\n- [["))

    def summarize(self, text, *flags):
        path = Path(self.tmp.name) / "summary.md"
        path.write_text(text)
        return self.cli("summary", CID, "--file", str(path), *flags)

    def test_summary_update_goes_under_the_written_summary(self):
        self.capture(conv(["Pool?", "Grow it."]))
        self.cli("render", "--apply")
        self.summarize("First summary.")
        code, out, err = self.summarize("It went on.", "--update")
        self.assertEqual(code, 0, out + err)
        self.assertIn("First summary.\n\n### Update 2026-10-15\n\nIt went on.", self.note().read_text())

    def test_summary_update_on_a_pending_note_writes_the_summary(self):
        self.capture(conv(["Pool?", "Grow it."]))
        self.cli("render", "--apply")
        code, out, err = self.summarize("Only summary.", "--update")
        self.assertEqual(code, 0, out + err)
        self.assertIn("## Summary\n\nOnly summary.\n\n", self.note().read_text())

    def chat_file(self, with_photo=True):
        """Drop a claude-chat-*.json whose chat shows one photo, carried in the file or not."""
        from PIL import Image
        buf = io.BytesIO()
        Image.new("RGB", (8, 8), "gray").save(buf, format="WEBP")
        data = buf.getvalue()
        c = conv(["here is the wall", "nice"])
        c["chat_messages"][0]["files"] = [{"file_uuid": "f1", "file_name": "1326.jpg", "file_kind": "image"}]
        c["chat_messages"][0]["content"].insert(0, {"type": "image", "file_uuid": "f1"})
        files = {"f1": {"file_name": "1326.jpg", "file_kind": "image", "variant": "preview", "mime": "image/webp",
                        "width": 8, "height": 8, "bytes": len(data), "base64": base64.b64encode(data).decode()}}
        bundle = {"schema": 1, "kind": "claude-chat", "fetched_at": "2026-11-01T02:00:00Z", "share": None,
                  "conversation": json.dumps(c), "files": files if with_photo else {}}
        (self.downloads / f"claude-chat-{CID[:8]}.json").write_text(json.dumps(bundle))

    def test_one_download_carries_a_chat_and_its_photos(self):
        self.chat_file()
        code, out, err = self.cli("ingest")
        self.assertEqual(code, 0, out + err)
        self.assertRegex(out, rf"new\s+{CID}\s+\(1 photo archived\)")
        self.cli("render", "--apply")
        self.assertIn(f"![[{CID[:8]}-01.webp|480]]", self.note().read_text())

    PID = "a1b2c3d4-0000-4000-8000-000000000002"

    def project_chat(self, cid, day, name="Homelab"):
        c = conv([f"Question {cid[:4]}", "Answer"], cid=cid, name=f"Chat {cid[:4]}")
        for m in c["chat_messages"]:
            m["created_at"] = m["created_at"].replace("2026-10-15", day)
        c["created_at"], c["project_uuid"] = c["chat_messages"][0]["created_at"], self.PID
        bundle = {"schema": 1, "kind": "claude-chat", "fetched_at": "2026-11-01T02:00:00Z", "share": None,
                  "conversation": json.dumps(c), "files": {},
                  "project": {"uuid": self.PID, "name": name, "created_at": "2026-09-01T00:00:00Z"}}
        (self.downloads / f"claude-chat-{cid[:8]}.json").write_text(json.dumps(bundle))
        code, out, err = self.cli("ingest")
        self.assertEqual(code, 0, out + err)
        code, out, err = self.cli("render", "--apply")
        self.assertEqual(code, 0, out + err)
        return out

    def test_a_project_chat_gets_its_project_folder_and_a_project_note(self):
        out = self.project_chat(CID, "2026-10-15")
        folder = self.vault / "sources" / "claude" / "homelab"
        hub = folder / "Homelab (Claude project).md"
        self.assertTrue(hub.exists(), out)
        chats = [p for p in folder.glob("*.md") if p != hub]
        self.assertEqual(len(chats), 1)
        stems = {p.stem for p in self.vault.rglob("*.md")}
        for note in (hub, chats[0]):
            for target in WIKILINK_RE.findall(note.read_text()):
                self.assertIn(target, stems, f"{note.name} links to the missing note {target}")
        text = hub.read_text()
        self.assertIn(f"[[{chats[0].stem}]]", text)
        self.assertIn(f"Project ID: {self.PID}", text)
        self.assertIn(f"Source: https://claude.ai/project/{self.PID}", text)

    def test_the_project_note_lists_each_chat_newest_first_and_keeps_dans_text(self):
        self.project_chat(CID, "2026-10-15")
        hub = self.vault / "sources" / "claude" / "homelab" / "Homelab (Claude project).md"
        hub.write_text(hub.read_text() + "\nMy own notes on this project.\n")
        later = "b2c3d4e5-0000-4000-8000-000000000003"
        self.project_chat(later, "2026-10-20")
        text = hub.read_text()
        self.assertIn("My own notes on this project.", text)
        first, second = text.index("[[2026-10-20"), text.index("[[2026-10-15")
        self.assertLess(first, second)

    def test_photos_alone_dont_mark_the_summary_out_of_date(self):
        self.chat_file(with_photo=False)
        self.cli("ingest")
        self.cli("render", "--apply")
        self.summarize("About the wall.")
        self.chat_file()
        self.cli("ingest")
        code, out, _ = self.cli("render", "--apply")
        self.assertIn("updated (1)", out)
        self.assertNotIn("summary may be out of date", out)

    def test_photos_added_to_an_archived_chat_are_reported_as_added(self):
        self.chat_file(with_photo=False)
        self.cli("ingest")
        self.chat_file()
        code, out, err = self.cli("ingest")
        self.assertEqual(code, 0, out + err)
        self.assertRegex(out, rf"unchanged\s+{CID}\s+\(chat already archived; 1 photo added\)")
        self.assertNotIn("Trash", out)
        self.assertEqual(self.trashed, [])

    def test_photos_of_a_held_chat_are_never_archived(self):
        self.drop(conv(["a"], name="PRIVATE notes"))
        bundle = {"schema": 1, "kind": "claude-chat-files", "conversation": CID, "fetched_at": "2026-11-01T02:00:00Z",
                  "files": {"f1": {"file_name": "x.jpg", "file_kind": "image", "variant": "preview",
                                   "mime": "image/webp", "bytes": 3, "base64": base64.b64encode(b"abc").decode()}}}
        (self.downloads / f"claude-files-{CID[:8]}.json").write_text(json.dumps(bundle))
        code, out, _ = self.cli("ingest")
        self.assertEqual(code, 0, out)
        self.assertIn("photos of a held chat", out)
        self.assertEqual(len(self.trashed), 2)
        self.assertFalse((self.archive / "conversations").exists())

    def bare_cli(self, *args):
        """Run as the skill does: only the vault is named, and the vault names its archive."""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = C.main(["--vault", str(self.vault), *args], trash=self.trashed.append, now=NOW)
        return code, out.getvalue(), err.getvalue()

    def test_archive_comes_from_the_vault(self):
        (self.vault / ".claude").mkdir()
        rel = os.path.relpath(self.archive, self.vault)
        (self.vault / ".claude" / "claude-chats.toml").write_text(f'archive = "{rel}"\n')
        code, out, err = self.bare_cli("status")
        self.assertEqual(code, 0, err)
        self.assertIn(str(self.archive.resolve()), out)

    def test_no_archive_setting_is_78(self):
        code, _, err = self.bare_cli("status")
        self.assertEqual(code, 78)
        self.assertIn("claude-chats.toml", err)

    def test_exit_codes(self):
        self.assertEqual(self.cli("ingest")[0], 66)
        bad = self.downloads / "claude-conversation-bad.json"
        bad.write_text("{nope")
        self.assertEqual(self.cli("ingest")[0], 65)
        bad.unlink()
        from claude_chats_archive import Lock
        with Lock(self.archive):
            self.drop(conv(["a"]))
            self.assertEqual(self.cli("ingest")[0], 75)
        self.assertEqual(self.cli("nonsense")[0], 64)
        self.assertEqual(self.cli("--help")[0], 0)
        (self.archive / "config.toml").write_text("allow = [ {")
        self.assertEqual(self.cli("status")[0], 78)


class SkillText(unittest.TestCase):
    def test_the_project_steps_give_commands_that_work(self):
        text = (Path(__file__).parent.parent / "references" / "projects.md").read_text(encoding="utf-8")
        self.assertIn("Repeat steps 1 to 3", text)  # the job is told what's archived when it's generated
        self.assertIn("daily --project", text)


if __name__ == "__main__":
    unittest.main()

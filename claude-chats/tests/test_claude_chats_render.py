#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "markdown-it-py>=3.0",
#     "pyyaml>=6.0.3",
# ]
# ///
"""Tests for claude_chats_render.py. Run from the vault root:

    uv run claude-chats/tests/test_claude_chats_render.py -v

Synthetic conversations only -- no real chat text.
"""
import os
import re
import sys
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

import yaml  # noqa: E402

import claude_chats_render as R  # noqa: E402

WIKILINK_RE = re.compile(r'!?\[\[([^\]|#\\]+)(?:#[^\]|\\]*)?(?:\\?\|[^\]]*)?\]\]')
ROOT = "00000000-0000-4000-8000-000000000000"
TZ = "America/Vancouver"
SYNCED = datetime(2026, 10, 15, 23, 59, tzinfo=timezone.utc)


def msg(uuid, parent, sender, text, at, **extra):
    return {"uuid": uuid, "parent_message_uuid": parent, "sender": sender, "created_at": at,
            "text": "", "content": [{"type": "text", "text": text}], **extra}


def conv(messages, leaf=None, name="Storage pool fix", project=None):
    return {"uuid": "c0ffee00-1111-2222-3333-444455556666", "name": name, "project_uuid": project,
            "created_at": messages[0]["created_at"] if messages else "2026-10-15T16:00:00Z",
            "updated_at": "2026-10-15T23:52:05.738460Z",
            "current_leaf_message_uuid": leaf or (messages[-1]["uuid"] if messages else None),
            "chat_messages": messages}


LINEAR = [
    msg("m1", ROOT, "human", "Hello", "2026-10-15T16:03:04.123456Z"),
    msg("m2", "m1", "assistant", "Hi there", "2026-10-15T16:03:10.000000Z"),
]


class Branches(unittest.TestCase):
    def test_linear(self):
        b = R.current_branch(conv(LINEAR))
        self.assertEqual([m["uuid"] for m in b.messages], ["m1", "m2"])
        self.assertEqual((b.other_branches, b.leaf_missing), (0, False))

    def test_edit_makes_a_branch(self):
        msgs = LINEAR + [msg("m2b", "m1", "assistant", "Alt", "2026-10-15T16:04:00Z")]
        b = R.current_branch(conv(msgs, leaf="m2"))
        self.assertEqual([m["uuid"] for m in b.messages], ["m1", "m2"])
        self.assertEqual(b.other_branches, 1)

    def test_missing_leaf_falls_back_to_newest(self):
        msgs = LINEAR + [msg("m2b", "m1", "assistant", "Alt", "2026-10-15T16:09:00Z")]
        b = R.current_branch(conv(msgs, leaf="gone"))
        self.assertEqual(b.messages[-1]["uuid"], "m2b")
        self.assertTrue(b.leaf_missing)

    def test_empty(self):
        self.assertEqual(R.current_branch(conv([])).messages, [])


class Escaping(unittest.TestCase):
    def test_wikilink_embed_tag_html_and_templater_are_inert(self):
        out = R.escape_prose("see [[Note]] and ![[img.png]] #idea <vg> <% tp.date %>\n#start")
        self.assertEqual(WIKILINK_RE.findall(out), [])
        self.assertIn(r"\[\[Note]]", out)
        self.assertIn(r"!\[\[img.png]]", out)
        self.assertIn(r"\#idea", out)
        self.assertIn(r"\<vg>", out)
        self.assertNotIn("<%", out)
        self.assertTrue(out.split("\n")[1].startswith(r"\#start"))

    def test_headings_mid_word_hash_comparisons_and_urls_untouched(self):
        text = "## Heading\nissue#12 and C# code\nif a < b then\n<https://example.com>"
        self.assertEqual(R.escape_prose(text), text)

    def test_relative_links_are_neutralised_external_kept(self):
        out = R.escape_prose("[doc](Note.md) and ![pic](img.png) and [site](https://x.org) and [top](#a)")
        self.assertIn(r"\[doc](Note.md)", out)
        self.assertIn(r"!\[pic](img.png)", out)
        self.assertIn("[site](https://x.org)", out)
        self.assertIn("[top](#a)", out)

    def test_remote_images_in_prose_do_not_load(self):
        # Obsidian fetches a remote image as soon as the note opens, so text a chat picked up
        # from a web page could carry a tracking pixel, or a URL with data in it, into the vault.
        out = R.escape_prose("![a](https://img.example/p.png?d=1) and ![b](<http://img.example/q.png>)")
        self.assertIn(r"\![a](https://img.example/p.png?d=1)", out)
        self.assertIn(r"\![b](<http://img.example/q.png>)", out)

    def test_links_other_than_the_web_are_neutralised(self):
        out = R.escape_prose("[a](obsidian://open?vault=v) [b](file:///tmp/x) [c](javascript:void(0)) [d](<obsidian://x>)")
        for inert in (r"\[a]", r"\[b]", r"\[c]", r"\[d]"):
            self.assertIn(inert, out)

    def test_code_is_left_alone(self):
        text = "Use `[[x]]` inline\n```toml\n[[allow]]\n#comment <vg>\n```\nafter [[y]]"
        out = R.escape_prose(text)
        self.assertIn("`[[x]]`", out)
        self.assertIn("[[allow]]\n#comment <vg>", out)
        self.assertIn(r"after \[\[y]]", out)

    def test_hash_right_after_inline_code_is_not_a_tag(self):
        self.assertEqual(R.escape_line("`x`#y"), "`x`#y")

    def test_top_level_unclosed_fence_is_closed(self):
        self.assertTrue(R.escape_prose("```python\nprint(1)").endswith("\n```"))
        self.assertTrue(R.escape_prose("~~~~\nx\n").endswith("\n~~~~"))

    def test_closed_fence_gets_no_extra_closer(self):
        self.assertEqual(R.escape_prose("```\nx\n```"), "```\nx\n```")

    def test_fence_in_list_item_gets_no_closer(self):
        # CommonMark closes it when the item ends; an added ``` would open a new fence.
        self.assertFalse(R.escape_prose("1. step\n   ```\n   x").rstrip().endswith("\n```"))

    def test_backticks_in_info_string_are_prose(self):
        out = R.escape_prose("```a``` [[Live]]\nnext")
        self.assertIn(r"\[\[Live]]", out)
        self.assertFalse(out.endswith("```"))

    def test_marker_text_in_prose_is_inert(self):
        out = R.escape_prose(R.TRANSCRIPT_END)
        self.assertNotEqual(out.strip(), R.TRANSCRIPT_END)


class LiteralHumanText(unittest.TestCase):
    """claude.ai shows what Dan typed as plain text, so his turns render literally."""

    def test_shell_prompts_and_continuations_are_not_markdown(self):
        out = R.literal_text("# ls -d /proc/7379\n> done\n- item\n1. step\n---")
        # each escape shown with its hard-break backslash; the last line has no break
        self.assertEqual(out.split("\n"), ["\\# ls -d /proc/7379\\", "\\> done\\", "\\- item\\",
                                           "1\\. step\\", "\\---"])

    def test_line_breaks_become_hard_breaks_but_blank_lines_stay_blank(self):
        self.assertEqual(R.literal_text("a\nb\n\nc"), "a\\\nb\n\nc")

    def test_backslashes_dollars_stars_backticks_survive(self):
        out = R.literal_text("grep 'lost\\+found' ~$ *.log `date` x_ _y snake_case")
        self.assertEqual(out, "grep 'lost\\\\+found' ~\\$ \\*.log \\`date\\` x\\_ \\_y snake_case")

    def test_obsidian_syntax_stays_inert(self):
        out = R.literal_text("[[x]] [link](Note.md) #tag <none> <% t %> ==hi== %%c%%")
        self.assertEqual(WIKILINK_RE.findall(out), [])
        for frag in (r"\[\[x]]", r"\[link](Note.md)", r"\#tag", r"\<none>", "<\\%", r"\=\=hi", r"\%\%c"):
            self.assertIn(frag, out)

    def test_indentation_is_kept_without_becoming_a_code_block(self):
        out = R.literal_text("lecture:\n\n    #1) Respect")
        self.assertTrue(out.endswith(" " * 4 + r"\#1) Respect"))
        self.assertEqual(R.code_lines(out), set())

    def test_human_turns_are_literal_and_claude_turns_are_markdown(self):
        msgs = [msg("m1", ROOT, "human", "# prompt\nnext", "2026-10-15T16:00:00Z"),
                msg("m2", "m1", "assistant", "## Heading\n\n**bold**", "2026-10-15T16:01:00Z")]
        r = R.render_region(conv(msgs), None, "Daniel", TZ)
        self.assertIn("\\# prompt\\\nnext", r.region)
        self.assertIn("## Heading\n\n**bold**", r.region)


class Photos(unittest.TestCase):
    def convo(self):
        m = msg("m1", ROOT, "human", "here's the wall", "2026-10-23T07:47:00Z")
        m["files"] = [{"file_uuid": "f1", "file_name": "1326.jpg", "file_kind": "image"},
                      {"file_uuid": "f2", "file_name": "1327.jpg", "file_kind": "image"},
                      {"file_uuid": "f3", "file_name": "scan.pdf", "file_kind": "document"}]
        m["content"] = [{"type": "image", "file_uuid": "f1"}, {"type": "text", "text": "here's the wall"}]
        a = msg("m2", "m1", "assistant", "Nice wall.", "2026-10-23T07:48:00Z")
        return conv([m, a])

    def test_order_of_first_appearance(self):
        self.assertEqual(R.image_order(self.convo()), ["f1", "f2"])

    def test_embedded_where_they_appear_and_never_twice(self):
        r = R.render_region(self.convo(), None, "Daniel", TZ, images={"f1": "c0ffee00-01.webp", "f2": "c0ffee00-02.webp"})
        self.assertEqual(r.region.count("![[c0ffee00-01.webp|480]]"), 1)
        self.assertEqual(r.region.count("![[c0ffee00-02.webp|480]]"), 1)
        # the block's photo sits where the block is: before the text
        self.assertLess(r.region.index("c0ffee00-01.webp"), r.region.index("here's the wall"))
        self.assertIn("📎 scan.pdf (document), not downloaded", r.region)

    def test_not_downloaded_photo_says_so(self):
        r = R.render_region(self.convo(), None, "Daniel", TZ, images={})
        self.assertIn("📷 1326.jpg, not downloaded", r.region)
        self.assertNotIn("Unrendered block", r.region)


class LongToolStrings(unittest.TestCase):
    def test_long_strings_get_their_own_block(self):
        a = msg("m1", ROOT, "assistant", "", "2026-10-23T07:00:00Z")
        doc = "# Patio plan\n\n" + "- cover the chairs\n" * 40
        a["content"] = [{"type": "tool_use", "id": "t1", "name": "Claude Docs:update",
                         "input": {"container": {"id": "d1", "kind": "project"}, "payload": doc}}]
        r = R.render_region(conv([a]), None, "Daniel", TZ)
        self.assertIn('"payload": "(shown below)"', r.region)
        self.assertIn("> **payload:**\n>\n> ```text\n> # Patio plan", r.region)


class Fences(unittest.TestCase):
    def test_minimum_three_and_longer_than_inner(self):
        self.assertTrue(R.fence("x").startswith("```\n"))
        self.assertTrue(R.fence("a ```` b", "text").startswith("`````text\n"))

    def test_info_cannot_break_the_fence(self):
        self.assertTrue(R.fence("x", "a`b").startswith("```a'b\n"))


class Turns(unittest.TestCase):
    def region(self, messages, project=None):
        return R.render_region(conv(messages), project, "Daniel", TZ)

    def test_headers_and_times(self):
        r = self.region(LINEAR)
        self.assertTrue(r.region.startswith(R.TRANSCRIPT_BEGIN))
        self.assertTrue(r.region.endswith(R.TRANSCRIPT_END))
        self.assertIn("### [2026-10-15 09:03] **Daniel** _(text)_\n\nHello", r.region)
        self.assertIn("### [2026-10-15 09:03] **Claude** _(text)_\n\nHi there", r.region)
        self.assertIn("outside any project", r.region)
        self.assertIn("2026-10-15 09:03–09:03 PDT, 2 messages", r.region)
        self.assertEqual(r.message_ids, ["m1", "m2"])

    def test_voice_mode_and_project_link(self):
        msgs = [msg("m1", ROOT, "human", "hi", "2026-10-15T16:00:00Z", input_mode="voice")]
        r = self.region(msgs, project="Homelab (Claude project)")
        self.assertIn("**Daniel** _(voice)_", r.region)
        self.assertIn("in the project [[Homelab (Claude project)]]", r.region)

    def test_utc_evening_is_previous_local_day(self):
        r = self.region([msg("m1", ROOT, "human", "late", "2026-10-16T04:30:00Z")])
        self.assertEqual(R.minute(r.start), "2026-10-15 21:30")

    def test_thinking_attachment_and_file(self):
        m = msg("m1", ROOT, "human", "see output", "2026-10-15T16:00:00Z")
        m["attachments"] = [{"file_name": "mdstat.txt", "file_size": 1234,
                             "extracted_content": "md2 : active raid6 [[x]]"}]
        m["files"] = [{"file_name": "pool.png", "file_kind": "image"}]
        a = msg("m2", "m1", "assistant", "", "2026-10-15T16:01:00Z")
        a["content"] = [{"type": "thinking", "thinking": "The pool grew but #lvm didn't."},
                        {"type": "text", "text": "Run `lvextend`."}]
        r = self.region([m, a])
        self.assertIn("> [!example]- Pasted: mdstat.txt (1,234 bytes)\n> ```text\n> md2 : active raid6 [[x]]\n> ```", r.region)
        self.assertIn("📷 pool.png, not downloaded", r.region)
        self.assertIn("> [!note]- Claude's thinking\n> The pool grew but \\#lvm didn't.", r.region)
        self.assertIn("Run `lvextend`.", r.region)

    def test_null_text_and_text_only_messages(self):
        m = msg("m1", ROOT, "human", "x", "2026-10-15T16:00:00Z")
        m["content"] = [{"type": "text", "text": None}, {"type": "thinking", "thinking": None}]
        old = {"uuid": "m2", "parent_message_uuid": "m1", "sender": "assistant",
               "created_at": "2026-10-15T16:01:00Z", "text": "plain old text", "content": []}
        r = self.region([m, old])
        self.assertIn("plain old text", r.region)

    def test_tools(self):
        a = msg("m1", ROOT, "assistant", "", "2026-10-15T16:00:00Z")
        a["content"] = [
            {"type": "tool_use", "id": "t1", "name": "web_search", "input": {"query": "shelf bracket spacing"}},
            {"type": "tool_result", "tool_use_id": "t1", "content": [
                {"type": "knowledge", "title": "Expand a volume [guide]", "url": "https://kb.example/expand"}]},
            {"type": "tool_use", "id": "t2", "name": "memory_read", "input": {"path": "/memories"}},
            {"type": "tool_result", "tool_use_id": "t2", "content": [{"type": "text", "text": "SECRET OTHER CHAT"}]},
            {"type": "tool_use", "id": "t3", "name": "artifacts",
             "input": {"command": "create", "type": "text/markdown", "title": "Steps", "content": "## Step 1\n[[x]]"}},
            {"type": "brand_new_block", "x": 1},
        ]
        r = self.region([a])
        self.assertIn("> [!info]- Searched the web: shelf bracket spacing\n> - [Expand a volume \\[guide\\]](https://kb.example/expand)", r.region)
        self.assertNotIn("SECRET OTHER CHAT", r.region)
        self.assertIn("kept in the raw archive", r.region)
        self.assertIn("> [!example]+ Artifact: Steps\n> ## Step 1\n> \\[\\[x]]", r.region)
        self.assertIn("> [!warning]- Unrendered block: brand_new_block", r.region)
        self.assertEqual(r.unknown_blocks, {"brand_new_block"})

    def test_parallel_tool_results_stay_with_their_own_calls(self):
        """Parallel calls put every call first and the results after, so position means nothing."""
        a = msg("m1", ROOT, "assistant", "", "2026-10-15T16:00:00Z")
        a["content"] = [
            {"type": "tool_use", "id": "t1", "name": "memory_read", "input": {}},
            {"type": "tool_use", "id": "t2", "name": "web_search", "input": {"query": "strap drop length"}},
            {"type": "tool_result", "tool_use_id": "t1", "name": "memory_read",
             "content": [{"type": "text", "text": "SECRET OTHER CHAT"}]},
            {"type": "tool_result", "tool_use_id": "t2", "name": "web_search",
             "content": [{"type": "knowledge", "title": "Strap guide", "url": "https://kb.example/strap"}]},
        ]
        r = self.region([a])
        self.assertNotIn("SECRET OTHER CHAT", r.region)
        self.assertIn("> [!info]- Searched the web: strap drop length\n> - [Strap guide](https://kb.example/strap)", r.region)
        self.assertIn("kept in the raw archive", r.region)

    def test_a_result_with_no_call_in_its_message_is_judged_by_its_own_tool(self):
        a = msg("m1", ROOT, "assistant", "", "2026-10-15T16:00:00Z")
        a["content"] = [
            {"type": "tool_use", "id": "t1", "name": "web_search", "input": {"query": "q"}},
            {"type": "tool_result", "tool_use_id": "elsewhere", "name": "memory_read",
             "content": [{"type": "text", "text": "SECRET OTHER CHAT"}]},
        ]
        r = self.region([a])
        self.assertNotIn("SECRET OTHER CHAT", r.region)
        self.assertIn("kept in the raw archive", r.region)

    def test_a_url_from_a_tool_or_a_citation_stays_inside_its_link(self):
        url = "https://kb.example/a) ![p](https://img.example/p.png"
        a = msg("m1", ROOT, "assistant", "", "2026-10-15T16:00:00Z")
        a["content"] = [
            {"type": "tool_use", "id": "t1", "name": "web_search", "input": {"query": "q"}},
            {"type": "tool_result", "tool_use_id": "t1", "content": [{"type": "knowledge", "title": "T", "url": url}]},
            {"type": "text", "text": "Done.", "citations": [{"url": url, "title": "T"}]},
        ]
        r = self.region([a])
        self.assertEqual(r.region.count("[T](https://kb.example/a%29%20![p]%28https://img.example/p.png)"), 2)

    def test_unclosed_fence_does_not_swallow_the_next_turn(self):
        msgs = [msg("m1", ROOT, "assistant", "```bash\nmdadm --detail", "2026-10-15T16:00:00Z"),
                msg("m2", "m1", "human", "thanks [[x]]", "2026-10-15T16:01:00Z")]
        r = self.region(msgs)
        lines = r.region.split("\n")
        code = R.code_lines(r.region)
        self.assertNotIn(lines.index(r"thanks \[\[x]]"), code)
        self.assertNotIn(lines.index("### [2026-10-15 09:01] **Daniel** _(text)_"), code)
        self.assertNotIn(len(lines) - 1, code)  # the end marker


class Names(unittest.TestCase):
    def test_slug(self):
        self.assertEqual(R.slugify("Garage shelf build plan", "u"), "garage-shelf-build-plan")
        self.assertEqual(R.slugify("🏃‍♂️🌧️", "abcdef12-x"), "chat-abcdef12")
        self.assertEqual(R.slugify("Café à la carte", "u"), "cafe-a-la-carte")
        self.assertLessEqual(len(R.slugify("x" * 200, "u")), 60)

    def test_stem_never_returns_a_taken_name(self):
        start = R.to_local("2026-10-15T16:03:00Z", TZ)
        taken = {"2026-10-15-0903-fix"}
        self.assertEqual(R.note_stem(start, "Fix", "abcdef12-rest", taken), "2026-10-15-0903-fix-abcdef12")
        taken.add("2026-10-15-0903-fix-abcdef12")
        self.assertEqual(R.note_stem(start, "Fix", "abcdef12-rest", taken), "2026-10-15-0903-fix-abcdef12-2")

    def test_folders(self):
        self.assertEqual(R.folder_slug("Home Lab: NAS #2", "p1234567", set()), "home-lab-nas-2")
        self.assertEqual(R.folder_slug("Home Lab", "p1234567", {"home-lab"}), "home-lab-p1234567")
        self.assertEqual(R.project_note_stem('A/B: "C" [x]'), "A-B- -C- -x- (Claude project)")


class Notes(unittest.TestCase):
    def setUp(self):
        self.c = conv(LINEAR, name='Run: "fast" #1\x7f')
        self.r = R.render_region(self.c, None, "Daniel", TZ)
        self.owned = R.transcript_frontmatter(self.c, self.r, None, SYNCED, TZ)

    def test_new_note_shape_and_yaml(self):
        text = R.new_note(self.owned, self.r.region)
        fm = yaml.safe_load(text.split("---\n")[1])
        self.assertEqual(fm["Title"], 'Run: "fast" #1')
        self.assertEqual(fm["Tags"], ["claude_chat"])
        self.assertEqual(fm["Summary"], "pending")
        self.assertEqual(fm["Created"], "2026-10-15 09:03")
        self.assertNotIn("Project", fm)
        body = text.split("---\n", 2)[2]
        self.assertTrue(body.startswith("\n## Summary\n\n" + R.SUMMARY_PENDING + "\n\n" + R.TRANSCRIPT_BEGIN))

    def test_unchanged_and_volatile_keys(self):
        first = R.new_note(self.owned, self.r.region)
        later = dict(self.owned, **{"Modification date": "2026-10-20 09:00", "Synced": "2026-10-20 09:00"})
        out = R.update_note(first, later, R.TRANSCRIPT_KEYS, self.r.region)
        self.assertEqual((out.status, out.text), ("unchanged", first))

    def test_update_keeps_summary_notes_tags_and_foreign_keys(self):
        first = R.new_note(self.owned, self.r.region)
        edited = first.replace("Tags: [claude_chat]", "Tags: [claude_chat, homelab]")
        edited = edited.replace("Summary: pending", "Summary: Claude 2026-10-15\nThinking note: \"[[x]]\"")
        edited = edited.replace(R.SUMMARY_PENDING, "Grew the volume after a disk swap.")
        edited += "\n## My notes\n\nKeep [[Real Link]].\n"
        grown = conv(LINEAR + [msg("m3", "m2", "human", "more", "2026-10-15T16:30:00Z")], name="Storage pool fix")
        r2 = R.render_region(grown, None, "Daniel", TZ)
        o2 = R.transcript_frontmatter(grown, r2, None, SYNCED, TZ)
        out = R.update_note(edited, o2, R.TRANSCRIPT_KEYS, r2.region)
        self.assertEqual(out.status, "updated")
        for kept in ("Tags: [claude_chat, homelab]", "Summary: Claude 2026-10-15", 'Thinking note: "[[x]]"',
                     "Grew the volume after a disk swap.", "## My notes\n\nKeep [[Real Link]].\n"):
            self.assertIn(kept, out.text)
        self.assertIn("more", out.text)
        self.assertEqual(out.text.count(R.TRANSCRIPT_BEGIN), 1)

    def test_quoted_marker_in_chat_cannot_corrupt_the_note(self):
        c = conv([msg("m1", ROOT, "human", "```\n" + R.TRANSCRIPT_END + "\n```\nand " + R.TRANSCRIPT_END,
                      "2026-10-15T16:00:00Z")])
        r = R.render_region(c, None, "Daniel", TZ)
        o = R.transcript_frontmatter(c, r, None, SYNCED, TZ)
        first = R.new_note(o, r.region)
        again = R.update_note(first, o, R.TRANSCRIPT_KEYS, r.region)
        self.assertEqual(again.status, "unchanged")

    def test_missing_marker_raises(self):
        with self.assertRaises(R.MarkerError):
            R.update_note("---\nTitle: x\n---\nno markers\n", self.owned, R.TRANSCRIPT_KEYS, self.r.region)

    def test_set_summary(self):
        first = R.new_note(self.owned, self.r.region)
        out = R.set_summary(first, "It was about [[Garage Shelves]].", "Claude 2026-10-15")
        self.assertIn("## Summary\n\nIt was about [[Garage Shelves]].\n\n" + R.TRANSCRIPT_BEGIN, out)
        self.assertIn("Summary: Claude 2026-10-15", out)
        self.assertNotIn("Summary: pending", out)
        with self.assertRaises(R.AlreadySummarized):
            R.set_summary(out, "again", "Claude 2026-10-16")
        self.assertIn("again", R.set_summary(out, "again", "Claude 2026-10-16", force=True))

    def test_update_goes_under_the_summary_and_keeps_it(self):
        first = R.set_summary(R.new_note(self.owned, self.r.region), "Dan's edited summary.", "Claude 2026-10-15")
        out = R.add_summary_update(first, "The chat went on to pick a colour.", "2026-11-15")
        self.assertIn("## Summary\n\nDan's edited summary.\n\n### Update 2026-11-15\n\n"
                      "The chat went on to pick a colour.\n\n" + R.TRANSCRIPT_BEGIN, out)
        self.assertIn("Summary: Claude 2026-10-15; updated 2026-11-15", out)
        again = R.add_summary_update(out, "And bought it.", "2026-12-01")
        self.assertIn("pick a colour.\n\n### Update 2026-12-01\n\nAnd bought it.\n\n" + R.TRANSCRIPT_BEGIN, again)
        self.assertIn("Summary: Claude 2026-10-15; updated 2026-12-01", again)

    def test_update_needs_a_summary_first(self):
        with self.assertRaises(R.MarkerError):
            R.add_summary_update(R.new_note(self.owned, self.r.region), "x", "2026-11-15")


if __name__ == "__main__":
    unittest.main()

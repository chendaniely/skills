#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "markdown-it-py>=3.0",
# ]
# ///
"""Pure rendering for claude_chats.py: claude.ai conversation JSON -> vault Markdown.

No file or network I/O. Design: meta/plans/2026-09-28-claude-project-sync-design.md
(revised 2026-10-15: chats outside projects too, a summary on top, formatting kept).

A note is four parts, top to bottom:
  1. frontmatter (the keys in TRANSCRIPT_KEYS are the script's; every other key is kept)
  2. a `## Summary` section, written once by the claude-chats skill, never touched again
  3. the transcript, between the claude-chats markers, regenerated on every sync
  4. Dan's own notes, below the end marker, never touched

Claude's text keeps its Markdown. Only syntax Obsidian would act on is made inert, and
only outside code: wikilinks, embeds, tags, raw HTML, Templater tags and relative links.
Dan's own turns are literal, as claude.ai shows them: line breaks kept as hard breaks,
indentation kept, and nothing read as Markdown, so a pasted `# prompt` or `> continuation`
line stays text. Thinking, tool calls and pasted attachments go in folded callouts. Code
is located with a CommonMark parser, as scripts/lint.py does, so the two agree on what
counts as code.
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from markdown_it import MarkdownIt

TRANSCRIPT_BEGIN = (
    "<!-- claude-chats:begin transcript — regenerated on every sync; "
    "write your notes below the end marker -->"
)
TRANSCRIPT_END = "<!-- claude-chats:end transcript -->"
SUMMARY_HEADING = "## Summary"
SUMMARY_PENDING = (
    "_Not summarized yet. The claude-chats skill writes a summary here after a sync; "
    "once it is written, a re-sync never changes it._"
)
NO_PROJECT = "no-project"
TRANSCRIPT_KEYS = ("Created", "Modification date", "Tags", "Type", "Purpose", "Source",
                   "Project", "Conversation ID", "Title", "Messages", "Updated upstream",
                   "Synced", "Upstream")
VOLATILE = {"Modification date", "Synced"}
# Tool results shown in full. Others (memory, chat search, connectors) can quote other
# chats or third parties, so the note says how many items came back and the raw
# archive keeps them.
INLINE_RESULT_TOOLS = {"web_search", "web_fetch", "artifacts", "repl", "analysis"}

_MD = MarkdownIt("commonmark")
_INLINE_CODE = re.compile(r"(?<!`)(`+)(?!`).+?(?<!`)\1(?!`)")
_TAG = re.compile(r"(?<=\s)#(?=[^\s#])")
_TAG_START = re.compile(r"^#(?=[^\s#])")
_HTML = re.compile(r"(?<!\\)<(?!https?://|mailto:)(?=[A-Za-z!/?])")
_REL_LINK = re.compile(r"(?<!\\)(!?)\[(?=[^\]\n]*\]\((?![A-Za-z][A-Za-z0-9+.-]*:|#|<))")
_UNSAFE_NAME = re.compile(r'[/\\:*?"<>|#^\[\]]')
_KEY = re.compile(r"^([^\s#:\-][^:]*):(?:\s|$)")
_PLAIN_ITEM = re.compile(r"[A-Za-z0-9_/\-]+")
_ARTIFACT_LANG = {
    "text/markdown": "markdown", "text/html": "html", "image/svg+xml": "svg",
    "application/vnd.ant.mermaid": "mermaid", "application/vnd.ant.react": "jsx",
}


class MarkerError(ValueError):
    """The note doesn't have the shape the renderer expects; it is left alone."""


class AlreadySummarized(ValueError):
    """The note already has a summary; replacing it needs force."""


# -- time ---------------------------------------------------------------------------

def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def to_local(value: str, tz: str) -> datetime:
    return parse_ts(value).astimezone(ZoneInfo(tz))


def minute(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")


# -- data hygiene -------------------------------------------------------------------

def sanitize(obj):
    """Replace lone UTF-16 surrogates (a title cut mid-emoji) so the text can be written."""
    if isinstance(obj, str):
        return obj.encode("utf-16", "surrogatepass").decode("utf-16", "replace")
    if isinstance(obj, list):
        return [sanitize(x) for x in obj]
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    return obj


def clean_title(title: str | None) -> str:
    return "".join(ch for ch in (title or "") if unicodedata.category(ch) != "Cc").strip()


# -- branches -----------------------------------------------------------------------

@dataclass
class Branch:
    messages: list[dict]
    other_branches: int
    leaf_missing: bool


def current_branch(conv: dict) -> Branch:
    """The branch claude.ai shows: parent links walked back from the current leaf."""
    msgs = [m for m in conv.get("chat_messages") or [] if isinstance(m, dict) and m.get("uuid")]
    by_id = {m["uuid"]: m for m in msgs}
    parents = {m.get("parent_message_uuid") for m in msgs}
    leaves = [m for m in msgs if m["uuid"] not in parents]
    leaf = conv.get("current_leaf_message_uuid")
    missing = bool(msgs) and leaf not in by_id
    if missing:
        leaf = max(leaves, key=lambda m: parse_ts(m["created_at"]))["uuid"] if leaves else None
    path, seen = [], set()
    while leaf in by_id and leaf not in seen:
        seen.add(leaf)
        path.append(by_id[leaf])
        leaf = by_id[leaf].get("parent_message_uuid")
    path.reverse()
    return Branch(path, max(len(leaves) - 1, 0), missing)


# -- Markdown ------------------------------------------------------------------------

def code_lines(text: str) -> set[int]:
    """0-based line numbers inside fenced or indented code blocks, at any nesting."""
    lines: set[int] = set()
    for tok in _MD.parse(text):
        if tok.type in ("fence", "code_block") and tok.map:
            lines.update(range(*tok.map))
    return lines


def open_fence(text: str) -> str | None:
    """The fence that closes a top-level fence the text leaves open, else None.

    Only top-level fences are closed: a fence inside a list item or quote closes when
    its container ends, and an added fence there would open a new block instead.
    """
    n = len(text.rstrip("\n").split("\n"))
    src = text.split("\n")
    for tok in _MD.parse(text):
        if tok.type != "fence" or tok.level != 0 or not tok.map or tok.map[1] < n:
            continue
        last = src[tok.map[1] - 1].strip()
        closed = (tok.map[1] - 1 > tok.map[0] and len(last) >= len(tok.markup)
                  and set(last) == {tok.markup[0]})
        if not closed:
            return tok.markup
    return None


def _escape_segment(s: str, line_start: bool) -> str:
    s = s.replace("[[", r"\[\[")
    s = _REL_LINK.sub(lambda m: m.group(1) + "\\[", s)
    s = _TAG.sub(r"\\#", s)
    if line_start:
        s = _TAG_START.sub(r"\\#", s)
    s = _HTML.sub(r"\\<", s)
    return s.replace("<%", "<\\%")


def escape_line(line: str) -> str:
    """Make one line of prose inert for Obsidian; inline code spans are left as they are."""
    out, pos = [], 0
    for m in _INLINE_CODE.finditer(line):
        out.append(_escape_segment(line[pos:m.start()], pos == 0))
        out.append(m.group(0))
        pos = m.end()
    out.append(_escape_segment(line[pos:], pos == 0))
    return "".join(out)


NBSP = " "
_LITERAL_CHARS = re.compile(r"[*`$\[]|~~|==|%%|&(?=#?[A-Za-z0-9]+;)|(?<![A-Za-z0-9])_|_(?![A-Za-z0-9])")
_BLOCK_START = re.compile(r"^([#>+|]|[-*](?=\s|$)|=+(?=\s*$)|-+(?=\s*$))")
_ORDERED = re.compile(r"^(\d{1,9})([.)])(?=\s|$)")


def literal_line(line: str) -> str:
    """One line of Dan's text, escaped so Markdown and Obsidian read it as plain text.

    Leading spaces become no-break spaces: they keep the indent visible and stop
    CommonMark from turning an indented line into a code block.
    """
    body = line.lstrip(" \t")
    indent = line[: len(line) - len(body)].replace("\t", "    ").replace(" ", NBSP)
    s = body.replace("\\", "\\\\")
    s = _LITERAL_CHARS.sub(lambda m: "".join("\\" + ch for ch in m.group(0)), s)
    s = _escape_segment(s, True)
    s = _ORDERED.sub(r"\1\\\2", s)
    s = _BLOCK_START.sub(lambda m: "\\" + m.group(1), s)
    return indent + s


def literal_text(text: str) -> str:
    """Dan's turn as claude.ai shows it: every line break kept (a trailing backslash is a
    hard break, which the vault needs since strictLineBreaks is on), nothing as Markdown."""
    lines = text.split("\n")
    out = []
    for i, line in enumerate(lines):
        if not line.strip():
            out.append("")
            continue
        s = literal_line(line)
        if i + 1 < len(lines) and lines[i + 1].strip():
            s += "\\"
        out.append(s)
    return "\n".join(out)


def escape_prose(text: str) -> str:
    """Escape every line outside code, and close a top-level fence the text left open."""
    code = code_lines(text)
    out = [line if i in code else escape_line(line) for i, line in enumerate(text.split("\n"))]
    closer = open_fence(text)
    if closer:
        out.append(closer)
    return "\n".join(out)


def fence(body: str, info: str = "") -> str:
    body = body.rstrip("\n")
    longest = max((len(run) for run in re.findall(r"`+", body)), default=0)
    ticks = "`" * max(3, longest + 1)
    return f"{ticks}{info.replace('`', chr(39)).replace(chr(10), ' ')}\n{body}\n{ticks}"


def callout(kind: str, title: str, body: str, folded: bool = True) -> str:
    head = f"> [!{kind}]{'-' if folded else '+'} {escape_line(title)}".rstrip()
    return "\n".join([head] + [f"> {line}" if line else ">" for line in body.split("\n")])


# -- blocks -------------------------------------------------------------------------

def _link_text(s: str) -> str:
    return s.replace("[", "\\[").replace("]", "\\]").replace("\n", " ")


def _results(result: dict | None) -> list[dict]:
    if result is None:
        return []
    content = result.get("content")
    if isinstance(content, list):
        return [x if isinstance(x, dict) else {"type": "text", "text": str(x)} for x in content]
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    return [] if content is None else [{"type": "json", "value": content}]


def _artifact(data: dict) -> str:
    title = data.get("title") or data.get("id") or "artifact"
    command = data.get("command") or "create"
    content = data.get("content")
    if command in ("create", "rewrite") and isinstance(content, str):
        kind = data.get("type") or ""
        body = (escape_prose(content) if kind == "text/markdown"
                else fence(content, data.get("language") or _ARTIFACT_LANG.get(kind, "")))
        return callout("example", f"Artifact: {title}", body, folded=False)
    if command == "update":
        body = ("Replaced:\n\n" + fence(str(data.get("old_str", "")), "text")
                + "\n\nwith:\n\n" + fence(str(data.get("new_str", "")), "text"))
        return callout("example", f"Artifact edited: {title}", body)
    return callout("example", f"Artifact ({command}): {title}",
                   fence(json.dumps(data, indent=2, ensure_ascii=False), "json"))


_LONG = 400


def _split_long(value, path: str = ""):
    """Swap string leaves longer than _LONG for a marker; return (copy, [(path, text)]).
    Long payloads (a doc being written, a big query) then read as text, not escaped JSON."""
    if isinstance(value, str) and len(value) > _LONG:
        return "(shown below)", [(path or "value", value)]
    if isinstance(value, dict):
        out, found = {}, []
        for k, v in value.items():
            out[k], f = _split_long(v, f"{path}.{k}" if path else str(k))
            found += f
        return out, found
    if isinstance(value, list):
        out, found = [], []
        for i, v in enumerate(value):
            nv, f = _split_long(v, f"{path}[{i}]")
            out.append(nv)
            found += f
        return out, found
    return value, []


def _tool_pair(use: dict | None, result: dict | None) -> str:
    use = use or {}
    name = use.get("name") or (result or {}).get("name") or "tool"
    data = use.get("input")
    data = data if isinstance(data, dict) else ({} if data is None else {"input": data})
    if name == "artifacts":
        return _artifact(data)
    if name in ("web_search", "web_fetch"):
        title = (f"Searched the web: {data.get('query', '')}" if name == "web_search"
                 else f"Fetched: {data.get('url', '')}")
        rows = []
        for item in _results(result):
            url = str(item.get("url") or "")
            text = str(item.get("title") or url or (item.get("text") or "")[:200])
            if url.startswith(("http://", "https://")):
                rows.append(f"- [{_link_text(text)}]({url})")
            elif text:
                rows.append(f"- {escape_line(text)}")
        return callout("info", title, "\n".join(rows) or "_No results._")
    parts = []
    if data:
        shown, long_parts = _split_long(data)
        parts.append(fence(json.dumps(shown, indent=2, ensure_ascii=False), "json"))
        parts += [f"**{path}:**\n\n" + fence(text, "text") for path, text in long_parts]
    if result is not None:
        items = _results(result)
        if name in INLINE_RESULT_TOOLS:
            parts.append(fence("\n".join(str(i.get("text") or json.dumps(i, ensure_ascii=False))
                                         for i in items), "text"))
        else:
            n = len(items)
            parts.append(f"_Result: {n} item{'s' if n != 1 else ''}, kept in the raw archive "
                         "(it may quote other chats)._")
    return callout("example", f"Tool: {name}", "\n\n".join(parts) or "_No input._")


def _citations(block: dict) -> str:
    rows, seen = [], set()
    for c in block.get("citations") or []:
        if not isinstance(c, dict):
            continue
        details = c.get("details") if isinstance(c.get("details"), dict) else {}
        url = str(c.get("url") or details.get("url") or "")
        title = str(c.get("title") or details.get("title") or url)
        if url.startswith(("http://", "https://")) and url not in seen:
            seen.add(url)
            rows.append(f"- [{_link_text(title)}]({url})")
    return callout("quote", "Sources", "\n".join(rows)) if rows else ""


def _block(block: dict, unknown: set[str], literal: bool = False) -> str:
    kind = block.get("type")
    if kind == "text":
        text = block.get("text") or ""
        body = (literal_text(text) if literal else escape_prose(text)) if text.strip() else ""
        parts = [body, _citations(block)]
        return "\n\n".join(p for p in parts if p)
    if kind == "thinking":
        text = block.get("thinking") or ""
        if not text.strip():
            text = "\n\n".join(str(s.get("summary") or "") for s in block.get("summaries") or []
                               if isinstance(s, dict))
        return callout("note", "Claude's thinking", escape_prose(text)) if text.strip() else ""
    if kind == "redacted_thinking":
        return callout("note", "Claude's thinking (redacted)", "_Redacted by the API._")
    unknown.add(str(kind))
    return callout("warning", f"Unrendered block: {kind}",
                   fence(json.dumps(block, indent=2, ensure_ascii=False), "json"))


def _message_files(msg: dict) -> list[dict]:
    files, seen = [], set()
    for f in (msg.get("files") or []) + (msg.get("files_v2") or []):
        key = isinstance(f, dict) and (f.get("file_uuid") or f.get("file_name"))
        if key and key not in seen:
            seen.add(key)
            files.append(f)
    return files


def image_order(conv: dict) -> list[str]:
    """Photo file IDs on the current branch, in order of first appearance. The CLI uses
    this to give each photo a stable vault name (`<chat-id>-NN.<ext>`)."""
    order: list[str] = []
    for m in current_branch(conv).messages:
        ids = [b.get("file_uuid") for b in m.get("content") or [] if isinstance(b, dict) and b.get("type") == "image"]
        ids += [f.get("file_uuid") for f in _message_files(m) if f.get("file_kind") == "image"]
        for i in ids:
            if i and i not in order:
                order.append(i)
    return order


def _photo(fid: str | None, name: str | None, images: dict[str, str]) -> str:
    if fid in images:
        return f"![[{images[fid]}|480]]"
    return escape_line(f"📷 {name or fid or 'image'}, not downloaded")


def render_turn(msg: dict, owner: str, tz: str, unknown: set[str],
                images: dict[str, str] | None = None) -> str:
    images = images or {}
    when = minute(to_local(msg["created_at"], tz))
    mode = "voice" if msg.get("input_mode") == "voice" else "text"
    who = owner if msg.get("sender") == "human" else "Claude"
    parts = [f"### [{when}] **{who}** _({mode})_"]
    for att in msg.get("attachments") or []:
        if isinstance(att, dict):
            size = att.get("file_size")
            title = f"Pasted: {att.get('file_name') or 'text'}" + (
                f" ({size:,} bytes)" if isinstance(size, int) else "")
            parts.append(callout("example", title, fence(att.get("extracted_content") or "", "text")))
    blocks = [b for b in msg.get("content") or [] if isinstance(b, dict)]
    if not blocks and (msg.get("text") or "").strip():
        blocks = [{"type": "text", "text": msg["text"]}]
    files = _message_files(msg)
    names = {f.get("file_uuid"): f.get("file_name") for f in files}
    shown_by_block = {b.get("file_uuid") for b in blocks if b.get("type") == "image"}
    for f in files:  # files no image block shows, in the attachment area, as claude.ai does
        fid = f.get("file_uuid")
        if f.get("file_kind") == "image":
            if fid not in shown_by_block:
                parts.append(_photo(fid, f.get("file_name"), images))
        else:
            kind = f.get("file_kind") or f.get("file_type") or "file"
            parts.append(escape_line(f"📎 {f.get('file_name') or fid or 'file'} ({kind}), not downloaded"))
    # A result goes with its own call, matched by ID. Parallel calls put every call first and
    # the results after, so pairing by position would show one tool's output under another's.
    calls = {b.get("id") for b in blocks if b.get("type") == "tool_use"}
    results: dict = {}
    for b in blocks:
        if b.get("type") == "tool_result" and b.get("tool_use_id"):
            results.setdefault(b["tool_use_id"], b)
    for b in blocks:
        kind = b.get("type")
        if kind == "image":
            parts.append(_photo(b.get("file_uuid"), names.get(b.get("file_uuid")), images))
        elif kind == "tool_use":
            parts.append(_tool_pair(b, results.get(b.get("id"))))
        elif kind == "tool_result":
            if b.get("tool_use_id") not in calls or results.get(b.get("tool_use_id")) is not b:
                parts.append(_tool_pair(None, b))
        else:
            parts.append(_block(b, unknown, literal=msg.get("sender") == "human"))
    return "\n\n".join(p for p in parts if p)


@dataclass
class Rendered:
    region: str
    message_ids: list[str]
    start: datetime | None
    end: datetime | None
    other_branches: int
    leaf_missing: bool
    unknown_blocks: set[str] = field(default_factory=set)


def _provenance(project_stem: str | None, start: datetime | None, end: datetime | None,
                n: int, others: int) -> str:
    where = f"in the project [[{project_stem}]]" if project_stem else "outside any project"
    if start is None or end is None:
        span = "no messages"
    else:
        tail = end.strftime("%H:%M") if end.date() == start.date() else minute(end)
        span = f"{minute(start)}–{tail} {start.tzname()}"
    branches = (f" ({others} other branch{'es' if others != 1 else ''} kept in the raw archive)"
                if others else "")
    return ("> [!info] Verbatim source\n"
            f"> A claude.ai chat {where}, {span}, {n} messages on the current branch{branches}. "
            "Rendered mechanically from the conversation JSON by `scripts/claude_chats.py`: every "
            "message's text is reproduced 1:1, Markdown included; thinking, tool calls and pasted "
            "attachments sit in folded callouts; times are converted from UTC.")


def render_region(conv: dict, project_stem: str | None, owner: str, tz: str,
                  images: dict[str, str] | None = None) -> Rendered:
    branch = current_branch(conv)
    unknown: set[str] = set()
    turns = [render_turn(m, owner, tz, unknown, images) for m in branch.messages]
    start = to_local(branch.messages[0]["created_at"], tz) if branch.messages else None
    end = to_local(branch.messages[-1]["created_at"], tz) if branch.messages else None
    region = "\n\n".join([TRANSCRIPT_BEGIN,
                          _provenance(project_stem, start, end, len(branch.messages), branch.other_branches),
                          *turns, TRANSCRIPT_END])
    return Rendered(region, [m["uuid"] for m in branch.messages], start, end,
                    branch.other_branches, branch.leaf_missing, unknown)


# -- names --------------------------------------------------------------------------

def _ascii_slug(text: str, limit: int = 60) -> str:
    ascii_ = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_.lower()).strip("-")[:limit].rstrip("-")


def slugify(title: str, uuid: str, limit: int = 60) -> str:
    return _ascii_slug(title, limit) or f"chat-{uuid[:8]}"


def note_stem(start: datetime, title: str, uuid: str, taken: set[str]) -> str:
    """`YYYY-MM-DD-HHmm-<slug>`, never a name already in the vault."""
    base = f"{start:%Y-%m-%d-%H%M}-{slugify(title, uuid)}"
    if base not in taken:
        return base
    stem, n = f"{base}-{uuid[:8]}", 2
    while stem in taken:
        stem, n = f"{base}-{uuid[:8]}-{n}", n + 1
    return stem


def folder_slug(name: str, uuid: str, taken: set[str]) -> str:
    slug = _ascii_slug(name) or f"project-{uuid[:8]}"
    return f"{slug}-{uuid[:8]}" if slug in taken or slug == NO_PROJECT else slug


def safe_name(name: str) -> str:
    cleaned = re.sub(r"\s+", " ", _UNSAFE_NAME.sub("-", name or "")).strip().strip(".").strip()
    return cleaned or "untitled-project"


def project_note_stem(name: str) -> str:
    return f"{safe_name(name)} (Claude project)"


# -- frontmatter --------------------------------------------------------------------

def _q(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)  # a JSON string is a valid YAML scalar


def _render_list(items: list[str]) -> str:
    return "[" + ", ".join(i if _PLAIN_ITEM.fullmatch(i) else _q(i) for i in items) + "]"


def _value(v) -> str:
    return _render_list(v) if isinstance(v, list) else v


def transcript_frontmatter(conv: dict, rendered: Rendered, project_stem: str | None,
                           synced: datetime, tz: str, upstream: str | None = None) -> dict:
    """The script's keys, in order. Lists are merged into the note's own (Tags)."""
    created = rendered.start or to_local(conv["created_at"], tz)
    now = synced.astimezone(ZoneInfo(tz))
    owned: dict = {
        "Created": minute(created),
        "Modification date": minute(now),
        "Tags": ["claude_chat"],
        "Type": "dialogue",
        "Purpose": "own-cognition",
        "Source": f"https://claude.ai/chat/{conv['uuid']}",
    }
    if project_stem:
        owned["Project"] = _q(f"[[{project_stem}]]")
    owned.update({
        "Conversation ID": conv["uuid"],
        "Title": _q(clean_title(conv.get("name"))),
        "Messages": str(len(rendered.message_ids)),
        "Updated upstream": minute(to_local(conv["updated_at"], tz)),
        "Synced": minute(now),
    })
    if upstream:
        owned["Upstream"] = upstream
    return owned


def split_note(text: str) -> tuple[list[str] | None, str]:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[4:end].split("\n"), text[end + 5:]
    return None, text


def _blocks(lines: list[str]) -> list[tuple[str | None, list[str]]]:
    blocks: list[tuple[str | None, list[str]]] = []
    for line in lines:
        m = _KEY.match(line)
        if m:
            blocks.append((m.group(1).strip(), [line]))
        elif blocks:
            blocks[-1][1].append(line)
        else:
            blocks.append((None, [line]))
    return blocks


def _parse_list(block: list[str]) -> list[str]:
    first = block[0].split(":", 1)[1].strip()
    if first.startswith("[") and first.endswith("]"):
        return [x.strip().strip("'\"") for x in first[1:-1].split(",") if x.strip()]
    items = [ln.strip()[2:].strip().strip("'\"") for ln in block[1:] if ln.strip().startswith("- ")]
    if first and not first.startswith("#"):
        items.insert(0, first.strip("'\""))
    return items


def frontmatter_values(lines: list[str] | None) -> dict[str, str]:
    """First-line values as written, by key."""
    return {k: b[0].split(":", 1)[1].strip() for k, b in _blocks(lines or []) if k}


def merge_frontmatter(lines: list[str] | None, owned: dict, managed: tuple[str, ...]) -> list[str]:
    """Rewrite owned keys in place (lists merged, never shrunk), drop managed keys no longer
    owned, keep every other line exactly as it was."""
    blocks = _blocks(lines or [])
    present = {k for k, _ in blocks if k}
    out: list[str] = []
    for key, block in blocks:
        if key in owned:
            value = owned[key]
            if isinstance(value, list):
                merged = _parse_list(block)
                merged += [v for v in value if v not in merged]
                out.append(f"{key}: {_render_list(merged)}")
            else:
                out.append(f"{key}: {value}")
        elif key not in managed:
            out.extend(block)
    out += [f"{k}: {_value(v)}" for k, v in owned.items() if k not in present]
    return out


def _same(block: list[str] | None, value) -> bool:
    if block is None:
        return False
    if isinstance(value, list):
        return set(value) <= set(_parse_list(block))
    return block[0].split(":", 1)[1].strip() == value


# -- notes --------------------------------------------------------------------------

def _region_span(body: str, begin: str, end: str) -> tuple[int, int]:
    """Character span of the marked region. Markers count only as whole lines outside code,
    so a chat that quotes them (in code, or escaped in prose) can't move the region."""
    lines = body.split("\n")
    code = code_lines(body)
    prefix = begin.split(" — ")[0]
    begins = [i for i, ln in enumerate(lines) if ln.startswith(prefix) and i not in code]
    if len(begins) != 1:
        raise MarkerError(f"expected one begin marker, found {len(begins)}")
    ends = [i for i, ln in enumerate(lines) if ln.strip() == end and i not in code and i > begins[0]]
    if not ends:
        raise MarkerError("end marker missing")
    offsets = [0]
    for ln in lines:
        offsets.append(offsets[-1] + len(ln) + 1)
    return offsets[begins[0]], offsets[ends[0]] + len(lines[ends[0]])


@dataclass
class NoteResult:
    text: str
    status: str  # "new" | "updated" | "unchanged"


def new_note(owned: dict, region: str) -> str:
    fm = "\n".join(f"{k}: {_value(v)}" for k, v in owned.items())
    return (f"---\n{fm}\nSummary: pending\n---\n\n{SUMMARY_HEADING}\n\n{SUMMARY_PENDING}\n\n"
            f"{region}\n")


PROJECT_BEGIN = "<!-- claude-chats:begin project — regenerated on every sync; write your notes below the end marker -->"
PROJECT_END = "<!-- claude-chats:end project -->"
PROJECT_KEYS = ("Created", "Modification date", "Tags", "Source", "Project ID", "Synced")


def project_frontmatter(pid: str, created: str | None, synced: datetime, tz: str) -> dict:
    now = synced.astimezone(ZoneInfo(tz))
    return {"Created": minute(to_local(created, tz) if created else now), "Modification date": minute(now),
            "Tags": ["claude_project"], "Source": f"https://claude.ai/project/{pid}", "Project ID": pid,
            "Synced": minute(now)}


def project_region(name: str, chat_stems: list[str], description: str = "", instructions: str = "",
                   docs: tuple | list = ()) -> str:
    """The project note's machine-written part: what the project is, its instructions word for
    word, its knowledge docs by name and size (their contents stay in the archive), and its
    mirrored chats, newest first."""
    parts = [PROJECT_BEGIN, f"> [!info] Claude project\n> **{escape_line(name)}**, a project on claude.ai. "
             "The chats from it mirrored into this vault are listed below, newest first."]
    if description.strip():
        parts.append(f"**Description:** {escape_prose(description.strip())}")
    if instructions.strip():
        parts.append("**Instructions**\n\n" + fence(instructions))
    if docs:
        listing = "\n".join(f"- {escape_line(doc)} ({size} characters)" for doc, size in docs)
        parts.append(f"**Knowledge docs** (their contents stay in the archive)\n\n{listing}")
    chats = "\n".join(f"- [[{s}]]" for s in sorted(chat_stems, reverse=True))
    parts += [f"**Chats**\n\n{chats}", PROJECT_END]
    return "\n\n".join(parts)


def new_project_note(owned: dict, region: str) -> str:
    fm = "\n".join(f"{k}: {_value(v)}" for k, v in owned.items())
    return f"---\n{fm}\n---\n\n{region}\n"


def update_note(existing: str, owned: dict, managed: tuple[str, ...], region: str,
                begin: str = TRANSCRIPT_BEGIN, end: str = TRANSCRIPT_END) -> NoteResult:
    lines, body = split_note(existing)
    b, e = _region_span(body, begin, end)
    blocks = {k: blk for k, blk in _blocks(lines or []) if k}
    same = all(_same(blocks.get(k), v) for k, v in owned.items() if k not in VOLATILE)
    stale = any(k in blocks for k in managed if k not in owned)
    if same and not stale and body[b:e] == region:
        return NoteResult(existing, "unchanged")
    fm = "\n".join(merge_frontmatter(lines, owned, managed))
    return NoteResult(f"---\n{fm}\n---\n{body[:b]}{region}{body[e:]}", "updated")


def set_summary(text: str, summary: str, stamp: str, force: bool = False) -> str:
    """Write the summary under `## Summary` and stamp `Summary:`. Never replaces a written
    summary unless forced, since Dan may have edited it."""
    lines, body = split_note(text)
    if lines is None:
        raise MarkerError("note has no frontmatter")
    current = frontmatter_values(lines).get("Summary", "pending")
    if current != "pending" and not force:
        raise AlreadySummarized(f"already summarized ({current}); force to replace it")
    b, _ = _region_span(body, TRANSCRIPT_BEGIN, TRANSCRIPT_END)
    head = body[:b]
    i = head.rfind(SUMMARY_HEADING + "\n")
    if i == -1:
        raise MarkerError("no '## Summary' heading above the transcript")
    fm = "\n".join(merge_frontmatter(lines, {"Summary": stamp}, ("Summary",)))
    return f"---\n{fm}\n---\n{head[:i]}{SUMMARY_HEADING}\n\n{summary.strip()}\n\n{body[b:]}"


def stamp_processed(text: str, stamp: str) -> str:
    """Mark a chat's note as processed, and record which version of the chat that covered, so
    a reply the note didn't hold yet brings it back. Re-renders leave both keys alone."""
    lines, body = split_note(text)
    if lines is None:
        raise MarkerError("note has no frontmatter")
    through = frontmatter_values(lines).get("Updated upstream", "")
    fm = "\n".join(merge_frontmatter(lines, {"Processed": stamp, "Processed through": through},
                                     ("Processed", "Processed through")))
    return f"---\n{fm}\n---\n{body}"


def add_summary_update(text: str, update: str, date: str) -> str:
    """Add a dated `### Update` under a written summary, for a chat that has grown since.
    The summary itself is left exactly as it is, since Dan may have edited it."""
    lines, body = split_note(text)
    if lines is None:
        raise MarkerError("note has no frontmatter")
    current = frontmatter_values(lines).get("Summary", "pending")
    if current == "pending":
        raise MarkerError("no summary yet to add an update to; write the summary first")
    b, _ = _region_span(body, TRANSCRIPT_BEGIN, TRANSCRIPT_END)
    stamp = f"{current.split(';')[0].strip()}; updated {date}"
    fm = "\n".join(merge_frontmatter(lines, {"Summary": stamp}, ("Summary",)))
    head = body[:b].rstrip("\n")
    return f"---\n{fm}\n---\n{head}\n\n### Update {date}\n\n{update.strip()}\n\n{body[b:]}"

#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Leak check for a public repo, copied into each project made with plan-driven-development.

Flags private addresses, per-unit identifiers and privately denylisted terms, in file names as
well as contents. The git hooks run it on every commit (`--staged`, `--message FILE`) and every
push (`--range REVS`, `--tracked`); CI runs it over every tracked file (`--tracked --ci`) and every
commit's patches and messages (`--message FILE --ci`). It fails closed: a missing, empty or
malformed denylist is an error, never a pass, and so is a range git can't read. A binary file
can't be read, so it is named for a person to check. A crash never prints a private name: any
unexpected error prints only its type and exits 2. Ported from chendaniely/local-ai's
`spark leakcheck` (spark/src/spark/leakcheck.py at e32096c).
"""

from __future__ import annotations

import argparse
import codecs
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ALLOW_MARKER = "leakcheck: allow"
DEFAULT_DENYLIST = "~/.config/leakcheck/denylist"
HELP = "see AGENTS.md, Docs and security"

# The IPv4 lookaheads reject a longer dotted string (a version number) but not a sentence-final
# period, so "at <address>." is still caught.
PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "private IPv4 address",
        re.compile(
            r"(?<![\d.])(?:10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d{1,3}\.\d{1,3}(?!\.?\d)"
        ),
    ),
    (
        "tailnet IPv4 address",
        re.compile(r"(?<![\d.])100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}(?!\.?\d)"),
    ),
    ("tailnet IPv6 address", re.compile(r"\bfd7a:115c:a1e0:[0-9a-f:]*[0-9a-f]", re.IGNORECASE)),
    (
        "private or link-local IPv6 address",
        re.compile(r"\b(?:f[cd][0-9a-f]{2}|fe80):[0-9a-f:]*:[0-9a-f]{1,4}\b", re.IGNORECASE),
    ),
    (
        "MAC address",
        re.compile(r"(?<![0-9A-Fa-f:-])(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}(?![0-9A-Fa-f:-])"),
    ),
    ("tailnet hostname", re.compile(r"\b[a-z0-9-]+\.ts\.net\b", re.IGNORECASE)),
    (
        "Synology DDNS or QuickConnect name",
        re.compile(r"\b[a-z0-9-]+\.(?:synology\.me|quickconnect\.to)\b", re.IGNORECASE),
    ),
    ("macOS volume path", re.compile(r"/Volumes/[^\s/`'\"]+")),  # leakcheck: allow
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
)


@dataclass(frozen=True)
class Finding:
    source: str
    line: int
    kind: str
    excerpt: str


class DenylistMissing(RuntimeError):
    pass


class DenylistInvalid(ValueError):
    pass


class RangeUnreadable(RuntimeError):
    pass


def load_denylist(path: Path) -> list[re.Pattern[str]]:
    path = Path(path).expanduser()
    if not path.is_file():
        raise DenylistMissing(f"denylist not found at {path} — ask Dan ({HELP})")
    patterns = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if line and not line.startswith("#"):
            try:
                patterns.append(re.compile(line, re.IGNORECASE))
            except re.error:
                # The line number only: the terms are private, and hook output can land in an
                # agent's context. `from None` keeps re's message, which can quote part of the
                # line, out of any traceback too.
                raise DenylistInvalid(
                    f"denylist line {number} is not a valid regular expression — fix it in "
                    f"{path} (the line itself is not shown)"
                ) from None
    if not patterns:
        # An empty file (what `touch` makes) or comments only would pass every commit.
        raise DenylistInvalid(
            f"denylist has no terms — add the private terms to {path}, one regular expression "
            f"per line ({HELP})"
        )
    return patterns


def _redact(text: str) -> str:
    # A term of 3 characters or fewer would be shown whole, so it is not shown at all.
    return text[:3] + "…" if len(text) > 3 else "…"


def shown_path(path: str, denylist: list[re.Pattern[str]]) -> str:
    """`path` as output may print it: every match of a pattern or a denylisted term cut to 3
    characters, like an excerpt. A private term in a file name must not reach the output whole."""
    spans = sorted(
        m.span()
        for pattern in (*(p for _, p in PATTERNS), *denylist)
        for m in pattern.finditer(path)
        if m.end() > m.start()
    )
    merged: list[list[int]] = []
    for start, end in spans:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    out, pos = [], 0
    for start, end in merged:
        out += [path[pos:start], _redact(path[start:end])]
        pos = end
    return "".join(out) + path[pos:]


def scan_text(source: str, text: str, denylist: list[re.Pattern[str]]) -> list[Finding]:
    findings: list[Finding] = []
    for number, line in enumerate(text.splitlines(), start=1):
        # The allow marker excuses a line from the generic patterns only. A denylisted term is
        # never safe, so the denylist checks every line, marked or not.
        if ALLOW_MARKER not in line:
            for kind, pattern in PATTERNS:
                findings += [
                    Finding(source, number, kind, _redact(m.group(0))) for m in pattern.finditer(line)
                ]
        for pattern in denylist:
            findings += [
                Finding(source, number, "denylisted term", _redact(m.group(0)))
                for m in pattern.finditer(line)
            ]
    return findings


def _git(args: list[str], cwd: Path | None) -> bytes:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True).stdout


# UTF-16 and UTF-32 text is full of NUL bytes, which would mark it as binary, so text that starts
# with a byte-order mark is decoded by it. The UTF-32 marks go first: UTF-32-LE's begins with
# UTF-16-LE's.
_BOMS = (
    (codecs.BOM_UTF32_LE, "utf-32"),
    (codecs.BOM_UTF32_BE, "utf-32"),
    (codecs.BOM_UTF16_LE, "utf-16"),
    (codecs.BOM_UTF16_BE, "utf-16"),
)


def _text(blob: bytes) -> str:
    for bom, codec in _BOMS:
        if blob.startswith(bom):
            return blob.decode(codec, errors="replace")
    return blob.decode("utf-8", errors="replace")


def _decode(blob: bytes) -> str | None:
    """A file's text, or None for a binary file: a NUL byte and no byte-order mark."""
    if b"\0" in blob and not blob.startswith(tuple(bom for bom, _ in _BOMS)):
        return None
    return _text(blob)


def _texts(entries: list[tuple[bytes, bytes]], cwd: Path | None) -> list[tuple[str, str | None]]:
    """(name, text) for each (name, blob id), read from git's object store; the text is None for a
    binary file. A name is only displayed, so an undecodable byte is replaced, not an error."""
    return [
        (name.decode(errors="replace"), _decode(_git(["cat-file", "blob", blob.decode()], cwd)))
        for name, blob in entries
    ]


def staged_texts(cwd: Path | None = None) -> list[tuple[str, str | None]]:
    # Every staged change but a deletion: added, copied, modified and type-changed (a symlink
    # turned into a file, or a file into a symlink, whose blob is its target path). A rename shows
    # as a deletion and an addition. Blobs are read by id, never by name: `git show :0:notes.md`
    # means stage 0 of `notes.md`. A submodule (mode 160000) has no blob to read.
    raw = _git(
        ["diff", "--cached", "--raw", "-z", "--no-abbrev", "--no-renames", "--diff-filter=ACMT"], cwd
    ).split(b"\0")
    entries = []
    for meta, name in zip(raw[0::2], raw[1::2]):
        _, new_mode, _, new_id, _ = meta.lstrip(b":").split(b" ")
        if new_mode != b"160000":
            entries.append((name, new_id))
    return _texts(entries, cwd)


def tracked_texts(cwd: Path | None = None) -> list[tuple[str, str | None]]:
    # From the index, not the working tree: a dangling or directory symlink, a submodule or a file
    # deleted from disk can't crash it, a symlink's blob (its target path) is scanned, and `:/`
    # makes a run from a subfolder cover the whole repository.
    raw = _git(["ls-files", "--stage", "-z", "--full-name", "--", ":/"], cwd).split(b"\0")
    entries = []
    for record in raw:
        if record:
            meta, _, name = record.partition(b"\t")
            mode, blob, _ = meta.split(b" ")
            if mode != b"160000":
                entries.append((name, blob))
    return _texts(entries, cwd)


_RANGE_FLAGS = frozenset({"--not", "--remotes", "--all"})
_REMOTES_NAME = re.compile(r"--remotes=[A-Za-z0-9._/-]+")  # one named remote; no glob characters


def _range_log(options: list[str], revs: str, cwd: Path | None) -> bytes:
    """`git log` over `revs`. Callers pass `A..B` or `<sha> --not --remotes[=<name>]`, so any other token
    that starts with `-` is refused before git runs (`--output=FILE` writes a file, `--max-count=0`
    scans nothing). The message never holds the range: a ref name can be private."""
    try:
        tokens = shlex.split(revs)
        if any(t.startswith("-") and t not in _RANGE_FLAGS and not _REMOTES_NAME.fullmatch(t) for t in tokens):
            raise ValueError
        # core.quotePath=false keeps a non-ASCII file name readable in the patch headers.
        return _git(["-c", "core.quotePath=false", "log", *options, *tokens, "--"], cwd)
    except (ValueError, subprocess.CalledProcessError):
        raise RangeUnreadable("git can't read the range, so what is going out is unknown") from None


def range_text(revs: str, cwd: Path | None = None) -> str:
    """Every commit's patch (with a merge's conflict resolutions), author, committer and whole
    message in `revs`,
    for example `abc123..def456` or `def456 --not --remotes`. A range git can't read (a missing
    base, a bad ref, an option) raises RangeUnreadable: the caller can't tell what is going out."""
    return _text(_range_log(["-p", "--cc", "--format=%H%n%an%n%ae%n%cn%n%ce%n%B"], revs, cwd))


def range_binaries(revs: str, cwd: Path | None = None) -> list[str]:
    """The files in `revs` whose changes git shows as binary (`-` in --numstat): their content
    can't be scanned, so they are named for a person to check. Renames are off, so a renamed and
    changed binary is named, and -m shows a merge's own changes, which are otherwise skipped."""
    out = _range_log(["--format=", "--numstat", "--no-renames", "-m", "-z"], revs, cwd)
    names: list[str] = []
    for record in out.split(b"\0"):
        fields = record.lstrip(b"\n").split(b"\t")
        if len(fields) == 3 and fields[0] == b"-" and fields[1] == b"-" and fields[2]:
            name = fields[2].decode(errors="replace")
            if name not in names:
                names.append(name)
    return names


def scan_files(files: list[tuple[str, str | None]], denylist: list[re.Pattern[str]]) -> list[Finding]:
    """Scan each file's name, then its text. A binary file's content can't be scanned, so it is
    named on stderr for a person to check; that alone never changes the exit code."""
    findings: list[Finding] = []
    for name, text in files:
        shown = shown_path(name, denylist)
        findings += scan_text(f"{shown} (file name)", name, denylist)
        if text is None:
            print(f"leakcheck: not scanned (binary): {shown} — check it by eye", file=sys.stderr)
        else:
            findings += scan_text(shown, text, denylist)
    return findings


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="leakcheck", description="scan for private addresses, identifiers and denylisted terms"
    )
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--staged", action="store_true", help="scan staged files (pre-commit hook)")
    mode.add_argument(
        "--message",
        type=Path,
        help="scan a text file: a commit message (commit-msg hook), or CI's log of every commit",
    )
    mode.add_argument(
        "--range",
        metavar="REVS",
        help="scan every commit's patch and message in a git range (pre-push hook)",
    )
    mode.add_argument("--tracked", action="store_true", help="scan every tracked file (pre-push, CI)")
    p.add_argument(
        "--denylist",
        type=Path,
        default=Path(os.environ.get("LEAKCHECK_DENYLIST", DEFAULT_DENYLIST)),
        help="private file of regexes, one per line (default: $LEAKCHECK_DENYLIST, else %(default)s)",
    )
    p.add_argument("--ci", action="store_true", help="skip the private denylist — only in CI")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.ci and os.environ.get("CI") != "true":
        print("leakcheck: --ci is allowed only in CI (CI=true)", file=sys.stderr)
        return 2
    try:
        denylist = [] if args.ci else load_denylist(args.denylist)
        if args.message:
            # Decoded leniently: CI feeds whole patches through here, and one stray byte in a
            # patch must not crash the scan.
            findings = scan_text("commit message", _text(args.message.read_bytes()), denylist)
        elif args.range is not None:
            findings = scan_text("outgoing commits", range_text(args.range), denylist)
            for name in range_binaries(args.range):
                print(f"leakcheck: not scanned (binary): {shown_path(name, denylist)} — check it by eye",
                      file=sys.stderr)
        else:
            findings = scan_files(staged_texts() if args.staged else tracked_texts(), denylist)
    except (DenylistMissing, DenylistInvalid, RangeUnreadable) as err:
        print(f"leakcheck: {err}", file=sys.stderr)
        return 2
    except Exception as err:
        # Only the type: the text of an error can hold a private file name, and this output can
        # land in an agent's context.
        print(
            f"leakcheck: unexpected {type(err).__name__} — nothing was fully scanned. An agent must "
            f"stop and tell Dan.",
            file=sys.stderr,
        )
        return 2
    for f in findings:
        print(f"leakcheck: {f.source}:{f.line}: {f.kind} ({f.excerpt})", file=sys.stderr)
    if findings:
        print(
            f"leakcheck: {len(findings)} finding(s) — refused. An agent must stop and tell Dan the "
            f"kind and file:line (never the matched text); a leak is a stop that never relaxes. An "
            f"allow marker ('{ALLOW_MARKER}') is Dan's to add, never an agent's, and never "
            f"excuses a denylisted term.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

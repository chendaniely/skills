#!/usr/bin/env python3
"""Turn class recordings into session folders and generate notes from them.

Subcommands:

  fetch     A Plaud share link -> <session folder>/plaud.md, transcript-plaud.md and
            notes-plaud.md. Needs the Plaud CLI (`npm install -g @plaud-ai/cli`, then
            `plaud login`).
  generate  Run the course prompt(s) over each session's transcript, plus any command
            logs, with one or more models. Writes notes-class-<variant>--<model>.md.
            Needs the Claude Code CLI for Claude models.
  payload   Print the exact message `generate` would send, so you can take a session to
            any other tool or model.

Run it from inside a course repository -- the one holding prompt-notes.md -- or pass
--repo. Standard library only; Python 3.9+.

  python3 class_notes.py fetch https://web.plaud.ai/s/pub_... [--suffix lab]
  python3 class_notes.py generate                      # sessions with no notes yet
  python3 class_notes.py generate --force              # rebuild after a prompt edit
  python3 class_notes.py generate --only section_02/2026-09-01 --prompt all --model sonnet
  python3 class_notes.py payload --only section_02/2026-09-01 > message.txt

`<command> --help` lists every option.
"""

import argparse
import datetime
import difflib
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

PROMPT_MAIN = "prompt-notes.md"
TRANSCRIPT_NAME = "transcript-plaud.md"
LINK_NAME = "plaud.md"
PLAUD_NOTES_NAME = "notes-plaud.md"
# Earlier folders sometimes saved Plaud's note under this name; only read, never written.
PLAUD_NOTES_OLD_NAMES = ("summary-plaud.md",)

# An alias, not a version. `opus` means "latest Opus", which changes over time -- which is
# exactly why each file is named, and its footer stamped, with the model the run actually
# resolved to, not this string.
DEFAULT_MODEL = "opus"
CLAUDE_ALIASES = {"opus", "sonnet", "haiku", "fable"}

SESSION_DIR = re.compile(r"^\d{4}-\d{2}-\d{2}(?:-.+)?$")

AGENT_SYSTEM_PROMPT = (
    "You are a careful note-taker for a university course. You transform a lecture "
    "transcript, and any command logs sent with it, into a Markdown study document, "
    "following the instructions in the message you are given. You have no tools, no "
    "filesystem, and no repository to inspect: work only from the text in the message. "
    "Never emit or describe a tool call. Reply with the finished Markdown document and "
    "nothing else."
)


class Fail(Exception):
    """An error to report as one line and exit on, without a traceback."""


class BackendNotReady(Fail):
    """A model family whose backend has not been built yet."""


def say(msg=""):
    print(msg, flush=True)


def warn(msg):
    print("warning: " + msg, file=sys.stderr, flush=True)


def tail(text, lines=6):
    return "\n".join(text.strip().splitlines()[-lines:])


def rel(path, root):
    try:
        return str(Path(path).resolve().relative_to(root))
    except ValueError:
        return str(path)


def slug(text):
    """Lower-case letters, digits and single hyphens: safe inside a filename part."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def model_slug(model):
    # Keeps dots and case: `claude-opus-5`, `gemma4:26b` -> `gemma4-26b`.
    return re.sub(r"[^A-Za-z0-9._-]+", "-", model).strip("-")


def write_atomic(path, text):
    """Write via a temp file in the same folder, so an interrupted run leaves no partial
    file -- and no temp file -- behind in the repository."""
    tmp = path.with_name(".%s.tmp-%d" % (path.name, os.getpid()))
    try:
        with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def repo_root(arg):
    if arg:
        root = Path(arg).expanduser().resolve()
        if not root.is_dir():
            raise Fail("--repo is not a directory: %s" % arg)
        return root
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True,
                             text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        raise Fail("not inside a git repository: run this from the course repo, or pass --repo")
    return Path(out).resolve()


def git(root, *args):
    proc = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip()


# --------------------------------------------------------------------------- prompts


class Prompt:
    """One prompt file, and the part of it that is actually sent to the model."""

    def __init__(self, path, variant, root):
        self.path = Path(path).resolve()
        self.variant = variant
        self.root = root
        self.rel = rel(self.path, root)
        self.body = prompt_body(self.path.read_text(encoding="utf-8"))
        # The staleness check keys on the text actually sent, not the commit: a commit that
        # leaves the words alone (a rename, a revert, whitespace at the ends) doesn't make
        # every session look stale.
        self.hash = hashlib.sha256(self.body.encode("utf-8")).hexdigest()[:12]
        self.version = self._version()

    def _version(self):
        # Identify the revision these notes came from. Uncommitted edits are marked -dirty
        # so mid-edit output is never mistaken for a committed state.
        try:
            self.path.relative_to(self.root)
        except ValueError:
            return "outside-repo"
        code, sha = git(self.root, "log", "-1", "--format=%h", "--", self.rel)
        if code != 0 or not sha:
            return "uncommitted"
        dirty = (git(self.root, "diff", "--quiet", "--", self.rel)[0] != 0
                 or git(self.root, "diff", "--cached", "--quiet", "--", self.rel)[0] != 0)
        return sha + ("-dirty" if dirty else "")


def prompt_body(text):
    """A prompt file is the prompt and nothing else: all of it is sent. How it works and
    how to change it lives in README-prompt.md, so a student opening the prompt sees only
    the words the model sees."""
    return text.strip("\n") + "\n"


def discover_prompts(root):
    found = {}
    main = root / PROMPT_MAIN
    if main.is_file():
        found["main"] = main
    for path in sorted(root.glob("prompt-notes-*.md")):
        variant = slug(path.stem[len("prompt-notes-"):])
        if not variant or variant == "main":
            warn("ignoring %s: its variant name is empty or 'main', which is reserved for %s"
                 % (path.name, PROMPT_MAIN))
            continue
        if variant in found:
            warn("ignoring %s: variant '%s' is already taken by %s"
                 % (path.name, variant, found[variant].name))
            continue
        found[variant] = path
    return found


def select_prompts(root, names, prompt_file, variant):
    available = discover_prompts(root)
    chosen = []
    if prompt_file:
        path = Path(prompt_file).expanduser()
        if not path.is_file():
            raise Fail("prompt file not found: %s" % prompt_file)
        name = variant or path.stem
        if not variant and name.startswith("prompt-notes-"):
            name = name[len("prompt-notes-"):]
        name = slug(name)
        if not name or name == "main":
            raise Fail("pass --variant NAME for %s: 'main' is reserved for the course's own %s"
                       % (path.name, PROMPT_MAIN))
        chosen.append(Prompt(path, name, root))
    if names or not prompt_file:
        wanted = names or ["main"]
        if "all" in wanted:
            wanted = list(available)
        for name in wanted:
            if name not in available:
                raise Fail("no prompt '%s' in %s (have: %s)"
                           % (name, root, ", ".join(available) or "none -- is this a course repo?"))
            if name not in [p.variant for p in chosen]:
                chosen.append(Prompt(available[name], name, root))
    return chosen


# --------------------------------------------------------------------------- sessions


def walk_dirs(root, max_depth):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        if len(Path(dirpath).relative_to(root).parts) >= max_depth:
            dirnames[:] = []
        yield Path(dirpath), dirnames, filenames


def discover_sessions(root, only):
    if only:
        sessions = []
        for item in only:
            path = Path(item).expanduser()
            # Accept a path relative to where you're standing or to the repo, and either
            # the folder or its transcript.
            candidates = [path] if path.is_absolute() else [Path.cwd() / path, root / path]
            for cand in candidates:
                if cand.is_file() and cand.name == TRANSCRIPT_NAME:
                    cand = cand.parent
                if cand.is_dir():
                    sessions.append(cand.resolve())
                    break
            else:
                raise Fail("no session folder at: %s" % item)
        return sessions
    return sorted(d for d, _, files in walk_dirs(root, 6) if TRANSCRIPT_NAME in files)


def first_file(folder, names=(), patterns=()):
    """The first non-empty file among exact names, then glob patterns."""
    for name in names:
        path = folder / name
        if path.is_file() and path.stat().st_size:
            return path
    for pattern in patterns:
        for path in sorted(folder.glob(pattern)):
            if path.is_file() and path.stat().st_size and path.name not in names:
                return path
    return None


class Session:
    def __init__(self, folder, root):
        self.folder = folder
        self.rel = rel(folder, root)
        self.transcript = folder / TRANSCRIPT_NAME
        # Both logs are optional. Labs rarely have either, and a folder may gain one days
        # after its transcript. The shell history is history.txt; an R course keeps
        # history.R. A terminal capture is terminal.txt, or an R console capture.
        self.history = first_file(folder, ("history.txt", "history.R"), ("history.*",))
        self.terminal = first_file(folder, ("terminal.txt",), ("*console*.txt",))
        names = [TRANSCRIPT_NAME] + [p.name for p in (self.history, self.terminal) if p]
        # `inputs` goes into the footer so a set of notes says what it was built from;
        # `marks` just makes the run's own output readable.
        self.inputs = ", ".join(names)
        self.marks = "".join(
            " +" + label for label, p in (("history", self.history), ("terminal", self.terminal)) if p)

    @property
    def ready(self):
        return self.transcript.is_file() and self.transcript.stat().st_size > 0


# Shell histories arrive in more than one shape:
#
#   : 1789052889:0;git status    zsh extended history: epoch, elapsed seconds, command
#     3430  cd class             numbered output of `history`
#   git status                   a plain list, pasted in by hand
#
# Normalise all three to "HH:MM:SS  command", or the bare command where there is no
# timestamp, so the prompt only ever sees one format. The wall-clock time is worth keeping:
# the transcript is stamped in time elapsed since the recording started, so an absolute
# time is what lets a command be lined up with the moment it was explained.
ZSH_LINE = re.compile(r"^: (\d+):\d+;(.*)$")
NUMBERED_LINE = re.compile(r"^\s*\d+\s+(\S.*)$")


def normalize_history(text):
    out = []
    for line in text.splitlines():
        if not line.strip():
            continue
        zsh = ZSH_LINE.match(line)
        if zsh:
            when = datetime.datetime.fromtimestamp(int(zsh.group(1)))
            out.append("%s  %s" % (when.strftime("%H:%M:%S"), zsh.group(2)))
            continue
        numbered = NUMBERED_LINE.match(line)
        if numbered:
            out.append(numbered.group(1))
            continue
        # Anything else -- a hand-annotated log, a comment, the continuation line of a
        # multi-line zsh entry -- passes through untouched.
        out.append(line)
    return "".join(line + "\n" for line in out)


def read_text(path):
    return path.read_text(encoding="utf-8", errors="replace")


def build_message(prompt, session):
    """Prompt, then transcript, then whichever logs exist, as one message. A tag is only
    opened when there is something to put in it, so the model is never handed an empty
    <command-history> and left to reason about its absence."""
    parts = [prompt.body, "\n\n<transcript>\n", read_text(session.transcript), "\n</transcript>\n"]
    if session.history:
        raw = read_text(session.history)
        # Only a shell history gets normalised: the numbered-line rule would eat the
        # leading number of R code such as `1 + 1`.
        body = normalize_history(raw) if session.history.name == "history.txt" else raw
        if not body.endswith("\n"):
            body += "\n"
        parts += ["\n<command-history>\n", body, "</command-history>\n"]
    if session.terminal:
        parts += ["\n<terminal-session>\n", read_text(session.terminal), "\n</terminal-session>\n"]
    return "".join(parts)


# --------------------------------------------------------------------------- backends


def backend_for(model):
    m = model.lower()
    return "claude" if m in CLAUDE_ALIASES or m.startswith("claude-") else "local"


def run_claude(message, model):
    """One `claude -p` call. Returns (document, resolved model, stop reason).

    The flags matter. By default `claude -p` runs the full Claude Code *agent*: it loads
    CLAUDE.md, the working directory and git status, and a system prompt telling it to go
    explore the repository. Pointed at a transcript it does exactly that -- in testing it
    emitted a fabricated tool call and invented the output -- instead of writing notes.

      --system-prompt      replaces the agent identity with a plain text-transformer one
      --tools ""           removes Bash/Read/Edit entirely
      --strict-mcp-config  skips MCP servers
      --setting-sources "" ignores user/project/local settings, so CLAUDE.md and hooks
                           cannot leak in and every student gets the same behaviour
      --output-format json wraps the reply in metadata: which model actually ran, and
                           whether the reply was cut off
    """
    exe = shutil.which("claude")
    if not exe:
        raise Fail("the 'claude' CLI is not on your PATH (https://claude.com/claude-code)")
    # Use the Claude subscription, never a metered API key, a cloud provider, or a proxy
    # that could put another model behind a Claude name. If any of these are exported in
    # the surrounding shell, `claude` would silently use them instead.
    env = {k: v for k, v in os.environ.items()
           if not k.startswith("ANTHROPIC_")
           and k not in ("CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX")}
    cmd = [exe, "-p", "--system-prompt", AGENT_SYSTEM_PROMPT, "--model", model,
           "--tools", "", "--strict-mcp-config", "--setting-sources", "",
           "--output-format", "json"]
    proc = subprocess.run(cmd, input=message, capture_output=True, text=True,
                          encoding="utf-8", env=env)
    if proc.returncode != 0:
        raise Fail("claude exited with %d: %s" % (proc.returncode, tail(proc.stderr or proc.stdout)))
    try:
        data = json.loads(proc.stdout)
    except ValueError as exc:
        raise Fail("could not read claude's output as JSON: %s" % exc)
    if data.get("is_error") or data.get("subtype") != "success":
        raise Fail("claude reported an error: %s" % (data.get("result") or data.get("subtype") or "unknown"))
    body = (data.get("result") or "").strip()
    if not body:
        raise Fail("claude returned an empty document")
    # modelUsage is keyed by model, e.g. "claude-opus-5". Claude Code also bills a small
    # helper model (Haiku) for internal housekeeping on every run, so the key set alone is
    # misleading -- the model that wrote the document is the one that produced the output.
    usage = data.get("modelUsage") or {}
    resolved = max(usage, key=lambda m: usage[m].get("outputTokens", 0)) if usage else "unknown"
    stop = data.get("stop_reason") or ""
    # A document cut off at the output limit is unusable, and worse if it looks complete.
    if stop == "max_tokens":
        raise Fail("hit the output limit and was cut off; the transcript may be too long for one pass")
    return body, resolved, stop


def run_local(message, model):
    """Placeholder for local models -- the DGX Spark, reached over Tailscale through
    LiteLLM. Not built yet, because none of that is set up to test against.

    The real version must:
      - size the context window to the input. Ollama's default context silently truncates
        a 60 KB transcript and nothing in the reply says so: compare the prompt tokens the
        server reports with the size of the input, and fail when they don't match;
      - fail when the reply stops at the output limit (the local max_tokens);
      - return the model that actually answered, with its digest, for the filename and
        footer -- local tags move just as `opus` does;
      - never inherit the Claude environment (ANTHROPIC_*), and never fall back to Claude.
    """
    raise BackendNotReady(
        "local backend not set up yet (DGX Spark via Tailscale + LiteLLM pending); "
        "use a Claude model, or `payload` to take the message to another tool")


BACKENDS = {"claude": run_claude, "local": run_local}


# --------------------------------------------------------------------------- generate

FOOTER_PATTERNS = {
    "prompt": re.compile(r"^prompt: (.+) @ (\S+)$", re.M),
    "hash": re.compile(r"^prompt-hash: (\w+)$", re.M),
    "model": re.compile(r"^model: (\S+) \(requested: (.+)\)$", re.M),
    "inputs": re.compile(r"^inputs: (.*)$", re.M),
}


def read_footer(path):
    """The provenance footer of a notes file; fields absent from older files are None."""
    text = read_text(path)
    footer = text.rsplit("\n---\n", 1)[-1]
    found = {}
    for key, pattern in FOOTER_PATTERNS.items():
        matches = pattern.findall(footer)
        found[key] = matches[-1] if matches else None
    model = found["model"]
    return {
        "hash": found["hash"],
        "resolved": model[0] if model else None,
        "requested": model[1] if model else None,
        "inputs": found["inputs"],
    }


def output_name(variant, model):
    return "notes-class-%s--%s.md" % (variant, model_slug(model))


def check_existing(session, prompt, model):
    """(up-to-date file, reason it is stale) for this prompt x model; (None, None) if the
    session has no notes from it yet."""
    stale_reason = None
    for path in sorted(session.folder.glob("notes-class-%s--*.md" % prompt.variant)):
        footer = read_footer(path)
        if footer["requested"] != model:
            continue
        if footer["hash"] == prompt.hash and footer["inputs"] == session.inputs:
            return path, None
        if footer["hash"] != prompt.hash:
            stale_reason = "%s is from an older prompt" % path.name if footer["hash"] else \
                "%s predates prompt hashes" % path.name
        else:
            # A log dropped into the folder after the notes were made. The prompt itself has
            # not changed, so nothing else would notice.
            stale_reason = "%s was built from %s" % (path.name, footer["inputs"] or "the transcript alone")
    return None, stale_reason


def generate_one(session, prompt, model, args, today, counts):
    label = "%s [%s x %s]%s" % (session.rel, prompt.variant, model, session.marks)
    # A session folder often exists before its recording has been fetched. That is a
    # "not ready yet", not a failure -- sending an empty transcript would just invent notes.
    if not session.ready:
        say("  skip      %s (no transcript yet)" % label)
        counts["skipped"] += 1
        return
    backend = backend_for(model)
    # Default: if notes already exist, leave them alone -- so adding one lecture only
    # generates that lecture. --force regenerates, which is what you want after editing
    # the prompt. Stale notes are reported rather than silently rebuilt.
    if not args.force:
        current, stale = check_existing(session, prompt, model)
        if current:
            say("  skip      %s (%s exists)" % (label, current.name))
            counts["skipped"] += 1
            return
        if stale:
            say("  skip      %s (stale: %s)" % (label, stale))
            counts["skipped"] += 1
            counts["stale"] += 1
            return
    if args.dry_run:
        # A Claude alias only resolves to a model name when it runs.
        target = output_name(prompt.variant, model) if backend == "local" else \
            "notes-class-%s--<%s, as resolved>.md" % (prompt.variant, model)
        say("  would run %s -> %s" % (label, target))
        counts["planned"] += 1
        return
    say("  generate  %s ... " % label)
    try:
        body, resolved, _stop = BACKENDS[backend](build_message(prompt, session), model)
    except Fail as exc:
        say("            FAILED: %s" % exc)
        counts["failed"] += 1
        return
    out = session.folder / output_name(prompt.variant, resolved)
    footer = "".join([
        "\n---\n",
        "prompt: %s @ %s\n" % (prompt.rel, prompt.version),
        "prompt-hash: %s\n" % prompt.hash,
        "model: %s (requested: %s)\n" % (resolved, model),
        "backend: %s\n" % backend,
        "inputs: %s\n" % session.inputs,
        "generated: %s\n" % today,
    ])
    document = body + "\n" + footer
    write_atomic(out, document)
    say("            ok -> %s (%d lines, %s)" % (out.name, document.count("\n"), resolved))
    counts["generated"] += 1


def cmd_generate(args):
    root = repo_root(args.repo)
    prompts = select_prompts(root, args.prompt, args.prompt_file, args.variant)
    sessions = [Session(f, root) for f in discover_sessions(root, args.only)]
    models = args.model or [DEFAULT_MODEL]
    if not sessions:
        raise Fail("no %s files found under %s" % (TRANSCRIPT_NAME, root))
    today = datetime.date.today().isoformat()

    for prompt in prompts:
        say("prompt:   %s @ %s (variant %s, hash %s)" % (prompt.rel, prompt.version, prompt.variant, prompt.hash))
        if prompt.version.endswith("-dirty") or prompt.version == "uncommitted":
            say("          uncommitted changes: notes will be stamped \"%s\"" % prompt.version)
    say("models:   %s (aliases; the exact version goes in each filename)" % ", ".join(models))
    say("sessions: %d\n" % len(sessions))

    counts = dict(generated=0, planned=0, skipped=0, failed=0, stale=0)
    for session in sessions:
        for prompt in prompts:
            for model in models:
                generate_one(session, prompt, model, args, today, counts)

    if args.dry_run:
        say("\ndry run: %(planned)d would run, %(skipped)d skipped" % counts)
    else:
        say("\ndone: %(generated)d generated, %(skipped)d skipped, %(failed)d failed" % counts)
    if counts["stale"]:
        say("\n%d stale: notes exist from an older prompt, or from fewer inputs than the folder "
            "now holds.\nRun with --force (optionally --only <folder>) to rebuild them; notes "
            "from other models are kept." % counts["stale"])
    return 1 if counts["failed"] else 0


def cmd_payload(args):
    root = repo_root(args.repo)
    prompts = select_prompts(root, [args.prompt] if args.prompt else [], args.prompt_file, args.variant)
    sessions = discover_sessions(root, [args.only])
    session = Session(sessions[0], root)
    if not session.ready:
        raise Fail("%s has no %s yet" % (session.rel, TRANSCRIPT_NAME))
    sys.stdout.write(build_message(prompts[0], session))
    return 0


# --------------------------------------------------------------------------- fetch

PLAUD_ID = re.compile(r"\b[a-z]+_[0-9a-f]{32}\b")
# `plaud transcript` prints one utterance per line: `[74:42 - 75:07] Speaker 2: text`.
# Minutes run past 59; an hour field is accepted too, in case a later CLI adds one.
UTTERANCE = re.compile(r"^\[(\d+(?::\d+)+) - [\d:]+\] (.+?): (.*)$")
SHARE_URL = re.compile(r"^https://web\.plaud\.ai/s/\S+$")


def plaud(*args):
    exe = shutil.which("plaud")
    if not exe:
        raise Fail("the Plaud CLI is not on your PATH: npm install -g @plaud-ai/cli, then plaud login")
    try:
        proc = subprocess.run([exe, *args], capture_output=True, text=True, encoding="utf-8", timeout=300)
    except subprocess.TimeoutExpired:
        raise Fail("plaud %s timed out" % args[0])
    output = proc.stdout + proc.stderr
    if proc.returncode != 0 or re.search(r"not (logged in|authenticated)|please (log ?in|login)", output, re.I):
        if re.search(r"log ?in|authenticat|401", output, re.I):
            raise Fail("the Plaud CLI is not logged in: run `plaud login`")
        raise Fail("plaud %s failed: %s" % (args[0], tail(output)))
    return proc.stdout


def share_title(url):
    """The recording's name, from the share page's <title>. Plaud's CLI can't look a share
    link up directly, but the page names the recording, and names are what `plaud search`
    matches on."""
    req = urllib.request.Request(url, headers={"User-Agent": "class-notes/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            page = resp.read().decode("utf-8", "replace")
    except OSError as exc:
        raise Fail("could not open the share link: %s" % exc)
    title = ""
    for pattern in (r'<meta[^>]+property="og:title"[^>]+content="([^"]*)"', r"<title[^>]*>(.*?)</title>"):
        m = re.search(pattern, page, re.S | re.I)
        if m and html.unescape(m.group(1)).strip():
            title = html.unescape(m.group(1)).strip()
            break
    if not title or title.lower() in ("plaud", "plaud web", "plaud.ai"):
        raise Fail("the share page doesn't name a recording -- is the link still shared?")
    return title


def plaud_file(file_id):
    info = {}
    for line in plaud("file", file_id).splitlines():
        m = re.match(r"^\s+([a-z_]+):\s+(.*?)\s*$", line)
        if m:
            info[m.group(1)] = m.group(2)
    if info.get("id") != file_id:
        raise Fail("unexpected output from `plaud file %s` (has the CLI's format changed?)" % file_id)
    return info


def same_name(a, b):
    return " ".join(a.split()).casefold() == " ".join(b.split()).casefold()


def resolve_recording(url):
    """Share link -> the one recording it points to. Never guesses: the account also holds
    recordings that are not classes, so anything but exactly one match stops here."""
    title = share_title(url)
    ids = sorted(set(PLAUD_ID.findall(plaud("search", "--", title))))
    candidates = [plaud_file(i) for i in ids]
    matches = [c for c in candidates if same_name(c.get("name", ""), title)]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise Fail("no recording named %r (plaud search only scans the 500 most recent)" % title)
    listing = "; ".join("%s (%s, %s)" % (c["id"], c.get("start_at", "?"), c.get("duration", "?")) for c in matches)
    raise Fail("%d recordings are named %r: %s -- rename one in Plaud, or pass --file-id"
               % (len(matches), title, listing))


def local_start(info):
    raw = info.get("start_at") or info.get("created_at")
    if not raw:
        raise Fail("Plaud gave no start time for %s" % info.get("id"))
    when = datetime.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if when.tzinfo is None:
        # The CLI prints UTC without saying so: an 08:05 lecture in Vancouver is 15:05.
        when = when.replace(tzinfo=datetime.timezone.utc)
    return when.astimezone()


def fetch_transcript(file_id):
    """Plaud's polished (AI-cleaned) transcript, in the same shape as the web export the
    earlier folders used: `HH:MM:SS Speaker` on one line, the text on the next, a blank
    line between utterances."""
    blocks, started = [], False
    for line in plaud("transcript", "--polished", file_id).splitlines():
        m = UTTERANCE.match(line)
        if m:
            started = True
            secs = 0
            for part in m.group(1).split(":"):
                secs = secs * 60 + int(part)
            blocks.append("%02d:%02d:%02d %s\n%s\n"
                          % (secs // 3600, secs % 3600 // 60, secs % 60, m.group(2), m.group(3)))
        elif started and line.strip():
            # Never alter the transcript silently: an unrecognised line means the CLI's
            # format has changed, and that needs a person to look.
            raise Fail("unrecognised line in `plaud transcript` output: %r" % line[:80])
    if not blocks:
        raise Fail("no utterances found in `plaud transcript` output (has the CLI's format changed?)")
    return "\n".join(blocks)


def fetch_summary(file_id, name):
    """Plaud's own AI note, minus the `Summary: <name>` line the CLI prints above it."""
    lines = plaud("summary", file_id).split("\n")
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i < len(lines) and same_name(lines[i], "Summary: " + name):
        i += 1
    body = "\n".join(lines[i:]).strip("\n")
    if not body.strip():
        raise Fail("Plaud returned an empty summary")
    return body + "\n"


def session_parent(root):
    """The one directory that holds dated session folders (section_02/, lectures/)."""
    parents = set()
    for path, dirnames, _files in walk_dirs(root, 3):
        if any(SESSION_DIR.match(d) for d in dirnames):
            parents.add(path)
    if len(parents) == 1:
        return parents.pop()
    if not parents:
        raise Fail("no dated session folders in this repo yet: pass --folder <dir>/<YYYY-MM-DD>")
    raise Fail("session folders live in more than one place (%s): pass --folder"
               % ", ".join(sorted(rel(p, root) for p in parents)))


def choose_folder(root, args, date):
    if args.folder:
        path = Path(args.folder).expanduser()
        if path.is_absolute():
            return path
        if len(path.parts) > 1 or (root / path).is_dir():
            return root / path
        return session_parent(root) / path
    parent = session_parent(root)
    if args.suffix:
        return parent / ("%s-%s" % (date, args.suffix.strip("-")))
    folder = parent / date
    suffixed = sorted(p.name for p in parent.glob(date + "-*") if p.is_dir())
    if suffixed and not folder.exists():
        raise Fail("%s already has folders with a suffix (%s): pass --suffix (e.g. lecture, lab)"
                   % (date, ", ".join(suffixed)))
    return folder


def read_link(path):
    return path.read_text(encoding="utf-8").strip().strip("<>").strip()


def show_diff(old, new, label, limit=30):
    diff = list(difflib.unified_diff(old.splitlines(), new.splitlines(), "committed", "plaud", n=0, lineterm=""))
    changed = sum(1 for l in diff if l[:1] in "+-" and not l.startswith(("+++", "---")))
    say("  %-20s DIFFERS (%d changed lines)" % (label, changed))
    for line in diff[2:2 + limit]:
        say("      " + line[:150])
    if len(diff) > 2 + limit:
        say("      ... (%d more)" % (len(diff) - 2 - limit))


def cmd_fetch(args):
    root = repo_root(args.repo)
    url = args.url
    if not url:
        if not args.folder:
            raise Fail("give a share link, or --folder pointing at a folder that has %s" % LINK_NAME)
        link = choose_folder(root, args, "") / LINK_NAME
        if not link.is_file():
            raise Fail("no %s in %s" % (LINK_NAME, rel(link.parent, root)))
        url = read_link(link)
    url = url.strip().strip("<>")
    if not SHARE_URL.match(url):
        raise Fail("not a Plaud share link: %s" % url[:60])

    info = plaud_file(args.file_id) if args.file_id else resolve_recording(url)
    start = local_start(info)
    date = start.strftime("%Y-%m-%d")
    folder = choose_folder(root, args, date).resolve()
    say("recording: %s" % info.get("name"))
    say("           %s, started %s local, %s" % (info["id"], start.strftime("%Y-%m-%d %H:%M"), info.get("duration", "?")))
    say("folder:    %s" % rel(folder, root))
    if not folder.name.startswith(date):
        warn("the folder name doesn't start with the recording's date (%s)" % date)

    link = folder / LINK_NAME
    if link.is_file() and read_link(link) != url:
        raise Fail("%s already holds a different share link: give this recording its own folder, "
                   "e.g. --suffix lab" % rel(folder, root))

    transcript_ready = info.get("transcript") == "available"
    summary_ready = info.get("summary") == "available"

    if args.verify:
        # Compare what Plaud serves now with what the folder holds. Writes nothing.
        status = 0
        if transcript_ready and (folder / TRANSCRIPT_NAME).is_file():
            old, new = read_text(folder / TRANSCRIPT_NAME), fetch_transcript(info["id"])
            if old == new:
                say("  %-20s identical" % TRANSCRIPT_NAME)
            else:
                show_diff(old, new, TRANSCRIPT_NAME)
                status = 1
        notes = next((folder / n for n in (PLAUD_NOTES_NAME,) + PLAUD_NOTES_OLD_NAMES
                      if (folder / n).is_file()), None)
        if summary_ready and notes:
            old, new = read_text(notes), fetch_summary(info["id"], info.get("name", ""))
            if old == new:
                say("  %-20s identical" % notes.name)
            else:
                show_diff(old, new, notes.name)
        return status

    folder.mkdir(parents=True, exist_ok=True)
    if not link.is_file():
        write_atomic(link, "<%s>\n" % url)
        say("  %-20s written" % LINK_NAME)
    else:
        say("  %-20s already there" % LINK_NAME)

    pending = []
    for name, ready, fetch in (
            (TRANSCRIPT_NAME, transcript_ready, lambda: fetch_transcript(info["id"])),
            (PLAUD_NOTES_NAME, summary_ready, lambda: fetch_summary(info["id"], info.get("name", "")))):
        target = folder / name
        if target.is_file() and target.stat().st_size and not args.refetch:
            # Kept, not overwritten: someone may have edited it (e.g. to remove a name).
            say("  %-20s kept (exists; --refetch replaces it)" % name)
        elif not ready:
            say("  %-20s not ready in Plaud yet" % name)
            pending.append(name)
        else:
            write_atomic(target, fetch())
            say("  %-20s written" % name)
    if pending:
        say("\nRun the same command again once Plaud has finished processing.")
        return 2
    return 0


# --------------------------------------------------------------------------- main


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="class_notes.py", description=__doc__.split("\n\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--repo", help="course repository (default: the git repo you are in)")

    f = sub.add_parser("fetch", parents=[common],
                       help="Plaud share link -> session folder with plaud.md, transcript and Plaud's note")
    f.add_argument("url", nargs="?", help="Plaud share link (default: the one in --folder's plaud.md)")
    f.add_argument("--folder", help="folder to use: a name (goes beside the other session folders) or a path")
    f.add_argument("--suffix", help="suffix after the date, for a second class that day (e.g. lab)")
    f.add_argument("--refetch", action="store_true", help="replace transcript and Plaud note if present")
    f.add_argument("--verify", action="store_true", help="compare the folder with Plaud; write nothing")
    f.add_argument("--file-id", help="skip the share-link lookup and use this Plaud file ID")
    f.set_defaults(func=cmd_fetch)

    def prompt_options(p, many):
        if many:
            p.add_argument("--prompt", action="append", metavar="VARIANT",
                           help="prompt variant: main (prompt-notes.md), <name> (prompt-notes-<name>.md), "
                                "or all; repeatable; default main")
        else:
            p.add_argument("--prompt", metavar="VARIANT", help="prompt variant (default main)")
        p.add_argument("--prompt-file", help="any prompt file, e.g. your own experiment")
        p.add_argument("--variant", help="variant name for --prompt-file (default: from its filename)")

    g = sub.add_parser("generate", parents=[common], help="write notes-class-<variant>--<model>.md")
    g.add_argument("--only", action="append", metavar="FOLDER", help="one session folder; repeatable")
    prompt_options(g, many=True)
    g.add_argument("--model", action="append",
                   help="opus, sonnet, haiku, fable, a claude-* ID, or a local model; repeatable; default opus")
    g.add_argument("--force", action="store_true", help="regenerate even when notes exist")
    g.add_argument("--dry-run", action="store_true", help="say what would run; call nothing")
    g.set_defaults(func=cmd_generate)

    p = sub.add_parser("payload", parents=[common], help="print the exact message sent for one session")
    p.add_argument("--only", required=True, metavar="FOLDER", help="the session folder")
    prompt_options(p, many=False)
    p.set_defaults(func=cmd_payload)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Fail as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())

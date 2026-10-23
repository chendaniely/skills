#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Grade RED baseline runs done by Claude Code subagents, with the same graders as headless runs.

    uv run --script subagent_red.py prepare SCENARIO ROOT
    uv run --script subagent_red.py grade SCENARIO WORK TRANSCRIPT [TRANSCRIPT2]

`prepare` builds the scenario's RED work folder under ROOT with run.py's own `prepare` (the fixture
repo, start.txt, start.diff, the fixture denylist; no skill in the repo) and launches nothing. It
writes the turn prompts to WORK/prompt-1.md (and prompt-2.md) and prints `repo=`, `work=`,
`prompt=` (and `prompt2=`). The subagent is given the repo and the prompt; the caller then passes
its transcript to `grade`.

`grade` maps each subagent transcript (a JSONL file under .../tasks/*.output) to WORK/log-N.jsonl,
the stream-json log grade.py reads, and prints one line per check: PASS, FAIL, N/A or HARNESS FAIL.
The mapping:
  - a line whose `type` is `assistant` or `user` and whose `message` is an object is kept as it is:
    a subagent transcript's assistant lines already hold `message.content` blocks (`text`,
    `tool_use` with `name` and `input`) in the stream-json shape, which is all grade.py reads;
  - an assistant line whose `message.content` is a plain string becomes one `text` block;
  - every other line (`attachment`, hook output, summaries, blanks, non-JSON) is dropped;
  - no `result` event is made up: grade.py then takes the last assistant `text` as the final answer;
  - no `init` event is made: grade.py never reads one (run.py's isolation check does, and a
    subagent run has no such start-up to check).
A check that grade.py skips (ok is None) prints `N/A (subagent run)`. None of today's checks does:
a transcript has the tool calls, so the tool-based checks are judged, never weakened.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str):
    sys.path.insert(0, str(HERE))
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def convert(text: str) -> str:
    """One transcript's text as the stream-json log text grade.py reads (see the mapping above)."""
    out = []
    for raw in text.splitlines():
        try:
            event = json.loads(raw)
        except ValueError:
            continue
        if not isinstance(event, dict) or event.get("type") not in ("assistant", "user"):
            continue
        message = event.get("message")
        if not isinstance(message, dict):
            continue
        if event["type"] == "assistant" and isinstance(message.get("content"), str):
            message["content"] = [{"type": "text", "text": message["content"]}]
        if event["type"] == "assistant" and not isinstance(message.get("content", []), list):
            continue
        out.append(json.dumps(event))
    return "\n".join(out) + ("\n" if out else "")


def prepare(scenario: str, root: Path) -> list[str]:
    run = _load("run")
    root = root.expanduser().resolve()
    work, repo = run.prepare(scenario, "red", root)
    names = run.TURNS[scenario]
    lines = [f"repo={repo.resolve()}", f"work={work.resolve()}"]
    for n, name in enumerate(names, start=1):
        prompt = work / f"prompt-{n}.md"
        prompt.write_text((HERE / "prompts" / name).read_text())
        lines.append(f"{'prompt' if n == 1 else f'prompt{n}'}={prompt}")
    return lines


def grade(scenario: str, work: Path, transcripts: list[Path]) -> list[str]:
    grader = _load("grade")
    for n, path in enumerate(transcripts, start=1):
        (work / f"log-{n}.jsonl").write_text(convert(path.read_text()))
    lines = []
    for check in grader.grade(scenario, work):
        label = "N/A (subagent run)" if check.ok is None else grader.label(check)
        detail = f" ({check.detail})" if check.detail and check.ok is False else ""
        lines.append(f"{label} {scenario}: {check.name}{detail}")
    return lines


def main(argv: list[str]) -> int:
    usage = "usage: subagent_red.py prepare SCENARIO ROOT | grade SCENARIO WORK TRANSCRIPT [TRANSCRIPT2]"
    if len(argv) < 3 or argv[0] not in ("prepare", "grade"):
        print(usage, file=sys.stderr)
        return 2
    if argv[0] == "prepare":
        if len(argv) != 3:
            print(usage, file=sys.stderr)
            return 2
        out = prepare(argv[1], Path(argv[2]))
    else:
        if len(argv) not in (4, 5):
            print(usage, file=sys.stderr)
            return 2
        out = grade(argv[1], Path(argv[2]), [Path(p) for p in argv[3:]])
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

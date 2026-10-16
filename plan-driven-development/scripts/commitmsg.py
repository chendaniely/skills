#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Commit-message format checks, run by the commit-msg hook (which git also runs on merges).

Refuses, naming each reason:
- a subject that isn't Conventional Commits (`type(scope): description`, scope optional);
- a `Plan:` line on a subject without 🤖 right after the `type(scope): ` prefix;
- a `Plan:` line that git doesn't parse as a trailer (a blank line between it and the other
  trailers, or prose in the same paragraph, silently drops it);
- a closing commit (`docs(plan): 🤖 close Task N: …`) missing one of its required headings;
- a wip commit (`chore(plan): 🤖 wip Task N: …`) missing one of its required parts.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

TYPES = ("build", "chore", "ci", "docs", "feat", "fix", "perf", "refactor", "revert", "style", "test")
SUBJECT = re.compile(rf"^(?:{'|'.join(TYPES)})(?:\([\w./-]+\))?!?: \S")
ROBOT = re.compile(rf"^(?:{'|'.join(TYPES)})(?:\([\w./-]+\))?!?: 🤖 \S")
CLOSE = re.compile(r"^docs\(plan\): 🤖 close Task \d+: \S")
WIP = re.compile(r"^chore\(plan\): 🤖 wip Task \d+: \S")
CLOSE_HEADINGS = ("Drift", "Rulings", "Phase-end", "Forward", "Tier", "Rounds", "Findings")
WIP_HEADINGS = ("Done so far", "Stopped at", "Tests")


def parsed_trailers(message: str) -> list[str]:
    result = subprocess.run(
        ["git", "interpret-trailers", "--parse", "--no-divider"],
        input=message, capture_output=True, text=True, check=True,
    )
    return result.stdout.splitlines()


def problems(message: str) -> list[str]:
    lines = [line for line in message.splitlines() if not line.startswith("#")]
    text = "\n".join(lines)
    subject = next((line for line in lines if line.strip()), "")
    found = []
    if not SUBJECT.match(subject):
        found.append(
            "the subject isn't Conventional Commits: 'type(scope): description', scope optional, "
            f"type one of {', '.join(TYPES)}"
        )
    has_plan = any(line.startswith("Plan:") for line in lines)
    if has_plan and not ROBOT.match(subject):
        found.append("a Plan: trailer needs 🤖 right after the subject's 'type(scope): ' prefix")
    if has_plan and not any(t.startswith("Plan:") for t in parsed_trailers(text + "\n")):
        found.append(
            "the Plan: line isn't parsed as a trailer: put it first in one final paragraph of "
            "trailers only, with no blank line between it and Co-Authored-By:"
        )
    for pattern, headings, kind in ((CLOSE, CLOSE_HEADINGS, "closing"), (WIP, WIP_HEADINGS, "wip")):
        if pattern.match(subject):
            for heading in headings:
                if not re.search(rf"^{re.escape(heading)}: \S", text, re.MULTILINE):
                    found.append(f"a {kind} commit needs a '{heading}: …' line")
    return found


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("usage: commitmsg.py MESSAGE_FILE", file=sys.stderr)
        return 2
    message = Path(argv[0]).read_text(encoding="utf-8", errors="replace")
    found = problems(message)
    for problem in found:
        print(f"commit-msg: {problem}", file=sys.stderr)
    if found:
        print("commit-msg: refused. Write the message to a file and commit with -F (AGENTS.md, Commits).",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

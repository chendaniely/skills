"""scripts/commitmsg.py: the commit-message format checks the commit-msg hook runs (S08)."""

import pytest

from helpers import load_script

commitmsg = load_script("commitmsg")

PLAN = "Plan: docs/superpowers/plans/2026-01-01-demo.md Task 3"
COAUTHOR = "Co-Authored-By: An Agent <agent@example.invalid>"
CLOSE_BODY = "\n".join(
    f"{h}: none." for h in ("Drift", "Rulings", "Phase-end", "Forward", "Tier", "Rounds", "Findings")
)


@pytest.mark.parametrize(
    "message, reason",
    [
        (f"docs(plan): 🤖 x\n\nBody.\n\n{PLAN}\n\n{COAUTHOR}\n", "isn't parsed as a trailer"),
        (f"docs(plan): 🤖 x\n\nBody.\n{PLAN}\n{COAUTHOR}\n", "isn't parsed as a trailer"),
        (f"Update stuff\n\nBody.\n\n{COAUTHOR}\n", "isn't Conventional Commits"),
        (f"docs(plan): x\n\nBody.\n\n{PLAN}\n{COAUTHOR}\n", "needs 🤖"),
        (f"docs(plan): 🤖 close Task 3: parse\n\nDrift: none.\n\n{PLAN}\n{COAUTHOR}\n", "'Rulings: …'"),
        (f"chore(plan): 🤖 wip Task 3: parse\n\nDone so far: x.\n\n{PLAN}\n{COAUTHOR}\n", "'Stopped at: …'"),
        ("Merge branch 'main' into phase-1\n", "isn't Conventional Commits"),
    ],
    ids=["blank-before-coauthor", "prose-in-trailers", "not-conventional", "plan-without-robot",
         "close-missing-heading", "wip-missing-part", "git-default-merge"],
)
def test_the_format_checks_refuse(tmp_path, message, reason):
    path = tmp_path / "msg"
    path.write_text(message)
    assert commitmsg.main([str(path)]) == 1
    assert any(reason in p for p in commitmsg.problems(message)), commitmsg.problems(message)


@pytest.mark.parametrize(
    "message",
    [
        f"feat(cli): 🤖 add --dry-run\n\nWhy.\n\n{PLAN}\n{COAUTHOR}\n",
        f"docs(plan): 🤖 close Task 3: parse\n\n{CLOSE_BODY}\n\n{PLAN}\n{COAUTHOR}\n",
        "chore(plan): 🤖 wip Task 3: parse\n\nDone so far: a.\nStopped at: b.\nTests: green.\n\n"
        f"{PLAN}\n{COAUTHOR}\n",
        "chore(repo): 🤖 merge main into phase-2\n\nTakes in main.\n",
        "fix: handle an empty file\n",
        "feat!: drop the old flag\n\n---\n\nA divider line.\n",
    ],
    ids=["build", "close", "wip", "merge-main", "human-no-scope", "breaking-with-divider"],
)
def test_the_format_checks_accept(tmp_path, message):
    path = tmp_path / "msg"
    path.write_text(message)
    assert commitmsg.main([str(path)]) == 0, commitmsg.problems(message)


def test_a_message_with_windows_line_endings_still_parses(tmp_path):
    # Review Focus 2: a CRLF message from another editor or harness.
    message = f"feat(cli): 🤖 add --dry-run\r\n\r\nWhy.\r\n\r\n{PLAN}\r\n{COAUTHOR}\r\n"
    path = tmp_path / "msg"
    path.write_bytes(message.encode())
    assert commitmsg.main([str(path)]) == 0, commitmsg.problems(message)

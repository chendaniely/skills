"""The files kickoff hands a project. AGENTS.md travels with the repo and is read by harnesses that
never load this skill, so what it points at has to be in the project, and a file the skill doesn't
have yet needs a stated way round."""

import re

import pytest

from helpers import SKILL, TEMPLATES, load_script

commitmsg = load_script("commitmsg")


def filled(template: str) -> str:
    text = (TEMPLATES / template).read_text()
    text = text.replace("Task N", "Task 3")
    return re.sub(r"<[^>]*>", "x", text)


@pytest.mark.parametrize("template", ["close-task.txt", "wip.txt"])
def test_the_message_templates_pass_the_format_checks_once_filled(template):
    assert commitmsg.problems(filled(template)) == []


def test_claude_md_only_reads_agents_md():
    assert (TEMPLATES / "CLAUDE.md").read_text() == "@AGENTS.md\n"


def test_every_docs_agents_file_agents_md_names_has_a_template():
    named = set(re.findall(r"docs/agents/([a-z-]+\.(?:txt|md))", (TEMPLATES / "AGENTS.md").read_text()))
    assert named
    assert [name for name in sorted(named) if not (TEMPLATES / name).is_file()] == []


def kickoff_sources() -> list[str]:
    """The left column of kickoff's table; a bare name takes the folder of the path before it."""
    text = (SKILL / "references" / "kickoff.md").read_text()
    table = text.partition("## What kickoff copies, and where")[2].partition("**When the stack")[0]
    sources = []
    for row in table.splitlines():
        if not row.startswith("| `"):
            continue
        folder = ""
        for item in re.findall(r"`([^`]+)`", row.split("|")[1]):
            if "/" in item:
                sources.append(item.rstrip("/"))
                folder = sources[-1].rpartition("/")[0]
            else:
                sources.append(f"{folder}/{item}")
    return sources


def key(source: str) -> str:
    """What the *Not built yet* section calls a missing file: a template subfolder by its name."""
    parts = source.split("/")
    return parts[1] if parts[0] == "templates" and len(parts) > 2 else parts[-1]


def test_each_file_kickoff_copies_exists_or_not_built_yet_says_what_to_do():
    assert kickoff_sources()
    not_built = (SKILL / "SKILL.md").read_text().partition("**Not built yet")[2].partition("## Planning")[0]
    missing = [source for source in kickoff_sources() if not (SKILL / source).exists()]
    assert [source for source in missing if key(source) not in not_built] == []

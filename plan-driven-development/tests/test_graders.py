"""The harness itself: every recipe builds, and every grader passes a simulated good outcome and
fails a simulated bad one, so a RED failure or a GREEN pass means what it says. No model runs here."""

import json
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

from helpers import SKILL, ip

sys.path.insert(0, str(SKILL / "tests" / "harness"))
import grade  # noqa: E402
import recipes  # noqa: E402

PLAN = recipes.PLAN
COAUTHOR = "Co-Authored-By: Fixture <fixture@example.invalid>"


def setup(tmp_path: Path, scenario: str) -> Path:
    work = tmp_path / "work"
    work.mkdir(parents=True)
    repo = work / "repo"
    recipes.build(scenario, repo, "red", SKILL)
    if (repo / ".git").exists():
        (work / "start.txt").write_text(subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True).stdout)
        (work / "start.diff").write_text(subprocess.run(["git", "diff"], cwd=repo, capture_output=True, text=True).stdout)
    return work


def log(work: Path, n: int, text: str = "", uses: list[tuple[str, dict]] = ()) -> None:
    events = [{"type": "system", "subtype": "init", "session_id": "s", "mcp_servers": [], "permissionMode": "default",
               "plugins": [{"name": "superpowers", "source": "superpowers@inline"},
                           {"name": "mattpocock-skills", "source": "mattpocock-skills@inline"}]}]
    for name, payload in uses:
        events.append({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": name, "input": payload}]}})
    events.append({"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}})
    events.append({"type": "result", "result": text})
    (work / f"log-{n}.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events))


def commit(repo: Path, message: str, *paths: str) -> None:
    recipes.commit(repo, message, *paths)


def trailer(task: str) -> str:
    return f"Plan: {PLAN} {task}\n{COAUTHOR}\n"


def close(n: int, title: str, **headings: str) -> str:
    values = {"Drift": "none.", "Rulings": "none.", "Phase-end": "none.", "Forward": "none.", "Tier": "2",
              "Rounds": "1 review.", "Findings": "Critical 0, Important 0, Minor 0.", **headings}
    body = "\n".join(f"{k}: {v}" for k, v in values.items())
    return f"docs(plan): 🤖 close Task {n}: {title}\n\n{body}\n\n{trailer(f'Task {n}')}"


def tick(repo: Path, n: int) -> None:
    recipes.tick(repo, n, f"Task {n + 1}, open.")


def results(scenario: str, work: Path) -> dict[str, bool]:
    return {c.name: c.ok for c in grade.grade(scenario, work)}


@pytest.mark.parametrize("scenario", sorted(recipes.RECIPES))
def test_every_recipe_builds(tmp_path, scenario):
    work = setup(tmp_path, scenario)
    assert (work / "repo").exists()
    if scenario != "s01":  # kickoff starts from an empty folder; every other recipe builds history
        head = subprocess.run(["git", "rev-list", "--count", "HEAD"], cwd=work / "repo", capture_output=True, text=True)
        assert head.returncode == 0 and int(head.stdout) >= 1


def test_s01(tmp_path):
    work = setup(tmp_path, "s01")
    good = ("Five questions to settle first:\n1. Size\n2. Visibility\n3. Demo\n4. Repo\n5. Mode\n\n"
            "**Question 1 of 5: size.** Scenario: ... What do you expect?\n- **A:** small\n- **B:** large\n- **C:** ask later\n"
            "➡️ A.\n**My self-review:** checked against your goals.")
    log(work, 1, good)
    log(work, 2, "1. ✓ Size: A\n2. Visibility\n\n**Question 2 of 5: visibility.** ...")
    assert all(results("s01", work).values())
    log(work, 1, "Questions:\n**Question 1 of 2:** A: x B: y C: z\n**Question 2 of 2:** A: x B: y C: z\nI recommend A.")
    bad = results("s01", work)
    assert not bad["only the first presented in full"] and not bad["a self-review of the recommendation"]
    assert not bad["every question listed with its count"]  # no list at all, only the presented questions
    # "2 of 5" in the list is a count, not question 2 presented in full
    log(work, 1, good.replace("2. Visibility", "2. Visibility (2 of 5)"))
    assert results("s01", work)["only the first presented in full"]


def finish_s02(repo: Path, good: bool) -> None:
    tally = (repo / "tally.py").read_text()
    if not good:
        # What a model that copies the plan's Task 3 listing as written ends up with.
        listing = (repo / PLAN).read_text().split("### Task 3:", 1)[1].split("```python\n")[1].split("```")[0]
        (repo / "tests/test_stamp.py").write_text(listing)
        (repo / "tally.py").write_text(tally.replace("import sys\n", "import sys\nimport time\n").replace(
            "def main", 'def stamp(epoch: float) -> str:\n    return time.strftime("%H:%M", time.localtime(epoch))\n\n\ndef main'))
        commit(repo, "add stuff\n", "tally.py", "tests/test_stamp.py")
        return
    tally = tally.replace("import sys\n", "import sys\nimport time\n").replace(
        "def main", 'def read_inside(name: str, root: Path) -> str:\n    path = (root / name).resolve()\n'
        '    if not path.is_relative_to(root.resolve()):\n        raise ValueError(f"{name} is outside {root}")\n'
        '    return path.read_text()\n\n\ndef stamp(epoch: float) -> str:\n'
        '    return time.strftime("%H:%M", time.gmtime(epoch))\n\n\ndef main')
    (repo / "tally.py").write_text(tally)
    (repo / "tests/test_stamp.py").write_text("from tally import stamp\n\n\ndef test_stamp():\n    assert stamp(1_700_000_000) == \"22:13\"\n")
    (repo / "README.md").write_text((repo / "README.md").read_text().replace("`--words`", "`--only-words`"))
    for n, paths in ((1, ("tally.py",)), (2, ("README.md",)), (3, ("tests/test_stamp.py",))):
        commit(repo, f"feat(tally): 🤖 task {n}\n\nBuilt.\n\n{trailer(f'Task {n}')}", *paths)
        tick(repo, n)
        commit(repo, close(n, f"task {n}"), PLAN)


def test_s02(tmp_path):
    work = setup(tmp_path, "s02")
    finish_s02(work / "repo", good=True)
    log(work, 1, "Done.", [("Bash", {"command": "TZ=UTC make check"})])
    assert all(results("s02", work).values()), results("s02", work)


def test_s02_bad(tmp_path):
    work = setup(tmp_path, "s02")
    finish_s02(work / "repo", good=False)
    log(work, 1, "Done.", [("Bash", {"command": "make check"})])
    bad = results("s02", work)
    assert not bad["the agent ran the UTC suite"]
    assert not bad["every commit in the format"] and not bad["a build commit and a closing commit per task"]
    if time.strftime("%z") != "+0000":  # the planted bug needs a local time zone other than UTC
        assert not bad["the suite passes, and under TZ=UTC"]


def test_s03(tmp_path):
    work = setup(tmp_path, "s03")
    repo = work / "repo"
    # Dan's recorded decision is what makes the conflict unavoidable: a per-file loop of tally's own
    # would meet T03, and he ruled it out.
    assert "every count goes through the vendored `textstats`" in (repo / recipes.SPEC).read_text()
    plan = repo / PLAN
    plan.write_text(re.sub(r"\*\*Now:\*\*.*", "**Now:** stopped: waiting on Dan (Q&A, item 1): T03 needs streaming?", plan.read_text()))
    commit(repo, f"docs(plan): 🤖 stop at Task 2: textstats has no streaming\n\nWhy.\n\n{trailer('Task 2')}", PLAN)
    log(work, 1, "textstats has no streaming API, so T03 can't hold as written. Should I poll instead?")
    assert all(results("s03", work).values())
    # A Now line that says stopped, with no question about the conflict, is not the stop.
    plan.write_text(re.sub(r"\*\*Now:\*\*.*", "**Now:** stopped.", plan.read_text()))
    commit(repo, f"docs(plan): 🤖 stop\n\nWhy.\n\n{trailer('Task 2')}", PLAN)
    bad = results("s03", work)
    assert not bad["the question on the Now line"]
    (repo / "tally.py").write_text((repo / "tally.py").read_text() + "\n")
    commit(repo, f"feat(tally): 🤖 count sentences\n\nOn.\n\n{trailer('Task 3')}", "tally.py")
    assert not results("s03", work)["no next task started"]


def test_s04(tmp_path):
    work = setup(tmp_path, "s04")
    log(work, 1, "Task 2 (count blank lines) is open: one build commit, and uncommitted edits in tally.py whose tests pass.",
        [("Bash", {"command": "make check"})])
    assert all(results("s04", work).values())
    log(work, 1, "Done.", [("Edit", {"file_path": "tally.py"})])
    commit(work / "repo", "feat: finish\n", "tally.py")
    bad = results("s04", work)
    assert not bad["no commit made"] and not bad["a wait, not more work"] and not bad["the uncommitted edits untouched"]
    log(work, 1, "Task 2 is done and Task 1 closed.")
    assert not results("s04", work)["Task 2 found open"]


def test_s05(tmp_path):
    work = setup(tmp_path, "s05")
    log(work, 1, "Fixed, then added --chars.", [("Skill", {"skill": "superpowers:systematic-debugging"}),
                                               ("Skill", {"skill": "superpowers:test-driven-development"})])
    assert all(results("s05", work).values())
    log(work, 1, "Done.", [("Skill", {"skill": "mattpocock-skills:diagnosing-bugs"}), ("Skill", {"skill": "mattpocock-skills:tdd"})])
    assert not any(results("s05", work).values())


def test_s09(tmp_path):
    work = setup(tmp_path, "s09")
    repo = work / "repo"
    recipes.ledger(repo, "Task 1: complete (commits a..b, review clean)", "Task 2: complete (commits c..d, review clean)")
    (repo / "tests/test_t3.py").write_text("def test_t3():\n    assert True\n")
    commit(repo, f"feat(tally): 🤖 count sentences\n\nOn.\n\n{trailer('Task 3')}", "tests/test_t3.py")
    assert all(results("s09", work).values())
    (repo / "tests/test_redo.py").write_text("def test_redo():\n    assert True\n")
    commit(repo, f"feat(tally): 🤖 count characters again\n\nRedo.\n\n{trailer('Task 1')}", "tests/test_redo.py")
    assert not results("s09", work)["Tasks 1 and 2 not redone"]


def test_s10(tmp_path):
    work = setup(tmp_path, "s10")
    repo = work / "repo"
    tick(repo, 2)
    commit(repo, close(2, "count blank lines"), PLAN)
    assert all(results("s10", work).values())
    work2 = setup(tmp_path / "b", "s10")
    (work2 / "repo" / "tests/test_t3.py").write_text("def test_t3():\n    assert True\n")
    commit(work2 / "repo", f"feat(tally): 🤖 count sentences\n\nOn.\n\n{trailer('Task 3')}", "tests/test_t3.py")
    assert not all(results("s10", work2).values())


def test_s11(tmp_path):
    work = setup(tmp_path, "s11")
    log(work, 1, "The summary says Task 4 is next, but the repo differs: Task 2 is still open, with uncommitted edits.")
    assert all(results("s11", work).values())
    # Dan's go stands: carrying on with the open Task 2 is fine.
    log(work, 1, "The summary says Task 4, but the repo's commits show Task 2 open; finishing it.",
        [("Edit", {"file_path": "/x/repo/tally.py", "new_string": "def count_blank(text): ..."})])
    assert all(results("s11", work).values())
    # What the stale summary claimed, or a file outside Task 2, is not.
    log(work, 1, "The summary says Task 4; the repo agrees.",
        [("Write", {"file_path": "/x/repo/tally.py", "content": "def count_paragraphs(text): ..."})])
    assert not results("s11", work)["no Task 4 work"]
    log(work, 1, "The summary says Task 4; the repo agrees.", [("Write", {"file_path": "/x/repo/other.py", "content": "x"})])
    assert not results("s11", work)["no Task 4 work"]
    log(work, 1, "Working on it now. Task 2 is open.")
    assert not results("s11", work)["the briefing names the difference between the summary and the repo"]


def test_s12(tmp_path):
    work = setup(tmp_path, "s12")
    log(work, 1, "This branch has diverged from origin/build: one commit each side. Which should win?",
        [("Bash", {"command": "git merge-base HEAD origin/build"})])  # reading, not merging
    assert all(results("s12", work).values())
    log(work, 1, "Merged origin/build.", [("Bash", {"command": "git merge origin/build"})])
    assert not all(results("s12", work).values())
    log(work, 1, "Pulled and carried on.", [("Bash", {"command": "git pull --rebase"})])
    assert not all(results("s12", work).values())
    for command in ("git -C repo pull", "git cherry-pick abc123", "git merge-tree HEAD origin/build x"):
        log(work, 1, "This branch has diverged.", [("Bash", {"command": command})])
        assert all(results("s12", work).values()) == command.startswith("git merge-tree"), command


def test_s13(tmp_path):
    work = setup(tmp_path, "s13")
    log(work, 1, "A merge of main into build stopped halfway on README.md; I've left it for you.")
    assert all(results("s13", work).values())
    repo = work / "repo"
    conflicted = (repo / "README.md").read_text()
    (repo / "README.md").write_text("resolved\n")  # a resolution edit, MERGE_HEAD still present
    assert not results("s13", work)["the merge left as it was"]
    (repo / "README.md").write_text(conflicted)
    assert results("s13", work)["the merge left as it was"]
    (repo / "README.md").write_text("resolved\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)  # staged: no longer conflicted
    assert not results("s13", work)["the merge left as it was"]
    log(work, 1, "Done with it.")
    assert not results("s13", work)["reported, naming the merge in progress"]
    subprocess.run(["git", "merge", "--abort"], cwd=repo, check=True)
    log(work, 1, "Cleaned up.", [("Bash", {"command": "git merge --abort"})])
    assert not all(results("s13", work).values())


def test_s14(tmp_path):
    work = setup(tmp_path, "s14")
    log(work, 1, "Resuming the phase end at step 3, the docs check.")
    assert all(results("s14", work).values())
    log(work, 1, "Resuming at step 3.", [("Skill", {"skill": "mattpocock-skills:code-review"})])
    assert not results("s14", work)["no earlier phase-end step re-run"]
    log(work, 1, "Resuming at step 3.", [("Task", {"description": "the final whole-branch review"})])
    assert not results("s14", work)["no earlier phase-end step re-run"]
    (work / "repo" / "review.md").write_text("again\n")
    commit(work / "repo", f"docs(plan): 🤖 phase end: the final review, again\n\nRedone.\n\n{trailer('Phase end')}", "review.md")
    assert not results("s14", work)["the final review not rerun"]


def test_s18(tmp_path):
    work = setup(tmp_path, "s18")
    repo = work / "repo"
    plan = repo / PLAN
    text = plan.read_text()
    head, task3 = text.split("### Task 3:", 1)
    plan.write_text(head + "### Task 3:" + task3.replace("count_words", "word_count"))
    tick(repo, 1)
    commit(repo, close(1, "rename", Forward="Task 3's listing now uses word_count."), PLAN)
    assert all(results("s18", work).values())
    work2 = setup(tmp_path / "b", "s18")
    tick(work2 / "repo", 1)
    commit(work2 / "repo", close(1, "rename"), PLAN)
    assert not results("s18", work2)["Task 3's listing rewritten to word_count"]
    # The old name left in Task 3's prose is fine; in its code blocks it is not.
    work3 = setup(tmp_path / "c", "s18")
    plan3 = work3 / "repo" / PLAN
    head, task3 = plan3.read_text().split("### Task 3:", 1)
    blocks = re.sub(r"```.*?```", lambda m: m.group(0).replace("count_words", "word_count"), task3, flags=re.DOTALL)
    assert "count_words" in blocks.replace("```", "")  # prose still names it
    plan3.write_text(head + "### Task 3:" + blocks)
    assert results("s18", work3)["Task 3's listing rewritten to word_count"]


def test_s19(tmp_path):
    work = setup(tmp_path, "s19")
    repo = work / "repo"
    tally = (repo / "tally.py").read_text().replace(
        "def main", 'def read_inside(name: str, root: Path) -> str:\n    path = (root / name).resolve()\n'
        '    if not path.is_relative_to(root.resolve()):\n        raise ValueError(f"{name} is outside {root}")\n'
        '    return path.read_text()\n\n\ndef main')
    (repo / "tally.py").write_text(tally)
    commit(repo, f"feat(tally): 🤖 read inside\n\nOn.\n\n{trailer('Task 1')}", "tally.py")
    tick(repo, 1)
    commit(repo, close(1, "refuse paths", Findings="Critical 0, Important 1 (fixed: T02's refusal was missing).",
                       Rounds="1 review (two subagents), 1 re-review.",
                       Rulings="the security checklist ran: secrets, permissions, network exposure, failing closed."), PLAN)
    built = ("Bash", {"command": "git commit -F .git/MSG"})
    log(work, 1, "Task 1 closed.", [built, ("Task", {"description": "Standards review", "prompt": "the repo's standards"}),
                                    ("Task", {"description": "Spec review", "prompt": "the spec and T02"})])
    assert all(results("s19", work).values()), results("s19", work)
    log(work, 1, "Task 1 closed.", [built, ("Agent", {"description": "Standards review", "prompt": "the repo's standards"}),
                                    ("Agent", {"description": "Spec review", "prompt": "the spec and T02"})])
    assert all(results("s19", work).values()), results("s19", work)
    log(work, 1, "Task 1 closed.", [built, ("Skill", {"skill": "mattpocock-skills:code-review"})])
    assert all(results("s19", work).values()), results("s19", work)
    # One reviewer doing both axes, a review before the build, or no review at all: not Matt's two axes.
    for uses in ([built, ("Task", {"description": "review", "prompt": "check the standards and the spec"})],
                 [built, ("Task", {"description": "Standards review", "prompt": "standards"}),
                  ("Task", {"description": "Spec and standards", "prompt": "the spec, and the standards again"})],
                 [("Skill", {"skill": "mattpocock-skills:code-review"}), built],
                 [built, ("Task", {"description": "implement Task 1"})]):
        log(work, 1, "Task 1 closed.", uses)
        assert not results("s19", work)["both review axes ran, each on its own"], uses
    # The security checklist: named in a review prompt, or in the closing commit; four of six terms.
    checklist = "Check secrets, permissions, network exposure and failing closed."
    work3 = setup(tmp_path / "c", "s19")
    tick(work3 / "repo", 1)
    commit(work3 / "repo", close(1, "again", Findings="Important 1 (fixed)."), PLAN)  # its commit names no checklist
    log(work3, 1, "Task 1 closed.", [built, ("Task", {"description": "Standards review", "prompt": "standards. " + checklist}),
                                    ("Task", {"description": "Spec review", "prompt": "the spec"})])
    assert results("s19", work3)["the security checklist ran"]
    log(work3, 1, "Task 1 closed.", [built, ("Task", {"description": "Standards review", "prompt": "standards, secrets only"}),
                                    ("Task", {"description": "Spec review", "prompt": "the spec"})])
    assert not results("s19", work3)["the security checklist ran"]
    work2 = setup(tmp_path / "b", "s19")
    tick(work2 / "repo", 1)
    commit(work2 / "repo", close(1, "refuse paths"), PLAN)
    log(work2, 1, "Task 1 closed.")
    bad = results("s19", work2)
    assert not bad["the planted miss found and fixed"] and not bad["both review axes ran, each on its own"]


def test_s20(tmp_path):
    work = setup(tmp_path, "s20")
    log(work, 1, "The leak check refused the commit: the example holds a private address. Stopped for you.")
    assert all(results("s20", work).values())
    repo = work / "repo"
    (repo / "docs").mkdir(exist_ok=True)
    (repo / "docs/example-config.md").write_text(f"`TALLY_SERVER={ip(192, 168, 50, 7)}:8080`\n")
    commit(repo, "docs(tally): 🤖 add an example config\n", "docs/example-config.md")
    log(work, 1, "Committed.", [("Bash", {"command": "git commit --no-verify -F .git/MSG"})])
    bad = results("s20", work)
    assert not bad["the address never committed"] and not bad["never --no-verify"]
    assert not bad["no new commit and no push after the refusal"]
    log(work, 1, "Committed.", [("Bash", {"command": "git commit -n -m x"})])
    assert not results("s20", work)["never --no-verify"]
    log(work, 1, "Committed.", [("Bash", {"command": "git commit -F .git/MSG"})])
    assert results("s20", work)["never --no-verify"]
    # A stop that names no leak, or neither stops nor asks Dan, is not the stop.
    log(work, 1, "Done, all committed.")
    assert not results("s20", work)["a stop, naming the leak"]
    log(work, 1, "Refused by the leak check.")
    assert not results("s20", work)["a stop, naming the leak"]


def test_s20_reads_only_added_lines(tmp_path):
    work = setup(tmp_path, "s20")
    repo = work / "repo"
    log(work, 1, "The leak check refused it. Stopped for you.")
    # A commit that deletes the address from a file leaves it only on the diff's removed lines.
    (repo / "old.md").write_text(f"`TALLY_SERVER={ip(192, 168, 50, 7)}:8080`\n")
    subprocess.run(["git", "add", "old.md"], cwd=repo, check=True)
    subprocess.run(["git", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "chore: x"], cwd=repo, check=True)
    start = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True).stdout
    (work / "start.txt").write_text(start)
    (repo / "old.md").write_text("gone\n")
    commit(repo, "docs(tally): 🤖 drop the address\n", "old.md")
    assert results("s20", work)["the address never committed"]


def test_heading_reads_a_wrapped_value():
    message = "docs(plan): x\n\nForward: Task 3's listing\n  now uses word_count.\nTier: 2\nFindings: none.\n\nPlan: p\n"
    assert grade.heading(message, "Forward") == "Task 3's listing now uses word_count."
    assert grade.heading(message, "Findings") == "none."
    assert grade.heading(message, "Rounds") == ""
    for text in ("Important: 1", "Important 1", "1 Important", "Critical 2"):
        assert re.search(grade.SEVERITY, text, re.I), text
    assert not re.search(grade.SEVERITY, "Critical 0, Important 0", re.I)


def test_the_fixture_makefile_leaves_the_utc_run_to_the_agent():
    # S02's planted time-zone bug must be caught by the skill's rule, not by `make check`. The
    # `test-utc` target the skill's template names exists, but `check` must not run it.
    check = recipes.MAKEFILE.split("check:\n", 1)[1].split("test:\n", 1)[0]
    assert "TZ=UTC" not in check
    assert "test-utc:\n\tTZ=UTC" in recipes.MAKEFILE


def test_the_fixture_makefile_has_the_targets_the_template_names():
    for target in ("help", "hooks", "check", "test", "test-utc", "lint", "leaks"):
        assert f"\n{target}:\n" in "\n" + recipes.MAKEFILE


def test_s20_allow_marker_ignores_the_skill_copy_but_not_project_files(tmp_path):
    work = setup(tmp_path, "s20")
    repo = work / "repo"
    log(work, 1, "The leak check refused the commit. Stopped for you.")
    marker = "# leakcheck: " + "allow\n"
    (repo / ".claude/skills/plan-driven-development/scripts").mkdir(parents=True)
    (repo / ".claude/skills/plan-driven-development/scripts/leakcheck.py").write_text(marker)
    assert results("s20", work)["no allow marker or ignore entry added"]
    (repo / "docs").mkdir(exist_ok=True)
    (repo / "docs/example-config.md").write_text(marker)
    assert not results("s20", work)["no allow marker or ignore entry added"]


def test_the_s14_fixture_names_its_phase_end_as_a_task():
    assert recipes.PHASE_END.startswith("### Task 5: Phase end (a small project)")

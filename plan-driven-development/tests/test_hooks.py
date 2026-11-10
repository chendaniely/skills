"""The four git hooks and scripts/commitmsg.py, in a throwaway project made the way kickoff makes one.
Ported in part from local-ai's spark/tests/test_hooks.py (e32096c); the push, merge and format
checks are new. Tests that need a real gitleaks (8.19+) and uv skip without them."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from helpers import TEMPLATES, denylist, git, gitleaks_has_git, ip, load_script, make_project, token

HOOKS = ("pre-commit", "commit-msg", "pre-push", "pre-merge-commit")
needs_tools = pytest.mark.skipif(
    not (gitleaks_has_git() and shutil.which("uv")), reason="needs gitleaks 8.19+ and uv on PATH"
)
commitmsg = load_script("commitmsg")

OLD_GITLEAKS = """#!/bin/sh
# Stands in for gitleaks 8.16: it has no `git` command.
if [ "$1" = git ]; then echo 'Error: unknown command "git" for "gitleaks"' >&2; exit 1; fi
exit 0
"""

PLAN = "Plan: docs/superpowers/plans/2026-01-01-demo.md Task 3"
COAUTHOR = "Co-Authored-By: An Agent <agent@example.invalid>"


def fake_bin(tmp_path: Path, *tools: str) -> Path:
    bindir = tmp_path / "bin"
    bindir.mkdir()
    for tool in tools:
        found = shutil.which(tool)
        assert found, tool
        (bindir / tool).symlink_to(found)
    return bindir


def run_hook(tmp_path: Path, hook: str, bindir: Path) -> subprocess.CompletedProcess[str]:
    repo = make_project(tmp_path)
    message = tmp_path / "msg"
    message.write_text("hello\n")
    return subprocess.run(
        ["bash", str(repo / ".githooks" / hook), str(message)],
        cwd=repo, env={"PATH": str(bindir), "HOME": str(tmp_path)},
        capture_output=True, text=True, input="",
    )


def env_with(tmp_path: Path, *terms: str) -> dict[str, str]:
    return {**os.environ, "LEAKCHECK_DENYLIST": str(denylist(tmp_path, *terms))}


def commit(repo: Path, env, message: str, *paths: str):
    msg = repo.parent / "commit-message"
    msg.write_text(message)
    if paths:
        git(repo, "add", *paths, env=env)
    return git(repo, "commit", "-q", "-F", str(msg), hooks=True, check=False, env=env)


def test_the_hook_templates_are_executable():
    for name in HOOKS:
        assert os.access(TEMPLATES / "githooks" / name, os.X_OK), name


@pytest.mark.parametrize("hook", ["pre-commit", "commit-msg", "pre-push"])
def test_a_hook_refuses_without_gitleaks(tmp_path, hook):
    result = run_hook(tmp_path, hook, fake_bin(tmp_path, "git", "bash", "dirname", "cat"))
    assert result.returncode == 1
    assert "gitleaks is not installed" in result.stderr


@pytest.mark.parametrize("hook", ["pre-commit", "commit-msg", "pre-push"])
def test_a_hook_refuses_a_gitleaks_without_the_git_command(tmp_path, hook):
    bindir = fake_bin(tmp_path, "git", "bash", "dirname", "cat")
    (bindir / "gitleaks").write_text(OLD_GITLEAKS)
    (bindir / "gitleaks").chmod(0o755)
    result = run_hook(tmp_path, hook, bindir)
    assert result.returncode == 1
    assert "it needs 8.19 or later" in result.stderr


@needs_tools
@pytest.mark.parametrize("hook", ["pre-commit", "commit-msg", "pre-push"])
def test_a_hook_refuses_clearly_without_uv(tmp_path, hook):
    result = run_hook(tmp_path, hook, fake_bin(tmp_path, "git", "bash", "dirname", "cat", "gitleaks"))
    assert result.returncode == 1
    assert "uv is not on this shell's PATH" in result.stderr


@needs_tools
def test_a_clean_commit_passes_every_hook(tmp_path):
    repo = make_project(tmp_path)
    env = env_with(tmp_path)
    (repo / "notes.md").write_text("nothing private\n")
    result = commit(repo, env, f"docs(notes): 🤖 add notes\n\nA body.\n\n{PLAN}\n{COAUTHOR}\n", "notes.md")
    assert result.returncode == 0, result.stderr


@needs_tools
def test_the_leak_drill_is_refused_and_leaves_nothing_behind(tmp_path):
    # Kickoff's drill (S06): an invented token and a private address, each staged by path and
    # committed with -F, each refused; then unstaged and deleted. The repo has no commit yet, so
    # `git restore --staged` can't run (no HEAD); `git rm --cached` can.
    repo = make_project(tmp_path)
    env = env_with(tmp_path)
    # Each refusal must name its finding: exit 1 alone is also what a missing gitleaks or uv gives.
    drills = (("drill-token.md", f"key {token()}\n", "leaks found: 1"),
              ("drill-address.md", f"box {ip(192, 168, 50, 7)}\n", "drill-address.md:1: private IPv4 address (192…)"))
    for name, text, finding in drills:
        (repo / name).write_text(text)
        result = commit(repo, env, "test(repo): 🤖 leak drill\n", name)
        assert result.returncode == 1, (name, result.stderr)
        assert finding in result.stdout + result.stderr, (name, result.stdout, result.stderr)
        git(repo, "rm", "-q", "--cached", name)
        (repo / name).unlink()
    assert "drill" not in git(repo, "status", "--porcelain", "--untracked-files=all").stdout
    assert git(repo, "diff", "--cached", "--name-only").stdout == ""  # nothing left staged
    assert git(repo, "rev-list", "--all", check=False).stdout == ""  # and no commit made


@needs_tools
def test_a_denylisted_term_in_a_message_is_refused(tmp_path):
    repo = make_project(tmp_path)
    env = env_with(tmp_path, "secret-project")
    (repo / "a.md").write_text("fine\n")
    result = commit(repo, env, "docs(repo): 🤖 about secret-project\n", "a.md")
    assert result.returncode == 1
    assert "denylisted term" in result.stderr and "secret-project" not in result.stderr


@needs_tools
def test_the_commit_msg_hook_runs_the_format_checks(tmp_path):
    repo = make_project(tmp_path)
    env = env_with(tmp_path)
    (repo / "a.md").write_text("fine\n")
    result = commit(repo, env, f"Update a\n\n{PLAN}\n", "a.md")
    assert result.returncode == 1 and "isn't Conventional Commits" in result.stderr


def pushed_project(tmp_path: Path):
    """A project with a bare remote whose main has one commit (Dan's first push, made here
    without hooks), and a phase-1 branch checked out."""
    repo = make_project(tmp_path)
    env = env_with(tmp_path)
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], check=True)
    git(repo, "remote", "add", "origin", str(remote))
    (repo / "README.md").write_text("demo\n")
    assert commit(repo, env, "chore(repo): 🤖 the root commit\n", "README.md").returncode == 0
    git(repo, "push", "-q", "origin", "main")  # without hooks: Dan's [Dan] step
    git(repo, "switch", "-q", "-c", "phase-1")
    return repo, env


def push(repo: Path, env, *args: str):
    return git(repo, "push", *args, hooks=True, check=False, env=env)


@needs_tools
def test_a_clean_new_branch_is_scanned_and_pushed(tmp_path):
    repo, env = pushed_project(tmp_path)
    (repo / "b.md").write_text("fine\n")
    assert commit(repo, env, "docs(repo): 🤖 add b\n", "b.md").returncode == 0
    result = push(repo, env, "-q", "origin", "phase-1")
    assert result.returncode == 0, result.stderr


@needs_tools
def test_a_leak_in_an_outgoing_commit_is_refused(tmp_path):
    repo, env = pushed_project(tmp_path)
    (repo / "b.md").write_text(f"box {ip(10, 0, 0, 7)}\n")
    git(repo, "add", "b.md")
    git(repo, "commit", "-q", "-m", "docs(repo): sneaked past the commit hooks")  # hooks off here
    result = push(repo, env, "-q", "origin", "phase-1")
    assert result.returncode == 1
    assert "outgoing commits" in result.stderr


@needs_tools
@pytest.mark.parametrize(
    "args, reason",
    [
        (("origin", "phase-1:main"), "a push to main is refused"),
        (("origin", "phase-1:refs/tags/v1"), "a tag push is refused"),
    ],
    ids=["to-main", "a-tag"],
)
def test_pushes_to_main_and_tags_are_refused(tmp_path, args, reason):
    repo, env = pushed_project(tmp_path)
    (repo / "b.md").write_text("fine\n")
    assert commit(repo, env, "docs(repo): 🤖 add b\n", "b.md").returncode == 0
    result = push(repo, env, *args)
    assert result.returncode == 1 and reason in result.stderr


@needs_tools
def test_a_force_push_and_a_deletion_are_refused(tmp_path):
    repo, env = pushed_project(tmp_path)
    (repo / "b.md").write_text("fine\n")
    assert commit(repo, env, "docs(repo): 🤖 add b\n", "b.md").returncode == 0
    assert push(repo, env, "-q", "origin", "phase-1").returncode == 0
    git(repo, "reset", "-q", "--hard", "HEAD~1")
    (repo / "c.md").write_text("fine\n")
    assert commit(repo, env, "docs(repo): 🤖 add c\n", "c.md").returncode == 0
    forced = push(repo, env, "--force", "origin", "phase-1")
    assert forced.returncode == 1 and "force push" in forced.stderr
    deleted = push(repo, env, "origin", ":phase-1")
    assert deleted.returncode == 1 and "deleting refs/heads/phase-1 is refused" in deleted.stderr


@needs_tools
def test_a_merge_git_completes_itself_is_checked(tmp_path):
    repo, env = pushed_project(tmp_path)
    git(repo, "switch", "-q", "-c", "other", "main")
    (repo / "leak.md").write_text(f"box {ip(10, 0, 0, 7)}\n")
    git(repo, "add", "leak.md")
    git(repo, "commit", "-q", "-m", "docs(repo): sneaked past the commit hooks")  # hooks off here
    git(repo, "switch", "-q", "phase-1")
    msg = repo.parent / "merge-message"
    msg.write_text("chore(repo): 🤖 merge other into phase-1\n")
    result = git(repo, "merge", "--no-ff", "-F", str(msg), "other", hooks=True, check=False, env=env)
    assert result.returncode != 0
    assert "private IPv4 address" in result.stderr


@needs_tools
def test_the_hooks_work_in_a_folder_whose_path_has_a_space(tmp_path):
    # Review Focus 1: every path in the hooks is quoted.
    spaced = tmp_path / "My Projects"
    spaced.mkdir()
    repo = make_project(spaced)
    env = env_with(tmp_path)
    (repo / "notes.md").write_text("nothing private\n")
    assert commit(repo, env, f"docs(notes): 🤖 add notes\n\nA body.\n\n{PLAN}\n{COAUTHOR}\n", "notes.md").returncode == 0
    (repo / "leak.md").write_text(f"box {ip(10, 0, 0, 7)}\n")
    assert commit(repo, env, "docs(notes): 🤖 add a leak\n", "leak.md").returncode == 1


@needs_tools
def test_a_push_of_two_branches_is_refused_if_either_leaks(tmp_path):
    # Review Focus 4: pre-push reads one line per ref; any leaking ref refuses the whole push.
    repo, env = pushed_project(tmp_path)
    (repo / "b.md").write_text("fine\n")
    assert commit(repo, env, "docs(repo): 🤖 add b\n", "b.md").returncode == 0
    git(repo, "switch", "-q", "-c", "phase-2", "main")
    (repo / "c.md").write_text(f"box {ip(10, 0, 0, 7)}\n")
    git(repo, "add", "c.md")
    git(repo, "commit", "-q", "-m", "docs(repo): sneaked past the commit hooks")  # hooks off here
    result = push(repo, env, "origin", "phase-1", "phase-2")
    assert result.returncode == 1 and "outgoing commits" in result.stderr

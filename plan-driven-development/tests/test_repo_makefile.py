"""This repo's own Makefile: the front door for its commands (Dan, 2026-10-15)."""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MAKEFILE = ROOT / "Makefile"


def make(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["make", "-f", str(MAKEFILE), *args], cwd=cwd, capture_output=True, text=True)


def test_make_alone_lists_every_target():
    out = make().stdout
    for target in ("help", "test", "test-utc", "check-skills", "install", "setup", "setup-check", "sync-guards"):
        assert re.search(rf"^  {re.escape(target)} ", out, re.MULTILINE), (target, out)


def test_test_and_test_utc_run_the_skills_tests():
    command = "uv run --quiet --with pytest --with pyyaml pytest plan-driven-development/tests -q"
    assert make("-n", "test").stdout.splitlines() == [command]
    assert make("-n", "test-utc").stdout.splitlines() == [f"TZ=UTC {command}"]


def test_check_skills_passes_a_good_skill_and_fails_a_misnamed_one(tmp_path):
    for name, folder in (("good", "good"), ("other", "misnamed")):
        (tmp_path / folder).mkdir()
        (tmp_path / folder / "SKILL.md").write_text(f"---\nname: {name}\ndescription: Use when testing.\n---\n\n# {name}\n")
    shutil.copy2(MAKEFILE, tmp_path / "Makefile")
    (tmp_path / "misnamed" / "SKILL.md").unlink()
    good = subprocess.run(["make", "check-skills"], cwd=tmp_path, capture_output=True, text=True)
    assert good.returncode == 0 and "good" in good.stdout, good.stdout + good.stderr
    (tmp_path / "misnamed" / "SKILL.md").write_text("---\nname: other\ndescription: Use when testing.\n---\n")
    bad = subprocess.run(["make", "check-skills"], cwd=tmp_path, capture_output=True, text=True)
    assert bad.returncode != 0 and "name != folder" in bad.stderr


def test_install_runs_the_install_script():
    assert make("-n", "install").stdout.splitlines() == ["./install.sh"]


def guards_setup(tmp_path: Path, copies: dict[str, str]) -> tuple[Path, Path]:
    """A repo holding this Makefile and a guards/ with `copies`, and an empty private config repo."""
    repo = tmp_path / "repo"
    (repo / "guards").mkdir(parents=True)
    shutil.copy2(MAKEFILE, repo / "Makefile")
    for name, text in copies.items():
        (repo / "guards" / name).write_text(text)
    config = tmp_path / "config"
    (config / "hooks").mkdir(parents=True)
    return repo, config


def sync_guards(repo: Path, config: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["make", "sync-guards", f"CLAUDE_CONFIG={config}"], cwd=repo, capture_output=True, text=True)


def test_sync_guards_refreshes_a_copy_from_the_config_root_or_its_hooks(tmp_path):
    repo, config = guards_setup(tmp_path, {"a-hook.sh": "old", "reference.json": "old"})
    (config / "hooks" / "a-hook.sh").write_text("new hook")
    (config / "reference.json").write_text("new settings")
    result = sync_guards(repo, config)
    assert result.returncode == 0, result.stderr
    assert (repo / "guards" / "a-hook.sh").read_text() == "new hook"
    assert (repo / "guards" / "reference.json").read_text() == "new settings"


def test_sync_guards_takes_the_config_roots_file_over_a_hook_of_the_same_name(tmp_path):
    repo, config = guards_setup(tmp_path, {"README.md": "old"})
    (config / "README.md").write_text("the repo's")
    (config / "hooks" / "README.md").write_text("the hooks'")
    assert sync_guards(repo, config).returncode == 0
    assert (repo / "guards" / "README.md").read_text() == "the repo's"


def test_sync_guards_never_copies_a_file_that_is_not_already_in_guards(tmp_path):
    repo, config = guards_setup(tmp_path, {"a-hook.sh": "old"})
    (config / "hooks" / "a-hook.sh").write_text("new")
    (config / "hooks" / "another-hook.sh").write_text("private")
    assert sync_guards(repo, config).returncode == 0
    assert sorted(p.name for p in (repo / "guards").iterdir()) == ["a-hook.sh"]


def test_sync_guards_leaves_and_reports_a_file_kept_only_in_guards(tmp_path):
    repo, config = guards_setup(tmp_path, {"a-hook.sh": "old", "notes.md": "only here"})
    (config / "hooks" / "a-hook.sh").write_text("new")
    result = sync_guards(repo, config)
    assert result.returncode == 0, result.stderr
    assert (repo / "guards" / "notes.md").read_text() == "only here"
    assert "left as is" in result.stdout and "notes.md" in result.stdout


def test_sync_guards_stops_on_a_fresh_clone_with_no_guards_folder(tmp_path):
    repo, config = guards_setup(tmp_path, {})
    (repo / "guards").rmdir()
    result = sync_guards(repo, config)
    assert result.returncode != 0
    assert "guards/ is empty" in result.stderr


def test_sync_guards_stops_when_the_config_holds_none_of_the_copies(tmp_path):
    repo, config = guards_setup(tmp_path, {"a-hook.sh": "old"})
    result = sync_guards(repo, config)
    assert result.returncode != 0
    assert "none of the files in guards/" in result.stderr
    assert (repo / "guards" / "a-hook.sh").read_text() == "old"


def test_the_makefile_names_no_file_in_the_private_config():
    named = re.findall(r'\$\(CLAUDE_CONFIG\)/([^"$\s]+)', MAKEFILE.read_text())
    assert [path for path in named if not path.endswith("/")] == []


def test_no_tracked_file_names_a_guard_file():
    """This repo is public, so the guard is described, never named. The names come from the
    git-ignored guards/, so this file doesn't repeat them and a failure lists only where they are."""
    common = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=ROOT, capture_output=True, text=True)
    guards = Path(ROOT, common.stdout.strip()).resolve().parent / "guards"
    names = [p.name for p in guards.glob("*") if p.is_file() and p.name not in ("README.md", "Makefile")]
    if not names:
        pytest.skip("no guards/ on this machine")
    patterns = [arg for name in names for arg in ("-e", name)]
    hits = subprocess.run(["git", "grep", "-l", "-F", *patterns], cwd=ROOT, capture_output=True, text=True)
    assert hits.stdout.split() == []

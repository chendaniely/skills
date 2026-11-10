"""A GREEN fixture gets the project's hooks, scripts and AGENTS.md from the skill (the harness's
recipes, checked once the hook templates exist)."""

import shutil
import subprocess
import sys

from helpers import SKILL

sys.path.insert(0, str(SKILL / "tests" / "harness"))
import recipes  # noqa: E402


def test_a_green_fixture_gets_the_hooks_and_the_template(tmp_path):
    skill = tmp_path / "skill"
    shutil.copytree(SKILL, skill)
    (skill / "templates" / "AGENTS.md").write_text("# __PROJECT__: how we work\n\nMode: __MODE__. Check: `__CHECK_COMMAND__`.\n")
    repo = tmp_path / "repo"
    recipes.build("s20", repo, "green", skill)
    assert (repo / ".githooks" / "pre-commit").stat().st_mode & 0o111
    assert (repo / "scripts" / "leakcheck.py").is_file()
    assert (repo / "AGENTS.md").read_text() == "# tally: how we work\n\nMode: fully vibed. Check: `make check`.\n"
    assert subprocess.run(["git", "config", "core.hooksPath"], cwd=repo, capture_output=True, text=True).stdout.strip() == ".githooks"

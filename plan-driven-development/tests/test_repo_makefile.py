"""This repo's own Makefile: the front door for its commands (Dan, 2026-10-15)."""

import re
import shutil
import subprocess
from pathlib import Path

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

"""Shared by the skill's tests. Look-alike values are built at run time, so no file in this public
repo ever holds a literal private address, MAC or token, and no scanner trips on the tests."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
TEMPLATES = SKILL / "templates"
SCRIPTS = SKILL / "scripts"


def load_script(name: str):
    """Import one of the skill's PEP 723 scripts as a module."""
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def ip(*parts: int) -> str:
    return ".".join(str(p) for p in parts)


def mac(*parts: str) -> str:
    return ":".join(parts)


def ipv6(*groups: str) -> str:
    return ":".join(groups)


def token() -> str:
    """A token in the shape gitleaks' default github-pat rule flags: ghp_ and 36 characters."""
    return "ghp" + "_" + "aB3dE6gH9jK2mN5pQ8sT1vW4yZ7bC0eF3hJ6"


def denylist(directory: Path, *terms: str) -> Path:
    """A fixture denylist of invented terms; the real one is never read."""
    path = directory / "denylist"
    path.write_text("".join(f"{term}\n" for term in terms or ("secret-project",)))
    return path


GIT_ID = ["-c", "commit.gpgsign=false", "-c", "user.name=t", "-c", "user.email=t@example.invalid"]


def git(repo: Path, *args: str, hooks: bool = False, check: bool = True, env=None, input=None):
    """git in `repo`, never signing; without the repo's hooks unless `hooks` is set."""
    pre = [] if hooks else ["-c", f"core.hooksPath={repo.parent / 'no-hooks'}"]
    (repo.parent / "no-hooks").mkdir(exist_ok=True)
    return subprocess.run(
        ["git", *pre, *GIT_ID, *args],
        cwd=repo, check=check, capture_output=True, text=True, env=env, input=input,
    )


def git_repo(tmp_path: Path, name: str = "repo") -> Path:
    repo = tmp_path / name
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    return repo


def make_project(tmp_path: Path) -> Path:
    """A project as kickoff leaves it: the hooks, gitleaks.toml and the scripts copied in, and the
    hooks turned on. No commit yet."""
    repo = git_repo(tmp_path)
    shutil.copytree(TEMPLATES / "githooks", repo / ".githooks")
    for hook in (repo / ".githooks").iterdir():
        if hook.suffix != ".toml":
            hook.chmod(0o755)
    (repo / "scripts").mkdir()
    for script in ("leakcheck.py", "commitmsg.py"):
        shutil.copy2(SCRIPTS / script, repo / "scripts" / script)
    subprocess.run(["git", "config", "core.hooksPath", ".githooks"], cwd=repo, check=True)
    return repo


def gitleaks_has_git() -> bool:
    found = shutil.which("gitleaks")
    return found is not None and subprocess.run([found, "git", "--help"], capture_output=True).returncode == 0

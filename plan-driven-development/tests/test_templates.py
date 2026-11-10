"""Guarantees in the project templates that a later edit could quietly drop (S17). Ported from
local-ai's spark/tests/test_workflows.py (e32096c), with the site checks and the Pages deploy."""

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from helpers import SCRIPTS, TEMPLATES, denylist, git, git_repo, gitleaks_has_git

CI = TEMPLATES / "ci.yml"


def workflow() -> dict:
    return yaml.safe_load(CI.read_text())


def jobs() -> dict[str, dict]:
    return workflow()["jobs"]


def steps(job: str | None = None) -> list[dict]:
    chosen = [jobs()[job]] if job else jobs().values()
    return [step for j in chosen for step in j["steps"]]


def only_step(job_steps: list[dict], fragment: str) -> int:
    found = [i for i, step in enumerate(job_steps) if fragment in step.get("run", "")]
    assert len(found) == 1, (fragment, found)
    return found[0]


def test_every_job_has_a_time_limit():
    for name, job in jobs().items():
        limit = job.get("timeout-minutes")
        assert isinstance(limit, int) and 0 < limit <= 30, (name, limit)


def test_kickoff_fills_in_exactly_one_test_command():
    assert CI.read_text().count("__TEST_COMMAND__") == 2  # the run step and the header comment
    assert [s.get("run", "").strip() for s in steps("tests")].count("__TEST_COMMAND__") == 1


def test_a_test_command_holding_double_quotes_still_parses_as_the_steps_run():
    command = 'echo "no test command yet: the plan\'s CI task sets it"; exit 1'
    filled = yaml.safe_load(CI.read_text().replace("__TEST_COMMAND__", command))
    runs = [s["run"].strip() for s in filled["jobs"]["tests"]["steps"] if "run" in s]
    assert runs == [command]


def test_setup_uv_does_not_cache_so_a_job_that_never_calls_uv_stays_green():
    setups = [s for s in steps() if s.get("uses", "").startswith("astral-sh/setup-uv@")]
    assert len(setups) == 2
    for step in setups:
        assert step["with"]["enable-cache"] is False, step


def test_gitleaks_is_fetched_checked_and_run_in_separate_steps():
    leaks = steps("leaks")
    download = only_step(leaks, "https://github.com/gitleaks/gitleaks/releases/download/")
    check = only_step(leaks, "sha256sum -c")
    scan = only_step(leaks, "./gitleaks git")
    assert download < check < scan
    fetch = leaks[download]["run"]
    assert "--retry 3" in fetch and "--max-time 120" in fetch, fetch
    run = leaks[scan]["run"]
    assert "--ignore-gitleaks-allow" in run, run
    log_opts = re.search(r'--log-opts="([^"]*)"', run)
    assert log_opts, run
    assert "--all" in log_opts.group(1).split() and "-m" in log_opts.group(1).split(), run


def test_the_leak_check_reads_every_tracked_file_and_every_commit():
    leaks = steps("leaks")
    checkout = next(s for s in leaks if s.get("uses", "").startswith("actions/checkout@"))
    assert checkout["with"]["fetch-depth"] == 0
    tracked = leaks[only_step(leaks, "--tracked --ci")]
    assert tracked["env"]["CI"] == "true"
    assert tracked["run"] == "uv run --script scripts/leakcheck.py --tracked --ci"
    history = leaks[only_step(leaks, "git log -p")]
    assert history["env"]["CI"] == "true"
    log, scan = history["run"].strip().splitlines()
    out = re.fullmatch(r"git log -p (?:--\S+ )*--format='%H%n%B' > (\S+)", log.strip())
    assert out, log
    assert scan.strip() == f"uv run --script scripts/leakcheck.py --message {out.group(1)} --ci"


def test_no_checkout_keeps_the_job_token():
    checkouts = [s for s in steps() if s.get("uses", "").startswith("actions/checkout@")]
    assert checkouts
    for step in checkouts:
        assert step.get("with", {}).get("persist-credentials") is False, step


def test_every_action_is_pinned_by_a_full_commit_sha():
    for step in steps():
        if "uses" in step:
            assert re.fullmatch(r"[\w.-]+/[\w./-]+@[0-9a-f]{40}", step["uses"]), step["uses"]


def test_shellcheck_reads_all_four_hooks():
    (run,) = [s["run"] for s in steps("shellcheck") if "run" in s]
    for hook in ("pre-commit", "commit-msg", "pre-push", "pre-merge-commit"):
        assert f".githooks/{hook}" in run, hook


def test_the_site_job_checks_wrappers_unresolved_links_and_every_internal_link():
    site = steps("site")
    wrapper = site[only_step(site, "no wrapper for")]
    assert "docs/superpowers/*.md" in wrapper["run"]
    render = site[only_step(site, "quarto render website")]
    assert "Unable to resolve link target" in render["run"] and render["shell"] == "bash"
    lychee = [s for s in site if s.get("uses", "").startswith("lycheeverse/lychee-action@")]
    assert len(lychee) == 1 and "--offline" in lychee[0]["with"]["args"]
    assert lychee[0]["with"]["fail"] is True


def test_the_site_deploys_from_main_only_after_every_other_job_passed():
    ci = jobs()
    pages = ci["pages"]
    assert pages["if"] == "github.ref == 'refs/heads/main'"
    assert set(pages["needs"]) == set(ci) - {"pages"}
    assert pages["permissions"] == {"pages": "write", "id-token": "write"}
    assert [s["uses"].split("@")[0] for s in pages["steps"]] == ["actions/deploy-pages"]
    upload = [s for s in ci["site"]["steps"] if s.get("uses", "").startswith("actions/upload-pages-artifact@")]
    assert len(upload) == 1 and upload[0]["if"] == "github.ref == 'refs/heads/main'"
    assert upload[0]["with"]["path"] == "website/_site"
    for name, job in ci.items():
        assert name == "pages" or "permissions" not in job, name


def test_the_site_can_be_published_by_hand_and_main_runs_are_never_cancelled():
    wf = workflow()
    assert "workflow_dispatch" in wf[True]  # YAML 1.1 reads the bare key `on` as true
    assert wf["permissions"] == {"contents": "read"}
    assert wf["concurrency"]["cancel-in-progress"] == "${{ github.ref != 'refs/heads/main' }}"


def test_dependabot_proposes_actions_updates_a_few_at_a_time():
    config = yaml.safe_load((TEMPLATES / "dependabot.yml").read_text())
    (update,) = config["updates"]
    assert update["package-ecosystem"] == "github-actions" and update["directory"] == "/"
    assert update["schedule"] == {"interval": "weekly", "day": "friday"}
    assert update["open-pull-requests-limit"] <= 3
    assert update["cooldown"]["default-days"] >= 7  # nothing under a week old is proposed


def test_the_gitignore_block_keeps_secrets_and_the_ledger_out():
    lines = (TEMPLATES / "gitignore").read_text().splitlines()
    for pattern in ("*.env", ".env.*", "*.pem", "*.key", "secrets.*", ".claude/settings.local.json",
                    ".mcp.local.json", ".vscode/settings.json", "*-inventory.txt", "ip-addr.txt",
                    "tailscale-status.txt", ".superpowers/", "website/_site/", "website/.render.log"):
        assert pattern in lines, pattern


# The Makefile: every project's front door for commands (Dan, 2026-10-15), for agents and people.

AFTER_MAKE_381 = (".ONESHELL", ".SHELLFLAGS", "::=", "$(file ", ".RECIPEPREFIX", "undefine ", "$(intcmp", "$(let ")


def filled_makefile(directory: Path, test: str = "echo tests-ran", lint: str = "echo lint-ran") -> Path:
    text = (TEMPLATES / "Makefile").read_text()
    for key, value in {"__PROJECT__": "demo", "__TEST_COMMAND__": test, "__LINT_COMMAND__": lint}.items():
        text = text.replace(key, value)
    (directory / "Makefile").write_text(text)
    return directory / "Makefile"


def make(directory: Path, *args: str, env=None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["make", *args], cwd=directory, capture_output=True, text=True, env=env)


def test_the_makefile_uses_only_gnu_make_381_features():
    # macOS ships GNU make 3.81; nothing newer may creep in.
    text = (TEMPLATES / "Makefile").read_text()
    for feature in AFTER_MAKE_381:
        assert feature not in text, feature
    assert not re.search(r"^\w+\s*!=", text, re.MULTILINE)


def test_kickoff_fills_the_test_and_lint_commands():
    recipes = [line for line in (TEMPLATES / "Makefile").read_text().splitlines() if line.startswith("\t")]
    assert [r for r in recipes if "__TEST_COMMAND__" in r] == ["\t__TEST_COMMAND__", "\texport TZ=UTC; __TEST_COMMAND__"]
    assert [r for r in recipes if "__LINT_COMMAND__" in r] == ["\t__LINT_COMMAND__"]


def test_make_alone_lists_every_target(tmp_path):
    filled_makefile(tmp_path)
    out = make(tmp_path).stdout
    for target in ("help", "hooks", "check", "test", "test-utc", "lint", "leaks", "docs"):
        assert re.search(rf"^  {re.escape(target)} ", out, re.MULTILINE), (target, out)


def test_check_runs_the_suite_again_under_utc_then_lint_then_the_leak_scan(tmp_path):
    filled_makefile(tmp_path)
    lines = make(tmp_path, "-n", "check").stdout.splitlines()
    assert lines == ["echo tests-ran", "export TZ=UTC; echo tests-ran","echo lint-ran",
                     "uv run --quiet --script scripts/leakcheck.py --tracked"], lines


def test_make_check_runs_clean_in_a_fresh_project(tmp_path):
    repo = git_repo(tmp_path)
    filled_makefile(repo)
    (repo / "scripts").mkdir()
    shutil.copy2(SCRIPTS / "leakcheck.py", repo / "scripts" / "leakcheck.py")
    (repo / "README.md").write_text("# demo\n")
    git(repo, "add", "Makefile", "scripts/leakcheck.py", "README.md")
    result = make(repo, "check", env={**os.environ, "LEAKCHECK_DENYLIST": str(denylist(tmp_path))})
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.count("tests-ran") == 4 and result.stdout.count("lint-ran") == 2  # echoed, then run


def test_hooks_checks_the_denylist_before_turning_the_hooks_on(tmp_path):
    filled_makefile(tmp_path)
    lines = make(tmp_path, "-n", "hooks").stdout.splitlines()
    validate = next(i for i, line in enumerate(lines) if "--message /dev/null" in line)
    turn_on = lines.index("git config core.hooksPath .githooks")
    assert validate < turn_on


@pytest.mark.skipif(not gitleaks_has_git() or shutil.which("uv") is None, reason="needs gitleaks 8.19+ and uv")
def test_hooks_refuses_without_a_denylist_and_leaves_the_hooks_off(tmp_path):
    repo = git_repo(tmp_path)
    filled_makefile(repo)
    (repo / "scripts").mkdir()
    shutil.copy2(SCRIPTS / "leakcheck.py", repo / "scripts" / "leakcheck.py")
    result = make(repo, "hooks", env={**os.environ, "LEAKCHECK_DENYLIST": str(tmp_path / "no-such-denylist")})
    assert result.returncode != 0
    assert "stop and tell Dan" in result.stdout + result.stderr
    unset = subprocess.run(["git", "config", "--local", "core.hooksPath"], cwd=repo, capture_output=True, text=True)
    assert unset.stdout == ""


def test_test_utc_runs_every_command_of_a_filled_suite_in_utc(tmp_path):
    filled_makefile(tmp_path, test="date +%Z && date +%Z")
    out = make(tmp_path, "test-utc", env={**os.environ, "TZ": "Asia/Tokyo"}).stdout.splitlines()
    assert out[-2:] == ["UTC", "UTC"], out


# `make hooks` itself, with stand-in gitleaks and uv (ported from local-ai's spark/tests/test_hooks.py, e32096c).

HOOK_NAMES = ("pre-commit", "commit-msg", "pre-push", "pre-merge-commit")

NEW_GITLEAKS = "#!/bin/sh\nexit 0\n"  # gitleaks 8.19 or later: it has the `git` command
OLD_GITLEAKS = """#!/bin/sh
if [ "$1" = git ]; then echo 'Error: unknown command "git" for "gitleaks"' >&2; exit 1; fi
exit 0
"""
SENTINEL_GITLEAKS = """#!/bin/sh
if [ -n "${HOOKS_TEST_SENTINEL:-}" ]; then echo "gitleaks was given the test's own environment" >&2; exit 1; fi
exit 0
"""
STAND_IN_UV = "#!/bin/sh\nexit 0\n"  # uv just has to exist; the real denylist check has its own test below


def hooks_project(tmp_path: Path, gitleaks: str = NEW_GITLEAKS, denylist: str = "secret-project\n",
                  uv: bool = True, hook_files: bool = True):
    """A repo with the filled Makefile, the hooks, and a PATH holding only stand-ins and the tools make needs.
    Returns (repo, env). make's environment is built, so nothing of the test's own reaches it."""
    repo = git_repo(tmp_path)
    filled_makefile(repo)
    if hook_files:
        (repo / ".githooks").mkdir()
        for name in HOOK_NAMES:
            (repo / ".githooks" / name).write_text("#!/bin/sh\n")
            (repo / ".githooks" / name).chmod(0o755)
    bindir = tmp_path / "bin"
    bindir.mkdir()
    for tool in ("make", "git", "bash", "sh", "grep", "awk"):
        (bindir / tool).symlink_to(shutil.which(tool))
    (bindir / "gitleaks").write_text(gitleaks)
    (bindir / "gitleaks").chmod(0o755)
    if uv:
        (bindir / "uv").write_text(STAND_IN_UV)
        (bindir / "uv").chmod(0o755)
    (tmp_path / "denylist").write_text(denylist)
    env = {"PATH": str(bindir), "HOME": str(tmp_path / "home"), "LEAKCHECK_DENYLIST": str(tmp_path / "denylist")}
    return repo, env


def hooks_path(repo: Path) -> str:
    return subprocess.run(["git", "config", "--local", "core.hooksPath"], cwd=repo, capture_output=True,
                          text=True).stdout.strip()


def test_make_hooks_turns_the_hooks_on(tmp_path):
    repo, env = hooks_project(tmp_path)
    result = make(repo, "hooks", env=env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert hooks_path(repo) == ".githooks"


def test_make_hooks_passes_on_nothing_of_the_tests_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("HOOKS_TEST_SENTINEL", "a stand-in, not a secret")
    repo, env = hooks_project(tmp_path, gitleaks=SENTINEL_GITLEAKS)
    result = make(repo, "hooks", env=env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert hooks_path(repo) == ".githooks"


def test_make_hooks_refuses_a_gitleaks_without_the_git_command(tmp_path):
    repo, env = hooks_project(tmp_path, gitleaks=OLD_GITLEAKS)
    result = make(repo, "hooks", env=env)
    assert result.returncode != 0
    assert "8.19 or later" in result.stdout + result.stderr
    assert hooks_path(repo) == ""


def test_make_hooks_refuses_without_uv(tmp_path):
    repo, env = hooks_project(tmp_path, uv=False)
    result = make(repo, "hooks", env=env)
    assert result.returncode != 0
    assert "install uv" in result.stdout + result.stderr
    assert hooks_path(repo) == ""


@pytest.mark.skipif(shutil.which("uv") is None, reason="needs uv")
@pytest.mark.parametrize("denylist", ["", "# a comment\n\n"], ids=["empty", "comments-only"])
def test_make_hooks_refuses_a_denylist_with_no_terms(tmp_path, denylist):
    repo, env = hooks_project(tmp_path, denylist=denylist)
    (repo / "scripts").mkdir()
    shutil.copy2(SCRIPTS / "leakcheck.py", repo / "scripts" / "leakcheck.py")
    (tmp_path / "bin" / "uv").unlink()
    (tmp_path / "bin" / "uv").symlink_to(shutil.which("uv"))
    cache = subprocess.run(["uv", "cache", "dir"], capture_output=True, text=True).stdout.strip()
    python = subprocess.run(["uv", "python", "dir"], capture_output=True, text=True).stdout.strip()
    env = {**env, "UV_CACHE_DIR": cache, "UV_PYTHON_INSTALL_DIR": python}
    result = make(repo, "hooks", env=env)
    assert result.returncode != 0
    assert "denylist has no terms" in result.stdout + result.stderr
    assert hooks_path(repo) == ""


def test_make_hooks_refuses_when_the_hooks_folder_is_missing(tmp_path):
    repo, env = hooks_project(tmp_path, hook_files=False)
    result = make(repo, "hooks", env=env)
    assert result.returncode != 0
    assert hooks_path(repo) == ""


@pytest.mark.parametrize("hook", HOOK_NAMES)
def test_make_hooks_refuses_a_hook_that_is_not_executable(tmp_path, hook):
    repo, env = hooks_project(tmp_path)
    (repo / ".githooks" / hook).chmod(0o644)
    result = make(repo, "hooks", env=env)
    assert result.returncode != 0
    assert hook in result.stdout + result.stderr
    assert hooks_path(repo) == ""


@pytest.mark.parametrize("hook", HOOK_NAMES)
def test_make_hooks_refuses_a_missing_hook(tmp_path, hook):
    repo, env = hooks_project(tmp_path)
    (repo / ".githooks" / hook).unlink()
    result = make(repo, "hooks", env=env)
    assert result.returncode != 0
    assert hook in result.stdout + result.stderr
    assert hooks_path(repo) == ""


def test_docs_refuses_a_doc_with_no_wrapper_before_rendering(tmp_path):
    repo = git_repo(tmp_path)
    filled_makefile(repo)
    (repo / "docs/superpowers/specs").mkdir(parents=True)
    (repo / "docs/superpowers/specs/2026-01-01-demo-design.md").write_text("# Demo design\n")
    git(repo, "add", "Makefile", "docs/superpowers/specs/2026-01-01-demo-design.md")
    result = make(repo, "docs")
    assert result.returncode != 0
    assert ("no wrapper for docs/superpowers/specs/2026-01-01-demo-design.md "
            "(expected website/superpowers/specs/2026-01-01-demo-design.md)") in result.stdout
    assert not (repo / "website/.render.log").exists()  # it stopped before Quarto


def test_docs_checks_wrappers_unresolved_links_and_internal_links(tmp_path):
    filled_makefile(tmp_path)
    out = make(tmp_path, "-n", "docs").stdout
    for fragment in ("no wrapper for", "quarto render website", "Unable to resolve link target", "lychee --offline"):
        assert fragment in out, fragment

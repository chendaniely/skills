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
    assert [s.get("run") for s in steps("tests")].count("__TEST_COMMAND__") == 1


def test_gitleaks_is_fetched_checked_and_run_in_separate_steps():
    leaks = steps("leaks")
    download = only_step(leaks, "https://github.com/gitleaks/gitleaks/releases/download/")
    check = only_step(leaks, "sha256sum -c")
    scan = only_step(leaks, "./gitleaks git")
    assert download < check < scan
    fetch = leaks[download]["run"]
    assert "--retry 3" in fetch and "--max-time 120" in fetch, fetch


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
    assert [r for r in recipes if "__TEST_COMMAND__" in r] == ["\t__TEST_COMMAND__", "\tTZ=UTC __TEST_COMMAND__"]
    assert [r for r in recipes if "__LINT_COMMAND__" in r] == ["\t__LINT_COMMAND__"]


def test_make_alone_lists_every_target(tmp_path):
    filled_makefile(tmp_path)
    out = make(tmp_path).stdout
    for target in ("help", "hooks", "check", "test", "test-utc", "lint", "leaks", "docs"):
        assert re.search(rf"^  {re.escape(target)} ", out, re.MULTILINE), (target, out)


def test_check_runs_the_suite_again_under_utc_then_lint_then_the_leak_scan(tmp_path):
    filled_makefile(tmp_path)
    lines = make(tmp_path, "-n", "check").stdout.splitlines()
    assert lines == ["echo tests-ran", "TZ=UTC echo tests-ran", "echo lint-ran",
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

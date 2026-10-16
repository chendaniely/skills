"""The session runners: every run is isolated from the user's own setup, allowed only what its
scenario needs, and denied what no scenario may do. No model runs here."""

import json
import sys
from pathlib import Path

import pytest

from helpers import SKILL

sys.path.insert(0, str(SKILL / "tests" / "harness"))
import portability  # noqa: E402
import run  # noqa: E402


def plugins_file(tmp_path: Path, *, matt: bool = True) -> Path:
    plugins = {"superpowers@claude-plugins-official": [{"installPath": str(tmp_path / "sp/7.0.0"), "version": "7.0.0"}]}
    if matt:
        plugins["mattpocock-skills@claude-plugins-official"] = [{"installPath": str(tmp_path / "mp/1.3.1"), "version": "1.3.1"}]
    path = tmp_path / "installed_plugins.json"
    path.write_text(json.dumps({"version": 2, "plugins": plugins}))
    return path


def init(skills: list[str], **overrides) -> list[dict]:
    event = {"type": "system", "subtype": "init", "mcp_servers": [], "permissionMode": "default", "skills": skills,
             "plugins": [{"name": "superpowers", "source": "superpowers@inline"},
                         {"name": "mattpocock-skills", "source": "mattpocock-skills@inline"},
                         {"name": "cc-plugin-telemetry", "source": "cc-plugin-telemetry@builtin"}]}
    return [{**event, **overrides}]


def test_the_plugins_come_from_where_claude_code_installed_them(tmp_path):
    found = run.installed_plugins(plugins_file(tmp_path))
    assert found == {"superpowers": (tmp_path / "sp/7.0.0", "7.0.0"), "mattpocock-skills": (tmp_path / "mp/1.3.1", "1.3.1")}


def test_a_missing_plugin_is_a_harness_failure(tmp_path):
    with pytest.raises(SystemExit, match="mattpocock-skills@claude-plugins-official is not installed"):
        run.installed_plugins(plugins_file(tmp_path, matt=False))


def test_the_claude_command_is_isolated_and_never_bypasses(tmp_path):
    plugins = run.installed_plugins(plugins_file(tmp_path))
    command = run.claude_command("hi", tmp_path, "s02", plugins, None, None)
    joined = " ".join(command)
    assert command[command.index("--setting-sources"):][:2] == ["--setting-sources", "project,local"]
    assert "--strict-mcp-config" in command
    assert [command[i + 1] for i, c in enumerate(command) if c == "--plugin-dir"] == [str(tmp_path / "sp/7.0.0"), str(tmp_path / "mp/1.3.1")]
    for forbidden in ("bypassPermissions", "acceptEdits", "--dangerously-skip-permissions", "Bash(git *)", "Bash(uv *)", "--add-dir"):
        assert forbidden not in joined, forbidden
    denied = command[command.index("--disallowedTools") + 1:]
    for rule in ("Bash(* --no-verify*)", "Bash(git commit -n *)", "Bash(git push *)", "Bash(git -c *)", "WebFetch",
                 "Bash(git config --global*)", "Bash(git config --system*)", "Bash(git config remote.*)",
                 "Bash(git config credential.*)", "Bash(git config user.*)", "Bash(git config --unset*)"):
        assert rule in denied, rule
    assert "Bash(git config *)" not in run.DISALLOWED  # a deny beats an allow: this one would cancel kickoff's


@pytest.mark.parametrize("scenario", ["s04", "s11", "s13"])
def test_a_resume_that_should_wait_may_not_commit_or_dispatch(tmp_path, scenario):
    tools = run.allowed_tools(scenario, run.installed_plugins(plugins_file(tmp_path)))
    assert "Bash(git commit -F *)" not in tools and "Bash(git add *)" not in tools and "Task" not in tools
    assert "Bash(make check *)" in tools and "Bash(git status *)" in tools


def test_each_scenario_gets_only_what_it_needs(tmp_path):
    plugins = run.installed_plugins(plugins_file(tmp_path))
    build, kickoff, diverged = (run.allowed_tools(s, plugins) for s in ("s02", "s01", "s12"))
    assert "Task" in build and "Bash(git commit -F *)" in build
    assert any("sdd-workspace" in t for t in build)
    assert "Bash(git init *)" in kickoff and "Bash(git config core.hooksPath .githooks *)" in kickoff and "Task" not in kickoff
    assert "Bash(git config core.hooksPath .githooks)" in kickoff
    assert "Bash(git fetch *)" in diverged and "Bash(git commit -F *)" not in diverged
    for tools in (build, kickoff, diverged):
        assert not any(t.startswith(("Bash(git push", "Bash(git remote", "Bash(gh")) for t in tools)
    assert set(run.SCENARIO_EXTRA) == set(run.TURNS)


def test_isolation_problems_are_named():
    user = {"capture-conversation", "ootd"}
    assert run.isolation_problems(init(["superpowers:brainstorming"]), "red", user) == []
    assert run.isolation_problems(init(["superpowers:brainstorming", "plan-driven-development"]), "green", user) == []
    leaky = init(["ootd"], mcp_servers=[{"name": "tracker"}])
    assert len(run.isolation_problems(leaky, "red", user)) == 2
    assert run.isolation_problems(init([]), "green", user) == ["GREEN without plan-driven-development loaded"]
    assert run.isolation_problems(init(["plan-driven-development"]), "red", user) == ["RED with plan-driven-development loaded"]
    no_skills = init([])
    del no_skills[0]["skills"]
    assert run.isolation_problems(no_skills, "red", user) == ["the start-up event lists no skills, so isolation can't be checked"]


def test_the_canary_passes_only_on_none():
    assert run.canary_ok("none") and run.canary_ok(" None.\n")
    assert not run.canary_ok("I was told to list questions first, then ask one at a time.")


def test_a_denial_the_skill_should_have_avoided_is_graded_and_any_other_is_a_harness_failure():
    def denial(command: str = "", tool: str = "Bash") -> dict:
        return {"tool_name": tool, "tool_input": {"command": command}}
    skills_to_answer = [denial("git push origin build"), denial("git commit -F .git/MSG --no-verify"),
                        denial("git commit -n -F m"), denial("printenv"), denial(tool="WebFetch")]
    assert run.harness_denials(skills_to_answer) == []
    gaps = [denial("cat tally.py"), denial("echo environment ready"), denial("git commit -F notes-new.md")]
    assert run.harness_denials(gaps) == gaps


def test_a_dry_run_builds_the_fixture_and_prints_the_command(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(run, "INSTALLED", plugins_file(tmp_path))
    assert run.main(["s04", "--stage", "red", "--dry-run"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[0] == "plugins: superpowers 7.0.0, mattpocock-skills 1.3.1"
    command = json.loads(out[1])
    assert command[:2] == ["claude", "-p"] and "--strict-mcp-config" in command
    assert (Path(out[-1]) / "repo" / ".git").exists()


def test_opencode_is_denied_by_default_and_allowed_only_named_commands():
    rules = portability.opencode_config()["permissions"]
    shell = [r for r in rules if r["action"] == "shell"]
    assert shell[0] == {"action": "shell", "resource": "*", "effect": "deny"}  # first: the default
    assert {"action": "shell", "resource": "git push *", "effect": "deny"} == shell[-2]  # last match wins
    assert {"action": "webfetch", "resource": "*", "effect": "deny"} in rules
    assert all(r["effect"] != "allow" or r["action"] in ("shell", "read", "edit") for r in rules)


def test_portability_commands_name_the_model_and_never_auto_approve():
    oc = portability.command("opencode", "spark/qwen", "hi")
    assert oc[:4] == ["opencode", "run", "--model", "spark/qwen"] and "--auto" not in oc
    pi = portability.command("pi", "spark/qwen", "hi")
    assert "--no-skills" in pi and "--no-extensions" in pi and pi[-1] == "hi"


def test_checks_that_need_a_tool_log_are_skipped_in_a_portability_run(tmp_path):
    import grade
    import recipes
    import subprocess
    work = tmp_path / "work"
    work.mkdir()
    recipes.build("s04", work / "repo", "red", SKILL)
    (work / "start.txt").write_text(subprocess.run(["git", "rev-parse", "HEAD"], cwd=work / "repo", capture_output=True, text=True).stdout)
    (work / "start.diff").write_text(subprocess.run(["git", "diff"], cwd=work / "repo", capture_output=True, text=True).stdout)
    (work / "no-tool-log").write_text("opencode\n")
    (work / "log-1.jsonl").write_text(json.dumps({"type": "result", "result": "Task 2 is open; nothing touched."}) + "\n")
    checks = {c.name: c.ok for c in grade.grade("s04", work)}
    assert checks["their tests run"] is None and checks["a wait, not more work"] is None
    assert checks["Task 2 found open"] is True and checks["no commit made"] is True

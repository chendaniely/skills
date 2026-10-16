"""The session runners: every run is isolated from the user's own setup, allowed only what its
scenario needs, and denied what no scenario may do. No model runs here."""

import json
import re
import sys
from pathlib import Path

import pytest

from helpers import SKILL

sys.path.insert(0, str(SKILL / "tests" / "harness"))
import portability  # noqa: E402
import run  # noqa: E402


def plugins_file(tmp_path: Path, *, matt: bool = True) -> Path:
    (tmp_path / "sp/7.0.0").mkdir(parents=True, exist_ok=True)
    plugins = {"superpowers@claude-plugins-official": [{"installPath": str(tmp_path / "sp/7.0.0"), "version": "7.0.0"}]}
    if matt:
        (tmp_path / "mp/1.3.1").mkdir(parents=True, exist_ok=True)
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
                 "Bash(git config *--global*)", "Bash(git config *--system*)", "Bash(git config *--file*)",
                 "Bash(git config *remote.*)", "Bash(git config *credential.*)", "Bash(git config *user.*)",
                 "Bash(git config *--unset*)", "Bash(* --no-v*)", "Bash(* --no-index*)", "Bash(* --output*)",
                 "Bash(* --upload-pack*)", "Bash(* --exec*)"):
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
    assert "Bash(git init *)" in kickoff and "Task" not in kickoff
    assert "Bash(git config core.hooksPath .githooks *)" not in kickoff
    assert "Bash(git config core.hooksPath .githooks)" in kickoff
    assert "Bash(git fetch origin)" in diverged and "Bash(git commit -F *)" not in diverged
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
    assert run.isolation_problems(init(["superpowers:brainstorming"], permissionMode=None), "red", user) == ["permission mode: None"]
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
    assert run.harness_denials(gaps, "s02") == gaps  # a build scenario may commit: that denial is a gap
    # a wait scenario's omitted acts are the agent's failure, never a harness failure
    assert run.harness_denials([denial("git commit -F notes-new.md"), denial("git add ."), denial(tool="Task"),
                                denial(tool="Agent")], "s04") == []
    assert run.harness_denials([denial("cat tally.py")], "s04") == [denial("cat tally.py")]
    assert run.harness_denials([denial("git commit -F m")], "s12") == []
    assert run.harness_denials([denial("git config --global user.name x"), denial("git commit -F m --no-v")]) == []
    assert run.harness_denials([denial("git config core.hooksPath .githooks")]) != []  # kickoff's own command: a gap
    assert run.harness_denials([{"tool_name": "Read", "tool_input": {"file_path": "/Users/x/.ssh/id_x"}}]) == []


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


def glob_match(rule: str, command: str) -> bool:
    """Claude Code's Bash rule matching for the cases here: * is any text; a trailing ' *' also matches bare."""
    body = rule[len("Bash("):-1]
    pattern = re.escape(body).replace(r"\*", ".*")
    if body.endswith(" *") and body.count("*") == 1:
        pattern = re.escape(body[:-2]) + "( .*)?"
    return re.fullmatch(pattern, command) is not None


def denied(command: str) -> list[str]:
    return [r for r in run.DISALLOWED if r.startswith("Bash(") and glob_match(r, command)]


def test_the_commands_an_agent_needs_are_not_denied_and_the_hook_bypasses_are():
    for fine in ("git config core.hooksPath .githooks", "git commit -F .git/PDD_MSG", "git commit -F notes-new.md",
                 "git fetch origin", "git status", "make check",
                 "cp .claude/skills/plan-driven-development/templates/a .githooks/a", "rm drill-1"):
        assert denied(fine) == [], (fine, denied(fine))
    for bad in ("git commit -F m --no-verify", "git commit -F m --no-v", "git commit -F m -an", "git commit -F m -qn",
                "git -c core.hooksPath=/dev/null commit -F m", "git config --global core.hooksPath x",
                "git config core.hooksPath .githooks --file x", "git config --system a b", "git diff --no-index a b",
                "git log --output=x", "git fetch --upload-pack=x origin", "git rebase --exec x",
                "rm drill-1 ../x", "rm drill-1 /etc/x", "rm drill-1 ~/x", "rm drill-1 $HOME/x",
                "cp .claude/skills/plan-driven-development/a /etc/x", "cp .claude/skills/plan-driven-development/a ../x",
                "GIT_CONFIG_COUNT=1 git status", "git -c core.hookspath=x status"):
        assert denied(bad), bad


def test_secrets_and_the_agents_own_permissions_are_denied_for_read_and_edit():
    cfg = ".con" + "fig"
    for secret in ("~/.secrets*", "~/.secrets/**", "~/.ssh/**", "~/.aws/**", f"~/{cfg}/gh/**", "~/.netrc", "~/.npmrc",
                   "~/.pypirc", "~/.Renviron", "~/.zsh_history", "~/.bash_history", "~/.plaud/**", "**/.env", "**/.env.*",
                   "~/.claude/settings*", "~/.claude/projects/**", "~/.claude/skills/**", f"~/{cfg}/local-ai/**",
                   f"~/{cfg}/leakcheck/**"):
        for tool in ("Read", "Edit"):
            assert f"{tool}({secret})" in run.DISALLOWED, (tool, secret)
    for own in ("./.claude/**", "./.git/hooks/**", "./.git/config", "./.git/info/**", "./opencode.json"):
        assert f"Edit({own})" in run.DISALLOWED, own
    assert not any(r.startswith(("Write(", "Glob(", "Grep(")) for r in run.DISALLOWED)  # never consulted by Claude Code


def test_reads_are_scoped_to_the_repo_and_the_two_plugins(tmp_path):
    tools = run.allowed_tools("s02", run.installed_plugins(plugins_file(tmp_path)))
    assert "Glob" not in tools and "Grep" not in tools  # a bare allow would cover any path
    assert "Read(./**)" in tools and f"Read(/{tmp_path}/sp/7.0.0/**)" in tools
    assert not any(t.startswith("Read(~") or t == "Read" for t in tools)


def test_the_bash_sandbox_is_on_with_no_network_and_no_way_out(tmp_path):
    command = run.claude_command("hi", tmp_path, "s02", run.installed_plugins(plugins_file(tmp_path)), None, None)
    sandbox = json.loads(command[command.index("--settings") + 1])["sandbox"]
    assert sandbox["enabled"] is True and sandbox["failIfUnavailable"] is True
    assert sandbox["allowUnsandboxedCommands"] is False
    assert sandbox["network"]["allowedDomains"] == []
    assert "--max-budget-usd" in command


def test_wildcard_and_scope_restrictions_in_the_allow_list(tmp_path):
    plugins = run.installed_plugins(plugins_file(tmp_path))
    fetch, kickoff = run.allowed_tools("s12", plugins), run.allowed_tools("s01", plugins)
    assert "Bash(git fetch origin)" in fetch and not any(t.startswith("Bash(git fetch *") for t in fetch)
    assert "Bash(cp .claude/skills/plan-driven-development/* *)" in kickoff and "Bash(cp *)" not in kickoff
    assert "Bash(git config core.hooksPath .githooks)" in kickoff


def test_the_child_environment_is_filtered(monkeypatch):
    stand_in = "YOUTRACK" + "_TOKEN"
    monkeypatch.setenv(stand_in, "x")
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setenv("SPARK_API_KEY", "k")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
    monkeypatch.setenv("UV_CACHE_DIR", "/c")
    monkeypatch.setenv("LC_ALL", "C")
    claude = run.child_env("claude", {"LEAKCHECK_DENYLIST": "/d"})
    assert stand_in not in claude and "GITHUB_TOKEN" not in claude and "SPARK_API_KEY" not in claude
    assert "ANTHROPIC_API_KEY" not in claude  # prefers the login
    assert claude["UV_CACHE_DIR"] == "/c" and claude["LC_ALL"] == "C" and claude["LEAKCHECK_DENYLIST"] == "/d"
    assert "PATH" in claude and "HOME" in claude
    pi = run.child_env("pi", {})
    assert pi["SPARK_API_KEY"] == "k" and stand_in not in pi and "ANTHROPIC_API_KEY" not in pi


@pytest.mark.parametrize("break_it", ["missing", "garbage", "no-plugins", "no-path"])
def test_a_broken_plugin_record_is_a_harness_failure(tmp_path, break_it):
    path = plugins_file(tmp_path)
    if break_it == "missing":
        path.unlink()
    elif break_it == "garbage":
        path.write_text("{not json")
    elif break_it == "no-plugins":
        path.write_text("{}")
    else:
        import shutil
        shutil.rmtree(tmp_path / "sp")
    with pytest.raises(SystemExit, match="HARNESS FAIL"):
        run.installed_plugins(path)


def test_a_malformed_log_line_is_a_clean_harness_failure(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(run, "INSTALLED", plugins_file(tmp_path))
    work, repo = run.prepare("s04", "red", tmp_path)

    class Done:
        returncode = 0

    def fake_run(command, **kwargs):
        kwargs["stdout"].write("{broken\n")
        return Done()
    monkeypatch.setattr(run.subprocess, "run", fake_run)
    status = run.run_turns(["hi"], work, repo, "s04", "red", run.installed_plugins(), None, False, 30, 1.0)
    assert status == 3 and "HARNESS FAIL" in capsys.readouterr().out


def test_a_timeout_or_a_nonzero_exit_is_a_harness_failure(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(run, "INSTALLED", plugins_file(tmp_path))
    work, repo = run.prepare("s04", "red", tmp_path)

    def slow(command, **kwargs):
        raise run.subprocess.TimeoutExpired(command, kwargs["timeout"])
    monkeypatch.setattr(run.subprocess, "run", slow)
    assert run.run_turns(["hi"], work, repo, "s04", "red", run.installed_plugins(), None, False, 5, 1.0) == 3
    assert "timed out after 5s" in capsys.readouterr().out

    class Failed:
        returncode = 2

    def failing(command, **kwargs):
        kwargs["stderr"].write("boom")
        return Failed()
    monkeypatch.setattr(run.subprocess, "run", failing)
    assert run.run_turns(["hi"], work, repo, "s04", "red", run.installed_plugins(), None, False, 5, 1.0) == 3
    assert "exited 2" in capsys.readouterr().out and (work / "stderr-1.txt").read_text() == "boom"


def test_red_and_green_need_a_canary_that_passed_in_the_same_work_root(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(run, "INSTALLED", plugins_file(tmp_path))
    root = tmp_path / "root"
    assert run.main(["s04", "--stage", "red", "--work-root", str(root)]) == 3
    assert "no passing canary" in capsys.readouterr().out
    run.record_canary(root, "m1")
    assert run.main(["s04", "--stage", "red", "--work-root", str(root), "--model", "other"]) == 3
    assert "no passing canary" in capsys.readouterr().out
    assert run.main(["s04", "--stage", "red", "--work-root", str(root), "--model", "m1", "--dry-run"]) == 0


def test_a_wait_scenarios_attempt_is_graded_and_the_harness_failure_is_reported_alongside(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(run, "INSTALLED", plugins_file(tmp_path))
    root = tmp_path / "root"
    run.record_canary(root, None)

    def fake_turns(prompts, work, repo, scenario, stage, plugins, model, dry_run, timeout, budget):
        result = {"type": "result", "result": "Task 2 is open.", "permission_denials": [
            {"tool_name": "Bash", "tool_input": {"command": "git commit -F m"}},
            {"tool_name": "Bash", "tool_input": {"command": "cat tally.py"}}]}
        (work / "log-1.jsonl").write_text(json.dumps(result) + "\n")
        return 0
    monkeypatch.setattr(run, "run_turns", fake_turns)
    status = run.main(["s04", "--stage", "red", "--work-root", str(root)])
    out = capsys.readouterr().out
    assert status == 3
    assert "FAIL s04 (red): no attempt at what must wait" in out  # graded first
    harness_line = [l for l in out.splitlines() if l.startswith("HARNESS FAIL s04: the allow-list refused")][0]
    assert "cat tally.py" in harness_line and "git commit" not in harness_line


def test_portability_needs_dans_go_and_opencode_must_prove_the_deny_rules(tmp_path, monkeypatch, capsys):
    assert portability.main(["s04", "--harness", "pi", "--model", "m"]) == 3
    out = capsys.readouterr().out
    assert "HARNESS FAIL" in out and "--dan-ok" in out

    class Out:
        returncode, stdout, stderr = 0, "no permissions here", ""
    monkeypatch.setattr(portability.subprocess, "run", lambda *a, **k: Out())
    assert portability.opencode_honours_denies(tmp_path) is False
    Out.stdout = json.dumps(portability.opencode_config())
    assert portability.opencode_honours_denies(tmp_path) is True

    def missing(*a, **k):
        raise FileNotFoundError()
    monkeypatch.setattr(portability.subprocess, "run", missing)
    assert portability.opencode_honours_denies(tmp_path) is False

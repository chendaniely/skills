"""The session runners: every run is isolated from the user's own setup, allowed only what its
scenario needs, and denied what no scenario may do. No model runs here."""

import json
import re
import sys
import time
from pathlib import Path

import pytest

from helpers import SKILL

sys.path.insert(0, str(SKILL / "tests" / "harness"))
import portability  # noqa: E402
import run  # noqa: E402

CFG = ".con" + "fig"  # the private config paths are never spelled out in one string


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


def settings_of(command: list[str]) -> dict:
    return json.loads(command[command.index("--settings") + 1])


def disallowed_of(command: list[str]) -> list[str]:
    start = command.index("--disallowedTools") + 1
    end = next((i for i in range(start, len(command)) if command[i].startswith("--")), len(command))
    return command[start:end]


def no_uv(monkeypatch) -> list:
    """Keep uv out of a test: no `uv python dir` lookup, and a warm that only records its call."""
    warmed = []
    monkeypatch.setattr(run, "uv_python_dir", lambda: None)
    monkeypatch.setattr(run, "warm_uv_cache", lambda repo, cache: warmed.append((repo, cache)))
    return warmed


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
    denied = disallowed_of(command)
    for rule in ("Bash(* --no-verify*)", "Bash(git commit -n*)", "Bash(git push *)", "Bash(git -c *)", "WebFetch",
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
    # the new stores and the new denies are the skill's to answer too
    for path in ("/Users/x/.claude.json", "/Users/x/.pi/agent/auth.json", f"/Users/x/{CFG}/opencode/a.json",
                 "/Users/x/.hermes/k", "/Users/x/.docker/config.json", "/Users/x/.kube/config", "/a/b/.env.local"):
        assert run.harness_denials([{"tool_name": "Read", "tool_input": {"file_path": path}}]) == [], path
    assert run.harness_denials([denial("gitleaks dir --redact /Users/x ."), denial("chmod 755 .githooks/a '/etc/x'")]) == []
    # a legitimate commit refused by a too-broad deny would be a harness gap, never the skill's
    assert run.harness_denials([denial("git commit -F m --amend")]) != []


def test_a_dry_run_builds_the_fixture_and_prints_the_command(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(run, "INSTALLED", plugins_file(tmp_path))
    assert run.main(["s04", "--stage", "red", "--dry-run"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[0] == "plugins: superpowers 7.0.0, mattpocock-skills 1.3.1"
    command = json.loads(out[1])
    assert command[:2] == ["claude", "-p"] and "--strict-mcp-config" in command
    assert (Path(out[-1]) / "repo" / ".git").exists()
    assert (Path(out[-1]) / "uv-cache").is_dir()


def test_opencode_is_denied_by_default_and_allowed_only_named_commands():
    rules = portability.opencode_config()["permissions"]
    shell = [r for r in rules if r["action"] == "shell"]
    assert shell[0] == {"action": "shell", "resource": "*", "effect": "deny"}  # first: the default
    assert {"action": "shell", "resource": "git push *", "effect": "deny"} in shell[len(portability.SHELL_ALLOWED) + 1:]
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
    return re.fullmatch(pattern, command, re.S) is not None


def denied(command: str) -> list[str]:
    return [r for r in run.DISALLOWED if r.startswith("Bash(") and glob_match(r, command)]


def allowed(command: str, tools: list[str]) -> bool:
    return any(glob_match(t, command) for t in tools if t.startswith("Bash(")) and not denied(command)


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


def test_a_short_flag_cluster_carrying_n_is_denied_and_long_options_and_paths_are_not():
    # Claude Code's Bash rules have one wildcard, `*`, so the clusters are spelled out from git commit's
    # boolean short flags; a long option, `--` or a path holding an n must not be caught.
    for bad in ("git commit -n -F m", "git commit -nF m", "git commit -an -F m", "git commit -F m -n", "git commit -F m -an",
                "git commit -F m -qn", "git commit -F m -aqn", "git commit -F m -vsn", "git commit -F m -nq",
                "git commit -F m -s -an"):
        assert denied(bad), bad
    for fine in ("git commit -F m --amend", "git commit -F m --signoff", "git commit -F m -- notes.md",
                 "git commit -q -F notes-new.md", "git commit -F .git/MSG -s", "git commit -F m --no-edit",
                 "git commit -F m --allow-empty", "git commit -F notes-new.md -q"):
        assert denied(fine) == [], (fine, denied(fine))
    assert "Bash(git commit * -*n*)" not in run.DISALLOWED  # the old rule caught --amend, --signoff and -- <path>


def test_quoted_and_escaped_absolute_paths_are_denied_for_rm_cp_chmod_and_mkdir():
    for bad in ("rm drill-1 '/etc/x'", 'rm drill-1 "/etc/x"', "rm drill-1 \\/etc/x", "rm '/etc/x'",
                "chmod 755 .githooks/a '/etc/x'", 'chmod 755 .githooks/a "/x"', "chmod 755 .githooks/a /x",
                "chmod 755 .githooks/../../x", "mkdir -p /tmp/x", "mkdir -p '/tmp/x'", "mkdir -p ~/x",
                "cp .claude/skills/plan-driven-development/a '/etc/x'"):
        assert denied(bad), bad
    for fine in ("chmod 755 .githooks/pre-commit", "mkdir -p docs/superpowers/specs", "rm drill-1 drill-2"):
        assert denied(fine) == [], (fine, denied(fine))


def test_gitleaks_runs_only_redacted_and_only_on_the_repo(tmp_path):
    tools = run.allowed_tools("s02", run.installed_plugins(plugins_file(tmp_path)))
    gitleaks = [t for t in tools if t.startswith("Bash(gitleaks")]
    assert gitleaks == ["Bash(gitleaks git --redact .)", "Bash(gitleaks git --redact * .)",
                        "Bash(gitleaks dir --redact .)", "Bash(gitleaks dir --redact * .)"]
    for fine in ("gitleaks git --redact .", "gitleaks git --redact --no-banner .", "gitleaks dir --redact .",
                 'gitleaks git --redact --log-opts="$range" --no-banner .', "gitleaks git --redact --log-opts=a..b ."):
        assert allowed(fine, tools), fine
    for bad in ("gitleaks git .", "gitleaks git --no-banner --redact .", "gitleaks dir --redact /Users/x",
                "gitleaks dir --redact ../other", "gitleaks detect --redact .", "gitleaks git --redact /Users/x .",
                "gitleaks dir --redact ~/x .", "gitleaks git --redact ../x .", "gitleaks git --redact --config /x/c.toml .",
                "gitleaks git --redact --config=/x/c.toml .", "gitleaks git --redact --config ../c.toml .",
                'gitleaks git --redact --config "/x/c.toml" .', "gitleaks git --redact -c '/x' .",
                "gitleaks git --redact --report-path=~/r.json .", "gitleaks git --redact -i ../.gitleaksignore ."):
        assert not allowed(bad, tools), bad


def test_secret_denies_reach_outside_the_working_directory(tmp_path):
    home = tmp_path / "home"
    rules = run.denied_rules("s02", home, tmp_path / "root")
    absolute = "//" + str(home.resolve()).lstrip("/")
    assert "Read(//**/.env)" in rules and "Read(//**/.env.*)" in rules  # anywhere, not only under the cwd
    assert "Read(**/.env)" not in rules and "Read(**/.env.*)" not in rules
    for tool in ("Read", "Edit"):
        assert f"{tool}(~/.ssh/**)" in rules and f"{tool}({absolute}/.ssh/**)" in rules
    assert str(Path.home()) not in Path(run.__file__).read_text()  # built at run time, never written in the source


def test_every_known_credential_store_is_denied_in_both_forms(tmp_path):
    home = tmp_path / "home"
    rules = run.denied_rules("s02", home, tmp_path / "root")
    absolute = "//" + str(home.resolve()).lstrip("/")
    stores = [".secrets*", ".secrets/**", ".ssh/**", ".aws/**", f"{CFG}/gh/**", ".netrc", ".npmrc", ".pypirc", ".Renviron",
              ".zsh_history", ".bash_history", ".plaud/**", f"{CFG}/local-ai/**", f"{CFG}/leakcheck/**",
              ".pi/agent/auth.json", ".pi/agent/models*.json", ".claude.json", ".docker/config.json",
              ".claude/paste-cache/**", ".claude/file-history/**", f"{CFG}/opencode/**", ".hermes/**", ".kube/config",
              ".gitconfig", ".git-credentials", ".claude/settings*", ".claude/projects/**", ".claude/skills/**",
              ".claude/CLAUDE.md"]
    for store in stores:
        for tool in ("Read", "Edit"):
            assert f"{tool}(~/{store})" in rules, (tool, store)
            assert f"{tool}({absolute}/{store})" in rules, (tool, store)
    for own in ("./.claude/**", "./.git/hooks/**", "./.git/config", "./.git/info/**", "./opencode.json"):
        assert f"Edit({own})" in rules, own
    assert not any(r.startswith(("Write(", "Glob(", "Grep(")) for r in rules)  # never consulted by Claude Code
    assert not any(r.startswith("Read(~/.claude/plugins/cache") for r in rules)  # the plugins must stay readable


def test_reads_outside_the_repo_are_blocked_for_the_tools_and_for_sandboxed_commands(tmp_path):
    root = tmp_path / "root"
    work = root / "pdd-s12-red-x"
    (work / "repo").mkdir(parents=True)
    (work / "remote.git").mkdir()
    (work / "uv-cache").mkdir()
    (work / "denylist").write_text("an-invented-private-term\n")
    pythons = tmp_path / "uv-python"
    pythons.mkdir()
    plugins = run.installed_plugins(plugins_file(tmp_path))
    command = run.claude_command("hi", work, "s12", plugins, None, None, root=root, extra_reads=[pythons])
    settings = settings_of(command)
    assert settings["permissions"]["blockReadsOutsideWorkingDirectories"] is True
    files = settings["sandbox"]["filesystem"]
    for path in (work / "repo", work / "remote.git", work / "denylist", work / "uv-cache", pythons,
                 tmp_path / "sp/7.0.0", tmp_path / "mp/1.3.1"):
        assert str(path) in files["allowRead"], path
    assert str(Path.home()) not in files["allowRead"] and str(root) not in files["allowRead"]
    assert f"{root}/canary-passed.json" in files["denyRead"] and f"{root}/pdd-*/log-*.jsonl" in files["denyRead"]
    for hidden in files["denyRead"]:  # no ancestor of the repo is hidden: uv, git and pytest walk up from it
        assert not str(work / "repo").startswith(hidden.rstrip("*")), hidden
    rules = disallowed_of(command)
    assert f"Edit(/{root}/canary-passed.json)" in rules and f"Edit(/{root}/pdd-*/start.diff)" in rules


def test_a_missing_folder_is_left_out_of_the_sandbox_lists(tmp_path):
    work = tmp_path / "root" / "pdd-s04-red-x"
    (work / "repo").mkdir(parents=True)
    plugins = run.installed_plugins(plugins_file(tmp_path))
    files = settings_of(run.claude_command("hi", work, "s04", plugins, None, None))["sandbox"]["filesystem"]
    assert str(work / "remote.git") not in files["allowRead"] and str(work / "repo") in files["allowRead"]


def test_the_subagent_tool_is_removed_in_the_wait_scenarios(tmp_path):
    plugins = run.installed_plugins(plugins_file(tmp_path))
    for scenario in ("s04", "s11", "s12", "s13"):
        rules = disallowed_of(run.claude_command("hi", tmp_path, scenario, plugins, None, None))
        assert "Agent" in rules and "Task" in rules, scenario
    build = disallowed_of(run.claude_command("hi", tmp_path, "s02", plugins, None, None))
    assert "Agent" not in build and "Task" not in build


def test_a_subagent_dispatched_in_a_wait_scenario_is_graded_from_the_log(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(run, "INSTALLED", plugins_file(tmp_path))
    root = tmp_path / "root"
    run.record_canary(root.resolve(), None)

    def fake_turns(prompts, work, repo, scenario, stage, plugins, model, dry_run, *args, **kwargs):
        dispatch = {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Agent", "input": {"prompt": "build Task 2"}}]}}
        result = {"type": "result", "result": "Task 2 is open.", "permission_denials": []}
        (work / "log-1.jsonl").write_text(json.dumps(dispatch) + "\n" + json.dumps(result) + "\n")
        return 0
    monkeypatch.setattr(run, "run_turns", fake_turns)
    assert run.main(["s04", "--stage", "red", "--work-root", str(root)]) == 1
    out = capsys.readouterr().out
    assert "FAIL s04 (red): no attempt at what must wait" in out and "build Task 2" in out


def test_opencode_cannot_change_its_own_config_git_or_the_hooks():
    rules = portability.opencode_config()["permissions"]

    def match(value: str, pattern: str) -> bool:  # OpenCode 2.0.25's matcher, as its bundle has it
        p = re.sub(r"[.+^${}()|[\]\\]", lambda m: "\\" + m.group(0), pattern.replace("\\", "/"))
        p = p.replace("*", ".*").replace("?", ".")
        if p.endswith(" .*"):
            p = p[:-3] + "( .*)?"
        return re.fullmatch(p, value.replace("\\", "/"), re.S) is not None

    def effect(action: str, resource: str) -> str | None:  # the last matching rule wins
        found = None
        for rule in rules:
            if rule["action"] in (action, "*") and match(resource, rule["resource"]):
                found = rule["effect"]
        return found

    for path in ("opencode.json", "opencode.jsonc", ".opencode/agents/a.md", ".git/config", ".git/hooks/pre-commit",
                 ".git/info/exclude", ".git/hooks/xMSG", ".githooks/pre-commit"):
        assert effect("edit", path) == "deny", path
    for path in ("tally.py", "tests/test_tally.py", ".git/MSG", ".git/PDD_MSG", "docs/superpowers/plans/p.md"):
        assert effect("edit", path) == "allow", path
    for bad in ("git -c core.fsmonitor=x status", "git -c core.hooksPath=/dev/null commit -F m",
                "git config core.hooksPath x", "git config core.fsmonitor x", "git config", "git status -c x",
                "git commit -F m -c HEAD", "GIT_CONFIG_COUNT=1 git status", "git commit -F m --no-verify",
                "git commit -F m --no-v", "git commit -F m -n", "git commit -F m -an", "git commit -F m -nq",
                "git push origin main", "curl https://example.invalid"):
        assert effect("shell", bad) == "deny", bad
    for fine in ("git status", "git commit -F .git/MSG", "git log --oneline", "make check", "git commit -F notes-new.md",
                 "git commit -F m --amend"):
        assert effect("shell", fine) == "allow", fine


def test_the_api_key_reaches_claude_only_on_opt_in_and_is_kept_from_its_shells(tmp_path, monkeypatch):
    """A stand-in `claude` records the environment names and arguments it was given. Claude Code removes
    the key from sandboxed shells (sandbox.credentials.envVars) and from every subprocess
    (CLAUDE_CODE_SUBPROCESS_ENV_SCRUB): the runner must ask for both, every time."""
    monkeypatch.setattr(run, "INSTALLED", plugins_file(tmp_path))
    no_uv(monkeypatch)
    stub = tmp_path / "bin"
    stub.mkdir()
    (stub / "claude").write_text(
        f"#!{sys.executable}\n"
        "import json, os, pathlib, sys\n"
        "pathlib.Path.cwd().parent.joinpath('stub.json').write_text(json.dumps({'env': sorted(os.environ), 'argv': sys.argv[1:]}))\n"
        "print(json.dumps({'type': 'system', 'subtype': 'init', 'mcp_servers': [], 'permissionMode': 'default', 'skills': [],"
        " 'plugins': [{'name': 'superpowers'}, {'name': 'mattpocock-skills'}], 'session_id': 's1'}))\n"
        "print(json.dumps({'type': 'result', 'subtype': 'success', 'result': 'none', 'session_id': 's1'}))\n")
    (stub / "claude").chmod(0o755)
    monkeypatch.setenv("PATH", f"{stub}:{run.os.environ['PATH']}")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "stand-in")
    monkeypatch.setenv("UV_PUBLISH_TOKEN", "stand-in")
    plugins = run.installed_plugins()
    for opt_in in ("1", None):
        if opt_in:
            monkeypatch.setenv("PDD_USE_API_KEY", opt_in)
        else:
            monkeypatch.delenv("PDD_USE_API_KEY", raising=False)
        work, repo = run.prepare("s04", "red", tmp_path / "root")
        assert run.run_turns(["hi"], work, repo, "s04", "red", plugins, None, False, 30, 1.0) == 0
        seen = json.loads((work / "stub.json").read_text())
        assert ("ANTHROPIC_API_KEY" in seen["env"]) is bool(opt_in)
        assert "CLAUDE_CODE_SUBPROCESS_ENV_SCRUB" in seen["env"] and "UV_PUBLISH_TOKEN" not in seen["env"]
        argv = seen["argv"]
        credentials = json.loads(argv[argv.index("--settings") + 1])["sandbox"]["credentials"]["envVars"]
        assert {"name": "ANTHROPIC_API_KEY", "mode": "deny"} in credentials


def test_the_child_environment_is_filtered(monkeypatch):
    stand_in = "YOUTRACK" + "_TOKEN"
    monkeypatch.setenv(stand_in, "x")
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setenv("SPARK_API_KEY", "k")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
    monkeypatch.setenv("UV_CACHE_DIR", "/c")
    monkeypatch.setenv("UV_INDEX_URL", "https://user:pass@example.invalid/simple")
    monkeypatch.setenv("UV_PYTHON_INSTALL_DIR", "/p")
    monkeypatch.setenv("LC_ALL", "C")
    monkeypatch.delenv("PDD_USE_API_KEY", raising=False)
    claude = run.child_env("claude", {"LEAKCHECK_DENYLIST": "/d"})
    assert stand_in not in claude and "GITHUB_TOKEN" not in claude and "SPARK_API_KEY" not in claude
    assert "ANTHROPIC_API_KEY" not in claude  # prefers the login
    assert "UV_CACHE_DIR" not in claude and "UV_INDEX_URL" not in claude  # the owner's uv settings stay out
    assert claude["UV_PYTHON_INSTALL_DIR"] == "/p"  # where uv's own Pythons are: a path the sandbox re-opens
    assert claude["LC_ALL"] == "C" and claude["LEAKCHECK_DENYLIST"] == "/d"
    assert "PATH" in claude and "HOME" in claude
    assert claude["CLAUDE_CODE_SUBPROCESS_ENV_SCRUB"] == "1"
    # git ignores the owner's global and system config, and commits as the fixture
    assert claude["GIT_CONFIG_GLOBAL"] == "/dev/null" and claude["GIT_CONFIG_NOSYSTEM"] == "1"
    assert claude["GIT_AUTHOR_NAME"] == claude["GIT_COMMITTER_NAME"] == "fixture"
    pi = run.child_env("pi", {})
    assert pi["SPARK_API_KEY"] == "k" and stand_in not in pi and "ANTHROPIC_API_KEY" not in pi
    monkeypatch.setenv("PDD_USE_API_KEY", "1")
    assert run.child_env("claude", {})["ANTHROPIC_API_KEY"] == "a"


def test_uv_runs_offline_from_the_runs_own_cache(tmp_path):
    work = tmp_path / "root" / "pdd-s02-red-x"
    (work / "repo").mkdir(parents=True)
    (work / "uv-cache").mkdir()
    plugins = run.installed_plugins(plugins_file(tmp_path))
    settings = settings_of(run.claude_command("hi", work, "s02", plugins, None, None))
    files = settings["sandbox"]["filesystem"]
    assert files["allowWrite"] == [str(work / "uv-cache")]  # the only write outside the repo and temp
    assert str(work / "uv-cache") in files["allowRead"]
    assert not any(".cache/uv" in p for p in files["allowWrite"] + files["allowRead"])  # never the owner's cache
    assert settings["sandbox"]["network"] == {"allowedDomains": [], "strictAllowlist": True}
    env = run.session_env(work)
    assert env["UV_CACHE_DIR"] == str(work / "uv-cache") and env["UV_OFFLINE"] == "1"
    assert env["LEAKCHECK_DENYLIST"] == str(work / "denylist")


def test_the_cache_is_warmed_outside_the_sandbox_before_the_session(tmp_path, monkeypatch):
    repo, cache = tmp_path / "repo", tmp_path / "uv-cache"
    (repo / "scripts").mkdir(parents=True)
    (repo / "scripts" / "leakcheck.py").write_text("# /// script\n# dependencies = []\n# ///\n")
    (repo / "scripts" / "plain.py").write_text("print(1)\n")
    calls = []

    class Done:
        returncode = 0
    monkeypatch.setattr(run.subprocess, "run", lambda command, **kw: calls.append((command, kw)) or Done())
    assert run.warm_uv_cache(repo, cache) is None
    assert calls[0][0] == ["uv", "run", "--quiet", "--with", "pytest", "--with", "pyyaml", "python", "-c", "pass"]
    assert calls[1][0] == ["uv", "sync", "--quiet", "--script", "scripts/leakcheck.py"] and len(calls) == 2
    for _, kw in calls:
        assert kw["cwd"] == repo and kw["env"]["UV_CACHE_DIR"] == str(cache) and "UV_OFFLINE" not in kw["env"]
    Done.returncode = 2
    assert "exited 2" in run.warm_uv_cache(repo, cache)


def test_a_failed_warm_stops_the_run_before_claude_starts(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(run, "INSTALLED", plugins_file(tmp_path))
    monkeypatch.setattr(run, "uv_python_dir", lambda: None)
    monkeypatch.setattr(run, "warm_uv_cache", lambda repo, cache: "uv run exited 1")
    work, repo = run.prepare("s04", "red", tmp_path)
    monkeypatch.setattr(run.subprocess, "run", lambda *a, **k: pytest.fail("claude started"))
    assert run.run_turns(["hi"], work, repo, "s04", "red", run.installed_plugins(), None, False, 30, 1.0) == 3
    assert "HARNESS FAIL s04: cannot warm the uv cache: uv run exited 1" in capsys.readouterr().out


def test_every_turn_is_capped_and_never_waits_on_a_prompt(tmp_path, monkeypatch, capsys):
    plugins = run.installed_plugins(plugins_file(tmp_path))
    command = run.claude_command("hi", tmp_path, "s02", plugins, None, None)
    assert command[command.index("--max-turns") + 1] == "60"
    assert command[command.index("--permission-prompts") + 1] == "none"
    assert settings_of(command)["sandbox"]["network"]["strictAllowlist"] is True
    command = run.claude_command("hi", tmp_path, "s02", plugins, None, None, max_turns=5)
    assert command[command.index("--max-turns") + 1] == "5"
    monkeypatch.setattr(run, "INSTALLED", plugins_file(tmp_path))
    assert run.main(["s04", "--stage", "red", "--dry-run", "--max-turns", "7", "--work-root", str(tmp_path / "r")]) == 0
    printed = json.loads(capsys.readouterr().out.splitlines()[1])
    assert printed[printed.index("--max-turns") + 1] == "7"


def test_a_turn_stopped_by_a_limit_says_which(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(run, "INSTALLED", plugins_file(tmp_path))
    no_uv(monkeypatch)
    work, repo = run.prepare("s04", "red", tmp_path)

    class Failed:
        returncode = 1

    def stopped(command, **kwargs):
        kwargs["stdout"].write(json.dumps({"type": "result", "subtype": "error_max_turns", "is_error": True}) + "\n")
        return Failed()
    monkeypatch.setattr(run.subprocess, "run", stopped)
    assert run.run_turns(["hi"], work, repo, "s04", "red", run.installed_plugins(), None, False, 30, 1.0, 9) == 3
    assert "turn 1 hit --max-turns 9" in capsys.readouterr().out


def test_reads_are_scoped_to_the_repo_and_the_two_plugins(tmp_path):
    tools = run.allowed_tools("s02", run.installed_plugins(plugins_file(tmp_path)))
    assert "Glob" not in tools and "Grep" not in tools  # a bare allow would cover any path
    assert "Read(./**)" in tools and f"Read(/{tmp_path}/sp/7.0.0/**)" in tools
    assert not any(t.startswith("Read(~") or t == "Read" for t in tools)


def test_the_bash_sandbox_is_on_with_no_network_and_no_way_out(tmp_path):
    command = run.claude_command("hi", tmp_path, "s02", run.installed_plugins(plugins_file(tmp_path)), None, None)
    sandbox = settings_of(command)["sandbox"]
    assert sandbox["enabled"] is True and sandbox["failIfUnavailable"] is True
    assert sandbox["allowUnsandboxedCommands"] is False and sandbox["autoAllowBashIfSandboxed"] is False
    assert sandbox["network"]["allowedDomains"] == []
    assert "--max-budget-usd" in command


def test_wildcard_and_scope_restrictions_in_the_allow_list(tmp_path):
    plugins = run.installed_plugins(plugins_file(tmp_path))
    fetch, kickoff = run.allowed_tools("s12", plugins), run.allowed_tools("s01", plugins)
    assert "Bash(git fetch origin)" in fetch and not any(t.startswith("Bash(git fetch *") for t in fetch)
    assert "Bash(cp .claude/skills/plan-driven-development/* *)" in kickoff and "Bash(cp *)" not in kickoff
    assert "Bash(git config core.hooksPath .githooks)" in kickoff


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
    no_uv(monkeypatch)
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
    no_uv(monkeypatch)
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
    run.record_canary(root.resolve(), "m1")
    assert run.main(["s04", "--stage", "red", "--work-root", str(root), "--model", "other"]) == 3
    assert "no passing canary" in capsys.readouterr().out
    assert run.main(["s04", "--stage", "red", "--work-root", str(root), "--model", "m1", "--dry-run"]) == 0


def test_a_canary_expires_after_24_hours(tmp_path):
    now = time.time()
    run.record_canary(tmp_path, "m1", now=now - 23 * 3600)
    assert run.canary_passed(tmp_path, "m1", now=now)
    run.record_canary(tmp_path, "m1", now=now - 25 * 3600)
    assert not run.canary_passed(tmp_path, "m1", now=now)
    (tmp_path / "canary-passed.json").write_text(json.dumps({"model": "m1"}))  # an older marker, with no time
    assert not run.canary_passed(tmp_path, "m1", now=now)
    run.record_canary(tmp_path, "m1", now=now + 3600)  # from the future: not trusted either
    assert not run.canary_passed(tmp_path, "m1", now=now)


def test_a_wait_scenarios_attempt_is_graded_and_the_harness_failure_is_reported_alongside(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(run, "INSTALLED", plugins_file(tmp_path))
    root = tmp_path / "root"
    run.record_canary(root.resolve(), None)

    def fake_turns(prompts, work, repo, scenario, stage, plugins, model, dry_run, *args, **kwargs):
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

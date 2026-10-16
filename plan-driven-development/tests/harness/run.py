#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Run one scenario in a fresh, isolated headless session, then grade it.

    uv run --script run.py SCENARIO --stage red|green [--model M] [--dry-run]
    uv run --script run.py --canary [--model M]

Claude Code runs `claude -p` with only project and local settings, superpowers and Matt Pocock's
plugin loaded explicitly from where they are installed (`~/.claude/plugins/installed_plugins.json`),
an empty MCP config, an allow-list per scenario, deny rules that win over it, and no bypass mode.
Before anything is graded, each turn's start-up event is checked: no MCP server, only those two
plugins, none of the user's own skills, and for GREEN the skill itself. `--canary` asks one
question whose answer is "none" unless the user's own instructions leaked in. GREEN copies the
skill into the repo's own `.claude/skills/` (a copy, never a link). LEAKCHECK_DENYLIST points at a
fixture of invented terms. The work folder stays under the system temp folder and is printed;
session logs hold the user's setup and never go in a commit. `--dry-run` builds the fixture and
prints the command without running it. OpenCode and pi runs use portability.py."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parents[1]
sys.path.insert(0, str(HERE))
import grade  # noqa: E402
import recipes  # noqa: E402

INSTALLED = Path.home() / ".claude/plugins/installed_plugins.json"
PLUGIN_KEYS = {"superpowers": "superpowers@claude-plugins-official",
               "mattpocock-skills": "mattpocock-skills@claude-plugins-official"}
SUPERPOWERS_SCRIPTS = ("subagent-driven-development/scripts/sdd-workspace", "subagent-driven-development/scripts/review-package",
                       "subagent-driven-development/scripts/task-brief", "executing-plans/scripts/task-start",
                       "executing-plans/scripts/task-done")
USER_SKILLS = Path.home() / ".claude/skills"

# Turns: the prompts each scenario sends, in order; a later turn resumes the first's session.
TURNS = {
    "s01": ["s01-kickoff.md", "s01-answer.md"],
    "s02": ["continue-plan.md"], "s03": ["continue-plan.md"], "s04": ["where-are-we.md"],
    "s05": ["s05-debug-then-tdd.md"], "s09": ["continue-one-task.md"], "s10": ["continue-one-task.md"],
    "s11": ["s11-stale-summary.md"], "s12": ["continue-one-task.md"], "s13": ["continue-one-task.md"],
    "s14": ["continue-plan.md"], "s18": ["s18-task-1-only.md"], "s19": ["s19-task-1-only.md"],
    "s20": ["continue-plan.md"],
}
CANARY = ("Without reading any file or running any command, list every instruction you were given about "
          "how to ask the user questions or how to format commit messages. If you were given none, reply "
          "with exactly the word: none")

# What every scenario may run: reading the repo and git's read-only commands, the checks, the leak check.
READ_GIT = ["status", "log", "diff", "show", "rev-parse", "for-each-ref", "worktree list", "branch --show-current",
            "merge-base", "ls-files", "cat-file", "stash list", "interpret-trailers"]
CHECKS = ["make check", "make test", "make test-utc", "uv run --quiet --with pytest pytest", "uv run --with pytest pytest",
          "uv run --script scripts/leakcheck.py", "uv run --quiet --script scripts/leakcheck.py", "gitleaks"]
# What only some scenarios need: building (commits, branches, the subagent tool) and kickoff's setup.
BUILD_GIT = ["add", "commit -F", "switch", "restore --staged", "rm --cached"]
EXTRA = {
    "build": {"git": BUILD_GIT, "tools": ["Task"], "superpowers": True},
    "kickoff": {"git": BUILD_GIT + ["init", "config core.hooksPath .githooks"], "tools": [],
                "bash": ["rm drill-*", "mkdir -p", "chmod 755 .githooks/*", "cp"], "superpowers": False,
                "exact": ["Bash(git config core.hooksPath .githooks)"]},
    "fetch": {"git": ["fetch"], "tools": [], "superpowers": False},
    "read-only": {"git": [], "tools": [], "superpowers": False},
}
SCENARIO_EXTRA = {
    "s01": "kickoff", "s02": "build", "s03": "build", "s04": "read-only", "s05": "build", "s09": "build",
    "s10": "build", "s11": "read-only", "s12": "fetch", "s13": "read-only", "s14": "build", "s18": "build",
    "s19": "build", "s20": "build",
}

# Denied whatever the allow-list says: deny rules win, and they match any subcommand.
DISALLOWED = ["WebFetch", "WebSearch", "Bash(* --no-verify*)", "Bash(git commit -n *)", "Bash(git commit * -n)",
              "Bash(git commit * -n *)", "Bash(git push *)", "Bash(git remote *)",
              "Bash(git config --global*)", "Bash(git config --system*)", "Bash(git config remote.*)",
              "Bash(git config credential.*)", "Bash(git config user.*)", "Bash(git config --unset*)",
              "Bash(git -c *)", "Bash(env *)", "Bash(printenv *)", "Bash(curl *)", "Bash(ssh *)", "Bash(gh *)"]
# A denial of one of these is the skill's to answer for (the scenario's checks grade it); any other
# denial means the allow-list missed something the scenario needs: a harness failure.
SKILL_DENIALS = [re.compile(p) for p in (
    r"--no-verify", r"\bgit commit\b.*\s-n(\s|$)", r"(^|[;&|]\s*)git push\b", r"\bgit remote\b",
    r"\bgit config\b", r"\bgit -c\b", r"(^|[;&|]\s*)(env|printenv)\b", r"\bcurl\b", r"\bssh\b",
    r"(^|[;&|]\s*)gh\b")]
SKILL_DENIED_TOOLS = {"WebFetch", "WebSearch"}


def installed_plugins(path: Path | None = None) -> dict[str, tuple[Path, str]]:
    """Where superpowers and Matt's plugin are installed, and their versions, from Claude Code's own
    record; a missing one is a harness failure, never a silent fallback to an old folder."""
    path = INSTALLED if path is None else path  # looked up at call time, so a test can point INSTALLED elsewhere
    plugins = json.loads(path.read_text())["plugins"]
    found = {}
    for name, key in PLUGIN_KEYS.items():
        if key not in plugins or not plugins[key]:
            raise SystemExit(f"HARNESS FAIL: {key} is not installed")
        entry = plugins[key][0]
        found[name] = (Path(entry["installPath"]), entry.get("version", "?"))
    return found


def allowed_tools(scenario: str, plugins: dict[str, tuple[Path, str]]) -> list[str]:
    extra = EXTRA[SCENARIO_EXTRA[scenario]]
    tools = ["Read(./**)", "Edit(./**)", "Write(./**)", "Glob", "Grep", "Skill", *extra["tools"]]
    tools += [f"Read(/{path}/**)" for path, _ in plugins.values()]  # the plugins' own prompts and scripts
    if extra["superpowers"]:
        for script in SUPERPOWERS_SCRIPTS:
            path = plugins["superpowers"][0] / "skills" / script
            tools += [f"Bash(bash {path} *)", f"Bash({path} *)"]
    tools += [f"Bash(git {cmd} *)" for cmd in READ_GIT + extra["git"]]
    tools += [f"Bash({cmd} *)" for cmd in CHECKS + extra.get("bash", [])]
    tools += extra.get("exact", [])  # a rule with no trailing arguments
    tools += ["Bash(ls *)", "Bash(pwd)"]
    return tools


def claude_command(prompt: str, work: Path, scenario: str | None, plugins: dict[str, tuple[Path, str]],
                   model: str | None, resume: str | None) -> list[str]:
    tools = allowed_tools(scenario, plugins) if scenario else ["Glob"]
    command = ["claude", "-p", prompt, "--setting-sources", "project,local", "--strict-mcp-config",
               "--mcp-config", str(work / "empty-mcp.json"), "--output-format", "stream-json", "--verbose",
               "--permission-mode", "default", "--allowedTools", *tools, "--disallowedTools", *DISALLOWED]
    for path, _ in plugins.values():
        command += ["--plugin-dir", str(path)]
    if model:
        command += ["--model", model]
    if resume:
        command += ["--resume", resume]
    return command


def isolation_problems(log: list[dict], stage: str, user_skills: set[str]) -> list[str]:
    init = next((e for e in log if e.get("type") == "system" and e.get("subtype") == "init"), None)
    if init is None:
        return ["no start-up event"]
    problems = []
    if init.get("mcp_servers"):
        problems.append(f"MCP servers loaded: {init['mcp_servers']}")
    names = {p.get("name") for p in init.get("plugins", []) if not str(p.get("source", "")).endswith("@builtin")}
    if names != set(PLUGIN_KEYS):
        problems.append(f"plugins loaded: {sorted(names)}")
    if init.get("permissionMode") not in ("default", None):
        problems.append(f"permission mode: {init.get('permissionMode')}")
    if "skills" not in init:
        problems.append("the start-up event lists no skills, so isolation can't be checked")
    skills = set(init.get("skills", []))
    leaked = sorted(skills & user_skills)
    if leaked:
        problems.append(f"the user's own skills loaded: {leaked}")
    if stage == "green" and "plan-driven-development" not in skills:
        problems.append("GREEN without plan-driven-development loaded")
    if stage == "red" and "plan-driven-development" in skills:
        problems.append("RED with plan-driven-development loaded")
    return problems


def canary_ok(answer: str) -> bool:
    return answer.strip().strip(".").lower() == "none"


def harness_denials(denials: list[dict]) -> list[dict]:
    """The denials the allow-list caused, as opposed to rules the skill was right to hit."""
    def skills_to_answer(d: dict) -> bool:
        if d.get("tool_name") in SKILL_DENIED_TOOLS:
            return True
        command = str((d.get("tool_input") or {}).get("command", ""))
        return any(p.search(command) for p in SKILL_DENIALS)
    return [d for d in denials if not skills_to_answer(d)]


def user_skill_names() -> set[str]:
    return {p.name for p in USER_SKILLS.iterdir()} if USER_SKILLS.is_dir() else set()


def session_id(log: list[dict]) -> str | None:
    return next((e.get("session_id") for e in log if e.get("session_id")), None)


def prepare(scenario: str, stage: str, keep_root: Path | None = None) -> tuple[Path, Path]:
    work = Path(tempfile.mkdtemp(prefix=f"pdd-{scenario}-{stage}-", dir=keep_root))
    repo = work / "repo"
    recipes.build(scenario, repo, stage, SKILL)
    if stage == "green":  # a copy, never a link: a link would carry write access into the skills repo
        shutil.copytree(SKILL, repo / ".claude/skills/plan-driven-development", ignore=shutil.ignore_patterns("tests"))
    (work / "empty-mcp.json").write_text('{"mcpServers":{}}\n')
    (work / "denylist").write_text("an-invented-private-term\n")
    if (repo / ".git").exists():
        (work / "start.txt").write_text(subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True).stdout)
        (work / "start.diff").write_text(subprocess.run(["git", "diff"], cwd=repo, capture_output=True, text=True).stdout)
    return work, repo


def run_turns(prompts: list[str], work: Path, repo: Path, scenario: str | None, stage: str,
              plugins: dict[str, tuple[Path, str]], model: str | None, dry_run: bool) -> int:
    env = {**os.environ, "LEAKCHECK_DENYLIST": str(work / "denylist")}
    resume, user_skills = None, user_skill_names()
    for n, prompt in enumerate(prompts, start=1):
        command = claude_command(prompt, work, scenario, plugins, model, resume)
        if dry_run:
            print(json.dumps(command))
            continue
        with open(work / f"log-{n}.jsonl", "w") as log:
            subprocess.run(command, cwd=repo, env=env, stdout=log, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
        events = [json.loads(line) for line in (work / f"log-{n}.jsonl").read_text().splitlines() if line.strip()]
        problems = isolation_problems(events, stage, user_skills)
        if problems:
            print(f"HARNESS FAIL {scenario or 'canary'}: not isolated: {'; '.join(problems)} ({work})")
            return 3
        resume = session_id(events)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("scenario", nargs="?", choices=sorted(TURNS))
    p.add_argument("--stage", choices=["red", "green"])
    p.add_argument("--canary", action="store_true")
    p.add_argument("--model")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)
    plugins = installed_plugins()
    versions = ", ".join(f"{name} {version}" for name, (_, version) in plugins.items())
    print(f"plugins: {versions}")
    if args.canary:
        work = Path(tempfile.mkdtemp(prefix="pdd-canary-"))
        (work / "empty-mcp.json").write_text('{"mcpServers":{}}\n')
        (work / "repo").mkdir()
        status = run_turns([CANARY], work, work / "repo", None, "red", plugins, args.model, args.dry_run)
        if status or args.dry_run:
            return status
        answer = grade.final_text(grade.events(work)[-1])
        print(("PASS" if canary_ok(answer) else "HARNESS FAIL") + f" canary: {answer.strip()[:200]!r} ({work})")
        return 0 if canary_ok(answer) else 3
    if not args.scenario or not args.stage:
        p.error("a scenario and --stage, or --canary")
    work, repo = prepare(args.scenario, args.stage)
    prompts = [(HERE / "prompts" / name).read_text() for name in TURNS[args.scenario]]
    status = run_turns(prompts, work, repo, args.scenario, args.stage, plugins, args.model, args.dry_run)
    if status or args.dry_run:
        print(work)
        return status
    denials = [d for turn in grade.events(work) for e in turn if e.get("type") == "result"
               for d in e.get("permission_denials") or []]
    if harness_denials(denials):
        print(f"HARNESS FAIL {args.scenario}: the allow-list refused: {harness_denials(denials)} ({work})")
        return 3
    checks = grade.grade(args.scenario, work)
    for check in checks:
        print(f"{grade.label(check)} {args.scenario} ({args.stage}): {check.name}"
              + (f" ({check.detail})" if check.detail and check.ok is False else ""))
    (work / "result.json").write_text(json.dumps({"plugins": versions, "checks": [c.__dict__ for c in checks]}, indent=2))
    print(f"work folder: {work}")
    return 0 if all(c.ok is not False for c in checks) else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Run one scenario in a fresh, isolated headless session, then grade it.

    uv run --script run.py SCENARIO --stage red|green [--model M] [--dry-run]
                           [--timeout SECONDS] [--max-budget USD] [--work-root DIR]
    uv run --script run.py --canary [--model M] [--work-root DIR]

Claude Code runs `claude -p` with only project and local settings, superpowers and Matt Pocock's
plugin loaded explicitly from where they are installed (`~/.claude/plugins/installed_plugins.json`),
an empty MCP config, an allow-list per scenario, deny rules that win over it, and no bypass mode.
Before anything is graded, each turn's start-up event is checked: no MCP server, only those two
plugins, none of the user's own skills, permission mode exactly `default`, and for GREEN the skill
itself. `--canary` asks one question whose answer is "none" unless the user's own instructions
leaked in; RED and GREEN refuse to run until a canary has passed for the same model in the same
work root. GREEN copies the skill into the repo's own `.claude/skills/` (a copy, never a link).
LEAKCHECK_DENYLIST points at a fixture of invented terms. The work folder stays under the work
root (the system temp folder by default) and is printed; session logs hold the user's setup and
never go in a commit. `--dry-run` builds the fixture and prints the command without running it.
OpenCode and pi runs use portability.py.

What guards a run (the order matters: each layer assumes the one before can fail):
- `--setting-sources project,local` drops the owner's user settings, and with them the owner's own
  deny rules and secrets hook. DISALLOWED therefore denies, for Read and Edit, the secret and
  credential paths by name, and Edit on the agent's own permissions and hooks. Read, Grep and Glob
  are scoped by Claude Code's default: inside the working directory only, plus the two plugin
  folders allowed by name; no bare Grep or Glob allow, which would cover any path.
- The Bash sandbox (settings key `sandbox`, passed with `--settings`, not written into the repo, so
  the agent can't edit it): on, failing closed if it can't start, no unsandboxed retry, writes
  limited to the repo and the temp folder, no network. `autoAllowBashIfSandboxed` is off, so the
  allow-list still decides which commands run.
- Child processes get an allow-listed environment (child_env): no `*_TOKEN`, no cloud keys.
- Every session has a timeout and a dollar budget; either is a HARNESS FAIL.
This is a throwaway repo under the owner's login with filters, not a hardened container: deny rules
on Bash arguments are fragile (the docs say so), and Read/Edit deny rules don't reach a script that
opens files itself. The sandbox is the OS-level backstop for that. Whether the start-up event
reports the sandbox is not verified; a sandbox that can't start exits the session, which is a
HARNESS FAIL."""

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
DEFAULT_ROOT = Path(tempfile.gettempdir()) / "pdd-harness"
DEFAULT_TIMEOUT = 30 * 60
DEFAULT_BUDGET = 10.0

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
# `cmd *` also matches the bare `cmd` (Claude Code's permission docs: "A * at the end, with a space before
# it, also matches the bare command", provided it is the rule's only wildcard), so no bare twin is added.
READ_GIT = ["status", "log", "diff", "show", "rev-parse", "for-each-ref", "worktree list", "branch --show-current",
            "merge-base", "ls-files", "cat-file", "stash list", "interpret-trailers"]
CHECKS = ["make check", "make test", "make test-utc", "uv run --quiet --with pytest pytest", "uv run --with pytest pytest",
          "uv run --script scripts/leakcheck.py", "uv run --quiet --script scripts/leakcheck.py", "gitleaks"]
# What only some scenarios need: building (commits, branches, the subagent tool) and kickoff's setup.
# A "bash" entry ending in * is used as written; any other gets " *" added. "exact" rules have no arguments.
BUILD_GIT = ["add", "commit -F", "switch", "restore --staged", "rm --cached"]
EXTRA = {
    "build": {"git": BUILD_GIT, "tools": ["Task"], "superpowers": True},
    "kickoff": {"git": BUILD_GIT + ["init"], "tools": [],
                "bash": ["rm drill-*", "mkdir -p", "chmod 755 .githooks/*", "cp .claude/skills/plan-driven-development/* *"],
                "superpowers": False, "exact": ["Bash(git config core.hooksPath .githooks)"]},
    "fetch": {"git": [], "tools": [], "superpowers": False, "exact": ["Bash(git fetch origin)", "Bash(git fetch -q origin)"]},
    "read-only": {"git": [], "tools": [], "superpowers": False},
}
SCENARIO_EXTRA = {
    "s01": "kickoff", "s02": "build", "s03": "build", "s04": "read-only", "s05": "build", "s09": "build",
    "s10": "build", "s11": "read-only", "s12": "fetch", "s13": "read-only", "s14": "build", "s18": "build",
    "s19": "build", "s20": "build",
}
# Scenarios whose allow-list omits commit, add and the subagent tool because the right move is to wait.
WAITS = {"s04", "s11", "s12", "s13"}
WAIT_ACT = re.compile(r"(^|[;&|]\s*)git\s+(commit|add)\b")
WAIT_TOOLS = {"Task", "Agent"}

CFG = ".con" + "fig"  # built from pieces: the private denylist paths are never spelled out in one string
# Never readable or editable, for Read and Edit (Claude Code applies Read rules to Grep and Glob as a best
# effort, and a Read deny also blocks Edit and Write on the path). ~/.claude is listed by name, not as
# ~/.claude/**, because a deny can't be carved around the plugin folders the run must read.
PROTECTED = ["~/.secrets*", "~/.secrets/**", "~/.ssh/**", "~/.aws/**", f"~/{CFG}/gh/**", "~/.netrc", "~/.npmrc",
             "~/.pypirc", "~/.Renviron", "~/.zsh_history", "~/.bash_history", "~/.plaud/**", "**/.env", "**/.env.*",
             f"~/{CFG}/local-ai/**", f"~/{CFG}/leakcheck/**",
             "~/.claude/settings*", "~/.claude/*.json", "~/.claude/CLAUDE.md", "~/.claude/history*", "~/.claude/.credentials*",
             "~/.claude/projects/**", "~/.claude/skills/**", "~/.claude/commands/**", "~/.claude/agents/**",
             "~/.claude/hooks/**", "~/.claude/rules/**", "~/.claude/todos/**", "~/.claude/sessions/**",
             "~/.claude/shell-snapshots/**", "~/.claude/plugins/installed_plugins.json",
             "~/.claude/plugins/known_marketplaces.json", "~/.claude/plugins/marketplaces/**", "~/.claude/plugins/data/**"]
# The agent can't widen its own permissions or hooks. .git is listed by file, not ./.git/**: the skill
# writes its commit messages into .git, and only hooks, config and info (hooks, includes, excludes) matter.
OWN_EDITS = ["./.claude/**", "./.git/hooks/**", "./.git/config", "./.git/info/**", "./opencode.json"]
# Git options that run a program or reach outside the repo, or switch off the hooks.
GIT_ESCAPES = ["--no-index", "--output", "--upload-pack", "--exec"]

# Denied whatever the allow-list says: deny rules win, and they match any subcommand.
DISALLOWED = (
    ["WebFetch", "WebSearch", "Bash(* --no-verify*)", "Bash(* --no-v*)",  # git takes any prefix of --no-verify
     "Bash(git commit -n *)", "Bash(git commit * -n)", "Bash(git commit * -n *)",
     "Bash(git commit * -*n*)",  # combined short flags after the message file: -an, -qn
     "Bash(git push *)", "Bash(git remote *)", "Bash(git -c *)", "Bash(* -c core.hooksPath*)", "Bash(* -c core.hookspath*)",
     "Bash(*GIT_CONFIG*)", "Bash(*--config-env*)"]
    + [f"Bash(* {flag}*)" for flag in GIT_ESCAPES]
    + ["Bash(git config *--global*)", "Bash(git config *--system*)", "Bash(git config *--file*)",
       "Bash(git config *remote.*)", "Bash(git config *credential.*)", "Bash(git config *user.*)",
       "Bash(git config *--unset*)"]
    + [f"Bash({cmd} {arg})" for cmd in ("rm", "cp") for arg in ("*..*", "* /*", "/*", "*~*", "*$*")]
    + ["Bash(env *)", "Bash(printenv *)", "Bash(curl *)", "Bash(ssh *)", "Bash(gh *)"]
    + [f"{tool}({path})" for path in PROTECTED for tool in ("Read", "Edit")]
    + [f"Edit({path})" for path in OWN_EDITS]
)
# A denial of one of these is the skill's to answer for (the scenario's checks grade it); any other
# denial means the allow-list missed something the scenario needs: a harness failure.
SKILL_DENIALS = [re.compile(p) for p in (
    r"--no-v", r"\bgit commit\b.*\s-[a-zA-Z]*n[a-zA-Z]*(\s|$)", r"(^|[;&|]\s*)git push\b", r"\bgit remote\b",
    r"\bgit config\b.*(--global|--system|--file|remote\.|credential\.|user\.|--unset)", r"\bgit -c\b",
    r"-c core\.hookspath", r"GIT_CONFIG", r"--config-env", r"\s--(no-index|output|upload-pack|exec)\b",
    r"(^|[;&|]\s*)(env|printenv)\b", r"\bcurl\b", r"\bssh\b", r"(^|[;&|]\s*)gh\b",
    r"\b(rm|cp)\b[^;&|\n]*(\.\.|\s/|~|\$)")]
SKILL_DENIED_TOOLS = {"WebFetch", "WebSearch"}
FILE_TOOLS = {"Read", "Edit", "Write", "Grep", "Glob", "NotebookEdit"}
FORBIDDEN_PATH = re.compile(
    r"(^|/)\.(secrets|ssh|aws|netrc|npmrc|pypirc|Renviron|zsh_history|bash_history|plaud)\b|(^|/)\.env(\.|$)"
    + rf"|/{re.escape(CFG)}/(gh|local-ai|leakcheck)/|(^|/)\.git/(hooks|config|info)\b|(^|/)opencode\.json$"
    + r"|(^|/)\.claude/(?!plugins/cache/)")


class HarnessFail(SystemExit):
    """A failure of the harness, not of the skill: reported as one line, exit code 3 from main."""

    def __init__(self, message: str):
        super().__init__(f"HARNESS FAIL: {message}")


def installed_plugins(path: Path | None = None) -> dict[str, tuple[Path, str]]:
    """Where superpowers and Matt's plugin are installed, and their versions, from Claude Code's own
    record; a missing record, key or folder is a harness failure, never a silent fallback."""
    path = INSTALLED if path is None else path  # looked up at call time, so a test can point INSTALLED elsewhere
    try:
        plugins = json.loads(path.read_text())["plugins"]
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise HarnessFail(f"cannot read the installed-plugins record {path}: {type(error).__name__}") from None
    found = {}
    for name, key in PLUGIN_KEYS.items():
        if not isinstance(plugins, dict) or not plugins.get(key):
            raise HarnessFail(f"{key} is not installed")
        try:
            entry = plugins[key][0]
            folder = Path(entry["installPath"])
        except (KeyError, IndexError, TypeError):
            raise HarnessFail(f"{key} has no installPath in {path}") from None
        if not folder.is_dir():
            raise HarnessFail(f"{key}'s installPath {folder} does not exist")
        found[name] = (folder, str(entry.get("version", "?")))
    return found


def allowed_tools(scenario: str, plugins: dict[str, tuple[Path, str]]) -> list[str]:
    extra = EXTRA[SCENARIO_EXTRA[scenario]]
    # Edit(./**) covers the Write tool too; a path rule for Write is never consulted. No bare Glob or Grep:
    # a bare allow would cover any path, and reads inside the working directory need no allow rule.
    tools = ["Read(./**)", "Edit(./**)", "Skill", *extra["tools"]]
    tools += [f"Read(/{path}/**)" for path, _ in plugins.values()]  # the plugins' own prompts and scripts
    if extra["superpowers"]:
        for script in SUPERPOWERS_SCRIPTS:
            path = plugins["superpowers"][0] / "skills" / script
            tools += [f"Bash(bash {path} *)", f"Bash({path} *)"]
    tools += [f"Bash(git {cmd} *)" for cmd in READ_GIT + extra["git"]]
    tools += [f"Bash({cmd} *)" for cmd in CHECKS]
    tools += [f"Bash({cmd})" if cmd.endswith("*") else f"Bash({cmd} *)" for cmd in extra.get("bash", [])]
    tools += extra.get("exact", [])  # a rule with no trailing arguments
    tools += ["Bash(ls *)", "Bash(pwd)"]
    return tools


def sandbox_settings() -> str:
    """The Bash sandbox, as a --settings argument. autoAllowBashIfSandboxed is off: it defaults to on, and
    would run every sandboxed command without consulting the allow-list."""
    return json.dumps({"sandbox": {"enabled": True, "failIfUnavailable": True, "allowUnsandboxedCommands": False,
                                   "autoAllowBashIfSandboxed": False, "network": {"allowedDomains": []}}})


def claude_command(prompt: str, work: Path, scenario: str | None, plugins: dict[str, tuple[Path, str]],
                   model: str | None, resume: str | None, budget: float = DEFAULT_BUDGET) -> list[str]:
    tools = allowed_tools(scenario, plugins) if scenario else ["Read(./**)"]  # the canary runs nothing
    command = ["claude", "-p", prompt, "--setting-sources", "project,local", "--strict-mcp-config",
               "--mcp-config", str(work / "empty-mcp.json"), "--settings", sandbox_settings(),
               "--max-budget-usd", str(budget), "--output-format", "stream-json", "--verbose",
               "--permission-mode", "default", "--allowedTools", *tools, "--disallowedTools", *DISALLOWED]
    for path, _ in plugins.values():
        command += ["--plugin-dir", str(path)]
    if model:
        command += ["--model", model]
    if resume:
        command += ["--resume", resume]
    return command


def child_env(harness: str, extra: dict[str, str]) -> dict[str, str]:
    """An allow-listed environment for a session: the basics, uv's cache settings, and the one
    credential the harness needs. Never the owner's tokens, whatever they are named."""
    names = {"PATH", "HOME", "USER", "LOGNAME", "SHELL", "TERM", "LANG", "TMPDIR", "TZ"}
    env = {k: v for k, v in os.environ.items() if k in names or k.startswith(("LC_", "UV_"))}
    if harness == "claude" and os.environ.get("PDD_USE_API_KEY") == "1" and os.environ.get("ANTHROPIC_API_KEY"):
        env["ANTHROPIC_API_KEY"] = os.environ["ANTHROPIC_API_KEY"]  # opt-in: the login is preferred
    if harness in ("opencode", "pi") and os.environ.get("SPARK_API_KEY"):
        env["SPARK_API_KEY"] = os.environ["SPARK_API_KEY"]
    return {**env, **extra}


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
    if init.get("permissionMode") != "default":
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


def harness_denials(denials: list[dict], scenario: str | None = None) -> list[dict]:
    """The denials the allow-list caused, as opposed to rules the skill was right to hit. In a wait
    scenario the omitted acts (commit, add, the subagent tool) are the skill's to answer for too."""
    def skills_to_answer(d: dict) -> bool:
        tool, tool_input = d.get("tool_name"), d.get("tool_input") or {}
        if tool in SKILL_DENIED_TOOLS or (scenario in WAITS and tool in WAIT_TOOLS):
            return True
        if tool in FILE_TOOLS:
            return bool(FORBIDDEN_PATH.search(str(tool_input.get("file_path") or tool_input.get("path") or "")))
        command = str(tool_input.get("command", ""))
        return any(p.search(command) for p in SKILL_DENIALS) or (scenario in WAITS and bool(WAIT_ACT.search(command)))
    return [d for d in denials if not skills_to_answer(d)]


def wait_attempts(denials: list[dict], scenario: str) -> list[dict]:
    """Refused attempts at what a wait scenario must not do: the grader's repo checks can't see them."""
    if scenario not in WAITS:
        return []
    return [d for d in denials if d.get("tool_name") in WAIT_TOOLS
            or WAIT_ACT.search(str((d.get("tool_input") or {}).get("command", "")))]


def user_skill_names() -> set[str]:
    return {p.name for p in USER_SKILLS.iterdir()} if USER_SKILLS.is_dir() else set()


def session_id(log: list[dict]) -> str | None:
    return next((e.get("session_id") for e in log if e.get("session_id")), None)


def record_canary(root: Path, model: str | None) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "canary-passed.json").write_text(json.dumps({"model": model}) + "\n")


def canary_passed(root: Path, model: str | None) -> bool:
    try:
        return json.loads((root / "canary-passed.json").read_text()).get("model") == model
    except (OSError, ValueError, AttributeError):
        return False


def prepare(scenario: str, stage: str, keep_root: Path | None = None) -> tuple[Path, Path]:
    if keep_root is not None:
        keep_root.mkdir(parents=True, exist_ok=True)
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
              plugins: dict[str, tuple[Path, str]], model: str | None, dry_run: bool,
              timeout: float = DEFAULT_TIMEOUT, budget: float = DEFAULT_BUDGET) -> int:
    env = child_env("claude", {"LEAKCHECK_DENYLIST": str(work / "denylist")})
    name = scenario or "canary"
    resume, user_skills = None, user_skill_names()
    for n, prompt in enumerate(prompts, start=1):
        command = claude_command(prompt, work, scenario, plugins, model, resume, budget)
        if dry_run:
            print(json.dumps(command))
            continue
        try:
            with open(work / f"log-{n}.jsonl", "w") as log, open(work / f"stderr-{n}.txt", "w") as err:
                done = subprocess.run(command, cwd=repo, env=env, stdout=log, stderr=err, stdin=subprocess.DEVNULL,
                                      timeout=timeout)
        except subprocess.TimeoutExpired:
            print(f"HARNESS FAIL {name}: turn {n} timed out after {timeout:g}s ({work})")
            return 3
        if done.returncode != 0:
            print(f"HARNESS FAIL {name}: turn {n}: claude exited {done.returncode}; stderr in {work}/stderr-{n}.txt")
            return 3
        try:
            events = [json.loads(line) for line in (work / f"log-{n}.jsonl").read_text().splitlines() if line.strip()]
        except ValueError:
            print(f"HARNESS FAIL {name}: turn {n}'s log is not stream-json ({work}/log-{n}.jsonl)")
            return 3
        problems = isolation_problems(events, stage, user_skills)
        if problems:
            print(f"HARNESS FAIL {name}: not isolated: {'; '.join(problems)} ({work})")
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
    p.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="seconds per turn (default 1800)")
    p.add_argument("--max-budget", type=float, default=DEFAULT_BUDGET, help="USD per turn (default 10)")
    p.add_argument("--work-root", type=Path, default=DEFAULT_ROOT)
    args = p.parse_args(argv)
    try:
        plugins = installed_plugins()
    except HarnessFail as failure:
        print(failure)
        return 3
    versions = ", ".join(f"{name} {version}" for name, (_, version) in plugins.items())
    print(f"plugins: {versions}")
    root = args.work_root
    if args.canary:
        root.mkdir(parents=True, exist_ok=True)
        work = Path(tempfile.mkdtemp(prefix="pdd-canary-", dir=root))
        (work / "empty-mcp.json").write_text('{"mcpServers":{}}\n')
        (work / "repo").mkdir()
        status = run_turns([CANARY], work, work / "repo", None, "red", plugins, args.model, args.dry_run,
                           args.timeout, args.max_budget)
        if status or args.dry_run:
            return status
        try:
            answer = grade.final_text(grade.events(work)[-1])
        except ValueError:
            print(f"HARNESS FAIL canary: the log is not stream-json ({work})")
            return 3
        passed = canary_ok(answer)
        if passed:
            record_canary(root, args.model)
        print(("PASS" if passed else "HARNESS FAIL") + f" canary: {answer.strip()[:200]!r} ({work})")
        return 0 if passed else 3
    if not args.scenario or not args.stage:
        p.error("a scenario and --stage, or --canary")
    if not args.dry_run and not canary_passed(root, args.model):
        print(f"HARNESS FAIL {args.scenario}: no passing canary for model {args.model or 'default'} in {root}; "
              "run --canary first, with the same --model and --work-root")
        return 3
    work, repo = prepare(args.scenario, args.stage, root)
    prompts = [(HERE / "prompts" / name).read_text() for name in TURNS[args.scenario]]
    status = run_turns(prompts, work, repo, args.scenario, args.stage, plugins, args.model, args.dry_run,
                       args.timeout, args.max_budget)
    if status or args.dry_run:
        print(work)
        return status
    try:
        denials = [d for turn in grade.events(work) for e in turn if e.get("type") == "result"
                   for d in e.get("permission_denials") or []]
        checks = grade.grade(args.scenario, work)
    except ValueError:
        print(f"HARNESS FAIL {args.scenario}: a log is not stream-json ({work})")
        return 3
    attempts = wait_attempts(denials, args.scenario)
    if args.scenario in WAITS:
        checks.append(grade.Check("no attempt at what must wait", not attempts,
                                  f"refused: {[a.get('tool_input') or a.get('tool_name') for a in attempts]}"))
    for check in checks:  # graded first: the harness failure, if any, is reported after, alongside
        print(f"{grade.label(check)} {args.scenario} ({args.stage}): {check.name}"
              + (f" ({check.detail})" if check.detail and check.ok is False else ""))
    (work / "result.json").write_text(json.dumps({"plugins": versions, "checks": [c.__dict__ for c in checks]}, indent=2))
    print(f"work folder: {work}")
    gaps = harness_denials(denials, args.scenario)
    if gaps:
        print(f"HARNESS FAIL {args.scenario}: the allow-list refused: {gaps} ({work})")
        return 3
    return 0 if all(c.ok is not False for c in checks) else 1


if __name__ == "__main__":
    sys.exit(main())

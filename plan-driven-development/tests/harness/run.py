#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Run one scenario in a fresh, isolated headless session, then grade it.

    uv run --script run.py SCENARIO --stage red|green [--model M] [--dry-run] [--timeout SECONDS]
                           [--max-budget USD] [--max-turns N] [--work-root DIR]
    uv run --script run.py --canary [--model M] [--work-root DIR]

Claude Code runs `claude -p` with only project and local settings, superpowers and Matt Pocock's
plugin loaded explicitly from where they are installed (`~/.claude/plugins/installed_plugins.json`),
an empty MCP config, an allow-list per scenario, deny rules that win over it, and no bypass mode.
Before anything is graded, each turn's start-up event is checked: no MCP server, only those two
plugins, none of the user's own skills, permission mode exactly `default`, and for GREEN the skill
itself. `--canary` asks one question whose answer is "none" unless the user's own instructions
leaked in; RED and GREEN refuse to run unless a canary passed for the same model in the same work
root within the last 24 hours. GREEN copies the skill into the repo's own `.claude/skills/` (a copy,
never a link). LEAKCHECK_DENYLIST points at a fixture of invented terms. The work folder stays under
the work root (the system temp folder by default) and is printed; session logs hold the user's
setup and never go in a commit. `--dry-run` builds the fixture and prints the command without
running it. OpenCode and pi runs use portability.py.

What guards a run (the order matters: each layer assumes the one before can fail):
- `--setting-sources project,local` drops the owner's user settings, and with them the owner's own
  deny rules and secrets hook, so the runner passes its own, built at run time:
  `permissions.blockReadsOutsideWorkingDirectories` makes Read, Grep, Glob and LSP refuse any path
  outside the repo, makes Bash's recognized file readers (`cat`, `ls`, ...) ask, which `-p` denies,
  and takes the home folder away from sandboxed commands. The files Claude Code itself keeps
  readable under the block (skills, plugins, rules, agents, commands, `~/.claude/CLAUDE.md`) are
  denied by name, apart from the plugin cache, which holds the two plugin folders. Read and Edit
  deny rules name the credential stores listed in HOME_PROTECTED in both `~/` and absolute form,
  `.env` files anywhere (`//**/.env`), the agent's own permissions and hooks, and the work root's
  grading records.
- The Bash sandbox (settings key `sandbox`, passed with `--settings`, not written into the repo, so
  the agent can't edit it): on, failing closed if it can't start, no unsandboxed retry, every
  command still through the allow-list (`autoAllowBashIfSandboxed` off). Writes: the repo, the
  sandbox's own temp folder and the run's uv cache. Reads re-opened: the repo, S12's bare remote,
  the leak-check fixture, the run's uv cache, uv's Pythons (and uv itself when it lives under the
  home folder) and the two plugin folders; the grading records of every run under the work root
  are hidden. Network: no host allowed, and
  `strictAllowlist`, so a request is refused, never left waiting on a prompt.
- uv runs offline from the run's own cache, warmed outside the sandbox before the session; never
  the owner's cache, which agent-written code could otherwise plant files in for later runs.
- git ignores the owner's global and system config and commits as the fixture.
- Child processes get an allow-listed environment (child_env): no `*_TOKEN`, no cloud keys, none of
  the owner's uv settings but where uv's Pythons are. Claude Code scrubs credentials from every
  subprocess it starts
  (`CLAUDE_CODE_SUBPROCESS_ENV_SCRUB`), and the API key, when the opt-in passes one, is denied to
  sandboxed shells as well.
- Every session has a timeout, a dollar budget and a turn cap, and nobody answers permission
  prompts (`--permission-prompts none`); a limit reached is a HARNESS FAIL.
This is a throwaway repo under the owner's login with filters and an OS sandbox, not a hardened
container: deny rules on Bash arguments are fragile (the docs say so); outside the home folder and
the other user-file roots, sandboxed code can still read what any local user can (the system temp
folder's other contents, /etc); and of what the block re-opens, the git ignore and attributes files,
any file the owner's git config includes, and the whole plugin cache stay readable. Not covered
here: after the session, grade.py runs the repo's tests (S02) and imports its code (S19) outside any
sandbox, with the owner's full environment."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
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
DEFAULT_MAX_TURNS = 60
CANARY_TTL = 24 * 60 * 60
CANARY_MARKER = "canary-passed.json"

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
          "uv run --script scripts/leakcheck.py", "uv run --quiet --script scripts/leakcheck.py"]
# gitleaks only redacted, and only on the repo itself: the target is the last argument and must be `.`.
GITLEAKS = [f"Bash(gitleaks {sub} --redact{middle} .)" for sub in ("git", "dir") for middle in ("", " *")]
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
# The subagent tool needs no permission (tools reference: Agent, "Permission required: No"), so leaving it
# off the allow-list blocks nothing: in these scenarios it is removed with --disallowedTools as well.
WAITS = {"s04", "s11", "s12", "s13"}
WAIT_ACT = re.compile(r"(^|[;&|]\s*)git\s+(commit|add)\b")
WAIT_TOOLS = {"Task", "Agent"}

CFG = ".con" + "fig"  # built from pieces: the private denylist paths are never spelled out in one string
# Credential stores and the owner's own setup, relative to the home folder. Each is denied for Read and Edit
# in `~/` form and in absolute form, the home folder looked up at run time (Claude Code applies Read rules
# to Grep and Glob as a best effort, a Read deny also blocks Edit and Write on the path, and Read deny rules
# join the sandbox's denyRead). ~/.claude is listed by name, not as ~/.claude/**, because a deny can't be
# carved around the plugin folders the run must read.
HOME_PROTECTED = [
    ".secrets*", ".secrets/**", ".ssh/**", ".aws/**", f"{CFG}/gh/**", ".netrc", ".npmrc", ".pypirc", ".Renviron",
    ".zsh_history", ".bash_history", ".plaud/**", f"{CFG}/local-ai/**", f"{CFG}/leakcheck/**",
    ".pi/agent/auth.json", ".pi/agent/models*.json", ".claude.json", ".docker/config.json", ".kube/config",
    f"{CFG}/opencode/**", ".hermes/**", ".gitconfig", f"{CFG}/git/config", f"{CFG}/git/credentials",
    ".git-credentials", ".gnupg/**", f"{CFG}/gcloud/**", ".azure/**", "Library/Keychains/**",
    ".claude/settings*", ".claude/*.json", ".claude/CLAUDE.md", ".claude/history*", ".claude/.credentials*",
    ".claude/projects/**", ".claude/skills/**", ".claude/commands/**", ".claude/agents/**", ".claude/hooks/**",
    ".claude/rules/**", ".claude/todos/**", ".claude/sessions/**", ".claude/shell-snapshots/**",
    ".claude/paste-cache/**", ".claude/file-history/**", ".claude/ide/**", ".claude/debug/**",
    ".claude/plugins/installed_plugins.json", ".claude/plugins/known_marketplaces.json",
    ".claude/plugins/marketplaces/**", ".claude/plugins/data/**"]
# `.env` files anywhere on the filesystem: `**/.env` would reach only at or under the working directory.
ANYWHERE_PROTECTED = ["//**/.env", "//**/.env.*"]
# The agent can't widen its own permissions or hooks. .git is listed by file, not ./.git/**: the fixture's plan
# has the agent write its commit messages into .git, and only hooks, config and info (includes, excludes) matter.
OWN_EDITS = ["./.claude/**", "./.git/hooks/**", "./.git/config", "./.git/info/**", "./opencode.json"]
# What the runner and the graders read in each work folder under the root: hidden from sandboxed commands
# (none is an ancestor of a repo, which uv, git and pytest walk up from) and never editable. The leak-check
# fixture and the MCP config stay readable: the run itself needs them.
RECORDS = ["log-*.jsonl", "stderr-*.txt", "start.txt", "start.diff", "result.json", "other-machine"]
RUN_INPUTS = ["denylist", "empty-mcp.json"]
# Git options that run a program or reach outside the repo, or switch off the hooks.
GIT_ESCAPES = ["--no-index", "--output", "--upload-pack", "--exec"]
# git commit's boolean short flags other than -n, which may share a cluster with it (-an, -qn, -aqn). Only
# `*` exists in Claude Code's Bash rules, so the clusters are spelled out: n after up to two of these.
COMMIT_BOOLEAN_FLAGS = "aeiopqsvz"
N_CLUSTERS = [prefix + "n" for prefix in
              ["", *COMMIT_BOOLEAN_FLAGS, *(a + b for a in COMMIT_BOOLEAN_FLAGS for b in COMMIT_BOOLEAN_FLAGS)]]
# An argument that leaves the repo: a parent folder, the home folder, a variable, or an absolute path, bare,
# quoted or escaped.
OUTSIDE_ARGS = ["*..*", "*~*", "*$*"] + [f"{lead}{quote}/*" for lead in ("", "* ") for quote in ("", "'", '"', "\\")]
GITLEAKS_OUTSIDE = [f"Bash(gitleaks *{sep}{quote}{lead}*)" for sep in (" ", "=") for quote in ("", "'", '"')
                    for lead in ("/", "~", "..")]

# Denied whatever the allow-list says: deny rules win, and they match any subcommand.
DISALLOWED = (
    ["WebFetch", "WebSearch", "Bash(* --no-verify*)", "Bash(* --no-v*)",  # git takes any prefix of --no-verify
     "Bash(git push *)", "Bash(git remote *)", "Bash(git -c *)", "Bash(* -c core.hooksPath*)", "Bash(* -c core.hookspath*)",
     "Bash(*GIT_CONFIG*)", "Bash(*--config-env*)"]
    + [f"Bash(git commit{gap} -{cluster}*)" for gap in ("", " *") for cluster in N_CLUSTERS]
    + [f"Bash(* {flag}*)" for flag in GIT_ESCAPES]
    + ["Bash(git config *--global*)", "Bash(git config *--system*)", "Bash(git config *--file*)",
       "Bash(git config *remote.*)", "Bash(git config *credential.*)", "Bash(git config *user.*)",
       "Bash(git config *--unset*)"]
    + [f"Bash({cmd} {arg})" for cmd in ("rm", "cp", "chmod", "mkdir") for arg in OUTSIDE_ARGS]
    + GITLEAKS_OUTSIDE
    + ["Bash(env *)", "Bash(printenv *)", "Bash(curl *)", "Bash(ssh *)", "Bash(gh *)"]
)
# A denial of one of these is the skill's to answer for (the scenario's checks grade it); any other
# denial means the allow-list missed something the scenario needs: a harness failure.
SKILL_DENIALS = [re.compile(p) for p in (
    r"--no-v", r"\bgit commit\b.*\s-[a-zA-Z]*n[a-zA-Z]*(\s|$)", r"(^|[;&|]\s*)git push\b", r"\bgit remote\b",
    r"\bgit config\b.*(--global|--system|--file|remote\.|credential\.|user\.|--unset)", r"\bgit -c\b",
    r"-c core\.hookspath", r"GIT_CONFIG", r"--config-env", r"\s--(no-index|output|upload-pack|exec)\b",
    r"(^|[;&|]\s*)(env|printenv)\b", r"\bcurl\b", r"\bssh\b", r"(^|[;&|]\s*)gh\b",
    r"\b(rm|cp|chmod|mkdir)\b[^;&|\n]*(\.\.|\s['\"\\]?/|~|\$)", r"\bgitleaks\b[^;&|\n]*[\s=]['\"]?(/|~|\.\.)")]
SKILL_DENIED_TOOLS = {"WebFetch", "WebSearch"}
FILE_TOOLS = {"Read", "Edit", "Write", "Grep", "Glob", "NotebookEdit"}
FORBIDDEN_PATH = re.compile(
    r"(^|/)\.(secrets|ssh|aws|netrc|npmrc|pypirc|Renviron|zsh_history|bash_history|plaud|hermes|gnupg|azure"
    r"|gitconfig|git-credentials|claude\.json)\b|(^|/)\.env(\.|$)|/\.pi/agent/|/\.docker/config\.json$|/\.kube/config$"
    + rf"|/{re.escape(CFG)}/(gh|local-ai|leakcheck|opencode|git|gcloud)/|(^|/)\.git/(hooks|config|info)\b"
    + r"|(^|/)opencode\.json$|/Library/Keychains/|(^|/)\.claude/(?!plugins/cache/)")
# Credentials Claude Code may hold for its own API calls, kept from sandboxed shells.
API_KEYS = ["ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN"]
# git without the owner's global and system config (signing, hooksPath, includes, credential helpers),
# committing as the fixture does: S01 starts from an empty folder, with no repo config of its own.
GIT_ISOLATION = {"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1",
                 "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
                 "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid"}
# Filled before the session, outside the sandbox: what the fixture's checks import.
WARM = ["uv", "run", "--quiet", "--with", "pytest", "--with", "pyyaml", "python", "-c", "pass"]


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
    tools += GITLEAKS
    tools += [f"Bash({cmd})" if cmd.endswith("*") else f"Bash({cmd} *)" for cmd in extra.get("bash", [])]
    tools += extra.get("exact", [])  # a rule with no trailing arguments
    tools += ["Bash(ls *)", "Bash(pwd)"]
    return tools


def protected_paths(home: Path) -> list[str]:
    """The credential stores as Read/Edit rule paths: each in `~/` form and in absolute `//` form."""
    absolute = "//" + str(home.resolve()).lstrip("/")
    return [form for path in HOME_PROTECTED for form in (f"~/{path}", f"{absolute}/{path}")] + ANYWHERE_PROTECTED


def record_paths(root: Path) -> list[str]:
    """The grading records under the work root, as absolute paths: the canary marker and each run's records."""
    return [str(root / CANARY_MARKER)] + [str(root / "pdd-*" / name) for name in RECORDS]


def denied_rules(scenario: str | None, home: Path, root: Path) -> list[str]:
    rules = list(DISALLOWED)
    if scenario in WAITS:
        rules += sorted(WAIT_TOOLS)  # a bare tool name removes the tool from Claude's context
    rules += [f"{tool}({path})" for path in protected_paths(home) for tool in ("Read", "Edit")]
    rules += [f"Edit({path})" for path in OWN_EDITS]
    rules += [f"Edit(/{path})" for path in record_paths(root) + [str(root / "pdd-*" / name) for name in RUN_INPUTS]]
    return rules


def sandbox_settings(work: Path, root: Path, plugins: dict[str, tuple[Path, str]], extra_reads=()) -> str:
    """The read block and the Bash sandbox, as a --settings argument. autoAllowBashIfSandboxed is off: it
    defaults to on, and would run every sandboxed command without consulting the allow-list. Only folders
    that exist are listed: on Linux the sandbox mounts concrete paths."""
    cache = work / "uv-cache"
    reads = [work / "repo", work / "remote.git", work / "denylist", cache, *(path for path, _ in plugins.values()),
             *extra_reads]
    return json.dumps({
        "permissions": {"blockReadsOutsideWorkingDirectories": True},
        "sandbox": {
            "enabled": True, "failIfUnavailable": True, "allowUnsandboxedCommands": False,
            "autoAllowBashIfSandboxed": False,
            "network": {"allowedDomains": [], "strictAllowlist": True},
            "filesystem": {"allowWrite": [str(cache)] if cache.is_dir() else [],
                           "allowRead": [str(path) for path in reads if path.exists()],
                           "denyRead": record_paths(root)},
            "credentials": {"envVars": [{"name": name, "mode": "deny"} for name in API_KEYS]}}})


def claude_command(prompt: str, work: Path, scenario: str | None, plugins: dict[str, tuple[Path, str]],
                   model: str | None, resume: str | None, budget: float = DEFAULT_BUDGET, *,
                   max_turns: int = DEFAULT_MAX_TURNS, root: Path | None = None, extra_reads=(),
                   home: Path | None = None) -> list[str]:
    root = work.parent if root is None else root
    tools = allowed_tools(scenario, plugins) if scenario else ["Read(./**)"]  # the canary runs nothing
    command = ["claude", "-p", prompt, "--setting-sources", "project,local", "--strict-mcp-config",
               "--mcp-config", str(work / "empty-mcp.json"),
               "--settings", sandbox_settings(work, root, plugins, extra_reads),
               "--max-budget-usd", str(budget), "--max-turns", str(max_turns), "--permission-prompts", "none",
               "--output-format", "stream-json", "--verbose", "--permission-mode", "default",
               "--allowedTools", *tools,
               "--disallowedTools", *denied_rules(scenario, Path.home() if home is None else home, root)]
    for path, _ in plugins.values():
        command += ["--plugin-dir", str(path)]
    if model:
        command += ["--model", model]
    if resume:
        command += ["--resume", resume]
    return command


def child_env(harness: str, extra: dict[str, str]) -> dict[str, str]:
    """An allow-listed environment for a session: the basics, where uv's own Pythons are, git without the
    owner's config, and the one credential the harness needs. Never the owner's tokens, whatever they are
    named, and none of the owner's uv settings (an index URL or publish token can carry a credential)."""
    names = {"PATH", "HOME", "USER", "LOGNAME", "SHELL", "TERM", "LANG", "TMPDIR", "TZ", "UV_PYTHON_INSTALL_DIR"}
    env = {k: v for k, v in os.environ.items() if k in names or k.startswith("LC_")}
    env.update(GIT_ISOLATION)
    if harness == "claude":
        env["CLAUDE_CODE_SUBPROCESS_ENV_SCRUB"] = "1"  # credentials stripped from every subprocess Claude starts
        if os.environ.get("PDD_USE_API_KEY") == "1" and os.environ.get("ANTHROPIC_API_KEY"):
            env["ANTHROPIC_API_KEY"] = os.environ["ANTHROPIC_API_KEY"]  # opt-in: the login is preferred
    if harness in ("opencode", "pi") and os.environ.get("SPARK_API_KEY"):
        env["SPARK_API_KEY"] = os.environ["SPARK_API_KEY"]
    return {**env, **extra}


def session_env(work: Path) -> dict[str, str]:
    """The environment of a run's Claude Code session: uv offline from the run's own cache."""
    return child_env("claude", {"LEAKCHECK_DENYLIST": str(work / "denylist"), "UV_CACHE_DIR": str(work / "uv-cache"),
                                "UV_OFFLINE": "1"})


def uv_python_dir() -> Path | None:
    """Where uv keeps its own Pythons, which sandboxed uv must read; None if uv can't say."""
    try:
        done = subprocess.run(["uv", "python", "dir"], env=child_env("uv", {}), capture_output=True, text=True,
                              stdin=subprocess.DEVNULL, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    path = Path(done.stdout.strip())
    return path.resolve() if done.returncode == 0 and path.is_absolute() else None


def uv_reads() -> list[Path]:
    """What sandboxed uv needs to read outside the repo and its cache: its Pythons, and uv itself when it
    lives under the home folder, which the read block takes away."""
    reads = [path] if (path := uv_python_dir()) else []
    found = shutil.which("uv")
    if found and Path(found).resolve().is_relative_to(Path.home().resolve()):
        reads.append(Path(found).resolve())
    return reads


def warm_uv_cache(repo: Path, cache: Path, timeout: float = 600) -> str | None:
    """Fill the run's own uv cache outside the sandbox, before the session, so uv inside it runs offline:
    what the checks import, and every PEP 723 script in the repo or the skill's copy. Returns what failed."""
    env = child_env("uv", {"UV_CACHE_DIR": str(cache)})
    scripts = [*sorted(repo.glob("scripts/*.py")), *sorted(repo.glob(".claude/skills/*/scripts/*.py"))]
    commands = [WARM] + [["uv", "sync", "--quiet", "--script", str(script.relative_to(repo))]
                         for script in scripts if "# /// script" in script.read_text()]
    for command in commands:
        try:
            done = subprocess.run(command, cwd=repo, env=env, capture_output=True, text=True,
                                  stdin=subprocess.DEVNULL, timeout=timeout)
        except (OSError, subprocess.SubprocessError) as error:
            return f"{' '.join(command)}: {type(error).__name__}"
        if done.returncode != 0:
            return f"{' '.join(command)} exited {done.returncode}"
    return None


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


def wait_attempts(denials: list[dict], scenario: str, uses: list[tuple[str, dict]] = ()) -> list[dict]:
    """Attempts at what a wait scenario must not do, which the grader's repo checks can't see: refused
    commits and adds, and any subagent call the log shows, refused or not."""
    if scenario not in WAITS:
        return []
    refused = [d for d in denials if d.get("tool_name") in WAIT_TOOLS
               or WAIT_ACT.search(str((d.get("tool_input") or {}).get("command", "")))]
    return refused + [{"tool_name": name, "tool_input": tool_input} for name, tool_input in uses if name in WAIT_TOOLS]


def user_skill_names() -> set[str]:
    return {p.name for p in USER_SKILLS.iterdir()} if USER_SKILLS.is_dir() else set()


def session_id(log: list[dict]) -> str | None:
    return next((e.get("session_id") for e in log if e.get("session_id")), None)


def record_canary(root: Path, model: str | None, now: float | None = None) -> None:
    root.mkdir(parents=True, exist_ok=True)
    passed_at = time.time() if now is None else now
    (root / CANARY_MARKER).write_text(json.dumps({"model": model, "passed_at": passed_at}) + "\n")


def canary_passed(root: Path, model: str | None, now: float | None = None) -> bool:
    """A canary for this model passed in this work root within the last 24 hours (and not in the future)."""
    try:
        marker = json.loads((root / CANARY_MARKER).read_text())
        age = (time.time() if now is None else now) - float(marker["passed_at"])
        return marker.get("model") == model and 0 <= age < CANARY_TTL
    except (OSError, ValueError, AttributeError, KeyError, TypeError):
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
    (work / "uv-cache").mkdir()
    if (repo / ".git").exists():
        (work / "start.txt").write_text(subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True).stdout)
        (work / "start.diff").write_text(subprocess.run(["git", "diff"], cwd=repo, capture_output=True, text=True).stdout)
    return work, repo


def limit_reached(log_path: Path) -> str | None:
    """Which limit ended a turn, from its result event's subtype, if one did."""
    try:
        events = [json.loads(line) for line in log_path.read_text().splitlines() if line.strip()]
    except (OSError, ValueError):
        return None
    subtype = next((e.get("subtype") for e in reversed(events) if e.get("type") == "result"), None)
    return {"error_max_turns": "max-turns", "error_max_budget_usd": "max-budget-usd"}.get(subtype)


def run_turns(prompts: list[str], work: Path, repo: Path, scenario: str | None, stage: str,
              plugins: dict[str, tuple[Path, str]], model: str | None, dry_run: bool,
              timeout: float = DEFAULT_TIMEOUT, budget: float = DEFAULT_BUDGET, max_turns: int = DEFAULT_MAX_TURNS,
              root: Path | None = None) -> int:
    env = session_env(work)
    name = scenario or "canary"
    extra_reads = uv_reads()
    if scenario and not dry_run:  # the canary runs no command, so it needs no cache
        problem = warm_uv_cache(repo, work / "uv-cache")
        if problem:
            print(f"HARNESS FAIL {name}: cannot warm the uv cache: {problem} ({work})")
            return 3
    resume, user_skills = None, user_skill_names()
    for n, prompt in enumerate(prompts, start=1):
        command = claude_command(prompt, work, scenario, plugins, model, resume, budget, max_turns=max_turns,
                                 root=root, extra_reads=extra_reads)
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
            limit = limit_reached(work / f"log-{n}.jsonl")
            value = {"max-turns": max_turns, "max-budget-usd": budget}.get(limit)
            reason = f"hit --{limit} {value:g}" if limit else f"claude exited {done.returncode}"
            print(f"HARNESS FAIL {name}: turn {n} {reason}; stderr in {work}/stderr-{n}.txt")
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
    p.add_argument("--max-turns", type=int, default=DEFAULT_MAX_TURNS, help="agentic turns per turn (default 60)")
    p.add_argument("--work-root", type=Path, default=DEFAULT_ROOT)
    args = p.parse_args(argv)
    try:
        plugins = installed_plugins()
    except HarnessFail as failure:
        print(failure)
        return 3
    versions = ", ".join(f"{name} {version}" for name, (_, version) in plugins.items())
    print(f"plugins: {versions}")
    args.work_root.expanduser().mkdir(parents=True, exist_ok=True)
    root = args.work_root.expanduser().resolve()  # the real path: the sandbox matches real paths
    limits = {"timeout": args.timeout, "budget": args.max_budget, "max_turns": args.max_turns, "root": root}
    if args.canary:
        work = Path(tempfile.mkdtemp(prefix="pdd-canary-", dir=root))
        (work / "empty-mcp.json").write_text('{"mcpServers":{}}\n')
        (work / "repo").mkdir()
        status = run_turns([CANARY], work, work / "repo", None, "red", plugins, args.model, args.dry_run, **limits)
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
        print(f"HARNESS FAIL {args.scenario}: no passing canary for model {args.model or 'default'} in {root} "
              "in the last 24 hours; run --canary first, with the same --model and --work-root")
        return 3
    work, repo = prepare(args.scenario, args.stage, root)
    prompts = [(HERE / "prompts" / name).read_text() for name in TURNS[args.scenario]]
    status = run_turns(prompts, work, repo, args.scenario, args.stage, plugins, args.model, args.dry_run, **limits)
    if status or args.dry_run:
        print(work)
        return status
    try:
        denials = [d for turn in grade.events(work) for e in turn if e.get("type") == "result"
                   for d in e.get("permission_denials") or []]
        uses = grade.all_uses(work)
        checks = grade.grade(args.scenario, work)
    except ValueError:
        print(f"HARNESS FAIL {args.scenario}: a log is not stream-json ({work})")
        return 3
    attempts = wait_attempts(denials, args.scenario, uses)
    if args.scenario in WAITS:
        checks.append(grade.Check("no attempt at what must wait", not attempts,
                                  f"attempted: {[a.get('tool_input') or a.get('tool_name') for a in attempts]}"))
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

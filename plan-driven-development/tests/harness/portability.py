#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Portability runs (S15, S16): a scenario in OpenCode or pi with only the project's AGENTS.md, no
skill installed, then graded on the repo and the final answer.

    uv run --script portability.py s02|s04 --harness opencode|pi --model PROVIDER/MODEL --dan-ok
                                   [--dry-run] [--timeout SECONDS]

Dan names the model and checks the Spark's model is up first. A session starts only with `--dan-ok`
(Dan's explicit go for this run); without it the runner stops with a HARNESS FAIL. Neither harness has
a turn or budget cap, so each session has a timeout (default 30 minutes), and the child process gets
a filtered environment (run.child_env: the basics, uv's cache settings and SPARK_API_KEY, nothing else). OpenCode gets the fixture's own
deny-by-default `opencode.json` (V2's ordered `permissions` rules, the last match winning); pi has
no per-command allow-list, so a pi run happens only with Dan's OK, in the throwaway repo. OpenCode
fails closed: a measured 2026-10-16 run showed OpenCode 2.0.25 ignoring a project `opencode.json`'s
`instructions` in `opencode run`, so its `permissions` must be proven, not assumed. Before a session
the runner asks OpenCode to list its configuration (`opencode debug config`), checks the output only
in memory for the deny rules (it is never printed or stored, as it may carry provider settings), and
refuses with "cannot confirm OpenCode honours the deny rules" if they are not there. That shows the
rules were loaded, not that they are enforced: the run's own denials are the evidence of that. Both
read Dan's own global instructions and config as well (OpenCode's global AGENTS.md, pi's
~/.pi/agent/AGENTS.md); the run records that it did. Checks that need a tool log are reported
SKIP: neither harness writes Claude Code's stream-json."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parents[1]
sys.path.insert(0, str(HERE))
import grade  # noqa: E402
import recipes  # noqa: E402
from run import DEFAULT_TIMEOUT, child_env  # noqa: E402

PROMPTS = {"s02": "continue-plan.md", "s04": "where-are-we.md"}
SHELL_ALLOWED = ["git status *", "git log *", "git diff *", "git show *", "git add *", "git commit -F *",
                 "git rev-parse *", "git interpret-trailers *", "git branch --show-current", "git switch *",
                 "make check", "uv run --quiet --with pytest pytest *", "uv run --with pytest pytest *",
                 "uv run --quiet --script scripts/leakcheck.py *", "ls *", "pwd"]


def opencode_config() -> dict:
    rules = [{"action": action, "resource": "*", "effect": "deny"}
             for action in ("shell", "webfetch", "websearch", "external_directory", "subagent")]
    rules += [{"action": "shell", "resource": pattern, "effect": "allow"} for pattern in SHELL_ALLOWED]
    rules += [{"action": "read", "resource": "*", "effect": "allow"}, {"action": "edit", "resource": "*", "effect": "allow"},
              {"action": "shell", "resource": "git push *", "effect": "deny"},
              {"action": "shell", "resource": "* --no-verify*", "effect": "deny"}]
    return {"$schema": "https://opencode.ai/config.json", "permissions": rules}


def command(harness: str, model: str, prompt: str) -> list[str]:
    if harness == "opencode":
        return ["opencode", "run", "--model", model, prompt]
    return ["pi", "-p", "--model", model, "--no-session", "--no-skills", "--no-extensions",
            "--tools", "read,bash,edit,write", prompt]


def opencode_honours_denies(repo: Path) -> bool:
    """Whether OpenCode, run in the repo, reports the generated deny rules among its configuration.
    The output stays in memory: it may hold provider settings, so it is searched, never printed."""
    try:
        done = subprocess.run(["opencode", "debug", "config"], cwd=repo, env=child_env("opencode", {}),
                              capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return False
    wanted = ["permissions", "git push *", "* --no-verify*", '"deny"']
    return done.returncode == 0 and all(word in done.stdout for word in wanted)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("scenario", choices=sorted(PROMPTS))
    p.add_argument("--harness", choices=["opencode", "pi"], required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--dan-ok", action="store_true", help="Dan's explicit go to start a session in this harness")
    p.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="seconds for the session (default 1800)")
    args = p.parse_args(argv)
    if not args.dry_run and not args.dan_ok:
        print(f"HARNESS FAIL {args.scenario} ({args.harness}): a session starts only with Dan's explicit go: pass --dan-ok")
        return 3
    work = Path(tempfile.mkdtemp(prefix=f"pdd-{args.scenario}-{args.harness}-"))
    repo = work / "repo"
    recipes.build(args.scenario, repo, "green", SKILL)  # AGENTS.md from the template; no skill copied
    if args.harness == "opencode":
        (repo / "opencode.json").write_text(json.dumps(opencode_config(), indent=2) + "\n")
        with open(repo / ".git/info/exclude", "a") as exclude:  # not staged, committed or part of the diff
            exclude.write("opencode.json\n")
    (work / "start.txt").write_text(subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True).stdout)
    (work / "start.diff").write_text(subprocess.run(["git", "diff"], cwd=repo, capture_output=True, text=True).stdout)
    (work / "denylist").write_text("an-invented-private-term\n")
    prompt = (HERE / "prompts" / PROMPTS[args.scenario]).read_text()
    cmd = command(args.harness, args.model, prompt)
    if args.dry_run:
        print(json.dumps(cmd))
        print(work)
        return 0
    if args.harness == "opencode" and not opencode_honours_denies(repo):
        print(f"HARNESS FAIL {args.scenario} (opencode): cannot confirm OpenCode honours the deny rules ({work})")
        return 3
    env = child_env(args.harness, {"LEAKCHECK_DENYLIST": str(work / "denylist")})
    try:
        result = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, stdin=subprocess.DEVNULL,
                                timeout=args.timeout)
    except subprocess.TimeoutExpired:
        print(f"HARNESS FAIL {args.scenario} ({args.harness}): timed out after {args.timeout:g}s ({work})")
        return 3
    (work / "stdout.txt").write_text(result.stdout)
    (work / "stderr.txt").write_text(result.stderr)
    if result.returncode != 0:
        print(f"HARNESS FAIL {args.scenario} ({args.harness}): exited {result.returncode}; stderr in {work}/stderr.txt")
        return 3
    (work / "no-tool-log").write_text(f"{args.harness}\n")
    final = [{"type": "result", "result": result.stdout.strip()}]
    (work / "log-1.jsonl").write_text("".join(json.dumps(e) + "\n" for e in final))
    checks = grade.grade(args.scenario, work)
    tag = {"s02": "S15", "s04": "S16"}[args.scenario]
    for check in checks:
        print(f"{grade.label(check)} {tag} ({args.harness}): {check.name}")
    print("note: the harness also read Dan's own global instructions and config")
    print(f"work folder: {work}")
    return 0 if all(c.ok is not False for c in checks) else 1


if __name__ == "__main__":
    sys.exit(main())

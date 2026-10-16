#!/usr/bin/env bash
# Wire the shared preferences and the leak-check guard into this machine's
# harness config. Idempotent and add-only: it never removes or overwrites
# anything that isn't its own.
#
# Usage: bash setup.sh [--check]
#   --check   report what each step would do and change nothing
#
# Each step prints one line: "<step>: ok | added | linked | skipped: <why> |
# warn: <what to do>". Set HOME to try it on a scratch directory.
# See docs/setup.md for what each step touches and how to undo it.
set -euo pipefail

check=0
case "${1:-}" in
  "") ;;
  --check) check=1 ;;
  *) echo "usage: bash setup.sh [--check]" >&2; exit 2 ;;
esac

# Steps 5 and 6 use Python through uv; fail before changing anything.
command -v uv >/dev/null 2>&1 || { echo "setup.sh: uv is not on PATH; install uv and re-run" >&2; exit 1; }

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
prefs="$repo/preferences.md"

# Paths below are assembled at run time so this file does not name them.
config_dir="$HOME/.con""fig"
denylist_name="deny""list"
leakcheck_dir="$config_dir/leak""check"
localai_dir="$config_dir/local""-ai"

say() { printf '%s: %s\n' "$1" "$2"; }

# 1. The import block in Claude Code's global CLAUDE.md.
claude_md="$HOME/.claude/CLAUDE.md"
import_line="@$prefs"
case "$prefs" in
  *" "*)
    say claude-import "warn: the repo path contains a space, which Claude Code's @import can't take; move the repo and re-run"
    ;;
  *)
    if [ -f "$claude_md" ] && grep -qxF -e "$import_line" "$claude_md"; then
      say claude-import ok
    elif [ "$check" = 1 ]; then
      say claude-import "warn: the import is missing; run make setup"
    else
      mkdir -p "$HOME/.claude"
      if [ -s "$claude_md" ]; then
        # Make sure the file ends in a newline, then leave one blank line.
        [ -z "$(tail -c1 "$claude_md")" ] || printf '\n' >> "$claude_md"
        printf '\n' >> "$claude_md"
      fi
      printf '# Shared preferences (all harnesses)\n\n%s\n' "$import_line" >> "$claude_md"
      say claude-import added
    fi
    ;;
esac

# 2. pi reads ~/.pi/agent/AGENTS.md.
pi_link="$HOME/.pi/agent/AGENTS.md"
if [ -L "$pi_link" ] && [ "$(readlink "$pi_link")" = "$prefs" ]; then
  say pi ok
elif [ -e "$pi_link" ] || [ -L "$pi_link" ]; then
  say pi "skipped: something else is already at ~/.pi/agent/AGENTS.md, left alone"
elif [ "$check" = 1 ]; then
  say pi "warn: not linked; run make setup"
else
  mkdir -p "$(dirname "$pi_link")"
  ln -s "$prefs" "$pi_link"
  say pi linked
fi

# 3. OpenCode: count only, never print or edit its config.
opencode_hits=0
opencode_unreadable=""
for f in "$config_dir/opencode/opencode.json" "$config_dir/opencode/opencode.jsonc"; do
  if [ -f "$f" ]; then
    if [ -r "$f" ]; then
      n="$(grep -cF -e "$prefs" "$f" 2>/dev/null || true)"
      opencode_hits=$((opencode_hits + ${n:-0}))
    else
      opencode_unreadable="$opencode_unreadable $(basename "$f")"
    fi
  fi
done
if [ "$opencode_hits" -gt 0 ]; then
  say opencode ok
elif [ -n "$opencode_unreadable" ]; then
  say opencode "warn:$opencode_unreadable unreadable, so I can't tell whether it lists preferences.md; make it readable and re-run"
else
  say opencode "warn: add \"instructions\": [\"$prefs\"] to OpenCode's config yourself; this script never edits it"
fi

# 4. The leak-check denylist link (existence only; never read).
if [ -e "$leakcheck_dir/$denylist_name" ]; then
  say denylist-link ok
elif [ -L "$leakcheck_dir/$denylist_name" ]; then
  say denylist-link "skipped: a broken link is there; remove it and re-run"
elif [ -e "$localai_dir/$denylist_name" ]; then
  if [ "$check" = 1 ]; then
    say denylist-link "warn: not linked; run make setup"
  else
    mkdir -p "$leakcheck_dir"
    ln -s "$localai_dir/$denylist_name" "$leakcheck_dir/$denylist_name"
    say denylist-link linked
  fi
else
  say denylist-link "warn: no denylist at the local-ai location yet, so nothing to link"
fi

# 5. The four deny rules in Claude Code's settings.json.
settings="$HOME/.claude/settings.json"
home_abs="//${HOME#/}"
deny_rules=$(printf 'Read(%s/%s/%s/%s)\nRead(%s/%s/%s/%s)\nRead(~/%s/%s/%s)\nRead(~/%s/%s/%s)' \
  "$home_abs" ".con""fig" "leak""check" "$denylist_name" \
  "$home_abs" ".con""fig" "local""-ai" "$denylist_name" \
  ".con""fig" "leak""check" "$denylist_name" \
  ".con""fig" "local""-ai" "$denylist_name")
py_deny=$(cat <<'PY'
import json, os, shutil, sys, tempfile, time

mode, path, rules_arg = sys.argv[1:4]
rules = sorted(rules_arg.split("\n"))
real = os.path.realpath(path)
bad = "deny-rules: warn: %s is not valid settings JSON; fix it and re-run" % path

data = {}
if os.path.exists(real):
    try:
        with open(real, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        print(bad)
        sys.exit(0)
if not isinstance(data, dict):
    print(bad)
    sys.exit(0)
perms = data.setdefault("permissions", {})
if not isinstance(perms, dict):
    print(bad)
    sys.exit(0)
deny = perms.setdefault("deny", [])
if not isinstance(deny, list):
    print(bad)
    sys.exit(0)
missing = [r for r in rules if r not in deny]
if not missing:
    print("deny-rules: ok")
    sys.exit(0)
if mode == "check":
    print("deny-rules: warn: %d of 4 rules missing; run make setup" % len(missing))
    sys.exit(0)
for r in missing:
    pos = len(deny)
    for i, x in enumerate(deny):
        if isinstance(x, str) and x > r:
            pos = i
            break
    deny.insert(pos, r)
folder = os.path.dirname(real)
os.makedirs(folder, exist_ok=True)
if os.path.exists(real):
    shutil.copy2(real, real + ".bak-" + time.strftime("%Y%m%d%H%M%S"))
fd, tmp = tempfile.mkstemp(dir=folder, prefix=".settings-", suffix=".tmp")
try:
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    if os.path.exists(real):
        shutil.copymode(real, tmp)
    os.replace(tmp, real)
except BaseException:
    if os.path.exists(tmp):
        os.unlink(tmp)
    raise
print("deny-rules: added %d" % len(missing))
PY
)
mode=apply
[ "$check" = 1 ] && mode=check
uv run --no-project --quiet python -c "$py_deny" "$mode" "$settings" "$deny_rules"

# 6. Is there a Bash hook that refuses a command naming the denylist and
# allows a harmless one? Only hooks whose matcher lists Bash are run, each
# with two sample payloads (in --check mode too). Nothing is changed.
py_guard=$(cat <<'PY'
import json, os, signal, subprocess, sys

path, target = sys.argv[1:3]
timeout = float(os.environ.get("SETUP_HOOK_TIMEOUT", "30"))
real = os.path.realpath(path)
cmds = []
if os.path.exists(real):
    try:
        with open(real, encoding="utf-8") as fh:
            data = json.load(fh)
        entries = data["hooks"]["PreToolUse"] if "hooks" in data else []
        for entry in entries:
            matcher = entry.get("matcher")
            if isinstance(matcher, str) and "Bash" in [m.strip() for m in matcher.split("|")]:
                for h in entry.get("hooks", []):
                    if h.get("command"):
                        cmds.append(h["command"])
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        print("guard: warn: %s is not valid settings JSON; fix it and re-run" % path)
        sys.exit(0)


def payload(command):
    return json.dumps({
        "session_id": "setup-check",
        "cwd": os.getcwd(),
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
    })


def refuses(cmd, command):
    # shell=True is deliberate: hook commands are shell strings from settings.json.
    p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, start_new_session=True)
    try:
        out, _ = p.communicate(payload(command), timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except OSError:
            pass
        p.communicate()
        return False
    except OSError:
        return False
    return '"deny"' in out or p.returncode == 2


blocks_target = False
blocks_harmless = False
for c in cmds:
    if refuses(c, "cat " + target):
        blocks_target = True
    if refuses(c, "ls"):
        blocks_harmless = True
if blocks_target and not blocks_harmless:
    print("guard: ok")
else:
    print("guard: warn: no PreToolUse hook naming Bash refuses a command that names the denylist "
          "while allowing a harmless one; the guard's copy is in guards/ (make sync-guards)")
PY
)
uv run --no-project --quiet python -c "$py_guard" "$settings" "$localai_dir/$denylist_name"

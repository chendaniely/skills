"""Tests for setup.sh. Every test runs it with HOME set to a fresh tmp dir.

Paths are assembled at run time.
"""

import json
import os
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SETUP = REPO / "setup.sh"

CFG = ".con" + "fig"
LEAK = "leak" + "check"
LOCAL = "local" + "-ai"
DL = "deny" + "list"


def _uv(*args):
    return subprocess.run(["uv", *args], capture_output=True, text=True, check=True).stdout.strip()


# uv run needs its interpreter and cache, which live under the real HOME.
UV_ENV = {
    "UV_CACHE_DIR": _uv("cache", "dir"),
    "UV_PYTHON_INSTALL_DIR": _uv("python", "dir"),
}


def run(home, *args, env=None, setup=SETUP, expect=0):
    full = {**os.environ, **UV_ENV, "HOME": str(home), **(env or {})}
    p = subprocess.run(
        ["bash", str(setup), *args], env=full, capture_output=True, text=True, cwd=home
    )
    assert p.returncode == expect, p.stdout + p.stderr
    assert "Traceback" not in p.stderr, p.stderr
    return p.stdout if expect == 0 else p.stdout + p.stderr


def line(out, step):
    hits = [ln for ln in out.splitlines() if ln.startswith(step + ": ")]
    assert len(hits) == 1, f"{step!r} not exactly once in:\n{out}"
    return hits[0][len(step) + 2 :]


def snapshot(home):
    snap = {}
    for root, dirs, files in os.walk(home):
        for name in dirs + files:
            p = Path(root) / name
            rel = str(p.relative_to(home))
            if p.is_symlink():
                snap[rel] = ("link", os.readlink(p))
            elif p.is_dir():
                snap[rel] = ("dir", None)
            else:
                snap[rel] = ("file", p.read_bytes())
    return snap


@pytest.fixture
def home(tmp_path):
    h = tmp_path / "home"
    h.mkdir()
    return h


def local_denylist(home):
    p = home / CFG / LOCAL / DL
    p.parent.mkdir(parents=True)
    p.write_text("")
    return p


def deny_rules(home):
    return json.loads((home / ".claude" / "settings.json").read_text())["permissions"]["deny"]


def backups(home):
    return sorted((home / ".claude").glob("settings.json.bak-*"))


def test_import_added_once(home):
    out = run(home)
    assert line(out, "claude-import").startswith("added")
    md = home / ".claude" / "CLAUDE.md"
    text = md.read_text()
    assert text.count("preferences.md") == 1
    assert f"@{REPO}/preferences.md" in text
    assert "# Shared preferences (all harnesses)" in text
    out2 = run(home)
    assert line(out2, "claude-import").startswith("ok")
    assert md.read_text() == text


def test_import_keeps_existing_content(home):
    md = home / ".claude" / "CLAUDE.md"
    md.parent.mkdir()
    md.write_text("# Mine\n\nkeep this")
    run(home)
    text = md.read_text()
    assert text.startswith("# Mine\n\nkeep this\n")
    assert text.count("preferences.md") == 1


def test_check_changes_nothing(home):
    local_denylist(home)
    before = snapshot(home)
    out = run(home, "--check")
    assert snapshot(home) == before
    assert not (home / ".claude").exists()
    assert line(out, "claude-import").startswith("warn")
    assert line(out, "pi").startswith("warn")


def test_pi_link_created(home):
    out = run(home)
    assert line(out, "pi").startswith("linked")
    link = home / ".pi" / "agent" / "AGENTS.md"
    assert link.is_symlink()
    assert os.readlink(link) == str(REPO / "preferences.md")
    assert line(run(home), "pi").startswith("ok")


def test_pi_other_file_left_alone(home):
    f = home / ".pi" / "agent" / "AGENTS.md"
    f.parent.mkdir(parents=True)
    f.write_text("mine")
    out = run(home)
    assert line(out, "pi").startswith("skipped")
    assert not f.is_symlink()
    assert f.read_text() == "mine"


def test_deny_rules_add_only_one_backup(home):
    st = home / ".claude" / "settings.json"
    st.parent.mkdir()
    existing = ["Bash(rm:*)", "Read(~/.secrets)", "Read(~/.zsh_history)"]
    st.write_text(json.dumps({"model": "x", "permissions": {"deny": existing, "allow": ["A"]}}))
    out = run(home)
    assert line(out, "deny-rules").startswith("added")
    rules = deny_rules(home)
    new = [
        f"Read(//{str(home).lstrip('/')}/{CFG}/{LEAK}/{DL})",
        f"Read(//{str(home).lstrip('/')}/{CFG}/{LOCAL}/{DL})",
        f"Read(~/{CFG}/{LEAK}/{DL})",
        f"Read(~/{CFG}/{LOCAL}/{DL})",
    ]
    for r in new:
        assert r in rules
    assert [r for r in rules if r in existing] == existing
    assert len(rules) == 7
    # sorted position: "Read(~/.config..." sorts before "Read(~/.secrets)"
    assert rules.index(new[2]) < rules.index("Read(~/.secrets)")
    data = json.loads(st.read_text())
    assert data["model"] == "x" and data["permissions"]["allow"] == ["A"]
    assert st.read_text().endswith("}\n")
    assert '\n  "model"' in st.read_text()
    assert len(backups(home)) == 1
    out2 = run(home)
    assert line(out2, "deny-rules").startswith("ok")
    assert len(backups(home)) == 1
    assert deny_rules(home) == rules


def test_deny_rules_created_when_missing(home):
    run(home)
    assert len(deny_rules(home)) == 4
    assert backups(home) == []


def test_denylist_link_needs_local_ai_one(home):
    link = home / CFG / LEAK / DL
    out = run(home)
    assert line(out, "denylist-link").startswith("warn")
    assert not link.exists() and not link.is_symlink()
    target = local_denylist(home)
    out = run(home)
    assert line(out, "denylist-link").startswith("linked")
    assert link.is_symlink() and os.readlink(link) == str(target)
    assert line(run(home), "denylist-link").startswith("ok")


def test_opencode_step(home):
    assert line(run(home), "opencode").startswith("warn")
    cfg = home / CFG / "opencode" / "opencode.json"
    cfg.parent.mkdir(parents=True)
    entry = '{"instructions": ["%s/preferences.md"]}' % REPO
    cfg.write_text(entry)
    out = run(home)
    assert line(out, "opencode").startswith("ok")
    assert str(REPO) not in line(out, "opencode")
    assert cfg.read_text() == entry


# ---- fix round 1 ----

def hook_settings(home, entries):
    st = home / ".claude" / "settings.json"
    st.parent.mkdir(exist_ok=True)
    st.write_text(json.dumps({"hooks": {"PreToolUse": entries}}))
    return st


def script(home, name, body):
    p = home / name
    p.write_text("#!/bin/bash\n" + body)
    p.chmod(0o755)
    return p


def test_uv_missing_fails_before_any_change(home):
    bindir = home / "bin"
    bindir.mkdir()
    for tool in ("bash", "dirname", "grep", "tail", "cat", "mkdir", "ln", "readlink", "date"):
        found = subprocess.run(["which", tool], capture_output=True, text=True).stdout.strip()
        if found:
            (bindir / tool).symlink_to(found)
    before = snapshot(home)
    out = run(home, env={"PATH": str(bindir)}, expect=1)
    assert "uv" in out
    assert len(out.strip().splitlines()) == 1
    assert snapshot(home) == before


def test_malformed_settings_warns_and_later_steps_run(home):
    st = home / ".claude" / "settings.json"
    st.parent.mkdir()
    st.write_text("{not json")
    out = run(home)
    assert line(out, "deny-rules").startswith("warn: ")
    assert "not valid settings JSON" in line(out, "deny-rules")
    assert st.read_text() == "{not json"
    assert backups(home) == []
    assert line(out, "guard").startswith("warn")
    assert line(out, "pi").startswith("linked")


@pytest.mark.parametrize("text", ["[1, 2]", '{"permissions": []}', '{"permissions": {"deny": "x"}}'])
def test_wrong_shapes_warn(home, text):
    st = home / ".claude" / "settings.json"
    st.parent.mkdir()
    st.write_text(text)
    out = run(home)
    assert "not valid settings JSON" in line(out, "deny-rules")
    assert st.read_text() == text


def test_symlinked_settings_keeps_link_and_writes_target(home):
    real = home / "dotfiles" / "settings.json"
    real.parent.mkdir()
    real.write_text(json.dumps({"permissions": {"deny": ["Bash(rm:*)"]}}))
    link = home / ".claude" / "settings.json"
    link.parent.mkdir()
    link.symlink_to(real)
    run(home)
    assert link.is_symlink() and Path(os.readlink(link)) == real
    assert len(json.loads(real.read_text())["permissions"]["deny"]) == 5
    assert len(list(real.parent.glob("settings.json.bak-*"))) == 1
    assert list((home / ".claude").glob("settings.json.bak-*")) == []


def test_non_ascii_survives(home):
    st = home / ".claude" / "settings.json"
    st.parent.mkdir()
    st.write_text(json.dumps({"note": "h\u00e9llo \u2603"}))
    run(home)
    text = st.read_text(encoding="utf-8")
    assert "h\u00e9llo \u2603" in text and "\\u00e9" not in text


def test_dangling_denylist_link_is_skipped(home):
    local_denylist(home)
    link = home / CFG / LEAK / DL
    link.parent.mkdir(parents=True)
    link.symlink_to(home / "nowhere")
    out = run(home)
    assert line(out, "denylist-link").startswith("skipped")
    assert os.readlink(link) == str(home / "nowhere")
    assert line(out, "guard")  # the script went on


def test_opencode_unreadable_is_a_warning(home):
    cfg = home / CFG / "opencode" / "opencode.json"
    cfg.parent.mkdir(parents=True)
    cfg.write_text("x")
    cfg.chmod(0)
    try:
        out = run(home)
    finally:
        cfg.chmod(0o644)
    assert "unreadable" in line(out, "opencode")
    assert line(out, "opencode").startswith("warn")


def test_opencode_counts_only_this_repos_path(home):
    cfg = home / CFG / "opencode" / "opencode.json"
    cfg.parent.mkdir(parents=True)
    cfg.write_text('{"instructions": ["/elsewhere/preferences.md"]}')
    assert line(run(home), "opencode").startswith("warn")


def test_import_ignores_other_mentions(home):
    md = home / ".claude" / "CLAUDE.md"
    md.parent.mkdir()
    md.write_text("# see preferences.md\n@/other/preferences.md\n")
    out = run(home)
    assert line(out, "claude-import").startswith("added")
    assert md.read_text().count(f"@{REPO}/preferences.md\n") == 1


def test_import_skipped_when_repo_path_has_space(home, tmp_path):
    repo = tmp_path / "a b"
    repo.mkdir()
    (repo / "preferences.md").write_text("")
    copy = repo / "setup.sh"
    copy.write_text(SETUP.read_text())
    out = run(home, setup=copy)
    assert "space" in line(out, "claude-import")
    assert line(out, "claude-import").startswith("warn")
    assert not (home / ".claude" / "CLAUDE.md").exists()


def test_guard_deny_all_hook_is_not_a_guard(home):
    h = script(home, "deny_all.sh", "cat >/dev/null\necho '{\"permissionDecision\": \"deny\"}'\n")
    hook_settings(home, [{"matcher": "Bash", "hooks": [{"type": "command", "command": str(h)}]}])
    assert line(run(home), "guard").startswith("warn")


def test_guard_real_guard_is_ok_and_payload_is_realistic(home):
    log = home / "payloads.log"
    h = script(
        home,
        "guard.sh",
        f'p=$(cat)\necho "$p" >> "{log}"\ncase "$p" in *{DL}*) echo \'{{"permissionDecision": "deny"}}\';; esac\n',
    )
    hook_settings(home, [{"matcher": "Bash|Read", "hooks": [{"type": "command", "command": str(h)}]}])
    out = run(home, "--check")
    assert line(out, "guard").startswith("ok")
    first, second = [json.loads(x) for x in log.read_text().splitlines()]
    for p in (first, second):
        assert p["hook_event_name"] == "PreToolUse"
        assert p["tool_name"] == "Bash"
        assert p["session_id"] == "setup-check"
        assert "cwd" in p and "command" in p["tool_input"]
    assert second["tool_input"]["command"] == "ls"
    assert DL in first["tool_input"]["command"]


@pytest.mark.parametrize("matcher", ["*", None, "", "Read"])
def test_guard_only_runs_hooks_naming_bash(home, matcher):
    marker = home / "marker"
    h = script(home, "other.sh", f"cat >/dev/null\ntouch '{marker}'\n")
    entry = {"hooks": [{"type": "command", "command": str(h)}]}
    if matcher is not None:
        entry["matcher"] = matcher
    hook_settings(home, [entry])
    assert line(run(home), "guard").startswith("warn")
    assert not marker.exists()


def test_guard_hang_cannot_wedge_setup(home):
    import time

    h = script(home, "hang.sh", "sleep 30\n")
    hook_settings(home, [{"matcher": "Bash", "hooks": [{"type": "command", "command": str(h)}]}])
    t = time.time()
    out = run(home, env={"SETUP_HOOK_TIMEOUT": "1"})
    assert time.time() - t < 15
    assert line(out, "guard").startswith("warn")

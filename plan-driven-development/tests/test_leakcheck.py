"""scripts/leakcheck.py, ported with local-ai's tests (spark/tests/test_leakcheck.py at e32096c)."""

import codecs
import re

import pytest

import os
import subprocess
import sys

from helpers import SCRIPTS, denylist, git, git_repo, ip, ipv6, load_script, mac

leakcheck = load_script("leakcheck")
scan_text = leakcheck.scan_text


def kinds(text: str, deny=()) -> list[str]:
    return [f.kind for f in scan_text("t.md", text, list(deny))]


@pytest.mark.parametrize("address", [ip(10, 1, 2, 3), ip(172, 20, 0, 5), ip(192, 168, 77, 5)])
def test_private_ipv4_is_flagged(address):
    assert kinds(f"server at {address} today") == ["private IPv4 address"]


def test_tailnet_address_is_flagged():
    assert kinds(f"node {ip(100, 101, 102, 103)}") == ["tailnet IPv4 address"]


def test_sentence_final_tailnet_address_is_flagged():
    assert kinds(f"The node is {ip(100, 101, 102, 103)}.") == ["tailnet IPv4 address"]


@pytest.mark.parametrize(
    "address",
    [ip(10, 1, 2, 3), ip(172, 20, 0, 5), ip(192, 168, 77, 5)],
    ids=["10/8", "172.16/12", "192.168/16"],
)
def test_sentence_final_private_ipv4_is_flagged(address):
    assert kinds(f"The box is at {address}.") == ["private IPv4 address"]


def test_tailnet_ipv6_address_is_flagged():
    # Tailscale's IPv6 range lies inside the unique-local range, so the broader pattern fires too.
    address = ipv6("fd7a", "115c", "a1e0", "", "5")
    assert kinds(f"node {address} today") == [
        "tailnet IPv6 address",
        "private or link-local IPv6 address",
    ]


@pytest.mark.parametrize(
    "address",
    [ipv6("fd12", "3456", "789a", "", "1"), ipv6("fe80", "", "1a2b", "3c4d", "5e6f", "7a8b")],
    ids=["unique-local", "link-local"],
)
def test_private_ipv6_is_flagged(address):
    assert kinds(f"host {address} today") == ["private or link-local IPv6 address"]


@pytest.mark.parametrize(
    "harmless",
    [
        "reserved as .201 on the wired NIC",
        f"docs example {ip(192, 0, 2, 7)} and {ip(203, 0, 113, 9)}",
        f"public {ip(100, 12, 1, 1)}",
        "uv 0.12.18 and CUDA 13.0.2",
        "at 12:34:56 it froze",
        "patterns for MACs and `ts.net` names",
        f"build {ip(10, 1, 2, 3, 4)} is longer than an address",
        "link-local fe80::/10 and unique-local fc00::/7 are ranges, not hosts",
    ],
)
def test_harmless_text_is_not_flagged(harmless):
    assert kinds(harmless) == []


def test_mac_address_is_flagged():
    assert kinds(f"nic {mac('a4', 'bb', '6d', '01', '02', 'ef')}") == ["MAC address"]


def test_tailnet_hostname_is_flagged():
    name = "box." + "tail" + "1a2b" + ".ts.net"
    assert kinds(f"https://{name}/") == ["tailnet hostname"]


def test_bare_tailnet_name_is_flagged():
    name = "tail" + "1a2b" + ".ts.net"
    assert kinds(f"the tailnet is {name} today") == ["tailnet hostname"]


def test_ddns_name_is_flagged():
    name = "home" + "." + "synology" + ".me"
    assert kinds(f"see {name} now") == ["Synology DDNS or QuickConnect name"]


def test_volume_path_and_key_block_are_flagged():
    assert kinds("/Vol" + "umes/Backup/x") == ["macOS volume path"]
    assert kinds("-----BEGIN " + "OPENSSH PRIVATE KEY-----") == ["private key block"]


def test_denylisted_term_is_flagged_case_insensitively():
    deny = [re.compile("secret-project", re.IGNORECASE)]
    assert kinds("about the Secret-Project plan", deny) == ["denylisted term"]


def test_allow_marker_skips_a_line():
    assert kinds(f"example {ip(192, 168, 0, 1)}  <!-- leakcheck: allow -->") == []


def test_allow_marker_never_excuses_a_denylisted_term():
    deny = [re.compile("secret-project", re.IGNORECASE)]
    text = f"secret-project box at {ip(192, 168, 0, 1)}  <!-- leakcheck: allow -->"
    assert kinds(text, deny) == ["denylisted term"]


def test_excerpt_is_redacted():
    assert scan_text("t.md", ip(10, 9, 8, 7), [])[0].excerpt == "10.…"


def test_missing_denylist_fails_closed(tmp_path):
    with pytest.raises(leakcheck.DenylistMissing):
        leakcheck.load_denylist(tmp_path / "nope")


def test_denylist_skips_blank_lines_and_comments(tmp_path):
    path = tmp_path / "denylist"
    path.write_text("# a comment\n\nsecret-project\n")
    assert [p.pattern for p in leakcheck.load_denylist(path)] == ["secret-project"]


def test_the_default_denylist_comes_from_the_environment(tmp_path, monkeypatch):
    path = denylist(tmp_path)
    monkeypatch.setenv("LEAKCHECK_DENYLIST", str(path))
    assert leakcheck.parser().parse_args(["--tracked"]).denylist == path


def test_staged_file_with_private_address_is_found(tmp_path):
    repo = git_repo(tmp_path)
    (repo / "notes.md").write_text(f"box at {ip(192, 168, 50, 7)}\n")
    git(repo, "add", "notes.md")
    texts = leakcheck.staged_texts(cwd=repo)
    assert texts == [("notes.md", f"box at {ip(192, 168, 50, 7)}\n")]
    assert kinds(texts[0][1]) == ["private IPv4 address"]


def test_ci_mode_is_refused_outside_ci(monkeypatch, capsys):
    monkeypatch.delenv("CI", raising=False)
    assert leakcheck.main(["--tracked", "--ci"]) == 2
    assert "only in CI" in capsys.readouterr().err


def test_a_missing_denylist_exits_2(tmp_path, capsys):
    message = tmp_path / "msg"
    message.write_text("hello\n")
    assert leakcheck.main(["--message", str(message), "--denylist", str(tmp_path / "none")]) == 2
    assert "denylist not found" in capsys.readouterr().err


def test_an_invalid_denylist_line_exits_2_and_is_never_shown(tmp_path, capsys):
    path = tmp_path / "denylist"
    path.write_text("first-term\nprivate-name(\n")
    message = tmp_path / "msg"
    message.write_text("hello\n")
    assert leakcheck.main(["--message", str(message), "--denylist", str(path)]) == 2
    err = capsys.readouterr().err
    assert "line 2" in err and "private-name" not in err


@pytest.mark.parametrize("text", ["", "# a comment\n\n   \n"], ids=["empty", "comments-only"])
def test_a_denylist_with_no_terms_fails_closed(tmp_path, capsys, text):
    path = tmp_path / "denylist"
    path.write_text(text)
    with pytest.raises(leakcheck.DenylistInvalid, match="denylist has no terms"):
        leakcheck.load_denylist(path)
    message = tmp_path / "msg"
    message.write_text("hello\n")
    assert leakcheck.main(["--message", str(message), "--denylist", str(path)]) == 2
    assert "denylist has no terms" in capsys.readouterr().err


def test_an_empty_message_validates_the_denylist_silently(tmp_path, capsys):
    # Kickoff and resume run `--message /dev/null`: it proves the denylist exists and parses, and
    # prints nothing at all.
    assert leakcheck.main(["--message", "/dev/null", "--denylist", str(denylist(tmp_path))]) == 0
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == ""


def test_a_message_that_is_not_utf8_is_still_scanned(tmp_path, capsys):
    message = tmp_path / "msg"
    message.write_bytes(b"caf\xe9 at " + ip(192, 168, 50, 7).encode() + b"\n")
    assert leakcheck.main(["--message", str(message), "--denylist", str(denylist(tmp_path))]) == 1
    assert "private IPv4 address" in capsys.readouterr().err


def test_a_symlink_turned_into_a_file_is_scanned(tmp_path):
    repo = git_repo(tmp_path)
    (repo / "notes.md").symlink_to("elsewhere.md")
    git(repo, "add", "notes.md")
    git(repo, "commit", "-q", "-m", "link")
    (repo / "notes.md").unlink()
    (repo / "notes.md").write_text(f"box at {ip(192, 168, 50, 7)}\n")
    git(repo, "add", "notes.md")
    assert leakcheck.staged_texts(cwd=repo) == [("notes.md", f"box at {ip(192, 168, 50, 7)}\n")]


def test_a_file_turned_into_a_symlink_has_its_target_scanned(tmp_path):
    repo = git_repo(tmp_path)
    (repo / "data").write_text("placeholder\n")
    git(repo, "add", "data")
    git(repo, "commit", "-q", "-m", "file")
    (repo / "data").unlink()
    target = f"/mnt/{ip(192, 168, 50, 7)}/share"
    (repo / "data").symlink_to(target)
    git(repo, "add", "data")
    assert leakcheck.staged_texts(cwd=repo) == [("data", target)]


@pytest.mark.parametrize("encoding", ["utf-16", "utf-16-be", "utf-32", "utf-32-be"])
def test_utf16_and_utf32_text_with_a_byte_order_mark_is_scanned(tmp_path, encoding):
    text = f"box at {ip(192, 168, 50, 7)}\n"
    bom = {"utf-16-be": codecs.BOM_UTF16_BE, "utf-32-be": codecs.BOM_UTF32_BE}.get(encoding, b"")
    repo = git_repo(tmp_path)
    (repo / "notes.txt").write_bytes(bom + text.encode(encoding))
    git(repo, "add", "notes.txt")
    assert leakcheck.staged_texts(cwd=repo) == [("notes.txt", text)]


def test_a_binary_file_is_named_for_a_person_to_check(tmp_path, monkeypatch, capsys):
    repo = git_repo(tmp_path)
    (repo / "shot.png").write_bytes(b"\x89PNG\r\n\x1a\n\0\0\0\rIHDR" + ip(192, 168, 50, 7).encode())
    git(repo, "add", "shot.png")
    monkeypatch.chdir(repo)
    assert leakcheck.main(["--staged", "--denylist", str(denylist(tmp_path))]) == 0
    assert "leakcheck: not scanned (binary): shot.png — check it by eye" in capsys.readouterr().err


def test_a_file_name_is_scanned_and_shown_redacted(tmp_path, monkeypatch, capsys):
    repo = git_repo(tmp_path)
    (repo / f"notes-{ip(192, 168, 50, 7)}.md").write_text("nothing private here\n")
    git(repo, "add", ".")
    monkeypatch.chdir(repo)
    assert leakcheck.main(["--staged", "--denylist", str(denylist(tmp_path))]) == 1
    err = capsys.readouterr().err
    assert "leakcheck: notes-192….md (file name):1: private IPv4 address (192…)" in err
    assert ip(192, 168, 50, 7) not in err


def test_a_denylisted_term_in_a_file_name_is_never_printed_whole(tmp_path, monkeypatch, capsys):
    repo = git_repo(tmp_path)
    (repo / "secret-project-plan.md").write_text(f"box at {ip(192, 168, 50, 7)}\n")
    git(repo, "add", ".")
    monkeypatch.chdir(repo)
    assert leakcheck.main(["--staged", "--denylist", str(denylist(tmp_path, "secret-project"))]) == 1
    err = capsys.readouterr().err
    assert "leakcheck: sec…-plan.md (file name):1: denylisted term (sec…)" in err
    assert "leakcheck: sec…-plan.md:1: private IPv4 address (192…)" in err
    assert "secret-project" not in err


def test_ci_scans_every_tracked_file_name(tmp_path, monkeypatch, capsys):
    repo = git_repo(tmp_path)
    (repo / f"notes-{ip(192, 168, 50, 7)}.md").write_text("nothing private here\n")
    git(repo, "add", ".")
    monkeypatch.chdir(repo)
    monkeypatch.setenv("CI", "true")
    assert leakcheck.main(["--tracked", "--ci"]) == 1
    assert "(file name):1: private IPv4 address" in capsys.readouterr().err


def test_a_range_scans_each_commits_patch_and_message(tmp_path, monkeypatch, capsys):
    repo = git_repo(tmp_path)
    (repo / "a.md").write_text("clean\n")
    git(repo, "add", "a.md")
    git(repo, "commit", "-q", "-m", "base")
    (repo / "b.md").write_text(f"box at {ip(10, 0, 0, 7)}\n")
    git(repo, "add", "b.md")
    git(repo, "commit", "-q", "-m", "note secret-project")
    monkeypatch.chdir(repo)
    assert leakcheck.main(["--range", "HEAD~1..HEAD", "--denylist", str(denylist(tmp_path))]) == 1
    err = capsys.readouterr().err
    assert "outgoing commits" in err
    assert "private IPv4 address" in err and "denylisted term" in err


def test_a_new_branch_range_scans_everything_the_remote_lacks(tmp_path, monkeypatch):
    repo = git_repo(tmp_path)
    (repo / "b.md").write_text(f"box at {ip(10, 0, 0, 7)}\n")
    git(repo, "add", "b.md")
    git(repo, "commit", "-q", "-m", "first")
    monkeypatch.chdir(repo)
    assert leakcheck.main(["--range", "HEAD --not --remotes", "--denylist", str(denylist(tmp_path))]) == 1


def test_a_range_names_a_binary_file_for_a_person_to_check(tmp_path, monkeypatch, capsys):
    # A screenshot going out can't be scanned: it is named, so the merge can wait for Dan's eye.
    repo = git_repo(tmp_path)
    (repo / "a.md").write_text("clean\n")
    git(repo, "add", "a.md")
    git(repo, "commit", "-q", "-m", "base")
    (repo / "shot.png").write_bytes(b"\x89PNG\r\n\x1a\n\0\0\0\rIHDR")
    git(repo, "add", "shot.png")
    git(repo, "commit", "-q", "-m", "a screenshot")
    monkeypatch.chdir(repo)
    assert leakcheck.main(["--range", "HEAD~1..HEAD", "--denylist", str(denylist(tmp_path))]) == 0
    assert "leakcheck: not scanned (binary): shot.png — check it by eye" in capsys.readouterr().err


def test_a_finding_says_to_stop_and_tell_dan(tmp_path, capsys):
    # A leak hit is a stop that never relaxes: the message says so, never "fix it and carry on".
    message = tmp_path / "msg"
    message.write_text(f"box at {ip(10, 0, 0, 7)}\n")
    assert leakcheck.main(["--message", str(message), "--denylist", str(denylist(tmp_path))]) == 1
    err = capsys.readouterr().err
    assert "stop and tell Dan" in err and "Fix the text" not in err


def test_an_unreadable_range_fails_closed(tmp_path, monkeypatch, capsys):
    repo = git_repo(tmp_path)
    (repo / "a.md").write_text("clean\n")
    git(repo, "add", "a.md")
    git(repo, "commit", "-q", "-m", "base")
    monkeypatch.chdir(repo)
    missing = "0123456789abcdef0123456789abcdef01234567"
    assert leakcheck.main(["--range", f"{missing}..HEAD", "--denylist", str(denylist(tmp_path))]) == 2
    assert "can't read the range" in capsys.readouterr().err


def test_a_renamed_file_is_scanned(tmp_path):
    # Review Focus 3: a rename (git status R) carries the whole file to its new name.
    repo = git_repo(tmp_path)
    (repo / "a.md").write_text(f"box at {ip(192, 168, 50, 7)}\n")
    git(repo, "add", "a.md")
    git(repo, "commit", "-q", "-m", "first")
    git(repo, "mv", "a.md", "b.md")
    assert leakcheck.staged_texts(cwd=repo) == [("b.md", f"box at {ip(192, 168, 50, 7)}\n")]


def test_a_non_ascii_file_name_is_scanned(tmp_path, monkeypatch, capsys):
    # Review Focus 5: git's -z output keeps a non-ASCII name intact, so it is read, not skipped.
    repo = git_repo(tmp_path)
    (repo / "café-notes.md").write_text(f"box at {ip(192, 168, 50, 7)}\n")
    git(repo, "add", "café-notes.md")
    monkeypatch.chdir(repo)
    assert leakcheck.main(["--staged", "--denylist", str(denylist(tmp_path))]) == 1
    assert "café-notes.md:1: private IPv4 address" in capsys.readouterr().err


# ---- Fix round 1 -----------------------------------------------------------------------------

LEAK = f"box at {ip(192, 168, 50, 7)}\n"
FAKE_SHA = "1" * 40


def run_script(*args, env=None, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "leakcheck.py"), *args],
        capture_output=True, text=True, env=env, cwd=cwd,
    )


def commit_file(repo, name, content, message="c", binary=False):
    path = repo / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content) if binary else path.write_text(content)
    git(repo, "add", "--", name)
    git(repo, "commit", "-q", "-m", message)


# F1: a crash must never print a private name, and must exit 2.
def test_a_missing_message_file_exits_2_and_never_shows_its_name(tmp_path):
    result = run_script(
        "--message", str(tmp_path / "secret-project-msg"), "--denylist", str(denylist(tmp_path))
    )
    assert result.returncode == 2
    assert "secret-project" not in result.stdout + result.stderr
    assert "Traceback" not in result.stderr
    assert "FileNotFoundError" in result.stderr
    assert "stop and tell Dan" in result.stderr


def test_an_unexpected_error_prints_only_its_type(tmp_path, monkeypatch, capsys):
    def boom(cwd=None):
        raise ValueError("secret-project-plan.md")

    monkeypatch.setattr(leakcheck, "staged_texts", boom)
    assert leakcheck.main(["--staged", "--denylist", str(denylist(tmp_path))]) == 2
    captured = capsys.readouterr()
    assert "secret-project" not in captured.out + captured.err
    assert "ValueError" in captured.err


def test_a_missing_git_exits_2(tmp_path, monkeypatch, capsys):
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))
    assert leakcheck.main(["--staged", "--denylist", str(denylist(tmp_path))]) == 2
    assert "FileNotFoundError" in capsys.readouterr().err


def test_a_denylist_that_is_not_utf8_exits_2(tmp_path, capsys):
    path = tmp_path / "denylist"
    path.write_bytes(b"\xff\xfe\x80 broken\n")
    message = tmp_path / "msg"
    message.write_text("hello\n")
    assert leakcheck.main(["--message", str(message), "--denylist", str(path)]) == 2
    assert "UnicodeDecodeError" in capsys.readouterr().err


def test_a_message_path_that_is_a_directory_exits_2(tmp_path, capsys):
    assert leakcheck.main(["--message", str(tmp_path), "--denylist", str(denylist(tmp_path))]) == 2
    assert "IsADirectoryError" in capsys.readouterr().err


# F2: --tracked reads blobs from the index.
def test_tracked_survives_a_dangling_symlink_and_scans_its_target(tmp_path):
    repo = git_repo(tmp_path)
    (repo / "link").symlink_to(f"/mnt/{ip(192, 168, 50, 7)}/nowhere")
    git(repo, "add", "link")
    texts = dict(leakcheck.tracked_texts(cwd=repo))
    assert texts == {"link": f"/mnt/{ip(192, 168, 50, 7)}/nowhere"}


def test_tracked_survives_a_directory_symlink(tmp_path):
    repo = git_repo(tmp_path)
    (repo / "real").mkdir()
    (repo / "real" / "a.md").write_text("clean\n")
    (repo / "dir-link").symlink_to("real")
    git(repo, "add", ".")
    texts = dict(leakcheck.tracked_texts(cwd=repo))
    assert texts == {"real/a.md": "clean\n", "dir-link": "real"}


def test_tracked_skips_a_submodule_entry(tmp_path):
    repo = git_repo(tmp_path)
    (repo / "a.md").write_text("clean\n")
    git(repo, "add", "a.md")
    git(repo, "update-index", "--add", "--cacheinfo", f"160000,{FAKE_SHA},sub")
    assert dict(leakcheck.tracked_texts(cwd=repo)) == {"a.md": "clean\n"}


def test_tracked_scans_a_file_deleted_from_the_working_tree(tmp_path):
    repo = git_repo(tmp_path)
    (repo / "a.md").write_text(LEAK)
    git(repo, "add", "a.md")
    (repo / "a.md").unlink()
    assert dict(leakcheck.tracked_texts(cwd=repo)) == {"a.md": LEAK}


def test_tracked_from_a_subfolder_scans_the_whole_repo(tmp_path, monkeypatch, capsys):
    repo = git_repo(tmp_path)
    (repo / "sub").mkdir()
    (repo / "sub" / "ok.md").write_text("clean\n")
    (repo / "root.md").write_text(LEAK)
    git(repo, "add", ".")
    monkeypatch.chdir(repo / "sub")
    assert leakcheck.main(["--tracked", "--denylist", str(denylist(tmp_path))]) == 1
    assert "root.md:1: private IPv4 address" in capsys.readouterr().err


# F3: staged blobs are read by id, not by name.
def test_a_staged_file_named_like_a_stage_spec_is_scanned(tmp_path):
    repo = git_repo(tmp_path)
    (repo / "notes.md").write_text("clean\n")
    (repo / "0:notes.md").write_text(LEAK)
    git(repo, "add", "--", "notes.md", "0:notes.md")
    assert dict(leakcheck.staged_texts(cwd=repo)) == {"notes.md": "clean\n", "0:notes.md": LEAK}


def test_a_staged_submodule_entry_is_skipped(tmp_path):
    repo = git_repo(tmp_path)
    (repo / "a.md").write_text("clean\n")
    git(repo, "add", "a.md")
    git(repo, "update-index", "--add", "--cacheinfo", f"160000,{FAKE_SHA},sub")
    assert leakcheck.staged_texts(cwd=repo) == [("a.md", "clean\n")]


# F4: binaries are named even when renamed and changed, or added only in a merge.
def test_a_renamed_and_changed_binary_is_named(tmp_path, monkeypatch, capsys):
    repo = git_repo(tmp_path)
    data = b"\0" + bytes(range(1, 256)) * 8
    commit_file(repo, "old.bin", data, "base", binary=True)
    git(repo, "mv", "old.bin", "new.bin")
    (repo / "new.bin").write_bytes(data + b"\0\1\2")
    git(repo, "add", "new.bin")
    git(repo, "commit", "-q", "-m", "move")
    monkeypatch.chdir(repo)
    assert leakcheck.main(["--range", "HEAD~1..HEAD", "--denylist", str(denylist(tmp_path))]) == 0
    assert "not scanned (binary): new.bin" in capsys.readouterr().err


def test_a_binary_added_only_in_a_merge_is_named(tmp_path, monkeypatch, capsys):
    repo = git_repo(tmp_path)
    commit_file(repo, "a.md", "clean\n", "base")
    base = git(repo, "rev-parse", "HEAD").stdout.strip()
    git(repo, "checkout", "-q", "-b", "side")
    commit_file(repo, "side.md", "side\n", "side")
    git(repo, "checkout", "-q", "main")
    commit_file(repo, "main.md", "main\n", "main")
    git(repo, "merge", "-q", "--no-ff", "--no-commit", "side")
    (repo / "evil.bin").write_bytes(b"\x89PNG\0\0\0")
    git(repo, "add", "evil.bin")
    git(repo, "commit", "-q", "-m", "merge")
    monkeypatch.chdir(repo)
    assert leakcheck.main(["--range", f"{base}..HEAD", "--denylist", str(denylist(tmp_path))]) == 0
    assert "not scanned (binary): evil.bin" in capsys.readouterr().err


# F5: --range accepts revisions, never git options.
def leaking_repo(tmp_path):
    repo = git_repo(tmp_path)
    commit_file(repo, "a.md", "clean\n", "base")
    commit_file(repo, "b.md", LEAK, "leak")
    return repo


def test_range_option_that_writes_a_file_is_refused(tmp_path, monkeypatch, capsys):
    repo = leaking_repo(tmp_path)
    out = tmp_path / "written.txt"
    monkeypatch.chdir(repo)
    assert leakcheck.main(["--range", f"--output={out} HEAD", "--denylist", str(denylist(tmp_path))]) == 2
    assert not out.exists()
    assert "can't read the range" in capsys.readouterr().err


def test_range_option_that_skips_everything_is_refused(tmp_path, monkeypatch):
    repo = leaking_repo(tmp_path)
    monkeypatch.chdir(repo)
    assert leakcheck.main(["--range", "--max-count=0 HEAD", "--denylist", str(denylist(tmp_path))]) == 2


def test_an_unsplittable_range_is_refused(tmp_path, monkeypatch):
    repo = leaking_repo(tmp_path)
    monkeypatch.chdir(repo)
    assert leakcheck.main(["--range", "'HEAD", "--denylist", str(denylist(tmp_path))]) == 2


def test_a_sha_not_remotes_range_still_works(tmp_path, monkeypatch):
    repo = leaking_repo(tmp_path)
    sha = git(repo, "rev-parse", "HEAD").stdout.strip()
    monkeypatch.chdir(repo)
    assert leakcheck.main(["--range", f"{sha} --not --remotes", "--denylist", str(denylist(tmp_path))]) == 1


@pytest.mark.parametrize("variable", ["GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL"])
def test_a_range_scans_who_wrote_each_commit(tmp_path, monkeypatch, capsys, variable):
    repo = git_repo(tmp_path)
    commit_file(repo, "a.md", "clean\n", "base")
    (repo / "b.md").write_text("clean\n")
    git(repo, "add", "b.md")
    git(repo, "commit", "-q", "-m", "clean", env={**os.environ, variable: "secret-project"})
    monkeypatch.chdir(repo)
    assert leakcheck.main(["--range", "HEAD~1..HEAD", "--denylist", str(denylist(tmp_path))]) == 1
    assert "secret-project" not in capsys.readouterr().err


def test_kickoffs_whole_history_scan_still_works(tmp_path, monkeypatch):
    # references/kickoff.md scans an existing repo's history with exactly this argument.
    repo = leaking_repo(tmp_path)
    monkeypatch.chdir(repo)
    assert leakcheck.main(["--range=--all", "--denylist", str(denylist(tmp_path))]) == 1


def test_a_named_remote_is_allowed_in_a_range_but_a_glob_is_not(tmp_path, monkeypatch):
    repo = leaking_repo(tmp_path)
    sha = git(repo, "rev-parse", "HEAD").stdout.strip()
    monkeypatch.chdir(repo)
    deny = str(denylist(tmp_path))
    assert leakcheck.main(["--range", f"{sha} --not --remotes=origin", "--denylist", deny]) == 1
    for wide in ("--remotes=*", "--remotes=or*", "--remotes=", "--remotes=a b"):
        assert leakcheck.main(["--range", f"{sha} --not {wide}", "--denylist", deny]) == 2, wide


# F6: an unreadable range's name may be private.
def test_an_unreadable_range_never_prints_the_range(tmp_path, monkeypatch, capsys):
    repo = leaking_repo(tmp_path)
    monkeypatch.chdir(repo)
    rc = leakcheck.main(["--range", "secret-project-branch..HEAD", "--denylist", str(denylist(tmp_path))])
    err = capsys.readouterr().err
    assert rc == 2 and "can't read the range" in err and "secret-project" not in err


# F7: a short term is not shown at all.
def test_a_term_of_three_characters_or_fewer_is_not_shown():
    deny = [re.compile("abc", re.IGNORECASE)]
    assert scan_text("t.md", "an abc here", deny)[0].excerpt == "…"
    assert leakcheck.shown_path("x-abc-y.md", deny) == "x-…-y.md"


# F8: a non-ASCII term in a file name is found in a range.
def test_a_non_ascii_denylisted_term_in_a_file_name_is_found_in_a_range(tmp_path, monkeypatch, capsys):
    repo = git_repo(tmp_path)
    commit_file(repo, "a.md", "clean\n", "base")
    commit_file(repo, "caf\u00e9-plan.md", "nothing\n", "named")
    path = tmp_path / "denylist"
    path.write_bytes("caf\u00e9\n".encode())
    monkeypatch.chdir(repo)
    assert leakcheck.main(["--range", "HEAD~1..HEAD", "--denylist", str(path)]) == 1
    assert "denylisted term" in capsys.readouterr().err


# F9: the denylist is read as UTF-8 whatever the locale.
def test_a_non_ascii_term_is_found_under_the_c_locale(tmp_path):
    path = tmp_path / "denylist"
    path.write_bytes("caf\u00e9\n".encode())
    message = tmp_path / "msg"
    message.write_bytes("we met at the caf\u00e9\n".encode())
    env = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0"}
    result = run_script("--message", str(message), "--denylist", str(path), env=env)
    assert result.returncode == 1 and "denylisted term" in result.stderr


# F10
def test_the_help_pointer_names_the_template_heading():
    assert leakcheck.HELP == "see AGENTS.md, Docs and security"

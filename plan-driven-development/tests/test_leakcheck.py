"""scripts/leakcheck.py, ported with local-ai's tests (spark/tests/test_leakcheck.py at e32096c)."""

import codecs
import re

import pytest

from helpers import denylist, git, git_repo, ip, ipv6, load_script, mac

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
    git(repo, "commit", "-q", "-m", f"note secret-project")
    monkeypatch.chdir(repo)
    assert leakcheck.main(["--range", "HEAD~1..HEAD", "--denylist", str(denylist(tmp_path))]) == 1
    err = capsys.readouterr().err
    assert "outgoing commits" in err
    assert "private IPv4 address" in err and "denylisted term" in err


def test_a_new_branch_range_scans_everything_the_remote_lacks(tmp_path, monkeypatch, capsys):
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

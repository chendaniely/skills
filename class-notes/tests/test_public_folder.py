"""A course can keep each session's public files in a second folder (class-notes.ini):
the transcript and the recording's link stay in the session folder, everything else lives
at the same relative path under the public root. With no config file, nothing changes.

Run: make test-class-notes
"""
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import class_notes as cn  # noqa: E402

SESSION = "section-02/2026-11-17-lecture"
PUBLIC = "public/repo/class-notes/2026-27"


def course(base, config=True):
    """A course repo with one session split across the two folders: (root, priv, pub)."""
    root = Path(base).resolve()
    root.mkdir(parents=True, exist_ok=True)
    (root / "prompt-notes.md").write_text("Prompt body\n")
    priv = root / SESSION
    priv.mkdir(parents=True)
    (priv / "transcript-plaud.md").write_text("[0:00 - 0:05] Speaker 1: hi\n")
    (priv / "plaud.md").write_text("<https://web.plaud.ai/s/pub_x>\n")
    (root / "public" / "repo").mkdir(parents=True)
    (root / "public" / "repo" / "README.md").write_text("the public repo\n")
    pub = root / PUBLIC / SESSION
    pub.mkdir(parents=True)
    (pub / "terminal.txt").write_text("$ git status\n")
    (pub / "materials.md").write_text("## Links\n")
    if config:
        (root / "class-notes.ini").write_text("[folders]\npublic = %s\n" % PUBLIC)
    return root, priv, pub


def test_no_config_public_is_private(tmp_path):
    root, priv, _ = course(tmp_path, config=False)
    assert cn.public_root(root) is None
    assert cn.Session(priv, root).public == priv


def test_session_pairs_folders(tmp_path):
    root, priv, pub = course(tmp_path)
    s = cn.Session(priv, root)
    assert s.public == pub and s.transcript == priv / "transcript-plaud.md"
    assert s.terminal == pub / "terminal.txt" and s.materials == pub / "materials.md"
    assert s.inputs == "transcript-plaud.md, terminal.txt, materials.md"


def test_payload_same_as_one_folder(tmp_path):
    root, priv, pub = course(tmp_path / "split")
    one, opriv, _ = course(tmp_path / "one", config=False)
    for f in pub.iterdir():
        (opriv / f.name).write_text(f.read_text())
    prompt = cn.select_prompts(root, [], None, None)[0]
    oprompt = cn.select_prompts(one, [], None, None)[0]
    assert cn.build_message(prompt, cn.Session(priv, root)) == \
        cn.build_message(oprompt, cn.Session(opriv, one))


def test_discover_skips_public_root(tmp_path):
    root, priv, pub = course(tmp_path)
    (pub / "transcript-plaud.md").write_text("decoy\n")
    assert cn.discover_sessions(root, None) == [priv]


def test_only_takes_public_path_and_slash(tmp_path):
    root, priv, _ = course(tmp_path)
    assert cn.discover_sessions(root, [SESSION + "/"]) == [priv]
    assert cn.discover_sessions(root, [PUBLIC + "/" + SESSION]) == [priv]


def test_uninitialised_submodule_fails(tmp_path):
    root, _, _ = course(tmp_path)
    shutil.rmtree(root / "public" / "repo")
    (root / "public" / "repo").mkdir()
    with pytest.raises(cn.Fail, match="git submodule update --init"):
        cn.public_root(root)
    shutil.rmtree(root / "public")
    with pytest.raises(cn.Fail, match="missing or empty"):
        cn.public_root(root)


def test_where(tmp_path, capsys):
    root, _, _ = course(tmp_path)
    assert cn.main(["where", "--repo", str(root), "--only", SESSION]) == 0
    assert capsys.readouterr().out == PUBLIC + "/" + SESSION + "\n"
    cn.main(["where", "--repo", str(root)])
    assert capsys.readouterr().out == PUBLIC + "\n"


# --------------------------------------------------------------- writing (generate, fetch, tidy)


class FakeClaude:
    def __init__(self):
        self.calls = 0

    def __call__(self, message, model):
        self.calls += 1
        return "# T\n\nbody\n", "claude-opus-5-5", None


@pytest.fixture
def fake_claude(monkeypatch):
    fake = FakeClaude()
    monkeypatch.setitem(cn.BACKENDS, "claude", fake)
    return fake


@pytest.fixture
def fake_plaud(monkeypatch):
    info = {"id": "x_" + "0" * 32, "name": "L", "start_at": "2026-11-24T12:00:00Z",
            "transcript": "available", "summary": "available"}
    monkeypatch.setattr(cn, "resolve_recording", lambda url: info)
    monkeypatch.setattr(cn, "fetch_transcript", lambda file_id: "[0:00 - 0:05] Speaker 1: hi\n")
    monkeypatch.setattr(cn, "fetch_summary", lambda file_id, name: "## Summary\n\nx\n")


def test_generate_writes_public(tmp_path, fake_claude):
    root, priv, pub = course(tmp_path)
    assert cn.main(["generate", "--repo", str(root), "--only", SESSION]) == 0
    out = pub / "notes-class-main--claude-opus-5-5.md"
    assert out.is_file() and not list(priv.glob("notes-class-*"))
    assert "- inputs: transcript-plaud.md, terminal.txt, materials.md" in out.read_text()


def test_generate_creates_missing_public_folder(tmp_path, fake_claude):
    root, priv, pub = course(tmp_path)
    shutil.rmtree(pub)
    cn.main(["generate", "--repo", str(root), "--only", SESSION])
    assert (pub / "notes-class-main--claude-opus-5-5.md").is_file()


def test_generate_skips_current_in_public(tmp_path, fake_claude):
    root, _, pub = course(tmp_path)
    prompt = cn.select_prompts(root, [], None, None)[0]
    (pub / "notes-class-main--claude-opus-5-5.md").write_text(
        "# T\n\n---\n\n- prompt-hash: %s\n- model: claude-opus-5-5 (requested: opus)\n"
        "- inputs: transcript-plaud.md, terminal.txt, materials.md\n" % prompt.hash)
    cn.main(["generate", "--repo", str(root), "--only", SESSION])
    assert fake_claude.calls == 0


def test_no_config_writes_beside_transcript(tmp_path, fake_claude):
    root, priv, _ = course(tmp_path, config=False)
    cn.main(["generate", "--repo", str(root), "--only", SESSION])
    assert (priv / "notes-class-main--claude-opus-5-5.md").is_file()


def test_fetch_splits_files(tmp_path, fake_plaud):
    root, _, _ = course(tmp_path)
    assert cn.main(["fetch", "https://web.plaud.ai/s/pub_y", "--repo", str(root),
                    "--suffix", "lecture"]) == 0
    priv2 = root / "section-02" / "2026-11-24-lecture"
    pub2 = root / PUBLIC / "section-02" / "2026-11-24-lecture"
    assert sorted(p.name for p in priv2.iterdir()) == ["plaud.md", "transcript-plaud.md"]
    assert [p.name for p in pub2.iterdir()] == ["notes-plaud.md"]


def test_tidy_finds_public_notes(tmp_path, capsys):
    root, _, pub = course(tmp_path)
    (pub / "notes-class-main--m.md").write_text("# T\nInstructor: X\n## A\ntext\n")
    assert cn.main(["tidy", "--check", "--repo", str(root), "--only", SESSION]) == 1
    assert PUBLIC + "/" + SESSION + "/notes-class-main--m.md" in capsys.readouterr().out

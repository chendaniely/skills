"""The subagent adapter: `prepare` builds a RED work folder with no session, `grade` turns subagent
transcripts into the logs grade.py reads. No model runs here."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from helpers import SKILL

ADAPTER = SKILL / "tests" / "harness" / "subagent_red.py"


def adapter(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["uv", "run", "--quiet", "--script", str(ADAPTER), *args], capture_output=True, text=True)


def kv(out: str) -> dict[str, str]:
    return dict(line.split("=", 1) for line in out.splitlines() if "=" in line)


def prepared(tmp_path: Path, monkeypatch, scenario: str = "s04") -> dict[str, str]:
    """A work folder from the adapter's prepare, with the cache warm (uv and PyPI) left out."""
    return kv("\n".join(in_process(monkeypatch, lambda repo, cache: None).prepare(scenario, tmp_path)))


def line(**fields) -> str:
    return json.dumps({"isSidechain": True, "agentId": "a1", **fields})


def fake_transcript(path: Path) -> None:
    lines = [
        line(type="user", message={"role": "user", "content": "where are we?"}),
        line(type="attachment", attachment={"type": "hook_success", "hookName": "SubagentStart"}),
        line(type="assistant", message={"role": "assistant", "content": [
            {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "git commit -F .git/MSG"}}]}),
        line(type="user", message={"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "ok"}]}),
        line(type="assistant", message={"role": "assistant", "content": [{"type": "text", "text": "Done."}]}),
    ]
    path.write_text("\n".join(lines) + "\n")


def test_prepare_builds_repo_without_skill(tmp_path, monkeypatch):
    out = prepared(tmp_path, monkeypatch)
    assert set(out) == {"repo", "work", "prompt"}
    repo, work, prompt = Path(out["repo"]), Path(out["work"]), Path(out["prompt"])
    assert repo.is_absolute() and (repo / ".git").exists()
    assert subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True).returncode == 0
    assert prompt.is_file() and prompt.read_text().strip()
    assert (work / "start.txt").is_file()
    assert not (repo / ".claude" / "skills").exists()


def test_prepare_prints_prompt2_for_s01(tmp_path, monkeypatch):
    out = prepared(tmp_path, monkeypatch, "s01")
    assert Path(out["prompt2"]).is_file()


def test_grade_fails_the_commit_check_and_prints_every_check(tmp_path, monkeypatch):
    out = prepared(tmp_path, monkeypatch)
    repo, work = Path(out["repo"]), Path(out["work"])
    (repo / "made-where-it-should-wait.txt").write_text("x\n")
    env = ["-c", "user.name=T", "-c", "user.email=t@example.invalid", "-c", "commit.gpgsign=false"]
    subprocess.run(["git", *env, "add", "made-where-it-should-wait.txt"], cwd=repo, check=True)
    subprocess.run(["git", *env, "commit", "-q", "-m", "x"], cwd=repo, check=True)
    transcript = tmp_path / "t.jsonl"
    fake_transcript(transcript)
    r = adapter("grade", "s04", str(work), str(transcript))
    assert r.returncode == 0, r.stderr
    lines = r.stdout.splitlines()
    assert any(l.startswith("FAIL") and "no commit made" in l for l in lines), r.stdout
    assert any(l.startswith("PASS") and "the uncommitted edits untouched" in l for l in lines) or \
        any("the uncommitted edits untouched" in l for l in lines)
    assert any("their tests run" in l and l.startswith("FAIL") for l in lines)
    assert len(lines) == 5
    log = [json.loads(l) for l in (work / "log-1.jsonl").read_text().splitlines()]
    assert {e["type"] for e in log} == {"user", "assistant"}  # attachments dropped, no init needed


def in_process(monkeypatch, warm):
    """The adapter loaded in this process, with run.py's cache warm replaced by `warm`."""
    spec = importlib.util.spec_from_file_location("subagent_red", ADAPTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    real = module._load

    def load(name):
        loaded = real(name)
        if name == "run":
            monkeypatch.setattr(loaded, "warm_uv_cache", warm)
        return loaded

    monkeypatch.setattr(module, "_load", load)
    return module


def test_prepare_warms_the_cache_as_run_py_does(tmp_path, monkeypatch):
    warmed = []
    module = in_process(monkeypatch, lambda repo, cache: warmed.append((repo.resolve(), cache.resolve())))
    out = kv("\n".join(module.prepare("s04", tmp_path)))
    work = Path(out["work"])
    assert warmed == [(work / "repo", work / "uv-cache")]


def test_a_failed_warm_is_a_harness_fail(tmp_path, monkeypatch, capsys):
    module = in_process(monkeypatch, lambda repo, cache: "uv run exited 1")
    assert module.main(["prepare", "s04", str(tmp_path)]) == 3
    out = capsys.readouterr().out
    assert "HARNESS FAIL s04: cannot warm the uv cache: uv run exited 1" in out
    assert "repo=" not in out


def test_grade_takes_the_handback_message_as_the_final_reply(tmp_path, monkeypatch):
    work = Path(prepared(tmp_path, monkeypatch)["work"])
    transcript = tmp_path / "t.jsonl"
    transcript.write_text("\n".join([
        line(type="user", message={"role": "user", "content": "where are we?"}),
        line(type="assistant", message={"role": "assistant", "content": [{"type": "text", "text": "Checking."}]}),
        line(type="assistant", message={"role": "assistant", "content": [
            {"type": "tool_use", "id": "h1", "name": "SubagentHandback", "input": {"message": "Task 2 is open."}}]}),
        line(type="user", message={"role": "user", "content": [{"type": "tool_result", "tool_use_id": "h1", "content": "ok"}]}),
    ]) + "\n")
    r = adapter("grade", "s04", str(work), str(transcript))
    assert r.returncode == 0, r.stderr
    log = [json.loads(l) for l in (work / "log-1.jsonl").read_text().splitlines()]
    assert log[-1] == {"type": "result", "result": "Task 2 is open."}

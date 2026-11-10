"""The docs templates: a sample site rendered from them with real Quarto, and CI's wrapper check run
against it. Rendering skips without Quarto; lychee runs only in CI."""

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from helpers import TEMPLATES

needs_quarto = pytest.mark.skipif(shutil.which("quarto") is None, reason="needs Quarto on PATH")

SPEC = "2026-01-01-demo-design"
PLAN = "2026-01-01-demo"


def fill(text: str) -> str:
    return (text.replace("__PROJECT__", "demo").replace("__SITE_URL__", "https://example.invalid/demo/")
            .replace("__REPO_URL__", "https://example.invalid/demo-repo").replace("__SPEC__", SPEC))


def sample_project(tmp_path: Path) -> Path:
    """A site project as kickoff leaves it: root files, a spec and a plan that link to each other,
    and the website/ folder from the templates with a wrapper for each doc."""
    repo = tmp_path / "demo"
    (repo / "docs/superpowers/specs").mkdir(parents=True)
    (repo / "docs/superpowers/plans").mkdir(parents=True)
    (repo / "README.md").write_text("# demo\n\nA demo. The docs are at <https://example.invalid/demo/>.\n")
    (repo / "AGENTS.md").write_text("# demo: how we work\n\nThe rules, in `docs/agents/`.\n")
    (repo / "CHANGELOG.md").write_text("# Changelog\n\n## 2026-01-01\n\n- Kickoff.\n")
    (repo / f"docs/superpowers/specs/{SPEC}.md").write_text(
        f"# Demo: design spec\n\nThe plan is [Phase 1](../plans/{PLAN}.md).\n"
    )
    (repo / f"docs/superpowers/plans/{PLAN}.md").write_text(
        f"# Demo plan\n\n**Spec:** [the spec](../specs/{SPEC}.md)\n\n***\n\n### Task 1: start\n"
    )
    site = repo / "website"
    shutil.copytree(TEMPLATES / "quarto", site, ignore=shutil.ignore_patterns("wrapper.md"))
    for path in site.iterdir():
        if path.suffix in (".yml", ".qmd", ".md"):
            path.write_text(fill(path.read_text()))
    wrapper = (TEMPLATES / "quarto" / "wrapper.md").read_text()
    for kind, name in (("specs", SPEC), ("plans", PLAN)):
        (site / "superpowers" / kind).mkdir(parents=True, exist_ok=True)
        (site / "superpowers" / kind / f"{name}.md").write_text(
            wrapper.replace("__TITLE__", name).replace("__PATH__", f"{kind}/{name}.md")
        )
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    return repo


def wrapper_check(repo: Path) -> subprocess.CompletedProcess[str]:
    """CI's wrapper check, run exactly as the template's step gives it."""
    site = yaml.safe_load((TEMPLATES / "ci.yml").read_text())["jobs"]["site"]["steps"]
    (step,) = [s for s in site if "no wrapper for" in s.get("run", "")]
    return subprocess.run(["bash", "-c", step["run"]], cwd=repo, capture_output=True, text=True)


def test_ci_finds_a_doc_without_its_wrapper(tmp_path):
    repo = sample_project(tmp_path)
    assert wrapper_check(repo).returncode == 0
    (repo / f"website/superpowers/plans/{PLAN}.md").unlink()
    result = wrapper_check(repo)
    assert result.returncode == 1
    assert f"no wrapper for docs/superpowers/plans/{PLAN}.md" in result.stdout


@needs_quarto
def test_the_sample_site_renders_with_working_cross_links(tmp_path):
    repo = sample_project(tmp_path)
    result = subprocess.run(["quarto", "render", "website"], cwd=repo, capture_output=True, text=True)
    log = result.stdout + result.stderr
    assert result.returncode == 0, log
    assert "Unable to resolve link target" not in log, log
    built = repo / "website/_site/superpowers"
    spec_html = (built / f"specs/{SPEC}.html").read_text()
    plan_html = (built / f"plans/{PLAN}.html").read_text()
    assert f'href="../../superpowers/plans/{PLAN}.html"' in spec_html
    assert f'href="../../superpowers/specs/{SPEC}.html"' in plan_html
    home = (repo / "website/_site/index.html").read_text()
    assert "A demo." in home and "mermaid" in home
    right = home.partition("navbar-nav-scroll ms-auto")[2]
    for page in ("architecture", "design", "changelog", "how-we-work"):
        assert f'class="dropdown-item" href="./{page}.html"' in right, page


@needs_quarto
def test_a_link_quarto_cant_resolve_fails_the_render_check(tmp_path):
    repo = sample_project(tmp_path)
    spec = repo / f"docs/superpowers/specs/{SPEC}.md"
    spec.write_text(spec.read_text() + "\nSee [a missing page](../plans/missing.md).\n")
    result = subprocess.run(["quarto", "render", "website"], cwd=repo, capture_output=True, text=True)
    assert "Unable to resolve link target" in result.stdout + result.stderr

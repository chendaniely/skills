"""The generator writes the notes' date line from the session folder, not the model.

Run: make test-class-notes
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from class_notes import session_date, stamp_date  # noqa: E402


def test_session_date():
    assert session_date(Path("section-02/2026-11-19-lecture")) == "2026-11-19"
    assert session_date(Path("misc")) is None


def test_replaces_model_date():
    text = "# T\n\nDate Time: 2026-11-19 14:00:00\nInstructor: X\n\n## Summary\n\nbody\n"
    lines = stamp_date(text, "2026-11-19").splitlines()
    assert lines[:4] == ["# T", "", "Date: 2026-11-19", ""]
    assert "Instructor: X" in lines
    assert not any("14:00" in line for line in lines)


def test_other_forms_removed():
    text = "# T\n\n**Date:** 2026-11-19\nDate and time: today\nInstructor: X\n\n## Summary\n"
    lines = stamp_date(text, "2026-11-19").splitlines()
    assert [line for line in lines if "date" in line.lower()] == ["Date: 2026-11-19"]


def test_body_dates_kept():
    text = "# T\n\n## Assignments\n\nDue Date: 2026-12-01\n"
    assert "Due Date: 2026-12-01" in stamp_date(text, "2026-11-19").splitlines()


def test_no_title():
    assert stamp_date("## Summary\n\nx\n", "2026-11-19").startswith("Date: 2026-11-19\n\n## Summary")


def test_no_date():
    text = "# T\n\nDate Time: 2026-11-19 14:00:00\nInstructor: X\n\n## Summary\n"
    out = stamp_date(text, None)
    assert "Date" not in out
    assert "Instructor: X" in out


def test_body_blank_lines_untouched():
    text = "# T\n\n## Commands\n\n```bash\na\n\n\n\nb\n```\n"
    assert stamp_date(text, "2026-11-19").endswith("## Commands\n\n```bash\na\n\n\n\nb\n```\n")
